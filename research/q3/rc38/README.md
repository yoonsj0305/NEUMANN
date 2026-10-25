# NEUMANN 1 | RC38 proof-gated on-demand instruction growth
Research only, dated 2026-10-26, DRAFT/unmerged. GLOBAL Q3/Q4/Q6/Q7 remain OPEN.

## Decisive new capability
The original own-weight learner starts with ZERO extra READ_REL instructions.
A human-coded conflict detector sees source IO contradictions and starts a NEW
PyTorch parameter vector whose SGD/Adam trained logits choose ONE new remote
READ_REL offset. The provided CREATE_READ_REL parser appends that operand to
the growing program. The loop STOPS when the SOURCE data is explained, capped
at six fresh instructions (budget HUMAN provided). No task-specific required
head number or offset is given as a supervised code label.

Five source-only tasks need 0,1,2,3,3 remote symbols; four frozen seeds each
are 20/20 source consistent. Subsequently a blind same-architecture task
requiring FOUR distinct reads is solved by 4/4 further seeds. Exact original
unminimized programs sometimes contain incidental unnecessary accesses:
18/24 minimal, 2/24 have one extra, 4/24 have two extra. HUMAN-authored
semantic compiler prunes these to true minimum 0,1,2,3,3,4 heads, then emits
safe text grammar. No claim that neural logits themselves performed pruning.

Independent AFTER-FIRST-PRED-FREEZE grader: 24/24 compiled programs
conditionally PROVED exact on ALL finite ABC strings from independent
reference under the provided predicate/conjunction/relative-read metalanguage.
240160/240160 frozen heldout strings, 2987612/2987612 chars correct (all
ABC words length1..8 plus unseen long inputs); 5000/5000 postfreeze balanced
single-symbol-change pairs, 13 distinct necessary-head impossibility
witnesses, 76 semantic mutations and 3 invalid opcodes fail closed. This
formal result pertains to compiled discrete executable rules, NOT the
original neural float output on arbitrary inputs.

Original real 62 PyTorch weight checkpoints from 24 structural-growth
runs were re-trained in a fully isolated sandbox with source IO only, no
gold code, no independent grader, no previous checkpoint: 62/62 tensors
EXACT match; both original FIRST prediction JSON files BYTE identical.
Fresh clean ZIP extracted and bash REPRODUCE.sh 6/6 pytest + sha manifest,
full independent grader and classical oracle-free baseline PASS;
bash RETRAIN.sh real 24-task/62-weight fit PASS.

Strong CLASSICAL source-IO-identical exhaustive minimum-head subset search
solves all six tasks for the same minimum 0,1,2,3,3,4: about 2.937 CPU
seconds total vs model's first cohort about 2.984 CPU seconds for same six
tasks; all 24 actor runs approx 6.751 process CPU seconds. No 10x neural
all-in speed or energy advantage. The neural policy has a human-provided
contrastive conflict-pair feature and ADD-head controller, so this does
not prove autonomous creation of the base ISA, contradiction monitor,
syntax compiler or generalized computing machinery.

Full ORIGINAL self-contained 98-file ZIP has SOURCE-only trainer and data,
actual 62 .pt, all frozen outputs, separate after-freeze private reference,
all-length proofs, minimality witnesses, failclosed parser, strong
classical baseline, two clean reproducibility shell scripts:
NEUMANN1_Q3_RC38_DYNAMIC_OPCODE_GROWTH_20261026.zip
SHA256 f4e84eec4d11cc90fe0a87e18d4205fd75df5bef46c0848bc99a13835a7254e2.
This PR contains only compact evaluated code and CI smoke, not the full
source-only 24-run original tensors.
