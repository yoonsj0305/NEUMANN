# NEUMANN 1 | Q3D first actual variable-relation trained semantic program experiment

**Research result dated 2026-10-17. Development-only, authored synthetic CHC family, Q1–Q7 ALL OPEN.**

## Actual experiment and bounded findings

A real 98,646-parameter PyTorch CPU model (2,048-character-n-gram source+goal features, 48-dimensional hidden layer, six predicted AST templates) was trained on 540 **researcher-authored** synthetic original Horn programs (3,059 predicate observations). Each complete original and its goal was supplied as input. Examples contain 2–9 predicates with Int/Bool/~Mut<Int> carrier and varying argument types. The output compiler accepts the correct source-specific arities but the **six semantic templates were HUMAN-DEFINED IN ADVANCE**. The model learns template choice, not a new invariant-language operator.

First training: 45 Adam updates, 90 separate synthetic validation programs / 445 relation observations, **91.2359535694% relation-label classification**. Local PyTorch version 2.10.0+cpu, 98,646 parameters. Frozen **2,088,569-byte** checkpoint SHA256 `671dab1ef5523958a0f654594d12866a0c5034769e9e393b8256cb1060e17275`. Its first training receipt captures environment and elapsed work, without equating per-relation classification with proof success.

The frozen model was then formally checked on **30 more researcher-authored synthetic source programs** generated after training. There were **171 original quantified Horn rules** in total. Source-bound typed compiler + native Z3 per original negated rule obtained:
- **22/30 full-original proofs** with learned templates; 128 original rules in these 22 successful programs were checked UNSAT.
- **30/30 full-original proofs** from a fully source-only exact classical baseline which reads the identical SMT-LIB facts and selects the corresponding property, **not a hidden label/oracle**.
- **22/22 safety-goal mutations** of the previously successful learned certificate each produced SAT counterexamples, preventing incorrect goal certification.
- The learned model's remaining 8 programs were NOT certified. Do NOT count their partial UNSAT clauses as successes.

One local candidate-only wall comparison (30 programs, frozen model, source-only classical, learned evaluated first) gave **130.813567 ms learned** versus **4.285331 ms classical**, ratio 30.526× **slower learned**. A fresh portable replay gave **210.241011 ms versus 9.268490 ms**, ratio 22.683× slower neural. These are single CPU runs, **not matched end-to-end resource cost including training/solver setup**. This is not a precise hardware performance claim, only a strong local negative signal. The classical baseline also has higher verified coverage.

## Immutable evidence and portability

The complete local source, first trained weights, first training receipt, original-rule verifier, equal-information source-only exact baseline and mutation audit were packaged for this conversation as:
- `NEUMANN1_Q3D_TRAINED_TYPED_PROGRAM_20261017.zip`
- 923,107 bytes, SHA256 `31de8ea2d2cc5d392e2b55fcc0c5800f5bb6c684ed1eefb27d178e9c31cf2c52`
- 12 members, CRC PASS, SHA-256 manifest member audit PASS, independent fresh-extract negative-control replay PASS.
- **The ZIP and its 2 MB checkpoint are available from the original conversation artifact, not committed to GitHub.** This PR logs the decision and immutable identities, not a false claim of a GitHub or independent provider model run.

The earlier PR #189 typed interface **CI fully passed**, but this does not make the new local Q3D model an external-source Q3 result.

## Scientific decision and stop-loss

**`Q3D_ACTUAL_TRAINED_VARIABLE_RELATION_TEMPLATE_MECHANISM_POSITIVE / EXACT_SOURCE_ONLY_CLASSICAL_DOMINATES / NO_NEW_OPERATOR_DISCOVERY / GLOBAL_Q3_OPEN`.**

Do not train this six-template classifier longer, widen its fixed templates posthoc, or select only its 22 successful cases. In this subdomain the classical method already solves more at lower cost. The full missing Q3 is not generic variable-arity output alone; it is proposing **previously unprovided useful mathematical structures** on a genuinely new external original, and proving their incremental necessity over the strongest equal-information classical route.

