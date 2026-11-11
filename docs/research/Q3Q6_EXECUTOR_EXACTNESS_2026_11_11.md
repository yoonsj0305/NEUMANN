# NEUMANN 1 | Invention-core executor fix: what changed, why it is exact, what it costs, and the next evaluation design
2026-11-11 | Branch `claude/neumann1-executor-fix` | Frozen FIRST receipts untouched (FIRST = INCOMPLETE) | Global Q1–Q7 OPEN

Context: the FIRST evaluation was terminated INCOMPLETE on the owner's instruction after profiling showed one rule-B
task spending ≥ 1 h 45 min inside nested calls of stored programs whose arguments were re-evaluated in every loop
iteration ([diagnosis](Q3Q6_INVENTION_FIRST_OPERATIONAL_DIAGNOSIS_2026_11_11.md)). This document covers only the
executor. It adds no capability, no new primitive and no search heuristic.

## 1. Changes (commit `4507b8e`, `neumann1/invention_core.py`)

| # | Change | Switch | Kind |
|---|---|---|---|
| 1 | **Call-by-need abstraction arguments.** A binder-free argument of an abstraction call (stored program or invention) is evaluated at most once per call, on first reference, and then reused. This covers top-level calls (`Prim.make`, kind `inv`) and nested calls inside templates (`_template` → `call_need`). | `CALL_BY_NEED` | semantics-preserving |
| 2 | **Faithful vector reuse.** In a higher-order candidate (fold/map/filter/higher-order abstraction), a binder-free child whose value vector is *faithful* (see §2.4) is read from that vector instead of being re-executed. | `REUSE_VECTORS` | semantics-preserving |
| 3 | **Work meter** `WORK`: first-order primitive applications, `if`/first-order vector steps, loop iterations. One unit for both modes; write-only. | — | metering |
| 4 | `solve()` additionally returns `cpu_seconds` (process CPU) and `work`. | — | metering |
| 5 | `research/q3/checkpoint_runner.py`: one process per job, JSON-lines checkpoint with fsync per job, restart skips finished keys, per-job exception capture, optional wall cap recorded as `timeout`, per-job CPU/work/candidates/peak RSS. | — | infrastructure |

Both switches default to ON. With both OFF the code follows the frozen executor's evaluation order (plus metering).
Search code (`_level`, `_pool`, `_keep`, budget accounting, retrieval, compression, prior) is unchanged.

## 2. Why the changes are exact (code-level argument)

### 2.1 Purity
* Substrate primitives (`_add` … `_range`) are pure: they return a new immutable value (int, bool, tuple) or `None`.
* Every compiled closure captures only compile-time data: indices, constants and child closures.
* The mutable state reachable during evaluation is limited to four things, none of which can change an
  evaluation result:
  * `WORK` (only incremented, never read by evaluation);
  * the private cell of one call-by-need thunk;
  * the `idx` cell of a vector-reuse evaluation (set by the loop before each env);
  * compile caches (`Prim.tmpl`, `vprog`), which are deterministic functions of (body, depth).

Hence evaluating the same expression twice on the same environment gives the same value, or raises the same
exception.

### 2.2 Exception propagation
Evaluation can raise `Fail` (a primitive returned `None`, or a reused child is `None`). Nothing inside
evaluation catches it. The only handlers are at per-environment boundaries: value mode and the closure loop in
`_cand`, `run_program`, and memory replay. So the first exception in an evaluation ends that whole
per-environment evaluation.

Call-by-need invokes the argument at its **first reference**, which is exactly where call-by-name would first
evaluate it:
* If the argument raises, the cell stays empty and the exception propagates. The outcome is identical, because the
  evaluation is over and no later reference happens.
* If it returns `v`, every later call-by-name re-evaluation would also return `v` (purity), so reusing `v` is
  identical.
* An argument that is never referenced is never evaluated in either mode, so laziness is preserved
  (`test_lazy_failure_semantics_kept`).

### 2.3 Scope
A hole with no binder dependencies (`js == ()`) in a template for call depth `dcall` is compiled to `A[k](env)`
(at the top of the body) or `A[k](env[:dcall])` (inside a loop). Inside a body, environments are only ever
extended by appending (`env + (x, acc)`, `env + (x,)`); no construct replaces or drops a prefix element. So at every
reference `env[:dcall]` is the call-site environment, which is exactly what the thunk captures.

