# P1 — First Real Non-Generative Controller Diagnostic

Stage: preregistered route-only first attempt. No actual P1 result exists yet.
P0 passed; original Decision 2 remains FAIL. P2 and Decision 3 remain blocked.

## Hypothesis and scientific scope

The same frozen Gemma core can produce finite, input-sensitive fixed-route
likelihoods without free-form generation. P1 tests operational controller
readiness only. It cannot establish routing accuracy, capability uplift,
compute savings, unseen generalization or a frontier gap.

The input file exports only the instruction/public view of the exact existing
12 opened AM1 tasks. Public examples are allowed; private answers, hidden tests,
task-family labels and runtime IDs never enter the scorer. IDs are bookkeeping
only. Original view SHA256 is
`c883a44136817bf2501549a42c268b29577b8f153b3ca95b807e7ab245fdd2f0`.
No new questions or sealed rows are obtained.

## Frozen configuration before first execution

- Gemma `google/gemma-4-E2B-it`, revision
  `3e22461f65e89153144f8adb70e3b8c2cc9845a7`, BF16, weights frozen.
- Original artifact/vocabulary SHA256s remain pinned by the P1 contract.
- Registered execution device: Kaggle Tesla T4; no CPU/model/precision fallback.
- Runtime matches retained D2: torch 2.11.0+cu128, torchvision 0.26.0+cu128,
  transformers 5.16.1. Framework mismatch stops the attempt; bootstrap does not
  automatically replace torch or choose a new accelerator.
- Same P0 route prompt and fixed candidate token strings:
  `DIRECT / ARITHMETIC / CSP / PYTHON`.
- No cost bias in P1: lambda=0. No relevance scoring or KEEP/DROP inference yet.
- Mean conditional log likelihood of forced label tokens only; explicit
  separately encoded prefix/label IDs, no special tokens on labels.
- Same frozen processor chat template; `enable_thinking=False` defines the score
  prefix. This is forward scoring, not a thinking-off generation rescue.

For every task, evaluate three modes: normal-order batch size 4, normal-order
batch size 1, reverse-candidate-order batch size 4. All 12 tasks receive all
three modes; no selected favorable subset. This is 144 candidate rows and 72
registered forward calls on complete execution, not 144 generated answers.
Candidate order is changed in the score batch, not in the public problem.

## Budgets and complete cost

- context including forced label: 4096 tokens, no truncation;
- each label: <=16 tokens;
- total evaluated tokens <=196608; padded tokens <=196608;
- total score rows <=144; forward calls <=72;
- each complete task (all three modes) <=120000 ms;
- study <=1800000 ms including registration, model load, template preparation,
  scoring, file/audit/controller overhead;
- outer bootstrap runner watchdog: 2700 s. Synchronous GPU forwards cannot be
  interrupted by Python's soft deadline; overrun work remains failed evidence.

Generated calls/tokens and tool calls must all be zero. Both core.generate and
model.generate have a counted hard tripwire. Scoring receipt costs include
tokenization and transfer/synchronization in the pass wall, plus raw label scores,
margins, exact encoded rows, evaluated/scored/padded tokens, forward calls and
measured per-pass peak allocated accelerator memory. Actual reserved/allocated
memory and parent RSS are retained by the original core audit. Missing memory
measurements are not substituted with zero. Scored tokens are not generated
tokens or FLOPs. Energy/FLOPs/money stay UNKNOWN.

Failed/partial forwards retain STARTED records and known attempted forward/pad
counts. Incomplete ledger entries do not mean the missing computation was free;
partial evaluated token counts remain unknown. A complete accounting claim is
made only when all three modes on all 12 tasks finish and agree with replay.
Bootstrap setup+runner wall and archive packaging time/hash are separate receipts;
the archive cannot contain its own final SHA256. Preserve its `.sha256.json`
sidecar as well. Download/installation costs are not hidden as query inference.

## Preregistered PASS, FAIL and NOT_EVALUATED

PASS requires 12/12 complete observations; exact unchanged model identity;
no generation/tool/hidden-input use; finite log probabilities; complete cost;
and all frozen resource caps met.

Additional diagnostic criteria are frozen, not fitted to P1 scores:

- maximum absolute batch/unbatched score difference <=0.05 nats;
- maximum absolute normal/reversed-batch score difference <=0.05 nats;
- if the primary top-two margin is >0.10 nats, the winner must remain unchanged
  in both comparison modes;
- at least 2 distinct primary winning routes;
- no route may win more than 10 of the 12 tasks;
- maximum across-task range of row-centered route scores >=0.001 nats.

The 0.05 nats tolerance is a fixed BF16 diagnostic allowance, not an empirically
validated accuracy threshold. Numeric consistency alone does not prove semantic
control quality. Collapse/order instability yields FAIL and requires a separately
registered representation/label revision. It never permits a favorable rerun of
this first attempt. Label lexical bias is not fully identified by order probes;
nondegeneracy cannot certify good routing. Matched original-answer P2 remains
necessary. Missing/partial receipts, source/runtime/model identity mismatch or
audit failure are NOT_EVALUATED; generation use is forbidden/FAIL.

## First attempt retention and subsequent gate

`scripts/control_plane_p1_kaggle.py` creates an exclusive setup marker and refuses
reuse of setup/output/archive paths. It downloads one exact published source
commit, validates source/contract hashes before model load, runs P1 once, replays
the result without model inference, and packages even incomplete attempts.
Do not clear those files to get a better run. Save the first ZIP and sidecar.

After final-head CI and merge, use the published commit+script hash in one Kaggle
cell. Enable Tesla T4 GPU and Internet first. No paid service is provisioned.
An incompatible image is reported rather than silently changing the experiment.
This preparation does not itself execute P1.

P1 PASS permits preparing/registering P2 only. Strong normal-answer DIRECT,
full-input TOOL and minimal-evidence NEUMANN must then share the frozen core,
tools and declared total resource limits with original independent verification.
Actual normal-answer/executor admission and a new capability/resource threshold
are required before P2 runs. A zero-success baseline cannot yield an efficiency
claim. Only successful P2 plus generic-interface readiness can reopen Decision 3.

## Verification

CI validates source freeze, exact public export, generation guards, identity,
accounting/admission, partial failure retention, batch/order functionality,
diagnostic degeneration/NaN/Inf/coverage faults, model-free evidence replay,
first-attempt exclusivity, and all prior P0 tensor/archive contracts.
CI uses synthetic logits/receipts and downloads no Gemma weights. No synthetic
fixture is a P1 observation or capability result.
