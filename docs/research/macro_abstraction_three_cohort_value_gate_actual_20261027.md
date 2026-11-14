# NEUMANN 1 — Macro abstraction learning: actual prospective stop decision

2026-10-27 KST. Existing research branch, no new RC or PR. All global Q1–Q7 remain OPEN.

**Question:** Can mining reusable executable *composite operators* from previously verified solution programs improve novel task capability per bounded compute, rather than just rank a finite known complete-program list?

**Scope:** Pure CLASSICAL symbolic learning, NOT a neural trained model. Six basic unary math op semantics and the entire synthetic task generator are authored; macros are newly learned aliases composed of two or three provided operations, NOT novel fundamental semantic primitives or genuinely external author tasks.

**Chronology:** First experiment source code SHA256 0a93dc6c4ab1a2f0723c900c9927a3b39dd6b8b0b55a26defdb3b84805375153; first prereg commit 070c1fadffc4a22cc9d147a147bee264f2c1c247. Then first 160 opened results frozen and never called independent again. Second experiment source adaptive_library.py SHA256 0060575cf334e1e03fcf4f927c78783dbd4afaaf72e265774178148ea69f0750 and new test seed 20261027 prereg commit ad18940f6b49147b81f9f95b159da88b812f7793. Then second 149 opened result frozen and moved to development. Third experiment source portfolio_gate.py SHA256 e1fd8f9abe52fba6bebd8bc836a37a14b0e5fab79c67446a6ae1a5fd7744036e, new test seed 20261028 prereg commit 1343b2e970af53982046a63b32dbcdf3e98472e5. Exact full 400 train function signatures and 439 TEST function signatures are all pairwise distinct; tested via a second independent arithmetic interpreter on source and unseen future x grids (**1,678 checks**).

| Cohort | Distinct heldout task signatures | Prior-program-trained macro first proposals (5k) | Pure primitives, same 5k proposals | Fully exhaustive classical, depth≤6 |
|---|---:|---:|---:|---:|
| First: frequency5, seed960 | 160 | 65 | 71 | 160 |
| Second: dev-coverage-greedy5, seed20261027 | 149 | 57 | 59 | 149 |
| Third: dev-selected portfolio3, seed20261028 | 130 | 41 | 42 | 130 |
| Combined, THREE DIFFERENT macro policies, so descriptive only | **439** | **163** | **172** | **439** |

Other matched 5k proposal arms: random 5 macro seed controls 57/67/76 of first 160, 48/44/41 of second 149, random 3 macro 34/48/31 of third 130. Third cohort simple frequency3 yielded **46/130**, BETTER than dev-overfit portfolio3 41/130 but lower than the strongest random 48/130. Learned-macro inference 5000 candidate evaluations DOES NOT beat plain classic in any cohort.

**Post-first paired complementarity / double-budget test:** Macro and primitive approaches occasionally solve different tasks: macro-only correct outside C0 = 13,15,16; C0-only correct outside macro = 19,17,17. Union of BOTH candidate catalogues with 10k total program proposals gives 84/160,74/149,58/130, while 10k vanilla primitive-only proposals give **113/160,95/149,81/130**. Therefore naive union is worse even at matched proposal count. This test was conducted AFTER first outcomes and is NOT new prospective evidence.

Developer-source coverage for greedy portfolios size 1..5: 54,77,84,70,68 versus primitive baseline 71. Knowledge addition is NONMONOTONIC. Choosing portfolio size3 using development evidence alone did not generalize. Program source-fit on eight source x's is not a uniqueness guarantee; future inputs scored independently and wrong/HOLD retained.

**Compute:** first c0 64.66ms vs macro5 77.95ms; second c0 56.72ms vs macro5 63.75ms; third c0 60.66ms vs macro3 67.35ms. These are individual CPU program-catalogue-building costs, excluding the separate macro mining/development selection overhead, and are not matched total system resource Pareto. Original first full exhaustive about 837ms, third exhaustive 812ms, which buys 160/160 and 130/130. No joules/peak RAM/USD measured. Neither quality nor comparable compute supports an advantage. No frontier 10x or global Q1–Q7 closure.

**Reproducible source artifact** downloadable in conversation: NEUMANN1_MACRO_ABSTRACTION_VALUE_GATE_20261027.zip; SHA256 cf3783685659bf4fe6cd49ab7b6c2c98126699141b1d2901c157191af5b7a000, 25 entries, ZIP CRC PASS. Fresh extract bash REPRODUCE.sh: 20/20 SHA256 integrity, 8/8 unit tests, 1678/1678 independent arithmetic reference checks, **first prospective candidate-and-score replay** in all 3 cohorts (6+6+7 arms) PASS. Fast replay reuses frozen macro definitions; the more expensive complete macro-development-selection rerun is available as REPRODUCE_FULL.sh, not asserted as verified (single-process full rerun exceeded a runtime limit). Exact source files and first receipts are in ZIP, not falsely described as committed in this GitHub documentation branch.

**Scientific decision:** STOP training or extending frequency/greedy macro libraries on this toy 6-op grammar. Do not train a neural predictor merely to approximate them. DreamCoder and Stitch already develop stronger abstractions, and these negative tiny DSL experiments do not establish scientific novelty. A genuine new NEUMANN discovery admission must involve original externally authored tasks, verified model-weight updates to generate a different executable representation after authentic failures, no exact program cache, A/sham B/strong classical C with complete resource accounting. All Q1–Q7 still OPEN.