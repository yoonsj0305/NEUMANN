# Q3-S3 | A three-variable source-derived invariant strictly outside fixed signed-octagon Γ₂
2026-10-19 KST

**Verifiable scoped result: PASS. Not a neural learned new operator, not Q3 GLOBAL PASS, not a claim to outperform general affine invariant algorithms.**

## What "new structure" actually means

The frozen Q3 asks whether a runnable system can find **useful hidden structure without gold/oracle input**. Prior Q3V/Q3V3 already demonstrated source-conditioned classical invariants. The stronger claim that **trained neural Q3R invents new semantic operators** was NO-GO (0 unique original proofs against the complete fixed Γ baseline) and remains NO-GO. This Q3-S3 tests a separate, precisely defined issue: extending from *signed two-variable octagonal conjunctions* to a **genuine dense three-variable relation** inferred only from original Pre singleton and unbounded transition step directions. It is **related to existing exact affine/nullspace classical algorithms** and must not be represented as novel algebra.

## Mathematical claim and proof

Let source state (s=(x,y,z)inmathbb Z^3), initial (s=s_0), and original nondeterministic transitions be (s'=spm d_1) or (s'=spm d_2), where (d_1,d_2) are linearly independent. For the constructed sources (d_1=(b,-a,0)), (d_2=(c,0,-a)), where (v=(a,b,c)) is a **dense primitive integer vector** (all three entries nonzero). The original target is

[
P(s) equiv (v^	op s=v^	op s_0);lor;(x=x_0).
]

Note that (P) **is not inductive**: (s=s_0+(0,0,1)) satisfies (x=x_0), but after (+d_1), (x
e x_0) and (v^	op s
e v^	op s_0).

**Source-only synthesis:** given ((s_0,{+d_1,-d_1,+d_2,-d_2})), and **not** the gold coefficient (v) or postcondition, calculate an exact nullspace vector (w) of the matrix whose rows are transition increments. Since rank is 2, the nullspace is 1-dimensional. Normalize (w) to primitive integers, derive (c=w^	op s_0), and propose (I(s): w^	op s=c). The original parser/SMT backend independently checks

[
operatorname{Pre}land
eg I: mathrm{UNSAT};quad
Iland Tland
eg I': mathrm{UNSAT};quad
Iland
eg P: mathrm{UNSAT}.
]

**Why the prior Γ₂ is insufficient:** an individual signed octagon atom has form (q^	op sle K) with (q) supported on at most TWO state variables, ±1 per nonzero coefficient. Since (v) has THREE nonzero entries and (operatorname{span}(d_1,d_2)^perp=operatorname{span}(v)), any such (q
e0) has (q^	op d_j
e0) for at least one step (d_j). Because BOTH (+d_j) and (-d_j) may repeat arbitrarily, some reachable states make (q^	op s	o+infty). Thus **no nontrivial signed octagon inequality with a finite bound is true of all reachable states**, and consequently the only sound *finite conjunction* of Γ₂ octagon atoms covering the reachable set is TRUE. It cannot imply the non-tautological (P). This is a **proof of strict expressivity separation from this bounded language**, NOT from broader polyhedra/linear equality algorithms or arbitrary classical provers.

## Prospective proof and exact evidence

Registered hypothesis, EXACT 12 normals, original formulas, negative mutants, criterion **before first source execution**: [Issue #251](https://github.com/yoonsj0305/NEUMANN/issues/251). One first [GitHub Actions #39191946299](https://github.com/yoonsj0305/NEUMANN/actions/runs/39191946299) SUCCESS (no model, free Ubuntu CPU), artifact 12159944699.

Downloaded artifact ZIP SHA256: `e0b4417ca8dad3d78504adb212b9dbc222000162db7fd294569b065eb1da8abf`. First raw original JSON SHA256: `26531698b8e7b457bb72d0ad6405afecdb042c91d60ab8c34012144161a81341`. Independently checked ZIP CRC, all 12 distinct source SHA, 12 sets original full 3VC UNSAT/UNSAT/UNSAT, 36/36 deliberately false original-control SAT, 12 separate 18/18 Γ₂ unbounded-direction witnesses.

Results:
- **12/12** dense three-variable conservation invariants autonomously generated from initial state+transition steps.
- **36/36** original Z3 inductive VC queries UNSAT (12 × 3).
- **12/12** `Post` by itself NOT inductive (SAT counterexample).
- **36/36** deliberately invalid controls SAT (changed branch, wrong constant, noninductive Post).
- **216/216** signed-octagon candidate direction unbounded-reachability witnesses checked (12 × 18).
- All original goals nonvacuous; no neural model calls, no GPU, training, paid API, hidden oracle, or source-file-name routing.

## Critical distinction about claims

```text
Q3_S3_CLASSICAL_DENSE_3VAR_OUTSIDE_CONJUNCTIVE_OCTAGONS = SCOPED_PASS
Q3_S3_ACTUAL_ORIGINAL_INDUCTIVE_VCS_12_OF_12             = SCOPED_PASS
Q3_S3_UNBOUNDED_GAMMA2_EXPRESSIVITY_SEPARATION           = MATHEMATICALLY_PROVED
Q3_EXISTENCE_SOURCE_DERIVED_USEFUL_HIDDEN_STRUCTURE      = PASS_SCOPED, prior evidence retained
Q3_LEARNED_NEW_OPERATORS_OUTSIDE_GAMMA                   = NOT_PROVEN (Q3R NO-GO unchanged)
Q3_BEATS_EXACT_AFFINE_OR_SPACER_SPECIALIST              = NOT_EVALUATED
Q3_GENERAL_UNSEEN_NEW_TASK_FAMILIES                     = OPEN
Q4/Q5 COMPLETE COST 10x, Q7 FRONTIER, GLOBAL Q1-Q7     = OPEN
```

**Stop point:** Do not retune these 12 author-constructed sources or promote them to unseen-family Q6; likewise do not promote synthetic proof to learned reasoning. No further classical Γ₂ demo is needed. To settle learned structure invention, preregister a genuinely trained source-conditioned operator generator on unseen independent sources and compare at equal budgets against *this dense affine/nullspace classical oracle-free generator*, not merely the weak signed-octagon Γ₂. If the learned method has zero unique safety proofs or higher complete costs, terminate it.

**Implementation / first evidence:** [Draft PR #252](https://github.com/yoonsj0305/NEUMANN/pull/252) with `research/evidence/q3s3-dense-conservation-20261019/first_dense_3var_octagon_separation.py`. No changes to frozen North Star, existing older Q3V protocols or historical neural results.
