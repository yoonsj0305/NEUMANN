# NEUMANN 1 · G0 real SMT-COMP 2026 QF_NIA: three independently certified original SAT proofs

**2026-10-21. Evidence boundary: source-bound non-neural classical structural problem solving, NOT newly invented neural intelligence, NOT global Q3/Q4/Q7.**

## Source and first-evidence identities

- Official SMT-COMP 2026 G0 union, parent branch `research/g0-smtcomp2026-official-union-20261020`, genuine raw original-status source cohort: 17 QF_NIA tasks unresolved by ALL 17 official submitted configurations.
- Original SMT-LIB corpus **SMT-LIB/benchmark-submission-2022@`81a39628827f61fbd74c6f3e67feb5c1b740d2f0`**.
- Original `STC_0228.smt2` first SHA metadata frozen at `39ed7c703a922daa4d99e72dfee2e18ea3b77069`. Its content was inspected BEFORE designing mod9 numeric proposer. Therefore **opened development**, not an unseen transfer.
- Seven later program Git hashes and unchanged 10,000 bound/algorithm preregistered BEFORE source bodies at `8ee9fbf8588ae0dd3cea67c121d4fde02699426c`.
- Immutable FIRST seven transfer Actions #39531276557 retained two exact original SAT witnesses, five UNKNOWN and first negative control cvc5 timeout. Artifact SHA256: `96e1f43b7c1fda093be995b8e5b8bd7cf90a247e83c934e61f52cef13431dc00`. Its overall strict gate FAILED; do not rewrite history.
- Diagnostic Actions #39531573511 found first wrong-grounding cvc5 returned UNKNOWN after 15 sec, Z3 returned UNSAT, independent integer arithmetic gives 43,035,697 != 228. Therefore we repaired **negative-control admission only**, preserving unknown cvc5 rather than inventing UNSAT.
- Successful checker-repair replay [Actions #39531809519](https://github.com/yoonsj0305/NEUMANN/actions/runs/39531809519): original development SAT PASS + two previously first-frozen transfer original SAT PASS + five UNKNOWN, all original true SAT candidates independently Z3+cvc5 verified. This replay is **not** a second first-blind run.

## Three actual original source witnesses

| Proven original | (x,y,z) from bounded proposer | Exact arithmetic | Scope |
| --- | --- | --- | --- |
| `STC_0228.smt2` | (-3788, -1577, 3877) | (-3788)^3 + (-1577)^3 + 3877^3 = **228** | opened development |
| `STC_0268.smt2` | (5667, -6823, 5138) | 5667^3 + (-6823)^3 + 5138^3 = **268** | NEW prospective first frozen transfer |
| `STC_0813.smt2` | (-7643, -2357, 7717) | (-7643)^3 + (-2357)^3 + 7717^3 = **813** | NEW prospective first frozen transfer |

The source's exact original `(assert (= (+ (* x x x) (* y y y) (* z z z)) N))` is not weakened. To independently verify, the generated signed integer assignments are appended to the original source (driver `check-sat`/`exit` relocated), then checked in two independent solver implementations: Z3 4.13.3.0 and checksum-pinned cvc5 1.4.2. Positive actual source assignments both return SAT. All source original Git blobs/byte sizes are checked first. The code fails closed on unsupported other original ASTs.

## Proven exact modular reduction and why it works

For every integer x, `(x+3)^3 - x^3 = 9(x^2 + 3x + 3)`. Hence x³ modulo 9 depends only on x modulo 3:

- x≡0 mod3 ⇒ x³≡0 mod9
- x≡1 mod3 ⇒ x³≡1 mod9
- x≡2 mod3 ⇒ x³≡−1 mod9

For `N≡3 (mod9)` (N=228, 291, 588, 786, 813), every cube must equal 1 modulo 9, since each is in {−1,0,1} and their sum is within [−3,3]. Thus **x≡y≡z≡1 mod3**; the possible integer triple residue classes are reduced from 729 to 27, an EXACT 27-fold shrinkage in residue search domain. For `N≡7 (mod9)` (N=268,880), exactly two cube residues are −1 and the third 0, in any order; 81 of 729 classes survive, EXACT 9-fold fewer residue triples. `N≡6 (mod9)` (N=609) forces all three cube residues −1.

The numeric algorithm searches the **bounded range −10,000..10,000** via sorted pair-of-cubes and exact binary search; every skipped residue class is mathematically impossible. A numeric MISS in this range is only UNKNOWN, NOT original UNSAT. The algorithm itself is ordinary classical modular pruning and two-sum. It is NOT new mathematics. Complete raw original independent SMT2 checker work and failed control receipts are archived.

## Scientific scope and next decision

- Three authentic original QF_NIA SAT proofs recovered from benchmarks that all 17 SMT-COMP 2026 submitted configurations failed on the official 1,200-second contest setting; those historical solver outcomes are NOT same-hardware time comparisons.
- Two SAT proofs are prospective transfer of one unchanged source-schema and fixed algorithm to first unseen source bytes. Five other genuine first targets remain UNKNOWN.
- No learned weights, neural forwards, model-generated structures, oracle witness labels, or external literature SAT triples at inference. Published outside specialist methods can overlap; no claim of new algorithm, unique NEUMANN superiority, or frontier-level problem solving.
- A next legitimate gate is matched current strong generic Z3/cvc5 **and specialized modular-cube search** with full cost against fresh unseen original families. The current result establishes a bounded classical source-specific Q3-B mechanism and genuine source-certified SAT answers, but **GLOBAL Q3, Q4, Q5, Q6, Q7 remain OPEN**.

## After-first matched CPU direct bounded evidence across ALL seven

A separate posthoc test was run on **all seven first-frozen transfer originals**, not only on the two solved successes: [Actions #39532298808](https://github.com/yoonsj0305/NEUMANN/actions/runs/39532298808); raw artifact SHA256 `b3440563fd7ada611c2f200596d0c2f81414652251351eeb63f935ff0bf7696d`.

- Source Git SHA/bytes verified: **7/7**.
- Current Z3 4.13.3.0 direct on raw unchanged original SMT2: **UNKNOWN for 7/7** after its per-source 15-second bound.
- Independently pinned cvc5 1.4.2 direct on raw unchanged original SMT2: **UNKNOWN for 7/7** after its per-source 15-second bound.
- Zero original task proof certificates from these two generic bounded Direct methods: **0/7**. This is strictly 15-second current-GitHub-runner evidence, not UNSAT, nor an exhaustive union of all best solver/number-theory methods.
- The preregistered fixed mod-9 + numeric sorted two-sum proposer produced **two independently verified original SAT proofs out of seven new original sources**, retaining FIVE original UNKNOWN at fixed radius 10,000.
- Thus the bounded algorithm has an authentic **2/7 versus 0/7 capability improvement over these two generic direct executors**, though both systems have unmatched capability and no same-capability 10× runtime quotient exists. Stronger specialized *sum-of-three-cubes* algorithms can use the same representation, so unique NEUMANN superiority over the strongest specialist Direct is **NOT ESTABLISHED**.
- On opened development `STC_0228`, independently verified source SAT proof required roughly 0.53 seconds of full recorded proof-path wall on the same runner; both generic direct methods returned UNKNOWN at 15 seconds each in [Actions #39530350142](https://github.com/yoonsj0305/NEUMANN/actions/runs/39530350142). Again this is a censored bounded capability comparison, not a measured pure 28× or 57× execution time ratio.
- No neural model was fitted or called. This provides a bounded **non-oracle, non-neural structural original-task discovery and verification mechanism** relevant to current Q3-B, but NOT a proof of learned-unique Q3-A, general Q3/Q4, matching frontier capability or full architecture economics.

**Research decision:** HOLD additional brute-force radius increases and additional same-family three-cubes sweeps unless a new structural representation, a credible stronger specialist baseline or a genuinely different hard original family is available. Changing K after seeing first unknown results would be posthoc development, NOT a second unseen transfer. The next high-value experiment must beat same-authority specialist Direct or show learned structural discovery on true residual hard tasks.