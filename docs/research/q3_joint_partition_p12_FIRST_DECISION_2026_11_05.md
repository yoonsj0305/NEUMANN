# NEUMANN P1.2 first result · P1.1→P1.2 STOP · 2026-11-05

North Star: **Frontier-level problem solving with minimum necessary computation**. Preserve P1.0 0/32, P1.1 1/24 vs 1/24, and all Q1–Q7 globally OPEN.

## First outcome (public opened ARC-AGI-1, new 24 registered IDs)
- P1.1 frozen classical object baseline **B 1/24 original exact**.
- P1.2 **J: jointly hypothesize object partition and transformation** **1/24 exact**, **+0 additional original tasks**, **0 lost**. Original task `c8f0f002` was solved by the frozen B, so J added no new solutions.
- J considered **27,048** typed program candidates (1,176 for each of the 23 B-abstaining tasks), with no successful new original-task result. B attempted 12,000 for all 24.
- Study-only `Date.now` aggregate: B **1,810 ms** (including original proposals); **5,590 ms** additional J search, excluding source download, verifier deployment, framework cold start, energy and monetary cost. Not iso-capability improvement. Measured end-to-end CPU FLOPs, joules, peak memory, dollars UNKNOWN.
- One previously unseen-to-this-code scene yielded 112 programs fitting training examples, but this did not yield a new verified test solution. Distinguish *hypothesis count* from *useful ability*. First results retained individually in four six-task shards plus one aggregate receipt.
- Registration froze 24 file IDs, source commit, B/J code blob SHA, budget and fail-closed policy before opening task bodies. The 24 tasks exclude P1.0's 32 and P1.1's 24 and four hand-inspected development tasks.
- No JEPA trained, no GPT-proposed operators, no neural model calls, no genuine primitive invention, no frontier-gap proof.

## Mathematical diagnosis: why another selector cannot solve a missing program
For frozen executable hypothesis space H and observed pairs D, define H_D={h in H: for all (x,y) in D, h(x)=y}. If H_D is empty then any selector `π(D)` constrained to choose h∈H **cannot** output a training-consistent h; smarter semantic ranking, representations or cost routing cannot repair that deficiency without changing the candidate-generation interface. This is a conditional set-theoretic result, not an impossibility theorem for AGI or unseen hypothesis spaces.

For the P1.2 extension, 27,048 candidate ASTs supplied only the same hand-built perception and transformation inventory. Candidate generation was broader than the P1.1 inventory, but still finite; insufficient hypothesis coverage and ambiguity remain.

## STOP and redesign
Do not tune these 24 scored tasks and call them fresh. Do not prolong fixed-grid/connected-component heuristics with another hand-chosen selector list. Treat P1.0-P1.2 as independent negative evidence on progressively expanded **human-authored finite hypothesis** approaches, not a rejection of structural intelligence.

The next admissible trial needs an *open-ended executable operator proposer* (e.g. frontier-generated code only as a clearly identified **teacher**), strict training-only input contract, a sandboxed independent original-task checker, source/test-answer separation, immutable first-run results and controlled cost. It must not be portrayed as a small learned NEUMANN solver or a 10x compute result merely because a GPT frontier teacher solves original tasks. If the teacher produces candidate new code, typed AST verification/compilation and reusable abstract macro extraction form the real NEUMANN research target. Strong deterministic and task-specific direct baselines remain mandatory.

## Prior art
DreamCoder (Ellis et al., PLDI 2021) provides wake-sleep learning of reusable program abstractions and search policy; recent object-centric ARC research notes that object identity itself depends on the task. Neither segmentation hypothesis enumeration nor classical program synthesis is novel. Reuse and cross-domain generalization must beat a meaningful strong classical alternative.

**Decision:** P1.2 local first gate FAIL_NO_JOINT_PARTITION_HEADROOM; global Q1–Q7 OPEN; next generative program-proposal gate NOT RUN as of this decision. No auto merge or sealed data opening.
