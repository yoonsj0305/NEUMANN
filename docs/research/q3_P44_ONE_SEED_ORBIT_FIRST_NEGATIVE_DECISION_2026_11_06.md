# NEUMANN 1 | Q3 P44: one working program → 180 D4/S10 orbit programs, independent original generalization FIRST FAIL

Date 2026-11-06. Scientific scope: **CLASSICAL TRANSFORMATION ORBIT, NO NEUMANN NEURAL INVENTION**.

## Problem and exact first contract

Use exactly the previous P43 real original transfer success: frozen P22 external GPT-6 teacher function `aa18de87`, original source Git blob `d82f09406b4b3ee4e9651c261013c8ce8aa850c7` (from PR #632), first successfully reused on *different* official original ARC train task `a699fb00.json`.

The source operation replaces 0 pixels located strictly between the leftmost and rightmost nonzero sites in each row with color 2, preserving all other pixels.

Conjugate this **same frozen source executable**, with no manual new gap primitive, by (i) axis orientation under D4 action on rectangular grids and (ii) invertible permutations of the ten ARC palette labels. The group orbit quotient has **two axes × ten possible background labels × nine different fill labels = 180 program parameterizations**. Original source program never changed.

Precommit [P44 first contract](../experiments/q3_P44_ONE_SEED_D4_S10_ORBIT_FIRST_PREREG_2026_11_06.json): on 400 previously OPENED original ARC train tasks, accept any unique TEST prediction with exact all-TRAIN consistency and observed positive TRAIN change; conflicting predictions must abstain. Strict local gate requires **≥2 additional correct original tasks** beyond historical `P30∨P43` **55/400 correct-set ORACLE union**, **zero wrong submissions**, and a genuinely nonidentity new successful orientation or palette. The historical P30 original safe algorithm had **54 correct and 8 wrong**, and P43 added one different originally correct task. Therefore **55 is not a deployed zero-error merged solver**.

## 1. Source-original implementation verification

Seven software unit tests passed, including:
- Source-identity original `f(row,background=0,fill=2)==seed` on varied grid shapes.
- Bijective ten-color conjugation for every distinct ordered background/fill choice.
- Exactly 180 parameter tuples, no filename-specific routing.
- Independent direct mathematical gap-fill check for **4,500** generated color/size/axis cases, plus every **19,683** 3×3 grid over a three-color alphabet (two orientations).
- Fail-closed no-visible-TRAIN-change control, ambiguous candidate predictions, malformed source grids and input mutation guard.

The initial [preflight CI #42146904375](https://github.com/yoonsj0305/NEUMANN/actions/runs/42146904375) failed **before any original data loading** due an invalid nested TEST-grid fixture in a unit test. The fixture was corrected; there was **no original scoring before the correction**, and the one eligible original FIRST below was independently preserved.

## 2. Immutable original FIRST and independent audit

- [FIRST original full 400 #42147159711](https://github.com/yoonsj0305/NEUMANN/actions/runs/42147159711): `SCOPED_ONE_SEED_ORBIT_REUSE_FAIL`, original JSON SHA256 `8efe48796c15f8f322124afa6751dca1ea7816c93e038e4a38b90d08dcc3e639`. Exactly **1/400 submitted, 1/400 original correct, 0 wrong, 0 additional correct beyond historical 55**, no new axis or palette transfer. Only original success `a699fb00.json` with **unchanged** canonical `row/background:0/fill:2` program, not a genuinely new one.
- Cost on first same runner: **72,015** total TRAIN program executions, **1** TEST-input program call; process CPU **918.973 ms**, original scoring-loop wall **697.908 ms**. These are narrow source-program measurements excluding model training and teacher generation.
- The original first GitHub Actions job was deliberately marked scientific **FAIL**, not overwritten with a green success claim.
- [Independent alternate-source read-only audit #42147546221](https://github.com/yoonsj0305/NEUMANN/actions/runs/42147546221): **PASS**, original P44/P43/P30 result bytes SHA verified and another implementation of the mathematical gap operator re-ran all **400** official public original tasks, confirming **1 submitted, 1 correct, 0 wrong, 0 extra**, **72,015** TRAIN calls and original success ID. First-result tampering and false PASS conversion were rejected. Audit does not import the first-run P44 proposer or source evaluator.

## 3. Generalization theorem and actual ceiling

For a grid `x` and any bijective palette permutation `π`, and spatial axis permutation `T`, the conjugate operator is

`f_{T,π}(x)=T^{-1}π^{-1} f_seed(πT(x))`.

Because `π` and `T` are invertible, any changed output site corresponds to a background pixel of a single color `b` between extremal non-background sites in one row/column, and it is replaced by exactly one color `c`. The source operation is shape preserving. Algebraic conjugation makes this guarantee for **every valid grid** in the source function's shape domain (1≤H,W≤30), not just one input image, and it applies to original source only under the documented `f_seed` semantics.

**That theorem does NOT guarantee any new ARC task follows the rule.** Original 400 scoring shows **zero** natural task gains beyond the original seed transfer.

## 4. First-principles selection

**Delete:** additional D4/palette color sweeps or more copies of the same exact fixed program; the completed 180-class source oracle already tested the entire declared quotient on the observed original 400.

**Keep:** exact algebraic source-conjugation as an optional low-cost verified compiler transform, plus the single original `a699fb00` transferred program as evidence of scoped reusability.

**Next discriminative extension only:** allow a typed `mask project → original kernel → merge` adapter that changes the *input representation* instead of only a bijective label or orientation. This still counts as a **human-authored classical** generative schema, not learned neural Q3. The next experiment must be independently checked with the full prior first results pinned, not reinterpret this failure.

## 5. Costs and safety

Original teacher generation compute, GPU, energy, cost, program-authoring time and full run pipeline overhead were **not measured** in the P44 CPU number. No `10×` all-in claim or manufactured-cost `Idiot Index` is supported.

Failures, ambiguous candidate outputs, out-of-range palettes, invalid grids or no observed training change result in `ABSTAIN`. No ARC public EVALUATION originals consumed. Previously opened ARC **TRAIN** examples are **not** a clean independently authored or pretrained-data-sealed validation corpus.

**Scientific gates:** `P44_SOURCE_PROGRAM_CONJUGATION=SCOPED_CORRECT`; `P44_ORIGINAL_TRANSFER_NEW_ANSWERS=0`; `P44_STRICT_FIRST=FAIL`; `P44_INDEPENDENT_FIRST_AUDIT=PASS`; `Q3_NEURAL_AUTONOMOUS_SEMANTIC_CREATION=OPEN`; `Q4_ALL_IN_10X=OPEN`; `Q6_OTHER_FORMALISM=OPEN`; `Q7_FRONTIER=OPEN`.
