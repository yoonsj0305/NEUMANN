# NEUMANN 1 | G0 hard original VeryMax first, immutable NO PROOF and read-only audit

**2026-11-06 | Scientific decision: `G0_FIRST_NO_NEW_INDEPENDENT_ORIGINAL_PROOF`.** This is **not** a general impossibility theorem, not a claim that native solvers cannot solve this benchmark, and not a learned-model failure. Q3/Q4/Q6/Q7 remain **OPEN**.

## Why this is the critical path

The North Star is *frontier-level problem solving with minimum necessary computation*. Before training an alleged new structure inventor, there must be a **real unclosed original source task and a falsifiable structural advantage against strongest classical algorithms under matched original input rights**. Prior official SMT-COMP 2026 evidence showed 17/2,857 QF_NonLinearIntArith originals were not solved by any of 17 competition variants, not that no classical specialist could solve them. Two of the 17 have previously published arithmetic witnesses, so competition-only unsolved is **not** novelty.

This experiment targets one of four VeryMax original entries, `From_T2__tqli.t2__p25231_terminationG_0.smt2`. This source was inspected before prereg; it is an **opened, not heldout-blind**, independently authored original and may not be promoted to an unbiased transfer success. A separately published external [FMCAD26 artifact](https://github.com/ilanashapiro/FMCAD26_Artifact) includes an 8-thread Z3 run on the same-named source reaching **600.530 s** wall without an accepted proof; separate runner and method, **not matched cost**.

## Immutable source and experimental contract

- Upstream `ilanashapiro/FMCAD26_Artifact@abba4cbda58f7e21ece28b6c854ab675404d340b`.
- Upstream original Git blob SHA-1 `72b1b77ed5996b5a3e6d81fd75d7ea3b58347ff7`; 547,273 bytes. Original `QF_NIA`, author-reported `:status sat`.
- GitHub prereg: `docs/experiments/G0_VERYMAX_TQLI_BRANCH_FIRST_PREREG_2026_11_06.json`.
- Same new GitHub Ubuntu runner, Python Z3 `4.13.3`, cvc5 CLI installed; NO neural model calls or trained weights.
- **Direct** unmodified original: 30-second Z3 timeout.
- **Source-preserving** candidate: strengthen ONE original top-level `(or a b)` assertion to either `a` or `b`, keeping the other 113 original assertions unchanged. Each candidate branch capped at 3s and aggregate 30s, with at most 64 alternatives. This approach **cannot invent or remove semantic constraints**, but is not a general simplifier. Any candidate SAT would be independently checked against all 114 original assertions and then by cvc5 on original source with all ground witnesses.
- This was a **classical source reframe**, not NEUMANN learned new semantic discovery.

## Actual original FIRST

[Immutable original first CI #42143419543](https://github.com/yoonsj0305/NEUMANN/actions/runs/42143419543), artifact ID `13469610454`, first JSON SHA256 **`658cf722962e5b4844518017878506d137efbf6bcf0f6c0d8268fe338a66a1f2`**.

| Frozen first condition | Result |
|---|---|
| Raw source hash | Correct `72b1...47ff7` |
| Original full parsed constraints | **114** |
| Direct Z3, budget 30s | **UNKNOWN**, measured **30,143.086 ms** solver wall |
| Original largest top-level OR considered | Original assertion index **113**, two large disjuncts, **227,105** Z3 sexpr chars |
| Strengthened source branch 0 (3s) | **UNKNOWN**, 3,001.374 ms |
| Strengthened source branch 1 (3s) | **UNKNOWN**, 3,000.434 ms |
| Branch search measured wall | **6,212.602 ms**; no more branches exist in selected source OR |
| Genuine SAT witness on original | **0**, therefore original SAT model verification NOT RUN |
| Independent cvc5 full-original witness proof | **NOT RUN**, because no model was produced |
| Six soundness/negative software controls | **6/6 PASS** |
| New learned semantic operator | **0**, no neural training |

The two explicit branch calls sum to only 6s rather than the allowed 30s, because the selected original OR had **exactly two branches**. These are not equal solver-time full-budget cases and cannot support a performance comparison. The partial result fails to establish an improved original solve capability; do not retune this previously opened task and advertise a first-success.

### Independent FIRST audit

[Immutable read-only audit #42143852843](https://github.com/yoonsj0305/NEUMANN/actions/runs/42143852843): **PASS for audit integrity**, correctly reports `FIRST_NO_PROOF`, `audit_pass=true`, 0 audit errors; independently downloads saved FIRST from failed science job, verifies SHA and original source identity, preserves all measured solver outcomes. Altering the archived receipt's scientific status to `G0_ORIGINAL_CLASSICAL_BRANCH_SAT_VERIFIED` without any proof is rejected by both immutable SHA and missing independent proof control. The audit **never re-runs original solver**.

## Structural bottleneck and choice

Simple OR specialization did not reduce the domain enough for either branch to be solved at its frozen budget. The prior opened source contains thousands of integer symbols and nonlinear mixed terms; both disjuncts remain difficult. Future model work **must not** merely rerank these two branches or claim representation invention by turning one originally authored OR into a selection.

The high-impact alternative is a fundamentally different **sound representation operator**, for example discovering a source-provable conditional linearization of bounded/unbounded integer products with its own explicit exhaustiveness proof, or using an existing specialist classical solver with the same rights. But finite-domain enumeration is exponentially expensive if applied blindly to thousands of bounded variables, and published Xolver work documents outer-constraint/ray completeness complications. These are **unverified hypotheses**, not reasons to run speculative tuning loops.

## Decision and exact stop criteria

1. **CLOSE this one preregistered disjunction experiment as `NO NEW ORIGINAL PROOF`; no rerun or posthoc first-PASS conversion.** A red original CI is the scientific failure verdict; the independent audit's green CI only certifies preserved truth.
2. **`G0` general target-admission remains OPEN**. The official 17 competition-gap tasks are credible *candidate* headroom, but strong modern specialist and alternate original witness baseline costs, cross-family independence and an oracle reframe upper bound are not closed.
3. **`G1=HOLD_LEARNING` on this benchmark**. More model training, another finite Mealy problem, another ARC evaluation run or cost-unsupported claim does not solve the bottleneck.
4. **Q3 autonomy, Q4 total cost, Q6 cross-formalism transfer, Q7 frontier all OPEN**. The immediate architecture-changing gate remains the existing [G0/G1 contract Issue #530](https://github.com/yoonsj0305/NEUMANN/issues/530), not a new GUI, orchestration layer or documentation-only capability claim.

### Costs and degraded mode

Observed for the candidate solver calls: direct 30.143s, disjunction search 6.213s. These durations exclude package setup, file retrieval, native parsing and verification, and **cannot** be used for 10x full-workflow advantage. CPU joules, GPU, tokens and electricity not measured, so material-based Idiot Index is undefined here. In operational terms, the prescribed degraded mode is **UNKNOWN + original first receipt + no proof admission**, which executed as designed.

**Preserve external original copyright attribution**: original VeryMax source authors listed in upstream header (Cristina Borralleras, Daniel Larraz, Albert Oliveras, Enric Rodríguez-Carbonell, Albert Rubio), CC BY 4.0 in upstream source.
