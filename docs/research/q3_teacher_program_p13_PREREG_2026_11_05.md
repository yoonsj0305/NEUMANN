# NEUMANN P1.3 | Frontier teacher → executable program → blind original checker
Date: 2026-11-05 KST · **PRE-REGISTERED BEFORE TASK CONTENT FETCH**

## Research question
P1.0-P1.2 human-authored finite grammar searches did not improve original-task success on their fresh public cohorts (P1.0 0/32, P1.1 +0 on 24, P1.2 +0 on another 24). Can an *external GPT-6 teacher* propose **task-specific executable algorithm source** not limited to a frozen DSL, while the original-task oracle is strictly isolated until verification? A positive response demonstrates an **interface feasibility** only. The teacher is NOT NEUMANN's self-improving small model, and its full inference time/tokens/cost are not measured here. Do not claim 10x or global Q3 PASS.

## Dataset and anti-answer leakage
Official `fchollet/ARC-AGI` public ARC-AGI-1 **training** set pinned to commit `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude exactly P1.0 32, P1.1 24, P1.2 24, and 4 manually inspected developer IDs. Rank remaining filenames by unsigned FNV-1a32(`neumann-q3-p13-20261105|` + filename) ascending, tie filename; select first **four** IDs. Freeze exact manifest **before opening bodies**. No difficulty/size substitutions.

The model may be shown *only* `train:[{input,output}]` and `test:[{input}]`. An isolated tool fetcher strips `test.output` fields **before returning anything to the model**; actual original answers remain private to the scoring tool until candidate source is committed. Even though these are public files and may be present in pretrained model corpora, no direct tool answer access or source post-hoc edits is permitted.

## Teacher proposal contract
- One first-submitted pure JavaScript `solve(inputGrid)` per task, or explicit ABSTAIN. No task-ID checks, no `if input equals testInput` memorization, no reading original test output, no network/file access, no model callbacks at execution. Program must apply a general rule inferred from the training examples.
- Programs are committed to a dedicated immutable first-answer source file *before first scoring*. Each must reproduce all original training pairs to qualify as `TRAIN_CONSISTENT`, then independently produce exact outputs for **all test inputs**. Failure remains FAIL; no retries after scores.
- Independent scorer loads frozen source and official pinned task content and checks all original outputs. It must be separate from the teacher's observed input. No generated program may inspect the scorer or gold.
- Program sandbox: run source using a local JS pure-function compiler, disallow injected imports/network/eval in generated solve body, validate shape [1..30]×[1..30], integer palette [0..9], and catch exceptions as ABSTAIN/FAIL.
- Baselines: frozen A/B P1.1 and J P1.2 each evaluated on the identical four original tasks, with one input/output checker. Teacher cost and the absence of equal model-level costs are explicitly reported.

## First-run decision
- **Local feasibility PASS** only if teacher-created code (not a fixed prewritten ARC DSL candidate) solves at least **one** original task that A/B/J all fail, first attempt, with training and test full-grid exact correctness, no test-answer access and independently verified program source. This does NOT prove genuinely invented mathematics, no-pretraining contamination, repeatable learned discovery or NEUMANN Q3/Q4.
- If zero new solved, **FAIL** and STOP task-specific LLM patching on these exact four. Do not search until success.
- Strongest generated candidate reused on future tasks only after independent semantic deduplication and new cohort evaluation. Need compute/latency/energy/price for any eventual system-level claim. Q1–Q7 globally OPEN and sealed Frontier Gap unchanged.

## Data and cost risks
ARC-AGI-1 public task content may have been in GPT-6 training, so a success is **not a clean generalization estimate**; treat as a teacher interface demonstration. No provider metering of GPT-6 inference token budget or actual electricity; mark UNKNOWN, not zero. No P2/Decision3 admission or production merge from this result.

## Baseline and provenance
- Frozen object baseline source blob `e2583c641426a51b1945b8fff7b1f9bba5bf9982`.
- Frozen joint-perception source blob `62e1461a4aec6ce5ce3edddfc3f42ec8d0332ef6`.
- The selected program source and original-task first receipt must remain separate from the task-data reading tool result and unchanged after first scoring.
