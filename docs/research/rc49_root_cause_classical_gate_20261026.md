# RC49 — NEUMANN 1: RC48 root-cause autopsy, delete redundant neural computation

2026-10-26. RESEARCH DRAFT. All global Q1–Q7 OPEN. This is a retrospective factual diagnosis, not a new blind validation.

## Fatal first-principles mismatch

RC48 `feat(codes)` reports the number of distinct opcodes and matching opcode pairs by index in three observed length-3 programs. Human-authored `compression_gain(codes,k)` rewards exactly the index where three codes differ and the other indices match. The learned 8→24→1 net, trained for 750 updates, is thus attempting to re-learn a trivial deterministic predicate ALREADY explicit in its feature vector. Classical anti-unification finds it in O(3 × 3) equality comparisons; this is not evidence of invented semantic machinery.

RC48 initial cross-ISA FAIL came from choosing just one syntactically source-fitting program, discarding functionally equivalent alternatives. RC48b fixed this using human-coded full source-consistent version-space enumeration (7³=343 programs for each source task), after seeing the first failure; the trained and strong classical selectors then produced exactly the same grid macro. 13/30 never-trained random models also passed the scoped criteria. This is a lack of unique neural contribution, not evidence to increase model size or training steps.

Measured original RC48 median CPU:
- Direct classical: **4,313,025 ns** for 4/4 retrospective synthetic task outcomes.
- Full classical version-space + macros: **21,597,372 ns**.
- Trained neural + classical source work: **579,767,046 ns**.
- Median training charge **535,997,649 ns**, **92.45%** of total neural; remaining neural path still **~10.15×** direct CPU.
- No joules, true start-up, VRAM/RAM peak or monetary cost were measured. Do not infer energy or whole-resource ratios.

## Executed RC49 correction

Created a **no-Torch/no-NumPy** deterministic fail-closed source candidate routing implementation in downloadable archive:
`NEUMANN1_RC49_FAILURE_AUTOPSY_CLASSICAL_GATE_20261026.zip`
SHA256 `76e506c371dd9446f8ed0cd384dbaee1925cf9813a1280a51977a6f481642fb7`.
Full archive contains original untouched RC48 public four queries, separate original RC48 gold for retrospective scoring, `rc49_core.py`, `test_rc49.py`, `audit.py`, README, SHA manifest and clean replay script. Fresh extract `bash REPRODUCE.sh` passed **7/7 SHA checks** and **5/5 pytest**.

Retrospective four-query CPU timings in an original 7-repeat run, process time only: direct first-fit candidate evaluation **217 total**, median **4,092,659 ns**. Exhaustive source agreement **1,372 candidate evaluations**, median **21,165,702 ns**. Independent clean ZIP extraction replay measured median 4,112,467 ns and 21,765,601 ns respectively; run-to-run clock drift acknowledged. BOTH **4/4** original grader outputs, ZERO neural forwards. Exhaustive within-grammar source-compatible predictions agree on each of 4 query outputs; **NOT a proof of correctness for new or bigger grids**. Adversarial all-zero source evidence correctly returns `HOLD_UNDERIDENTIFIED`; unsatisfiable bounded grammar `HOLD_SCOPED_REPRESENTATION_EXHAUSTED`; finite work cap `HOLD_CLASSICAL_BUDGET`; malformed task returns UNKNOWN. All HOLD outcomes have `authorize_neural=False`.

Crucially, full consensus is **5× slower** than first-fit on this workload and is selected for scoped uncertainty checking, not for speed. No global NEUMANN A/B/C or 10x speedup.

## New research admission rule: no model where strong classical suffices

1. PRECHECK a cheap executable/provable classical candidate on the actual original task under the stated budget.
2. Do not train to predict a property already provided in human features, source equality, program semantics or a cheap deterministic library.
3. Stop attempting to turn fixed 3-opcode SLOT toy families into evidence of general invention.
4. If classical cannot satisfy budget, record **which** strong and equal-rights baseline failed, its cost and actual independent reference capability; a finite DSL miss is NOT proof that classical mathematics in general cannot solve the task.
5. Invoke neural *research*, never deployment authority, only for a **meaningful bounded capability/cost gap** and a feasible independent verifier/proof. Let it propose SEMANTIC transformations and new reusable concepts in a general typed program representation; classical search/SMT/e-graphs may validate, canonicalize and compile.
6. Before examining another-domain labels, freeze own trained model, problem identities, first proposals, no-learn/shuffled controls, full cost caps and the same tool rights. C means discovery method itself generalizes to independent semantic tasks, not just applying one recorded macro to new surface data.
7. Charge training, inference, failed search, verification, memory, external frontier calls, retries and amortization. Preserve FAIL/UNKNOWN. Any claim of 10× full system advantage must use matched useful capability and measured total resources.

**Next high-value experiment is NOT another engineered three-token toy.** The open problem is an independently authored task where a strong classical portfolio stalls under declared budget, a learned policy genuinely changes the hypothesis/representation space, that change solves verified cases inaccessible to the bounded baseline or earns a measured full-cost advantage, and the same discovery policy transfers without adaptation to a third author/domain.

Global Q1–Q7 remain OPEN; this PR closes only the narrower **root cause / unnecessary-model decision**.
