# NEUMANN 1 | G0 integer Newton lifting on exact original Hoenicke QF_NIA (2026-10-18)

## Verdict: FOUR genuine source-verified UNSAT proofs; THREE specific two-solver nonanswers at 3-second bound; GLOBAL Q1–Q7 remain OPEN

**Mathematical result (closed in a narrow development-only scope):** On ALL 27 opened original `SMT-LIB/benchmark-submission-2023/non-incremental/QF_NIA/20230328-sqrtmodinv-hoenicke` source programs frozen at Git `7f993a017850ba547c6ea19a1bf3b54adf54a449`, a single classically valid integer-polynomial modular lifting mechanism certified **4/27 exact original UNSAT**. Twenty-three original programs yielded `NO_SOUND_INTEGER_POLYNOMIAL_CERTIFICATE` (not SAT nor unsatisfiability proof). The previous unchanged fixed `not mod P(y) =0` residue matcher genuinely failed 0/27 on the same source originals ([Issue #221](https://github.com/yoonsj0305/NEUMANN/issues/221)). This new program is a DISTINCT preregistered theorem-proving mechanism, but it was designed AFTER the source family was opened, so it is **development only**, not evidence of prospective Q3/Q6 neural generalization.

## Universal algebraic proof

For all integers a,u,s with s>1, define `e = a*u-1`, `u2 = u*(2-a*u)`. In the integer polynomial ring:
`a*u2-1 = a*u*(2-a*u)-1 = -(a*u-1)^2 = -e^2`.
If the **original necessary premise** is `(a*u mod s)=1`, then `e=s*k` for some integer k. Consequently `a*u2-1=-s^2*k^2`, and because `s^2>1`, the *exact SMT-LIB integer mod* value `a*u2 mod s^2` is 1. If an original required top-level conjunct says `not (a*u2 mod s^2 =1)`, the source formula is UNSAT.
The same conclusion holds if an original necessary integer-polynomial equality gives `a*u=1+k*s`, or more generally the exact compiler-style source equality and source-variable definitions prove `E-1=M*q` with **q an integer-coefficient polynomial**, and original source guard proves `M>1`. NO rational quotient is admissible.

**Actual exact original cases:**
- `modInvStep.smt2`: **UNSAT**, source's `(a*u mod s)=1` and source's `u2 = u(2-a*u)` imply squared error. Integer coefficient quotient `-1`.
- `modInvVar1.smt2`: **UNSAT**, source's `a*u=1+k*s` and same source Newton update imply squared error. Integer coefficient quotient `-1`.
- `modInvStepSimplified.smt2`: **UNSAT**, original `a*u2=1-k^2*s^2`; direct quotient `-k^2`.
- `modSimpleTest.smt2`: **UNSAT**, original direct expression `1+k*s`; quotient `k`. **This is a trivial existing-classical solved control**, not novel improvement.
All 4 proofs use the complete unmodified actual original source assertions, source SHA256 and original independent Z3 parser; the program adds only the previously mathematically proven lemma `E mod M=1` and observes the contradiction for each original. The **soundness** of the inserted lemma derives from an exact SymPy `ZZ[variables]` polynomial division/reexpansion and necessary source premises, not from trusting the additional Z3 assumption.

## First-run proof and failure preservation

- Preregistered method + original 27 before new study in [GitHub Issue #222](https://github.com/yoonsj0305/NEUMANN/issues/222).
- First CI [#39117884954](https://github.com/yoonsj0305/NEUMANN/actions/runs/39117884954) failed due only to SymPy `GeneratorsNeeded` for source integer constant with no symbolic generator. The [issue prereg fix comment](https://github.com/yoonsj0305/NEUMANN/issues/222) fixed **only** generator-free literal integer checking; mathematical criteria and all original task IDs unchanged.
- First successful CI [#39117957178](https://github.com/yoonsj0305/NEUMANN/actions/runs/39117957178), immutable [artifact #12132652822](https://github.com/yoonsj0305/NEUMANN/actions/runs/39117957178/artifacts/12132652822), ZIP SHA256 `1d686e46f05c499a705ceff25a388c1a4dabf76055a9b9b2bc5203e294fdece4`. Individual four original certificate proof+original-parser/check wall on runner **0.009998 / 0.004848 / 0.007256 / 0.002969 seconds** (associated with modInvStep / Simplified / Var1 / SimpleTest respectively). Full 27-file Python proof + network originals and interpreter = **4.780s** in that CI, not per-case wall; source downloading/environment and CI activation remain separate.
- Executable: `research/evidence/g0-newton-hoenicke27/one_shot_integer_polynomial_proof.py`. This remains one **hand-crafted classical** algorithm and does NOT establish that NEUMANN learned it.

## Direct matched source-identity ordinary-classical falsification

A second preregistered [Issue #222 comment #6248594040](https://github.com/yoonsj0305/NEUMANN/issues/222) froze **all same 27 originals** (not four successes only) for Z3 and cvc5, each external subprocess `<=3s` per case on GitHub Ubuntu CPU. Historical original source names and exact raw source SHA identities matched. [Actions SUCCESS #39118193242](https://github.com/yoonsj0305/NEUMANN/actions/runs/39118193242), [first artifact #12133256426](https://github.com/yoonsj0305/NEUMANN/actions/runs/39118193242/artifacts/12133256426) ZIP SHA256 `a94555f1760f2bd8e9e4228f009662baf9110d3c0e43f3b337f13590e603ead3`:
- Z3 Python package **4.15.4**: 17/27 returns `unsat`, 10/27 `unknown`, wall sum **29.823s** (27 cold invocations).
- cvc5 native **1.1.2**: 2/27 returns `unsat`, 2 external wall-timeouts, 23 return `OUTPUT_ERROR` (typically process exit 134 under the internal time limit; **do not call them valid mathematical unknown or proofs**); wall sum **74.463s**.
- Among the already four **source-certified** development cases, **`modInvStep`, `modInvVar1`, `modInvStepSimplified`** each: Z3 `unknown` (~2.78s) and cvc5 timed-out/no-usable-claim (~2.9–3.0s), while structural math original proof exists. `modSimpleTest` solved immediately by Z3 (0.1116s) and cvc5 (0.0245s); it MUST NOT be touted as headroom.
- The literal times are *distinct GitHub Actions jobs, possibly not identical CPU SKUs*, with different interpreter start and data-download amortizations. Do not take `2.78/0.01` as a certified N× operational speedup. A timed-out classical method gives no actual correct-answer latency denominator and the strongest available optimized specialist solver portfolio was not tested.

## FAST-CLOSE scientific gate

| Gate | Verdict |
|---|---|
| Exact mathematically verifiable classic-style source UNSAT on opened 2023 origin | **4/27 PASS** |
| Earlier original narrow residue matcher transfer | **0/27 FAIL preserved** |
| Conditional target mathematical Newton squaring lemma | **Universal PASS** |
| Under frozen <=3s, Z3/cvc5 two-tool nonanswer on three of these four | **3/4 observed limited** |
| Novel neural autonomous semantic relation discovery | **NOT TESTED / G1 HOLD** |
| Prospective blind, separate ORIGINAL source-family transfer | **NOT TESTED for new mechanism** |
| Strongest classical specialist *all-in* cost win vs verified oracle reframe | **OPEN / NOT ADMITTED** |
| G2 authentic frontier-small provider gap | **BLOCKED** |
| Global NEUMANN questions Q1–Q7 | **OPEN** |

**Stop after these source-opened experiments.** Do not retroactively mark the 27 as blind validation, claim global Q3/Q4 PASS, claim 10x cheaper, or start neural/GPU training. Any future decisive evaluation needs a new untouched source lineage, a frozen algorithm before source viewing, independent proof checker, strong specialist portfolio and total elapsed/CPU/RAM accounting. No PR created, model training and paid model calls ZERO.
