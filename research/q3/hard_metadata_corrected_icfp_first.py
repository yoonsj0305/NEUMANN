"""Metadata-only corrected external FIRST after PRE_151..171 missing.
No solver modifications after previous original results. Prespecified 24
source-UNOPENED existing ICFP-series problems, two groups x 12 tasks.
The prior failed first is retained as-is; this is a NEW independent cohort.
"""
import hard_unseen_adaptive_arity_gate as base

COHORT=[f'PRE_icfp_gen_{family}.{i}' for family in (1,2) for i in range(1,13)]
assert len(COHORT)==24 and len(set(COHORT))==24
base.COHORT=COHORT

if __name__=='__main__':
    base.run()
