# NEUMANN 1 P2 OOD Operator Grammar Growth · preregistered before OOD source generation

**2026-10-17. Strict scope: source-derived automatic new macro structure with a frozen 126-weight prior, not neural invention or external source-family transfer. Q1–Q7 OPEN regardless.**

## Frozen legacy head
Reuse byte-identical `FROZEN_TRAINED_AST_HEAD.npz` from the previous 70/70 compositional experiment, SHA256 `990c7ba0b96e017180c35388da622ab292cb9d270d0e8a5fc43b0d65d72d21a3`. Original learned 7-leaf vocabulary `N,N_SQ,N_CUBE,MOD_2,MOD_3,RAMP_3,RAMP_6`. Reuse old source AST probe extractor, 17 n=0..16 observations and all original three quantified Horn rule Z3 check with no label/goal leakage.

## First controlled out-of-vocabulary cases
Create **exactly two** new source programs with hidden invariants `s=floor(n/5)` and `s=floor(n/7)`, with original transition increment `ite(= (mod n K) (K-1)) 1 0`, initial n=0,s=0, and a concrete forbidden state n=35 and s=floor(35/K)+1. The goal shall not include source-invariant expression. Different source names and syntax, no goal access to model. Both K are outside previous MOD_2/MOD_3 training operator leaves. First test whole-original proof (3 obligations) for frozen learner's seven-leaf output, exact classical existing-seven-leaf span and fixed leaf baseline. A seven-leaf sum is not permitted to hallucinate a missing operator.

## Abstraction-family growth protocol (post-neural ABSTAIN, pre-program examples frozen)
- Detect OOV using exact source transition signature vector, and require no exact rank-preserving solution within frozen seven primitive delta signatures; use a **full rank residual certificate**, not learned logits alone.
- Only on OOV, run predeclared **symbolic classical operator-macro generator** `FLOOR_DIV(n,k)`, k scanned from 4 through 11 in ascending cost order. This *family* is researcher-given. Check candidate delta equality over ALL 17 source probe points, then **independently validate all 3 original quantified Horn assertions** after replacing the relation with emitted SMT-LIB `(= s (div n k))` and `n>=0`.
- Any model decision after OOV is ABSTAIN, no neural retraining or post-example weights modification. The new macro is discovered **by classical, bounded search**, not by trained neural output. This is constrained grammar extension, not autonomous creation of a previously unknown operator family.
- Equal-information **strong classical** uses the same source original and same macro generator; it is expected to solve as well or cheaper. Compare original checks and wall times; do not claim learned necessity, 10× advantage, Q3 closure.
- Include synthetic falsification test where the output `s=0`, `s=(div n (k+1))`, or mutated source transition shall be rejected by original full Horn verification.

If two new OOV macros become formally certified, allowed verdict `SYNTHETIC_SOURCE_DRIVEN_GRAMMAR_GROWTH_CONFIRMED_CLASSICAL`, not novel neural operator invention or cross-family transfer. If none certified, report actual negative result without posthoc source changes. No additional holdout cases.