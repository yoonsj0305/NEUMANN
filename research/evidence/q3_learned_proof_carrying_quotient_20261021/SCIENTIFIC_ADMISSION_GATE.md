# Q3 learned proof-carrying quotient: admission decision

Status: **SCOPED MECHANISM PASS / GLOBAL Q3 OPEN / NO ARCHITECTURAL SUPERIORITY**.

## What really happened
- A numeric projection is fitted by self-supervised gradient descent on 1,500 GIVEN permutation-equivalence pairs of 8-bit states. Twelve independent random seeds converge. The source problem does **not** teach the model which coordinate permutations are valid: the augmentations already encode that symmetry prior.
- The learned weights extract an integer-valued summary \`h(s)=sum_i s_i\`. That summary is a NEW COMPOSED STATE REPRESENTATION relative to the original individual Boolean state variables; it is **not a new mathematical operation or a newly discovered general theorem**.
- The representation is tested on held-out bit widths 12,16,18. Every original state is exhaustively checked against the original transition relation, not only sampled trajectories. For the bounded source family it is proof-carrying.
- A symmetry-broken transition example has same learned count but different successors, so it is explicitly rejected. Anchored-but-untrained weights are also rejected.
- State exploration visits 155,382 explicit reachable states vs 10 quotient states for n=18,k=9. This ratio is a reduction versus NAIVE explicit exploration only. It is **not** an end-to-end advantage or efficiency comparison against a strong classical method.
- Exact classical symmetry/orbit reduction produces THE SAME 10-state quotient with zero training overhead. Therefore the learned module adds **no unique capability in this study** and global Q3, Q4, Q6 remain OPEN.

## Honest formal gate for a new NEUMANN architecture

Q3 structural novelty passes only if ALL conditions hold:
1. New source problems were registered before reading source bodies, and after all representation rules are frozen.
2. A source-conditioned learner (not a human or known answer in augmentation data) produces a reusable transformed program, operator, latent state or decomposition previously unavailable to the system's frozen candidate vocabulary.
3. Independent check proves semantics preserved on the **original** problem and goal.
4. Disabling learned structure removes a result **relative to a strong classical synthesizer with equal operator/proof rights**, or full end-to-end cost is lower under equal task budgets.
5. Transfer repeats across unrelated, unseen source families; exact failed/unknown/mismatch entries are retained.
6. All learning, exploration, fallback, proof and amortized costs are charged; Q4 and 10x claims require measured paired repeated results.

This experiment proves a constrained representation-learning mechanism and exposes the **missing work: autonomous source-driven abstraction invention**. Stop scaling symmetry-only examples merely to improve a misleading ratio. The next minimal experiment must begin with a real source whose structural relation is NOT supplied in the augmentation data, and compare source-generic learned AST invention to exact classical synthesis.
