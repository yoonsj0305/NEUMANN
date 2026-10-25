# NEUMANN 1 Q3 RC17 · Own-weight PARAMETRIC language production

**Research-only DRAFT. Do not merge without independent review. Date: 2026-10-25.**

RC16 human-authored DSL was limited to three states. RC17 removes that *bound* by providing only a universal integer register, parameter reference, binary low-level arithmetic, comparison, reset and emit interface. It provides **NO completed MOD-k or wrap-counter operator**.

Real 25-logit PyTorch categorical policy (slots 2×6×3×5×3×4×2 = 4,320 candidate compositions) is fitted from frozen source-only examples k3,k4 and binary prefix-event output. 12 independent seeds / 90 CEM+Adam iterations / 140 candidate samples. Each 12/12 policy samples an exact training fit (1,284/1,284 output bits); **4/12 final greedy**, so the 12/12 measure is *best sampled*, not greedy. Selected original seed ID 2026111003 is an RNG label, NOT an experiment timestamp. Source-selected sampled body (not greedily emitted by this selected seed) is:

```
state = 1
for b in binary_stream:
    t = state + b
    emit(t == 1)     # emitted PRE reset
    state = 0 if t > parameter - 1 else t
```

This is an unexpected shifted-state representation with invariant
`state_after_prefix = (1 + number_of_ones_so_far) mod k`.
No full body, state offset, MOD operation, or target state count was provided as a target instruction.

**FROZEN before withheld truth:** first 5,760 streams for unseen k5,6,7 and lengths7..10, **53,376/53,376 bits independently correct**. Additional 150 heldout long strings up to 4,096 bits pass over 10 k values (163,680 input bits). Formal symbolic mathematical induction holds all integers k>=2 and every finite bitstring. State capacity is EXACT k distinct states, MINIMAL by k pairwise-distinguishable residual histories (Myhill–Nerode). Storage for current state ceil(log2(k)) bits, excludes parameter and program code.

`AUTO_a4f32841906f` is a new lexical library symbol **derived from the learned program body hash** and registered only after independently checked universal proof. The human wrote the compiler, primitive ISA, proof gate and registration scheme. Unknown proof => UNKNOWN, reference fallback remains available. This is **model-proposed, proof-gated PARAMETRIC MACRO LANGUAGE EXTENSION**, not independent invention of base machine syntax.

**SAME-RIGHTS strong classical control:** entire 4,320-program grammar exhaustively source-graded and 10/4,320 perfect; all 10 generalize on untouched k5..7. Single-machine measured CPU classical 2.113 seconds vs neural 12-run 22.590 seconds. NO neural-exclusive advantage and NO Q4 all-in10x.

Complete clean-extraction ZIP with actual .pt, all 12 seed receipts, frozen first predictions, symbolic proof, invalid mutation gates, strong classical audit, isolated 12-run fresh retraining and manifest:
`NEUMANN1_Q3_RC17_OWNWEIGHT_PARAMETRIC_LANGUAGE_20261025.zip`
SHA256 `218447d4d6a0d565b7192d9f69c7d83156213ed10d347d9ff8abec3334967ded`.
`bash REPRODUCE.sh` and `bash RETRAIN.sh` both independently completed EXIT0. The GitHub draft includes only a compact extracted runtime/proof and quick regression; ZIP contains raw full torch weights.

**SCOPED PASS:** learned macro body with shifted representation, previously absent from registered library, parametric unbounded-capacity-in-k reuse, universal correctness, minimal state capacity, proof-gated language extension. **GLOBAL OPEN:** entirely self-invented base DSL/ISA, no human-coded reward optimizer/proof/compiler, independent external-author open-family tasks, classical efficiency superiority, full Q3/Q4/Q6/Q7. Q7 Frontier Gap still totally unproven.