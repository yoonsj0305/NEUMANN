# NEUMANN 1 | Q3 first actual trained quantifier proposer: integration PASS, unbounded extrapolation FAIL

2026-11-06 | **Authoritative research decision. No retraining and no favorable FIRST rerun.** Frozen North Star stays: *Frontier-level problem solving with minimum necessary computation.*

## 1. Measured positive evidence

The original first **TRAIN** is [GitHub Actions #42198111692](https://github.com/yoonsj0305/NEUMANN/actions/runs/42198111692), checkpoint SHA256 `982ef08b88758537dfe56f3ad8451de26fbd438df295802c491c25d231de9bdc`. Actual gradient-updated NumPy weights learned 20/20 four-token role programs from 3 **already OPENED** CHC source programs init4/init6/init7, and their generated SMT predicates discharged **49/49 unchanged source Horn clauses** with independent Z3. The TRAIN first process's measured end-to-end opened-development runtime was 1.64s wall and peak RSS 50,620kB, including source fetch, learned fit, compilation and verification. Only source-free training computation was partly measured; all human development costs UNKNOWN.

The **original first** heldout-with-respect-to-student-training run is [#42198669136](https://github.com/yoonsj0305/NEUMANN/actions/runs/42198669136), raw original JSON SHA256 `04a8cac1f5b886ee5b242844f6fc3ff9ceb202c17332dba37271c6d3b2c546c7`. Frozen weights generated successful quantified invariants for **2/2 source-excluded original CHC tasks**, init2 and init3, proving **20/20 unchanged source clauses** (9+11) independently. An untrained all-zero same-grammar weight control proved 0/2. Human-written G3 parametric rule also proved 2/2. No original source gold was used as a supervised neural label.

Independent **post-FIRST** [#42199539359](https://github.com/yoonsj0305/NEUMANN/actions/runs/42199539359) re-read the first evidence and checkpoint without importing training/evaluation implementation; independently reconstructed 4-token outputs from actual weights, checked the original Git blobs, re-proved all **20/20 clauses UNSAT**, and refuted one deliberately wrong quantified-value mutant with a **real SAT** counterexample. No retuned model, no relabeled FIRST.

**Scientific interpretation:** an actually trained own-weight *proposal-to-independent-proof interface* works. It is supervised distillation of a human-invented, highly constrained prefix/suffix/whole typed AST metalanguage. **There is no learned novel base operator outside human H0 and zero demonstrated exclusive solves over the strong human G3 generator.** No Q3 global PASS.

## 2. Genuine generalization test, negative

The entire trained weight SHA above was frozen before this stage test. [FIRST source-free 2..128 extrapolation #42200289388](https://github.com/yoonsj0305/NEUMANN/actions/runs/42200289388) preregistered **127 stage counts and 8,382 stage-role programs**. All model scoring was independently reimplemented in pure Python, with **zero new training, original benchmark-source access, or solver execution**. Status: `FAIL_FROZEN_OUT_OF_DISTRIBUTION_SYMBOLIC_N`.

- Trained own-weight exact **8,257/8,382** roles. **125** role errors.
- Entire stage count correct: **38/127** (n=2..39 inclusive). First failure at **n=40, final stage i=n**.
- The final stage must select `WHOLE/PREVIOUS` first interval, but the frozen student emitted `PREFIX/PREVIOUS` as its first two tokens, with remaining tokens OFF.
- Untrained zero weights exact **0/8,382**; human conditional symbolic rule exact **8,382/8,382 by definition** (this is *not* an independent new-source CHC proof for all n).
- The first FAIL JSON is archived and has not been overwritten. No source-based attempt to turn this failure into PASS.

This 127-length test demonstrates limited learned extrapolation **inside the fixed human grammar**. It does not disprove earlier human symbolic all-finite-N theorem. Learned predictions for stages n>=40 must not be assumed theorem-valid without exact original proof.

An optional independent post-FIRST **logit decomposition** will diagnose whether the input feature `n/12` causes the n39→n40 category switch, without any new training or original test. That explanation is *not* a correction to the negative FIRST.

## 3. Raw native solver classification metadata correction, READ ONLY

In first source run, raw original Z3 with cap 15s returned `CHECKER_ERROR` by the initial string parser for each of two tasks; stdout SHA256 is `7ed6120912d915f6ba8ef82ba3ec0b703265a0979bc0a243e0144580ad0c0b6b`, which is **exactly** the hash of literal ASCII `timeout\n`. Therefore this is a **15s censored source-solver TIMEOUT**, NOT a checker error, NOT an unsatisfiability witness, NOT proof that no native solver can succeed at any time budget. The original raw JSON remains immutable; only post-first classification is corrected.

Raw-native timeout plus model+proof fast success DOES NOT demonstrate 10× system advantage, because the same-source, deterministic, human-specified G3 rule also has 2/2 fully proven solutions with comparable local proof runtime, and its design cost was not measured.

## 4. Delete the now redundant neural path in this family

Treat **native classically solved cases first**. For narrowly compatible `standard_init` sources, the human G3 quantified template + independent original clause proof is already a proven deterministic route. A trained model that copies that template, costs more to train, and breaks at n40 should **not become the default production solver**.

A safe runtime must retain: proof of every original clause before acceptance; if learned candidate fails, fall back to same-rights certified classical G3; if both fail, emit UNKNOWN. Never silently substitute a guessed theorem.

Do NOT train the same model on the n40 failure and then claim the previously tested n2..128 scores are still blind. Do NOT promote source-level syntactic compression or in-family teacher distillation to Q6 transfer.

## 5. Only remaining decisive Q3 experiment

New learning work must aim **outside frozen human H0** on a different mechanism, selected by source-only preregistration and a same-budget strong-native hardness preflight. Candidate learned policy must generate a *new executable typed relation/quantifier operator* not in the prior grammar, with trainable proposal weights and without human target operator labels. Independent original source proof and genuine new-family source-unopened FIRST are mandatory; baseline is strong native plus equal-language classical CEGIS/GP, ablation is same-model untrained and trained without library.

Q6 requires a frozen learned candidate with separately author-sourced different formalism and original proof. Q4/Q5 require entire cumulative training/search/proof/fail/fallback/cold-start costs at iso-capability; Q7 requires real frontier-gap recovery. Each remains **OPEN**.

**Decision:** do not expand G3 student role-count benchmarks. Preserve the independently verified teaching-distillation mechanism as a reusable component, but redirect further discovery computation to a harder unsaturated semantic class. The moment an independent original under equal source rights is uniquely solved by a novel learned operator will be a legitimate Q3 scoped result; no such result has yet been obtained.


## 2026-11-06 actual frozen-weight analytic root cause, independently executed

[POST-FIRST analytic audit #42200792140](https://github.com/yoonsj0305/NEUMANN/actions/runs/42200792140) downloaded ONLY the original training checkpoint and the original **FAILED** 8,382-point source-free extrapolation artifact; no source program, proof engine, or model training was executed.

At the **final stage** of an N-stage initialization, the required first AST head is category 3 (`WHOLE`), not category 1 (`PREFIX`). For the original trained four-head linear model, the exact two-logit difference at the last stage reduces to

`logit(WHOLE) - logit(PREFIX) = 8.16567575830 - 0.2059240841417 * N`

because the original input contains an **unnecessary absolute stage-count feature `N/12`** in addition to the role flags. Observed `N=39` difference **+0.13463647677** and `N=40` difference **-0.07128760737**. Analytical crossing **N=39.65381607662**, exactly accounting for the first recorded error at N=40. This is not statistical speculation: the affine crossing follows by direct decomposition of the *frozen original weights*.

It proves a concrete **inductive-bias defect**: a hypothesis learned from lengths 4,6,7 inadvertently depends on the absolute stage count even though the general human theorem's role does not. Retraining on N=40 after opening this FIRST would not count as a corrected blind result. No such retraining was performed.

**Architectural decision:** for already proven `standard_init` structures, invoke the certified deterministic generalized human G3 rule directly and check all original clauses. Do **not** use the neural policy's size-dependent role decision by default. Reserve learned compute for structure operators genuinely missing from the classical hypothesis space, with independent original verifier and degraded fallback. Global Q3/Q6 still OPEN.

**Original negative first retained:** [#42200289388](https://github.com/yoonsj0305/NEUMANN/actions/runs/42200289388), **8,257/8,382 predictions**, **38/127 exact entire stage counts**. Post-FIRST audit does not change this verdict.
