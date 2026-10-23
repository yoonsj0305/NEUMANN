# NEUMANN Q3 · ACTUAL trained grammar routing to unseen ERBench original 32 | First immutable research verdict

**Date:** 2026-10-23 (KST). **First dedicated GitHub Actions run** [#39902306657](https://github.com/yoonsj0305/NEUMANN/actions/runs/39902306657), three independent jobs **SUCCESS**. Source code PR [#538](https://github.com/yoonsj0305/NEUMANN/pull/538). This is ACTUAL cross-task learning, not a mock: 32-unit scikit-learn MLPClassifier trained with CPU on different original ERBench author-provided formula categories, then applied to another original source task set.

## Provenance and strict original split

Third-party original EquationDiscovery ERBench public train10,000 original equations. HF Git revision `95bf15c27de68c3f170ca6140d2e4a811c60344f`, CSV SHA256 `03c0ceb53ed0348650c0a94ed5cd1e452325d2b7c7d3be68f9a458316eda33b1`. A fixed safe 1-D AST filter identifies 5717 eligible expressions; metadata-only SHA-sort selects ranks **64..95 for exactly 32 test originals**, with originals hidden in a separate evaluator job. Training metadata+original formula grammar labels are from ranks **96..2095**, 1907 valid numerical training tasks from 2000 originally eligible, **zero overlap** with test ranks. Both sets are still PUBLIC from the same external benchmark distribution; NOT a blind private external benchmark or a different author-family transfer claim.

Training source-only grammar labels from original *other* authors' equations: RATIONAL 1235, OTHER 576, SQRT 46, LOG 33, SIN 8, EXP 5, COS 4. Extremely imbalanced low-example classes, honest generalization ceiling. Numeric-only task features (normalized shape and summary statistics) with class supervision, 32-hidden-unit MLP on CPU, no GPU or paid tokens. **Grammar functions, allowed operators and candidate-program synthesis are all HUMAN-DEFINED**: `RATIONAL,SIN,COS,EXP,LOG,SQRT,OTHER`. The learned MLP chooses TWO candidate classes, not a truly invented mathematical primitive.

Training source JSON SHA256 `dd6bf54aff6c8373c012b78f1f1b0f7ee06e005cd46763575b5a96d1b781b627`, third source-only numeric input SHA256 `5bd1287518921eed233828f58f7202c991ca552fdb7dbf6b798e18f0ed2a4de2`, private grader truth SHA256 `b7b46b42aeb4fcf35a03b01f87484d83fedce3dd6f4463b0a8127ea8729ff06c`. Source-only before-grade predictions SHA256 `a851eba449dc9418484fef1b7f8dfd966e50808b40c3b90465c748c0f9e8290b`.

## Original native exact formula proof scores: FIRST GRADE

Third job downloaded sealed third32 original test truth ONLY after predictions were frozen and **symbolically compared source true author equation to candidate formula exactly**, not only a numerical curve-fitting RMSE. First independent grade receipt SHA256 `20124ca992a59435f72ee9ea33cf58ec26bf58365a810bbd9d2f0e01698b5e37`.

| True original third32 methods on SAME 32 task IDs / numeric observations | exact original formulas | withheld / abstain | wrong certified as correct |
| --- | ---: | ---: | ---: |
| D: actual learned-top-two expression category router + exact source-only classical synthesizer | **3/32** | **29** | **0** |
| C: nolearn fixed-first-two classical categories same source/functions | **3/32** | **29** | **0** |
| A: strong all-SEVEN category enumerator with identical legal candidate templates | **3/32** | **29** | **0** |

Trained **neural-exclusive original truths vs all-grammar classical A = ZERO**. No demonstrated accuracy gain from learned grammar routing, though actual source class parameters were learned. This is not full PySR/Operon/SRBench third-party SOTA comparator, but it IS exact maximum-permitted closed program-library baseline for the human fixed grammar tested. A nolearning-first-two source method matches D, so D is not even better than its cheap same-source restricted ablation.

## Cost boundary
From the first successful SOURCE-ONLY training and prediction log: CPU for MLP training on 1907 original training tasks `0.23637556299999996 seconds`; full classical all-library candidate mean over same 32 test tasks `0.006424866343750026 seconds`/task, hence total approximately `0.205595722 seconds` for its source candidate passes in the identical inference job. **The learned model's training CPU alone exceeds the full same-grammar classical candidate pass CPU of all 32 test tasks.** Caveat: full startup/package/workflow IO, preparation of 1907 labelled training tasks, shared inference and symbolic grading are not included; the numbers do not establish any universal full-lifecycle speedup/slowdown, and training could hypothetically amortize over many future cases. They show NO positive full-cost dominance on the actual fixed 32 here. Learned and fixed classical also had identical verified accuracy.

## Conditional scientific verdict and stop/decision
- `Q3_ACTUAL_LEARNED_GRAMMAR_ROUTING_ON_EXTERNAL_ORIGINALS=IMPLEMENTED_AND_VERIFIED`: truly fitted weights on independent source tasks, source-only test inference and original exact grade was physically separated and executed.
- `Q3_LEARNED_UNIQUE_PROOF_CAPABILITY=FAIL_THIS_CLOSED_GRAMMAR`: 0 learner-only new originals, strong classical complete library matches.
- `Q6_CROSS_TASK_ROUTER_GENERALIZATION=SCOPED_EXECUTED` but **no new performance benefit**. Cross-author or first-time private external transfer not proven.
- `Q4_MATCHED_TASK_ACCURACY_PER_TOTAL_CPU_IMPROVEMENT=NOT_PROVED`. No 10×, frontier or all-system parity.
- `G1=HOLD`, `Q3_AUTONOMOUS_NEW_OPERATOR=OPEN`, `Q7_FRONTIER=BLOCKED`. **Terminate mere fixed-grammar MLP routing development** unless an entirely new expressive mechanism and strong source-native comparer are available.

## Crucial mechanism implication
This study cannot establish an agent that *creates a new typed operator*, because the researcher predeclared every allowable operator. It is a measured useful distinction: learning to choose among already-supplied expert templates is not the capacity to invent them. A new Q3 architecture should attempt open-ended composition with independent counterexample-driven oracle queries and a fixed strong identical-authority symbolic synthesizer. Merely more original corpus samples, 1000 hidden units, tuning seeds, or 1000 more PRs in the same closed grammar do not cure missing representational ability.

The original literature, code and tasks are third-party or common algebra; no priority claim of discovering a new mathematical theorem. Historical earlier source32 #535 remains 0/32, second32 #537 10/32 on a different cohort; NEVER compare 10/32 second vs 3/32 third as a causal accuracy regression.
