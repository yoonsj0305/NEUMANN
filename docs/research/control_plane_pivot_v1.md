# Non-Generative Control Plane — Pivot v1

Stage: P0 contracts. P1/P2 are NOT ARMED. Decision 2's first verdict stays FAIL.
All global Q1–Q7 remain OPEN; Decision 3 sealed data remains closed.

## One hypothesis

Low-entropy executor/evidence decisions can be selected from teacher-forced
fixed candidates without waiting for a generated reasoning/action envelope.
This removes dependence on free generation for control, not the computation
required to score candidates. Capability and resource improvement are untested.

The retained first GPU attempt has 36 observations, all three arms 0/12,
72/72 model calls at 256 output tokens, 0 final-channel observations and 0 tool
calls. No generation deadline was hit. Do not rescue/relabel/rerun that verdict.
The uploaded 78 original JSON files are now retained byte-identically under
`docs/experiments/results/am1_decision2_first_original/`, with SHA256/byte pins
and model-free replay. The earlier report copies remain unchanged.

## P0 implementation

- `neumann1/control_plane_v1.py`: fixed `DIRECT/ARITHMETIC/CSP/PYTHON`
  candidates, KEEP–DROP evidence ordering, cost-aware selection, monotone
  one-public-field expansion, bounded executor retries and original verification.
- `neumann1/control_plane_scoring_v1.py`: teacher-forced, length-normalized
  candidate log likelihood with explicit prefix/label token boundaries.
- `attach_frozen_gemma(core)`: attach the existing artifact-audited frozen
  Gemma core. No download, fitting, generation or alternate model is performed.
- `experiments/control_plane_p0_v1.py`: independently replay original first
  failure bytes, order, core/trace identity, token receipts and arm aggregates.

The tensor backend calls forward, never `generate`. Causal position `p-1+t`
scores forced candidate token `t` after prefix length `p`. Padding and prompt
tokens are excluded from the candidate mean. Right-padded candidate batches
must equal independent unbatched scores. All scoring prompts expose only the
explicit `instruction/public` view; task IDs/family/private answers are rejected
at the controller boundary.

Route preference is `mean_logprob - lambda * estimated_ms`, where lambda has
units nats/ms. All estimates require declared provenance, finite nonnegative
values, and future preregistration before measured P2 outcomes. They are not
actual latency. TOOL has the same candidates and scoring backend but uses full
input and no cost bias. NEUMANN scores KEEP/DROP on the full public view once,
orders fields by the difference, and tests ascending evidence prefixes. The
original instruction is always retained. Ties use frozen route order and
lexicographic field order. These scores are not calibrated semantic relevance
probabilities, and label-length normalization does not remove label bias.

At each prefix, failed routes try remaining fixed candidates; only after those
fail is one more evidence field added. The first accepted original answer stops
all subsequent computation. No verifier answer/rationale enters scoring.
The controller receives only a boolean original-verifier result. A verifier
exception, malformed receipt, identity drift or deadline cannot produce PASS.
Evidence ranking is advisory. Successful verification of one answer is not a
proof that the selected subset preserves every possible solution.

## Interface and generation boundaries

Executor and verifier callbacks are explicit injection points in P0. There is
no family-specific answer lookup, generated JSON action, or hidden task-family
router. An executor receives only the selected public values, original
instruction, remaining deadline and remaining generation/tool allowances.
It must return charged receipts even for failed routes. Original verification
is bound to the complete original task by the caller and never weakened to the
selected subset. Existing AM1 runtimes/checkers are unchanged.

DIRECT must use a normal typed answer path; no action envelope or tool-selection
label is required from it. Actual normal-answer decoding, bounded coding-source
generation, existing executor bridges and representative original-checker
integration remain P2 admission work. P0's injected synthetic callbacks do not
establish those real paths or a stronger baseline. The tensor adapter's actual
Gemma/processor compatibility must be checked in P1, before any capability run.

## Accounting and degraded mode

P0 fixture defaults are 4096 context tokens, 32768 evaluated tokens, 256 score
rows, 32 forward calls, 32 evidence fields, 32 attempts, 512 generated answer
tokens, 4 generative model calls, 16 tool calls and 120000 ms complete wall.
These are development contract defaults, NOT a frozen P2 experiment budget.
Matched P2 caps must be preregistered separately for all arms.

Admission checks occur before scoring. No silent truncation. Prompt+forced-label
tokens, scored label tokens, padded tokens, forward calls, answer-generation
tokens/model calls, tool calls, attempts and complete wall are distinct receipts.
Zero generated controller tokens does not mean zero computation. Relevance
scoring repeats the original context for every field and may cost more than
Direct; failed subset attempts and original checks also count.

If scoring fails partway, retained STARTED receipts mark accounting incomplete;
known attempted tensor forwards/padded tokens remain charged. Admitted token
counts on incomplete batches are not evidence of all rows actually evaluated.
A synchronous GPU forward cannot be preempted by this Python deadline; overrun
work is retained and never accepted. A future isolated runner must enforce any
hard process bound. FLOPs, energy and money remain UNKNOWN, not inferred from
token counts. Full controller wall includes tokenization, scoring, execution and
verification; study startup/load/packaging remain future runner obligations.

Degraded mode exhausts bounded alternative routes/evidence, including DIRECT,
then returns a failed/incomplete receipt. There is no paid frontier fallback,
automatic model scaling, hidden fitting, or favorable rerun.

## Stage sequence and gates

P0 PASS requires pure control contracts, independent causal-scoring reference,
synthetic tensor padding/multitoken/batch tests, frozen-identity/budget/negative
verifier tests, and original first-failure byte replay. All are model-free or
explicitly synthetic logits fixtures. P0 closes no capability question.

P1 is the next separately registered GPU diagnostic: route scoring only on
the existing 12 OPENED tasks, same frozen model/precision. No task solving,
executor invocation, capability comparison, sealed rows or frontier calls.
Freeze template/label IDs, batching, budgets and route-readiness criteria before
running. Retain all scores, margins, exact forward/token/time/memory receipts,
first errors and pre/post artifact identity. Compare batch/unbatched numerical
behavior on a bounded diagnostic sample. Inspect label/order bias on opened
data; do not infer reliable routing from the mere existence of finite scores.

Only after P1 can P2 be registered: DIRECT normal answers versus full-input TOOL
versus minimal-evidence/cost-aware NEUMANN, with identical frozen weights,
eligible tools, context and total resource caps, independent original checking,
and a working nonzero representative Direct admission control. Freeze the
capability/resource PASS rule before P2, including refusal of a zero/zero
"efficiency win". A new P2 verdict cannot rewrite the original Decision-2 FAIL.

Decision 3 remains blocked until a new opened matched gate passes AND the
task-specific-interface blocker is resolved before sealed content is seen.

## Primary API reference

The Hugging Face Gemma4 forward interface exposes input IDs, attention masks,
causal logits and `logits_to_keep` for indexed score positions:
https://huggingface.co/docs/transformers/model_doc/gemma4
The actual installed version and template must be recorded by P1; documentation
compatibility is not a substitute for an actual pinned-model forward receipt.
