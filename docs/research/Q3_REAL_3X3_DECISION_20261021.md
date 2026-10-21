# NEUMANN Q3 · Decision after genuine 3×3 original-source experiments (2026-10-21)

## Original unsolved input surface

Five real pinned original SMT-LIB 2022 files: `MF_03, MQ_03, SC_03, SQ_03, MC_03`.
They were frozen by blob SHA before their very first source-body read in commit
`941ec4d16357cb9120490506e7c45cc60c76e74a`, and have been **OPENED**
since PR354.  They are not unseen Q6 results, independent authors, or a
frontier model's genuine solved-task set.

All have source-authentic full QF_NIA SMT-LIB, strict positivity and distinctness.
The 5 exact source sum-linear skeletons were extracted and independently
certified source-basis equivalence in Z3+cvc5, PR357 CI #39542891631:
MF/MQ/MC rank7 among 10 formal power-features; SC/SQ rank5 among 10.
This only proves the formal-power-feature linear constraints, NOT the actual
integer nonlinear SAT/UNSAT of the original source.

## Three separate full-source attempts

- PR354, CI #39541260820: actual full 3×3 Direct Z3 and cvc5 with requested
  finite budget solved 0/5. Power injectivity short 2×2 proof solved
  5/5 2×2 original source, but raw Direct also 5/5: no unique Q3 gap.
- PR358, CI #39543409874: 5/5 independently source-equivalent **full**
  QF_NIA SMT-LIB with one mathematically redundant row/column sum deleted,
  all other source clauses unchanged; 0/5 original, 0/5 reduced genuinely
  SAT or UNSAT. UNKNOWN is NOT matched useful correctness.
- PR359, CI #39544683167: 5/5 FULL source *nonlinear quotient* compiler,
  exact native original power terms substituted into independent integer
  RREF pivot relations, bidirectional Z3+cvc5 linear-feature equivalence
  and original non-sum AST identity preserved; matched original,
  row-subset and nonlinear quotient ALL 0/5 original SAT/UNSAT. Full solver
  evidence negative. First CI preflights failed on erroneous *protocol
  assertion parsing*, archived unchanged; final run succeeded.

## External established-number-theory discovery changes admission

Hajdu (Acta Arithmetica 113.4, 2004, p.343) explicitly attributes to
Darmon–Merel the established deep theorem excluding any three nontrivial
distinct positive k-th powers in arithmetic progression for k≥3.
Public citation: https://www.impan.pl/shop/en/publication/transaction/download/product/83315

PR360, CI #39545074888:
- 5/5 actual source SHA validated;
- independent Z3+cvc5 verifies native full magic 3×3 SUM constraints entail
  top-middle^k + bottom-middle^k = 2*center^k for MF_03(k5),
  MQ_03(k4), MC_03(k3); all three strict positives and pairwise distinct
  also verified through source-native AST hashes;
- therefore **3/5 authentic original true unbounded UNSAT** by applying
  an *EXTERNAL ESTABLISHED mathematical theorem*.
- SC_03 and SQ_03 are SEMI magic, so no 3-power AP follows from their six
  source-sum constraints, both must remain UNKNOWN and were independently
  shown not to entail the selected AP.
- the original external deep number theory theorem is NOT proved in this
  repository and is NOT independently discharged by the two SMT engines;
  they prove the exact source-to-theorem **premises only**. This is a valid
  literature-dependent mathematical derivation, NOT a self-contained formal
  Z3/cvc5 original UNSAT certificate and NOT a new theorem.
- A strong classical Direct equipped with the same published external
  theorem can derive the same result, with no learned model. This cannot
  close unique learned Q3 or Q4/Q5 iso-capability against equal-authority
  strong Direct.
- Do NOT treat these 3 literature-derived labels as neural discovery or
  add them to the machine-formal dual original UNSAT counter.

Research risk: a 3×3 SEMI magic square of distinct positive cubes is labeled
`research open` in Google DeepMind FormalConjectures
`exists_semi_magic_square_cubes` and issue #3505 (2026).
https://github.com/google-deepmind/formal-conjectures/issues/3505
This is a warning against using `SC_03` as a *routine supervised-label*
task. Do not turn an unresolved mathematical question into an invented
gold answer. `SQ_03` also lacks an original certified label here; no
claim that SQ_03 is formally known open outside this source cohort.

## Decision (no cherry-picked re-training on this cohort)

**STOP further 2×2/3×3 source-specific hotfixes, neural fitting on
these five, or claimed frontier-level success.** Original source was opened,
existing strongest applicable classical literature resolves three,
the remaining source labels are unknown, and the complete execution
currently offers no same-capability learned headroom.

The *next* Q3 unique-learned mechanism admission must use a **different
pre-source-frozen original task family** with:
1. an independently checked real original SAT/UNSAT or exact solution oracle
   for audit ONLY, not exposed to proposer;
2. strong deterministic and equal-authority mathematical/reuse baselines
   fully costed, not merely a raw SMT time cap;
3. a genuinely TRAINED original-input-conditioned model proposing
   source-specific useful structure for residual cases classical paths
   fail; no answer leakage, no filename labels, no free teacher outputs;
4. same model/parser/verifier/tool access for direct executable
   learner and no-compression ablation;
5. complete training, inference, source verification, retries,
   failure, memory and peak compute accounting, and a prospective
   held-out source family.
If no legitimate residual capability gap exists, reject training.
Frozen North Star and ALL Q1–Q7 remain OPEN.

**Summary:** Multiple scoped proofs completed (five exact
source-equivalent structural encodings, and three literature-conditional
true source original UNSAT), but none demonstrates NEUMANN's learned
unique hidden-structure discovery, capability advantage over the best
equal-authority classical method, or frontier-level cost superiority.
