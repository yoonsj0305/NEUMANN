# NEUMANN 1 | G0 original VeryMax TQLI structural headroom FIRST negative decision

2026-11-06. **Scientific decision: NO NEW ORIGINAL CERTIFIED PROOF / G1 HOLD.**

## Problem and current context

The frozen North Star remains **frontier-level problem solving with minimum necessary computation**. Do not confuse machine-checker correctness with new semantic representation invention.

The external official SMT-COMP 2026 QF_NonLinearIntArith single-query division had **2,857** benchmark records and **17** jointly unresolved by all 17 competition solver variants on the accepted SAT/UNSAT cohort, after the prior published competition data were independently audited ([original official-union run #39421585497](https://github.com/yoonsj0305/NEUMANN/actions/runs/39421585497); see issue #218). This proves a competition-time specialist gap, **not** logical unsolvability or a learned NEUMANN edge. The 17 include 4 VeryMax/ITS and 13 MathProblems. Two MathProblems SAT witnesses already published were verified, making external literature/witness retrieval a necessary additional strong classical baseline.

We selected ONE externally authored QF_NIA SAT original from VeryMax, unchanged:
`ilanashapiro/FMCAD26_Artifact@abba4cbda58f7e21ece28b6c854ab675404d340b`,
`scripts_datasets/inputs/QF_NIA_2313/From_T2__tqli.t2__p25231_terminationG_0.smt2`, Git blob
`72b1b77ed5996b5a3e6d81fd75d7ea3b58347ff7` (547,273 bytes; CC BY 4.0 according to original header). This was **researcher-opened during preregistration**, not a sealed first-blind original; the same filename was already included in prior published solver benchmarks. No possible novelty claim from changing its name.

The independent 2026 external [FMCAD26 artifact](https://github.com/ilanashapiro/FMCAD26_Artifact) recorded a same-named **600.530-second 8-thread Z3** run without a conclusive answer. This is contextual external difficulty evidence only, not a matched local benchmark, and not a proof no other exact classical solver can answer.

## Registered test

**G0 headroom hypothesis**: without training, a semantics-sound transparent OR-branch specialization may reduce a massive SMT source by keeping every original assertion except replacing one selected top-level OR by one of its exact disjuncts. Such a model, if independently checked on ALL original constraints, is a valid original SAT witness. Unlike arbitrary expression rewriting, this is a sufficient-strengthening transformation, not an equivalent whole-formula transformation; it cannot establish UNSAT from merely a capped subset of alternatives.

- Precommitted exact source blob and 30 s native Z3 control; branch search total budget <=30 s, <=3 s per branch, <=64 candidates; independent original cvc5 with exact model mandatory for any SAT success. Read the [frozen prereg](../experiments/G0_VERYMAX_TQLI_BRANCH_FIRST_PREREG_2026_11_06.json).
- Original Z3 4.13.3 + cvc5 apt installed in actual GitHub-hosted runner. Invariant software negative controls **6/6 PASS**.
- [One-and-only original FIRST #42143419543](https://github.com/yoonsj0305/NEUMANN/actions/runs/42143419543): **scientific FAIL**, not infra. Exactly **114 original assertions** parsed. Native direct Z3 `unknown` after **30,143.086 ms**, budget 30 s. The selected top-level OR (assertion index 113; 2 children; printed AST 227,105 chars) produced candidate 0 `unknown` after **3,001.374 ms** and candidate 1 `unknown` after **3,000.434 ms**. Branch verification path **6,212.602 ms total**; both alternatives were tried and neither produced a model; total source model check **NOT RUN**, independent cvc5 original witness check **NOT RUN**. **No original SAT proof.**
- Original first JSON SHA256 **`658cf722962e5b4844518017878506d137efbf6bcf0f6c0d8268fe338a66a1f2`**, preserved as original [FIRST artifact #13469610454](https://github.com/yoonsj0305/NEUMANN/actions/runs/42143419543/artifacts/13469610454) after scientific CI failure. Do not change it or relabel CI green for nonproof.
- Independent [pinned first read-only audit #42143852843](https://github.com/yoonsj0305/NEUMANN/actions/runs/42143852843): **PASS**, original result SHA pinned, exact source file Git blob identity matches, original two UNKNOWN branches and direct UNKNOWN preserved, source not re-solved, first-result forged PASS rejected. Audit success means **provenance honest**, not mathematical problem solved.

## Causal diagnosis and discrimination

1. This task has **2,347 declared integer variables**, **114 top-level original assertions**; one selected OR's printed AST spans **227,105 characters** and only **2 disjuncts**. Literal top-level OR splitting at 3 s did **not** expose a feasible model.
2. The native Z3 run at 30 s is `UNKNOWN`; the two specialized branches got only 3 s each and spent ~6.2 s total. Thus this execution **cannot establish a fair equal-compute-performance regression or parity**, merely **absence of the preregistered positive proof**. A direct Z3 30-second UNKNOWN is not proof of any solver-wide intrinsic lower bound.
3. Repeatedly extending timeouts, testing many similar disjunctions or manually picking a lucky branch after seeing the original first result would be **posthoc tuning**, not an independently transferable structure learner.
4. This run used **zero neural discovery policies, zero training, zero ARC evaluation IDs**, so it cannot demonstrate Q3/Q6 true learned transfer regardless of a future SAT classical result.
5. External published competition result is a real G0 **candidate** headroom screen; Q3 learned-exclusive headroom still requires native specialist + literature baseline comparison, a true candidate representation not in a fixed hand-provided DSL, and a sealed independent source-family target.

## Five-step first-principles decision

1. **Challenge requirement**: No longer treat larger benchmark counts, more fixed-state simulations or green workflow as necessary proxies for new intelligence.
2. **Delete**: STOP top-level OR-split variants, repeated timed solver attempts on this already-opened original, and more MQTT/TLS classical task variants.
3. **Simplify**: Keep only the explicit discovery-policy output interface, original proof checker, strongest classical control, and fixed unseen external evaluation.
4. **Accelerate**: Admit G1 *only after* finding at least one class of original problems where a verified new representation can surpass the strongest same-rights classical portfolio on a registered denominator. Existing 2026 union gap of 17 is candidate only.
5. **Automate last**: Automate repeated cross-family evaluations only after a first genuinely discriminative G1 receipt, not to scale nonproofs.

## Costs and impossibility of 10x claim

Measurement units here are single GitHub runner wall milliseconds for the direct/branch calls. No matched full-lifecycle GPU training, serving, proof, operating costs. The product `Idiot Index = finished manufactured cost / raw material cost` is **not applicable** to this algorithm-only proof experiment and cannot be filled with invented values. Do not calculate a favorable 5x speedup from `30.14s/6.21s`; both are **UNKNOWN**, accuracy 0/1 on a single original, and branch budget allocation differs.

## Risk and degraded mode

- Missing / incorrect source Git blob => `INFRA_OR_SOURCE_FAIL_CLOSED`.
- Interrupted solver or exhausted cap => `UNKNOWN`, **not proof**.
- Candidate SAT from branch without full original verification => `UNKNOWN`, not SAT.
- Incorrect or unverified independent model => **not admitted**.
- Hard examples selected because publicly known to be hard => no claim of probability-unbiased new-family generalization.
- Original frozen binary G0 failed; posthoc research can inform future source-isolated *new* experiments but never overwrite this FIRST.

**Final gates**:
`G0_TQLI_SEMANTIC_BRANCH_FIRST=FAIL_NO_PROOF`,
`G0_REAL_COMPETITION_JOINT_HEADROOM_CANDIDATE=17` (historical external screen only),
`G1_NEW_LEARNED_OPERATOR=HOLD`,
`Q3_NEURAL_NEW_SEMANTICS=OPEN`,
`Q4_EQUAL_RIGHTS_ALL_IN_COST=OPEN`,
`Q6_CROSS_FORMALISM_NEW_AUTHOR_TRANSFER=OPEN`,
`Q7_FRONTIER=OPEN`.

**Recommended minimum next actual experiment:** one previously unopened, independently authored original family with fixed raw problem denominator; frozen learned semantic proposal and same-rights native solver/CEGIS/GP baselines; independent original proof/witness and complete cold/warm costs. Stop early if classical solves all cases or the new proposal only selects already-supplied operations. Preserving clear failure here is more valuable than fabricating a breakthrough.
