# CORE-27: Non-goal-visible intermediate homomorphism + learned operator token

**2026-10-16. Development-only scientific result, Q1–Q7 remain OPEN. Do not upgrade frozen failures.**

## Exact authentic external source
CHC-COMP 2026 `ADTRem/isaplanner/goal52_000.smt2`, repository commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, Git blob `f27b6a56e752498b2a67cb59bd739aebbb7dd179`, **2,605 bytes**, SHA256 `3db92ef5e5f890bf6fc0a61aefddd45bfe364fcd9b39653c9f542c59bcd372f5`. Original was independently fetched and byte-matched before checking any certificate.

## What was actually proved
Original final failure goal states count preservation under reverse. Unlike goal43 and goal47, the key **intermediate** theorem below is not stated in the final unsafe goal:

```
COUNT(x,APP(A,B)) = COUNT(x,A) + COUNT(x,B)
```

Certified **2/2** auxiliary homomorphism induction steps, then **2/2** reverse-count induction cases, then **11/11 independent negated original Horn clauses UNSAT** under HUMAN-WRITTEN recursive meaning for count, append, reverse. Controls: **2/2 false arithmetic relations SAT** and **4/4 deliberately poisoned original clauses SAT**. Removing homomorphism from the chosen reverse induction leaves its step UNKNOWN at 1.2s (does **not** establish that every mathematical approach needs that lemma). Original standalone Z3 4.13.3 is UNKNOWN(timeout) at 2s and 8s; this is NOT strongest specialized CHC baseline. Local clean extraction with exact upstream source separately supplied: **14/14 pytest PASS**.

## The learned part and strict novelty limit
A **3,748-param CPU MLP** was trained 1.270s on 3,000 synthetic algebra probes for `+,-,max,min` and then frozen, checkpoint SHA256 `3879daf9ecc2b588401f44f404118be81bc6aa8ee5314b87f6132bc73cc13f9b`. Eight source-conditioned numeric probes, **generated using a researcher-supplied count interpretation**, made the frozen model emit the `+` operator. The *entire homomorphism lemma skeleton*, the source interpreter, the probes and induction templates are researcher-provided. The learner does not see the whole original source and does not invent the abstraction language. Further, the researcher inspected goal52 BEFORE training/probe design, so **NOT blind source transfer**.

The learned-proposed lemma is actually inserted into Z3: homomorphism 2/2 UNSAT, reverse induction 2/2 UNSAT, and original 11/11 UNSAT. The equally authorized symbolic grammar enumerator finds `+` with 4 candidates (~1.86s full SMT search in one run), and a direct exact arithmetic evaluator of the same eight observations trivially finds `+` faster without training. No irreducible learned headroom.

## Postfreeze falsification and fair economic baseline
Distinct-seed synthetic operator tasks (NOT independent public sources): 
- in-range: neural **393/400**, exact classical **400/400**
- wider nonnegative: neural **392/400**, exact classical **400/400**
- signed OOD: neural **235/400**, exact classical **400/400**
- total neural **1020/1200**, exact classical **1200/1200**.

120 paired warm 400-case vectorized batches: neural median **0.14779 ms** for **394/400**, NumPy classical exact median **0.19209 ms** for **400/400**. This does not show iso-capability advantage: different accuracy, and training/load/inference/proof complete costs not included in the paired microbenchmark. Exact arithmetic already solves the class; no frontier parity, novel new abstract TYPE, full-system economy or 10x claim.

## Reproducibility and archive
Release `NEUMANN_CORE27_NON_GOAL_INTERMEDIATE_LEARNED_20261016.zip`, **35,214 bytes**, SHA256 **`ce5f164d0e75bffb563ccc5b8f6671528b0376fad537244e8d38b67b19dca57b`**, 18 entries (17 payload files + manifest). CRC and SHA manifest confirmed. Includes frozen checkpoint, training/test scripts, receipts, Z3 bridge, negative controls, 14 tests. Upstream CHC source not redistributed; pinned fetcher requires source to be supplied separately. GitHub text evidence committed; **the original ZIP and weights are NOT yet uploaded as GitHub binaries**.

Full local CORE1–27 vault: `NEUMANN_CORE1_27_COMPLETE_LOCAL_VAULT_20261016.zip`, SHA256 `d64a1213d216691353a99ec8d51e95dd4be2c9f720b9d943b5084eda90b43828`, **2,992,388 bytes**, **32** original archive ZIPs, 32/32 hash+CRC verified and isolated safe uploader `LOCAL_PREFLIGHT_PASS` only. Remote bytes NOT transferred.

**Verdict: NON_GOAL_VISIBLE_CLASSICAL_AUX_PROOF + LEARNED_OPERATOR_TOKEN_IN_CERTIFIED_ORIGINAL_PROOF, BUT NEW_ABSTRACTION_TYPE_NOT_LEARNED, STRONG_EXACT_CLASSICAL_SUFFICIENT, ALL_GLOBAL_Q_OPEN.** 
