# NEUMANN 1 | Structural representation insufficiency: actual execution and critical failure

**Date:** 2026-11-06. Frozen North Star unchanged: *Frontier-level problem solving with minimum necessary computation*. Scientific decision: **keep formal semantic collision gate; STOP the tiny lexical representation classifier; no Q3/Q6 promotion.**

## 1. New first experiment actually executed

[PR #676 original FIRST run #42204120156](https://github.com/yoonsj0305/NEUMANN/actions/runs/42204120156), branch `research/q3-counterexample-representation-grower-20261106`, original result JSON SHA256 `c05a039ecb371279de66714bafcd1a5b6c05ebc18d7477ce4c77f302d9e21127`, frozen trained policy SHA256 `0e8f31b31e89f211455634fa460605df6d6f53aa67bdf75629b692320f20d276`.

Six **author-constructed training** typed transition ASTs supplied only SMT SAT/UNSAT feedback about insufficiency of destination-only H0. No H1 macro label, gold candidate, or external frontier model was provided. The learner was a **3-weight logistic classifier**; the human-coded general typed AST binder-lifter performed the actual new relation construction. Therefore it is NOT proof of model-autonomous grammar invention.

Eight frozen synthetic evaluation expressions, including affine source transformation and constant write shapes, gave:
- trained decision **8/8** and symbolic INIT+STEP UNSAT / NONVACUITY+WRONG_STORE SAT **8/8**;
- original untrained weights **2/8**;
- stronger same-rights classical direct typed dependency **8/8**;
- training included six actual Z3 SAT/UNSAT oracles, all TRAIN+EVAL evidence **78 Z3 calls**, measured train wall **0.0565s**, complete script wall **0.8145s** and process peak RSS **31,072kB** (not full software development or economic cost);
- no external original CHC full proof, no untouched author/formalism transfer, no novel typed base grammar created by learned policy.

**Scoped first gate**: PASS for the *proof-feedback selection and human typed binder compilation pipeline*. Global Q3 remains OPEN.

## 2. Adversarial frozen test: semantic relevance is not source syntax

[PR #678 first actual semantic test #42204887589](https://github.com/yoonsj0305/NEUMANN/actions/runs/42204887589), using **identical original frozen weights**, without training. Six new preregistered source-free AST expressions included `S-S`, `0*S`, `2*S-2*S`, `7+0*S` plus two genuinely dependent cases. Results:

| Model / algorithm | Correct dependency/representation-growth classification |
| --- | ---: |
| frozen learned 3-weight model | **2/6** |
| original zero-weight policy | 4/6 |
| classical lexical source-mention heuristic | 2/6 |
| actual SMT semantic collision oracle | **6/6** |

Scientifically **FAIL_SEMANTIC_RELEVANCE_LEXICAL_PROXY**. Four syntactically source-reading expressions do not semantically depend on S, so expansion would be wasted computation. The trained policy learned a surface proxy, not minimum necessary information. The first artifact, output and failure are preserved. Early infrastructure attempts #42204704757 and #42204875697 failed **before any semantic evaluation**, due a 63-character transcription of the FIRST JSON SHA. Exact pre-target SHA erratum is recorded; target/cohort/test threshold did not change.

## 3. Independent complete semantic collision proof after first

[Read-only exact audit #42205311728](https://github.com/yoonsj0305/NEUMANN/actions/runs/42205311728) independently reconstructed symbolic collision obligations for the 8+6 **already opened** synthetic ASTs using all integer source array values and arbitrary nonnegative index positions, rather than the initial narrow 0/1-at-index-0 witness. Original learned predictions were NOT rescored or retrained. Exact SMT first-vs-auditor **14/14 decisions agree**, with 14 independent Z3 invocations and process wall **0.24s**. This supports validity of the semantic labels on these restricted types and rule shapes; it does not prove anything for arbitrary NLP, full programs or changed semantics.

The mathematically precise sufficiency predicate for a deterministic task answer f and observation phi is:

`E(phi, f) = EXISTS x,y IN VALID_DOMAIN : phi(x)=phi(y) AND f(x)!=f(y)`.

- `SAT` plus validated concrete witnesses proves **H0 is insufficient** for the task specification (every g∘phi must err on at least one witness).
- `UNSAT` with a **sound, complete decision for the asserted formal domain** establishes f factors through phi on that domain, not that an efficient or easily learnable g exists.
- `UNKNOWN`, timeout, incomplete abstraction, or untrusted solver encoding do **not** justify a PASS or a FALSE status; return UNKNOWN/ABSTAIN.

This theorem is known in representation sufficiency/observational equivalence and abstraction refinement. It is not a new universal model training theorem.

## 4. Remove the wrong thing before optimizing it

Directly inferring necessary variables with SMT semantic witness analysis works on this restricted family and outperforms the learned lexical classifier in the adversarial cohort. The human-designed typed AST compilation also handles these expressions **without training**. Thus for this task shape, invoking a neural selector is not justified by marginal accuracy or cost: **delete neural involvement in the H0-sufficiency decision**. Invoke the native semantic check or a verified static normalization first; use the already-certified classical typed compiler when appropriate.

Future learned research goes only where the current human compiler **cannot compose** an executable missing relation, not where the model can imitate a source-variable presence test. The selected target must have a genuine unsaturated strong-classical residual, a frozen H0 typed grammar, a learned H0-outside proposal **not simply a lifted human rule**, independent verification of all original Horn clauses, equal-language CEGIS/GP and native solver comparisons, and at least one distinct formalism for Q6.

All original benchmark results and their failures remain immutable. Training a new model on the now-opened six adversarial expressions would be development, not a repaired FIRST. No new ARC public-EVAL resources used.

## 5. Evidence boundaries and prior work

- [PR #672 H0/H1 symbolic separation](https://github.com/yoonsj0305/NEUMANN/pull/672): mathematical source–destination missing information theorem, eight typed SMT checks.
- [PR #674 actual already-opened original COPY2](https://github.com/yoonsj0305/NEUMANN/pull/674): **9/9 independent original CHC clauses proved** by HUMAN-written two-array operator.
- [PR #675 proof-reward selection](https://github.com/yoonsj0305/NEUMANN/pull/675): 12/12 synthetic proven from a HUMAN pre-enumerated operator list, classical baseline also 12/12.
- [PR #676 new generic AST binder and collision policy](https://github.com/yoonsj0305/NEUMANN/pull/676): 8/8 synthetic policy with 78 Z3 calls, strong classical 8/8.
- [PR #678 frozen semantic redundancy FAIL](https://github.com/yoonsj0305/NEUMANN/pull/678): 2/6 student vs 6/6 SMT; exact all-index oracle 14/14 agrees with prior first labels.

Nearby academic prior art: COGS (Frankel et al., FMCAD 2026) on counterexample-guided observational equivalence e-graphs; NeuGuS (Kobayashi et al., 2025) on NN weight-guided formula extraction; Latent Program Network (Macfarlane & Bonnet, NeurIPS 2025) on latent test-time program search. This combination requires a clear *new empirical advantage* before any novelty claim.

**Final status:** collision-based insufficiency theorem CONDITIONALLY PROVED; scalar typed AST representation composition **PASS_SCOPED_SYNTHETIC**; learned policy **FAIL_SEMANTIC_OOD**; full original H1 was human-authored; Q3/Q4/Q5/Q6/Q7 global **OPEN**.
