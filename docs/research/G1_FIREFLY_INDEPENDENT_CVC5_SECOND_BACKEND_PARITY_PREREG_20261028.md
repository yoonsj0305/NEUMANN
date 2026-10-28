# G1 FIREFLY post-FIRST independent second formal backend parity | frozen check protocol 2026-10-28

This is an **independent solver reproduction** after both original official SyGuS source and native C/Z3 candidate results were opened. NEUMANN ownweight neural discovery is NOT demonstrated, global Q1–Q7 OPEN, G1 HOLD, G2 NOT RUN.

Pin benchmark official original Git **13c8deb68a873635879c9a69bc78caebd340f646**, path **lib/Inv_Track/andrew_lustre/FIREFLY_luke_1b_e1_1139_e2_2893.lus.sl**. Official native CVC5 1.4.2 from pinned binary asset SHA256 **0af677313c8277dc558d3049b192389db4d975d31c968fbd6f31cf0849ee411d** originally **TIMEOUT** in fixed 12 CPU/15 wall headroom first. Frozen five non-adaptive symbolic hypotheses original Z33-VC [run #40629900597](https://github.com/yoonsj0305/NEUMANN/actions/runs/40629900597), 5-candidate original source result JSON exact SHA256 **fb98bc250e57131cb671c613616796373a5f5ff2a93acd4ebb0472cd28f810c4**, source freeze committed before that actual run. Original source has **23 typed state variables**, source `synth-inv str_invariant`, complete original `init`, `trans`, `prop`, and exactly one `inv-constraint str_invariant init trans prop`.

Known Z3 4.13.3 actual logic verdicts:
- A_OK_ONLY: INIT UNSAT, CONSECUTION SAT, POST UNSAT => NOT INDUCTIVE.
- B_OK_AND_STORED_SUM: UNSAT, UNSAT, UNSAT => PASS.
- C_OK_SUM_NOT_INIT: INIT SAT, CONSECUTION UNSAT, POST UNSAT => NOT INITIALLY TRUE.
- D_OK_IF_EVENT_THEN_SUM: UNSAT, UNSAT, UNSAT => PASS.
- E_OK_SUM_AUX_RELATION: UNSAT, UNSAT, UNSAT => PASS.

**Second engine protocol**: Download frozen first five-candidate artifact and verify result JSON SHA and individual candidate program SHA with no re-synthesis, preserve raw source exactly pinned original Git SHA. Independently assemble all 15 *genuine* named SMT-LIB2 verification conditions using original complete `define-fun` helpers, original `init`, `trans`, `prop` parameter signatures and original 23 state typed argument sort, frozen source candidate I:
1. `init(s) AND NOT I(s)`;
2. `I(s) AND trans(s,s') AND NOT I(s')`;
3. `I(s) AND NOT prop(s)`.
Original source trans helper signature must be exactly 2× source invariant state sort. Save each full SMT script; run **official CVC5 1.4.2** on each script with up to 8 seconds wall and max 7 seconds CPU. No Z3 library imported for second backend checks. Record CVC5 actual stdout/stderr SHA, all 15 SAT/UNSAT/UNKNOWN/error, wall and CPU cost. If all 15 match the prior independent Z3 expectation, claim **2 solver parity on the five fixed hypotheses** but NOT new model learning, not fully independent parallel source parsing (one parser utility can be shared), and NOT an equitable apples-to-apples full program synthesis runtime comparison. Otherwise state mismatch/HOLD and don't promote.

This independent check is an engineering trust audit. The original 12-task classical source baseline result is retained (nine originally verified by CVC5 native plus postfirst Z3, sorting_naive/max6/FIREFLY three assistant classical postfirst structures). Human discovery time and all solver runs count against any full-compute claim; none gives 10× NEUMANN ownweight achievement. PR #616 DRAFT, main not merged.
