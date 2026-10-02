# v0.0.106 first outcomes and dependency readiness

Runtime-0 was merged in PR #119 at main `5bae33350da01552cb4eb7b18a7c1d7ac7e717c0`. Its first two registered runs are retained without replacement. All global Q1–Q7 remain OPEN.

## Mechanism: frozen basis-pursuit transfer STOP

Actions run 36996124336 retained 256 observations (64 warmups before 192 timed observations) on 16 new constructed basis-pursuit originals. Both existing checkpoints preserved original capability throughout, but neither met the preregistered complete-cost gate. Independent witness and cost replay passed without inference, fitting or solving.

| k | EXPAND4 seed 100001 / Direct | EXPAND4 seed 100002 / Direct |
|---|---:|---:|
| 8 | 2.102555 | 2.048507 |
| 16 | 1.632854 | 1.645032 |
| 32 | 1.550543 | 1.548401 |
| 64 | 1.570273 | 1.606257 |

These are medians of complete amortized cost ratios, including discovery, execution, original verification, retry/fallback, transport, cold startup and prior training amortized at Q=10000. Direct is the optimistic best per-source Native/IPM diagnostic envelope. Both decisions are **STOP_FROZEN_TRANSFER_NO_REFIT**. No rerun, refitting, reseeding or threshold rescue follows this negative transfer. This constructed LP result establishes neither natural problem transfer nor general Q5/Q6 closure.

First archive: `91da2b10f72657e01b12885c8ffd1fec732419cd`. Original terminal and report remain authoritative.

## General: first processor startup INCOMPLETE

Actions run 36996120155 downloaded the anonymous revision-pinned public model snapshot, then failed while importing Gemma4Processor. **Zero of fifteen observations ran; no model forward or solution was observed.** This is a startup defect, not fifteen incorrect solutions. First archive `30e615b42093f25a3f2cc70aea2aea15c6992031` is retained byte for byte.

The pinned Transformers 5.10.1 Gemma4 image processor imports `torchvision.transforms.v2.functional`, including when the task input is text. The repair installs the matching CPU Torch 2.14.0 and torchvision 0.29.0, imports the class before snapshot download, and checks the pinned processor without downloading weights or performing a forward pass. Failure reports now retain a traceback; identity receipts include torchvision and the effective tokenizer vocabulary hash.

## Separately registered Boot2 opened controls

Boot2 uses three distinct, fully opened arithmetic/coding/planning controls and the same frozen revision, precision, prompts, tools, context and hard budgets. It is a dependency readiness diagnostic after a zero-forward failure, not a repeat of the original first study, sealed holdout, training experiment or capability gate. Its manifest is published before execution and its first bytes are retained even on failure. The 41258.945662 ms prior failed startup is explicitly included in cumulative cold-query accounting.

Boot2 is armed only after this repair and both first archives pass CI and merge. Processor-only CI performs no neural inference; retained BP CI replays original witnesses and costs without refitting or fresh solves. New archive pins protect every original raw file, including gzip inputs, events, reports, terminals and setup failures.

No paid API or frontier call is made. Development must next demonstrate useful capability and resource gains against the strongest matched B0/B1/B2/B3 baseline before v0.0.107 fresh holdout. v0.0.108 is the later frontier gap pilot; v0.0.109 is the actual edge gate. Toy interface controls cannot close those gates.

## Boot2 first actual model outcome: readiness FAILED

Run36998148198 completed all15 opened controls and the frozen-core audit, with no training or frontier calls. Workflow SUCCESS means execution and retention completed; **every arm was0/3 and no tool invocation occurred in any query**. The NEUMANN structural loop was therefore not exercised. General capability gate remains NOT_EVALUATED; Q1–Q7 remain OPEN.

| Arm | Accepted | Actual output tokens, all3 queries | Median runtime-query latency (seconds) |
|---|---:|---:|---:|
| B0 Direct | 0/3 | 290 | 39.315 |
| B1 reasoning | 0/3 | 576 | 91.167 |
| B2 one tool | 0/3 | 751 | 120.240 |
| B3 iterative tools | 0/3 | 725 | 120.320 |
| N required representation | 0/3 | 706 | 120.413 |

The9 B2/B3/N queries retained unfinished thought output, rejected it as an action, restarted and reached the120-second complete query limit without a tool call. All3 B1 queries ended at the192-token per-call cutoff inside thought output, although the shared query token cap was512. B0 coding emitted an answer-only object, missing the strict action field; B0 planning emitted a truncated tool-call string despite the direct restriction; B0 math emitted final answer11, rejected by the original exact checker (26). These are protocol/budget and one actual arithmetic failure, not evidence that a functioning NEUMANN architecture lost a hard capability contest. No failed receipt is converted into success.

Core: public Gemma E2B revision3e22461f65e89153144f8adb70e3b8c2cc9845a7, CPU BF16, actual5104297504 parameters. Weights/files/tensor-version audit unchanged; artifact digestbf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66. Startup69236.473193ms; prior failed startup41258.945662ms is charged in the reported cold-query scenarios. Whole study1573892.639070ms. Peak parent-process RSS7057285120bytes is cumulative, not whole-device or per-arm peak memory. FLOPs, energy, money, thermal and VRAM remain unavailable. Latency above is the retained runtime-query interval; archival/controller overhead is reflected in whole-study time, not a closed Q5 per-query cost claim.

Frozen executor79ff7e5721b61c35929a4d88a4362f711936568c; first archivec57fd111b249d442e63113ae223801b2987e7b82. Every raw query, actual token ID, failed action, manifest, core audit, terminal and setup record is protected by first-byte pins. Independent replay checks original accepted-answer obligations and receipt/accounting consistency without neural generation, fitting or fresh CSP solving; zero original successes remain zero.

Next development must correct action framing and bounded reasoning before another model study or hard capability evaluation. Preserve all first outcomes, keep the old runtime/checker authoritative for their replay, and preregister any revised opened diagnostic separately. Do not open v107 holdout or spend on frontier references on this evidence.
