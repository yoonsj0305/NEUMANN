# NEUMANN Q3 | First actual generative AST attempt on NEW external original source fifth32: honest FAIL

Date 2026-10-23 KST. **PR #541** https://github.com/yoonsj0305/NEUMANN/pull/541 . **Dedicated first triple-stage Actions #39908195040** https://github.com/yoonsj0305/NEUMANN/actions/runs/39908195040 . **ALL THREE JOBS SUCCESS** (environment, actual MLP training/program generation, independent original native mathematical grading).

## Why this experiment was different
Prior learned router #538 merely chose from seven human-named grammar labels and tied classical 3/32. This test trained a **genuine 32-hidden-unit neural policy to predict primitive operations** from externally authored numerical input-output examples and their original (different source tasks') AST operation-presence labels. A source-only typed program constructor then COMPOSED program graphs from primitive `+, *, /, sin, cos, exp, log, sqrt`, automatically creating 215 evaluable intermediate AST features, and proposed new source-specific whole programs combining one or two generated AST features with exact-rational numerical coefficient repair. These complete program expressions were NOT simply chosen as labels from a human-specified finite set of entire target formulas. However, the typed primitives, tree-generation rules, coefficient grammar and candidate-budget cap were still human-selected. This is a *compositional program proposal mechanism*, not unbounded new operator invention.

## Genuine third-party original-first split
Original independent author EquationDiscovery ERBench public 10,000 formulas in HF git `95bf15c27de68c3f170ca6140d2e4a811c60344f`, author CSV SHA256 `03c0ceb53ed0348650c0a94ed5cd1e452325d2b7c7d3be68f9a458316eda33b1`. Eligible 1D source rows metadata-hash ranked, learner supervision trained from rank 96..2095, source eligible original input-output **1903** (no originals from test included), test first untouched fifth32 rank2128..2159 (disjoint previous tested0..95, fourth2096..2127, training96..2095). Source original formula physically isolated from all prediction jobs; fifth32 source numeric x/y SHA256 `5e3d18db2efdaa55380893557e63089c00724aceb8b1502260d8e7d480633e69`, secret author original formula SHA256 `fc544d3aa495644898257475cf6c16018978b11adc8dc8efd106d7079ddd17ae`.

Training operation labels across real other author programs: SIN211, COS216, EXP194, LOG341, SQRT378, DIV768, MUL1742. Trained classifier MLP CPU 0.514042433 seconds. **215** intermediate compositional AST source programs constructed by general typed graph generator, with primitive semantics restricted to programmer-specified list. All proposed full expressions, numerical proposal validation and source-only CPU budget sealed before ANY fifth32 true source formula was opened in the third job. Source prediction artifact first SHA256 `f3c954e097c93813a7b131d9b49b377ce76ec8e2ad191573aac0c4f3a45b85b8`.

## Decisive independently verified negative, *same external original32*
Immutable FIRST real full author symbolic-equivalence grader third job complete original32 receipt SHA256 `eeac8e96fb1618778c2ec088017c69c44639e08f4e7dee1df02a4643e85793b7`.

| Source-only same-primitive method | certified whole original expressions | no exact proof |
| --- | ---: | ---: |
| **D learned-operator scoring, 28 induced AST features, one/two-feature source program proposals** | **0/32** | 32 |
| **C no-learn static order, 28 induced AST features, same one/two-feature source program synthesis procedure** | **5/32** | 27 |
| **A classical wider grammar enumeration, all 215 induced AST features + same proposal checker** | **5/32** | 27 |
| Neural-only exact originals beyond A and C | **0** | n/a |

