# Q3K-2 | Predeclare original-source compositional safety certificate

2026-10-18 KST. This is a **second, explicitly post-Q3K-result** test; it does not replace or alter the first immutable Q3J/Q3K results.

## Observed frozen first receipts before this registration

Original single file, SHA256 `7b1ed83d1a2e80a1e5aa97e27a23c7ac1a53bd734cc95808ecce4aa868c41a23`, pinned Loopy revision `91fe89245a0894ec8ad3741d85ae91ce3b552b2e`, unchanged source.

- Q3J first run [#39086074828](https://github.com/yoonsj0305/NEUMANN/actions/runs/39086074828), artifact **12121180486**: from source-only polynomial Houdini, original `INIT UNSAT`, `STEP UNSAT`, `SIGNED_OVERFLOW UNSAT`, original `EXIT SAT`. Whole certificate Q3J **FAILED**.
- Q3K first corrected-control run [#39086984020](https://github.com/yoonsj0305/NEUMANN/actions/runs/39086984020), artifact **12121177715**: genuine wrong-exit, safe-exit, signed-overflow controls all PASS. For original source, `PRELUDE_BAD UNSAT`, `BadExit UNSAT` under source-only Reach CHC transition restricted to no signed overflow; `BadOverflow ERROR: canceled after 15 seconds`. Bounded exact BMC no bad exit up to 64 steps, not a global proof. Whole direct Q3K **UNKNOWN**.

This pairing reveals a **complementarity**, not that either Q3J or Q3K alone proved complete safety. They share Z3 backend and Q3H's finite one-loop C semantics, so no claim of diverse independent theorem provers or all ISO C.

## Proof composition principle

Let `I` be the source-only Q3J polynomial/Houdini inductive conjunction, `R` be Q3K's exact source-specific Reach CHC over original state variables, `G` the original loop guard, `T` original C state transition, and `P` the unchanged original postcondition.

1. **Base:** Q3J original init proof guarantees `Init=>I` after original prelude; Q3K checks original prelude signed arithmetic safe and source state domain.
2. **Inductiveness:** Q3J checks `I(s) && G(s) && signed(s) => I(T(s))` UNSAT when negated.
3. **No execution overflow:** Q3J checks `I(s) && G(s) && signed(s) => signed(T(s)) && in-range(source evaluated arithmetic)`. Combined with (1)-(2), every reachable loop transition is legal signed-32 C arithmetic. Consequently, **Q3K's Reach transition exclusion of overflowing steps discards no real reachable execution**.
4. **Original exit safety:** Q3K direct SPACER independently proves `Reach(s) && !G(s) => P(s)` (BadExit UNSAT) for that exact safe-transition Reach relation.
5. Therefore original program exit safety and no signed arithmetic overflow both follow in the shared explicitly supported C subset. Deliberate wrong-safe/unsafe/overflow controls must still pass.
6. **Do not** label whole original PROVEN unless a *fresh execution on the same exact original source* regenerates the Q3J init/step/no-overflow UNSAT, the Q3K prelude UNSAT and bad-exit UNSAT, and all three controls. The original Q3K overflow timed-out result must stay `UNKNOWN`; do not rewrite history.

No published Loopy invariant or benchmark gold supplied. Source grammar degree at most 2 remains original Q3J code. **No new semantic hints, source-specific lemma patch, model training or inference.** This is a two-lemma compositional **classical** proof, NOT NEUMANN autonomous learned operator discovery, Q4 equal-outcome 10x or Q7 frontier gap. Q1–Q7 OPEN, Q3F holdout source bodies unopened.

If source identities mismatch, any fresh obligation SAT/UNKNOWN, controls fail, a backend/translation mismatch, or unsupported C syntax, verdict `NOT_PROVEN`, no success claim. The success is narrow but substantive: **a complete original-C safety theorem under the existing accepted Q3H source semantics**, built from two complementary classical methods.
