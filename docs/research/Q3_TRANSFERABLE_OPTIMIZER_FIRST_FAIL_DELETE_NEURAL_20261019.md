# NEUMANN 1 Q3 | FIRST frozen optimizer transfer: genuine original 3VC but preregistered scientific FAIL

**2026-10-19 · Decision: STOP learned linear schedule and prefer exact classical nullspace in this source class.**

## Why this matters

This study was preregistered in [Issue #275](https://github.com/yoonsj0305/NEUMANN/issues/275) before any new first experiment output. It was proposed as a learned optimizer transferred to actual published SyGuS sources with no source-specific fitting. **First run failed the scientific gate** despite both cases having sound original proofs. The training optimization did not actually move any shared parameter, and a **fixed untrained recurrent schedule** solved the same two tasks. It is therefore WRONG to call these results learned weight transfer.

## Immutable first outcomes

- FIRST [GitHub Actions #39220633383](https://github.com/yoonsj0305/NEUMANN/actions/runs/39220633383): workflow **FAIL**, specifically the preregistered scientific gate, NOT task solver or infrastructure.
- First complete evidence archived BEFORE decision in artifact **#12170929899**.
- Downloaded ZIP SHA256 **d531fcd64ffbc5151d89215c0b36df0ab395ebc75a187f7a9bb9c2f414980e69**, ZIP CRC PASS, 3622 bytes, original receipt JSON SHA256 **c19e3c921e4da4570095aa1b0e1957db1b12c5469684ef9047cac8dbcc645fd6** (16055 bytes). Values were independently read from exact first ZIP.
- Same two already-opened official SyGuS `comp/2018/Inv_Track` sources, pinned official `SyGuS-Org/benchmarks` commit `13c8deb68a873635879c9a69bc78caebd340f646`.

| Pre-registered original source | Shared frozen repeated recurrence, Z3+cvc5 | Never-trained recurrence α=0.5, Z3+cvc5 | Strong exact Sympy nullspace Z3+cvc5 |
|---|---:|---:|---:|
| `cggmp2005_variant_true-unreach-call_true-termination.sl` | **PASS** (`[1,2,-1]`) | **PASS** | **PASS** |
| `brett.sl` | **PASS** (`[1,-1,1]`) | **PASS** | **PASS** |

Both are authentic original Pre/Trans/Post inductive certificates, not source-list labels. Original Post-only failed induction in both cases; original cvc5 checker separately replayed each successful candidate’s original 3VC. The recurrence performed **ZERO original-source gradient weight updates**.

## Dispositive failure in learned component

The preregistered source-agnostic pretraining attempted to learn four recurrent step-size parameters on **256 deterministic synthetic rank-two covariance matrices** by minimizing unsupervised drift over 32 unrolled forward steps, BEFORE any official source file was read by the study. Actual optimizer returned:

- Learned parameter vector = **[0.75, 1.0, 1.25, 1.5]**, unchanged from its initialized values.
- Optimizer `nit=0`; its `success=True` represented a **numerical optimizer termination**, not proof that learning improved any parameter.
- Training drift loss **0.004409006468408312 → 0.004409006468408312**, no decrease whatsoever.
- Shared initial/final parameter SHA256 **8ed2ea81a920fe3ecf34643c22e05d454fe1fd35b685626de54ed7b1f9f04c27**.
- The crucial preregistered check `trained_shared_operator_reduces_training_drift` was **FALSE**; the other eight were TRUE. Hence first science verdict **FAIL**, unchanged.

## Exact same-source component costs: full classical is substantially cheaper

| Published original | Recurrent 4096-step forward wall | Classical Sympy exact nullspace wall |
|---|---:|---:|
| `cggmp2005_variant` | **39.429 ms** | **1.014 ms** |
| `brett` | **39.138 ms** | **0.850 ms** |

These exclude the **shared** public source sampling, inductive bounds, native/cvc5 original verification, Python startup and unmeasured electricity/dollars. They are **component-only** cost comparisons, not ISO-capability Q4/Q5 complete-cost Pareto. Relative coefficient computation speedups for classical within these two records are approximately 39x and 46x, with the same accepted original 3VC. Additional synthetic shared pretraining took 5.96ms and does not improve correctness.

## Required architectural consequence

**The source-classical route is the component to KEEP for this exact rank-two linear-invariant capability. DELETE the no-benefit recurrent learned schedule from the scientific mainline**, retaining first code+artifact as negative evidence, rather than tuning the scalar optimizer or rerunning the same opened cases until it passes.

```text
Q3_SHARED_LEARNED_OPTIMIZER_IMPROVES_TRAIN_LOSS = FAIL (0 training iterations, unchanged parameters)
Q3_ZERO_PER_SOURCE_RETRAINING_CLASSICAL_FORWARD_COMPUTATION = PASS_SCOPED (2 originals source-bound)
Q3_TRANSFERABLE_ACTUALLY_LEARNED_STRUCTURE = NOT_PROVEN
Q3_FIXED_UNTRAINED_RECURRENCE = SAME_2_OF_2_CAPABILITY
Q3_STRONG_CLASSICAL_EXACT_NULLSPACE = SAME_2_OF_2_WITH_LOWER_COMPONENT_WALL
Q3_PER_ORIGINAL_3VC_AND_INDEPENDENT_CVC5 = PASS_SCOPED
Q3_ACTUAL_EXTERNAL_UNSEEN_AUTHORED_FAMILIES = NOT_TESTED
Q4_Q5_COMPLETE_COST = NOT_EVALUATED
Q7_FRONTIER_CAPABILITY = NOT_EVALUATED
HISTORICAL_AM1_FIRST = FAIL_UNCHANGED
SEALED_D3 = BLOCKED
GLOBAL_Q1_Q7 = OPEN
```

This negative result **does not invalidate** earlier Issue #273 source-local self-supervised real published-source 3VC PASS; it limits the additional assertion that its source-learned weights can be transferred. In Issue #273 every source required fresh local weight optimization and the full classical exact nullspace was faster. Across BOTH experiments, no demonstrated unique advantage of a trained linear component remains. Broad Q3 is still OPEN.

Next decisive research should not be another synthetic eigenvalue toy or same opened source. Require a genuinely independent source family whose structural capability is NOT delivered cheaply by an eligible strongest exact classical specialist, and verify all-in costs. If none is found, this particular neural module should remain STOPPED. Code preserved in [Draft PR #276](https://github.com/yoonsj0305/NEUMANN/pull/276); first source/prereg history immutable.