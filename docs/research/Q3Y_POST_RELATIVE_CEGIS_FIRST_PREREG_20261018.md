# Q3Y | Safety-region-relative equality CEGIS pivot (pre-registered 2026-10-18)

## Why this is a new hypothesis, not a rescue of Q3X's failed first trial
First Q3W CI #39102940034 blocked on exhaustion of fresh LIA origin groups before running any original source. First Q3X CI #39103213463 failed on a logically non-discriminating synthetic B. After the documented synthetic correction (first failure retained), Q3X replay #39103332296 exposed a **mathematical** failure: unconditional affine equality hull must admit a spurious negative-guard transition from x=y<=0; it therefore discards a useful x=y relation, even though the original program's target Post(y>=1) excludes that branch in an inductive proof. NO NIA source file contents were read in either Q3X failed run. Do not retrospectively label Q3X PASS.

## Frozen new mathematical hypothesis
Generate a postcondition-RELATIVE affine equality hull E rather than globally inductive affine hull:
- Initial condition: original Pre(x) => E(x), exact SMT.
- Equality consecution: E(x) AND original Post(x) AND original Trans(x,x') => E(x'), exact SMT.
- The full original proof is still **not** admitted until all THREE independently negated original VCs for I(x)=E(x) AND original Post(x) are UNSAT:
  1. Pre(x) AND NOT I(x)
  2. I(x) AND Trans(x,x') AND NOT I(x')
  3. I(x) AND NOT Post(x)
- The equality proposal uses only exact-model counterexamples and growing exact rational span, never gold invariants, teacher covers or direct SPACER output. The guarded equality hull can be inductive *relative to the original safety region*; merely proving two equality checks is NOT enough for safety. If Post itself is not inductive inside E, mark the proof FAIL and keep original goal UNKNOWN/unsafe as justified, never claim safety.
- Span rank rises strictly on each counterexample <= n+1, preserving same 16 state cap, 2.5s SMT cap per check, original source-body SHA and two parser-path XOR UNSAT gate, Bool 0/1 embedding, original strong SPACER and Post-only controls, no benchmark source redistribution.

This is a target-conditioned **classical abstract interpretation / CEGIS** mechanism, not a new academic invention, not trained neural intelligence, and not proof of global Q3. It discovers useful target-dependent hidden structure without a gold oracle if a new untouched benchmark's Post-only inductive check fails and the E+Post original independent 3VC check passes.

## Data/controls frozen BEFORE first Q3Y execution
- Synthetic A: Q3V joint rotation fixed point; two equations individually fail, joint relative E+Post PASS.
- Synthetic B: Pre=(x=y=1) OR (x=y=2). Branch positive x>0 -> (x+y,x+y), negative x<=0 -> (x,y-5). Post y>=1. Relative E must discover x=y and certify original full three VCs; Post alone must fail. The prior unconditional engine failure is retained as ablation, not hidden.
- Synthetic C: mixed Bool/Int flag, unreachable negative branch, Post x>=1; relative E including true flag must prove goal, mutated reachable-negative branch must fail original 3VC.
- Synthetic D: actual unsafe x'=x-1 from x0=0 with Post x>=0; no false proof.
- Real historical development: exactly the same previously opened 12 LoopInvGen LIA originals.
- Prospective NIA: **same, unchanged** path-only first two origin groups and first 4 genuine .sl files/group from Q3X 2026-10-18 source revision 6ac90265b11431c9477dfbd33e3e3380234c0499. Their bodies have not been opened in a prior successful/failed original trial. No posthoc changes to source lists, caps, thresholds, or compiler.
- Control comparison: Q3W unconditional CEGIS synthetics and prior frozen Q3U/Q3V; never claim resource or solver dominance, and count discovery/verification/specialist elapsed ms separately.

## Frozen decision
A bounded Q3 transferable submechanism **PASS** only if synthetic controls all pass, and the freshly selected TWO NIA origin groups each contain at least one independently true original source theorem (full 3VC UNSAT) that Post alone cannot prove, with nonzero discovered affine equalities and parser parity UNSAT. If fewer than 2 groups, NO prospective cross-domain PASS. Full global Q1-Q7 remain OPEN pending broader representational domain, deployment, Q4/Q5 iso-capability costs and Q7 real frontier gap evidence. Preserve the full first fresh NIA run and stop if cross-domain negative.