Binder-free ⇔ `js == ()`:
* `_au` gives each hole the binder types of exactly its `js`.
* `_to_body` creates memory holes `("h", i, ())` with parameter `(t, ())`.
* `Prim.lazy` lists exactly the parameters with an empty binder tuple.

Holes that depend on loop variables (`js ≠ ()`) stay call-by-name.

### 2.4 Faithfulness of reused vectors
A binder-free child is evaluated by its parent only on the parent's own environment:
* `make`: `init(env)`, `lst(env)`;
* abstractions: through holes at `env[:dcall] = env`.

Its vector was computed on the same `_Ctx.envs` list, in the same order, so env #i ↔ `vec[i]`.

`faith` (vector equals what the closure returns, `None` ⇔ `Fail`) holds by induction:
* terms: the vector is the environment values;
* first-order primitives: strict in all arguments in both executors;
* `if`: lazy selection in both;
* closure-evaluated candidates: by definition.

It does **not** hold for value-mode first-order abstraction calls. Those are strict (`if None in args`), whereas
the closure executor is lazy, so their vectors are never reused.

**Pre-existing finding, kept unchanged:** the frozen executor evaluates the same expression with these two
semantics depending on context. This is harmless for `Found`, because strict success implies lazy success with the
same value. But some observational-equivalence vectors show a failure where lazy evaluation would succeed. Changing
this would change the search, so it is out of scope here.

### 2.5 What is not claimed
The argument covers the executor paths above. It does not cover a different Python version, and it does not prove
anything about tasks outside the differential test. Exactness on data is evidence, not proof, and is reported
separately (§3).

## 3. Differential evidence on development data (no TARGET file read)

Harness: `research/q3/executor_equivalence.py`. Executors compared per (task, arm):
* **frozen:** the file at freeze commit `0954ed5`, loaded from git;
* **off:** new code with both switches off;
* **on:** new code with both switches on.

Compared per job: fit, solved, via, returned AST, candidate count, and SHA-256 of the ordered trace of every entry
reaching `_keep` (context depth, AST, value vector). This trace equals the candidate order plus every intermediate
value vector.

Data:
* 80 self-authored dev tasks;
* 312 usable SOURCE tasks of the FIRST registry (rule_source 125 + oeis_source 187 usable), read with blob SHA-1
  checks;
* arms A, B (frozen memory), C (frozen inventions, prior and memory); budget 50 000 candidates; wall cap 300 s per
  job.

### 3.1 Results (run 12:03–13:39 UTC, code commit `4507b8e`, core sha256 `e94ce526…614c`)

Receipts: `docs/experiments/results/executor_equivalence_50k.json` (aggregate),
`executor_equivalence_50k_rows.jsonl.gz` (all 3 528 rows; sha256 of the uncompressed file `a4b53f16…79fe`),
`executor_equivalence_50k.log`.

**Accounting.** 392 tasks × 3 arms × 3 executors = 3 528 jobs expected; 3 528 rows; 0 missing; 0 duplicate keys.

| Executor | completed | wall-cap timeouts (300 s) |
|---|---:|---:|
| frozen | 1 161 | 15 (B 4, C 11) |
| off | 1 159 | 17 (B 6, C 11) |
| **on** | **1 176** | **0** |

All 32 timeouts belong to the old evaluation order, on rule SOURCE tasks in the memory arms. They are **not
comparable** and are **excluded from the correctness evidence**: for 4 (B) + 11 (C) task–arm pairs there is no
frozen result to compare with. No job raised an exception.

**Equality on every comparable pair** (fit, solved, via, returned AST, candidate count, SHA-256 of the ordered
`_keep` trace, trace length):

| Arm | frozen vs on: comparable / mismatches | frozen vs off | off vs on | solved (frozen = on) |
|---|---:|---:|---:|---:|
| A | 392 / **0** | 392 / 0 | 392 / 0 | 51 = 51 |
| B | 388 / **0** | 386 / 0 | 386 / 0 | 82 = 82 |
| C | 381 / **0** | 381 / 0 | 381 / 0 | 93 = 93 |

1 161 frozen-vs-on comparisons, 0 mismatches. This is evidence on development data at a 50 000 budget, not a
proof; the proof obligations are the code-level argument of §2.

**Cost** (triples where all three executors finished; so the 32 worst old-executor cases are *not* in these sums):

