# NEUMANN 1 P0.8 | Data-defined semantic operator induction

**Frozen PRE-REGISTRATION before first results, 2026-11-03 KST.** North Star remains frontier-level problem solving with minimum necessary computation. Global Q1–Q7 all OPEN.

## Target
P0.7 induced parameters of a human-written relation. P0.8 induces an **entire 8-entry binary local truth table** from observations, compiles the rule as a typed `LOCAL_RULE8` executable operator, and independently certifies all 8 local inputs. The opcode interface, binary alphabet, radius-1 stencil and periodic boundary are predefined, but no rule ID or truth-table entries are supplied to the learner. This is *data-defined program semantics in a closed template*, not open-ended new instruction-set invention or JEPA training.

## Frozen data and source separation
- NumPy `default_rng(20261103).choice(256, size=16, replace=False)`: 16 distinct, unknown-to-learner 8-bit rule IDs.
- For each rule, 5 training sequences at lengths [19,23,29,31,37], each with iid random binary cells; periodic local update outputs from independently written reference. No conditional resampling if missing context; in that case ABSTAIN.
- Separate held-out arrays per rule: 3 sequences of lengths [41,53,67], and 2 row-wise 2D matrices of shapes 4×43 and 7×59. Independent row update under same rule. The row-wise interface is explicit; no claim of arbitrary 2D or new-family generalization.
- Only training input/output pairs enter induction. Gold rule IDs and held-out reference outputs go only to independent original-task scorer **after** induction.

## Local gate (frozen)
- 16/16 unique complete tables induced and equal independent reference rule.
- All 48/48 unseen 1D sequences and all 32/32 2D matrices exactly correct (shape included).
- 5/5 negative controls reject: incomplete coverage, conflicting labels, shape mismatch, invalid alphabet, and genuinely nonlocal target incompatible with radius-1.
- Every accept has an independent 8/8 local truth-table certificate plus exact training replay.
- On any miss: immutable local FAIL. No favorable reseeding, tuning, changing gates or post-hoc replacement.

## Cost/comparators
- Same train/test inputs, run exhaustive 0..255 rule search as a baseline and compare full induction + program compilation + independent certificate + held-out execution.
- An optimized classical direct truth-table fill is computationally equivalent to the proposed mechanism; **do not claim superiority against this strong classical baseline**.
- Measure CPU nanoseconds, hypothesis checks, train/test exactness and all fallback/abstain events. FLOPs, energy, RAM if unmeasured and money are UNKNOWN; do not equate local time ratio to a 10x iso-capability system win.

## Scope and degraded mode
New operator content is within fixed local-stencil schema, not a wholly novel general algorithm/DSL or neural JEPA improvement. Global Q1–Q7 unchanged. Missing neighborhood, contradiction, malformed output, unsupported alphabet, changed boundary or nonlocal behavior => ABSTAIN and verified conventional fallback where available.

## If local gate passes
Only proceed toward Q3 through uninspected *different semantic program families*, independent original-task checkers, matched strongest classic Direct and budget, and complete cost/verification/fallback. Q4/Q5/Q6/Q7 remain gated by full resource and genuine unseen/open-set/frontier evidence. Never open sealed sets from this pilot.
