# NEUMANN 1 | RC39 W-method FIRST decisive cost verdict and portability gate

2026-11-06 | **SCOPED PASS only, global Q3/Q4/Q6/Q7 OPEN.** All original RC39 and ARC source receipts preserved. No new public ARC evaluation item used.

## Precommitted experiment and actual hosted result

Precommitted scope: same **24 previously opened** RC39 finite-state reference tasks, same source-only membership rights, same trusted reference-state upper bound N=5, same frozen learner, same query caps. Classical exhaustive checker vs classical W-method checker, independent reachable-state product proofs AFTER compiled outputs are frozen. Preregistration: `docs/experiments/q3_RC39_WMETHOD_REOPENED24_PREREG_2026_11_06.json`.

- **FIRST original GitHub run #42135377794**: https://github.com/yoonsj0305/NEUMANN/actions/runs/42135377794 . Hosted CI SUCCESS, 5 unit tests PASS, both methods 24/24 independent all-length equivalence proofs, no false certificates.
- **Original exhaustive source calls**: 172,051 distinct, reproduced exactly. **W-method**: 4,737 distinct, **36.32066708887481× fewer** (97.24674660420457% reduction).
- **Original source characters**: 1,362,696. W-method: **22,843**, a **59.654861445519415× reduction in source characters**.
- Same FIRST run process CPU summed over tasks: exhaustive **613.432559 ms**, W-method **20.265010 ms**. Ratio **30.270528×**; environment and Python implementation dependent, *not* a full-NEUMANN end-to-end performance claim. Total sequential script CPU 637.805074 ms includes setup/audit overhead.
- Exact 24 task rows, generated executable model audit flags, distinct call/character counts and per-algorithm process CPU preserved in `docs/experiments/q3_RC39_WMETHOD_REOPENED24_FIRST_RECEIPT_2026_11_06.json` (recovered from unmodified first hosted log output and normalized to a text JSON file).
- **Additional hosted #42135972803** https://github.com/yoonsj0305/NEUMANN/actions/runs/42135972803: repeated original query totals **172,051 vs 4,737**; per-algorithm CPU **704.168472 vs 23.423992 ms**, ratio **30.061847×**. CI SUCCESS, no retuning. This is a corroborating run, not substituted for the original FIRST.

## Conditional implementation generalization, without model retraining

A separately preregistered implementation stress test varies input alphabet size (3 or 4 symbols), output alphabet size (2 or 3 symbols), and reference state count (3,4,5,6), with 16 fixed seeds per combination. This yields 256 reference structures and **512/512** independent exact product-equivalence classifications correctly matching the membership-only verifier. The earlier independent test family includes all 260 one/two-state structures times 3 hypotheses = 780 checks and 250 three-state references times 2 hypotheses = 500 checks. So at least **1,792** independent product classifications exercised the implementation across tests, plus the 24 end-to-end learning cases. All 6 unit tests passed in #42135972803.

Crucial distinction: this proves the **generic verifier code carries across finite-state alphabet/size variations**. It is **not semantic-family Q6**: all cases still live in the designer-given finite-state Mealy substrate.

## Trust model, failure modes, degradation

- **Assumptions**: complete deterministic state machine, truthful resettable membership observations, finite fixed alphabet, public **correct** upper bound on reachable reference states.
- An explicit negative control supplies an **incorrect bound**: finite conformance can then issue a false all-length certificate. It is a violation of the theorem premise, not a disproof of W-method itself.
- Unknown or unbounded state count, nondeterministic physical environment, inconsistent reset, noisy output, budget exhaustion or interface violation: **UNKNOWN, never silent PASS**. Production cannot infer the state bound from finitely many samples alone.
- This is a well-known classical W-method transformation. No neural training or novel representation base ISA was added. Same-rights classical alternatives include Wp and HSI; no comparison to them yet. Therefore the **36.32x result is against the project's prior naive exhaustive classical checker, not the strongest available classical conformance implementation**.

## Scientific conclusion and next high-value decision

**SCOPED CLASSICAL CONFORMANCE COST PASS**. The code is a portable structural verification primitive and reduces cost under specific known model assumptions.

**OPEN:** Q3 learned autonomous structure discovery, Q4 total learning+inference cost superiority over strongest equal-rights classical method, Q6 independent external semantic-family transfer, Q7 frontier-level accuracy. Do not spend the remaining 11 globally unused original ARC-AGI-1 IDs on this verification improvement. A truly independent domain, frozen proposal policy, and strong competing baseline are required before any such global claims.

The historical T1 12/12 / 3,312/3,312 chat-era study is documented separately and **not reproduced** because its original ZIP bytes were unavailable. PR #631 (P2.1.1), #632 (P2.2) and #633 (P2.3) already carry their respective code/evidence in Draft; do not claim they were missing from GitHub.

References: TACAS 2024 `Small Test Suites for Active Automata Learning`, classical W-method, https://link.springer.com/chapter/10.1007/978-3-031-57249-4_6 . This PR is Draft and stacked on Draft #651, itself stacked on provenance Draft #650. Do not merge as a global North Star PASS.