| Arm | CPU s frozen → on (total) | ratio | work off → on (total) | per-task CPU ratio: median / p90 / p99 / max | worst single task (frozen → on) |
|---|---:|---:|---:|---|---|
| A | 254.7 → 251.7 | 1.01× | 1.25× less | 1.00 / 1.25 / 1.50 / 2.0 | 1.46 s → 1.22 s |
| B | 2 236.8 → 571.7 | 3.9× | 6.9× less | 0.93 / 1.41 / 12.8 / 18.4 | 198.4 s → 15.5 s |
| C | 2 278.9 → 520.9 | 4.4× | 7.7× less | 0.96 / 1.44 / 13.1 / 20.6 | 193.2 s → 11.2 s |

How to read this honestly:
* The saving is concentrated in the tail. On the median task the new executor is slightly **slower** (0.93–0.96×
  in B/C; largest slowdown < 1 s) because of thunk and metering overhead. In the worst decile of old-executor cost
  it is 10–20× faster.
* With the censored cases included the tail is larger than the table shows: every task the old executors could not
  finish in 300 s finished in ≤ 30 s (max `on` CPU over all 1 176 jobs: A 1.2 s, B 25.0 s, C 29.7 s).
* The work meter falls in every arm (A 1.25×) because binder-free children are no longer re-executed, but in A
  this does not reduce CPU: the saved steps are cheap and the bookkeeping costs as much.

Unit tests:
* `tests/test_executor_exactness.py`: trace-level equality with the frozen executor on a dev sample for A, B, C;
  laziness; equal outputs and less work on the profiled blow-up pattern.
* `tests/test_checkpoint_runner.py`: restart equals a fresh run; errors and timeouts are recorded.

Profiled pattern, measured: the largest stored program (33 nodes, references its input 5 times inside loops),
nested 3 times on dev inputs. Outputs identical; work 333 206 → 1 794 steps (185×).

## 4. Budget redesign (search policy, NOT an executor optimisation)

Two quantities are now measured separately per task: **candidates** (the FIRST budget unit) and **work** (substrate
steps), plus CPU seconds. Any limit on work changes which programs can be found, so it is a search-policy
condition. It must be pre-registered and applied identically to every arm:

| Policy | Definition | Changes results? |
|---|---|---|
| P0 candidate budget (FIRST) | stop after N candidates | reference |
| P1 per-task work cap | additionally stop the task's search when cumulative work > W | yes: tasks needing more work are lost |
| P2 per-candidate fuel | a candidate whose evaluation on an env exceeds F steps counts as failing on that env | yes: changes value vectors and the search |

Rules for using them:
* W and F are fixed on development data only (e.g. a high percentile of SOURCE per-task work under P0).
* Compute-matched comparisons between arms use equal W (Q1/Q4); candidate-matched comparisons are secondary.
* A P1/P2 result is never reported as if it were P0.

## 5. Next evaluations (design; nothing run, no TARGET opened)

1. **SECOND evaluation on the FIRST targets (disclosed as second, on opened targets).**
   * Setup: same registry, frozen core, arms, budgets and PASS rules, policy P0, executor `4507b8e`, checkpoint
     runner.
   * Integrity condition: because the executor is exact, rule A and A4 must reproduce **25** and **34**; any
     difference voids the run.
   * Label: it cannot be called FIRST evidence. Its value is completing the pre-registered comparison at
     affordable cost.
2. **Independent fresh evaluation (Q3 on a never-opened pool; Q6 cross-semantic as a real transfer).**
   * Registered pools (`docs/experiments/second_eval_candidate_registry.json`, metadata only, no content on disk):
     499 OEIS A000 reserve files, and 1 000 OEIS A001 files never mentioned in commits, PRs or issues.
   * Q6 transfer arm: a core trained on **lists only** (rule SOURCE), evaluated zero-shot on A001. This is
     different from the FIRST "shared core" design, whose core also learned from OEIS SOURCE.
   * A fresh *list* family is still needed. Candidates with zero mentions in this repository's commits, PRs and
     issues: λ² benchmarks (Feser et al.), CrossBeam/LambdaBeam DeepCoder-style tasks, Myth benchmarks. Each must
     be registered blobless by blob SHA-1 before any byte is read.
   * Excluded: SyGuS (104 PRs), ConceptARC (opened 2026-10-22).
3. **Gate before any freeze:** time every arm on a development sample with the checkpoint runner, and report
   per-task work and CPU percentiles.
