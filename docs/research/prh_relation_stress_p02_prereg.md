# P0.2 preregistered stress test, frozen before first actual execution

Scope: guarded geometric correspondence on fully observed same rigid scene, not general cross-modal intelligence, new algorithm invention, JEPA learning, Q3 or Q4 closure. Base code: immutable P0/P0.1, PR #617; existing JSON receipts unchanged.

**Research hypothesis**: a full-scene metric fingerprint can transfer across previously unseen rotations if two modalities observe the same finite set and metric; without these assumptions, similarity scores can be ambiguous or misleading. Kill unconditional integration if ambiguous or incompatible views are accepted. Include degraded mode.

Frozen conditions: 4 new seeds `46001..46004`; n=128, d=8, noise standard deviation=0.035. Each seed has rigid same scene; independent unpaired world, nonlinear tanh(3z) metric warp, partial scene (drop 16 items), and perfect symmetric +/- orthogonal basis set (16 elements). No model retraining, tuning, reruns, labels during matching. The evaluator uses latent indices **only to score** after matching; the matcher cannot access them.

Provisional protection gate: full rigid-scene matching recall >=90% and accepted for all 4, unrelated worlds never accepted, symmetry never accepted and all partial views rejected. A geometry-error accept threshold of 0.08 was chosen using earlier P0.1 diagnostic and therefore *not* independent confirmation of that threshold; new P0.2 seeds are disjoint, but this is an exploratory dev gate. The nonlinear cell is diagnostic and does not disappear when it fails. **No post-results threshold change**.

Resource: report per-cell wall-clock nanoseconds. Additional SVD/NN/deployment training is not measured and energy/FLOPs/RAM/money are UNKNOWN. Assignment O(n^3) with O(n^2) memory; do not claim 10x savings. Q1-Q7 stay OPEN.

### Downstream decision

Whether this geometrical tool is worthwhile for NEUMANN should be determined only when it improves an **original verified executable task** over cheap deterministic canonicalization and strong Direct, including its own full cost. If a hard negative or symmetry is ambiguous, return ABSTAIN and fall back to original-task Direct. Do not force geometric match.
