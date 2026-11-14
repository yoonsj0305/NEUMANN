# Frozen FIRST results: real ownweight autoregressive AST sequence generator
Date 2026-10-26. NO heldout gold inspected when this was committed.

Prereg GitHub commit: `81d1f768fae67a8487a0a3cf3be4c0e93744934e`.
FULL executable first prediction local SHA256: `661e04887a620a2ce9d2edbb60575f97f95b29cd96411336f4fbd43dd912fc21`, file `FIRST_FROZEN.json`. Full 8-task source-only data in conversation runtime `holdout_source_only.json`. File/code SHA recorded within first receipt. 4 paired seeds [3,7,11,17] 140 training epochs, dev 12 distinct originally verified external PROSE old task solutions out of 19 candidates, no per-task program lookup at inference.
Original cohort exactly `Log.000021,UserAgent.000004,Name.000011,Email.000007,Address.000006,Phone.000003,City.000007,DateTime.000004` (all ORIGINAL spec SHAs in source-only).
- `Name.000011`: only 2 available original examples; **INELIGIBLE** under prereg, NO substitution, total scored task count **7**.
- A real target-supervised Torch autoregressive AST model: **0/7 SOURCE_FITS** in EVERY seed. Source-only HOLD 7/7. Its output sequences are new compositions of trained verified atoms, not hard-coded finished task IDs. This does NOT prove useful new semantics.
- B sham program-target permuted train control: 1/7 source-fit on `Phone.000003` in 3/4 seeds, HOLD others. This is a disconfirming pattern, not a success for A.
- C strong classical dynamic substrings: 5/7 source-consensus, 2/7 HOLD, originals source-only:
  `Log.000021` => [`      235->66      `,`      81->207      `,`      185->175      `];
  `Email.000007` => [`henrique@fabrikam.com`];
  `Address.000006` => [`Rome`];
  `Phone.000003` => [`x571`,`x188`,`x8294`];
  `DateTime.000004` => [`20:41:48 2067-01-08`,`00:46:58 1984-05-23`,`04:29:27 1858-12-08`].
  `UserAgent.000004` and `City.000007`: HOLD.
- Precise state: **only source fits are known**, untouched external heldout target strings have NOT been inspected at this stage. Any subsequent grading is AFTER this immutable GitHub commit and must preserve failure.

Model vocabulary is extracted from 12 fully DEV-verified classical AST programs; fixed interpreter vocabulary does not contain unbounded open-ended semantic code ops; generalize program combinations not true ISA invention. Reward is teacher-forced program target, sham permutes target among tasks, not a formal reward-permutation meta-RL control. Both models spend significant CPU relative to classic. No Q1–Q7 promotion.