Source-only numerically fitting complete candidate programs were produced for learned D in **1/32 cases** but **0/1 passed full author mathematical expression equality**, so nothing in D is an established helpful true structural discovery. The C/A source-only procedure found numerical candidate(s) for 6/32 cases, **5/32 full author exact**, so the independent external verifier correctly rejected one misleading numerical fit. Both C and D use **same 28-feature allowance** but different ordering, so learned failure is not solely due to classical A having a larger budget. A is a *wider* grammar (215 features), NOT strictly cost-matched to D; do not call it an equal-CPU state-of-art PySR/Operon challenger. The whole candidate feature generator remains limited to human specified typed operators and two-feature compositions; no unbounded typed invention.

No wrong non-matching original source was admitted as certified. The above scores are ORIGINAL author full analytic formula equality, not first 40 or 48 numeric curve fits. Exact task original input on public benchmark, neither secret ERBench leaderboard nor independent-author challenge because train/test are split from same benchmark.

## Scientific verdict
- `ACTUAL_NEURAL_WEIGHT_TRAINING=PASS`: 1903 distinct author original training examples and fitted MLP weights.
- `EXECUTABLE_COMPOSITIONAL_AST_GENERATOR=IMPLEMENTED`: 215 human-primitive-language intermediate AST programs generated, numeric proposals sealed before author grading.
- `Q3_LEARNED_NEW_USEFUL_COMPOSITE_EXPRESSION_ON_UNSEEN_AUTHOR_SOURCE=FAIL_0_OF_32`.
- `Q3_NEURAL_EXCLUSIVE_VS_NONLEARN_SAME_28_FEATURES=FAIL_0_VS_5`.
- `Q3_LEARNED_NEW_SEMANTIC_PRIMITIVE=NOT_PROVED`.
- `Q4_ALL_IN_TOTAL_COST_10X=NOT_PROVED`; `Q6_CROSS_AUTHOR_TRANSFER=NOT_PROVED`; `Q7_FRONTIER=BLOCKED`; `G1=HOLD`.

## One scientific redirection, not more minor tuning
**DO NOT claim this as autonomous expression invention** merely because the construction code emits ASTs. Most structural choices still originate from human-written expansion rules and the neural ranking fails to select useful program structures. The only future valid Q3 scientific mechanism must LEARN actual new typed graph construction decisions or a new executable learned abstraction, accept counterexample-driven correction, and demonstrate **strictly verified original author target gains beyond a same-rights classical program synthesis baseline** on a first-use independent family. Merely changing ranking weights or expanding the fifth32 after labels were opened would be posthoc evaluation leakage.

This trial conclusively excludes *the specific frozen learned top28 operation presence ranking* on fifth32 as a viable current demonstration. It does NOT prove the global impossibility of learning structural ideas or claim all learned search is inferior. Exact original source and all failures remain in immutable first Actions artifacts. No GPU or paid model resources used.


## Mechanistic source-code audit, after original truth was opened (not a new blind result)

The FIRST frozen learned scorer (line `key=lambda e:(-sum(ranking[op] for op in consumed_ops(e)),sp.count_ops(e),len(str(e)))`) **rewards the sum of positive predicted operator-use probabilities for all distinct operator types that appear in an expression**, while *omitting negative evidence for operators predicted absent*. For fixed learned probabilities `p(op)>0`, adding a new distinct operator type increases the rank score by `p(op)`, even when that operator is unlikely and increases grammar complexity. The length/complexity key applies only when operator sums tie. This is a **provable model-design confound**, not an empirical mathematical discovery: the score is not a calibrated posterior for the entire AST, and it could prioritize complex irrelevant terms above simple needed terms. It plausibly explains the observed 0 learned vs 5 fixed top28, but no causal ablation replacing this scoring rule has yet been run, so do not claim that this bug fully caused the observed failure.

A properly differentiated later model would need to learn explicit **conditional graph construction decisions** from counterexample feedback or supervised successful programs, use valid normalized program probabilities including negative operator evidence and depth prior, and be frozen before evaluation on another genuinely untouched source cohort. Merely tuning the score on these opened 32 original tasks is not an independent capability demonstration. The first fifth32 results stay `LEARNED_EXACT=0` with original SHA-receipts unchanged.
