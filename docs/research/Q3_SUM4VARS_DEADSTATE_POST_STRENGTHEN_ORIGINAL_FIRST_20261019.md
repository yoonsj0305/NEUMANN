# NEUMANN 1 Q3 | Authentic sum4_vars six-state source → three live states and inductive source-bound original proof

**2026-10-19 KST. Result: 11/11 first preregistered POSTHOC DEVELOPMENT conditions PASS.**

## Explicit scientific limitation

This is NOT a clean blind evaluation of new independent sources. The earlier [Issue #283](https://github.com/yoonsj0305/NEUMANN/issues/283) prospectively froze three unseen metadata-selected original SyGuS files and then actual first [GitHub Actions #39234827646](https://github.com/yoonsj0305/NEUMANN/actions/runs/39234827646) **FAILED** with zero added original inductive certificates beyond the strong full classical baseline. On first inspection of failed original `comp/2017/Inv_Track/sum4_vars.sl`, the new solver exceeded its 5-variable grammar cap. After viewing the actual source and finding symbolically unused variables, we separately preregistered **one-source posthoc development** [Issue #285](https://github.com/yoonsj0305/NEUMANN/issues/285), not a do-over of the blind test. Preserve Issue #283 FIRST FAIL forever.

## True original program and strong baseline

- Authentic original: [official SyGuS sum4_vars.sl](https://github.com/SyGuS-Org/benchmarks/blob/13c8deb68a873635879c9a69bc78caebd340f646/comp/2017/Inv_Track/sum4_vars.sl). Upstream frozen Git commit `13c8deb68a873635879c9a69bc78caebd340f646`, registered Git blob SHA1 `ba2a948d21a8b64a6ede2a441448118736792172`, independently verified source SHA256 `a83425aba1eaac9e8af569107c2eac2ddc10748e58aeb58d41a69a35425ef058`.
- Six original integer state dimensions `i`, `sn`, `size`, `v1`, `v2`, `v3`. Public source Pre: `sn=0, i=1`; Trans: `size'=size, i'=i+1, sn'=sn+1` while `i<=size`; Post: `i<=size OR sn=size OR sn=0`.
- Old immutable **full classical source portfolio**: `ORIGINAL_SOURCE_ONLY_SPACER_UNSAT`, meaning safety only, **no explicit inductive 3VC invariant**. Earlier Pre-tight sparse candidate generator failed before trying invariant synthesis (`UNSUPPORTED_ORIGINAL_STATE_DIMENSION`), because its 5-state cap was exceeded.

## New mathematical mechanism, and why it is sound

1. **AST-based dead-state deletion:** inspect the *actual Z3 expressions* of original Pre, Trans and Post and collect referenced current and next-state symbols. Three state pairs `v1/v2/v3` and their primed counterparts are absent from **ALL three relations**, so these can be ignored *during candidate generation* without changing the meaning of the actual source requirements. The generated candidate depends on three live states, and the **final original checker still evaluates the full unprojected six-state Pre/Trans/Post**. This is exact syntactic liveness, NOT a potentially unsound heuristic or unverified existential projection.
2. **Existing source-only invariant discovery unchanged:** run the previously developed fixed Pre-tight sparse signed-inequality generator (Z3 Optimize exact finite minimum under public Pre plus separate entailment/attainment check), followed by original Trans counterexample-guided Houdini. The original published Post is not read by the **cutpoint optimizer or pruning**. Actual two CEGIS elimination steps occurred, and nontrivial signed two-variable atoms survived.
3. Extracted useful invariant: **`i - sn = 1`**, logically forced by surviving `i-sn >=1` and `sn-i >=-1`. This source-only relation is actually inductive (`initial=UNSAT`, `consecution=UNSAT`) but fails the goal implication (`post=SAT`), so **the source-only relation must NOT be called a complete original proof**.
4. **Strengthen only AFTER the source-only structure freezes:** let `I := R ∧ OriginalPost` and prove the three actual original obligations against the entire source, not the reduced abstract program. The original `Post` alone is NOT inductive, but **`R ∧ Post` is inductive**, thanks to the relationship between the loop bound and the synchronized `i` / `sn` increments. This is a legitimate source-goal-conditioned inductive strengthening, not a concealed hardcoded solution.
5. Canonicalize SMT2 and require `XOR(raw,canonical)=UNSAT` before sending to existing source-hash-bound independently parsing original checker. Native Z3 original Pre→I, I+Trans→I', I→Post **UNSAT 3/3**, independent standalone `cvc5` exact original bad queries **UNSAT 3/3** with exit code 0. The real source parser native/custom semantic parity 3/3 UNSAT and Pre/NotPost nonvacuity passed. Wrong `true`, `false`, forged source SHA and disallowed SMT command rejected **4/4**.

## First execution and verified archive

- FIRST actual independent bounded GitHub CI job `q3-sum4vars-deadstate-3vc-posthoc-first` in [Actions #39235933225](https://github.com/yoonsj0305/NEUMANN/actions/runs/39235933225): **JOB SUCCESS, 11/11 frozen development conditions PASS**. This was a separate job embedded in the normal CI workflow. Other unrelated CI jobs do not define this research outcome.
- First artifact ID `12179646131` downloaded from GitHub and independently checked: ZIP SHA256 **`b3bd2f471a4836967b897e05bfff6eb10ac898c0d7757ff270381cd520da61d8`**, ZIP CRC PASS, 3,172 bytes.
- Raw first original JSON SHA256 **`e0ea34bb3a3bf4108fbc087d3b89e867775fc21ad0d1751a116b34f3e795491c`**, 10,587 bytes. Original source digest, AST live/dropped coordinate pairs, 3VC bad query results, separate cvc5 statuses and negative controls, 2 real pruning iterations and first gate booleans inspected.
- Source-only reduced-state-search wall reported `97.411 ms`, whole measured Python study wall `307.455 ms` on CI CPU. **No iso-capability all-in cost, energy, dollars or frontier efficiency comparison**: the old source SPACER method did not export an explicit invariant and is not an equal-capability baseline for direct 3VC output.

## Exact scientific verdict

```text
Q3_SUM4VARS_EXACT_DEAD_STATE_LIVENESS = POSTHOC_DEV_SCOPED_PASS (6 -> 3)
Q3_REAL_PRETRANS_SOURCE_INVARIANT_R = POSTHOC_DEV_SCOPED_PASS (i-sn=1; initial+consecution only)
Q3_R_AND_ORIGINAL_POST_FULL_SOURCE_INDUCTIVE = POSTHOC_DEV_SCOPED_PASS (original Z3 3/3)
Q2_ORIGINAL_SHA_BOUND_INDEPENDENT_CVC5 = POSTHOC_DEV_SCOPED_PASS (cvc5 3/3)
Q3_STRONG_CLASSICAL_PRIOR_EXPLICIT_3VC = ABSENT (source-only SPACER safety)
Q3_ISSUE283_FIRST_BLIND_THREE_SOURCE_TRANSFER = FAIL_UNCHANGED
Q3_TRUE_NEW_INDEPENDENT_AUTHOR_ORIGINAL_FAMILIES = UNPROVEN
Q3_NEURAL_NEW_MATH_OPERATOR_OR_CAUSAL_STRONGER_THAN_CLASSICAL = NOT_EVALUATED (pure classical)
Q4_Q5_FULL_COMPUTE_DOLLARS_ENERGY_10X = NOT_EVALUATED
Q7_FRONTIER_CAPABILITY_GAP = NOT_EVALUATED
HISTORICAL_FIRST_AM1 = FAIL_UNCHANGED
SEALED_D3 = BLOCKED
GLOBAL_Q1_Q7 = OPEN
```

**STOP** repeating the opened `sum4_vars` case. The new **generic AST dead-state projection plus post-strengthened source-only relation** should be treated as a candidate engineering operator; only a **subsequent preregistered untouched original** from a source-independent family, plus strong full classical comparisons and complete expense, could demonstrate transfer generalization or resource superiority. On tasks where a strong exact classical specialist provides the same proof more economically, obey NEUMANN’s North Star and delete unnecessary neural computation.

Code and raw evidence: [Draft PR #286](https://github.com/yoonsj0305/NEUMANN/pull/286), source-first registration [Issue #285](https://github.com/yoonsj0305/NEUMANN/issues/285).