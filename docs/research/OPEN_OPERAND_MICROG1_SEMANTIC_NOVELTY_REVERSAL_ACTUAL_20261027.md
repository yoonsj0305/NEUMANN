# NEUMANN 1 | Open-operand micro-G1 causal study and **semantic novelty reversal** — 2026-10-27

> **FINAL SCIENTIFIC VERDICT:** `SYNTHETIC_REPRESENTATION_OR_TRANSFER_FAILURE`; `FALSE_NOVELTY_CAUGHT_BY_FULL_DOMAIN_SEMANTIC_AUDIT`; `Q1–Q7 GLOBAL OPEN, G1 HOLD, G2 NOT RUN`.

This is an actual CPU-trainable ownweight model study and a separately executed post-first finite-domain audit, NOT a novel general intelligence, external benchmark, new basic primitive, frontier parity, or 10× system advantage.

## 1. Chronology, preserving negative results

1. Frozen source-free protocol [here](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/docs/research/OPEN_OPERAND_UNSEEN_COMPOSITION_CAUSAL_PREREG_20261027.md), **pre-run amendment** at GitHub `8a697ff4d17ef320c5c0436a933fe9f6c43380df`. Six fixed typed two-op families: AX, XA, AR, RA, XR, RX. A=ADD mod256, X=XOR, R=8bit rotate left, parameters: ADD/XOR 0..255, R 1..7. Train only AX/XA/AR/RA/RX; test syntactically absent XR. Training constants 0..127, test 128..255. This is programmer-created **synthetic tasks**, not unseen external authors.
2. Full local executable Python `experiment.py` SHA256 **`47448b8662af9db7e57105ce9d1bcab538355b54d0b8d0a52be9586a59ccd22d`**, 5/5 engineering tests PASS, **frozen before model training** by GitHub commit `9719804b9f58974d14121c8aa882ba36414962d6`.
3. Actual PyTorch 2.10.0+cpu, no GPU/API: model MLP source-IO bit encoding → independent operation-type heads, source-only classical inverse-fits arbitrary operands; no fixed complete-program retrieval. A trained on true source-program type; B same model, 22 epochs/seed and shuffled per-example type labels, seeds **[3,7,11]**, 2,400 author-generated training tasks. Note **B is shuffled supervised targets, not online reward-shuffle RL**. 160 transfer + 160 known-family test tasks, six source input-output examples, next six **future inputs only** used before grade.
4. FIRST learned A/B program-type ranking lists serialized with **no future output labels**: `FIRST_PROPOSALS_PRE_GRADE.json` SHA256 **`1901f00cb24851532162507543cab0d84ecdc0205ae2733ad4cc88bcee93ba0d`**, immutable GitHub pre-grade seal commit `8c8ddd4c6d5bab3734e49861a1de9777d9878928`.
5. Original brute-force grading repeated identical classical inverse tasks for arms/seeds and timed out before creating a grade receipt. **POST-FIRST** grading-only cache `grade_postfirst_cache.py` used the identical source-only inverse solver once per task/pair; source and output candidates unchanged. Development-source equivalence test **9/9** across 1/3/6 proposal bounds PASS. First SHA/first code SHA verified. Post-first grade `POSTFIRST_GRADE_CACHED.json` SHA256 **`df35fc8b5f98993ddb19793d7b30b431ab8505f5d83d8d56949a0e09461fbc9c`**. Runtime of this cache judge is not equivalent to separate A/B/C production cost, so report proposal-count cost, not a comparable end-to-end wall-time result.
6. **POST-FIRST semantic quotient audit** found a decisive benchmark-design defect. All allegedly unseen `XR` functions are equivalent to already-trained `RX` functions by the exact identity:

   `ROL_8(x XOR c, r) = ROL_8(x,r) XOR ROL_8(c,r)`

   For every `c` in 0..255, `r` in 1..7, ALL 256 byte inputs were exhaustively checked: **1,792 program identities × 256 inputs = 458,752 point comparisons PASS**. `POSTFIRST_SEMANTIC_QUOTIENT_AUDIT.json` SHA256 **`8f5f3f983facc4ad78736c9b759c6db4165c8996800d694f8a65de1cef4e1b14`**. **0/160** heldout task functions semantically new versus RX, although program text had withheld order XR.
7. To ensure the equivalence is not a special cherry-picked RX witness, an independent **full finite library index** enumerated **ALL 136,448** two-step programs from training families using every legal operand (not just those seen in training). It found **68,836 distinct full-domain byte functions**; all **160/160 XR target functions appeared in existing library**. Two independent controls, BIT_REVERSE8 and `x XOR (x >> 1)` (Gray transform), were correctly **absent** from this narrow finite library. `POSTFIRST_FULL_LIBRARY_EQUIVALENCE_INDEX.json` SHA256 **`084701a0415ce608c10f1f77d6d0551e62f4a7b42c3ccef7a33420f3df78efae`**. Hash-collision caveat: SHA-256 fingerprints; positive matches additionally compared full truth-table bytes. This is **not** proof the controls are novel to all classical algorithms.

