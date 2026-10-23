# NEUMANN 1 Q3/Q4 · Sharp exact seven-query grammar-identification gate | First external original fourth32

**Scientific execution (2026-10-23 KST):** [PR #540](https://github.com/yoonsj0305/NEUMANN/pull/540). **FIRST untouched original-source three-stage run** [GitHub Actions #39905500072](https://github.com/yoonsj0305/NEUMANN/actions/runs/39905500072) **three jobs SUCCESS**. **SEPARATE immutable-first-receipts postgrade truth audit** [GitHub Actions #39905927719](https://github.com/yoonsj0305/NEUMANN/actions/runs/39905927719) **SUCCESS**.

## The theorem: seven observations are worst-case NECESSARY and SUFFICIENT (conditioned on grammar)

Consider `R_(4,2) = { f=P/Q ∈ Q(x) : deg P≤4, deg Q≤2, Q≠0 }`. If two candidates `P1/Q1` and `P2/Q2` agree on **seven pairwise distinct rational query points where denominators do not vanish**, the polynomial `P1 Q2-P2 Q1` has degree at most 6 and seven zeros, hence identically zero. The functions must agree for all x on their common domain.

**TIGHT 6-point counterexample verified exactly.** Take
`f1(x)=x^4/(x²+1)`
and
`f2(x)=(11x^4 + 1029x³ + 904x² − 1764x + 720)/(10x² +1050x + 740)`.
Both are rational functions within `R_(4,2)`; for x=1,2,3,4,5,6 they are identical and all six finite, but at x=7 their exact difference is `6/3575`, nonzero. Therefore no universal rule-identification protocol requiring at most six exact rational oracle evaluations can uniquely identify every member of this class. There is a seven-query sufficient interpolation algorithm below; **worst-case exact query complexity is seven** for nonadaptive distinct finite query points with functions defined there.

These results follow from established elementary algebra; neither theorem nor counterexample is claimed as new to mathematical literature. The hypothesis/grammar `R_(4,2)` and query oracle are explicitly supplied by a HUMAN, not a learned neural agent.

## Authentic external full original input provenance and physical information isolation

External author EquationDiscovery **ERBench PUBLIC training dataset** pinned HuggingFace source commit `95bf15c27de68c3f170ca6140d2e4a811c60344f`, complete original 10,000 row CSV SHA256 `03c0ceb53ed0348650c0a94ed5cd1e452325d2b7c7d3be68f9a458316eda33b1`. Static original 1D filter yields 5717 eligible formulas. Fourth prospective original cohort is SHA-rank metadata positions **2096..2127 inclusive (32)**, disjoint from all previously experimentally opened 1D cohorts ranks0..95 and source supervised learner ranks96..2095 (though all tasks originate in the same PUBLIC benchmark).

1. Job #1 independently generated **exact rational** oracle replies by calling actual original analytic formula on rational inputs in its support, recording ALL attempts and producing source-only `x,y` without original function text. Original source/formula truth is retained in a physically separate secret-only grader artifact. First source-only JSON SHA256 `151c9e2e2731d50fefc1e75b56c58b3971067a058cff77c04cdc67033cdb420a`, separate private true original metadata SHA256 `8f7bd5ed2ca2cd9c8c39e72f6a2ad830b409815d2fb7c522c820874fd56875e1`. **Total source oracle attempts across all 32 cases = 338**, including unsupported/nonrational, not seven per each task. **13/32 original tasks** supplied exactly seven valid rational pairs.
2. Job #2 never sees original analytic formula and uses **CLASSICAL exact rational linear algebra** on seven points to recover `P_4/Q_2` coefficients. It cycles exact denominator coefficient pivots, sets rational free parameters by fixed rule, verifies all seven source points exactly, and freezes its predictions before grader runs. All 13 query-sufficient cases generated syntactically executable exact rational candidate programs, **0 wrong answers submitted as certified**. Candidate generation total measured CPU `0.318376887s` (EXCLUDES expensive original exact oracle computation, runner boot, package downloads, grader). Pre-grade predictions SHA256 `03eb04ca69d2630f46f122af9e26bdb73701d32f2b893e04b0a25a3de9dc3e07`.
3. Job #3 physically reads the private true author expression ONLY AFTER source-only SHA is already sealed, compares the full analytic source formula with the candidate using exact SymPy rational/function symbolic equality over x, never merely approximate RMSE. First independent original author grade: **7/32 exact full original formulas, 6/32 rejected as genuinely non-equivalent, 19/32 abstained**; complete grade SHA256 `fa22a50316b5f33ea2716048998c3d53fb6c75b296c3fd88c1634545372d9a99`.
4. Independent later SHA-authenticated **POSTGRADE** original syntax audit on EXACT unchanged three artifacts (SHA pinned above), report SHA256 `ecdfd92a2eebc3c30a61c35d7ca98192b6f33627863aa846c5dda459a7df333b`: **7 originals INSIDE_EXACT_P4_Q2, 6 originals RATIONAL_OUTSIDE_DEGREE_CAP, 19 originals OUTSIDE_RATIONAL_FUNCTION_CLASS**. All **7/7** truly in-grammar original formulas were correctly reconstructed from exact source queries; **all six** apparent seven-sample-fit candidates whose original target was out-of-grammar were properly rejected by the independent original-formula symbolic verifier. The 19 nonrational originals were not independently exact-reconstructed, and the oracle declared UNKNOWN. This postgrade diagnostic does NOT rebrand the fourth32 as a new blind cohort.

## Precisely certified outcomes

| Claim | Evidence | Status |
| --- | --- | --- |
| Seven distinct exact finite rational point responses uniquely identify a function *within the declared P4/Q2 rational grammar* | General all-degree upper bound 6 cross-product roots | **MATHEMATICALLY PROVED** |
| Six are not universally sufficient for this class | Two explicit rational functions same at x1..6 and differ at x7 by `6/3575` | **MATHEMATICALLY PROVED** |
| Original author tasks in declared grammar reconstructed exactly | **7/7** within-grammar public-original fourth32 verified against entire author analytic functions | **PROSPECTIVE SCOPED PASS** |
| Outside-grammar apparent matches do NOT become false certified rules | **6/6** source candidates rejected at independent original verifier | **PASS** |
| Honest abstentions on source tasks with no seven rational outputs | **19** cases unavailable | **PASS** |
| No unverified program treated as certain correct | **0 false certified** | **PASS** |
| Neural training autonomously discovers new typed grammar operators | **No model trained here**, grammar fully provided by researcher | **NOT TESTED / Q3 OPEN** |
| Whole-system query cost or CPU >=10× improvement vs original 48 **approximate** observations | 338 charged exact oracle attempts, different input fidelity and costs, no matched end-to-end benchmark | **NOT PROVED** |
| Transfer beyond author/public/secret and frontier parity | Public ERBench and conditional source grammar only | **NOT PROVED** |

### Research significance and caveats

This is a **sharp, reproducible information-complexity mechanism** for minimizing necessary exact information *under a falsifiable declared representation class*. It solves the previous unrestricted finite interpolation identifiability barrier ONLY because the grammar here is bounded. It is NOT a new class of self-improving AI; it is standard classical algebra, source oracle values have higher information precision than the former 48 IEEE754 numeric samples, and obtaining exact outputs can be more expensive. Successful 7/7 within-grammar authentic original recovery does not establish outside-grammar competence or a learned primitive discovery.

**G0 restricted hypothesis identifiability gate = PASS for class R_(4,2); G1 autonomous learned operator invention = HOLD; Q3 global OPEN; Q4 frontier/10× OPEN; Q6 unseen-author transfer OPEN; Q7 frontier gap unmeasured**. Do not prolong closed-grammar neural routing tests based solely on this mathematically classical success.

[Current parent decision issue #530](https://github.com/yoonsj0305/NEUMANN/issues/530). Source code: `research/g0/erbench_exact7_interpolation.py`, postgrade strict audit `research/g0/erbench_exact7_postgrade_original_grammar.py`. No paid model APIs/GPU.
