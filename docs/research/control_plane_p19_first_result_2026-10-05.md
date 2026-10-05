# P1.9 first actual opened-development result — retained FAIL

Date: 2026-10-05

This note retains the immutable first P1.9 result reported by the original Kaggle session. It does not rerun, rescue, replace or reinterpret the frozen historical verdict.

## Immutable first-result identity

- archive: `NEUMANN_P19_FIRST_EVIDENCE.zip`
- bytes: `66,795`
- SHA-256: `3493421fca63f1a2155a0ed21265a4f1b2c799f91cb20bcc0d1a57269ea9a759`
- frozen source head: `d5811f44a018e86660769ba9bebb542168ee97fd`
- bootstrap SHA-256: `a37e29f91a98d183e3f6906fd53643096eab2baae4a7bb5af034c3f1c8ee36a6`
- runner exit: `2`
- model-free replay exit: `0`
- study status: `COMPLETE`, 8 observations
- accounting complete: true
- frozen verdict: **FAIL / P19_SEMANTIC_CAPABILITY_FAILURE**
- no favorable rerun or replacement

The copied receipt bundle reports terminal complete=true, no_replacement=true and unchanged frozen-core identity.

## Frozen path accounting

The prospective control path completed exactly:

- model calls: 8
- neural forwards: 39
- generation: 0
- evaluated tokens: 58,101
- padded tokens: 58,101
- feasibility calls: 23
- selector receipts complete: 8/8
- tool calls: 1
- original-verifier calls: 1
- witness-cache hits: 1

Whole study: 580,714.165182 ms.
Frozen-core startup: 185,390.141922 ms.

Peak receipts:
- max accelerator allocated: 10,407,165,440 bytes
- max accelerator reserved: 11,966,349,312 bytes
- peak process RSS: 11,985,166,336 bytes

Energy, FLOPs and monetary cost remain UNKNOWN.

## P1.8 -> P1.9 control-cost localization

Relative to the retained P1.8 actual result:

- neural forwards: 138 -> 39, **71.74% lower**
- evaluated tokens: 257,088 -> 58,101, **77.40% lower**
- whole-study wall: 856.606 s -> 580.714 s, **32.21% lower**
- excluding frozen-core startup receipts: approximately **43.72% lower** study work wall

These are within-experiment control-path comparisons on different opened-development task sets, not a general iso-capability efficiency claim.

## Semantic outcomes

Expected candidate positions were prospectively frozen as:

`[1,0,2,0,2,3,1,0]`

All three P1.9 scoring modes produced numerically identical candidate A-minus-B log odds on every task.

| task | expected | raw top candidate | raw top correct? | top-vs-second margin (nats) | frozen outcome |
|---|---:|---:|---|---:|---|
| p19d_b01 | 1 | 1 | yes | 0.125000 | semantic abstain: margin |
| p19d_b02 | 0 | 0 | yes | 2.421875 | **ACCEPTED** |
| p19d_b03 | 2 | 1 | no | 0.656250 | semantic abstain: no positive candidate |
| p19d_b04 | 0 | 0 | yes | 0.125000 | semantic abstain: margin |
| p19d_b05 | 2 | 2 | yes | 0.375000 | semantic abstain: margin |
| p19d_b06 | 3 | 1 | no | 0.078125 | semantic abstain: no positive candidate |
| p19d_b07 | 1 | 2 | no | 0.125000 | semantic abstain: margin |
| p19d_b08 | 0 | 1 | no | 0.375000 | semantic abstain: no positive candidate |

Raw top-candidate direction is therefore 4/8. Only B02 clears the preregistered absolute-faithfulness and candidate-margin gates and reaches independent original verification. It is accepted.

Historical decision:
- selected: 1/8
- accepted: 1/8
- semantic abstained: 7/8
- verifier rejected: 0
- accounting failure: 0

## What P1.9 establishes

P1.9 successfully removes the P1.8 full-S4 cost explosion as the immediate blocker. The 39-forward path completes within every registered selector/item/study wall, and all three batch/order modes are exactly stable on this opened set.

P1.9 does **not** establish adequate residual semantic capability. Lowering the 0.5-nat margin or deleting the positive-faithfulness floor would not solve the underlying issue: B03, B06, B07 and B08 have wrong raw top candidates. Threshold tuning alone is therefore not the next architecture.

The current candidate-local prompt also contains substantial semantic-irrelevant structure after feasibility is already complete: full domains, all CSP relations, evidence aliases and canonical atoms. The unresolved semantic decision is much smaller: which source-bound entity the pronoun `It` denotes under the public role instruction.

## P1.10 development hypothesis

Prospective only, no P1.10 model score yet:

```
source-bound evidence
-> deterministic feasibility
-> one candidate: zero neural
-> multiple candidates:
     derive minimal semantic contrast IR
     {original semantic instruction, ambiguous mention, candidate source-bound entity bindings}
-> symmetric pairwise preference scoring
-> independent original verifier
```

For candidate pair i,j, score both orientations with fixed output semantics:

- A = LEFT binding is more faithful
- B = RIGHT binding is more faithful

Let

`L(i,j) = log P(A | i-left,j-right) - log P(B | i-left,j-right)`

and symmetrize:

`D(i,j) = (L(i,j) - L(j,i)) / 2`.

This removes a global A/B token preference and first-order left/right presentation bias. Candidate selection should be based on pairwise source-bound semantic contrast, not independent absolute FAITHFUL calibration.

P1.9's exact batch/unbatched/reverse equality on all eight tasks is development evidence that repeated per-candidate unbatched scoring is not buying useful numerical robustness on this frozen backend. A P1.10 P0 may therefore prospectively retain only two opposite batch-order passes while still failing closed on numerical drift.

P1.9 is never rerun or rescued. P1.9 tasks may be used only as model-free/synthetic regression fixtures for architecture construction. Any actual P1.10 score requires newly authored, independently checked and preregistered tasks.

Fresh validation remains unregistered. P2 registration=false. P2 actual=false. Decision3=false. Q1-Q7 globally OPEN.
