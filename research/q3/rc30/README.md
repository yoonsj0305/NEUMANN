# RC30 | own-weight joint generator for comparison AND accumulation language

Research-only Draft, unmerged; date 2026-10-25.

The **actual separately trained NEUMANN PyTorch models** have NINE scalar
trainable parameters (4 local comparison truth entries +4 accumulator truth
entries +1 initial value) and a differentiable 2-state FOREACH recurrence.
Models were trained ONLY from 48 final string-relation I/O examples for each
of two tasks: ALL_EQUAL and ANY_EQUAL. Six of eight 3-bit patterns were source;
patterns5 and6 were held out. No intermediate Boolean table or program labels
were provided. **Human DID supply the entire two-state loop/conditional
Bernoulli table metasyntax, interpreter, optimizer and data**. Therefore
model-learned joint primitive meaning/loop accumulator = SCOPED PASS, while
full autonomous foundational ISA/metalanguage invention = GLOBAL OPEN.

First 12 initializations per task: **24/24 final greedy exact** 48/48 source.
Bit-frozen first unseen predictions (24 models x16 heldout width3 strings
plus 24x160 long balanced strings) **4,224/4,224** perfect. Exhaustive
width1..8 same specification for first model of each task:
**174,760/174,760**. Independent finite product-state proof of BOTH learned
two-stage opcodes' entire discrete transducers: **24/24 exact all finite
lengths**; proof DOES NOT attach to non-discretized neural logits.
Nine local circuit truth-table mutations per task rejected. 7 parser attacks
blocked. Two semantically different model-generated implementations per task
accepted and physically frozen, evidence supports genuine distinct latent
encodings. 16 post-first disjoint seeds: **16/16** correct output and all-length
proof, compared to **0/16 same initialized weights prior to gradient fit**.
Fresh retraining all 40 persisted Torch checkpoint files and all 24
source-only first generated grammar texts was tensor/byte exact.

Classical SAME-RIGHTS full search of 512 possible programs per task
**finds exactly two** source solutions, independently certifiable at all
lengths, in **~0.001--0.004 CPU seconds**. Original 12-seed neural training
takes about **17.68s +16.57s** CPU, vastly slower. This is NOT Q4 cost
superiority, nor true independent external-author Q6 or frontier-level Q7.

Full **81-file** original reproducible ZIP including all **40 actual .pt
Torch tensors**, 24 original model-generated DSL files, original SHA-sealed
FIRST outputs, original full source trainer, independently authored grader,
exhaustive comparator, 16 unfitted controls, 40-seed exact retrainer, SHA
manifest:
`NEUMANN1_Q3_RC30_JOINT_SEMANTICS_AND_LOOP_20261025.zip`
SHA256 **370f6add3cf5fba05a9550f180cc7ad5b6f998ed534ff61a5a31bfed2634c8bd**.
CLEAN ZIP extract and `bash REPRODUCE.sh` PASS. Both parts of
`RETRAIN.sh` actually executed and PASSED, 20 seeds/task.

This GitHub branch intentionally contains a **readable compact extracted
runtime and independent short regression only**, not the original full model
checkpoint files. Preserve Q1–Q7 frozen global admission constraints.
