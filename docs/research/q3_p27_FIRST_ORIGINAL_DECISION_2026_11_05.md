# NEUMANN 1 | P2.7 최초 공식 평가 FAIL · 구조 생성 병목 판정
2026-11-05 KST. North Star: Frontier-level problem solving with minimum necessary computation. Q1–Q7 OPEN.

## Immutable evidence
- First official original evaluation [run #42003978711](https://github.com/yoonsj0305/NEUMANN/actions/runs/42003978711) completed its 400-task meta-training and 32-task heldout scoring. Its CI showed failure ONLY because the subsequent validation referenced meta_training_tasks at the top level instead of within stats. The first COMPLETE 32-task artifact was preserved as artifact #13402994617.
- Original first-result raw JSON SHA-256: c472a96a4b1dc1cbe5e8292323a69455a1ac4deec2c38e27ac3c887a74346671. Do not overwrite.
- [Independent replay #42004559375](https://github.com/yoonsj0305/NEUMANN/actions/runs/42004559375) PASS: confirmed original raw hash, frozen engine/cohort/source identities, official original task IDs, regenerated every learned/classical original prediction and scored all 32 original targets. 0 mismatches.
- Auditor was unchanged. An audit-only adapter promoted the existing stats.meta_training_tasks into a top-level metadata field in memory; no original file or solver changed. Pre-evaluation controls passed 8/8.

## Frozen source and public original cohort
ARC-AGI-1 upstream commit 399030444e0ab0cc8b4e199870fb20b863846f34. Six earlier original public evaluation cohorts contain 200 unique IDs; new 32 filenames were preregistered by hash from the other 200 before opening content. The evaluation is public, NOT private/sealed or guaranteed free from pretrained LLM contamination.

P2.7 learner trained its cross-task program prior from the 400 official public data/training tasks and found just 9 correctly generalizing meta-task programs. Language: 12 HUMAN-defined atomic functions, maximum 2 composed operations, 157 exact AST candidates, 0 teacher calls, 0 neural forward calls. This is learning a candidate preference, not autonomous opcode invention.

## First original result, independently checked
- Frozen B/P20/P24/P25 combined baseline: 2/32 original correct, zero baseline conflicts.
- P2.7 exhaustive classical in the SAME compositional grammar: 0/32 correct, zero false accepted, all 32 ABSTAIN.
- P2.7 cross-task learned-frequency prior under the IDENTICAL 157-candidate grammar and budget: 0/32 correct, zero false accepted, all 32 ABSTAIN.
- Exactly 5,024 AST candidates examined by EACH new arm (32 x 157).
- On 31/32 original tasks, NO TRAIN-consistent P2.7 program exists. On remaining 1/32, a program fits TRAIN but tied test-time execution is unsupported; no safe original prediction.
- Learned additional correctness over classical: 0; over legacy baseline: 0. P2.7 local gate FAIL_OR_INCONCLUSIVE.
- First runner numbers: summed classical P2.7 inference 71.722 ms; learned P2.7 inference 66.617 ms; meta prior training 534.970 ms; sum learned meta+inference 601.587 ms; entire first script 4,110.761 ms; sampled process RSS 162,963,456 bytes. No energy/dollar/full-system 10x cost measurements. All numbers scoped to one runner.

## Root cause theorem and decision
Let H be the frozen complete candidate language and D original TRAIN pairs. Let F(D,H) be programs h in H that exactly replay all TRAIN examples. If F(D,H) is empty, no selector, neural reranker, prior or extra ranking compute can produce a TRAIN-consistent program drawn from H. P2.7 has F empty for 31/32. Learning higher-quality selection weights on that H cannot change this upper bound. Only 9/400 positive meta-training successes also provide an inadequate source of cross-task positive supervision for broad novelty.

STOP tuning fixed-grammar ranking, adding manual Boolean splits and making beam/depth larger without changing executable meaning. The P2.6 31/31 source-language impossibility finding and this independent P2.7 FIRST FAIL point to the same missing capability: new structural semantics.

KEEP strong cheap classical Direct; original-first prereg; code/source locking; exact execution proof; fail-closed ABSTAIN; accounting for all model/training/proposal/verification/fallback costs.

## P2.8 next decisive design contract [PROPOSED, NOT RUN]
1. **Invent structurally new typed operators.** From original TRAIN examples, propose reusable executable object-relation, geometry and goal-conditioned transformation schemas not already present as complete programs or primitives in a frozen grammar. Prove novelty by source-equivalence testing against the old grammar, not prose descriptions.
2. **Learn from failures.** Supervise from partial exact outputs and causal counterexample distinctions for the many meta-training tasks the old language cannot solve. Reject task-ID lookup, test-label use, whole-example memorization, prior teacher program copying or arbitrary opaque functions with no generalization.
3. **Independent control.** Match a strong classical synthesizer given the SAME new combinators, inputs and budget. Compare learned invention benefits separately from mere vocabulary expansion.
4. **Fresh-transfer prereg.** Exclude all older evaluation IDs. Freeze a new original ARC cohort and independently generated heldout DIFFERENT semantic family before construction/evaluation; preserve first outcomes even if FAIL. Return ABSTAIN on unverified/ambiguous/OOD/over-budget cases.
5. **Proposed ASSUMPTION gates:** >=16/32 fresh original TRAIN tasks represented by concise source-verifiable non-memorization ASTs; >=2/32 extra original exact correct over strong matched classical; >=1 independent cross-family transfer; 0 newly false accepted submissions; full all-in training+discovery+verification+fallback cost recorded. Not achieved results.
6. Q1–Q7 remain OPEN irrespective of any synthetic local PASS.

## Immutable implementation and references
- docs/experiments/q3_p27_COHORT_FROZEN.json
- docs/experiments/q3_p27_SOURCE_FROZEN.json
- experiments/q3_compositional_schema_learning_p27.mjs
- experiments/q3_compositional_schema_learning_p27_scorer.mjs
- experiments/q3_compositional_schema_learning_p27_first.mjs
- experiments/q3_p27_independent_audit.mjs
- Original artifact [#13402994617](https://github.com/yoonsj0305/NEUMANN/actions/runs/42003978711/artifacts/13402994617)
- Independent audit [#42004559375](https://github.com/yoonsj0305/NEUMANN/actions/runs/42004559375)

Scientific conclusion: P2.7's learned prior **did not discover any additional original-task capability**. The generator's hypothesis language, not selector ranking, is the decisive bottleneck in this frozen experiment.
