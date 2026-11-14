# NEUMANN 1 | PRH good-view adoption decision (P0, 2026-11-03)

Authority: `docs/research/frozen_north_star.md`. Q1–Q7 and all first actual failures stay unchanged. This is a **parallel optional mechanism investigation**, not a new production architecture, P1.12 replacement, or admission to P2/Decision 3.

## Source and limitation

Balestriero and LeCun, *Proving and Improving the Platonic Representation Hypothesis with JEPAs* (2026), https://arxiv.org/abs/2610.39302 and https://github.com/galilai-group/prh-proof. The authors show a particular good-view JEPA objective can yield aligned representations under assumptions. They do **not** establish that an arbitrary representation alignment discovers a new executable program, preserves original-task correctness, recovers frontier capability, or beats strong Direct.

## Main question

Can same-underlying-state, independently acquired observations improve cross-view matching without using labels or an output oracle? Does the gain persist across changed structural statistics and an untrained sensor?

**Deliberate inexpensive first-principles deletion:** Run an exact linear orthogonal Procrustes estimator before training any JEPA. If a classical transform already solves the constructed alignment problem at lower complete cost, do not justify neural training from this case. P0 is a hypothesis/interface smoke test, **not LeJEPA training**.

## Frozen P0 protocol

- RNG seed 20261103; dimension 8; 512 paired training states; 128 untouched examples per test cell; independent Gaussian sensor noise SD 0.035 (dimensionless normalized vectors). All three test cells use independently generated held-out latent states.
- Independent orthogonal sensors A and B observe the same *unseen* latent state. The encoder sees only sensor values and same-state positive pair indexing at training, never the generator's latent vectors or family labels. Independent observation noise, not multiple perturbations of one observation.
- `iid`: new states and same sensors. `sparse-structure`: new states with two active latent coordinates, same sensors. `new-sensor`: new states and an untrained B sensor rotation; deliberately tests sensor transfer failure.
- Baselines/negative controls: no rotation, randomly unrelated positives, and view perturbations from A alone fitted as if they belonged to B. Full candidate pool is independently permuted for each retrieval evaluation. No paired test example is fitted to the transform.
- Frozen *local alignment-only* gate: iid recall@1 >= 0.80; iid good-minus-unrelated >= 0.50 absolute; sparse recall@1 >= 0.50. The new-sensor cell is diagnostic and does not become PASS by being ignored; its status must be reported.
- One execution result only; no seed search, hyperparameter tuning, test-driven threshold changes, retries or alternate corpus. Failures remain failures.

## What would follow (NOT RUN here)

1. Use source-approved, truly independently observed semantic/program structure views with formal equivalence checks. Do not treat shared labels as good-view certificates or create positive pairs from gold solutions.
2. Pair-matched cheap symbolic/canonical and frozen P1.12 comparators. Add genuine LeJEPA only if the non-neural baseline misses a capability-bearing need.
3. Measure **executable** original-task correctness, unique new program discovery without oracle, verifier false acceptance, complete CPU/GPU training/inference/checker/fallback, amortization and unseen-family transfer. Require Q3/Q4 joint utility recovery >=0.80 and discovery C < eta*C_saved only within the relevant preregistered scope, and Q5 strong Direct iso-capability independently.
4. No sealed holdout or Decision 3 until the existing gate contract admits it. On alignment-only success, global Q1–Q7 remain OPEN.

## Failure modes and degraded mode

Pair provenance can encode the answer, bad negatives can be too easy, view identity can leak, and test sensors can be inadvertently reused. Any missing original-instance verification, collapsed embedding, out-of-family failure or increased full cost forces **classical direct fallback**. The `new-sensor` diagnostic is a built-in transfer stress test.

## Resource declaration

Procrustes has training asymptotic O(nd²+d³) and full-pool retrieval O(md²+m²d) here, with n=512 training pairs, m=128 evaluation tasks, and d=8. Report observed wall time in nanoseconds. FLOPs, energy, peak RAM and price remain UNKNOWN (null), not zero. A meaningful **Idiot Index** for this software pipeline cannot be constructed from a raw-material ratio; use measured total-system cost / irreducible useful computation only when both denominators can be operationalized. Do not invent costs.

## Next gate

A true JEPA comparison is **NOT RUN**. P0 only determines whether aligned good views are learnable and whether the easy path already has an exact classical solution. No promotion on alignment scores.
