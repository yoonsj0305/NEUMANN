# NEUMANN 1 / Q3: exact minimum-cardinality PolyRank original certificate (posthoc)

**2026-10-19 KST | Scoped classical proof: PASS. Learning novelty: OPEN.**
This extends [PR #290](https://github.com/yoonsj0305/NEUMANN/pull/290) without changing first prospective three-origin FAIL (#287/#288) or claiming unseen-family transfer.

## Immutable original and reproducibility

Original public `SaswatPadhi/LoopInvGen@6ac90265b11431c9477dfbd33e3e3380234c0499`, `benchmarks/LIA/2005.ICALP_PolyRank/poly2.sl`; Git blob SHA1 `17448225fffad0cef48634b9d68f4f9193d616d8`, exact SHA256 `2a8a874b4f0861cb8219059dfc9572c6f02a827e80d0c0cc583c7f13c251eb7d`. The bounded script refuses modified source bytes.

Run **Python + SymPy 1.14**:

```bash
python research/evidence/q3_polyrank_full_signed_first_20261019/poly2_auto_minimal_exact.py path/to/pinned/poly2.sl
```

The separate local first exact-rational run reported `PASS_FIXED_GRAMMAR_MINIMUM_WITH_EXACT_RATIONAL_CERTIFICATE`, 242 signed directions, 26 Pre-tight candidates, eight individually inductive predicates, and 37 complete subset checks (one empty, eight singleton, 28 pairs). Minimal cardinality within these **eight**, not among arbitrary program invariants, is **two**. Exactly two 2-predicate subsets verify full original Post.

## Mathematical authority

Let `u=x-x0`, `v=y-y0`. For original `Pre: c=0,x=x0,y=y0`, the signed linear form `ac*c+ax*x+ay*y+ax0*x0+ay0*y0` has a finite lower bound iff `ax+ax0=0` and `ay+ay0=0`; all 26 such nonzero bounded directions have exact minimum zero. The original inactive transition has zero difference; active branches increment `c` by 1 and decrease `x` or increase `y` by at least 1. An atom `ac*c+ax*u+ay*v >= 0` is individually inductive exactly when `ax<=0`, `ay>=0`, `ac-ax>=0`, `ac+ay>=0`, yielding eight atoms.

Original Post has a counterexample from an invariant-state (`c,u,v`) if and only if at least one of these two bad cones is populated:

```text
BAD_POS = c>=1 AND c+u-v>=1
BAD_NEG = c<=-1 AND u-v>=1
```

They exactly cover the original conditional Post, including both cases for `x0>=y0` and `x0<y0`. The candidate inequalities are homogeneous, so a rational witness of either bad cone can be multiplied by a common positive denominator to give an integer witness. Exact rational LP is therefore both sound and complete for the original integer safety test **in this source reduction**.

**All and only minimal pairs:**

```text
PAIR A: (-c-u+v >= 0) AND ( c-u+v >= 0)
PAIR B: (-c-u+v >= 0) AND ( c >= 0)
```

The original source Trans preserves all selected predicates. All eight singleton candidates fail the exact goal check; among 28 pairs only the two displayed pass. The original published Post alone is noninductive. Byte-mutated source is rejected; a changed original `c'=c+2` branch fails an essential invariant at increment step 1.

This is not a generic learned grammar inventor. The exact reduction was derived with knowledge of this **previously opened** source and a separate source-pinned program, not a zero-shot new-family demonstration. The prior eight-atom PR #290 was Z3/cvc5 checked on original three VCs; **the new minimum-pair stage here uses independently implemented exact rational symbolic LP and algebra, not a fresh native Z3/cvc5 run**. No claim of improving whole-task runtime is supported: the local SymPy diagnostic itself required about 1.28 seconds, compared with approximately 0.715 seconds for the earlier eight-atom Python original study on a different environment/workload. Comparing these as speed measurements is not meaningful.

## Admission ledger

- `Q3_POLYRANK_FIXED_EIGHT_ATOM_MIN_CARDINALITY_2=SCOPED_CLASSICAL_PASS`.
- `Q2_SOURCE_BOUND_ORIGINAL_Z3_CVC5_EIGHT_ATOM_CERT=PR290_SCOPED_PASS` (prior result; distinct from new exact LP).
- `Q3_LEARNED_NEW_ABSTRACT_OPERATOR=NOT_PROVEN`.
- `Q6_SOURCE_FAMILY_BLIND_TRANSFER=OPEN`.
- `Q4_Q5_COMPLETE_COST_10X=NOT_PROVEN`.
- `Q7_FRONTIER=BLOCKED`; `Q1_Q7_GLOBAL=OPEN`.

Preserve all first-run failures. The next neural study must first obtain an independent-source gap against a strong exact classical specialist; another posthoc PolyRank model retry is prohibited by the frozen evidence contract.
