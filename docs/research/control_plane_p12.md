# P1.2 — full-S4 permutation marginalization

Status: preregistered new opened-development revision. Actual Gemma P1.2 is
NOT RUN at publication. P1 and P1.1 first FAILs stay unchanged; development
cannot admit P2 or Decision 3. Fresh validation remains unregistered/unopened.

## What the first P1.1 result establishes

Original ZIP SHA256 `6bdc2cc9435cefd8a3e99d1d0bc3589bd3b6ad84e50be83db877b1dde769e3ec`,
52833 bytes, 36 members. Independent replay confirms complete accounting and
the frozen FAIL / NUMERIC_OR_PERMUTATION_INSTABILITY. The twelve pooled winners
and both Latin-schedule winners agree with the coarse constructed family
pattern after the fact; 7/12 exceed the original centered 0.50-nat schedule
criterion. Numerical batch/order delta is at most 5.960464477539063e-8 nats.
This is a development signal, not executor correctness, cheapest-executor
evidence, answer capability, calibrated confidence or unseen generalization.
The observed collapse is absent on these twelve; universal removal of all
verbalizer effects has not been established.

For CI portability the exact original ZIP bytes are retained as base64 in
`docs/experiments/results/control_plane_p11_first.zip.b64`, not a repacked
archive. Decode, verify whole-archive SHA/size and all member pins, then replay
the unchanged P1.1 contract offline. Runtime P1.2 never opens or reuses these
historical scores. The original uploaded ZIP is immutable.

## Complete group and the limit of the claim

Keep the original frozen Gemma model/revision/artifact/vocabulary, BF16,
Torch2.11.0+cu128, torchvision0.26.0+cu128, transformers5.16.1, Tesla T4,
public views, executor semantics and one-token A/B/C/D codes unchanged.
Explicitly pin audited code IDs 236776/236799/236780/236796 too.

Enumerate all 24 route-index-to-code-index bijections lexicographically. Every
route receives every code six times. The production candidate statistic is
the equal mean of log probabilities over all 24; no map selection, early
stopping, fitting, task-prior calibration or historical score reuse.

The complete mean has no selected Latin subset, and is invariant to consistent
reindexing of the complete group. This is an algebraic fact. It is NOT an
independent empirical test that Gemma is mapping-insensitive. Fixed additive
code priors cancel under the same additive assumption; nonlinear route/code/
problem/configuration effects are marginalized and may bias the full mean.
A stable mean can still choose a wrong or unnecessarily expensive executor.

## A new, nontrivial operational robustness contract

Partition S4 into six disjoint four-map orbits under cyclic code shifts.
Representatives are the lexicographically minimum member of each orbit; the
partition depends only on the group and is frozen before P1.2 scores.
Each orbit is balanced. For each orbit, leave out its four maps and compute a
20-map mean from the other five. All six leave-four-out means are mandatory;
no favorable deletion is selected. They need no extra model forward calls.

Freeze the following gates for every development task:

- numerical batch/unbatched/reversed delta <=0.05 nats;
- full24 margin >0.50 nats (a separation policy, not calibrated confidence);
- all six leave-four-out winners equal the full24 winner;
- largest centered full24-versus-leave-four-out20 score delta <=0.50 nats.

Keep >=2 distinct winners, dominant winner <=10/12 and across-task centered
score range >=0.001 nats. No expected family labels enter the gate.

**This changes the estimand.** P1.1 tested two four-map means against each
other; P1.2 tests sensitivity of a full24 mean to six balanced deletions.
Keeping the numeric value 0.50 does not make these the same test. P1.1 remains
FAIL; a P1.2 PASS can coexist with large original subgroup differences. This
is a redesigned development architecture after observing a failure, not a
confirmatory rescue or proof of permutation-score invariance.

Always report the six orbit means, six leave-four-out means/winners, full
scores/margin, maximum centered orbit-pair delta and per-mapping centered
range. Those interaction diagnostics are not discarded or relabeled zero
when the operational gate passes. Synthetic CI demonstrates both residual
interactions with stable full means and large effects that fail the new gate.

## Complete compute contract

Recompute all 24 prefixes in three modes for all twelve opened tasks:
batch4 (6 forwards), unbatched1 (24), reverse batch4 (6). Exact complete
totals: 432 forwards, 864 input rows, 3456 scoring rows/scored code tokens.
One prefix forward yields all four next-code log probabilities from the full
vocabulary distribution. Labels are not appended/generated; KV caching and
generation remain disabled. Reuse the frozen causal backend and code audit.

Caps: context4096 including one code, evaluated/padded tokens589824 each,
task120000ms, controller540000ms, whole study1800000ms. Row/forward/token and
controller ceilings are scaled by 24/8 relative to P1.1; context/task/study
ceilings stay unchanged. These are new preregistered diagnostic budgets, not
efficiency evidence. No cap may be relaxed after P1.2 scores.

Estimate only: linear mapping-count scaling of the observed P1.1 controller
147784.539878ms gives 443353.619634ms (~7.39min). Assuming unchanged startup
136019.051389ms gives ~579373ms (~9.66min) for the study, excluding bootstrap.
Audit/setup costs need not scale linearly, and execution may differ; measure
all costs again. These estimates neither guarantee admission nor justify an
operational cost win. Larger diagnostic cost is explicitly charged.

Attempted model-input work is counted before every forward. Partial failure
preserves started passes and known work; missing work remains UNKNOWN. Retain
all modes, encoded prefixes, exact costs, wall times and actual peak VRAM.
Whole study includes startup and audit; bootstrap download/setup/log/replay/
packaging costs are separate receipts. Energy/FLOPs/money remain UNKNOWN.

## First-only interface and publication

Model-free source check:
`python -m experiments.control_plane_p12_dev --check-registration`.
Tokenizer-only readiness uses the original processor and ASCII-escaped core
vocabulary hash helper; no weights or task scoring. Actual entry:
`python -m experiments.control_plane_p12_dev --directory NEW --frozen-head SHA`.
The new directory is exclusive; no CPU/generative/model/code fallback.
Model-free replay recomputes full group, all layouts, costs, robustness and
the development-only verdict. It rejects cached-summary and admission drift.

The P1.2-only Kaggle bootstrap is `scripts/control_plane_p12_kaggle.py`. The
published cell pins its immutable tested source commit and SHA256, sets
`NEUMANN_P12_FROZEN_HEAD` to that same exact commit before loading definitions,
then invokes `run()` once. No main/branch URL, alternate model, budget argument
or task override. The bootstrap checks the original CUDA runtime before and
after constrained dependencies, preserves logs/timing, terminates owned
process groups on timeout/interruption, independently replays and packages
even non-PASS attempts. Existing setup/output/checkout/archive blocks reruns.

Output: `NEUMANN_P12_FIRST_EVIDENCE.zip` plus separate archive SHA/size/packaging
receipt. Original bootstrap bytes and all available study files have member
pins. The same verified bootstrap supports evidence-only `--package-existing`
after a hard stop, blocking a live child; it never starts inference. The
filesystem guard cannot prevent manual deletion/another session. Never reset
the first attempt to replace a result. No actual study runs during publication.

After actual development PASS, freeze architecture and register a genuinely
fresh opened validation source/deduplication/checkers/criteria/cost before
seeing any scores. Fresh validation PASS precedes P2 registration. Only P2
and generic-interface PASS can open Decision 3. Q1–Q7 remain globally OPEN.
