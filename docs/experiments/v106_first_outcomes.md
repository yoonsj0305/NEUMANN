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
