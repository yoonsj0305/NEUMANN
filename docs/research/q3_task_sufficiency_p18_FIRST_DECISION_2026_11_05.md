# NEUMANN 1 P1.8 first decision (2026-11-05)

Frozen objective: **Frontier-level problem solving with minimum necessary computation.** Global Q1-Q7 OPEN.

## Exact constructed result

A pre-registered synthetic dataset contains 2,048 unique non-horizontally-symmetric 6x6 binary scenes and two equally likely independent task goals for each, for 4,096 original task records. Input views V1 and V2 are a scene and its vertical reflection, with perfect reconstruction of the same world.

Goal 0 requires returning the scene. Goal 1 requires returning its horizontal reflection. These outputs differ for every scene. A decision based only on V1,V2 must give the same response for both tasks of a scene and therefore can get at most one task correct per pair: **2,048/4,096 = 50%**. With the goal available to the executor, both are correct: **4,096/4,096 = 100%**. Conditional output entropy **H(Y|V1,V2)=1 bit**. The pre-registered local construction gate PASS. Four independent Python tests PASS; all first source and JSON records retained.

### Scope of the conditional lemma

When goal T is uniform and independent of the scene views, and the two goals require distinct outputs for every observed scene, the best scene-view-only full-output classifier has expected accuracy 1/2. A decision interface that also receives the goal can be exact. This does not challenge the conditional representation-alignment theorem in Balestriero and LeCun, arXiv:2610.39302. Representation alignment of a scene is a different mathematical property from sufficiency for an independent requested operation.

### Engineering decision

NEUMANN must preserve *both* task/goal and world observations in the joint decision interface, then propose typed executable structures and verify all original-task outputs. Task information can be passed separately to the solver rather than embedded in the representation itself. If the goal is unavailable or ambiguous, ABSTAIN instead of fabricating a program.

P1.5 uniform-vs-evolutionary search failed to improve beyond 1/32. P1.6 exact semantic quotient preserved 24/24 original-task decisions and reduced operator calls 3.62x but failed its 10x local gate. P1.7 contrastive same-operation view learning scored 80.7% on synthetic eight-way operator retrieval, yet only 32.3% on unseen rotations versus a 100% classical exact baseline. Both neural training on P1.7 and the present synthetic construction are insufficient to close global Q3/Q4.

Next original-task gate (NOT RUN): compare a task-conditioned learnable proposer with strong classical Direct and P1.6 exact quotient on a new source split; freeze source and costs before evaluation. Require new verified executable task capability and complete discovery, validation, inference, fallback and amortized training cost. No scored cohort reuse or sealed evaluation unlock. All Q1-Q7 remain OPEN.
