# NEUMANN Q3: fixed 17-probe information impossibility gate (2026-10-17)

**Registered BEFORE constructing or running the two new exact source texts.** This is a *synthetic counterexample*, not a clean holdout and not a solution to global Q3. This directly attacks an architectural assumption rather than improving toy synthetic accuracy.

## Frozen input and learned model
Use original preexisting label-free trained 126-parameter head from `NEUMANN1_LABEL_FREE_SEMANTIC_OPERATOR_LEARNING_20261017.zip`, frozen file SHA256 `e43208341dba128ba4c853ab42abe7ad8bd12ffdc292b1649ca0eb0eb74465ff`. Source input is exactly `source_probe(source,nmax=17)`: integer transition deltas at n=0,...,16, no safety goal content. No training changes and no source-specific rewrite of model output.

## Controlled indistinguishable pair, no answer leakage
Construct precisely TWO original 3-Horn SMT-LIB programs (P0/P1), one Int×Int unknown relation each. Both initialize n=s=0 and have n'=n+1. P0 has s'=s+1 at all n>=0. P1 has s'=s+1+ite(n>=17,1,0). All the 17 source delta probes are identically 1. P0 has unsafe goal `R(18,19) -> false`; P1 unsafe goal `R(18,18) -> false`. These goals are both actually unreachable in their own source, but every common candidate invariant covering both programs' reachability would have to contain **both** R(18,18) and R(18,19), while each source goal forbids one of those states. This is a **pairwise unsatisfiability proof for any common inductive invariant**, independent of network size, training method, or classical solver used, so long as the input is only these 17 deltas. For stochastic models, expected success over a uniform hidden target with only these identical features is <=1/2.

## Execution requirements
- Validate exact identity of the 17 probe arrays via source AST, and that probe 18 (at n=17) differs. Hash both original source bytes.
- Freeze and run existing actual learned 126-weight checkpoint once on both: predicted graph must be **identical**, and if exact original SMT Horn proof runs, at most one program may pass. Independent native Z3 4.13.3 verifies each of three original clauses with each candidate.
- Give two human-derivable correct explicit proof certificates **only for the proof checker control**: P0 `s=n ∧ n>=0`; P1 `s=n+ite(n>=18,n-17,0) ∧ n>=0`. Both must pass each own untouched three Horn clauses, and cross certificates fail. Do not call either a learned proposal.
- Show source-aware classical active step `probe(n=17)` separates both, and **predeclared** grammar search `F(n)=n+max(0,n-k)` for k=2..24 emits k=17 for P1 while selecting F=n for P0. Verify full originals. **This is deterministic classical repair, not neural operator invention.** Record calls, time, and no neural fallback for a learned success.
- Every code output must distinguish `FORMAL_INFORMATION_LIMIT_CONFIRMED` from `AUTONOMOUS_ABSTRACTION_DISCOVERY_UNPROVEN`; all Q1–Q7 OPEN.

This study establishes a specific architectural lower bound and a safe active-probing remedy, NOT a positive frontier-level or genuine cross-family result.