## 2. Frozen-result causal comparison (160 tasks/cohort; means over 3 seeds)

| Arm | Syntactically unseen XR exact / wrong / HOLD | Known-family diagnostic exact / wrong / HOLD |
|---|---|---|
| A1 correct learned weights, 1 type proposal | **57.667 / 0 / 102.333** | **56 / 2.667 / 101.333** |
| B1 shuffled labels, 1 proposal | **37.333 / 0 / 122.667** | **34.333 / 1.333 / 124.333** |
| A3 correct learned weights, 3 proposals | **140 / 0 / 20** | **108.667 / 4.667 / 46.667** |
| B3 shuffled labels, 3 proposals | **149.333 / 0 / 10.667** | **95 / 3.333 / 61.667** |
| C6 strong classical complete six-type search | **160 / 0 / 0** | **140 / 0 / 20** |

**At matched proposal count three, A<B in the purported transfer subset.** A1>B1 does not prove novel semantics: ALL **61/57/55** per-seed A1 exact answers originated from type **RX** (ALREADY in training), and every solution program was verified identical to target XR over **all 256 byte inputs**. The actual withheld XR syntactic type ranked first on **0/160 tasks in each seed**. Even a positive A/B type-ranking effect in a predetermined family is not a learned new primitive or a novel semantic operator.

Training+first-proposal process CPU total **19.929135 s** across 3 normal A + 3 shuffled B models, partial and not directly comparable to model-free C. Peak process self RSS (ru_maxrss) **326,684 KiB** (includes Python/PyTorch model and data), energy and full-dollar cost UNKNOWN. No valid full-system 10× claim.

## 3. The actual discovery is a falsification mechanism, not AI progress

Syntactic novelty overstates model capacity. A program is semantically nonnovel if there exists a preexisting executable program computing the same output on every valid input. Finite 8-bit universe permits exhaustive exact equivalence checking. For larger/infinite domains use SMT equivalence with fail-closed `UNKNOWN`; a bounded random test alone proves only *no counterexample observed*, never global equivalence.

**New mandatory G0 stage**: `SEMANTIC_EQUIVALENCE_QUOTIENT` BEFORE neural training/admission. Check candidate `I` against admissible preexisting classical library (and strongest baseline), requiring either (a) exact equivalence certificate → reject fake innovation, or (b) concrete separating input with verified unequal outputs → *representation gap relative to the explicitly enumerated library only*, then test wider classical synthesis, or (c) UNKNOWN → HOLD. Program-shape entropy, new AST text or unseen token order alone ≠ discovered function.

## 4. Recommended next bounded experiment

Do NOT rerun/optimize this 8-bit MLP to chase an apparent gain. Fix the benchmark ambiguity **before** generating new first outputs: choose functions that demonstrably have separating-input certificates against the entire admitted grammar, and switch to externally authored, heterogeneous, previously unseen tasks rather than same synthetic operator family. Extend output language only when there is an independent verifier and a known strong whole-goal classical comparator. Require a trainable ownweight proposer that can emit novel typed AST structures, not just select two already human-supplied primitive op types. Compare authentic repair A against shuffled-target/reward B, strong domain solver C, memory-allowed D, controlling train/test leakage and full amortized cost.

**Do not confuse finding a *fixed-grammar representational exclusion* for a proof no known classical algorithm can solve the task.** Failure to produce new semantic operations with own weights keeps `G1_HOLD`, `G2_NOT_RUN`, `Q1–Q7_OPEN`.

## 5. Reproduction and contents

Local conversation artifact `NEUMANN1_OPEN_OPERAND_CAUSAL_20261027.zip` includes untouched original executable and FIRST proposal hashes, all actual PyTorch weights and training logs, postfirst cache grade, semantic algebra audit, full 136,448-enumeration membership/exclusion record and separate integrity manifest. No third-party copyrighted corpus embedded. Run engineering tests first. **Do not rerun training in-place over the frozen FIRST files**; copy into a fresh directory, compare behavioral predictions rather than wall times/SHA of timing-containing JSON.

## Artifact verified after writing this report

- [Local generated standalone package](sandbox:/mnt/data/NEUMANN1_OPEN_OPERAND_CAUSAL_20261027.zip) (conversation container attachment, not GitHub-hosted source code), SHA256 **`834739799e9d891582f9ed3cdc64477bda1c759d0e1ff0965f94dddd7dd4a886`**, **17 archived entries**, ZIP CRC PASS, SHA256 manifest **16/16** PASS. Original first files and models remain unchanged. Contains all four post-first evaluation/semantics scripts in addition to the pre-grade PyTorch script.
- Separate explicit test for semantic candidate audit: **all 61/57/55 exact A1 proposals across three seeds** implement already-trained `RX`, verified identical to true `XR` on all 256 possible byte inputs; none uses syntactically heldout XR as top-1.
