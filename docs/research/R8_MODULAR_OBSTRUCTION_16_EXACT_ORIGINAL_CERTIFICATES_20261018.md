# NEUMANN 1 · R8 · Exact original modular obstruction proves 16/16 2022 MathProblems UNSAT
**2026-10-18 KST. This is a real, reproducible classical structural proof result with a source-body-unseen same-generator next-eight holdout. It is NOT learned NEUMANN frontier intelligence or proof of a novel number-theoretic theorem.**

## What was proven and what was NOT

After R7's completely frozen original Hoenicke-derived `not (= (mod E M) 1)` detection found **0/8** original 2022 MathProblems UNSAT proofs, the researcher inspected exactly three of the already opened first eight original `STC_0013`, `STC_0058`, `STC_0095` after that failure. Their true original required formulas were `x^3+y^3+z^3=n`. This suggested **a DIFFERENT, already well-known number-theoretic obstruction**: every integer cube is 0, 1 or 8 modulo 9. A sum of three cubes can never equal a number congruent to 4 or 5 modulo 9.

The researcher preregistered [Issue #231](https://github.com/yoonsj0305/NEUMANN/issues/231) **before modifying or reading the next eight selected original source bodies**, and froze ONE generic polynomial proof algorithm not conditioned on source filenames, values, 3-cube shape, source expected status, or gold labels. On original byte-preserved source SMT-LIB from `SMT-LIB/benchmark-submission-2022` commit `81a39628827f61fbd74c6f3e67feb5c1b740d2f0` `non-incremental/QF_NIA/20220315-MathProblems`, it now **automatically proves original UNSAT for all first eight already-opened DEV cases and all NEXT EIGHT source-body-UNSEEN HOLDOUT cases, 16/16 independently verified mathematical certificates**.

Because ALL 16 selected belong to **the same manually discovered 2022 `Sum of three cubes` generator/source family**, this is **within-family source-body generalization**, NOT cross-generator or cross-mathematical-domain generalization. The 2026 official source status `unsat` was used ONLY to select the originals before source text access and was NEVER treated as a proof or given to the algorithm. The empirical improvement measures a classically known number-theoretic obstruction against two general-purpose solvers under **3-second caps**, NOT a novel architecture defeating optimized number theory.

## The sound source-general proof mechanism

1. Parse original exact SMT-LIB with the real Z3 original reader, preserving all original assertions. Unroll ONLY top-level original required AND conjuncts, never choose a formula under OR/implication or invented assumption.
2. Find any original *necessary asserted integer polynomial equality* `lhs=rhs`. Accept only Z3 AST integer constants, uninterpreted integer variables, addition, multiplication, subtraction, unary minus and bounded nonnegative integer powers. Any unrecognized original expression must fail closed as unsupported, NOT be approximated.
3. For deterministic moduli m=2 through 12, if at most 4 free integer variables and m^n<=50,000, enumerate EVERY assignment of original integer variables to 0..m-1. Evaluate `lhs-rhs mod m` with exact integer modular arithmetic. If **zero never appears**, the necessary original equality is impossible over ALL integers, since each integer assignment necessarily induces one enumerated residue tuple. Therefore full original source is UNSAT. The engine makes no SAT judgments.
4. The returned per-original certificate includes source SHA256, **original necessary SMT AST sexpr**, variable list, modulus, complete reachable difference residues (zero excluded), number of enumerated residue tuples, and exact original assertion count. A **separately implemented SymPy `ZZ[variables]` integer-polynomial interpreter + full residue enumeration** independently rechecks every residue and rejects any mismatch or occurrence of zero. No expensive full-original Z3 refutation is needed for soundness because the finite modular impossibility is a mathematically complete contradiction with a necessary original asserted equality.
5. The **proof code was frozen BEFORE all eight holdout original source files were fetched**, with Git commit `17c127dde4b477edf0a93ca041ae53150dc97e93`, exact Git blob SHA1 `e6e8682bbc87def7921d13954331e1ab66ac9267`, downloaded and SHA1 checked by first runner before benchmark. No between-development-and-holdout tuning.

For the particular 16 original STC required formulas, the algorithm discovers **m=9 automatically** (rather than a handcoded modulus-9 test). For every case, it exhaustively enumerates **9^3=729** residue assignments; the independent polynomial verifier reproduces the exact attainable difference residues. All 16 sources are mathematically impossible by the known residue obstruction.

## Official dataset provenance, fixed input selection

Preregistered exact official `SMT-COMP/smt-comp.github.io` Git SHA `cd15cbedd4ef312d615448100797a80e922cf575`, `benchmarks-2026.json.gz` SHA256 `ba855e47e1ed88e2e6bb26272e84a20a0e8f0c320adc704b062f4c287e586a54` and `results-sq-2026.json.gz` SHA256 `7abe5cadf800cc84db00506f85176378f714cdaa8c02a0e491059835f5039c58`. Source family exact `QF_NIA/20220315-MathProblems`. The official original reference contains **1,100** tasks: 822 SAT, 232 UNSAT, 46 UNKNOWN. Exactly **27** original tasks meet official `status unsat` + >=1 2026 SingleQuery participating solver `unsat` + zero conflicting SAT returns. Select alphabetically FIRST 8 (already R7 opened) and NEXT 8 **without opening raw source bodies before code freeze**.

**Already-opened first eight DEV:** `STC_0013`, `STC_0058`, `STC_0095`, `STC_0139`, `STC_0185`, `STC_0238`, `STC_0284`, `STC_0292` (each `.smt2`).

**Next-eight source-body-unseen at freeze:** `STC_0382`, `STC_0428`, `STC_0437`, `STC_0644`, `STC_0652`, `STC_0671`, `STC_0698`, `STC_0707` (each `.smt2`). All 16 original source SHA256 distinct and official original logic QF_NIA.

All eight holdout files were fed to precisely the same generic algorithm **before any holdout source-dependent edits**, no per-case failure tuning or prompt mutations.

## First execution and independent artifact audit

- [First SUCCESS Github Actions #39130417694](https://github.com/yoonsj0305/NEUMANN/actions/runs/39130417694), one free GitHub Ubuntu CPU worker, 16 original files, Z3 4.15.4 and native cvc5 baseline each newly cold-started with ~2.7s inner / max 3s external original bound, general modular proof tool as a separate cold subprocess. Exact original file order alternated deterministically among comparator/proof arms based only on frozen list index, no gold-result-driven order.
- [Complete first-run ZIP artifact #12137797624](https://github.com/yoonsj0305/NEUMANN/actions/runs/39130417694/artifacts/12137797624), independently downloaded, **SHA256 `ad493ea74c6ab68f364e145e4709b5d93e1c9badf6cac7e61a2d3cf008d1337f`**, ZIP raw JSON `neumann_r8_math2022_first_evidence.json` opened and each original source and certificate inspected.
- Exactly **16/16 `INDEPENDENT_ORIGINAL_UNSAT_MODULAR_CERTIFICATE`** (8/8 DEV + 8/8 source-body-unseen HOLDOUT), no witness missing, for EACH m=9, n=3, 729 enumerated residue tuples with independently identical reachable residue sets lacking zero. The original full original AST equality for every cert was inspected, and all were `x*x*x+y*y*y+z*z*z=n` with original integer n congruent to 4 or 5 mod9.
- Z3 original **0/16 UNSAT decisions** under 3s; cvc5 original **0/16 usable UNSAT decisions** under 3s (do not call such time-capped nonanswers absolute unsolvability). The 2026 official results dataset DID contain an external competitor's UNSAT result for each selected case, so the result does **NOT** mean the whole competition failed on them.
- All 16 new original certificate source hashes differ. No GPU, neural forwards, model training, paid API or PR.

### Time accounting: entire cohort one same CPU first run

| Arm | DEV first 8 cold wall | Source-body-unseen holdout next 8 wall | All 16 wall | Original source-certified mathematical UNSAT |
|---|---:|---:|---:|---:|
| Z3 4.15.4, 3s outer | **22.079426s** | **22.080456s** | **44.159882s** | **0 (no answer under cap)** |
| Native cvc5, 3s outer | **23.555650s** | **23.429974s** | **46.985624s** | **0 (no answer under cap)** |
| New exact modular certificate solver | **2.698433s** | **2.455883s** | **5.154316s** cold processes plus **0.175720s** pinned source fetch = **5.330036s** | **16/16** |

**Do not claim a true `8.3x` time-to-correct-answer speedup over these baseline solvers**: both baseline solvers produce zero correct UNSAT answers under the 3s cap, so no finite correct-answer latency ratio can be computed. The numbers instead show bounded comparison: new prover delivers all 16 correct, at ~5.3s counted runtime, whereas Z3/cvc5 consumed ~44/47s allocated original budget without correct UNSAT returns. The competition's stronger solver already claims original UNSAT, and trivial optimized `cube mod 9`/modular arithmetic is a much stronger relevant classical specialized baseline that was NOT benchmarked here. This simple classical obstruction may beat this generic parser + SymPy approach in speed and energy by a large amount; NEUMANN has not established headroom versus it.

## Exact scientific CLOSE status

- `R8_GENERIC_CLASSICAL_MODULAR_UNSAT_ORIGINAL_FIRST8_DEV = PASS / CLOSE`: **8/8 independently source-mathematically verified**.
- `R8_GENERIC_CLASSICAL_MODULAR_UNSAT_SOURCE_BODY_UNSEEN_NEXT8_HOLDOUT = PASS / CLOSE`: **8/8** with frozen algorithm, *within the same three-cube source/generator family*.
- `R7_FROZEN_OLD_NEWTON_SOURCE_TRANSFER = FAIL / CLOSE`: unchanged, historical 0/8 original; R8 new classical theorem doesn't revise historical R7.
- `G0_FULL_PROSPECTIVE_ACROSS_DIFFERENT_GENERATORS_STRONGEST_CLASSICAL = OPEN/NOT_ADMITTED`.
- `G1_NEURAL_AUTONOMOUS_STRUCTURAL_INVENTION = HOLD/UNPROVEN`. This modular theorem was **human identified after viewing three DEV originals**, not learned by NEUMANN, and algorithm itself is deterministic classical mathematics.
- `G2_FRONTIER_PARITY_MINIMUM_TOTAL_COMPUTE = BLOCKED/UNPROVEN`, global **Q1–Q7 ALL OPEN**. No frontier throughput, GPU/joule, base-model parameter or learned cost comparator.
- Source-body holdout first eight belongs to one historically public generator, so these results do not guarantee domain generality. No confidence interval from a single original group and one timing run.
- **STOP R8 exactly as preregistered.** Do not tune this run after holdout reveals 16 successes. Any next scientific study must compare against the **appropriate specialized modular mathematics** (not just Z3 3s) and examine genuinely different algebraic source generators / learned discovery with fresh prenamed holdouts. This R8 result is a valuable, correctly bounded classical semantic proof result, not the endpoint of NEUMANN's grand claim.

Full original code: [general exact modular arithmetic + independent checker](https://github.com/yoonsj0305/NEUMANN/blob/research/r8-modular-obstruction-2022-16-20261018/research/evidence/r8-modular-obstruction/exact_polynomial_remainder_certificate.py) and [first 16 original source frozen test driver](https://github.com/yoonsj0305/NEUMANN/blob/research/r8-modular-obstruction-2022-16-20261018/research/evidence/r8-modular-obstruction/first16_math2022_dev_plus_holdout.py).
