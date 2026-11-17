# NEUMANN 1 | Q3/Q6 invention-core FIRST: operational diagnosis of the B stall, and a checkpointed re-design
2026-11-11 11:41 UTC | Diagnosis only. The running evaluation was NOT stopped, restarted or modified | Global Q1–Q7 OPEN

## 1. Status at 11:39 UTC (OS read-only)

* `eval.log` still ends with `rule A4 … wall 312.2` (08:28:08). **rule B has printed nothing** and its count is unknown.
* Completed B tasks inferred from pipe syscall counters (protocol verified against CPython 3.13 `multiprocessing`,
  §4 of the receipts): **124 / 125**. Workers 4151, 4153, 4154 are idle (S). Worker 4152 has been on the last
  task since before 10:08:21, i.e. **≥ 91 min**, at 100 % CPU, with byte-identical RSS (216 MB) throughout.
* No OS limit applies: CPU-time and memory rlimits are unlimited, memory cgroup failcnt 0, the process is detached
  (PPID 1). The remaining hazard is reclamation of the container.

## 2. Profiling (what was done and its effect on the run)

Tool: `py-spy 0.4.0 dump --nonblocking` on PID 4152, installed in the scratchpad only. `--nonblocking` reads the
target's memory with `process_vm_readv`. It does not send SIGSTOP or ptrace-stop the target, and it writes nothing
into it. Effect on the run: none on results, which are deterministic in candidate counts with no time dependence;
negligible on wall time (two of the four cores were idle). 3 + 12 successful samples, 11:40:00–11:40:51; failed
reads (a race inherent to non-blocking mode) were discarded.

Every one of the 12 samples has the same shape:

```
_cand  (invention_core.py:729)      higher-order candidate evaluated on every env
 └ foldr (:190)                      the candidate: a base foldr whose body …
   └ <memory program> (:212)         … calls a retrieved SOURCE program, whose argument is …
     └ gl/filter (:259/:267)         … re-evaluated inside its foldl/filter loop (:285) …
       └ <memory program> (:212)     … and that argument is itself a memory call, 3–4 levels deep
         └ … not/eq/tail             innermost work: substrate primitives
```

3–4 nested memory-program calls per sample, Python stack depth 22–30. No sample was outside this candidate shape.

## 3. Code-level root cause: candidate budget and real work are decoupled

1. **The budget counts candidates, not work.** `self.n += 1` once per candidate (`_cand`, l.695). Evaluating
   that candidate (`fn(env)` for every env, l.724–732) has no step or time limit.
2. **Call-by-name argument re-evaluation.** In a compiled abstraction body, a hole that does not depend on
   binders is compiled to `lambda env, A: A[k](env[:dcall])` (l.285). The argument closure is re-run at every
   reference, **including every iteration of a loop inside the body**, although its value depends only on the
   call-site scope `env[:dcall]` and is therefore constant for the whole call. Memory programs become abstractions
   whose input is hole `?0` (`_to_body`, l.1060–1066), so every reference to the input inside a stored program's
   fold/filter re-executes the whole argument expression. In the frozen memory, **11 of 34 L→L programs reference
   their input inside a loop**; the largest (33 nodes) does so 5 times, at loop depth 2. Inventions `f5`
   `(foldlL (filter (not (eq b0 b2)) ?0) ?0 ?0)` and `f6` have the same structure.
3. **Nesting multiplies, pricing hides it.** A composition `m_a(m_b(m_c(m_d(x))))` costs only ≈ 4 × `$mem` (= 12) in
   the prior. With call-by-name its evaluation cost is roughly the product, over levels, of
   (loop length × references in the loop). Each level multiplies the cost by about `n` to `n²` for lists of length
   `n` (≤ 40 by `LEN_CAP`). Top-level first-order calls avoid this, because value mode (l.710–723) passes values.
   But inside the body of a higher-order parent (here a `foldr`) the closure path is used, over ~32 probe envs.

Termination: every loop runs over values of length ≤ 40, integers are capped, levels ≤ 80 and candidates ≤
200 000, so each task terminates in principle. Its cost, however, is exponential in the nesting depth of
re-evaluated calls. No statement about how long the last task needs is possible from this evidence.

