# 2026-10-17 · NEUMANN 1 first actually TRAINED typed semantic coefficient kernel, with strong classical control

**EXECUTED & INDEPENDENTLY REPLAYED.** **Restricted positive evidence for learned numeric conjecture formation. NOT global Q3/Q4/Q7 passage. Q1–Q7 remain OPEN.**

## Motivation and new mechanism

Two frozen authentic real-source Qwen0.5B original→SMT attempts had generated 0 complete usable mathematical relations (RustHorn 0/13 and hard nonlinear CHC 0/48 checked). This time we implemented a **real trained semantic-content head**, not a prompt, natural-language theorem, syntax corrector or classical proof solver.

A 27-trainable-parameter float64 `torch.nn.Linear(9,3,bias=False)` maps an input consisting of **nine bilinear interactions** among *two original affine state-transition delta vectors* to three **learned** coefficients `(a,b,c)`. The conjecture is `a*x+b*y+c*z=0`. Numeric source-to-IR extraction only parses the transition clauses, not the goal, and deterministic compilation only rounds/reduces predicted coefficients. It never synthesizes a missing lemma itself. Training teacher: *exact classical cross product*. This is **supervised algorithm distillation within a preselected invariant language**, not free-form invention of new structure.

Training: 2,048 authored source-family A programs, 256 validation programs, both text programs parsed to source-derived IR; optimizer Adam lr .07, 273 steps, 27 trainable parameters. Frozen weight file SHA-256 **`49d89436443e92e3594aca4e094769d40c90138b838a89d5a8681b27cccc7d5d`**. The first source-family B dev run (seed 2026101703) showed 64/64 original four-Horn proofs, but its **goal disclosed the correct linear invariant equation**, weakening the evidence even though the model's extractor did not read that goal. This initial receipt is retained, NOT suppressed.

## Pre-registered stricter second holdout

[PRE-SOURCE REGISTRATION](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-learned-coeff-20261017/PREREG_SECOND_HIDDEN_GOAL.md) is frozen in commit **`5c26f64b8d4e057a3eb7a7cce17f7c52beaaa18a`**, BEFORE generating the second evaluation source texts. Second holdout seed `2026101704`, 64 unseen authored affine CHCs, 8-bit-sized integer deltas between -7 and +7, syntactic family B with renamed variables, explicit equality assignments and reversed addition operands. The **safety goal forbids a concrete unreachable single point**; it does **not reveal any invariant equation or coefficients**. The *semantic program family is still the same linear-affine structure*, so this is **not** an external independent source-family generalization claim.

The model file was SHA-pinned before this second holdout and was **not retrained or tuned**. Every proposed formula was substituted into each of the **4 untouched original generated Horn clauses** and refuted using native Z3; only all 4 UNSAT is counted as a certified whole-source proof. A zero invariant is rejected. False formula and altered source checks must fail.

| Equal-source-information route | Authentic new 64-problem synthetics full 4/4 Horn proofs |
|---|---:|
| **Trained neural coeff head** (frozen 27 weights) | **64/64 PASS** |
| Same architecture **untrained** (fixed random initial weights) | **0/64** |
| `x=0` fixed candidate baseline | **0/64** |
| **Strong source-derived classical cross-product nullspace solver** | **64/64 PASS** |

Measured median *candidate only* on this local CPU: **trained 91.04 microseconds**, exact classical **33.71 microseconds**; neural is **~2.70x slower** for candidate output, with training **1,113.218ms** extra previously incurred. Comparing these micro-latencies with complete Z3 prove times would be invalid, and energy/price unavailable. In particular **learned adds ZERO capability over strong classical on this family**. No 10x claim.

Built an actual first-principles **classical-first compute router** that examines source/typing, runs exact cheap symbolic method and independently verifies all original constraints *before* authorizing model inference. On the same 64 new problems: **64 certified, 0 neural calls**, median ~4.1ms per *full source parse + all 4 Z3 proof checks*. An unsupported eight-variable-style source returns **ABSTAIN**, not a hallucinated learned invariant. This is correct scoped decision architecture, not general CHC success.

## Integrity and reproducibility

Downloadable conversation artifact **`NEUMANN1_LEARNED_SEMANTIC_P0_20261017.zip`**, 71,702 bytes, SHA-256 **`9380018bd8d11bc6a316128db880a268940a4c1697e6fb60d2c1e20f87374b0d`**. It contains: full executable CPU learner and parser, frozen binary weights, fresh holdout runner, hybrid router, source-independent C/Python-Z3 proof verifier, 8 negative/positive tests, first source-goal-leakage developmental raw receipts, second holdout exact proof ledger, all 64 authored source texts, `audit.py`, complete SHA-256 manifest and README.

**ZIP CRC PASS**, **79/79** source file SHA entries PASS. Replayed in fresh independently extracted temporary directory: 64/64 source hashes correct, same frozen 27 weights, 64/64 recovered neural semantic coefficients and **all 64 × 4 = 256 original Horn rule proofs rechecked**. 2 forged audit claims (wrong weight hash, 65-of-64 success) **both rejected**. Independent regression test suite **8/8 PASS**, including source mutation, forged predicate, zero predicate and unsupported source rejection. Validation and training were carried out locally CPU, no expensive model API and no user payment.

## Scientific decision

**`TRAINED_TYPED_SEMANTIC_KERNEL_RESTRICTED_POSITIVE / STRONG_CLASSICAL_MATCHES_AND_IS_FASTER / NO_LEARNED_NECESSITY / GLOBAL_Q1–Q7_OPEN`.**

Important: bilinear features, an exact classical teacher and this simple affine program distribution already embody sufficient mathematical structure. Discovering a new hard-source invariant operator family, safe nonlinear Horn proof DAG and frontier-class problem efficiency remains unproven. The training/test *syntax* differs but semantic mechanisms are shared. **Do not scale the 27-weight head or claim Q3/Q4 closure.** The correct high-value next branch is a source-group-independent learned *relation-family invention* study only where the best classical synthesis has actual headroom, with original full-proof validation and cost. Q7 remains provider-evidence-blocked.
