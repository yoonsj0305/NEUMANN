# NEUMANN 1 | Q3 oracle-free source-consistency learned operator AST: new frozen holdout + real source abstentions

**2026-10-17 KST | CPU-only | REAL verdict: `LABEL_FREE_LEARNING_SYNTHETIC_29_OF_29_REPLAYED / STRONG_CLASSICAL_29_OF_29_FASTER / EXTERNAL_FAMILY_0_OF_2 / ALL_Q1–Q7_OPEN`.**

## Real new mechanism tested, with strict authority boundary

Prior **126-weight supervised AST** achieved 70/70 source-generated symbolic proofs on new 3–4-leaf combinations, but training had explicit *seven-bit classical AST answer labels*. This new experiment removes those answers from the learner's training loss entirely. **Exactly 126 real float64 PyTorch weights** are optimized solely for reconstructing the **17 source-extracted transition deltas**, after deterministic classical QR of the transition signatures of the same **seven already-specified AST primitives**. No gold symbolic answer, safety clause, generated graph label or verification certificate is used as a training target.

This source consistency loss is `mean((Q @ NN(normalize(source_delta)) - source_delta_scaled)^2)`; the numeric outputs are decoded through the frozen classical upper triangular R into seven operator inclusion coefficients, threshold .5. **Crucial limitation:** the operator list, addition combinator, and QR/R preconditioner are given by the researcher. This is **label-free compositional parameter learning**, **not invention of a novel primitive or operator grammar**. QR computes much of the mathematics, and an equally informed exact classical method can solve it directly.

[PRE-HOLDOUT GitHub frozen contract](https://github.com/yoonsj0305/NEUMANN/commit/8abd4024efed0350791a3e1975d71b78b0799f6f) disclosed prior **development** comparisons (naive reconstruction 22/70 and QR variant 35/70 on already opened 3–4-leaf tests). The single chosen QR variant was then trained with **only 28 synthetic train source texts**: 7 one-leaf plus 21 two-leaf, without reading their generator graph labels into the gradient. Actual PyTorch LBFGS 123 closure calls, **28/28 train graph match posthoc**, optimizer-only wall **62.544ms** excluding synthesis/imports. Binary `FROZEN_LABEL_FREE.npz` SHA256 **`e43208341dba128ba4c853ab42abe7ad8bd12ffdc292b1649ca0eb0eb74465ff`** saved before evaluation source generation.

## New untouched synthetic split AFTER freeze, original three-Horn whole proof

Exactly the full set of **29 distinct 5-, 6-, and 7-leaf mathematical compositions** in synthetic source family B, seed `20261017071`, no overlap with any 1- to 4-leaf dev/training graph; forbidden-state goal does NOT disclose theorem equation. Inferred model's **operator AST matched 29/29**. Independent native Z3 **4.13.3.0** checked source initialization, transition induction, and unsafe goal for every exact original 3-rule source.

**Preserve BOTH receipts:**
- **First immutable run, hard per-clause 1300ms cap:** trained learned **28/29 certified**, strong exact classical **28/29**; one IDENTICAL correct operator graph had transition obligation **`unknown` due SMT cap**, NOT SAT or a proof failure. Random untrained identical head **0/29**.
- **Fresh re-extracted, independently replayed all 29 sources with solver cap 7000ms and UNCHANGED original bytes/candidate/checkpoint:** trained **29/29**, strong classical **29/29** with **all 87/87 original Horn negations UNSAT**. The single previously UNKNOWN clause is UNSAT with a longer finite check; receipt records that first result separately and does NOT rewrite it.
- **Falsification 3/3 PASS:** remove a needed AST leaf => original transition SAT; change source safety goal to an actually reachable forbidden state => source false rule SAT; forge frozen checkpoint SHA => rejected before proof.
- Same-information candidate-only measured median Python CPU **trained 604.056 microseconds**, strong classical exact least-squares **82.772 microseconds** (classical **~7.30× faster in this scoped implementation**, excluding parsers/SMT and QR preparation). Neural optimizer overhead is additional. **No overall 10× advantage**, no monetary/electricity claims.

## Two genuinely different REAL external source groups preregistered

These paths were registered in same commit **before inspecting their source bodies**; upstream genuine CHC-COMP 2026 frozen at `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`.

| First genuine external target | Exact upstream Git blob SHA1 | Real original structural facts | Untouched frozen learner disposition |
|---|---|---|---|
| `hopv/lia/mochi/sum_intro_000.smt2` | `89fc6781b89f5659015d1cfaecc7ef3b835afbad` | 2 relations, 4 original assertions | **ABSTAIN_UNSUPPORTED_RELATION_COUNT** |
| `eldarica-misc/LIA/llreve/square_twice_safe_weaved.c-1_000.smt2` | `dc17fa1ff2d7a68f905c2eaa7725f9bafec3046b` | 5 relations, 9 original assertions | **ABSTAIN_UNSUPPORTED_RELATION_COUNT** |

The frozen `source_probe` admitted **EXACTLY one two-Int relation and three original assertions**; no user-authored transformation from these external programs into synthetic shapes, no output model calls, no theorem assertions. **Actual full different external source-family learning transfer: 0/2**. Neither external source is included in package; identities come from the pinned GitHub upstream file fetch. The fact that those sources require a multi-predicate **relation graph** and source-neutral proof context is an **architecture blocker**, not evidence the external math is unsolvable.

## Replay archive and clear STOP decision

**Real downloadable archive:** `NEUMANN1_LABEL_FREE_SEMANTIC_OPERATOR_LEARNING_20261017.zip`, **37,418 bytes**, SHA256 **`43fca30bfbab49a0eb2c137408c2599b2c04bad9321080f163f92b2c38ef396a`**. Includes exact teacher-label-free training source, prior restricted original source engine, 126-weight frozen checkpoint, first frozen result, full exact source text for **29 authored synthetic original SMT2 programs**, independent original proof replayer, two actual external source identifiers, all model/classical per-source records and original audit. Archive CRC PASS, **37/37 immutable file SHA256** validated after new temporary-directory extraction, and `python audit.py` successfully independently re-executed **87/87 original Horn obligations** and **3/3 falsification controls**.

**Scientific admission: `SYNTHETIC_ORACLE_FREE_CONSISTENCY_COMPOSITION_PASS` only.** Because the classical QR operator basis and the 7 types were preselected and classical solves all source cases faster, this does not prove learning is mathematically needed. No new operator-kind invention, genuinely external family transfer, frontier comparable Q7, or global Q3 gate closure. North Star continues *frontier-level problem solving with minimum necessary computation*. **STOP scaling fixed-leaf toy studies**. Next legitimate first-pass architecture must emit *new cross-predicate relation-operator AST* from a general source graph on unseen actual external source families, then pass independent full-original certification and strong classical/Cegis equal-information cost baseline. All Q1–Q7 **OPEN**.
