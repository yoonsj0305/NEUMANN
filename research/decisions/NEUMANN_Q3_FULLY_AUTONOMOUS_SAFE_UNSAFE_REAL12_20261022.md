# NEUMANN 1 | Autonomous original-source SAFE/UNSAFE decision on 12 published programs

2026-10-22 KST. **Verified scoped scientific result**: 12/12 genuinely original, correctly authenticated source programs classified with **no human winning invariant or prewritten UNSAFE counterexample as algorithm input**; complete source certificates separately checked by Z3 and checksum-pinned cvc5. This is a **POSTHOC** cohort where original source bodies were previously read in this research; no first-blind, neural-unique, frontier, or 10x claim.

## Reproduced official independent evidence

- GitHub [PR #453](https://github.com/yoonsj0305/NEUMANN/pull/453), separate from earlier [PR #452](https://github.com/yoonsj0305/NEUMANN/pull/452); research branches are **not merged** into default main.
- Official final run [39712926246](https://github.com/yoonsj0305/NEUMANN/actions/runs/39712926246) = **SUCCESS**, commit `f4a7b5e09e4d644112b6a336a8b4a598e9522ff5`.
- Official Action artifact #12397831910: byte size 12,151; ZIP SHA256 `084c27980e03d84e80c7c944df2006357a0cb971a519ae24d647466f5abaaa86`; CRC and JSON claims separately checked.
- Previous independently certified 12-source ground truth: run #39709811720 and #39711864365; independent Z3 + cvc5. Original published source commit `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646`. Historic first registered `fib_11.sl` SHA was mistaken and corrected **posthoc**, never represented as successful first-blind.

## Actual mechanism, without oracle labels

1. Fetch all 12 source files from the fixed external repository. Check original raw Git blob SHA1 and byte size. The *algorithm input register contains only filename, path, expected git SHA, size*. No target invariant, labels, or manual UNSAFE witness.
2. For each original program, run source-bound bounded reachability: `Pre(s) AND NOT Post(s)` (depth0) and `Pre(s) AND Trans(s,s') AND NOT Post(s')` (depth1). Independently Z3 and cvc5 must agree. If SAT, obtain ALL state assignments through solver get-value and re-check the completely grounded source Pre/Trans/NotPost in BOTH SMT solvers. Only then authorize `UNSAFE`. If no such witness, return `NO_SHORT_WITNESS`, **never SAFE**.
3. For the **one** actually UNSAFE source `fib_07.sl`, the controller itself recovered exact states `i=0,n=1,a=0,b=0 -> i'=1,n'=0,a'=1,b'=2` with Z3 and cvc5. No human-known trace was supplied. Because next-state `n'` is unrestricted in one authentic source branch, the actual Post fails. The model is never allowed to certify SAFE there.
4. For the remaining eleven source programs, compute exact source-conditioned affine conservation from original Pre linear equalities and all original transitions using rational kernel `C Mᵀ α=0`. Split by actual source syntactic guards where relevant; emit conditional conservation AST and signed small relational inequalities. Run exact Houdini fixed-point removal. Every accepted candidate must satisfy **the original complete Init, Consecution, Goal** SMT unsatisfiability independently on two backends, before a SAFE verdict.
5. For all 11 SAFE originals, independent checker accepted 33/33 exact original three-VC formulas **in Z3 and in cvc5**. 22 negative controls correctly returned SAT in both. Source SHA verified for all eleven, no unsupported or UNKNOWN. Entire 12-case input denominator preserved.

## Actual receipt summary, not expectation

| Measure | Actual result |
|---|---:|
| Authentic original program identities | 12/12 |
| Source-only model-generated SAFE, independently dual 3VC proved | **11/11 actual SAFE** |
| Automatically found dual-proved original reachable UNSAFE | **1/1 actual UNSAFE** |
| Full original status known correctly in this set | **12/12** |
| Wrong certified SAFE | **0** |
| Human-provided winning invariant or concrete UNSAFE trace | **0** |
| Real neural forwards and GPU operations | **0** |
| BMC original Z3 / cvc5 queries | 24 / 24 |
| Concrete witness original Z3 / cvc5 rechecks | 1 / 1 |
| SAFE 3VC unsat in BOTH independent solvers | 33/33 each |
| SAFE checker negative controls SAT in BOTH solvers | 22/22 each |
| Independent SAFE checker total queries Z3 / cvc5 | 55 / 55 |
| BMC source query stage wall | 1.46058 s |
| Eleven-safe automatic source proposer wall | 1.5362 s |
| Independently authored 11-source dual checker wall | 0.850 s |

Step time sum ≈3.847 s, excluding installations, downloads, general deployment cold-start and full cost; this was one unpaired CI run and does NOT prove a 10x advantage, or even statistically reliable speedup. The controller's early grounded UNSAFE gate saved needlessly asking the stronger source-invariant generator to prove an impossible property, but has its own cost.

## Structural mathematics and the learning limitation

For the previously unproved source `fib_13.sl`, no nontrivial *unconditional affine equality* can hold every original Pre state and be inductive across both source transition modes: Pre has `j=2,k=0` with unconstrained t, and modes have increments `(4,0,0)` and `(2,1,0)`. Therefore any unconditional `a j+b k+c t=d` invariant forces c=0, 4a=0, 2a+b=0, and a=b=0. In contrast the program supplies guards; the exact no-neural algebraic constructor generates `t=0 => k=0` and `t≠0 => j-2k=2`, and the complete original independent dual 3VC certifies their sufficiency (with the appropriate additional source-derived bounds if needed). This is a *scoped class barrier*, not a universal impossibility or newly invented mathematical operator.

The research project has, within this benchmark cohort, demonstrated an executable proof-carrying **source-to-structure-to-verified-truth** pipeline rather than only manual proofs. However all the underlying algorithms in the successful run are classical (exact linear algebra, SMT bounded model checking, Houdini), and the original 12 program cohort was already exposed. Prior genuinely learned source policy #450 solved 7/12, tied random order at 7/12 on its first recorded setup, and never beat strong exact classical on verified unique solved tasks. **Learned neural-specific structural invention, independent authorship blind generalization, global Q3/Q4/Q6/Q7 and frontier/10× efficiency remain OPEN.** Calling these closed would misattribute the real result.

## Architectural admission decision

Use exact source integrity → cheap bounded UNSAFE search (SAT only is authoritative if grounded and independently checked) → cheap direct Post 3VC where possible → exact source affine/guarded structural generation and fixed-point pruning → independent complete dual original safety proofs → explicit UNKNOWN/ABSTAIN on any missing proof. No text narrative can confer proof authority. Avoid any mandatory learned stage in a workload fully solved by these exact non-neural methods. Next high-value neural-exclusive test must use genuinely new independent original families with baseline headroom, pretrained weights frozen before source exposure, model-proposed typed novel operator beyond supplied grammar, and budget-matched exact classical controls.