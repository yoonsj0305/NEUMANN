# NEUMANN 1 | P2.9 Prospective ARC48 FIRST: +1 exact, independently replayed, threshold FAIL

Date 2026-11-05. North Star: Frontier-level problem solving with minimum necessary computation.

## Scientifically authoritative results
- P29 program synthesizer: `experiments/q3_p29_induced_coordinate_programs.mjs`, human-authored bounded symbolic coordinate/shape/color metagrammar. **No learned neural model, no learned new opcode**.
- Public ARC data/training original **400 opened**: P29 19/400 exact; P29 false submissions 1; five existing classical TOOL arms combined 39/400; after addition 50/400 exact (+11). Combined wrong submissions 8 (not safe).
- This is developmental evidence, not an untouched generalization result. See [matched 400 original audit](https://github.com/yoonsj0305/NEUMANN/actions/runs/42022318273).
- 48 **new public ARC-AGI-1 data/evaluation tasks**, registered solely from filenames before inspecting original task bodies; 280 earlier evaluation filenames excluded; 72 untouched public evaluation filenames left.
- First real original run [#42022927624](https://github.com/yoonsj0305/NEUMANN/actions/runs/42022927624): old five classical TOOL consensus 1/48, P29 alone 1/48, safely combined **2/48 (+1)**, 1 P29 submission, 0 P29 wrong, 0 combined wrong, 0 old exact lost. 35/48 found a possible shape expression, but only 1 found an executable exact TRAIN-fitting program.
- First raw JSON receipt SHA256 `f20af6575a6479f36352ab95df8883aa4d17e366c3de355735c96c4d4bd37ed8`; artifact `NEUMANN-P29-FIRST-FRESH-ORIGINAL48`.
- Precommitted prospective local gate: >=2 additional exact, 0 new wrong, 0 old lost. Observed **+1** -> `P29_FIRST_FRESH_TRANSFER_FAIL_OR_UNSAFE`. No favorable re-evaluation of this cohort.
- Independent alternate-language original checker [#42023374911](https://github.com/yoonsj0305/NEUMANN/actions/runs/42023374911) PASS: retained first source bytes, source Git blobs, 280 prior exclusions, filename-only 48 selection, all original evaluation source JSON SHA256, re-executed original AST in Python on full TRAIN and original TEST. Correct original task ID **`0692e18c`**, 1/1 predicted P29 submission; no wrong. Fake 48 successes rejected by auditor.
- Important boundary: old five classical solvers' own internal predictions not independently reimplemented in the Python auditor; their scores and flags are hash-locked to the first source-executed result.

## Scientific interpretation
**Positive:** This is one observed out-of-sample *same ARC benchmark domain* example of a generated, executable typed coordinate program, correct on original TEST; it is new relative to the five previously existing classical source strategies.

**Negative:** The 2-additional threshold failed; 1/48 is not enough to establish robust generalization. It is **not** cross-semantic-family Q6 transfer, Q3 autonomously invented opcode, inference from training a neural discovery policy, or 10x end-to-end compute advantage. The same 81/P29 expanded hypothesis grammar could be searched by classical TOOL; P29 itself is deterministic classical program synthesis.

## Decision and next admissible test
Stop reranking P29 on these 48 and stop same-source regex/coord tweaks that see the first result. Preserve untouched remaining 72 evaluation originals until a *new architecture* demonstrates stronger headroom on already-opened development, including independently executed new composition rules and stricter abstention on uncertain extrapolation. For any next original test, freeze source, cost budget, register fresh evaluation IDs and independent verifier first. Do not claim full Q3/Q6/Q7 closure.