## 4. Risk if the current run continues

The same mechanism is present in every remaining memory arm: rule C, C_no_inventions, C_no_learned_prior; dc B and
C (L→L / I→I tasks); oeis B and C (I→I memory, 1 of 11 programs re-evaluates its input in a loop). C adds `f5`/`f6`,
and under C's learned prior memory calls (cost 3) are cheaper than every invention (4–5), which favours exactly
these nested compositions. rule B: 123 tasks finished in 2 h 10 min, then 1–2 tasks have taken ≥ 91 min each. With 6
memory arms left, a repeat of this tail per arm is the expected case, not a worst case. A tail of unknown length
on any one task blocks the whole run, because `pool.map` returns only when every task of an arm is done. Per-task
rows exist only in process memory until the very end, so the expected exposure to a container loss grows with every
hour.

## 5. Recommendation: ABORT RECOMMENDED (not executed; awaiting the owner's decision)

Reason: the delay is not normal search cost. It is a measurable defect of the execution model, call-by-name
re-evaluation that the candidate budget does not meter, and it will recur in six arms. The question this run asks
("does experience → invention → new capability?") can be answered at a reliable cost only after that is fixed.

If stopped: record the run as **INCOMPLETE**. Surviving evidence is the rule A 25/125 and A4 34/125 log lines (run 1
and run 2 agree) and the inferred "B 124/125 tasks finished, count unknown". B's per-task rows are lost. Nothing is
FAIL, no PASS rule is changed, no verdict is inferred.

Option: keep the process until the owner decides. This costs nothing in evidence and may capture B's count if the
last task ends.

## 6. Re-design for an amended, checkpointed evaluation (to be pre-registered before any run)

**Semantics-preserving changes** (identical returned program and identical candidate count on every task; must be
shown exact on opened development data, as `classical_grid_fast.fit_all` was, before adoption):

| Change | Where | Why exact |
|---|---|---|
| **call-by-need holes**: evaluate a binder-free hole argument at most once per call (lazy, on first reference) and reuse it | `_template` l.282–285, `_comp_body` l.318–321, template `call` l.303–305 | pure substrate; lazy evaluation raises `Fail` at exactly the first reference where call-by-name would, so success/failure per env is unchanged |
| binder-free children of higher-order candidates read from the already computed `k.vec[i]` | `_cand` l.724–732 | same value, same env |
| per-primitive value memo `(prim, args) → value / Fail` | value mode l.710–723 | pure, deterministic |

**Semantics-changing changes** (alter which programs are found; they must be part of the pre-registered search
definition and apply identically to every arm):

| Change | Effect |
|---|---|
| per-candidate evaluation fuel (substrate steps): a candidate exceeding it is treated as failing on that env | bounds worst-case work; may change `Found` on tasks whose answer needs more work |
| per-task work cap (total substrate steps) in addition to the candidate cap | makes budgets compute-matched; changes reach |
| pricing memory/invention calls by their expanded size or measured work instead of a fixed `$mem = 3` | changes search order and therefore capability |

**Run infrastructure** (no effect on outcomes): per-task result rows appended to a JSON-lines checkpoint and flushed
after every task, so a restart resumes and skips finished `(family, arm, task)` keys. Per-task exception capture,
counted as failure. Exact cost metering per task: candidates, substrate steps, CPU seconds (`time.process_time`),
peak RSS. The interpreter version is recorded. Wall-time precondition: every arm is timed on an opened development
sample before freezing.

**Evidence status of a re-run.** The registered TARGET bytes have been opened by this run, and the outcomes rule
A 25 and A4 34 have been seen; no B, C, dc or oeis outcome has. An amended run on the same splits is therefore a
second run on opened targets. That is acceptable only with full disclosure, and with an integrity condition: under
the exact (semantics-preserving) changes alone, A and A4 must reproduce 25 and 34 exactly. If fuel is added, its
effect on A/A4 is reported, and any change counts against the amendment. A fresh, never-opened target is still
available for sequences: the 499 registered `oeis_reserved_unopened` A000 files. For lists no registered unopened
pool remains.
