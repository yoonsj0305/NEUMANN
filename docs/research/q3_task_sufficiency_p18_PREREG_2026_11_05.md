# NEUMANN 1 P1.8 | Task sufficiency of good-view representations (pre-registered)
2026-11-05 KST. North Star: **frontier-level problem solving with minimum necessary computation**. Global Q1–Q7 OPEN.

## Question and formal claim
The October 2026 JEPA/PRH preprint (Balestriero & LeCun, arXiv:2610.39302) concerns learning similar latent representations from good views of the **same scene**. Even perfect shared-scene identification does not guarantee that a decoder can choose an executable action if the *goal instruction is omitted*.

Let S be a scene, T∈{0,1} uniform independent goal, V1=S and V2=vertical-flip(S), so both views perfectly determine the same scene. Let target Y=f_T(S) where f0=identity and f1=horizontal-flip. Require S ≠ horizontal-flip(S). Every scene then has two equally likely different correct outputs and identical scene-only views. Therefore `H(Y|V1,V2)=H(T)=1 bit` and any deterministic predictor `Yhat=g(V1,V2)` has exact-output accuracy at most **50%** over this balanced distribution. Goal-aware `Yhat=f_T(V1)` can achieve **100%**. The limitation disappears if the decoder or representation retains T. This is a *conditional sufficiency counterexample*, **not a refutation** of the JEPA PRH theorem.

## Frozen independent computational check
- Random generator `numpy.default_rng(20261105)`, 2,048 unique asymmetric binary 6×6 scenes, iid Bernoulli(p=0.30); resample only when a scene equals its horizontal flip or duplicates a previous scene (declared construction constraints).
- For every scene generate BOTH goals and both exact outputs: 4,096 original task records. Scene-only views V1=S,V2=flip_vertical(S) are same regardless of goal; no label/goal leakage into scene-only encoder.
- For each pair compute the maximum possible scene-only deterministic correct responses, count exactly 2,048/4,096. Goal-conditioned interpreter f_T must score 4,096/4,096. Count distinct conflicting outputs and conditional entropy analytically and by empirical conditional counts.
- Strict first local gate: scene-only Bayes optimal 0.5, goal-aware exact 1.0, each scene has two distinct target grids, all deterministic multi-view images recover the same scene. Any deviation FAIL without revising seed/corpus.
- Independent code checks and immutable first JSON receipt. This is a proof illustration on a constructed distribution, **not a natural problem benchmark**, neural model training, novel operator discovery, Q3/Q4/Q7 improvement or 10× cost proof.

## Design implication, to be tested later
For useful NEUMANN representations, require *task-conditioned sufficiency* of Z for original executable outputs or validated subgoal decisions, not merely similarity of encoders. If the goal is visible separately to a downstream solver, task information need not be inside Z itself; the **joint decision interface (Z,T)** must be sufficient. Task-goal labels should never be smuggled from a test oracle. JEPA-style learned good views may still be valuable when conditioned on goal and independently verified. The exact P1.6 quotient remains the cheapest credible baseline for eliminating duplicate executable work.

Global Q1–Q7 remain OPEN. No auto-merge or sealed data affected.
