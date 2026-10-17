# Q3B first external transfer · final bounded architecture no-go and next kernel

Date: 2026-10-17 KST. This is an actual **experimental result**, not an extrapolated neural-failure score and not a global Q3 close.

## Frozen first-only real original source experiment
- Frozen source BEFORE target access: Git commit `47e1677bb9206bbd62395673b526795d52037247`; first immutable [GitHub Actions #39040534264](https://github.com/yoonsj0305/NEUMANN/actions/runs/39040534264) **SUCCESS**, 4/4 adapter contracts PASS.
- Frozen actual 40-weight CPU-trained model checkpoint SHA256: `2d557d5d92f4627749ded23c762ec0faf343ee20db679cee0b3222f15bf1b360`.
- Original public RustHorn upstream commit `e5a86a1ad252fe1df75e06814769ec1d14540032`, no task source modifications, no model retraining.
- Real source 1, `inc-max-2-base3-safe.smt2`: SHA256 `bed91ed9ddcac635626f150b683c23329e87e7ff8ccb1b39110745d5814cf889`, 11 original Horn clauses; frozen grammar requires exactly five; therefore `ABSTAIN_UNSUPPORTED_SOURCE_GRAPH` before model inference.
- Real source 2, `lists-3-inc-some-safe.smt2`: SHA256 `caca97e89ef8cd7a089d107d7b74971a50b5135deab68d268dc7f01b0a87786d`, 12 original Horn clauses; same abstention.
- First result: `0/2 INPUT_SHAPE_COVERAGE`, **0 neural calls**, **0 attempted proof outputs**, no inference failure claimed, global Q1–Q7 OPEN. Both targets are subgroups of the same upstream RustHorn corpus, not two independent external data families.

## Independently measured minimum source-graph capacities
After those first outcomes were frozen, a **separate post-opened engineering diagnostic** on the unchanged two originals:
- [First diagnostic #39040774203](https://github.com/yoonsj0305/NEUMANN/actions/runs/39040774203) FAILED before semantic verification because original quantified bound variables mixed Bool, Int and datatype sorts; a bug connected quantifier declaration order to Z3 de Bruijn substitution order. Keep failure receipt artifact 12104086781, not a negative science result.
- Corrected **only** quantifier variable sort order; no original changes. [Independent reparse #39040893627](https://github.com/yoonsj0305/NEUMANN/actions/runs/39040893627) PASS:
  - inc-max: **6 typed relations**, **18 non-Int formal argument slots**, 11/11 original clause decomposition XOR UNSAT, one forged-head mutation XOR SAT;
  - lists: **7 typed relations**, **16 non-Int formal argument slots**, 12/12 XOR UNSAT, forged-head mutation XOR SAT.
- Subsequently enriched JSON typed graph to emit **all guards, all relation-call arguments, typed bound variables, head term and entire original rule S-expression**, not just predicate names, so a future learner can see *meaning*, not just connectivity. [Latest meaning-preservation workflow #39041089887](https://github.com/yoonsj0305/NEUMANN/actions/runs/39041089887) PASS, 23/23 checks, replayed first frozen model transfer remained 0/2 with no model calls.

## Exact scoped no-go statement
The **unchanged frozen Q3B decoder** has two relation slots, both `(Int,Int)->Bool`, with a five-rule transition schema and only 5 predicted numeric coefficients. On each authentic original above, a *complete source interpretation* requires at least one term for EACH of the **6 or 7** distinct typed relation declarations and the full original rules. The Q3B output schema has neither enough relation slots nor the required non-Int formal domains. Therefore **no value of the 40 learned weights can make that decoder directly emit a complete well-typed interpretation for either original**. This is a *type/signature expressivity no-go* for the **CURRENT DECODER**, not a theorem that neural networks or hybrid systems in general cannot solve these tasks.

Do NOT bypass by human-filling the missing relations, renaming data to a synthetic two-int problem, or using the actual safety answer leaked by filename. If future deterministic code supplies the extra semantic clauses, model contribution must be attributed only to the relation content it truly generated.

**Scientific decision:** `Q3B_FROZEN_AFFINE_DECODER_EXTERNAL_NO_GO_CLOSED / Q3_AUTONOMOUS_SEMANTICS_OPEN`.

## Minimal next architecture, not another synthetic toy
Replace the flat fixed-coefficient input with **source-typed Horn program graph**:
1. Interface: arbitrary relation arity and sorts, original goal, guarded transitions, typed bound vars, and original source hash.
2. Learned action: emit **typed relation-program AST with variable-sized relation slots**, not one fixed numeric tuple. No manually supplied target invariant. Compile syntax only; code must not invent mathematical semantics on the model's behalf.
3. Independent proof: all original Horn rules, goal/source negative mutations, timeout/UNKNOWN fail-closed.
4. Same-info competitor: exact classical specialization, Catalia/Eldarica/Z3 as appropriate, and learned-minus, all complete compute included.
5. Freeze actual learner and grammar before choosing *new external benchmark family*. **Do not reuse these now-opened RustHorn originals as fresh learned holdout**.

This task does not establish any improved model economy, absolute classical impossibility, or frontier parity. It does eliminate an entire **unsupportable architecture family for external transfer** before spending more training compute.
