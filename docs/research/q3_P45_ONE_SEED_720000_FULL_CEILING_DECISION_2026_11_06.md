# NEUMANN 1 | One seed -> 1,800 exact operators -> complete 720,000-case boundary proof

**Date:** 2026-11-06  
**Scope:** previously opened public ARC-AGI-1 `data/training` 400 tasks, NOT original evaluation; 11 evaluation IDs are reserved.  
**Final scientific decisions:** **P45 task-transfer capability FAIL**, **fixed mask-language reachability ceiling CERTIFIED**, **independent first audit PASS**, **global Q3/Q4/Q6/Q7 OPEN**.

## 1. Problem redefinition

Given ONE original GPT-6 teacher-authored source function `aa18de87` that filled empty cells between first and last nonzero marker in a grid row, can a source-preserving programmable input representation amplify its capability into **new, correct, independently verified original task solutions** beyond the frozen project classical baseline?

This is different from asking whether there are more syntactically valid programs, or whether the source solver is mathematically consistent.

## 2. Preregistered assumptions and exactly fixed source

- Original teacher source `experiments/q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs`, Git blob `d82f09406b4b3ee4e9651c261013c8ce8aa850c7`, unchanged. External GPT-6 authored it. **NEUMANN did not learn this operator**.
- Original public ARC-AGI-1 training corpus `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`, **400 previously opened training tasks**. Not a clean held-out generalization claim.
- P30 original strong project classical first SHA256 `0fb747b4fd7355649465b8ff3424c0170d6d178f47fd1ea64ca486c416672b79`, **54/400 exact**, **8 wrong submissions**.
- P43 source program transfer first SHA256 `8b5cb4927133930f6238adb17dbeba5a73d6955a368965b67318cc6aca78a398`, one extra original exact case `a699fb00` via `aa18de87`, **zero wrong submissions**.
- P44 original D4/color conjugation first SHA256 `8efe48796c15f8f322124afa6751dca1ea7816c93e038e4a38b90d08dcc3e639`, 180 variants, original case still only `a699fb00`, +0.
- Frozen original correctness-set union = **55/400 only as an offline ground-truth ORACLE upper bound**. Not a deployable merged router, as the P30 original had 8 wrong answers.
- P45 prereg `docs/experiments/q3_P45_ONE_SEED_MASK_LIFT_FIRST_PREREG_2026_11_06.json` was written before original first. Requires **>=2 new original correct outside prior 55, 0 incorrect accepted outputs, >=1 new selective-marker solution**.

## 3. First-principles structural analysis

The one original source function can be lifted by a typed adapter:

1. Choose the line axis `a∈{row,column}`.
2. Choose source background `b∈{0,...,9}` and distinct output fill `c∈{0,...,9}\\{b}`.
3. Choose a marker mask: `ANY_NON_BACKGROUND` or exactly one selected input color `m != b`. There are ten mask choices per background.
4. Project the selected marker sites to normalized 0/1 input, execute the exact frozen source program, and merge newly produced color-2 positions into the original grid **only when the original cell was background b**, writing c. Preserve other input colors.

This yields exactly `2 × 10 × 9 × 10 = 1,800` syntactic candidates. It **does not** create a fundamentally new geometric operation; it adds one **human-authored typed input/output adapter**.

A necessary condition for any candidate program in this language to match original training is:

```text
For EVERY changed TRAIN pixel (input, output), input == b AND output == c.
All input/output grid shapes must match.
At least one TRAIN pixel must change (nontrivial policy condition).
```

No amount of parameter ranking or neural feature matching can overcome failure of this necessary structural condition within the same fixed language.

## 4. Immutable original FIRST

