# NEUMANN 1 | 2026-11-06 external technology adoption and EXP-2 Stitch actual first gate

**Authority:** [Frozen North Star](../research/frozen_north_star.md) and Q1–Q7 core gates. **Scientific status:** Q3/Q4/Q6/Q7 OPEN. This document does not claim to implement a learned policy.

## 1. Only essential removals

- STOP revisiting P43/P44/P45 1,800-member fixed mask/class search, G1 225-member fixed two-atom string AST search, G2 native-saturated 12 bit-vector and 12 integer invariant originals.
- Do not count a solver router, cache, passive compression, original source re-run, additional PR or positive synthetic test as learned semantic invention.
- No merger of experimental third-party engines into main without independent original-task behavior and all-in cost proof.

## 2. Actually investigated external source and license/dependency

| Public original code | Primary mechanism | Source/license and running requirements | Decision |
|---|---|---|---|
| [Stitch](https://github.com/mlb2251/stitch) | Top-down mining of reusable subexpressions of already-available programs | MIT; Rust binary via Cargo; pinned upstream **350804b7b35807c78bd21c313785ae5152ae2985** actually built and run in CI | **ACCEPT only as isolated optional compression/adoption baseline**; does not invent unseen source semantics out of thin air |
| [DreamCoder](https://github.com/ellisk42/ec) | Wake-sleep neural guided program synthesis plus library learning | MIT repository; Python + OCaml compiler/build + submodules; public source `Readme.md` | Strong research baseline concept; **DO NOT integrate full old environment** at this stage; no execution proven this turn |
| [LILO](https://github.com/gabegrand/lilo) | DreamCoder, Stitch, LLM language documentation | Public Docker and source; Python 3.7 + OCaml + Rust + recursive submodules; root machine-readable LICENSE not identified in repo root inspection | **DEFER** pending compatible license and verified end-to-end need |
| [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) | LLM proposal evolution using measured evaluator feedback | Apache-2.0; Python >=3.10, `openai`, NumPy, PyYAML, Flask, cloudpickle. Real `openevolve/llm` code uses model provider interfaces, not the NEUMANN student's weights | **REFERENCE AS EXTERNAL-LLM BASELINE ONLY**; never attribute LLM-authored programs to NEUMANN; not executed as a proposal engine this turn |
| Z3, cvc5, Eldarica, Golem | Native CHC/SMT and independent correctness authority | Existing/pinned actual task proof routes | **KEEP native-first; do not duplicate native solver internals** |

## 3. Executed EXP-1: what truly remains hard?

The original frozen 2025 CHC-COMP 24 sources were evaluated in [G3 FIRST #42174775254](https://github.com/yoonsj0305/NEUMANN/actions/runs/42174775254), independently compared to original official published task and track labels [#42175491787](https://github.com/yoonsj0305/NEUMANN/actions/runs/42175491787). Native Z3 returned a grounded verdict on 9/24 within 15 seconds, matching all nine official published ground truths; 15/24 returned no grounded verdict.

Actual latest [post-first real Eldarica v2.3 + Golem v0.9.0 original #42182127715](https://github.com/yoonsj0305/NEUMANN/actions/runs/42182127715), after both passed independent source-free SAT/UNSAT probes [#42176098022](https://github.com/yoonsj0305/NEUMANN/actions/runs/42176098022):

- Of **7** LIA-Lin originally Z3-undecided tasks, **3** were newly claimed SAT by native specialist(s), consistent with published 2025 SAT metadata. **4/7** remain resource-bounded undecided at a 20-second-per-expert predeclared budget.
- Of **8** LIA-Lin-Arrays sources, **0/8** newly decided. All 8 are in the 2025 official tournament source-set and **have no `expected_verdict`**. Their source labels are *absent*, which is not a mathematical proof of impossibility. Published 2025 competition no-success does not guarantee a later/newer stronger solver cannot solve them.
- This is evidence of a real **bounded classical residual**, NOT NEUMANN's own learned structural discovery or frontier capability recovery. No new ARC public evaluation IDs consumed.
- Per-program wall time is in milliseconds; no GPU/FLOPs/electricity or end-to-end matched-correctness cost result exists.

## 4. Executed EXP-2: one published exact Stitch source-free proof

**Before running**, preregistered:
`docs/experiments/Q3_EXP2_STITCH_MINIMAL_ACTUAL_SOURCE_PILOT_PREREG_2026_11_06.json`.

From official Stitch README, only two original source-free Lisp programs:
`(foo (a a a))`, `(bar (b b b))`.

Actual pristine pinned Rust binary:
- [FIRST #42182841182](https://github.com/yoonsj0305/NEUMANN/actions/runs/42182841182) **SUCCESS**; extracted **one** reusable abstraction `fn_0(x)=(x x x)`; rewrites `(foo (fn_0 a))` and `(bar (fn_0 b))`.
- Static program-description cost **806 → 604** = **1.3344x** improvement *in Stitch's own objective only*. This is not a reduction in actual NEUMANN computation cost. First cold build + executable wall **25.35 s** on GitHub hosted runner, peak resident process memory **420088 kB**; not an amortized runtime benchmark.
- [Independent FIRST SHA and syntactic macro expansion #42183161164](https://github.com/yoonsj0305/NEUMANN/actions/runs/42183161164) **PASS**; original stdout SHA256 `3e40357e645bfcfb6d6eb768b624da4ca40a2d684dc2737ef3fc84709d50a947`. Expanding the invented macro recovers both original byte-string Lisp representations; deliberately wrong macro `(x x)` rejected. Stitch synthesis NOT rerun.
- This proves the upstream module runs and compresses its **own preexisting official toy example**. It is **NOT** original unseen source generalization, not learned NEUMANN weights, not a neural advantage or EXP-2 Gate A/B/C PASS.

## 5. The only architectural connection worth considering

Do not implement or integrate yet: keep external engines behind a **four-stage contract**.

1. **Problem**: typed CHC source + author Git blob + original task identity, theory, source-safe train/validation partition, available native solvers and caps.
2. **Candidate**: independently trained own-weight policy proposes AST/typed invariant/operator that is **outside the closed prior H**, with complete provenance, output signature, generation cost, and no source oracle leakage. Stitch may propose *compression of existing solved-program source only*.
3. **Proof**: original semantics restored and certified by an independent checker (SMT unsat of failure or genuine countermodel), plus strong native Z3/Eldarica/Golem and equal-language GP/CEGIS; invalid/UNKNOWN yields abstain and native fallback.
4. **Reusable Structure**: a versioned typed macro, independently re-expanded and tested on *previously unseen author/family* without edits. External LLM-created macros explicitly tagged as external teacher, not student.

### STOP / unknown rules
If no genuine new trained AST has an independent original-source witness, Q3 remains OPEN. If no frozen untouched off-family source exists, Q6 remains OPEN. Equal-capability full-cost formula `R_C=C_strong_baseline/C_NEUMANN` remains UNKNOWN without student training/inference/failures/verifier/fallback/cold-start accounting. No promotion based on static compression cost or source query count.

## 6. Next ONE indispensable experiment (not done)

**EXP-2: learn a typed reusable array invariant/lemma proposer on disjoint, licensed CHC training tasks, not on the eight already opened CHC-COMP 2025 test originals.** Freeze own-weight model and typed output operator grammar and *separately authored* fresh originals before consuming any original test body. Compare matched identical rights/compute budgets against strongest native algorithms and equal-language classical GP/CEGIS plus an untrained-policy ablation. Candidate must be independently proved under source semantics; a Stitch-only passive abstraction does not count.

If no strong native benchmark residual survives or no independently verified original witness appears, STOP rather than expand fixed syntax or tune a solver. No `Q3/Q4/Q6/Q7` change until the declared necessary evidence is actually obtained.

**Project status:** EXP-1 native residual **identified** at bounded budgets. EXP-2 Stitch executable **verified only as a published library mechanism**. EXP-2 true learned semantic creation **NOT RUN**. EXP-3 cross-formalism learned transfer **NOT RUN**. Full-cost 10× **UNKNOWN**, Frontier Gap **OPEN**.