The only justified new learner is a **source+goal-conditioned typed AST constructor** with genuine variable-depth program/operator structure (including recursive folds, aggregate invariants and relation joins when needed), trained on **real source-group-disjoint program-proof pairs**, not another synthetic fixed-template labeler. Freeze both grammar and weights BEFORE a new source-family holdout; original 100% proof, negative mutations, model-minus ablation and matched strong specialized solver are hard gates. If available training examples only reproduce cheaper exact classical procedures, `HOLD_LEARNING` rather than expanding compute. Frontier-provider comparison remains a separate Q7 admission prerequisite.

No global Q1–Q7 promoted.

## Second, post-training genuine ORIGINAL evidence (development-only)

After the local 98,646-weight checkpoint and the 30 synthetic study were frozen, the SAME checkpoint was actually called **once per original** on the already-opened authentic upstream RustHorn files (both byte-for-byte SHA256 verified, no model tuning):
- `inc-max-2-base3-safe.smt2` (SHA256 `bed91ed9ddcac635626f150b683c23329e87e7ff8ccb1b39110745d5814cf889`): 6 heterogeneous relations, **one real model proposer forward**, Z3 independently rejected its output with SAT at the *third* original clause (2 previous original clauses UNSAT). Selected templates `MUT_EQ, MUT_EQ, MUT_EQ, MUT_EQ, BOOL_NEG, INT_GE0`.
- `lists-3-inc-some-safe.smt2` (SHA256 `caca97e89ef8cd7a089d107d7b74971a50b5135deab68d268dc7f01b0a87786d`): 7 relations, **one real proposer forward**, Z3 rejected its output with SAT at *first* original clause. Six of seven relation choices were **type-forced to TRUE** because the human-written grammar had no legal template for the List/mutable-List first argument. This exposes a semantic output-language gap, not just a poor trained weight setting.
- Both first post-opened model outputs were rejected, **0/2 real original whole-proofs**, 2 actual model inference calls. This is NOT a blind source-family evaluation; both targets were already used for Q3B/Q3C.
- The model's real-source verdict file is `first_opened_real_model_receipt.json` in the conversation archive, NOT a GitHub executed model receipt.

### Stronger bounded impossibility: exhaustive available AST language

Do not infer merely from the observed two failed predictions that more training would fail. Instead exhaustively enumerate **EVERY type-correct assignment** of the FROZEN six AST semantic templates across all original relations:
- Inc-max 6 relations: **144/144** candidate assignments returned actual SAT counterexamples on an unchanged original Horn rule. **UNKNOWN/ERROR 0**.
- Lists-3 7 relations: **3/3** assignments likewise SAT counterexamples, **UNKNOWN/ERROR 0**.
- Total **147/147** invalid source-specific complete certificates. Z3 4.13.3.0 fresh-context native local verification, source hashes checked, candidate coverage enumerated by typed cartesian product. **No weight vector, extra training, or confidence-threshold adjustment can select a valid candidate within this exact finite six-template decoder for THESE two sources.** This is a mathematical result about the specified finite decoder and exact original sources, NOT an impossibility theorem for neural models, more expressive grammars or unknown alternatives.
- The independent GitHub Z3Py replay, defined in `research/evidence/q3d-exhaustive-20261017/exhaustive_two_originals.py` and its workflow, is the canonical separate-platform audit; it checks source SHA256, the **frozen grammar AST SHA256** `6dbf2c209ca31b31d9ce8aeeae4f75c8d900c002d1d4dc38c70d1e096b4d4ddf`, all 147 original rule negations, and requires SAT for each without UNKNOWN. Local proof receipt `exhaustive_template_no_go_receipt.json` preserved separately. The first independent GitHub result must be inspected before calling GitHub-reproduced PASS.

**New precise decision:** `Q3D_SIX_TEMPLATE_EXTERNAL_NO_GO_CLOSED_ON_TWO_OPENED_SOURCES / SOURCE_CONDITIONED_NEURAL_Q3_SEMANTIC_INVENTION_OPEN`. STOP all additional synthetic-template finetuning. Meaningful next move is **learned variable-depth operator/relation-program construction**, not more parameters or hand-patched lemma templates. Q1–Q7 remain globally OPEN.
