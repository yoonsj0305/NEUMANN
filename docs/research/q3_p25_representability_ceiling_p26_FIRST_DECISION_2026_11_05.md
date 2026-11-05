# NEUMANN 1 | P2.6 Independent P2.5 representability-ceiling certificate
2026-11-05 KST | Research-only, stacked on P2.5 | Global Q1–Q7 remain OPEN.

## First full result, reproducible
[GitHub Actions run #41999187958](https://github.com/yoonsj0305/NEUMANN/actions/runs/41999187958): **SUCCESS**, 7/7 synthetic tests PASS, 32/32 original ARC public evaluation tasks audited against upstream commit 399030444e0ab0cc8b4e199870fb20b863846f34. Machine-checkable per-mode witnesses uploaded as artifact: neumann-q3-p26-representability-certificate.

Frozen P2.5 cohort contained 32 tasks, pre-existing combined Direct baseline correctly solved one. Of the 31 unsolved:
- 9/31 have **no output shape** expressible by any P2.5 mode consistently across original TRAIN pairs. More compute cannot fix incompatible dimensions.
- 22/31 have a **feature collision for every shape-compatible P2.5 mode**. At least two training cells have identical Boolean predicate outputs and identical source-action numeric values (a,b) but differing required target outputs.
- 0/31 remain unclassified by this analysis.

**Theorem.** For a fixed P2.5 mode, let O(x) be (source action values a,b; full actual P2.5 Boolean feature vector). All P2.5 branch nodes depend only on the Boolean features; its leaves output a, b, or a task-fixed color constant. If O(x_i)=O(x_j) while required target y_i differs from y_j, every legal decision tree must output the same value at both inputs, contradicting exact training fit. Consequently, no program using that mode can fit. This holds irrespective of the chosen depth and search beam. If all shape-compatible modes collide, the frozen P2.5 language cannot fit that original TRAIN task at all.

The verifier imports the real P2.5 feature-set builder and P2.4 geometry/feature implementation, then independently checks label collisions. Both files, the cohort, original task IDs, training examples, and actual P2.5 mode counters are integrity-checked. The report contains a source SHA and a short counterexample witness for each mode; **test outputs are not read**.

## Existing experimental economics
P2.5 first immutable results: additional correct original tasks +0/32; 116,766 examined feature splits; 13,664 ms additional local study-region wall time; 0 exact TRAIN fits on 31 invocations. These now have a representation-level explanation rather than only a search-failure label.

[Same-runner paired cost CI #41999803577](https://github.com/yoonsj0305/NEUMANN/actions/runs/41999803577) **PASS**: 31 previously opened baseline-unsolved ARC tasks, 2 alternating-order calls per method per task, original P2.5 compiler search vs P2.6 sound TRAIN-only sufficiency preflight. Total timed P2.5 search **5,232.187336 ms**, preflight **511.421657 ms**, observed ratio **10.2306722×** on 62 calls per arm. Both paths abstained on all 31 cases; original P2.5 returned zero train fits and the preflight gave a valid impossibility certificate for every case. This is a **local failed-search elimination ratio**, not an all-in problem-solving speedup and not new ARC ability. File loading, provenance checking, GitHub runner setup, training and production integration costs were excluded. Ratio is one CI runner, two order-balanced repeats and not a confidence interval. The reproducible paired receipt is p26-paired-cost.json in the same uploaded workflow artifact.

No end-to-end saving from an integrated preflight has been measured; any deployed preflight consumes time, too. Training, teacher, compilation, verification, fallback, hardware memory, FLOPs, power and full economic cost are UNKNOWN. Do not claim a 10x PASS.

## Limits and integrity
This is a **postmortem on an already opened public ARC cohort**, not new-family transfer. It proves inexpressibility for the P2.5 frozen source language only, **not impossibility of solving ARC tasks in general**. Richer object-based, relational, spatial or higher-order features can invalidate this narrow impossibility, which is precisely the required research direction.

The source-independent manual feature collision scan and the checked-in real-source verifier agree. Exact source/cohort provenance is frozen. No neural calls or teacher calls. It is not evidence of autonomous learned operator invention, JEPA success, frontier ability or full same-capability compute superiority. Q1–Q7 remain OPEN.

## Architecture decision
STOP increasing search depth/beam and manually inflating Boolean predicates within P2.5's current representational regime. The current 31 tasks are formally blocked by missing geometry/observations. Keep a cheap, fail-closed Direct baseline, and only run expensive search if a train-only representation sufficiency preflight finds that the candidate observation vocabulary distinguishes the necessary outputs. If not, abstain or generate a structurally different representation. This sufficiency gate is a proposed system change, NOT currently deployed in the solver.

## P2.7 decisive next test contract (proposed, NOT RUN)
Hypothesis: a trainable across-task representation/schema proposer can produce **new typed, executable operator structures**, independently prove fit on original TRAIN, and transfer to unseen task families at lower all-in cost than matched strong classical baselines.

1. Freeze a **new never-opened** original-task cohort and different-family transfer cohort before model/grammar selection; exclude every previous eval ID, including P2.5's 32. Avoid task-ID, gold-test, source-identity and teacher-output leakage.
2. Compare against a matched classical searcher with the SAME new feature vocabulary and computational budget. Separately report external teacher performance and student performance.
3. Every proposal carries executable AST, type/shape contract, independent original TRAIN exact replay, ambiguity resolution, and fail-closed ABSTAIN/DEGRADED behavior.
4. [Assumption, preregistration gate] at least +2 additional exact correct heldout original tasks per 32, zero false accepts, at least one successful transfer from a different heldout family, and complete discovery+training+inference+verification+fallback cost. These are **targets, not observed results**.
5. STOP on any false accepted output, architecture tuning against the fixed test cohort, lack of genuinely new grammar, absent transfer or excess full cost.

**Research decision:** P2.5's ceiling is a representation sufficiency bottleneck, not primarily a depth/beam shortage on its frozen cohort. P2.6 certifies that negative mechanism with original data; autonomous cross-family discovery and 10x total computational efficiency remain unproven.
