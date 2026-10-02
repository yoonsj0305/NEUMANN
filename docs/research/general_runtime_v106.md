# v0.0.106 General NEUMANN Runtime-0

The 2026-10-02 user decision supersedes the previous next-action order:
v106 opened runtime development → v107 sealed Fresh General Holdout →
v108 Frontier Gap Pilot-1 → v109 actual Edge Reality Gate.
The Frozen North Star and Q1–Q7 remain fixed. All global gates remain OPEN.

## Fixed core and matched experiment

No fitting, structural fine-tuning, paid API or frontier execution.
Use public `google/gemma-4-E2B-it`, revision
`3e22461f65e89153144f8adb70e3b8c2cc9845a7`, CPU BF16, greedy decoding,
weights in eval/inference mode. Record downloaded artifact/config/tokenizer hashes,
actual parameter count, dependency versions and before/after mutation audit.
Google's E2B denotes 2.3B effective parameters, 5.1B including embeddings;
it is not a 2B-total-memory model. Published BF16 memory estimates are not
our device measurements. This runner is a development CPU, not an Edge pass.

| Arm | Strategy | Eligible tools / common rights |
|---|---|---|
| B0 | Direct, no reasoning channel | Same pool, strategy elects no tool |
| B1 | Reasoning then final | Same pool, strategy elects no tool |
| B2 | One tool then final | Same pool, at most one selected tool |
| B3 | Iterative tools, verification and correction | Full same pool; certified batch plan allowed |
| N | Required representation, elimination, executor, original check, repair | Full same pool; certified batch plan allowed |

The same loaded weights/precision/processor, 4096 complete-sequence context,
512 complete-query generated tokens (including thinking), 192 tokens/call,
6 model calls, 6 tool calls, 120s/query and 2s/Python invocation apply.
Deadlines stop at generation-step boundaries; a CPU forward can overrun, in which
case the retained receipt fails the complete-query wall gate. Startup and
download are separately measured and charged in cold single-query totals.
There is no silent context truncation or free retry. Total latency includes
representation, routing, failed attempts, subprocesses and original checks.
Token counts are a proxy only. FLOPs, energy, money, thermal and VRAM remain
unavailable; no conversion from tokens or latency is invented.

## Bounded Runtime-0 scope

Shared JSON action protocol, not a tuned native function-calling baseline.
The small core selects representations and computations. A deterministic tool
certifies exact original-field retention and drops only marked background and
unused arithmetic bindings. No general semantic-compression theorem is claimed.
Math uses bounded exact rational expressions, coding a pure resource-capped
Python subset, and planning finite integer CSP. Coding validation is finite
original-spec test validity, not a proof for every input. Original checkers
receive the original obligations, not authority delegated to a reduced IR.
Verifier returns only pass/fail; hidden test vectors/solutions never reach core.
Both B3 and N can execute a certified plan without extra narration calls.

The first registered run contains three OPENED author-constructed interface
controls, one per family, five arms = fifteen serial shuffled observations.
They diagnose real model/protocol/tool integration; they are intentionally not
hard general tasks, a sealed holdout, a statistical Pareto gate or Q7 evidence.
Model-load failure, unsupported dependency, timeout, invalid response and
verification failure must be retained without rerunning this first attempt.
Contract tests use synthetic adapters and cannot be promoted to model evidence.

## Subsequent admission

Build nontrivial opened development families before freezing architecture.
Compare N against the strongest measured matched small-model frontier,
including B3, across capability and complete resource curves. A favorable
accuracy alone does not pass. Declare measured Pareto coordinates and leave
unmeasured axes open. Then freeze new licensed task sources/checkers and the
architecture before a single v107 holdout. No frontier solutions before small/N
results and full traces are frozen. v108 may then measure actual gap recovery.
v109 alone introduces actual device RAM/latency/energy/network-off constraints;
no quantization or kernel optimization in this version.

## Concurrent mechanism scope

Basis-pursuit was admitted for frozen-checkpoint transfer by v104's privileged
ceiling. Use both existing EXPAND4 seeds 100001/100002 on newly registered
original A,b,c, without oracle support/dual or any refit. This subordinate study
is M106_BP, not v107. Assignment remains stopped for lack of Oracle headroom.
Preserve all historical archives and every failed cost/capability observation.

Official sources checked 2026-10-02:
https://ai.google.dev/gemma/docs/core
https://ai.google.dev/gemma/docs/core/model_card_4
https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4
https://huggingface.co/api/models/google/gemma-4-E2B-it
