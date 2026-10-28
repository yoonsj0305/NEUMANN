# G1 FIREFLY hard original | post-FIRST fixed classical invariant candidates and 3-VC independent check | 2026-10-28

**Research type:** Post-FIRST fully-opened source classical structure diagnostic. Not ownweight neural discovery; Q1–Q7 OPEN, G1 HOLD, G2 NOT RUN. Prior official full original cvc5 1.4.2 FIRST 12s CPU timeout on the exact original `lib/Inv_Track/andrew_lustre/FIREFLY_luke_1b_e1_1139_e2_2893.lus.sl`, repository `SyGuS-Org/benchmarks` commit `13c8deb68a873635879c9a69bc78caebd340f646`, first frozen 12 JSON SHA256 `bde9d71dc8e9120a4178e29cb1e758014c2f7effcade3ccec1e75fdc1c1505ba`. Previous independently graded ordinary + invariant source candidates 9/9 valid with grade SHA `d8573f8e3098e72d0cfdc21864a223ac0ba53660ebea1780610600808d3dba4a`. Current original is OPENED DEV.

Original FIREFLY synthesized I(state) with 23 typed Bool/Int state arguments, single `inv-constraint I init trans prop`; prop(state)=top.usr.OK. The original source's next-state top.usr.OK! is constrained by equality of the previous four integer sums vs previous stored top.res.abs_7 under a guard top.res.abs_6!. Crucially, discovering that relation from the already-opened original makes this a **classical hypothesis**, not neural learning. We precommit these exact FIVE candidates and their logical authoring order before first execution:

A. `I = top.usr.OK`
B. `I = (and top.usr.OK (= top.res.abs_7 (+ (+ (+ top.res.abs_0 top.res.abs_1) top.res.abs_2) top.res.abs_3)))`
C. `I = (and top.usr.OK (= stored_sum current_four_sum) (not top.res.init_flag))`
D. `I = (and top.usr.OK (=> top.res.abs_6 (= stored_sum current_four_sum)))`
E. `I = (and top.usr.OK (= stored_sum current_four_sum) (= top.res.abs_5 (and top.res.abs_4 (>= top.usr.i_invalid 0))))`

No other candidate can be added or tuned in this FIRST, even after seeing failures. For each: construct a correct native typed `define-fun str_invariant` with original 23 state parameters; run independent Z3 4.13.3, FULL ORIGINAL definitions and original helper signatures, 3 proper obligations INIT→I, I∧TRANS→I' and I→PROP, each with up to 10 seconds Z3 timeout, record each SAT/UNSAT/UNKNOWN, counterexample existence and wall/CPU/RSS where actually available. PASS only if all three UNSAT; any solver unknown/exception HOLD; SAT falsifies the candidate only (NOT original task unsatisfiability). Preserve all five, no cherry pick. One original task, no unseen author claims. A successful candidate is further strong CLASSICAL baseline, not learned. Time to select candidate and all failed Z3 calls must count as work.

If all fail, do NOT repeatedly generate hand-picked tweaks to get lucky; next genuine NEUMANN G1 experiment must train direct typed expression generation A vs label-shuffled B and compare specialist classical and cvc5 under equal rights on NEW independent families. If any passes, this task is a classical spend-avoid result and should not be used to claim frontier superiority.
