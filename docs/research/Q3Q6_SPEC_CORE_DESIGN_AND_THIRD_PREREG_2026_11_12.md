# NEUMANN 1 | Specification-space core: design, SOURCE-only development evidence, pre-registration of THIRD
2026-11-12 | Plan `third`: BINDING from its freeze commit (§6) | SECOND verdicts: FAIL, sealed, unchanged | Global Q1–Q7 OPEN

Authority: [Frozen North Star](frozen_north_star.md); the owner's instruction of 2026-11-12 (keep SECOND's FAIL and
all evidence immutable; do not run FRESH with the old core; design a state-representation and operation-generation
mechanism distinct from macro compression; show added capability on development data against an
invention-removed control, a strong classical baseline and an equal CPU budget; do not open FRESH before an
independent verification is significant; change no existing gate).

## 0. What is fixed

* SECOND: every verdict stays as computed (P2 rule/dc/oeis FAIL, Q3 scoped FAIL, #745 gate FAIL). The evidence
  files are sealed by SHA-256 in `docs/experiments/second_evidence_seal.json`; `tests/test_second_evidence_seal.py`
  fails on any byte change.
* FRESH (499 OEIS A000 reserve) and the 1 000 A001 files: not fetched, not opened. The same test asserts that no
  `fresh` freeze, rows or result exists.
* The old invention core (`invention_core.py`, memory, macro inventions, learned prior) is not modified and not
  used by the new mechanism except for its substrate and forward enumerator.

## 1. Why SECOND failed, from first principles

A macro abbreviates a fragment of programs that were already reachable. It re-weights the same
generate-and-test search; it does not change what is searched or what each candidate is tested against.
SECOND measured this: on the rule family the core with inventions solved 28, without inventions 29, the
4×-candidate classical search 34, and the memory arms did about 10× the work per candidate.

Generate-and-test uses the examples as a pass/fail bit per candidate. The examples contain far more: where each
output element comes from, which positions are kept, how one term follows from the previous ones. A search that
ignores this pays for a program of size s with about b^s candidates. If the examples are used to split the problem
into parts of sizes s₁ … s_k, the cost is about Σ b^(s_i). That difference is the computation that need not be
done (North Star §2: Problem → Structure → Minimal Sufficient Representation → Eliminate → Cheapest Sufficient
Compute → Verify).

## 2. The mechanism (`neumann1/spec_core.py`)

### 2.1 State representation

1. **Specification space.** A task is a specification: the vector of required values over the examples. The
   solver state is a table of goal vectors. Every value the forward enumerator keeps is looked up in that table
   by hash, so a goal costs nothing per candidate.
2. **Observable maximal traversal state.** A list→list task is re-represented as a traversal. At position j the
   state is (element, index, remaining count, reversed input prefix, input suffix, whole input). Every component
   is read from the examples, so the step operator is searched with one supervised example per position instead
   of one per list. Two alignments are derived from the data: equal lengths (the step returns the output element)
   and subsequence (the step returns keep/drop). The solved body names the components it needs: the minimal
   sufficient state is an output of the search, not an input.
3. **Sequence as a self-referential object.** An integer sequence on consecutive indices is re-represented with
   its own history as state; a(n) is searched as a function of (n, previous terms), again with one supervised
   example per term.

### 2.2 Operation generation

1. **Inverse operators are derived, not written.** `derive_inverses` poses, for every first-order primitive and
   argument position, the task "recover this argument" on self-generated data and solves it with the system's own
   enumerator (counterexample-guided: a candidate that fails on fresh samples adds them to the sample). A
   primitive that is not injective on perturbation tests is rejected. No task data is used. Result
   (`docs/experiments/results/spec_core_inverses.json`, 1.6 CPU s, reproduced by a test):

   | Primitive | Derived inverse |
   |---|---|
   | cons(a, b) = c | a = head(c); b = tail(c) |
   | add(a, b) = c | a = sub(c, b); b = sub(c, a) |
   | sub(a, b) = c | a = add(c, b); b = sub(a, c) |
   | mul(a, b) = c | a = div(c, b); b = div(c, a) (partial; re-application is checked) |
   | not(a) = c | a = not(c) |
   | range(a) = c | a = foldrI(λ. acc + 1, 0, c), i.e. length: an operation that is not in the substrate |

   mod, div, head, tail, eq, lt, isnil were rejected as non-injective.
2. **Backward steps.** A list goal is decomposed by the derived inverse of cons into head goals and a tail goal,
   repeatedly; the task is solved when a prefix of head goals and one tail goal are all in the forward bank. An
   integer goal g gets, for each early bank value v, the goals op⁻¹(g, v). Every backward step is verified by
   re-applying the primitive.
3. **Step operators.** Index-aware maps, positional filters and recurrences are synthesised per task under
   per-step supervision. They are not sub-trees of earlier programs and there is no memory of earlier tasks.

### 2.3 Designed by the developer vs generated by the system

| Designed (general, task-independent) | Generated by the system |
|---|---|
| substrate and forward enumerator (unchanged from `invention_core`) | the inverse-operator table (§2.2.1) |
| goal table; backward application of whatever inverses exist | every goal and sub-goal of a task |
| the traversal state and the two alignments; the history state | which state components are used; every step operator |
| CPU split: 40 % of the cap for traversal sub-tasks first, the rest for the goal-directed main search | every solution program |

### 2.4 How this differs from macro compression

| | Macro compression (SECOND core) | Specification-space core |
|---|---|---|
| Source of new operations | sub-trees of programs already solved | inversion of primitives on self-generated data; per-step synthesis |
| What is searched | whole programs | sub-specifications |
| Supervision per candidate | 8 whole examples, pass/fail | one equation per position / per term; exact goal match |
| Search space | larger library → larger branching | library unchanged; no memory, no cross-task learning |
| Needs solved tasks first | yes | no |

### 2.5 Prior art (no novelty is claimed for the ingredients)

Inverse semantics and deductive decomposition (FlashMeta witness functions; λ² deduction rules for map/filter/fold),
counterexample-guided synthesis, and analytical inductive programming are established. In those systems the
inverse rules are written by hand; here the first-order inverses are derived by the system. What is tested below
is only whether this design adds solving ability at equal CPU, and which component is responsible.

### 2.6 Deleted by ablation

Case analysis (two partial solutions joined by a bank predicate) was implemented and removed. On rule SOURCE the
solver solved 57 with it and 57 without it; on OEIS SOURCE it produced 11 wrong fits. North Star §5: a component
whose deletion does not worsen the system is deleted.

## 3. Development evidence (SOURCE only; not evidence for any gate)

Data: the SOURCE splits of the FIRST registry (rule 125 list functions, OEIS 187 usable sequences). No TARGET
byte and no reserve byte was read in development (`research/q3/dev_source.py` can reach SOURCE paths only).
Every arm has the same cap of **6 CPU seconds per task**, everything included; `A@4` has 24 s.

| Arm | Definition | rule SOURCE solved / 125 | CPU s (total) |
|---|---|---|---|
| A | frozen forward enumerator (all new components removed) | 22 | 616 |
| A@4 | the same with 4× the CPU cap | 26 | 2343 |
| S | specification-space core | **57** | 405 |
| S_no_state | S without traversal state and step operators | 37 | 506 |
| S_no_inverse | S without the derived inverse operators | 46 | 463 |

* S vs A (equal CPU): S only 36, A only 1; exact McNemar p = 5.5e-10.
* S vs A@4 (baseline has 4× the CPU): S only 32, A@4 only 1; p = 7.9e-09.
* Component ablations: S vs S_no_state 21 / 1 (p = 1.1e-05); S vs S_no_inverse
  11 / 0 (p = 9.8e-04).
* S solved by: zfilter 27, chain 15, zmap 13, search 2. TRAIN fits 63, of which 57 generalise to the 24 hidden tests.
* **Computation eliminated.** On the 32 tasks that S solved and A@4 did not solve in 24 CPU s, S needed a
  median of 0.014 CPU s (maximum 2.5 s, 21 s in total). The baseline spent
  771 CPU s on the same tasks without solving one. On the 21 tasks both solve, S used
  6.1 s and A 12.0 s.
* **Why.** Programs found through the cons-inverse chain have 3 to 30 substrate nodes (median 13). Measured on a
  SOURCE task, the forward enumerator completes cost level 7 in 6 CPU s (99 000 candidates) and level 8 in 24 s
  (532 000), growing 5–7× per level. Extrapolated, not measured: a 13-node program needs about 10⁹–10¹⁰
  candidates and a 30-node program more than 10²⁰. The decomposition reaches them with a few hundred to a few
  hundred thousand candidates because each sub-goal has 1–7 nodes.

OEIS SOURCE (187): A 8, S 15, classical specialist D (finite differences + Berlekamp–Massey)
**33**. S solves 3 sequences that D does not; D solves 21 that S does not. The
mechanism does not beat the specialist on sequences, and no such claim is made.

Limits seen in development (stated before THIRD):
* The design was tuned on rule SOURCE, which comes from the same generator as rule TARGET.
* Unsolved classes: outputs that are neither aligned with nor a subsequence of the input (interleaving, ranges,
  reverse-and-append), rules that need an aggregate inside the step (counts, sorting), conditionals on the whole
  list.
* A wrong traversal fit can pre-empt a correct forward solution (1 SOURCE task).
* CPU caps make outcomes at a stage boundary time-dependent. No S or A solution on SOURCE came after 80 % of
  the cap, but S_no_inverse solved 45 in one run and 46 in an identical second run.
* Full rows: `docs/experiments/results/spec_core_dev_source.json`.

## 4. Pre-registration of the THIRD evaluation (independent of development data)

**Disclosure.** THIRD runs on the TARGET families whose bytes FIRST/SECOND already opened: rule TARGET (125),
dc (217, 199 usable), OEIS TARGET (250, 178 usable). It is **not first-exposure evidence**. What the developer
knew when designing S: the SECOND aggregates per arm (rule A 25, A4 34, B 29, C 28; dc A 115, A4 129, B 95, C 119;
oeis A 4, A4 6, C 5, D 25), nine C-exclusive program strings (rule/c066; dc/007, 010, 096, 098, 141, 142, 169, 187),
and the full content of rule SOURCE and OEIS SOURCE. No TARGET task content was read. Channels: rule TARGET is
in-distribution with the development data; dc is by different authors and was never used in development; the
OEIS result of SECOND (D 25 vs C 5) motivated the history state.

**Arms** (cap 6 CPU s per task, `A@4` 24 s; code, table of inverses and caps pinned in the freeze file):
rule and dc: S, A, A@4, S_no_state, S_no_inverse. oeis: S, A, A@4, D.

**Rules** (computed by `research/q3/spec_eval.py`, fixed before the run):

| ID | PASS rule |
|---|---|
| V_f for a family f | solved(S) > solved(A) and solved(S) > solved(A@4); exact two-sided McNemar p < 0.05 against both; ≥ 5 tasks solved by S and by none of A, A@4 (and D on oeis); total CPU(S) ≤ total CPU(A) |
| THIRD gate | V_rule and V_dc |
| Component necessity (reported per family, not gating) | S > ablation with McNemar p < 0.05 → SHOWN, else NOT_SHOWN |

* A is at once the equal-CPU strong classical baseline and the control with every new component removed.
  A@4 is the same baseline with four times the CPU.
* V_oeis is computed and reported. **Stated in advance: it is expected to FAIL** (development: S 15, D 33). It is
  not part of the gate, and the scope of any claim is list-transformation families.
* Reported, not gating: how S solved (chain / zmap / zfilter / rec / inverse / search), TRAIN-fit precision,
  S CPU on tasks A@4 failed, CPU on tasks both solve, solutions found after 80 % of the cap, the frozen SECOND arms
  on the same tasks, and SECOND-A4 solutions that A@4 missed (expected 0).

**Policy.**
* Single attempt per (family, arm, task); checkpointed rows are committed while the run proceeds.
* Unresolved rows (error / timeout / died / not run) are never auto-failed: PASS iff the rule passes when every
  unresolved S row is unsolved and every unresolved rival row is solved; FAIL iff it fails under the reverse
  completion; otherwise INCOMPLETE.
* If the machine restarts, the evidence and the loss are reported first; the run resumes with the identical
  command (recorded keys are never re-run) after the owner's go-ahead.
* No rule is changed after an outcome is seen. A FAIL is kept. SECOND's verdicts are not affected by any outcome.

**What a PASS would and would not mean.**
* THIRD gate PASS = on one in-distribution held-out family and one cross-author family, the specification-space
  core solves significantly more tasks than classical enumeration given equal and 4× CPU. Evidence for Q1 and Q3
  in the North Star sense (structure found without an oracle reduces computation) at this scope.
* It would not be first-exposure evidence, would not establish Q5, Q6 at scale or Q7, and would not make S a
  general solver: it covers list transformations whose structure is positional, element-wise or a short
  recurrence.
* A PASS makes a first-exposure test worthwhile. FRESH stays closed until the owner decides.

## 5. FRESH

Not opened. Note for the owner's decision: the FRESH reserve is OEIS sequences, where development shows the
specialist D ahead of S. A first-exposure test of this mechanism needs a never-opened list-transformation family
registered by blob hash before any byte is read. That registration is not part of this pre-registration.

## 6. Freeze record

| Plan | Freeze file | freeze_sha256 | Commit |
|---|---|---|---|
| third | `docs/experiments/spec_third_freeze.json` | `cab062fc…cad7` (2026-11-12T05:27:37Z) | the commit that adds the freeze file; pushed before launch |
