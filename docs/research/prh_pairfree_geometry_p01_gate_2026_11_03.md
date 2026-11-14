# NEUMANN 1 | P0.1 pair-free relational matching

**Independent opened-development follow-up**, registered after immutable P0 results. This is not a confirmatory rerun of P0, not a new JEPA, and not a Q3/Q4 closure. Previous P0's `new-sensor` 1/128 observation is immutable.

## Distinction between identifiability and pointwise matching

P0 attempted to apply a previously learned pointwise rotation to an arbitrary new sensor frame. That fails when the frame changes. However, two complete observations of the **same finite set of states** carry extra *relational* information unavailable from individual samples: all pairwise distances are invariant to orthogonal rotation and permutation. Therefore the mapping between sets can be identified by matching geometric distance fingerprints, even when a pointwise learned rotation fails. Do not incorrectly claim that an unknown orthogonal transform is information-theoretically unidentifiable **given an entire shared finite scene**. If only independent marginal samples from an isotropic distribution are available, without shared scene anchors/structure, orientation remains unidentifiable.

## Frozen P0.1 contract (see code constant)

- New synthetic seed 20261104, dimension 8, 128 items per scene, independent Gaussian sensor noise SD 0.035.
- Two positive conditions: previously unobserved arbitrary sensor rotation with iid states, and with sparse states. A separate negative condition has **different latent worlds** in each sensor.
- No positive pair index or latent vector is supplied to the algorithm. Only each modality's complete unordered point set is supplied. For each item, compute its sorted distances to all other items within the same modality. Construct the cross-set Euclidean fingerprint cost matrix; solve one-to-one assignment via Hungarian algorithm. No fitting or data-derived hyperparameter selection.
- Gate: unseen sensor iid correct correspondence >=0.75; unseen sensor sparse >=0.50. The independent-world control is diagnostic, with no oracle correspondence to score. Record normalized full-scene geometric inconsistency to detect mismatch.
- Original world sets, Q1–Q7 results, seal status, and P1.12 are unchanged. This is a classical non-neural boundary test of what useful structure exists without a known mapping.

## Interpretation limit and cost

Pair-free recovery is not executable program invention. The method relies on identical scene membership and metric-preserving sensors; arbitrary nonlinear/partial views, repeated symmetric structures, unequal cardinalities and adversarial noise may break it. Measuring only correspondence is not iso-capability task solving. `scipy` Hungarian matching has cubic assignment complexity in item count, and pairwise distances require O(n²d) work and O(n²) memory. Larger scenes can make this more expensive than Direct or neural routes. If the original-task verifier is unavailable, fail closed to classic Direct.

Next real gate requires independently sourced semantic/program observations, a program generator that creates a new executable operator without gold references, independent original-task verification and complete matched comparator cost. Q3/Q4 PASS cannot be inferred from geometry alone.
