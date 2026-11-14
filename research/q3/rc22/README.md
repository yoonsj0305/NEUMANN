# RC22: proof-carrying grammar authority repair

**Research-only. Critical correction to RC21, not a neural language invention.**

The previous RC21 compact GitHub conditional acceptance could mistake a bounded-length callback returning `None` for an all-length proof. RC21 is now patched to return UNKNOWN. This standalone RC22 gate implements the classical W-method **without an exact equivalence oracle**: candidate syntax and a resettable membership-I/O endpoint plus an independently trusted upper bound U on target state count produce a complete conditional test suite. Missing bound, malformed/nonminimal hypothesis or excessive budget => UNKNOWN, never PASS. A wrong bound can cause a false conditional positive; so a bare U is an EXTERNAL TRUST ASSUMPTION, not itself a certificate of its own correctness.

The **full independently executed and SHA-verified seven-test research ZIP** in this conversation contains the actual classical observation-table grammar generator, six independent target families, exact external grader used only AFTER freeze, 1,716 exhaustive <=2-state crosschecks, 11,664 three-state exhaustive crosschecks, 286 random crosschecks, an untrusted bound counterexample, and test source:
`NEUMANN1_Q3_RC22_MEMBERSHIP_ONLY_VERIFICATION_20261025.zip`
SHA256 `29199486f40a6997b292511c76aa3dc93c05b0635e15384c336c4ee9356d2f8c`.
Clean extraction + `sh REPRODUCE.sh` + SHA manifest check all PASS.

The 6 successful conditional induced syntaxes have 3/5/7/4/4/5 states, no target table or target state number was provided to the learner. HOWEVER the verifier requires trusted bound U and membership oracle. This is CLASSICAL, no PyTorch weights, and neither invented a foundational ISA nor established global Q3/Q4/Q6/Q7. The project is obligated to pursue *external-author task, new-language invention* and benchmark all-in costs against this very inexpensive classical baseline.

W-method is established conformance-testing research (Chow 1978; Vasilevskii 1973), not NEUMANN's new algorithm.
