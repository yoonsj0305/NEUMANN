# NEUMANN 1 Q3 | Actual trained 42-weight operator first SHA-frozen original transfer, then posthoc synchronized-clock repair

**2026-10-20. Two immutable distinct experiments, carefully separated. GLOBAL Q3 OPEN, Q1–Q7 OPEN.**

## (A) PR #310: Actual learned model, first untouched source identities fixed before source contents were inspected

Real original public sources `SaswatPadhi/LoopInvGen@6ac90265b11431c9477dfbd33e3e3380234c0499`. SHA identities frozen at commit `b300aa21c8fc5c8b4675e3bafe0ad3856f0898f2`:
- `benchmarks/NIA/other/pottsumm2.sl` Git blob `81eda39a343064ade00393afc3b7ac85f296dddf`.
- `benchmarks/NIA/other/pottsumm4.sl` Git blob `58e7abf2b607dafefaacd8f3007a1cc6e2cbe399`.
- `benchmarks/NIA/2018.CHI_InvGame/non-lin-ineq-4.desugared.sl` Git blob `7981b1ebef61779043278aabc250d17eab3d3a1b`.

**Learned model:** `384` author-synthetic integer recurrence coefficient vectors (RNG 20261020), labels come from actually unrolling numeric recurrence prefix sums and exact rational polynomial interpolation, not from any original source or hand-labeled real target AST. Train `6→7` linear coefficient operator, **42 fitted trainable numerical weights** by NumPy `lstsq`; scale denominator `5040`, learned integer coefficient matrix SHA256 **`563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78`**. Heldout synthetic `64/64` full coefficient vectors exact, shuffled training labels control `0/64` correct, zero weights `0/64`. Training is supervised linear regression, **not a nonlinear neural architecture** nor discovery of operators outside fixed polynomial grammar. Original unseen source bodies are opened only after model training/hash was frozen. It outputs exact coefficients of whole polynomial candidate, not just a solver route label.

