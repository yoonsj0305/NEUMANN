# NEUMANN 1 | Authentic SyGuS-SGI original heldout and structural invariant G0 ACTUAL (2026-10-27)

**Verdict:** `G0_CLASSICAL_ORIGINAL_HELDOUT_CVC5=11/12`; `LEGACY_GRAMMAR_STRUCTURAL_EXCLUSION=2/3_EXTERNAL_EASY`; `NEUMANN_NEW_LEARNED_STRUCTURE=NOT_PROVEN`; **GLOBAL Q1-Q7 OPEN / G1 HOLD / G2 NOT RUN**.

This is NOT NEUMANN trained intelligence, NOT a first-blind across LLM pretraining sources, NOT frontier performance, NOT a 10x gain. The result concerns authentic original tasks and strong classical programs.

## 1. Evidence chronology, immutable first outputs and first failed run

1. External independently published [Barnard-PL-Labs/sygus-sgi-1](https://github.com/Barnard-PL-Labs/sygus-sgi-1) pinned at commit `e7ae840e5546e9243ff94afb1a29064fc050011c`, easy 8-bit / hard 64-bit. Filename-only hash rank seed `neumann1-semantic-gap-v1/`. Public benchmark, possible LLM pretraining contamination (no trained LLM called).
2. Initial prereg GitHub **`4a5ae8b89e46b5b5a618043c9e2ea4f1de770788`** requested 6 easy+6 hard; first [Actions #40451521100](https://github.com/yoonsj0305/NEUMANN/actions/runs/40451521100) installed native cvc5 but **failed before opening selected original task contents** because the original repo contains only 3 easy file paths at the specified depth. Preserve as `EXECUTOR_SELECTION_ERROR`, not a model failure.
3. Transparent PRE-CONTENT but POST-FIRST amendment GitHub **`a49478b83570447bdc186c0ec849d4253acec956`** changed to 3 easy+9 hard, selected by **the same original filename-only SHA256 ranking**; runner amended `68d871227255b0844236280ae984e8428c0c1120`. No manual choice by result or task body.
4. [Real native CVC5 1.1.2 first source-only Actions #40451797444](https://github.com/yoonsj0305/NEUMANN/actions/runs/40451797444), research workflow commit `89a03b8a8e4273c37143b772dcefcce3e57f16ed`: 12 original pinned file IDs. A balanced S-expression extractor removed exactly the **last original `constraint`** from each solver copy, retaining the original `synth-fun` grammar and all prior constraints. 12/12 source-only `define-fun` candidates, zero executor errors; NONE graded before freeze. **FIRST JSON SHA256 `44047cd18e17e517cf0029329589411b997f53427d8fa3e152b044183d8524f0`**, pre-grade freeze GitHub **`47242458b0333bb6d974445e91ca837c482d24bf`**. [Raw 12 program outputs and original source/input hashes artifact #12710573047](https://github.com/yoonsj0305/NEUMANN/actions/runs/40451797444/artifacts/12710573047), ZIP SHA256 `1075da4e7f379adad13477aa92077b7247ac4eeb01bd26db36ed3955416e6ef1`.
5. AFTER the above freeze, [separate Z3 4.13.3 original constraint verifier Actions #40452338505](https://github.com/yoonsj0305/NEUMANN/actions/runs/40452338505), first candidate hashes checked unchanged. For each candidate, Z3 independently checked **(a) that the negation of conjunction of all original SOURCE conditions is UNSAT** and **(b) that the negation of removed LAST original condition is UNSAT**. Results: **12/12 source UNSAT, 11/12 omitted original heldout UNSAT, 1/12 heldout SAT**. The single actual heldout failure is `hard/PRE_76_10/PRE_76_10.sl` (its frozen CVC5 source-only candidate is source-consistent but future-falsified). No skipped files or HOLD. **Independent grade JSON SHA256 `e76dbc2fb50740c784bea140b60044d74587fc9dc9b10cdc0cf4aed854e31162`**. [Verifier artifact #12710484140](https://github.com/yoonsj0305/NEUMANN/actions/runs/40452338505/artifacts/12710484140), ZIP SHA256 `91e02aef16a2f5f7f9a9c17840228b172fe324cc5744aa82e7597f3ccdfba31e`.

## 2. New FIRST-PRINCIPLES representation barrier: bijection invariant

Previous NEUMANN 8-bit generator grammar used only operations `ADD(c) modulo 256`, `XOR(c)`, `ROL(r)`. EACH operation is a bijection on the 256 possible bytes:
- `ADD(c)` inverse `ADD(-c mod 256)`;
- `XOR(c)` is its own inverse;
- `ROL(r)` inverse `ROR(r)`.

**Theorem:** Every finite composition of these three operator classes is bijective, independent of depth and constants. Any target that maps two distinct byte inputs to the same output is mathematically IMPOSSIBLE to express in that legacy DSL. This is stronger than a 136,448-program bounded enumeration and requires only a verified collision witness; no neural call or long search needed.

On three ACTUAL externally authored original SyGuS-SGI easy tasks, the already frozen native classical CVC5 expressions were:
- `easy_1`: `f(x)=x`. 256 distinct outputs, bijective. Expressible in the old DSL (`ADD(0); XOR(0)`).
- `easy_2`: `f(x)=x >> 1` (the ORIGINAL author provided `ehad(x)` = `bvlshr x #x01`). 128 distinct outputs; **f(0)=f(1)=0**, so not in the legacy A/X/R language **at any depth**.
- `easy_3`: `f(x)=NOT8(x >> 1)`. 128 distinct outputs; **f(0)=f(1)=255**, so likewise impossible in the legacy A/X/R language **at any depth**.

All 256 input words explicitly evaluated per task, and the exact original author's native program constraints were independently checked by Z3 in the frozen 11/12 baseline grade. Fast standalone certificate script's JSON SHA256 `959c1803d0567ec8a8418adac133ae0c2ecaf2536131fe625fc00e2df642aa07`. The first attempt to re-enumerate the 136,448 restricted two-step programs timed out; the fully general bijection invariant replaced that costlier test and proves a stronger (arbitrary-depth) conclusion.

**IMPORTANT LIMIT:** These two external functions are out of the *NEUMANN legacy toy DSL*, **NOT beyond strong classical solvers**. Native cvc5 explicitly used the original external author's grammar, including `ehad(x)`, and solved both in about 16ms process wall each. No NEUMANN model invented a new operator here. Do NOT mistake a proven DSL gap for a learned discovery PASS.

## 3. Costs and causal interpretation

Native cvc5 first execution's SUM over 12 separate processes: **0.875342 seconds wall**, **0.753593 seconds user CPU + 0.044364 system CPU = 0.797957 CPU seconds**, sampled maximum process RSS across all tasks **50,580 KiB**. RSS polling misses peaks and is a lower bound; hardware, apt installation, source acquisition, Python harness, separate Z3 verification, energy, all-in latency and dollars are not included. Not an end-to-end cost, not comparable with neural amortized training and no 10x claim.

Existing classical C has already solved 11/12 original heldouts with independent verification. The one C-specific failure only establishes a **bounded source-only cvc5 1.1.2 generalization error**, not a proven representation gap against all equally authorized classical solvers. If selecting or training on this failure, consider the outcome already **OPENED / POST-FIRST**. Any future genuine model study needs NEW unseen source families and ownweight A/B/C/D with full capability/cost parity and separated independent gold.

## 4. Research decision and evidence

- Promote as an **engineering gate**: use cheap structural semantic invariants (bijectivity, monotonicity, linearity, etc., when their applicability is proved) BEFORE spending on exhaustive enumeration or neural training. Such an invariant is a *certificate relative to an explicitly defined operator class*, not a general global impossibility claim.
- Do NOT train an extra A/X/R neural program selector on the 2 impossible functions. The output support is mathematically absent. To close genuine capability gaps a model must support open typed semantics, invent executable operations beyond its pre-supplied grammar, learn from independent repair feedback, and beat strong classical algorithms.
- Global Q1-Q7 OPEN; G1 HOLD; G2 NOT RUN. Research PR #616 remains draft.

**Portable evidence ZIP**: `NEUMANN1_SGI_G0_CVC5_Z3_AND_SEMANTIC_PROOF_20261027.zip`, SHA256 **`ec34459cc9b081142a6626b988bdcee44ec80874e030fae6f43e6e0e248dfa0e`**, 6 entries, CRC PASS, inner SHA manifest of 5 files, with original CVC5 first ZIP, independent Z3 grade ZIP, 3-case semantic theorem JSON, rerunnable cert script, README and manifest. No upstream benchmark source files redistributed.
