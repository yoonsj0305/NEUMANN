# NEUMANN P2.1 and P2.1.1 | First original public evaluation decision (2026-11-05)

North Star: **Frontier-level problem solving with minimum necessary computation**. All global Q1–Q7 OPEN.

## Original P2.1 source failed before scoring
First registered object-rewrite engine was frozen with 48 original ARC-AGI-1 public evaluation filenames; the first 12 bodies were fetched and the source threw `TypeError: Cannot read properties of undefined (reading '0')` in the move-proposer `coloredDiff`: training output dimensions can differ from input. This was NOT repaired within the frozen P2.1 experiment. [Immutable first abort](docs/experiments/results/q3_object_rule_induction_p21_FIRST_ABORT.json) records `BLOCKED_RUNTIME_EXCEPTION`; no first original-task score claimed.

## Corrected P2.1.1 separate fresh-cohort first experiment
The P2.1.1 correction checks train target shape before inferring a *same-size* object movement. No task-specific solution rules were introduced. Eight Node regression tests PASS. All 48 previously reserved P2.1 evaluation IDs were excluded; a new 48 from the official public `data/evaluation/` at pinned `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34` were selected by filename-hash before opening task bodies, with source/harness blobs frozen.

- B (P1.1): **0/48** exact original tasks.
- Q (P1.6): **0/48**.
- P20 (strong existing typed affine/panel synthesis plus exact shape and palette pruning): **1/48**.
- Strong combined B+Q+P20: **1/48**.
- Combined + C211 object rewrite constructor: **1/48**; **+0** new solved tasks. No accepted wrong original outputs in this sample.
- C211 invoked on **47/48**, tried **30,943** object rewrite candidates, replayed **30,943** training programs but found **zero** training-consistent executable object program. Zero original test predictions from C211.
- Additional C211 study-region wall time **14,447 ms**; B **7,146 ms**, Q **10,253 ms**, P20 **3,165 ms** aggregated. These are coarse `Date.now()` regions, not equal-cost or full end-to-end accuracy comparisons.
- Four 12-task first receipts and complete result are immutable at `docs/experiments/results/q3_object_rule_induction_p211_FIRST_COMPLETE.json`.
- First local criterion required >=2 additional exact original tasks and 0 false accepts; outcome **FAIL_NO_ADDITIONAL_ORIGINAL_TASK_ABILITY**.

## Scientific meaning and stop decision
Object segmentation, component rank and mask/motion rewriting are still a **human-specified finite grammar**. The evidence rejects this *particular* extra object rewrite hypothesis as an efficient remedy for the NEUMANN Q3 deficit on the frozen public evaluation cohort. This does NOT prove that object-centric representations or JEPA cannot work; it does show that manual accumulation of object templates remains unproductive without a mechanism for generating genuinely new executable semantics.

**STOP** expanding P2.1/P2.1.1 handcrafted object variants on any already scored evaluation tasks. Keep P1.9's independent earlier public training cohort +2/48 original capability and P2.0 9.81× bounded primitive reduction as separate positive signals, not causal evidence for P2.1.1. Do not combine unrelated sample accuracies.

## Next decisive proposal
A new program-construction interface must be able to propose **operator schemas not present in its frozen initial library** and compile them into typed executable code, then independently verify across genuinely unseen public tasks and novel problem families. If an external GPT-6 teacher writes code, label it as *teacher* and meter separate full generation cost; do not call it NEUMANN's learned policy. Future work should focus on generative program proposal and **policy internalization**, not additional handwritten selectors.

All Q1–Q7 globally OPEN. No automatic mainline merge, no sealed ARC-AGI-2 test.
