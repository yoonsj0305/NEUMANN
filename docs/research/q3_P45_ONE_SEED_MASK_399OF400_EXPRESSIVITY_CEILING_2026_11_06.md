# NEUMANN 1 | 2026-11-06 Q3 P45: one-seed 1,800-program expressivity ceiling **399/400 PROVED within fixed language**

**Status:** original public-TRAIN transfer **FAIL**, independently audited **PASS**, fixed-language *TRAIN inconsistency theorem* **PROVED**. These three findings must never be conflated. **Global Q3, Q4, Q6, Q7 remain OPEN.**

## 1. Problem redefinition

Determine how far **one** previously independently scored transferable source program `aa18de87` can be amplified into executable programs by changing its representation interface, **without editing the source kernel** or introducing unverified novel learned semantic primitives. Count original public benchmark source successes, independent source equivalence, and exactly where the enlarged language cannot represent an original TRAIN mapping.

The original source P22 externally authored teacher program has pinned Git blob `d82f09406b4b3ee4e9651c261013c8ce8aa850c7`, original separate transfer `a699fb00.json` verified in parent [PR #659](https://github.com/yoonsj0305/NEUMANN/pull/659). Its exact D4/S10 palette orbit [PR #660](https://github.com/yoonsj0305/NEUMANN/pull/660) covered 180 variants, but FIRST original 400 yielded **0 new** beyond the prior historical correct set.

## 2. Challenge/delete assumptions

| Presumption | Fixed source-grounded result |
|---|---|
| More fixed programs automatically generalize | **FALSE on measured benchmark:** 180 symmetry programs then 1,800 mask programs both yielded zero new original correct |
| Whole-grid geometry and constant foreground/background colors need no change | **FALSE:** independently audited 138/400 original TRAIN tasks have output shape change |
| All original outputs need just one pixel replacement mapping | **FALSE:** 199/400 original TRAIN tasks require at least 2 distinct input→output color substitutions |
| 1,800 options require testing all on each task | **DELETE:** source-changed pixels logically determine `background=b` and `fill=c`, leaving exactly 2 axes × 10 marker choices = **20** candidates on each of the 63 uniform-delta tasks |
| Pretrained external teacher code is NEUMANN learned discovery | **REJECT:** origin was GPT-6 externally authored, this entire amplification is human-specified classical composition |
| 55 historic correct-set union is deployable zero-error solver | **REJECT:** it is a post-scoring **oracle union upper bound** and original P30 had **8 wrong accepted** |

## 3. One source operator, new typed mask interface

Retain exact `f_seed`: for every row, it fills zero pixels between the leftmost and rightmost nonzero cells with source color `2`. Compose:

`h_{axis,b,c,m}(x) = MERGE(x, c, f_seed(PROJECT_{axis,b,m}(x)))`,

where:
- `axis ∈ {row,column}` is a transpose-to-row view;
- `b∈{0,...,9}` is the destination background; `c∈{0,...,9}\\{b}` is the fill color;
- `m` is exactly one of `ALL_NON_BACKGROUND` or the 9 specific color markers `m!=b`;
- `PROJECT` converts the original input into a binary mask (marker=1, everything else=0);
- `MERGE` writes color c **only** at original input cells of value b where the unchanged source kernel has newly written 2; all other original pixels are preserved.

The global family has **2×10×9×10=1,800** parameter tuples. Source code `aa18de87` is used as the only internal gap kernel and remains byte-identical. Projection and merge are **human-authored generic adapters**, not a new generative model.

### Structural theorem 1: shape and substitution necessity (all valid grids)

For every `h` in this exact family, input and output grid dimensions are identical, and there exist fixed colors `b!=c` such that **every** changed pixel has input color b and output color c. This follows directly from the MERGE definition, independent of source data.

Therefore:
- An original TRAIN example that changes grid dimensions is **impossible to fit** by any one program in the declared 1,800 family.
- An original TRAIN set containing two different nonidentity pixel substitution pairs is **impossible to fit** by any one program in this family.

These are **structural impossibilities relative to this exact language**, not lower bounds on all algorithms or on general intelligence.

### Structural theorem 2: complete original TRAIN candidate reduction

For any TRAIN set with ≥1 changed pixel and all changed pairs equal to one specific `b→c`, any consistent program in this family must have the **same (b,c)**. Hence exhaustive fit testing needs only **20 candidates** (2 axes × 10 markers), not 1,800. This is complete under the frozen representation. Each candidate is tested against **all original TRAIN pairs**, not only the changed example.

It follows that testing all 20 candidates and finding no exact all-TRAIN fit is a **finite-domain exhaustive certificate of non-representability** in this frozen family.

## 4. Original 400 evidence and exact representational ceiling

Upstream `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`, **400 previously opened public TRAIN tasks**, no untouched original ARC public EVALUATION files consumed.

- [Immutable P45 original FIRST #42148341148](https://github.com/yoonsj0305/NEUMANN/actions/runs/42148341148): program source and three historic FIRST baseline JSON SHA pins all passed. **9 source/negative tests PASS**, including 9,000 varied shape/palette/axis direct-reference comparisons and 19,683 3×3 three-color grids. Scientific `SCOPED_ONE_SEED_MASK_LIFT_FAIL`, original JSON SHA256 `38e41ddd312eb451745f2d73194840e98464e9660d14c52c30537fb7e30bfff5`.
- Actual original source: **1/400 correct**, **1 submitted**, **0 wrong**, **0 newly correct over original P30∨P43∨P44 correct-set upper bound 55**. Only `a699fb00.json` repeated, with canonical row `b=0,c=2,m=ANY` and selective `m=1` alternatives. No new task gained from 1,800 programs.
- Original score loop measured **1,279** TRAIN program executions, **2** TEST-input calls, **86.988ms** process CPU and **43.340ms** loop wall. Those are not model-training, energy or full research life-cycle costs.
- [Independent read-only original 400 audit #42148654995](https://github.com/yoonsj0305/NEUMANN/actions/runs/42148654995): **PASS**, SHA-pinned original FIRST/three parent receipts, a *separately coded direct mathematical mask/merge implementation* (does not import P45 generation code) independently scored all 400. Exactly **1 TRAIN-fitting original**, **1 original correct**, **0 wrong**, **0 newly correct**, **0 audit errors**; forged 100-new-correct success rejected.
- [Post-FIRST original TRAIN-only taxonomy #42149088333](https://github.com/yoonsj0305/NEUMANN/actions/runs/42149088333): **PASS**, six synthetic classification unit tests, original first SHA check, no original TEST gold examined. Classified each original task exactly:

| Original TRAIN-only structural class | Number of tasks | P45 proof meaning |
|---|---:|---|
| Output dimensions change | **138** | h always preserves shape → no h can fit |
| At least two distinct input→output pixel substitutions | **199** | h can change only one fixed b→c pair → no h can fit |
| Exactly one changed b→c pair across training | **63** | source-delta candidate theorem restricts to 20 exact variants; independent audit finds 1 fitting task, **62 non-fitting** |
| Zero-change TRAIN | **0** | no ambiguity from this class here |
| **TOTAL** | **400** | **399 have NO source-consistent executable in this frozen 1,800-program family** |

**Bounded original evidence theorem:** 138 + 199 are ruled out by necessary shape/substitution invariants; 62 by complete source-TRAIN enumeration; the remaining one is the preexisting seed transfer. Thus **399/400 inexpressible on original TRAIN inside H_P45**. The conclusion requires original source authenticity, precise semantic class and correct executable/original comparisons. It is **not** a proof that those 399 tasks are unsolvable by classical search generally or by an expressive neural policy.

A duplicate separate source CI invocation may exist on the same branch. The authoritative P45 FIRST for this contract is explicitly the SHA-pinned run #42148341148 above, and later checks never replace it.

## 5. Musk five-step research decision

1. **Question:** Why must a single successful code body imply transfer to fundamentally unrelated semantics? It need not. A finite set of positive observations cannot logically determine arbitrary unseen outputs without a prior inductive bias.
2. **Delete:** Stop stacking more coordinate/color masking variants, or running new evaluation IDs against this source family. The 1,800 fixed hypothesis class is exhausted relative to the 400 opened originals.
3. **Simplify:** Maintain the exact source verifier, strong classical-first fallback and auditable typed-program interface; delete any unsupported intuition that new module count means Q3 growth.
4. **Accelerate:** Target **output shape changes and multiple simultaneous output colors**, which account for **337/400 original TRAIN tasks** that current syntax excludes outright, with a learned new-operator proposer and strongest same-rights native GP/CEGIS comparator. Do not simply implement 337 manual case templates.
5. **Automate last:** Only begin bulk model/student iterations after one precommitted outside-the-language output program is independently proven on a new *external author/source family*, outperforms equal-rights strongest classical and amortized end-to-end cost is metered.

## 6. Cost/physical basis

`C_total=C_data+C_teacher_training+C_student_training+C_proposal+C_source_execution+C_independent_proof+C_failure_retries+C_fallback`. The first P45 source execution 1,279 TRAIN calls and ~87ms CPU cannot be turned into a 10x full-system benefit. Teacher generation tokens, training cost, device energy, API fees, setup and independent human engineering time not measured. Software-only algorithm has no physical raw-material manufactured-cost baseline, so manufacturing `Idiot Index` is **N/A rather than invented**.

The theorem additionally gives a *computational* simplification: reduce the apparent 1,800 hypotheses to **≤20 candidate tests per eligible task** solely by source TRAIN-delta information. This improves source algorithm search efficiency, but does not improve original answer coverage on the observed corpus.

## 7. Risk / degraded mode

- Previously opened public TRAIN corpus, externally authored by dataset community but not first-blind held-out to researcher, and may have been in LLM pretraining.
- Teacher was GPT-6 externally, not NEUMANN own learned structural policy. This classical source-composition outcome cannot close global Q3 neural invention.
- An exact source-TRAIN fit is necessary but not sufficient for arbitrary TEST correctness; conflicts require ABSTAIN. In this cohort no first P45 accepted wrong submissions, but no out-of-sample zero-error safety claim.
- All malformed original source, source SHA drift, insufficient source delta, nonuniform colors, shapes, ambiguous test-input proposals or verifier uncertainty must return UNKNOWN/ABSTAIN.
- The 55 historical oracle correct-set union is not an inference-time available decision policy; prior underlying classical union had 8 wrong submissions.

## 8. Actual 10× options, explicitly NOT PROVEN

**A. Delete wrong hypothesis search.** Original TRAIN-delta indexing reduces 1,800 syntax tuples to ≤20 relevant variants for the 63 representable-shape class. Exact source correctness proven; actual capability extension **zero**.

**B. Generative typed AST engine.** Learned proposals must produce new higher-order operations that can change output dimensions and implement nonuniform palette rules, beyond H_P45. Matched GP/CEGIS exhaustive search gets the **same** AST rights; need real independent original verified additional solves. **NOT RUN**.

**C. Separate human/solver/AI functions.** Classical certified modules handle finite-state and exact-known domains; a learned generator is invoked only where it offers verified new semantic headroom, and abstains otherwise. **NOT RUN**.

**D. Source-independent representation transfer.** Freeze learned weights/policy, run on different author/domain mathematical representation with common proof-carrying semantics and full training/serving cost. **NOT RUN**.

## 9. Recommendation and future experiment gate

**Conclude the one-source classical closure investigation:** `P44_180_SYMMETRY=0_NEW` and `P45_1800_MASK=0_NEW` with **399/400 original TRAIN representational ceiling**. This is the strongest available fact from these runs, rather than another optimistic score.

A future genuine Q3 attempt should choose a learned *generator*, not a selector over human-prescribed operators. It should propose an executable operation absent from frozen classical and teacher libraries, check every original example with an independent verifier, and require ≥1 new independently sourced formalism solve over a strongest equal-rights classical proposer including the newly allowed AST expressivity. Include total model training/inference/proof costs and strict separate failure receipts. No ARC evaluation ID is authorized for a cosmetic next-source update.

**Final gates:**
`SINGLE_SEED_1800_ORBIT_MASK_SOURCE_PROGRAM_EQUIVALENCE=SCOPED_PASS`;
`FIXED_H_P45_TRAIN_INEXPRESSIBLE=399/400_PROVED`;
`P45_ORIGINAL_NEW_CORRECT=0`;
`P45_STRICT_GENERALIZATION_GATE=FAIL`;
`P45_ORIGINAL_FIRST_INDEPENDENT_AUDIT=PASS`;
`Q3_AUTONOMOUS_LEARNED_SEMANTIC_INVENTION=OPEN`;
`Q4_ALL_IN_10X=OPEN`;
`Q6_CROSS_FORMALISM_INDEPENDENT_TRANSFER=OPEN`;
`Q7_FRONTIER=OPEN`.
