# NEUMANN 1 Q3 | FIRST ACTUAL CPU-trained source-conditioned structural operator proposal

**2026-10-19 KST · Result: preregistered SCOPED PASS, not learned mathematical operator invention, not global Q3.**

## A small but real learned mechanism

For the first time in this specific new experiment, **an actual 339-parameter supervised neural MLP was TRAINED** on source transition features, not just a hand-coded classical prover, forged model-call stub or Q3R fixed grammar re-run.

- Preregistration BEFORE FIRST training / verifier outcomes: [Issue #271](https://github.com/yoonsj0305/NEUMANN/issues/271).
- Exact first actual [GitHub Actions #39216091769](https://github.com/yoonsj0305/NEUMANN/actions/runs/39216091769): SUCCESS, CPU-only; Python 3.11, pinned `numpy==1.26.4`, `scikit-learn==1.5.2`, `z3-solver==4.13.3.0`; no paid API, no accelerator allocation, no Gemma4 E2B inference.
- Actual frozen training corpus: 360 **author-constructed** integer-transition original tasks, 120 per family, construction seed 53, step magnitude k from 2 to 7. Trained MLP classifier hidden layers (16,8), `solver=lbfgs`, random seed 17, `max_iter=500`, train-only StandardScaler and 339 learned weights+biases.
- Actual first holdout: 90 **distinct author-constructed** source original tasks, 30 per family, construction seed 79, disjoint k from 8 to 13. All original source SHA distinct and none equal training source SHA. This is unseen **parameters and task bytes**, NOT unseen independent original authors, open-set new abstract mathematical families or a public benchmark.
- Each source publicly specifies `Pre(x,y,z)` and two nondeterministic transition branches `x'=x+dx, y'=y+ax*x+cy, z'=1-z`. The trusted original verifier separately holds `Post = conserved_relation OR (z=0)`. **No Post, gold semantic family label or verifier result is used by the MLP at heldout inference.** The trusted verifier independently checks all three original bad conditions for every candidate, not just matching class labels.
- Operators in finite library (all preregistered): **QUADRATIC**, learned to select source-only `y-x²=C`; **MODULAR**, `x mod k=r`; and **AFFINE**, `a*x+b*y=c`. A deterministic parameter extractor constructs each from PUBLIC initial state and transition increments *after* the neural classifier chooses a family. Neither open-ended formal-language invention nor learning the symbolic coefficients end to end is established. Training uses supervised correct family labels only on TRAIN.
- The original Post is intentionally non-inductive so source structure is **necessary**. All 90 were checked: `Post` alone inductive 0/90.

## FIRST science evidence (not posthoc threshold chosen)

| Original source Z3-inductive 3VC successes on same 90 | Actual first count |
|---|---:|
| **CPU-trained source-conditioned MLP + deterministic operator parameterization** | **90/90** |
| Untrained seeded RANDOM operator selection | **34/90** |
| Same trained MLP but **source transition features all zero** | **30/90** |
| Previous restricted **affine-only Γ** (without square and modular operators) | **30/90** |
| **Strong full classical deterministic source-signature algorithm** with same all three templates | **90/90** |
| Original `Post` alone inductive | **0/90** |

**60/90** learned candidates belonged to QUADRATIC or MODULAR, which are **outside the frozen restricted affine-only Γ** grammar. Those 60 all passed original 3VC. No incorrect candidate was falsely accepted by the Z3 original inductiveness verifier.

**All nine pre-registered gates passed in the FIRST run**: 90 unique original test tasks vs 360 train, no train-test SHA overlap, learned ≥81/90, learned nonlinear/modular ≥54/60, gains ≥25 relative to both untrained and zero-source ablations, restricted Γ ≤30 successes, Post-only never inductive, and zero false original-VC certificates.

This is a **causal ablation signal that actual supervised training and actual public-source transition features affect the selection of useful structural operators** on the narrow constructed study domain. It is stronger than the previous fixed-Γ Q3R neural FAIL because it includes sources whose adequate invariant class lies outside Γ and is chosen by trained inference at TEST time.

## Important null result against the strongest exact classical expert

**Strong full classical algorithm also achieves 90/90**. It derives the same operator family by exact degree / transition-rank detection without learning. The neural selector **does not buy a single distinct solved original** beyond this stronger method; its training plus inference and verification cost are extra. Thus these data **DO NOT** demonstrate that learning is necessary or computationally efficient for this construction class. The best architecturally economical choice on this domain may be to DELETE the neural component and use the classical detector, consistent with the project's own North Star. No universal neural discovery, truly original operator invention, stronger-than-classical capability or 10× efficiency is supported.

The original Q3R trained fixed Γ found **zero distinct semantic operator improvements**, and remains immutable NO-GO for THAT historical architecture. This new study uses a different deliberately enlarged operator library and supervised task construction, and may only be called **bounded learned source-conditioned operator selection**. A trained selector over a known library is not a system inventing unknown operators.

## Immutable original evidence

- First actual [GitHub Actions #39216091769](https://github.com/yoonsj0305/NEUMANN/actions/runs/39216091769), archived before admission verdict.
- Raw artifact #**12169936962**, downloaded ZIP SHA256: `df4339e48e5f59391222ad3a4b39e63b18c709d25bcfd589194a150d9cdcd435`; independently inspected ZIP CRC PASS.
- Raw original first JSON SHA256: `0a5540331f2f6138a9c8e6e6957bea24c914972b4818f0bd76031e6256ed69f5`, 263320 bytes, all 90 original proof row/controls retained.
- Actual learned MLP weights SHA256: `30eac0aa22ed01848c06a92d262eab160af9f0743cf943adfb7e2535f2800b93` and **339** numeric learned parameters. Training wall as reported by process: **6.523 ms** (CPU, not total experiment cost, excluding task construction/Z3 verification, pip install and cold startup). No energy/dollars/inference complete-cost claims.
- Self-contained reproducible source: `research/evidence/q3_cpu_learned_operator_20261019/first_trained_source_operator.py` in [draft PR #272](https://github.com/yoonsj0305/NEUMANN/pull/272).

## Exact scientific interpretation

```text
Q3_CPU_ACTUALLY_TRAINED_SOURCE_CONDITIONED_OPERATOR_SELECTION = SCOPED_PASS (90/90)
Q3_CPU_LEARNED_NONAFFINE_OR_MODULAR_STRUCTURE_VERIFIED         = SCOPED_PASS (60/60)
Q3_TRAINED_CAUSAL_ADVANTAGE_VS_UNTRAINED_SOURCE_OFF           = SCOPED_PASS (90 vs 34/30)
Q2_Z3_ORIGINAL_INDUCTIVE_CERTIFICATES_FOR_TRAINED_CANDIDATES  = SCOPED_PASS (90/90)
Q3_LEARNED_INVENTION_OUTSIDE_KNOWN_CLASSICAL_OPERATORS       = NOT_PROVEN
Q3_STRONGEST_CLASSICAL_UNIQUE_CAPABILITY                     = NONE (both 90/90)
Q4_DISCOVERY_COST_ECONOMICALLY_BETTER_THAN_CLASSICAL         = NOT_PROVEN; may be worse
Q6_TRUE_EXTERNAL_UNSEEN_AUTHORED_FAMILY_GENERALIZATION      = OPEN
Q7_REAL_SMALL_VS_FRONTIER_GAP_RECOVERY                       = NOT_EVALUATED
Q1_Q7_GLOBAL                                                 = OPEN
```

**STOP** after this first completed bounded learned-mechanism experiment. The valid next question is NOT how to further increase 90/90 on author-constructed families. It is how to produce **semantic hypotheses that an eligible best exact classical expert does not already supply** on authentic independently sourced hard original tasks, at enough benefit to justify trained learning and full costs, ideally using available pretrained model/hardware legitimately. Do not turn a tiny supervised grammar-router win into a large AI architectural discovery. Maintain historical first AM1 real accelerator FAIL and sealed D3 BLOCKED.
