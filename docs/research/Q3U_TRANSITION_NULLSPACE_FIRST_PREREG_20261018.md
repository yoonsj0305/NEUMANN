# Q3U: Automatically discovering source-transition affine invariant COEFFICIENTS (first experiment; frozen 2026-10-18)

## What is being tested
Previous Q3S tried a human-fixed basis of pair coefficients ±1 and neural ranking; it produced ZERO genuinely useful affine witnesses. This test replaces fixed enumerated coefficient guesses with **a rank/nullspace computation using actual transition models**. We seek program-specific integer linear equations whose coefficients are discovered automatically, then prove original source induction. This is a **classical structural discovery subroutine**, NOT a neural-invented mathematical operator; even perfect results do not close global Q3/Q4/Q7.

## Proven soundness condition (NOT proof of completeness from samples)
Candidate I(x): c·x+c0=0 from integer rational nullspace. Two sufficient admission routes:
1. **Image**: Original Pre=>I(x) and original Trans=>I(x′), all negations UNSAT. This proves induction of I.
2. **Conservation**: Original Pre=>I(x) and original Trans=>(c·x′=c·x), all negations UNSAT. This also proves induction of I.

Finite transition sampling can suggest candidates but **NEVER proves** any law; only *unbounded* exact Z3 UNSAT refutation of negated original formulas can prove the mathematics. Any SAT/UNKNOWN/timeout rejects candidate. An invariant can be nontrivial without implying the final program goal; so form I_final = conjunction(all admitted equations, ORIGINAL Post) then recheck exact original Pre=>I, I∧Trans=>I′, I=>Post all negations UNSAT. Always compare Post-only and direct source-only strong SPACER on the exact same original.

## Frozen experimental examples
- Safe synthetic mixed-linguistic source with 3 Int states and **one hidden affine relation**: Pre=(x=0,y=5,z=3), Trans=(x′=x+y-z, y′=y+1, z′=z+1), Post=(x>=0). No coefficient manually supplied to generator. Post-alone NOT inductive; a provable discovered relation must have >=2 variables and nonzero offset, and full original three VCs must be UNSAT. This checks genuinely constructive coefficient discovery beyond human ±1 pair candidate list.
- Deliberately corrupt transition z′=z+2; the old candidate y-z=2 must NOT pass original induction, and corrupted program must not falsely be certified safe.
- Three pinned **real** original SyGuS-INV programs from already-opened origin groups (this is engineering/development validation, NOT blind learning):
  1. `benchmarks/LIA/2017.ASE_FiB/fib_01.sl`, original git blob `480ddf9d1ddb0c2c3e6d2aabf6af2e38f8f26f09`.
  2. `benchmarks/LIA/2018.NeurIPS_Code2Inv/101.c.sl`, original blob `a59e04c08abc9601350cd64915255253ae44517f`.
  3. `benchmarks/LIA/others/inria-00615623_4.sl`, original blob `56f60de6e81a0fa450f82efa2d7276696ed02378`.
- Repo `SaswatPadhi/LoopInvGen` pinned immutable SHA `6ac90265b11431c9477dfbd33e3e3380234c0499` and source license metadata Git blob `1e853cd500e1317b7c2ad0a2514b548c32c46f5e`. No original benchmark code or generated formula text copied into public receipt.

## Frozen algorithm
For N current original Int state variables collect at most 28 distinct SMT models of original Pre and 28 distinct SMT models of original Trans; sample both current and next values but block DISTINCT complete state pair per sample. Build exact rational matrices:
- **Image relation** nullspace of rows `[pre_current...,1]` plus `[trans_next...,1]`.
- **Conservation relation** nullspace of rows `[pre_current...,1]` plus `[(trans_next−trans_current)...,0]`.
Check EVERY candidate basis vector against exact original Pre and Trans (as specified above), reject tautological/allzero and non-integer/too-large coefficients; primitive integer coefficients via gcd and sign canonicalization. Validate original formula with direct same-source Z3 3VC. No synthesized target answer or solver invariant supplied as input.
- Freeze 28 samples/model type, max state arity 12, max absolute normalized coefficient 100000, max full original VC timeout 2.5s/VC, sample SMT 2s/request, up to 8 basis candidates/type, max 3 original test sources. No neural training, no Q3F heldout source reads.
- Count individual sound relational discoveries with >=2 nonzero state coefficients and separately full program safety proofs. Strong classical SPACER with 2s per original, and Post-only independent three VCs. Preserve zero outcomes and unsupported originals; no code/parameter retuning after seeing first outcome. A self-contained script should test synthetic controls and original benchmarks in same run.

## Admission
**Bounded mathematical subgoal PASS** only if algorithm, without hard-coded hidden coefficients, derives >=1 relational coefficient witness that passes exact original Pre and Trans induction, passes original full Pre/Trans/Post program theorem with the source goal, while Post-alone fails, with the false/corrupted control correctly blocked. For real-source example success, separately require original unmodified Pre/Trans/Post full 3VC, and mark if relation also appears in source (not novel mathematically). CPU and SMT costs, original classical baseline reported. This is a construction/certification proof for a narrow hybrid structural operator; **not** autonomous neural invention Q3, nor 10x Q4 nor frontier Q7. All global Q1–Q7 OPEN.