Original first natural task scoring [GitHub Actions #42148341148](https://github.com/yoonsj0305/NEUMANN/actions/runs/42148341148) completed as an intentionally **red scientific FAIL**, not infrastructure failure.

- Exact original first JSON SHA256 `38e41ddd312eb451745f2d73194840e98464e9660d14c52c30537fb7e30bfff5`.
- Original TRAIN delta structure compatible for **63/400**; the other **337/400** fail necessary nontrivial source change condition.
- Of 63 eligible problems, only one produced a valid exact TRAIN-fit + unambiguous original TEST prediction.
- **P45 submissions 1/400; exact 1/400; wrong 0/400; new exact beyond prior frozen correct 55 = 0.**
- No new selective marker original task was solved. The only exact original `a699fb00` was previously correctly solved by P43 (source background 0, fill 2).
- Initial P45 original process CPU **86.988 ms**, wall **43.340317 ms** on that GitHub Actions runner, *the recorded 400-task JS proposal loop only*, excluding human development, teacher generation, verification and source preparation. Not an end-to-end 10x measurement.
- Earliest FIRST is authoritative. A later duplicate run on the same family is not a new independent first.

[Read-only alternate source implementation audit #42148654995](https://github.com/yoonsj0305/NEUMANN/actions/runs/42148654995): **PASS**; independently reconstructs 400 original source tasks and all 1,800 mask choices using a different direct mathematical implementation, original first hashes P30/P43/P44/P45 pinned, exact 1/400 confirmed, false favorable score forgery rejected. It did not reuse P45's first proposal code.

## 5. Complete fixed-language theorem and 720,000-case independent audit

Post-FIRST, a separately registered **complete-denominator audit** eliminated one remaining potential ambiguity: *could the P45 source-delta pruning or learned variant ordering have hidden a candidate that really fit?*

The independent evaluator enumerated **all 1,800 parameter tuples for all 400 original task IDs without delta pruning**, then compared the output to **every original TRAIN pair**. It intentionally did **not access original TEST output gold**, avoiding another favorable score.

[Actions #42149282404](https://github.com/yoonsj0305/NEUMANN/actions/runs/42149282404): **`FIXED_LANGUAGE_TRAIN_CEILING_CERTIFIED`**.

| Complete original TRAIN proof metric | Measured |
|---|---:|
| Original source task IDs | 400 |
| Exact fixed candidate tuples per task | 1,800 |
| Exhaustive candidate-task combinations | **720,000 / 720,000** |
| Original TRAIN program executions (including later examples for rare fits) | **720,032** |
| Original task source changes structurally incompatible | **337** |
| Source changes compatible but no exact TRAIN program | **62** |
| Source tasks with >=1 nontrivial exact TRAIN candidate | **1** |
| Total exact TRAIN-fit parameter tuples | **2**, both for `a699fb00.json` |
| New original TEST ground truth used in this complete certificate | **0** |
| Original public EVALUATION task IDs consumed | **0** |
| Independent audit process CPU | **2,173.139 ms** |
| Independent audit process wall | **2,678.755 ms** |

The two matching programs are row/background=0/fill=2/marker=`ANY` and row/background=0/fill=2/marker=1. Both are old-case fits, not a new original solved case. A synthetic one-fill positive and a synthetic impossible two-fill negative source control passed. A forged successful original FIRST is rejected by its pinned SHA256.

**Conditional finite-language proof:** Let `H` denote exactly these 1,800 source-derived programs and let `D` be the complete original TRAIN pairs. For a *nontrivial* task define

\[
H_D = \{p\in H:\forall(x,y)\in D,\ p(x)=y\;\land\;\exists(x,y)\in D,\ x\neq y\}.
\]

If `H_D=∅`, any policy restricted to selecting or reranking an element of `H` **cannot** return a nontrivial TRAIN-consistent program on that task, irrespective of amount of compute or policy training. The exhaustive run has `H_D=∅` for **399/400** already-opened tasks. This is a precise **hypothesis-space reachability ceiling**, **not a claim that the 399 tasks are intrinsically unsolvable** or that no genuinely larger learned program language can solve them.

## 6. Delete, simplify, accelerate, automate (in that order)

- **Challenge:** The number of generated candidates or cheap source calls is not evidence of improved intelligence.
- **Delete:** STOP further D4 × S10 relabeling, single-color mask-only parameter expansion, rankers/caches/search heuristics limited to this 1,800-program family, and extra ARC evaluation consumption. Exhaustive evidence now shows why more compute in that exact language cannot improve TRAIN reachability.
- **Simplify:** Retain the original teacher-authored semantic primitive and exact source checker as training examples/tools. Prioritize the *proposal-language extension mechanism*, not more human-authored patterns.
- **Accelerate:** Require a student learned generator to **emit a new typed AST or executable semantic operator outside H**, then source-prove exact original TRAIN and unseen TEST outcomes under a precommitted independent source family. Compare to same-language GP/CEGIS and full classical fallback, not earlier weak DSLs.
- **Automate:** Only after actual source-original new verified solutions, safety and equal-rights cost, not to scale a proven dead-end.

## 7. Cost, interfaces, risks and degraded mode

**Measured** code-side first and exhaustive audit process CPU/wall above; cannot equate P45's 43 ms original scoring loop to end-to-end user/inference cost. External teacher code generation, human typed adapter design, possible learned training, hardware energy and verifier cost are all **not metered**. The manufacturing `Idiot Index` is not meaningful here without defined raw material vs product cost, so no fabricated values. The high-risk interface is typed program -> full TRAIN execution -> original verifier -> abstain or accept; this must be a **separate, untrusted-proposal / trusted-verifier boundary**.

**Risks:** Public ARC tasks may be known to model pretraining; 400 are already opened. This is not 400 independent human-authored semantic families. Test consistency does not guarantee correctness on all unseen inputs; zero wrong submissions 1/1 does not justify zero-error calibration. Human-defined adapter is not autonomous neural invention. The 1,800 candidate tuples can be semantically redundant; the exhaustive count is parameter tuples, not 1,800 pairwise distinct functions.

**Degraded mode:** If original source hash changes, original receipt tampered, a candidate is ambiguous, shape/constraints invalid, source evaluation `UNKNOWN`, or an original independent proof missing, abstain and route to verified classical solver. Never label an AI-generated unverified output as PASS.

## 8. Tenfold innovation options, in order

1. **Delete selection-only learning on H:** Immediate elimination of a mathematically unproductive optimization loop. This is not itself a measured 10x system advantage.
2. **Generate a typed representation, not a selected variant:** A frozen learned proposer can construct **new operators absent from H**. Require an original strict transfer gate before allowing any scaling.
3. **Proof-carrying composition across formalisms:** Learned generator emits semantic AST and independently checkable obligations, reusable from ARC to another creator-origin language. Global Q6 remains OPEN until real external proof.
4. **Classical-first compute gate:** If a strong equal-rights classical GP/CEGIS/SMT solver solves it, bypass a neural model. Only pay neural discovery cost when it adds provable new reachability.

## 9. Strongest recommendation

**STOP treating a single operator's symmetry and mask closure as sufficient for general problem solving.** Keep the source as a minimal reusable symbolic tool and train/test the **ability to invent an operator/type-system primitive absent from the fixed source language**. The certificate lets us stop this entire line of ranker hyperparameter work with a formal, replayable reason, not an intuition.

**Final scope:**
- `P45_FIRST_NEW_ORIGINAL_SOLVES=0`: **FAIL**.
- `P45_FIRST_INDEPENDENT_AUDIT`: **PASS**.
- `P45_FULL_720000_FIXED_LANGUAGE_COMPLETENESS`: **PASS**.
- `Q3_AUTONOMOUS_NOVEL_STRUCTURE`: **OPEN**.
- `Q4_10X_ALL_IN_COST`: **OPEN**.
- `Q6_INDEPENDENT_CROSS_FORMALISM`: **OPEN**.
- `Q7_FRONTIER`: **OPEN**.

Review/merge order: this P45 branch is stacked on P44 -> P43 -> P2.2 and **must not be merged directly into `main`** without its parent research context. Original FIRST and negative scientific gate must remain immutable.
