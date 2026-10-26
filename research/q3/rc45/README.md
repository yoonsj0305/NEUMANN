# NEUMANN 1 RC45 · External model-proposed operators and falsified zero-shot reuse

**Date:** 2026-10-26. **RESEARCH DRAFT ONLY.** Never merge this as a
global Q3/Q4/Q5/Q6/Q7 PASS. This is a GPT-6 **CHAT ASSISTANT** experiment,
not an NEUMANN own-weight learned-core experiment.

## Why this was necessary
RC44 had one correctly authored model-proposed external ARC-AGI-2 public
TRAINING operator and **zero source admission on eleven other public
training problems**. The immediate question was whether multiple
first-proposed operators produce real additional source/test correctness,
and whether a task-ID-free operator bank actually transfers to independent
external tasks without new model reasoning.

## Pinned external study and order of access

Upstream: arcprize/ARC-AGI-2 commit
`f3283f727488ad98fe575ea6a5ac981e4a188e49`.
Corpus selection: all `data/training/*.json` filenames lexicographically
ordered, only original JSON byte sizes <= 2500. Cohorts are positions
**25–36**, **37–48**, **49–60**. All 36 official original Git blob SHA1s
and source-only frozen predictions are checked into separate JSON files.
No ARC-AGI-2 official evaluation/private data accessed.

The model was shown only `train.input/train.output` and `test.input`
for the first two cohorts when authoring operators. We committed each
operator program and its corresponding **FIRST** ungraded test predictions
to GitHub **before** independently checking original test gold.

Immutable Git histories:
- First program and first predictions: `cb4000e5`, `89d40dc2`.
- Second cohort baseline transfer freeze: `777a8b70` (9 fixed operators).
- Second cohort adapted operators and first predictions:
  `aef16562`, `b978c31c`.
- Third cohort untouched 17-op reuse freeze: `805e220e`
  (dispatcher code freeze: `8bfc94c7`).

These commits are not rewritten by the subsequent grade or report.

## Observed results

| First-prediction stage | Public training tasks | Exact tasks | Unknown/abstain | Wrong submitted test grids |
| --- | ---: | ---: | ---: | ---: |
| GPT-6 authored first 9 fixed program semantics | 12 | **9** | 3 | **0** |
| Those 9 operators, no task-ID route, unchanged on fresh 12 | 12 | 0 | **12** | 0 |
| GPT-6 then authored 8 task-conditioned new programs on the same second 12 | 12 | **8** | 4 | **0** |
| All 17 unchanged operators, no task-ID route on fresh third 12 | 12 | 0 | **12** | 0 |

Across the **first two development cohorts**: 17/24 solved tasks,
18/18 submitted exact test grids, 733/733 grid output cells, **zero wrong
submitted**; 7 tasks abstained. Do **not** call this 17/24 a prospective
generalization or independent small-model result. New programs were written
AFTER reading each task's public source examples.

**Decisive adverse result:** both prospective source-only zero-retraining
cross-task reuse experiments were **0/12**. The 17-op library did NOT
generalize to the third cohort. Its 12 public test gold outputs have **NOT**
been opened by the experiment. A source admission is never a universal
equivalence proof.

## Scientific value and controls

This is direct evidence that current GPT-6 chat reasoning can propose
multiple executable rule programs that reproduce withheld *within-task*
test grids after source-only authoring and first-prediction freeze. It
also **falsifies the claim** that the current task-conditioned operator bank
is already reusable on broad unseen external problems.

The proposed functions remain executable classic code, but ID labels on
their first creation reflect task authorship. Only `dispatcher.mjs` and
`dispatch17.mjs` try *all* operators, match original task source IO, require
a single consensual test prediction, and abstain otherwise. Thus no task
ID is used for the future-selection comparison; the first two authored
cohorts WERE task-specific program-writing demonstrations.

**Limits, not loopholes:** ARC public training data could be contained in
GPT-6 pretraining; a stronger classical solver could find equal programs;
17/24 is source-conditioned; prospective reuse is 0/12; output tests
do not prove all-length correctness; no NEUMANN own-weight model ran; no
neural inference price, FLOP, energy or strong-classic all-in comparator
was measured. No Q3, Q4, Q5, Q6, Q7 global PASS is justified.

## Reproduce

Requires Node >=18 and internet access to github.com. No npm packages.
Every original task raw blob is verified against its independent Git SHA1.

```sh
node research/q3/rc45/verify.mjs
node research/q3/rc45/verify.mjs --online
```

Offline form checks frozen-receipt structure only, not claims of gold
accuracy. `--online` independently reconstructs original public ARC
tasks, verifies every Git blob SHA1 and FIRST immutable prediction, scores
the first two cohorts, and checks all twelve third-cohort source abstentions
without scoring their gold.

**Next permissible mechanism experiment:** genuinely learn/generate a
task-agnostic *parameterized* representation from source data, preregister
an independent prospective corpus with data exposure controls, compare
strong classical inductors and charge ALL proposal/search/verification
cost. Do not run more toy neural fits just to turn a scoped label green.
