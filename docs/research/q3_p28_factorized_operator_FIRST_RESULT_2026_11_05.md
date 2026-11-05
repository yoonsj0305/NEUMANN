# NEUMANN 1 | P2.8 구조 표현력 첫 원본 검증

2026-11-05. North Star: Frontier-level problem solving with minimum necessary computation.

## Latest source diagnosis
- [P2.7 first original result](q3_p27_FIRST_ORIGINAL_DECISION_2026_11_05.md): 31/32 official public ARC evaluation tasks have zero TRAIN-fitting AST in frozen 12-atom depth-2 language. Both learned ranking and same-grammar classical enumerator achieved 0/32 new solves. Q1–Q7 remain OPEN.
- This is a **representation bottleneck**: reranking a set with no valid TRAIN-fitting member cannot make a solution.

## P2.8 implemented
- Gold-blind example-conditioned factorized operator, typed executable AST: `Y[i*h+r][j*w+c]=select(X[i][j], X[r][c])`.
- The selector is independently learned as a 4-entry truth-table conditioned on zero/nonzero of each source cell. Choices are `0`, `outer`, `inner` (81 candidates).
- Exact TRAIN replay of every pair. On multiple consistent ASTs disagreeing at TEST input, safe ABSTAIN.
- **Human-invented factorization representation, machine-selected executable selector.** Not autonomous invention of a general unknown opcode, not JEPA or frontier intelligence.
- Shape proof: 3×3→9×9 cannot be expressed by two operations among the frozen P2.7 crop/rotate/flip/transpose/scale2/tile2 vocabulary. A second scale2 would give 12×12, not 9×9.

## First selected original evidence (not a fresh cohort)
- Source: `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`, public `data/training/007bbfb7.json`; source Git blob SHA `433f607a7e5a42e879811473e500af00eb69c454`.
- **Selection disclosure:** target chosen **after researchers inspected original TRAIN examples and TEST input shape**, but before its TEST gold; not an unbiased or heldout task-selection result.
- First original evaluation of the frozen engine: **5/5 exact TRAIN examples, 81 candidate ASTs, 177 candidate/pair checks, 24 exact TRAIN-fit ASTs, one distinct TEST prediction, exact original TEST 1/1**.
- Independent inline interpreter re-evaluated both TRAIN and TEST predictions; original public TEST gold checked only after producing the prediction.
- Additional eight files from the *previously used* P2.7 evaluation manifest: all **8/8 out of this operator's shape scope**, zero new predictions. Not new/sealed evidence.
- Local Node test suite: **8/8 PASS**: candidate count, exact replay, color transfer toy, invalid input, unsupported sizes, abstention on ambiguous multi-color transfer, P2.7 shape ceiling.

## Scientific decision
- **Local expressivity PASS:** an original public ARC task requiring a spatial relation unavailable in P2.7's bounded grammar was solved by a new program family.
- **Q3 full autonomous new semantic family OPEN:** the high-level factorization template is human chosen, selection biased, and one task cannot prove broad invention.
- **Q4 unseen cross-family transfer OPEN:** one original and synthetic within-family transfer do not establish unknown family generalization.
- **Q5/Q7 all-in 10× and frontier OPEN:** 81 classical candidates; no strong same-language learned advantage, energy costs, or frontier result.
- **Q1/Q2/Q6 global OPEN.** Independent exact replay is not a universal formal proof.

## Reproduction and audit
- `experiments/q3_p28_factorized_operator.mjs`
- `tests/test_q3_p28_factorized_operator.mjs`
- `experiments/q3_p28_original_diagnostic.mjs`
- `docs/research/q3_p28_factorized_operator_PREREG_2026_11_05.md`
- `node --test tests/test_q3_p28_factorized_operator.mjs`
- `node experiments/q3_p28_original_diagnostic.mjs <your-local-ARC-AGI>/data/training/007bbfb7.json`

## Next decisive gate
Prerecord original unseen cohort *before opening targets*, freeze source/compiler and input contracts; invent executable semantic structures beyond fixed source vocabulary from partial exact proof obligations; match a classical searcher with **identical** new semantics/budget; require independent AST replay, unseen semantic-family transfer, no newly wrong submissions, all-in cost benefit. Preserve original FAIL rather than patching against evaluation labels.
