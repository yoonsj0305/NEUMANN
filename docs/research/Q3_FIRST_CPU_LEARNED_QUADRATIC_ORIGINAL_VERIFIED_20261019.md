# NEUMANN 1 Q3 · FIRST real CPU-learned quadratic polynomial coefficient generation on original SyGuS

**2026-10-19 | POSTHOC SCOPED PASS. Not operator invention outside trained grammar, not classically unique or global Q3.**

## Real immutable first successful study

- [Draft PR #291](https://github.com/yoonsj0305/NEUMANN/pull/291) on dedicated stacked research branch.
- [GitHub Actions #39246663900](https://github.com/yoonsj0305/NEUMANN/actions/runs/39246663900): scientific job **SUCCESS** with all frozen registered checks.
- [First full raw artifact #12182868290](https://github.com/yoonsj0305/NEUMANN/actions/runs/39246663900/artifacts/12182868290). Downloaded ZIP: SHA-256 `8b67d3e3a726eb980fb5f5e8da530c698cf468159f8c5ee1fd0eee189d951cb1`, ZIP CRC PASS. Exact raw JSON SHA-256 `8ec68baddc34f7164342d608de388313640ccb0b1638a13a19da9d4d88249ff7`.
- Model: actual supervised CPU MLP `12 → 96 tanh → 96 tanh → 10`, **11,530 learned parameters**; first CI trained numeric weight SHA-256 `5c935594cccd0ee0742810ff1c3ca2a7db33ed745e6297382cc33c1e74dd49bf`.
- Training input: 588 author-constructed source-transition signatures plus complete 10-dimensional symbolic polynomial coefficient labels; train wall **3429.926 ms** on GitHub Actions CPU. Frozen authored source-parameter holdout **124/132** correct complete coefficient arrays. All six permutations of source transition parameters `a=1,b=0` were entirely excluded from training and reproduced exact coefficients **6/6**. This is **not a source-family-disjoint split**; synthetic data follows one formula-generating program family.
- Actual original: upstream `SaswatPadhi/LoopInvGen@6ac90265b11431c9477dfbd33e3e3380234c0499`, `benchmarks/NIA/2018.CHI_InvGame/gauss_sum-more-rows.auto.sl`. Pinned Git blob SHA1 `a46943a0aacdfc418f5b57788d3b0b0015a815f1`; original SHA256 `8fa3a57a5d44bd51a6ec87f5efe46f13b47e71b14681923a17134a231d70c5b2`. **This source was already opened in older Q3Y/Q3Z experiments, so the external test is retrospective**, not a fresh blind source. It was not included as bytes in the MLP training corpus.

## Learned source-conditioned relation and actual safety

The frozen model receives ONLY the public original source's **independently Z3-proved** affine transition-difference coefficient matrix and update constants. Neither the original Post nor hidden gold coefficients enter model inference. It directly predicts all 10 coefficients in the fixed degree-≤2 polynomial monomial vocabulary, NOT a class or index of prelisted invariant formulas. Result:

```
coefficients [1,n,sum,i,n²,sum²,i²,n·sum,n·i,sum·i]:
[0, 0, 2, 1, 0, 0, -1, 0, 0, 0]
learned relation: 2*sum + i - i² = 0
```

One small **classical** source-only independently inductive bound `i ≤ n+1` is also required to imply the *published original* safety Post. The model did **not** learn this helper. The combined invariant passes native **Z3 three original bad obligations UNSAT 3/3** and the existing unchanged source-SHA-bound independent **cvc5 UNSAT 3/3** (exit code 0), including the full original nontrivial guarded Trans and published Post.

Controls on the identical original:
- The source-only helper alone: initial/consecution UNSAT but original Post condition SAT, so it cannot explain success without the learned polynomial.
- Set all neural source features to zero: native initial, consecution, Post conditions all SAT, so the trained function is source-conditioned.
- Strong same-source classical specialist deriving exact coefficients from the source update: **also full original safety PASS**. Hence **zero unique neural solved-original advantage** over the best available exact classical for this case.
- Warm neural inference-only wall **0.313 ms**; training wall **3429.926 ms**. Complete matched classical+neural cold task costs and power not evaluated. Neither 10× cost improvement nor training investment recouped is established.

## Scope ledger / scientific interpretation

**NEW and now demonstrated**: `Q3_CPU_TRAINED_SOURCE_CONDITIONED_QUADRATIC_COEFFICIENT_GENERATION = POSTHOC_SCOPED_PASS`; `Q2_AUTHENTIC_SOURCE_LEARNED_PROPOSAL_Z3_CVC5=SCOPED_PASS`. The model emits a non-affine quadratic relation rather than merely selecting a fixed operator label.

**Unproven**: The entire monomial/operator vocabulary up to degree two was supplied in advance, and synthetic training carried coefficient labels. Thus `Q3_LEARNED_MATHEMATICAL_PRIMITIVE_OUTSIDE_PRESET_GRAMMAR=NOT_PROVEN`; `Q3_UNIQUE_CAPABILITY_OVER_STRONG_CLASSICAL=NO`; `Q6_BLIND_CROSS_SOURCE_AUTHOR_TRANSFER=OPEN`; `Q4_Q5_10X_COMPLETE_COST=NOT_PROVEN`; `Q7_FRONTIER=BLOCKED`; `GLOBAL_Q1_Q7=OPEN`. The immutable first prospective three-source original transfer FAIL [Issue #287](https://github.com/yoonsj0305/NEUMANN/issues/287) and historical learned optimizer FAIL remain unchanged.

**Research decision:** Do not retune, enlarge, or repeatedly sample the same opened Gauss source and call it stronger Q3 evidence. Training a model to reproduce a relation that a fast exact classical specialist also derives is not a sufficiently efficient permanent NEUMANN 1 design under the frozen North Star. If neural study resumes, require a one-shot preregistered G0 classical headroom gap on a genuinely new source family and actual new candidate grammar, matched verifier/cost/ablation, before new training investment. Keep this real bounded learned-mechanism success in the evidence archive.
