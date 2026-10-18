# NEUMANN 1 · Q3U FIRST transition-derived affine coefficient discovery: verified bounded mechanism

Date 2026-10-18 KST. **Final scientific verdict:** `BOUNDED_CLASSICAL_STRUCTURAL_OPERATOR_DISCOVERY_PROVED`, `NEURAL_OPERATOR_INVENTION_UNPROVEN`, `GLOBAL_Q1_Q7_OPEN`.

## Frozen before first run

Preregistered method, tests, original source identities and strict success in `docs/research/Q3U_TRANSITION_NULLSPACE_FIRST_PREREG_20261018.md`, first commit `e14566361613b11e1e35b958f58b4ce312fd78da`, BEFORE actual first CI.

Actual first independent GitHub Actions [#39100514274](https://github.com/yoonsj0305/NEUMANN/actions/runs/39100514274) **SUCCESS**, immutable uploaded artifact **12126715638**. Exact source-only typed original validation, no neural inference/training. Raw first JSON SHA256 **`2efb010042f05d3a3641e6421b17724847c09387e4047eac06f81a777fa104c8`**. Git upstream originals immutable LoopInvGen `6ac90265b11431c9477dfbd33e3e3380234c0499`.

## Mechanism and theorem

Define `e(x)=c·x+k=0`, with coefficients discovered by computing exact rational nullspaces of rows constructed from finite sampled original SMT models of Pre and Trans:
- IMAGE: rows `[x_pre,1]` and `[x'_trans,1]` -> candidate `c·x+k=0`, checked **universally** by exact Z3 UNSAT for `Pre∧¬e(x)` and `Trans∧¬e(x')`.
- CONSERVATION: rows `[x_pre,1]` and `[x'_trans−x_trans,0]` -> candidate `c·x+k=0`, checked **universally** by exact Z3 UNSAT for `Pre∧¬e(x)` and `Trans∧[c·(x'−x)≠0]`.

Either route is mathematically sufficient for `e` to be inductive under ORIGINAL source semantics; no finite sample is treated as proof. All primitive integer coefficients from exact rational nullspace and gcd reduction, not from hand-entered target coefficients. The final goal theorem uses **I = all independently sound discovered equations AND original Post**, with complete original three VCs `Pre⇒I`, `I∧Trans⇒I'`, `I⇒Post` each negation UNSAT. Original Pre SAT and ¬Post SAT ensure nonvacuity. The algorithm is **not complete** over all linear invariants because finite samples/basis and two conservative proof patterns can miss invariants.

## Adversarial synthetic proof (not a real benchmark)

Original synthetic: `x0=0,y0=7,z0=3`; transition `x'=x+3y−2z, y'=y+2, z'=z+3`; safety `x>=0`. No relation coefficient label provided to generator.

**Automatic exact nullspace returns c=(0,3,-2,-15), i.e. 3y−2z=15**, on 28 source transition samples (1 feasible initial), then checks exact first-order original Pre and full transition relation. `I=(3y−2z=15) AND (x>=0)` passes all three original VCs `UNSAT/UNSAT/UNSAT`. `Post=(x>=0)` alone does NOT satisfy induction (step negation `SAT`). This is a nontrivial program-specific coefficient relation discovered from actual source transitions rather than an enumerated ±1 variable-pair grammar.

Mathematically, `3(y+2)−2(z+3)=3y−2z`; initially `3*7−2*3=15`; so `x'=x+15`, positive progress and `x>=0` preserved. This is an independently human-readable symbolic justification of the SMT proof.

**Corrupted control** changes only `z'=z+4` while holding all else. It **does not** admit the old invariant `3y−2z=15`; it finds a different conserved relation `2y−z=11` but the full original safety proof is **NOT** admitted (step original SMT SAT). In fact for the corrupted transition `y_n=7+2n`, `z_n=3+4n`, `x_n=16n−n²`, so `x_17=−17` is an explicit mathematical violation of safety. The false proof is correctly rejected.

## Actual independent original SyGuS sources (ALL preregistered before run)

| Exact original source | Source-bound discovered and original-inductive relational coefficient | Source goal solved by discovered relation + original Post | Post alone inductive? | Classical source-only SPACER |
| --- | --- | --- | --- | --- |
| `2017.ASE_FiB/fib_01.sl`, Git blob `480ddf9d1ddb0c2c3e6d2aabf6af2e38f8f26f09` | `x−y=0`, **IMAGE** relation, original candidate refutations UNSAT | **YES**, all 3 original negated VCs UNSAT | **NO** (step query SAT) | **UNSAT**, ~5.289ms |
| `2018.NeurIPS_Code2Inv/101.c.sl`, blob `a59e04c08abc9601350cd64915255253ae44517f` | none admitted | **NO new discovered relation** | **YES** | **UNSAT**, ~4.918ms |
| `others/inria-00615623_4.sl`, blob `56f60de6e81a0fa450f82efa2d7276696ed02378` | none admitted | **NO new discovered relation** | **YES** | **UNSAT**, ~5.144ms |

**Critical interpretation:** On the last two real sources the original Post itself is already inductive (all three Post-only negated VCs UNSAT), so the Q3U mechanism's `full_original_program_proven=False` just means it DID NOT PRODUCE a new verified equation; it is **not** a declaration that source safety is unprovable. All 3 real source programs were independently solved by direct strong classical Z3 SPACER. The `fib_01` equality `x=y` is mathematically relatively straightforward (two next-state equations are identical), and already expressible in the earlier hand-coded pair-comparison grammar. Thus it is source-derived real original relation discovery, NOT stronger mathematics than classical solver.

## Honest North Star decision and STOP
- **PROVED:** a reusable exact classical **source-transition coefficient constructor** and independent original symbolic soundness checker; source-derived nontrivial relations are auto discovered without target coefficients (synthetic `3y−2z=15`, real `x=y`), combined with source goal and certified with original three VCs. Corrupt transition generates neither false proof nor false old relation acceptance. Two classes of equations (IMAGE and CONSERVATION) work on genuine Z3 typed source states.
- **NOT PROVED:** that NEUMANN neural weights actually invent or predict unseen symbolic coefficient structures, that a blind external source-family distinction generalizes (three real sources previously opened), that this beats a strong classical specialist (specialist proves all three), any equal-capability full cost 10x Q4, or frontier gap Q7. Q1–Q7 all OPEN.
- **DO NOT RUN** another near-identical fixed-base grammar or small-model reranker against these opened tasks and claim Q3. Future high-value step would require a **neural variable-binding/affine coefficient constructor trained only on original source train families**, with the mathematically validated nullspace generator as STRONG CLASSICAL BASELINE, new external untouched original family, no-learning and Post-only controls, true 3VC verification and full teacher/inference/SMT cost receipts. Prior Q3F challenge originals remain sealed.

Code `research/evidence/q3u-nullspace-20261018/transition_nullspace_original_proof.py` reproducible in CI. Draft PR #210. No third-party original source bodies or invariant text redistributed in outputs.
