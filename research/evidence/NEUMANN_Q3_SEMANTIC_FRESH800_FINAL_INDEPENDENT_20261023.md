# NEUMANN Q3 semantic structural quotient: first true fresh-seed closed evidence

Date: 2026-10-23 KST. PR: https://github.com/yoonsj0305/NEUMANN/pull/529
**Authoritative independent 3-stage GitHub Actions**: https://github.com/yoonsj0305/NEUMANN/actions/runs/39886652275 (**ALL 3 SUCCESS**).

## Core question
Can a model infer the same *function* even if hidden block shape/phase/permutation is not uniquely identifiable? Given four controlled 8x8 full-state before/after transitions, a nine-template **human-specified** family of local block-permutation models, and no true family tag in source input, perform minimal-description symbolic program fitting; use exhaustive finite local influence-bit proofs to merge internally distinct but universally functionally equivalent programs. Fail-closed UNKNOWN outside grammar.

## Provably sound local semantic equivalence
For two block programs with blocks <=2x2 and periodic partition phases <=2, each output cell depends only on the union of that cell's two candidate input blocks. Enumerate EVERY assignment of that union and all 4 output parity classes. If all output bits match, the functions agree on **every possible binary grid state on every even toroidal h,w >=4**. The proof is valid because neither operator accesses any input cell outside its two local block supports; parity translation replicates the local mapping across the whole grid. Inequivalence returns a concrete counterexample with input support and output coordinate. No truth metadata is required for this pairwise equivalence theorem.

**Post-grade discovery (not new validation)**: prior 960 original/source examples passed semantic equivalence to their known native programs 960/960, including 12 previous ambiguous minima and 13 distinct representations (https://github.com/yoonsj0305/NEUMANN/actions/runs/39886327188). The new quotient logic was adopted only AFTER this exploration, so all such numbers remain *development evidence*.

## Fresh untouched, code-pinned, genuinely separate-seed test
Pinned code Git blobs were hard-checked BEFORE generating new data:
- initial nine-template symbolic grammar: `2d24f0ebbd3d01e3a62724339754f2eea09ffe51`;
- all-input local program equivalence theorem: `f21137cc4b6961330c184ce6152d7f1136662b87`;
- different flat-index verifier: `78f15d4968290f1fbc4c2032822b617050785c47`;
- fresh800 generator/inference/scorer script: `950f67927a8fe74e668ade2fbaf19a360ede9461`.

The fresh generator seed was `202610241253`. 800 **unselected** tasks: 160 each 1x1, 1x2, 2x1, 2x2 block permutation (640 in-grammar), plus 80 one-step XOR-down and 80 XOR-right neighbor-dependent rules (160 **outside** the grammar). Source records had no family label, shape, phase, permutation, or withheld targets. Distinct source generator, source-only model, and independent truth-grader jobs; source model predictions were SHA sealed before original laws and 3 larger-grid holdouts became available.

Original blinded source SHA256: `8cd5baac19694e04a34ef4ef1c89b29c5744ef1da21253a3e08a097e7465b729`.
Prediction-seal SHA256: `226f85702f5239639221c162fa5b7add0f3288a9d36e4c5f1703ebdb777afc06`.

### Final independent grading
| Metric | Observed |
|---|---:|
| Fresh supported in-family tasks | 640 |
| Source-only CERTIFIED_UNIQUE_SEMANTIC_OPERATOR | **640/640** |
| True program syntactically identical | 598/640 |
| Distinct internal program, **universally equivalent** by local proof | 42/640 |
| Proof of true one-step function semantic equality on all even h,w>=4 | **640/640** |
| Unsupported 2D XOR-neighbor tasks | 160 |
| Unsupported correctly abstained UNKNOWN_NO_CONSISTENT_PROGRAM | **160/160** |
| Unsupported incorrectly admitted | **0** |
| Held-out 12x12 exact full transitions | **640/640** |
| Held-out 14x18 exact full transitions | **640/640** |
| Held-out 30x34 exact full transitions | **640/640** |
| Total held-out whole-grid verifications | **1920/1920**, 0 wrong |

Third-party independent benchmarking of a novel learned architecture was **NOT PERFORMED**. The 800 fresh cases are original *computer-generated from four predeclared local families and two predeclared nonlocal controls*. Strong other computational frameworks might easily achieve the same accuracy. The finite grammar is known, and calibration oracle is a rich intervention interface not necessarily available in real-world problems. We have a formally correct, source-blind, **conditional structural program abstraction**, not a spontaneous newly invented neural primitive.

## Counterexample / degraded mode
When no entire human-declared local program fits all pairs, do not force the structure into the model. All 160 fresh unsupported local-neighbor XOR controls returned UNKNOWN, with no false submissions. When several minimum-sized syntactic programs fit, certify all-input equivalence and choose a canonical functional representative ONLY if all equal; otherwise UNKNOWN with a concrete output-bit disagreement counterexample.

## Q3/Q4 decisions
- Q3 scoped discovery of unknown local block shape/phase/law *within declared grammar* **PASS**, fresh 640/640.
- Q3 exact target-function recovery across semantically equivalent, syntactically distinct programs **PASS**, fresh 42/42 exact functional proofs.
- Q3 detect out-of-grammar models without hallucinating in-grammar **PASS**, fresh 160/160.
- Q3 unbounded neural-discovered primitive, **OPEN**.
- Q4 efficient inference 10x whole life-cycle, frontier parity, hardware energy benefits, **OPEN**.
- Degraded mode: UNKNOWN on unsupported families and non-equivalent ambiguous minima; no unsupported source prediction admitted.
