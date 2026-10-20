# NEUMANN 1 Q3 | First independent-origin 5-source result + algebraic NO-GO for frozen 42-weight integrator

**2026-10-20 KST | Bounded architecture-specific mathematical NO-GO proved. Cross-origin proof transfer NOT demonstrated. Global Q3 and Q1–Q7 remain OPEN.**

## Immutable provenance and first experiment

- Research PR: [#316](https://github.com/yoonsj0305/NEUMANN/pull/316).
- Five true original source identities frozen as **Git blobs and upstream commit** in commit [3fce7ba3](https://github.com/yoonsj0305/NEUMANN/commit/3fce7ba3a67bcd3d8c801b7274344eb17e5fe109), **BEFORE original bodies were inspected**.
- Upstream **different original repository** `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646`, with three `xujie_code2inv` files and two `andrew_lustre` files. Two named source submission families in one upstream, not five independently identified authors.
- The old fixed synthetic-trained linear model from PR #310/312 was frozen: 42 parameters `W` (shape 6x7), integer numerator matrix and rational denominator **5040**, weight SHA256 `563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78`. Synthetic original training 384 records, 64/64 exact heldout. Reconstructed/froze hash BEFORE reading any of the five target contents, with no target training, label, tuning or feedback.
- **First official [GitHub Actions #39436675738](https://github.com/yoonsj0305/NEUMANN/actions/runs/39436675738) SUCCESS**, first [artifact #12272311075](https://github.com/yoonsj0305/NEUMANN/actions/runs/39436675738/artifacts/12272311075), raw JSON SHA256 **`8333563ca90ba7e2d8afe6ee807b1fe36f62a0be4514d038ebec47ea9594f592`**, official ZIP SHA256 `16a546ac59fdfe87def2a9febc6c160eb293f4b0c16a5c77b36bb1fbf7891552`, 3169 bytes, CRC PASS. No scientific first run omitted.
- Whole official CPU process including synthetic-training replay, exact rational theorem verification and five-source classification measured **3528.596 ms** in one runner. Not a valid energy, frontier, or paired cold-cache benchmark.

## An actual proved theorem: the fixed degree-6 learned operator IS the classical inverse

Write source state increment `δ(t)=d0+d1*t+...+d5*t^5`, a polynomial of degree≤5. The candidate integrated invariant is `F(t)=f0+f1*t+...+f6*t^6`, with `F(0)=0` and `F(t+1)−F(t)=δ(t)`.

Exact rational coefficient map `D` of discrete difference is a 6x7 matrix:
`D[k,j]=binomial(j,k)` if `j>k`, else 0, for `k=0..5`, `j=0..6`.

The actual **learned 42-weight matrix W** (shape 6x7) from the frozen training receipt satisfies, by **exact SymPy integer/rational matrix arithmetic**:
- `D * W.T / 5040 = Identity_6` exactly, **all six input monomial directions**, not an empirical finite test;
- `(W.T / 5040)[0,:] = 0`, the source start condition `F(0)=0`;
- `rank(D)=6` and determinant of the 6x6 nonconstant block `D[:,1:]` is exactly **720 !=0**, so F is UNIQUE given δ and F(0)=0;
- **`W.T / 5040 = [zeros(1,6); inverse(D[:,1:])]`**. This is the exact independently calculated classical antidifference inverse, not an approximate numerical equivalence;
- Perturbing one learned coefficient by `1/5040` makes `D*W.T/5040 ≠ I`, independent negative control PASS.

**Decisive bounded conclusion:** On the predeclared degree≤6 polynomial grammar with F(0)=0, any correct model that learns to integrate arbitrary degree≤5 polynomial increments MUST implement precisely the same mathematical operator as exact classical symbolic summation. For the current 42-weight architecture, **learned-exclusive invention of a DIFFERENT mathematical operator within this grammar is impossible**. This *does NOT* mean all possible models or larger grammars cannot invent structure; even the same operator might be implemented faster in hardware at inference, but no all-in speed superiority has been measured here. This is a **PASS of a bounded exact negative theorem**, not a PASS of global Q3.

## Real first external-origin five-source results (no cherry-picking)

| Frozen original | Git blob SHA1 | First actual run classification |
|---|---|---|
| `lib/Inv_Track/xujie_code2inv/1.c.sl` | `859bae24a9f26044a40a3c97f1d2e5fc08504f06` | `NEXT_COORDINATE_MISSING` in source AST extraction; no full learned/classical 3VC |
| `lib/Inv_Track/xujie_code2inv/10.c.sl` | `22bcd1792d96ccdfcd2c829999cb37f6b7f373ba` | `NEXT_COORDINATE_MISSING`; no full learned/classical 3VC |
| `lib/Inv_Track/xujie_code2inv/100.c.sl` | `ec31090e13e75640447f234a7e2b58cfd09b1086` | `NEXT_COORDINATE_MISSING`; no full learned/classical 3VC |
| `lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl` | `8490b3e25ff7d462a7405e68e742be1abb35b8f8` | `ABSTAIN_UNSUPPORTED_NON_INTEGER_STATE_SORTS`, Boolean state |
| `lib/Inv_Track/andrew_lustre/DRAGON_2.lus.sl` | `17f0cea250008e9e3575d38181f7e40804501dde` | `ABSTAIN_UNSUPPORTED_NON_INTEGER_STATE_SORTS`, Boolean state |

All 5 actual SHA-frozen Git blobs verified; target original files were never used to train weights. Three Int programs have source non-deterministic/branched next-state relations, whereas current source interface expects conjunctive deterministic coordinate equalities: **interface abstention**, not mathematical proof that the LLM is wrong, not a safety violation, and not demonstration of strong exact classical headroom. The two Lustre programs have Boolean state, outside fixed integer-polynomial symbolic input grammar. **0/5 first-source certified original 3VC** for both learned and equally scoped classical baseline.

No source-specific decoder refit, no evidence laundering. G1 genuinely new-operator success: **NOT DEMONSTRATED**.

## Q3 scientific decision

- `Q3_FIXED_42_WEIGHT_POLYNOMIAL_OPERATOR_EXCLUSIVE_NEW_PRIMITIVE=BOUNDED_NO_GO_PROVED`.
- `Q3_INDEPENDENT_ORIGIN_FIRST_SOURCE_REAL_CERTIFIED=0/5`, mostly unsupported representation; this is not 0% source reasoning accuracy on supported benchmarks.
- `Q3_GEN_GENERAL_BRANCHING_OR_BOOLEAN_SUPPORT=UNIMPLEMENTED`; **OPEN capability gap**, not proof impossible.
- `Q3_CLASSIC_EXACT_ADVANTAGE=NOT_PROVEN` (original first scripts all abstained).
- `Q3_GLOBAL=OPEN`, `GLOBAL_Q1–Q7=OPEN`, Q7 runtime/Frontier comparative gate blocked. No GPU/paid API.

**Minimum necessary compute next move**: Stop training/refining these particular polynomial integration weights: their attainable mathematical operator is exactly the known classical inverse. To pursue structural intelligence novelty, change the *represented family* and specialize by actual evidence: (a) source-level deterministic multi-branch transition graph + relational state mapping for code2inv, (b) Boolean invariant/state-machine abstraction for Lustre, (c) actual genuine learned proposal of something not in a full strong classical exact grammar. These must each have a new source-frozen independent test cohort and same-input CEGIS/Houdini/PDR/SMT controls before claiming G1; do not relabel these now-opened five files as fresh blind later.

Executable experiment: `research/evidence/q3_independent_origins_20261020/first_five_sources_and_exact_no_go.py`.