# NEUMANN 1 / FGSR-Q3 · trained numerical invariant component on actual external source

**2026-10-17 KST. Genuine training and source-level original proof. Exact scientific verdict: `TRAINED_NUMERIC_INVARIANT_COMPONENT_CAUSAL_ON_OPENED_REAL_CHC / HUMAN_SCAFFOLD_NEEDED / CLASSICAL_EQUAL_AND_CHEAPER / GLOBAL_Q1–Q7_OPEN`.**

## Why this differs from older artificial successes

Former Q3 source-to-SMT frozen Qwen0.5B failed on two authentic source families; former 27-weight *linear* and 18-weight *quadratic* numerical heads achieved synthetic-only original proofs but stronger classical solvers were better. Recently an authentic public CHC-COMP `square_twice_safe.c-1_000.smt2` received a complete *researcher-authored* 9/9 original proof after native Z3 timed out. This study attempts to replace **one substantive polynomial coefficient segment** of the human-authored proof with values from actual trained source-conditioned neural weights, without pretending the whole certificate was automatically invented.

## Mechanism actually built and executed

- A fresh **15 genuinely trainable float64 parameters** implement `Linear(3,5,bias=False)`. Three input features come from the actual original SMT program's recursive relation: `remaining' = remaining - 1; accumulator' = accumulator + k*bound + m*remaining + n`. The frozen output is the five coefficients `(A,B,C,D,E)` of the researcher-specified accumulator grammar `accumulator=A*bound²+B*bound*remaining+C*remaining²+D*bound+E*remaining` for entry `accumulator=0; remaining=bound`. The neural output is rounded but **never replaced with exact symbolic coefficients**. This grammar was chosen by a researcher and labels supplied from classical summation, not learned operator invention.
- Actual trained samples **1,024**, independent validation **256**, Adam **226 updates**, optimizer-only training **66.757ms**, validation max abs coefficient error **6.80e-5**. CPU `torch`, random seed `20261017091`; checkpoint SHA256 `cc2b34773dd095b7980fa6365518714d896e69a64dd38a37e34cf522a64cc3e6`. [Frozen 15 weights and receipt](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-learned-real-loop-20261017/FROZEN_LEARNED_15_WEIGHTS_AND_RESULT.json).
- Same-family coefficient-disjoint synthetic 64-case holdout: **64/64** symbolically inductive learned coefficients; same-information exact classical summation **64/64**, zero coefficient baseline **0/64**. This is NOT independent external source-family validation.
- Authentic public original `chc-comp/chc-comp26-benchmarks` upstream `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, `eldarica-misc/LIA/llreve/square_twice_safe.c-1_000.smt2`, **9 original Horn rules**, SHA256 `f62d0fb72140e6bd7e953dcebd131a4e9498cc9c0c150588ca79944962e9e748`. The source had **already been read for the prior researcher-authored full proof before this model was developed**. This is OPENED development, not blind transfer.
- A fresh typed SMT S-expression parser with algebraic guard extraction independently discovers three original self-loop recurrence rules for `inv_main22` (rule 2, bound position 2), `inv_main8` (rule 3, bound position 1), and `inv_main13` (rule 5, bound position 1). Each source-derived tuple `(k,m,n)=(1,0,0)` was independently checked to be **absent from both 1,024 training and 256 validation feature vectors** (new within restricted arithmetic family; no new operator kind).
- Frozen neural head independently outputs **`(1,-1,0,0,0)`** for each of these three original recursive clauses, representing the **actual content** `accumulator=bound*(bound-remaining)`.

## Authentic, independent nine-clause proof, and ablation

Crucial deliberate boundary: the complete five-predicate certificate **scaffold is taken from the PREVIOUSLY HUMAN-AUTHORED source-specific proof**: it contains relation equalities, loop bounds, the total `max(0,a²)`, and the cross-predicate alignment. **None of these were inferred or invented by the neural network.** The model supplies only the three local polynomial accumulator coefficient vectors. A source AST parser and a native C libz3 SMT verifier are separate from the model and analyze ALL **unchanged** original 9 source clauses with freshly constructed solver contexts.

| Exact same original and full hand-provided scaffold | Whole authentic 9-Horn original proof |
|---|---:|
| Learned-coefficient head (15 trained weights) | **9/9 UNSAT PASS** |
| Strong exact symbolic closed-form summation on same three extracted deltas | **9/9 UNSAT PASS** |
| Ablation: zero all learned numerical coefficients, same scaffold | **1/9 UNSAT; original clause 2 SAT; REJECTED** |

Native libz3 version **4.13.3**; 10 separate positive/negative regression tests PASSED, including original source SHA and checkpoint pin, changed source transition, forged terminal equality, zero coefficient ablation, full 9-rule real verification, and source-independent synthetic recurrence examples. Separate audit confirms all source-level receipts plus unique synthetic 64/64. Single-run candidate-only total learned ~**20.620µs** across three coefficient vectors, exact classical ~**2.773µs**, and **~116.9ms complete local original loading+AST extraction+all three verification arms**. Tiny timing differences are noisy, no robust ratio, solver/version/environment comparisons require equal conditions. Training cost is additional. All 9 original clauses were also previously proved using no model by the human-authored certificate, so the real source presents **NO evidence of learned necessity over strong classical**.

**Reproducible artifact:** `NEUMANN1_REAL_LEARNED_COMPONENT_GATE_20261017.zip`, 16,150 bytes, SHA256 **`fde973a62a0f6b909419287244a089402987592d7fa0b9de7816fb4741a633b7`**, 11 authored files; manifest/ZIP CRC/audit/10 tests pass. Contains actual training code, frozen 15 weights, synthetic 64 cases ledger, independent source AST extractor, native Z3 verifier, human-authored scaffold plainly shown in code, exact benchmark source SHA fetch link (the external raw text is not redistributed), original 9/9 neural/classical/zero-ablation receipts, regression tests and accounting checker. Users can reproduce by fetching pinned source via `native_runner.py`.

## Admission boundary

**ADMIT ONLY:** a truly trained coefficient head can causally supply one useful numeric part of a fully certified genuine external program proof; its exact `(k,m,n)` input tuple wasn't in training or validation.

**NOT ADMITTED:** autonomously inventing the invariant grammar, multi-predicate relational semantics or cross-predicate scaffolding; fully learned proof of a completely unseen real program family; superiority over exact classical; 10× cost advantage; frontier-level Q1–Q7. The particular problem was OPENED before training and there was still posthoc human scaffold. No misleading semantic transfer or true Q3 passage.

**NEXT high-value action:** stop training on exact polynomial coefficient extraction because exact classical is better. Future neural effort only merits a clean **new real source-family heldout** and model actually proposing previously unknown relational **operator structure**, without a posthoc human-supplied certificate, followed by full original verification and matched strongest classical alternative.
