# P1.1 — Permutation-Marginalized Coded Router

Status: new architecture, preregistered opened-development diagnostic. Real
P1.1 has NOT run. P1 FAIL stays immutable; P2 and Decision 3 remain blocked.
Original 12 P1 views are development only. No fresh validation rows exist yet.

## Problem and change

The first P1 completed 12/12 with unchanged frozen weights, finite scores and
zero batch/order deltas, but chose ARITHMETIC on all 12. The raw route strings
have unequal tokenization. Context-sensitive movement is a diagnostic clue,
not proof of routing correctness. Do not reuse P1 as confirmatory evidence.

P1.1 binds explicit executor contracts to four fixed code strings A/B/C/D.
These are opaque identifiers, not assumed equiprobable or semantically neutral.
Their scores come from the final prefix distribution, without generated text.
Actual original tokenizer vocabulary SHA256 is checked, and each string must
encode to one distinct non-special token with exact decode. CI performs this
tokenizer-only readiness check without downloading any model weights or reading
tasks. Runtime repeats it against the original core tokenizer before scoring.
Readiness uses the same Gemma4Processor as the original core and its exact
vocabulary hash function (JSON with ASCII Unicode escaping). Public-view/trace
hashes use a different Unicode serialization; those digests must not be reused
for the frozen vocabulary. Processor assets are downloaded, model weights are
not. CI's CPU vision dependency is only for that processor import.
Numeric IDs are determined by the frozen vocabulary and encoding rule; no
response-dependent code search, fallback code selection or fitted task prior.

## Balanced assignment, not a label rename

Routes retain fixed semantics: normal neural answer reasoning; exact scalar
arithmetic with stated values; finite constraints with stated domains; bounded
general Python algorithm implementation/execution. No executor runs here.
Each legend is sorted by code. Thus each route occupies every code and legend
position once per schedule. Two disjoint four-map Latin-square schedules use
base assignments (0,1,2,3) and (0,2,1,3), each shifted modulo four. All eight
maps are always evaluated, not a favorable subset of the full 24 permutations.

For route r and mapping pi, the forced single-token score is
`log P(code[pi(r)] | public_problem, explicit_legend_pi)`.
The route statistic is its mean over all eight maps. Four observations per
schedule are also averaged independently and compared after row centering.
No across-task calibration, learned head, family labels, private answers or
post-hoc P1 mean subtraction enter this statistic.

If scores have the additive form `utility(r,x) + bias(code) - Z(x,pi)`, a
balanced schedule gives every route the same mean code bias and normalizer.
Relative route scores then recover relative utilities. This is an algebraic
property under an assumption, not evidence that real Gemma follows that model.
Code/problem and code/route interactions can survive; different schedules and
fresh validation test that limitation. CI explicitly injects such interactions.

## Compute and accounting

One prefix forward supplies all four code probabilities. The first forced
token is scored from the last causal prefix position; feeding four separate
copies of the same prefix or appending a token is unnecessary. Log-softmax uses
the full vocabulary. Right padding and the union of required causal positions
are explicit. KV caching and generation are disabled; eval/frozen parameters
are checked before and after. A counted generation tripwire guards both APIs.

For every development task: eight legends in batch4 (2 forwards), unbatched1
(8 forwards), and reversed-prefix-order batch4 (2 forwards). This is 12 forwards
and 24 actual input rows per task. Four code targets per row give 96 scoring
rows/tokens per task. Complete 12-task totals: 144 forwards, 288 input rows,
1152 scoring rows and 1152 scored tokens. These are controller costs, not solved
answers. Model input tokens count the evaluated prefix once; output code tokens
are scored but not appended or generated. This token definition differs from
P1's repeated full prefix-plus-label rows and cannot establish a cost advantage.

Frozen caps: context including the forced code 4096, total evaluated/padded
tokens 196608 each, task wall120000ms, controller wall180000ms, complete study
wall1800000ms. Controller wall includes preparation, scoring, receipts and final
core audit after startup. Study wall includes source admission, model load and
initial audits. These are preregistered operational limits, not efficiency
claims. Energy, FLOPs and money remain UNKNOWN. All modes retain encoded
prefixes, code IDs, scores, margins, layout, forwards, input/scored/padded tokens,
complete wall and actual peak allocated VRAM. Model-input attempts are charged
before forwards. Partial failure retains STARTED passes and known attempted
cost; missing partial work remains UNKNOWN and cannot pass accounting.

## Development gate and boundaries

Requirements: all original 12 views complete, unchanged original BF16/Tesla T4
model/revision/artifacts/runtime, zero generation/tools, complete cost/caps and
finite probabilities. Frozen additional requirements:

- batch/unbatched/reversed-layout maximum delta <=0.05 nats;
- centered route-score delta between the two schedules <=0.50 nats;
- pooled margin >0.50 nats requires the same winner in both schedules;
- >=2 winning routes; no route >10/12;
- across-task centered route-score range >=0.001 nats.

The numeric allowances are policy choices fixed before any P1.1 scores, not
empirically established correctness thresholds. Development PASS is diagnostic
only. It always reports P2=false, Decision3=false, no general capability result
and no global Q closure. Degeneration or interactions require a separate
registered revision; never replace a failed first outcome.

Fresh validation remains UNREGISTERED/UNOPENED. After actual development PASS,
freeze the architecture and then preregister a new opened validation source,
stable task identities and deduplication against the original P1/development
items, input hashes, original independent checkers, route diagnostic criteria
and complete cost before viewing scores. Hold architecture fixed through its
first fresh result. Do not merely reseed templates from the old twelve and
call them unseen. A fresh validation PASS is required before registering P2.
No validation PASS or admission is synthesized from development receipts.

Then P2 compares operational strongest normal DIRECT / full-input TOOL /
minimal-evidence NEUMANN with the same core, tools and declared limits, original
answer checks and complete failed/retry/verification cost. Successful P2 plus
generic-interface readiness is required for Decision 3. No frontier or sealed
rows are accessed here. No new training or edge optimization.

## First evidence and operation

PR133 preserves the P1 FAIL summary. The original 32 ZIP members are now retained
byte-for-byte under `docs/experiments/results/control_plane_p1_first`, with
size/SHA256 pins and independent original receipt replay in CI. Original ZIP
SHA256: `38d489dde092e86eea6a9f2276bc15fcfa574c463e18ececf161037dfd95cb38`.

`python -m experiments.control_plane_p11_dev --check-registration` is model-free.
`--tokenizer-readiness` loads only the pinned tokenizer. The actual development
entry point requires a separately supplied frozen commit and a new exclusive
first directory. This PR does not run or automatically arm GPU execution.
Save partial output too; do not change directory to replace an unfavorable run.
`python -m experiments.control_plane_p11_replay --directory PATH` recomputes
hashes, all layouts, costs, aggregates and the development-only verdict without
model inference. Source/code audit mismatch degrades to a preserved incomplete
attempt; no generative, CPU, alternate-code or alternate-model fallback.

CI: synthetic additive-prior cancellation and residual-interaction faults,
balanced/duplicate map admission, causal next-token reference, ragged batch
equivalence, frozen parameter/generation guards, cost caps, partial failures,
development-only gates, receipt tampering and original P1 FAIL replay; plus
actual pinned tokenizer single-token readiness. No synthetic test is a Gemma
result, fresh validation result or capability evidence.
