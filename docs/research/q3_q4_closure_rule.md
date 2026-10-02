# Q3/Q4 closure rule — LP structural-support line

Frozen before v0.0.101 evidence.

The project will no longer keep Q3 and Q4 open indefinitely for the current
constructed-LP structural-support line.

## Operational meanings

For this task family:

- Q3 PASS means a target-free deployable structural proposer, with verifier
  and charged Direct fallback, recovers at least 80% of the structural savings
  available from the free Oracle support on every preregistered fresh cell,
  under equal original-problem certificate authority.
- Q4 PASS means the same system keeps discovery burden at or below 20% of
  recovered pre-discovery savings and complete amortized cost below Direct on
  every preregistered fresh cell.

Q3 and Q4 are closed jointly because a structure that is not economical is not
an admissible NEUMANN mechanism, and a cheap proposal that does not recover
enough useful structure is not sufficient for Q5.

## Final local sequence

1. v0.0.101 may perform exactly one training-free development comparison of
   frozen quotient ranking:
   - STATIC: top2m -> restricted solve -> verifier -> Direct fallback;
   - ADAPTIVE: top2m -> if verifier rejects, top4m -> verifier -> Direct fallback.
2. No refit, threshold change, support-width sweep, or use of the sealed
   v0.0.98 holdout is allowed.
3. If neither frozen contract clears the Q34 development conjunction, close
   Q3 and Q4 as REJECTED_CURRENT_LP_FORMULATION and stop local point-support tuning.
4. If one contract clears development, freeze that contract and register one
   new fresh holdout with new seeds.
5. If that fresh holdout clears the unchanged Q34 conjunction for both model
   seeds and every preregistered cell, close Q3 and Q4 as PASS_LP_MECHANISM
   and advance directly to Q5.
6. If the fresh holdout fails any required cell, close Q3 and Q4 as
   REJECTED_CURRENT_LP_FORMULATION and do not perform another local rescue.

These closures are scoped to the current constructed-LP mechanism. They are not
claims that general structural discovery or compute economics are solved across
all domains.
