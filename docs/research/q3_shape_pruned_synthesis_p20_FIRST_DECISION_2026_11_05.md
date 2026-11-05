# NEUMANN 1 P2.0 | Sound shape-directed AST pruning first result and risk decision
Date: 2026-11-05 KST. North Star: **Frontier-level problem solving with minimum necessary computation**; Q1–Q7 global OPEN.

## Frozen source and first independent public ARC cohort
The P2.0 preregistration was committed before implementation and before reading the new source corpus. New public `fchollet/ARC-AGI` training files pinned at `399030444e0ab0cc8b4e199870fb20b863846f34`: 48 distinct filename-hash selected original tasks, excluding **216** previously opened public tasks and developer cases. `docs/experiments/q3_shape_pruned_synthesis_p20_COHORT_FROZEN.json` froze both source blobs and cohort IDs before opening task bodies. First results are recorded in four 12-task first shards and `docs/experiments/results/q3_shape_pruned_synthesis_p20_FIRST_COMPLETE.json`.

Compared exactly the same P1.9 executable program semantics:
- P19: 1/48 original tasks solved, **247,057** training primitive evaluations, 25,893 ms in-isolate study region.
- P20: 1/48 original tasks solved, **25,184** actual primitive evaluations, 3,637 ms study region.
- **48/48 original-task proposals and ABSTAIN reasons identical**, accepted wrong outputs 0 in each arm. One original source task `d511f180` was solved by both with a consistent 5↔8 color transformation. A separate independent direct cell-by-cell implementation and original train/test grid checks PASS.
- **9.81008× fewer primitive executions, 7.11933× faster study-region time**, including shape checking / incremental palette propagation overhead.
- Both programs enumerated 76,704 candidate ASTs; P20 **deleted 51,601 candidate primitive executions** via shape constraints and **rejected 25,098** additional candidates at first inconsistent color mapping. Early-exit does not imply the candidate is an incomplete valid solution: two different observed outputs for the same symbolic source value make a global mapping impossible.

## Soundness argument and assumptions
For frozen P1.9 types:
1. A dihedral orientation of a whole input (or its single nonbackground bounding box) has fully determined output `(height,width)`; integer translation and replacement/palette map do not change dimensions.
2. For a middle separator, horizontally split source output has `((H-1)/2,W)` and vertically split output `(H,(W-1)/2)`, provided the separator constraints are met.
3. If any training target shape differs from this declared output shape, **no** palette map or later operation in this candidate schema can repair the mismatch. Hence pruning is sound.
4. If the same upstream primitive value maps to two different observed target colors across train pairs, a *single deterministic palette mapping* is impossible. Hence early conflict stopping is sound.

P20 explores all 1,598 ASTs per eligible task in the same order, using **identical original P19 `primitive` and `execute` methods**, and returns a prediction only on the same exact consensus. These proofs do NOT transfer to a richer compiler with dynamic resizing or context-dependent palette maps. Independent audit `docs/experiments/results/q3_shape_pruned_synthesis_p20_INDEPENDENT_AUDIT.json` PASS for source identity, 48/48 proposal parity, zero wrong-accepted, one original independently replayed source solution.

## Frozen first gate and decision
P2.0 preregistered **≥10×** fewer primitive sample evaluations, **≥2×** measured task-region wall time at exact parity. **Wall speed passed**, but primitive call reduction was **9.81×**, so **P2.0 local 10× PASS gate FAIL**. Do not round 9.81 to 10 or redefine the denominator. The mechanistic 9.81× operator-call saving is still a valid observed cost result.

The P2.0 48-task cohort's original accuracy remained **1/48**, showing this round improved **efficiency only**, not semantics. Do not claim full-system 7.12×: source download, OS startup, memory, energy, GPU and monetary bills were NOT measured. A stronger neural proposal policy could still be useful if it generates new verified original-task programs; this benchmark does not establish that.

## Integrated research decision
- Retain P1.9 first original-task +2/48 capability headroom as an **independent cohort**, and P2.0 48/48 semantic preservation with 9.81× primitive-call reduction as a **different cohort**. They are not sequential accuracy scores on identical tasks; do not combine 5/48 and 1/48 into a single model accuracy claim.
- Keep deterministic **goal/shape abstract pruning and early impossibility rejection** in research mode, with explicit typed semantics and fallback ABSTAIN.
- Stop adding handcrafted ARC operator templates solely to make a first result PASS. Next high-value research must learn to **propose unprovided program schemas** and transfer across unseen task families, compare against this guarded strong Direct + exact quotient + shape deletion stack, and fully meter cost.
- All Q1–Q7 globally OPEN, unchanged P1.12/P2 and sealed Decision3, no auto-merge.
