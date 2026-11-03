# P0.3 PRH-to-executable-structure interface: public ARC-AGI-1 development

**Frozen before first actual P0.3 run.** This is a deliberately limited test of whether a representation-derived *hypothesis* is an executable verifiable program, not proof of a new architecture, PRH theory or JEPA training.

## Source and selection caveat

Four original publicly released ARC-AGI-1 training IDs (007bbfb7, 08ed6ac7, 0d3d703e, 05f2a901) obtained from https://github.com/fchollet/ARC-AGI, Apache-2.0 license. **Researcher saw example and test content prior to design**. Program library and selected tasks are not blind and may be task-informed. Honest scope: opened, development smoke test; NOT unseen-family Q6, NOT frontier Q7, and not an unbiased ARC performance score. Retain all four cases, including failures.

## Inputs and controls

The synthesizer is passed only each task's `train` input/output pairs. It may infer a mapping from train colors and apply fixed generic primitive/composition candidates; it cannot inspect hidden test outputs or index by task ID. After synthesizing, it produces candidate programs, runs them on test input, and a separate scorer checks the original ARC test output. Multiple consistent programs must agree on test prediction or else ABSTAIN. Unsupported tasks ABSTAIN. Preserve unique program descriptions and number of program candidate executions.

The candidate library deliberately contains: no-op, geometric flips/rotations/transpose, repetitions, Kronecker replication from active input mask, height-rank coloring of columns, and a train-inferred palette map. **These are existing human-specified operators**, so a successful solution does **not** prove a new invented opcode or Q3. Even if several test predictions are exact, that is developer-set functional validation, not real-world generalization.

## Cost and go/no-go

Compare cheap classical fixed library first. Additional learned JEPA encoder training is not justified without capability that classic grammar fails to obtain and complete resource accounting. The `PRH` relational hypothesis is currently not wired to this synthesizer: its transfer into program discovery remains OPEN. Measure candidate executions and wall time. FLOPs, RAM, joules, dollars UNKNOWN, not zero. No cost advantage over strong Direct asserted. No holdout touched.

## Follow-up only if warranted

P0.4 must test novel executable operator discovery using dynamically induced grammar, equivalence certificates, matched strong baseline and genuinely fresh tasks with duplicate/solution leakage audit. Consider real ARC cases from uninspected sources only after formal preregistration. Never elevate P0.3 to Q3/Q6/Q7 global PASS.
