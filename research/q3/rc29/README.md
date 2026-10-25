# NEUMANN 1 | Q3 RC29 | Self-trained primitive generalizes, monolithic GRU fails

**2026-10-25 · Research Draft, DO NOT MERGE as global Q3.**

RC28 established eight own-trained conditional-GRU weights that yield
exact extracted 3/4-state pattern recognizers under a human-written classical
extractor. RC29 probes a far harder **held-out TASK SPECIFICATION**:
six trained patterns 000,001,010,011,100,111; two held-out patterns 101 and 110.

## Critical negative control (actual 2 own PyTorch GRUs)
The 24-hidden-component conditioned GRU directly takes the pattern as input,
trained only on task-level output streams for 6 patterns. Seeds 2901,2902,
900 gradient steps each, both pass ALL six known 256-length patterns with
32768/32768 bits each and 128/128 full streams. On unseen:
- pattern101: 27443/32768, 24580/32768
- pattern110: 30479/32768, 30728/32768
- **0/128 full-correct unseen streams per pattern for both models**.
This unstructured variant's heldout test was exploratory and performed in
the same program run as the first training; do NOT claim source-blind freeze.

## Critical positive control (real NEW PyTorch learned-bit opcode)
A different own PyTorch policy has FOUR learned gate logits, and shares that
unknown gate at each of the three pattern positions. A human supplies the
AND-reduce structure and binary table shape: **this remains a significant
inductive bias not self-invented by the network**.
From SIX short pattern source tasks / 48 input-output examples, with NO gate
labels or code supervision, 12 independent initialization policies all
learn EXACT gate meaning `1001`, XNOR/equality in input order 00,01,10,11.
Weight-sign-derived syntax:
`DEF OWN_<hash>(bit,bit)\nTABLE 1001\nEND`.
The parser/type/registration/proof gate is human-written, accepts only valid
explicit syntax and exhaustive 4-bit correctness under source task contract.
The inference/predictions were SHA frozen BEFORE independent oracle grade:
- held pattern 101/110 all 12 FIRST 16/16
- independently sampled both held patterns 256 streams/policy length 256:
  **786432/786432 output bits total** 12×256×256
- 400 independent arbitrary string comparisons lengths1..128 correct
- Four-entry truth-table proof and human-supplied AND fold prove all binary
  patterns of ANY finite length correct, not the raw GRU of RC29a.

## Same-rights classical benchmark
Source-task outputs and AND fold available in both cases. Complete enumeration
of ALL16 Boolean two-input truth tables uniquely recovers `1001` in
~0.00042 single-process CPU sec, vs SUM 12 trainable policy fits ~1.7 CPU sec,
strong classical massively cheaper. Absolute clock numbers are device-specific.
The trained large GRU baseline takes ~7 CPU seconds per fit with 900 rather
than 450 steps: an informative but NOT iso-parameter/iso-update comparison.
This is NO total-cost Q4 advantage, NO external independently authored Q6,
NO frontier-level Q7, and not a fresh fundamental Boolean theorem.

## Full original raw-evidence archive
`NEUMANN1_Q3_RC29_UNSEEN_PATTERN_LEARNED_OPCODE_20261025.zip`
SHA256 `4a02bf20076bf6edcde591e0910d5e574c9852fc1a052fe5fa01de0000375b53`
38 files: 12 REAL .pt primitive weights, 2 REAL .pt conditioned GRU weights,
12 SHA-frozen first prediction blobs, PyTorch source trainers, independent
grading, nonleaking generated grammar parser and exact-scope receipts.
Fresh clean-extraction `bash REPRODUCE.sh` PASS AND fully isolated
`bash RETRAIN.sh` PASS: 14/14 trainable model tensor states bit-equal,
12/12 initial predictions byte-equal. This lean GitHub PR intentionally
does NOT commit large model tensors; original ZIP is available in conversation.

## Admission
**Bounded PASS** for own-weight new re-usable bit-opcode semantics and
task-specific specification generalization under externally provided AND
compositionality. **FAIL** for unfactorized own GRU meta-generalization.
**OPEN** for totally autonomous creation of the meta-grammar, Python host,
new pattern logic parser, strong-classical total-cost advantage, external
independently authored task families, and frozen global Q3/Q4/Q6/Q7.
