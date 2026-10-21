# NEUMANN 1 — Q3 finite operator vocabulary transfer and failure admission

Date: 2026-10-22 (KST). Scientific status: **SCOPED STRUCTURAL SELECTION + FAIL-CLOSED PASS; NEW PRIMITIVE / FRONTIER Q3 OPEN**.

## Official first study
PR [#438](https://github.com/yoonsj0305/NEUMANN/pull/438), GitHub Actions [39623533296](https://github.com/yoonsj0305/NEUMANN/actions/runs/39623533296) PASS.
- Synthetic original integer transition: Pre `x=1`, Trans `x'=x+k`, Post `(x-1) mod k=0`, six primes k=5,7,11,13,17,19, four seeds each.
- The model receives ONLY raw transition pairs and a **supplied operator vocabulary** `m ∈ [2,20]`, optimizes weights of a 19-category operator selector. The source goal is independently verified. No modulo *primitive* was invented.
- **24/24** fitted operators pass original Init, Consecution, Goal with both Z3 and cvc5. Mutation of source step to `k+1` is independently refuted by SAT counterexamples, **24/24**.
- Degree≤3 SINGLE POLYNOMIAL EQUALITY invariants cannot simultaneously hold at 4 reachable points and exclude actual unsafe `x=2`; each study computes exact nonzero Vandermonde determinant. This is NOT an impossibility proof for all polynomial inequality/Boolean expression programs.
- Equal-rights exact classical GCD of the SAME 50 transition samples also produces the correct operator in **24/24**. In GitHub run, total selector fit 19.918505ms vs exact GCD 0.141463ms. The latter is only candidate computation, not total end-to-end source solve. No superiority for the trained model.

## Official outside-vocabulary falsification and degraded mode
PR [#439](https://github.com/yoonsj0305/NEUMANN/pull/439), repaired GitHub Actions [39624265173](https://github.com/yoonsj0305/NEUMANN/actions/runs/39624265173) PASS.
- Same frozen model and 19-operator vocabulary, now OOD k=23,29,31,37, four repetitions each.
- **16/16** learned candidate operators FAIL the true original induction. They are not accepted: independent Z3 AND cvc5 SAT counterexamples demonstrate a real original source transition mismatch.
- An actually executed classical GCD FALLBACK generates `k` outside model's vocabulary and obtains complete independent Z3+cvc5 original safety proofs, **16/16**.
- All-source fitted+veto+fallback total observed wall 659.903179ms across 16 synthetic original programs; no matched classical-only full-system wall measured in that experiment.
- Historical initial run [39624114050](https://github.com/yoonsj0305/NEUMANN/actions/runs/39624114050) failed due missing `PYTHONPATH`. Fixed environment only, not source or trained-operator methodology; historical failure preserved.

## What these experiments prove

1. A trained **parameterized operator-family selector** can construct source-dependent nonpolynomial expressions from raw original transition data within its admitted dictionary; dual complete source proof passes for 24 tests.
2. A finite selector does NOT extrapolate outside its vocabulary. Every extrapolated safety proposal failed independent source proof (16 witnesses), and safe fallback recovered 16 task proofs with zero false SAFE admission.
3. A classical GCD solves all 40 synthetic original tasks using the same raw transition evidence and no trained primitive invention. **NEUMANN learned novelty / strongest-classical advantage was NOT shown**.
4. An exact "degree≤3 polynomial equality" lower bound helps explain why a different mathematical expression *family* is helpful, but is not a no-go theorem for full classical proof solvers.
5. The correct architecture deletes redundant model calls first, treats `learner_proposal` as untrusted, demands original semantic proof, and runs source-authenticated classical fallback. Degraded mode and original-source identity are mandatory.

## Next decisive gate (no more same-family counting)

On untouched **real**, cross-author source-body frozen programs, have a source-conditioned learned module PROPOSE a *compositional AST or auxiliary state* outside the COMPLETE frozen available grammar (not just polynomial span), and independently certify:
- explicit goal-preserving transformed original program,
- admission proof of non-representability in baseline grammar (when decidable),
- equal-rights exact/symbolic/CEGIS baselines with matched total training/search/proof costs,
- knockout of learned transformation,
- cross-family transfer and failed cases retained.

Q3/Q4/Q6 **OPEN**. No frontiers or 10× efficiency claim.
