# Q3K-2 | ONE AUTHENTIC ORIGINAL C PROGRAM FULL SAFETY PROVEN BY CLASSICAL PROOF COMPOSITION

Date: 2026-10-18 KST. **Scoped ORIGINAL-C safety theorem PROVEN**. **NEUMANN learned Q3/Q4/Q7 remain OPEN**.

## Exact original and immutable provenance

One actual program: `dataset/loop_invariants/LinearArbitrary-SeaHorn/loops/loops/sum04_true-unreach-call_true-termination.i.annot.c` from Microsoft Loopy dataset commit `91fe89245a0894ec8ad3741d85ae91ce3b552b2e` and dataset Git blob `17cac0f6734a39f0fe73558199cc2ad8d5c1a810`. Exact original source SHA256 `7b1ed83d1a2e80a1e5aa97e27a23c7ac1a53bd734cc95808ecce4aa868c41a23`. The source was previously OPENED in Q3I/Q3J; this is **not blind cross-group generalization**.

Source unchanged, published Loopy answer/invariant not supplied to either proposer, Q3F competition holdouts still unopened. Both methods use scoped original Q3H C-to-integer semantics (one supported loop, integer state, no unsupported pointer/alias effects, explicit signed 32-bit range obligations).

## Historical first-only results preserved, without retconning

1. [Q3J first original study #39086074828](https://github.com/yoonsj0305/NEUMANN/actions/runs/39086074828), artifact **12121180486**: generic source-only polynomial nullspace + Houdini generated 3 quadratic relations and inductive certificate. **Original init UNSAT, induction UNSAT, signed-overflow UNSAT, exit-safety SAT**. Q3J **did NOT** prove whole original.
2. [Q3K first CHC study #39086984020](https://github.com/yoonsj0305/NEUMANN/actions/runs/39086984020), artifact **12121177715**: original prelude overflow UNSAT, reachability BadExit **UNSAT in 69.860ms**, reachability BadOverflow **CANCELED after 15 seconds**. Three independent original-like controls all PASS, 64-step BMC found no bad exit (not a full proof). Q3K **did NOT** prove whole original.

## Mathematical composition, separately preregistered

Protocol committed in `docs/research/Q3K2_COMPOSITION_PREREG_20261018.md` at commit `8702f399dc8c10fd8b8e40fe4133c0e365f1423d`, **after first Q3K outcome but before composition rerun**.

Let `Init` be original initialization, `G` original loop guard, `T` original transition, `P` original postcondition, `I` the classically generated Q3J invariant. Let `Reach` be all states reachable using the original CHC transition that excludes signed integer overflow. The proof is:

- `Init => I` by Q3J original initialization UNSAT.
- `I && G && signed_source_state => I(T)` by Q3J original inductive consequence UNSAT.
- `I && G && signed_source_state => no signed source arithmetic overflow` by Q3J original overflow obligation UNSAT; Q3K prelude signed-overflow is also UNSAT. Consequently, all reachable actual steps are contained in Q3K's safe-transition Reach relation, rather than silently removed by its no-overflow condition.
- `Reach && !G => P` by Q3K directly generated source-only SPACER `BadExit UNSAT`.
- Therefore, under this explicit C semantics subset, `Init` followed by any number of original loop transitions cannot overflow and cannot reach an unsafe exit. **This closes the previously missing complete ORIGINAL program safety theorem.**

No single first proof route could close all obligations. We use complementary mathematical implications from two separate proof approaches, **both relying on the Z3 solver backend**, not two independent theorem prover implementations.

## Actual independently rerun composition

[GitHub Actions **#39087265530**](https://github.com/yoonsj0305/NEUMANN/actions/runs/39087265530) **SUCCESS**, immutable artifact **12120424041**. **Code reran both** source-only Q3J polynomial induction/overflow and Q3K CHC bad-exit on exact same source. No hidden manually supplied lemma or changed decoding.

- Q3J rerun: init UNSAT, inductive UNSAT, overflow UNSAT, exit remains SAT, false safety goal SAT, empty invariant SAT.
- Q3K rerun: original prelude overflow UNSAT; SPACER reached BadExit **UNSAT**, about **60.065ms**. 64-step BMC independently found no reachable bad exit within that finite bound.
- Original source state signature `(i, sn)` matched exactly; **nine composition condition checks 9/9 PASS**. Three synthetic controls (real unsafe termination, genuinely safe termination, signed overflow) each returned the expected reachable SAT/unreachable UNSAT results.
- Composed proof study measured **905.680ms** local job runtime inside the Python step, not total install/setup/CI cost and not a matched model energy or frontier benchmark.
- **Final scoped verdict:** `ONE_AUTHENTIC_ORIGINAL_C_SAFETY_PROVEN_BY_CLASSICAL_COMPOSITION`. Historical Q3J whole-source NOT PROVEN and historical Q3K overflow UNKNOWN are unchanged.

## Research admission limits and next STOP

This is a legitimate first **full original program safety proof** for an instance previously unsolved by Q3I and Q3J, but it comes from **classical polynomial invariant discovery + classical SPACER reachability composition**. Zero neural forwards and no neural training. It does **not** close NEUMANN Q3 autonomous learned novelty, Q4 >10× equal-success complete costs or Q7 frontier parity. All global Q1–Q7 remain OPEN.

**STOP tuning this opened original.** The mathematical lesson for NEUMANN is not “train a larger model,” but **decompose the original specification into independently certifiable obligations and let different cheap classical specialists discharge them** before ever calling a learned typed AST operator proposer. Q3F’s two competition-grade 2025/26 unsolved source-group targets remain SHA escrowed until the learned model, costs and strong solvers are frozen.