**First independent official run** [Actions #39424234515](https://github.com/yoonsj0305/NEUMANN/actions/runs/39424234515), immutable [artifact #12264693070](https://github.com/yoonsj0305/NEUMANN/actions/runs/39424234515/artifacts/12264693070), raw JSON SHA256 `993e7ce6ce116bedce68efa66ada4a42ea1913629730ec1b914bdfc60316f513`, ZIP SHA256 `5c35295502b50ec55a740454e276fd78361add3fb19b201f1151c2c05ecd5e76`, CRC PASS.

Original **published** Pre/Trans/Post all unchanged, genuine native SMT original three VCs **Z3 UNSAT 3/3 + independent official SHA-pinned cvc5 1.4.2 UNSAT 3/3**:
1. `pottsumm2.sl`: learned `2x=y²+y` plus `y=i`, source guard bounds. **PASS**. Strong same-info exact classical discrete sum **PASS**.
2. `pottsumm4.sl`: learned `4x=y⁴+2y³+y²` plus `y=i`, source guards. **PASS**. Strong exact classical **PASS**.
3. `non-lin-ineq-4.desugared.sl`: learned policy could not identify `j=i+1`, generated no useful accumulator polynomial, only source bounds; original Post VC **SAT**. **FAIL**. Strong classical without that normalizer also **FAIL**. The initial true first-generalization result **2/3** must remain unchanged.

Train+test complete study wall `4066.628ms`, synthetic-training/heldout `3471.530ms`, three actual original cases wall `248.453+178.516+167.882≈594.851ms`. No GPU or paid API. Note total excludes repository engineering/R&D and external data download.

## (B) PR #311: POSTHOC method improvement after observing the failed source, unchanged learned weights

**This is NOT the first blind test.** After actual third source content was opened, developer noticed two synchronized unit clocks `i'=i+1, j'=j+1` but original Pre initializes `i=0,j=1`. A general source-only bridge (NO manual answer label or per-file branch) was frozen at commit `d8b1fdc1c9eaf423f66951228824ccd6712d7af6`. It:
- Computes all +1 clocks from verified source Trans, obtains exact integer initial anchors from original Pre with Z3 uniqueness;
- Picks canonical lowest-starting clock, derives `other_clock=canonical_clock+offset`, independently proves original Pre⇒relation and relation∧Trans⇒relation' Z3 UNSAT;
- Canonicalizes source increment in **one** primary clock under proven affine offsets and verifies exact algebraic semantic equivalence;
- Uses **unchanged same 42 weight matrix SHA** to synthesize full normalized antidifference coefficient vector `F(t)` and anchors it as `acc−acc₀−[F(t)−F(t₀)]=0`; no retraining;
- Gives IDENTICAL normalizations to the strongest source-only SymPy exact classical baseline, and proves untouched native original three VCs in Z3 and independently pinned cvc5.
- No real source Post is used until candidate structure is selected and frozen; all original Pre/Trans/Post native/custom semantic XOR parity UNSAT 3/3, Pre SAT and NotPost SAT.

**Posthoc first actual independent official run** [Actions #39425280587](https://github.com/yoonsj0305/NEUMANN/actions/runs/39425280587) **SUCCESS**, [artifact #12264539362](https://github.com/yoonsj0305/NEUMANN/actions/runs/39425280587/artifacts/12264539362), raw unchanged JSON SHA256 `032e1b020efdb17ff7fddb0bbd37cf19078d8575a1a36a79283f91d2c1245858`, ZIP SHA256 `ac8fb7191e67e6e1f10c1c6c56f87e4f671a44c2c83343410efeeffe7b28ae29`, ZIP CRC PASS.

**All three genuine native ORIGINAL sources Z3 3VC and independent cvc5 3VC 3/3 UNSAT per source, 9/9 per backend**:
- `pottsumm2`: learned `2x=y²+y`, also exact clock offset `i=y`, both proofs **PASS**;
- `pottsumm4`: learned `4x=y⁴+2y³+y²`, `i=y`, both proofs **PASS**;
- `non-lin-ineq-4`: automatically derive `j=i+1` and check original Pre / Trans induction UNSAT. Canonicalize actual source increment `k'−k=(i+1)(j+1)` as `(i+1)(i+2)`. Same FROZEN 42 weights produce `3k=i(i+1)(i+2)`. Source original three VCs **Z3 UNSAT 3/3 and independent cvc5 UNSAT 3/3**. Exact classical same-info source normalization/antidifference also **PASS**.

Compute new full study wall **3936.003ms**, synthetic retraining+64 fresh tests **3397.663ms**, three original cases **213.398+145.938+178.796≈538.132ms**. No GPU/paid API. This is not a 10× improvement over the exact classical baseline when training amortization counted.

## Honest Q3 interpretation

Scoped **established**: a learned (linear) finite-dimensional coefficient generator trained solely on synthetic numeric recurrence traces can make **first learned polynomial proposals for at least two previously unopened actual program originals** that independently certify complete original 3VC in Z3+cvc5. With a posthoc improved, source-sound affine-clock adapter and **unchanged model weights**, all three originals now prove. The model is a learned numerical mapping, not a nonlinear neural model and not invention of a mathematical operator outside its preset polynomial hypothesis space.

**NOT established**: 3/3 *first* prospective transfer (historical immutable result is 2/3); unique discovered operator outside predeclared grammar; advantages over same-information exact classical math; first new author-family blind G1; model capability after no classical feature extraction; 10× all-in or frontier parity. `GLOBAL Q3=OPEN`, `GLOBAL Q1-Q7=OPEN`.

**STOP/next decisive experiment**: repeat frozen `trained operator + general proven source clock adapter` on a **new, independently authored never inspected original test family**, with weights/source adapter source hashes and source identities frozen before ANY target contents; run genuine source 3VC and strong matched exact classical. If all strong classical are already solved at less cost, this bounded learned-specific efficiency gap is CLOSED as no advantage, no re-tuning on same tests. The Q3 North Star remains frontier-level problem solving at minimum necessary compute, not accumulation of easy polynomial proofs.