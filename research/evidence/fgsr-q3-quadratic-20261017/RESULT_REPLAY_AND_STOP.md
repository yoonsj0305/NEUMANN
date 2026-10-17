# NEUMANN 1 · Q3 quadratic learned semantic content: strict holdout and classical gap audit

**Date:** 2026-10-17 KST.
**Verdict:** `TRAINED_QUADRATIC_RELATION_CONTENT_CERTIFIED_RESTRICTED / CLASSICAL_16.59x_FASTER / NO_LEARNED_NECESSITY / Q1_Q7_OPEN`.

## One new scientific question only

Last stage: 27 trained coefficients could generate **only linear equality invariants** on a fixed synthetic 3-Int source class, with exact classical cross product at least as capable and faster. This experiment asked whether a genuinely trained coefficient head could make **nonlinear degree-two invariant conjectures** that escape any *nonzero linear equality* invariant on source-reaching states. No authentic external hard benchmark solved.

## Pre-registered mechanism, no source-goal answer hint

[PRE-HOLDOUT contract](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-quadratic-20261017/PREREG_BEFORE_HOLDOUT.md) was committed as **`d2562efd61af99441758990034c76219b7e0aa95`** after training checkpoint freeze and **before generating or opening holdout**. Source and resulting weights were not tuned in response to holdout.

- Original source class: 3-Int `Inv(x,y,z)`, initialization `(0,0,0)`, `x+=1` and `y+=1` with correctly guarded quadratic `z` increments, and a safety goal forbidding `(x=0,y=0,z=1)`. Safety goal **never includes candidate invariant coefficients**.
- **Researcher-specified** polynomial basis `z = A x²+Bxy+C y²`. Neural architecture **`torch.nn.Linear(6,3,bias=False,dtype=float64)` = 18 genuine trainable weights**, taking exact source-parsed coefficients from 2 original transition Horn rules. SMT renderer only inserts neural numbers into the preselected quadratic basis and may not repair an incorrect candidate.
- Training 1,024 (seed `2026101705`) and validation 256 (seed `2026101706`) authored syntactic-source-A programs. Adam lr .08, **247 optimizer steps**, validation max abs error **9.23e-6**, optimizer-only wall **73.149ms**, data synthesis/parsing excluded. Classical symbolic teacher produced coefficients for training: this is supervised method distillation, NOT independent operator invention.
- Frozen weight file SHA256 **`7d7893a0cadd385a799770fb910fd11811fb650458c07bac97bf6bcd48aea67f`**. Actual [human-inspectable 18 learned numbers](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-quadratic-20261017/FROZEN_18_LEARNED_WEIGHTS.json) also committed. 
- Exactly one corrected-goal unseen-random-seed set, 64 authored source-B guarded-assignment programs, seed `2026101707`, integer coefficients with A,C nonzero and opposite sign drawn from [-11,+11]. Source-B differs **syntactically**, same semantic program family. No actual unseen external CHC family.
- Each original generated file was independently checked under Z3: substitute candidate for Inv in all 4 original quantified Horn clauses, test each negation UNSAT. Invalid or partial proof not counted. All source bytes, per-original hashes, inferred coefficients and proof-status vectors are in archived reproducibility ZIP.

## Actual result, including honest overlap

| Equal-source-information proposal | All four untouched generated Horn clauses verified |
|---|---:|
| **Frozen trained 18-weight neural coefficient head** | **64/64** |
| **Strong source-exact classical quadratic algebra** | **64/64** |
| Fixed `z=0` conjecture | **0/64** |

A post-holdout **leakage/uniqueness audit** discovered **4 of the 64** holdout coefficient triples had also occurred in training (indices 12,21,26,27), and one other holdout duplicate (index 46 repeats 13). They were NOT concealed or dropped from the raw result. Therefore the strict scientific number is **59/59 unique train+validation-disjoint examples with valid 4/4 proofs**. These still all belong to the same authored quadratic semantic family.

- Median **candidate proposal only**: frozen neural **91.826µs**, stronger exact classical **5.534µs**. Classical is **16.59× faster** on that substep, ignoring model training, and perfectly matches capability. **DO NOT compare this microbenchmark to full original Z3 verifier wall times.** No economic speedup claim, no frontier parity.
- New proof that previous *linear equality* representation is insufficient on **all 64** original programs. Original transition semantics reach `(1,0,A),(2,0,4A),(0,1,C)`; since A != 0, an affine equality `a*x+b*y+c*z=0` holding at all reachable states has `a+cA=0`, `2a+4cA=0`, `b+cC=0`, forcing **a=b=c=0**. Independent audit checked the corresponding determinant nonzero on every original. This does **not** rule out arbitrary linear inequalities, disjunctions or stronger classical CHC solvers.

## Independent integrity / replay

Artifact `NEUMANN1_QUADRATIC_LEARNED_GATE_20261017.zip` **50,366 bytes**, SHA256 **`ab0eda564bc7fe179f9ba7105f9481438ae1f76a644a821525fcd7179f8a7fcc`**. ZIP CRC PASS, **72/72 authored payload SHA-256 manifest PASS**. Extracted in a fresh temporary directory and reran `python audit.py`: **64 × 4 = 256 original Horn clauses** independently checked again, 59 strict unique unseen-triple checks, 64 no-linear-equality certificates, and **3 mutation/zero-predicate negative controls** PASS. Archive includes all source texts, training implementation, learned checkpoint, exact proof code, holdout receipt and audit. No third-party program text redistributed. Source code is in downloadable artifact; the GitHub content record preserves frozen weights, preregistration and scientific verdict, not the complete source implementation.

## Core decision

`GO` only on learned operator/abstraction language proposals for truly new independent **external original source families** where existing top classical specialist has measured **unsolved headroom**, with full original proof and actual matched cost. **STOP** further scaling quadratic synthetic source model; its success is fully explained by a trivial exact algebraic teacher and strong classical control. Our North Star is frontier-level problem solving at minimum necessary computation, not small models for their own sake. Q1–Q7 **all OPEN**, Q7 remains provider evidence blocked.
