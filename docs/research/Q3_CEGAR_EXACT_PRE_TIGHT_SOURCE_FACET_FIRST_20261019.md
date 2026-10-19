# Q3 cegar1 exact public Pre facet | Posthoc original inductive proof verified

**2026-10-19 KST · Result: DEVELOPMENT-ONLY SCOPED PASS after explicit first prospective transfer FAIL. Not independent new original family and NOT neural learning.**

## Scope integrity

The original 3-file prospective transfer preregistered in [Issue #279](https://github.com/yoonsj0305/NEUMANN/issues/279) **FAILED** in immutable first [Actions #39230552099](https://github.com/yoonsj0305/NEUMANN/actions/runs/39230552099). Old full classical portfolio reported source-only SPACER safety on `cegar1` but no explicit inductive invariant. The newly evaluated uniform grammar's candidate was inductive (initial and consecution UNSAT) yet insufficient for Post (`SAT`). That earlier FAIL stays FAIL. First log/artifact, source SHA and selection have not been altered.

After the failure, the original public `cegar1` source was examined and a specific structural gap identified: old source-only sparse octagon grammar generated candidate lower bounds from `-1,0,1` and one arbitrary valid Pre witness, missing the true finite minimum **`y-x>=-2`** entailed by actual **public** Pre `0<=x<=2, 0<=y<=2`. Original published Trans `x'=x+2, y'=y+2` preserves it, while Original Post forbids `x=4,y=0`, which that inequality excludes.

This new experiment was separately pre-registered **after** this prior failure as [Issue #281](https://github.com/yoonsj0305/NEUMANN/issues/281) and evaluated on the exact same now-OPENED source `comp/2017/Inv_Track/cegar1.sl`, SyGuS-Org/benchmarks commit `13c8deb68a873635879c9a69bc78caebd340f646`, Git blob SHA1 `5265f78e457228bfb7eef931aca690ee40f53a31`. Any success here is an engineered retrospective mechanism improvement, not evidence of blind external family generalization.

## What the new general source operator does

The proposer enumerates the same sparse one/two-variable **signed coefficients from {-1,0,1}**, using ONLY the original public Pre and Trans to build the invariant. For every linear expression `c·state`, it uses actual **Z3 Optimize** to calculate an EXACT **finite integer minimum under Pre**. An optimizer-reported bound is not accepted by fiat: a separate ordinary Z3 query must prove `Pre AND (c·state < minimum) = UNSAT` and a witness must prove `Pre AND (c·state = minimum) = SAT`. If unbounded/nonintegral/unknown, it does NOT manufacture a cutpoint. The new finite source-tight cutpoint is joined with the already frozen -1/0/1 and original Pre witness, the Pre-entailed atoms are kept, and unchanged exact inductive Houdini removes all terms refuted by true Trans counterexamples. The original Post is used **ONLY for the final original 3VC**, not to select the tight bound or guide candidate grammar.

The actual extra non-guessed integer facets included `y-x>=-2` (coefficients `[-1,1]`, threshold -2) and its signed counterpart `x-y>=-2` (coefficients `[1,-1]`, threshold -2). Both survived. Other Pre-tight candidate bounds from exact Optimize were also logged; this is not hardcoded by basename/solution.

### FIRST independent actual dev execution

- First valid actual isolated research job `q3-posthoc-pre-tight-source-original` in existing registered CI [GitHub Actions #39231785533](https://github.com/yoonsj0305/NEUMANN/actions/runs/39231785533): **JOB SUCCESS** after adding a separate research job to registered CI because newly created separate workflow did not trigger on this stacked PR. The independently executed job uploaded the complete first original receipt **BEFORE final gate**. Other CI jobs are unrelated.
- First attached artifact **#12177306016**, exact downloaded ZIP SHA256 **`426721a7bd81166e51adfc257c46bc7e683bbd253a90cebf9230b350e79de437`**, ZIP CRC PASS. Original receipt JSON exact SHA256 **`622ea80419bdb66d3f710679b3c97ea48a43058b7a22231264248c05b89f5c84`** (8240 bytes). Independently opened and checked all original evidence.
- Frozen first dev research conditions **8/8 PASS**. All 3 native original 3VCs **UNSAT** (`initial`, `consecution`, `post`), existing original SHA-bound native checker status `CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5`, and separate cvc5 **UNSAT 3/3 with exit code 0** (its log contains a harmless missing `set-logic` warning, not a rejected/unknown condition).
- **11** selected source Pre-entailed candidate facets, **2** actual counterexample pruning iterations; a correct source-tight relation survives. Old first source grammar reproduced **6** candidates and `post=SAT`, confirming new structural min-cutpoint is consequential.
- Four original verifier adversarial control candidates `TRUE`, `FALSE`, injected SMT command and wrong original source SHA all **REJECTED**; original native/custom parser original semantic parity 3/3 UNSAT, actual Pre/NotPost nonvacuous. Candidate SMT canonicalization and genuine source identity retained.

## Precise adjudication

```text
Q3_CEGAR_POSTHOC_SOURCE_PRE_TIGHT_LINEAR_BOUND_MECHANISM = DEVELOPMENT_SCOPED_PASS
Q2_REAL_ORIGINAL_3VC_Z3_AND_INDEPENDENT_CVC5 = PASS_SCOPED (1 previously opened original)
Q3_ISSUE279_FIRST_PROSPECTIVE_NEW_FAMILY_TRANSFER = FAIL_UNCHANGED (0 distinct 3VC wins)
Q3_NEW_INDEPENDENT_AUTHORED_ORIGINAL_GENERALIZATION = NOT_TESTED
Q3_LEARNED_NEURAL_UNIQUE_DISCOVERY = NOT_TESTED; this method is pure exact classical SMT
Q4_Q5_FULL_COST_AND10X = NOT_EVALUATED
Q7_FRONTIER_LEVEL_CAPABILITY_GAP = NOT_EVALUATED
HISTORICAL_FIRST_AM1 = FAIL_UNCHANGED
SEALED_D3 = BLOCKED
GLOBAL_Q1_Q7 = ALL OPEN
```

The learned transfer branch [Issue #275](https://github.com/yoonsj0305/NEUMANN/issues/275) remains retired because its shared optimizer did not actually update, and an exact classical nullspace was far cheaper. This NEW source-tight exact optimization operator is a promising **classical fallback** for a goal-insufficient inductive relation, but evaluating its generalization requires entirely new preregistered unrelated hard source originals and strong comparator/cold complete-cost accounting. **STOP further evaluation on `cegar1` or the already tested `anfp` variants.**

Evidence and code in [Draft PR #282](https://github.com/yoonsj0305/NEUMANN/pull/282), preserved as a stacked development branch, not merged to `main`.