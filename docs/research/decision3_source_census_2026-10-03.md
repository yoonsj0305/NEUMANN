# Decision-3 Source Census — 2026-10-03

Purpose: identify candidate sealed/unseen evaluation sources without opening
task content before Decision 2 admits Decision 3.

## Frozen model context

The frozen Decision-2 core is `google/gemma-4-E2B-it`, revision
`3e22461f65e89153144f8adb70e3b8c2cc9845a7`. Hugging Face metadata inspected
during this preparation reports the model repository updated on 2026-07-20.

That date is a public artifact timestamp, **not a claimed training cutoff**.

## Candidate assessment

| Source | Metadata observed | Decision-3 role | Current admission |
|---|---|---|---|
| HLE-Rolling | gated, MIT, updated 2026-09-17; dynamic HLE fork with harder held-out replacements | strongest current text-reasoning unseen candidate | candidate only; use only ids absent from frozen base-HLE ids; generic QA interface required |
| HLE-Diamond | gated, MIT, released 2026-09-22; 1,000 questions, 500 reasoning + 500 knowledge | contamination-control / hard general benchmark | not sufficient by release date alone because it is refined from broader HLE collection |
| GPQA | gated, CC-BY-4.0; expert science QA; original benchmark 2023 | checker/verifier sanity only | not primary unseen evidence for a 2026 model |
| ARC-AGI-2 | 1,000 public train, 120 public eval plus semi-private and fully-private tiers | very strong private generalization candidate | deferred: frozen AM1 lacks grid/ARC interface |
| LiveCodeBench | release-date-tagged coding with hidden tests | temporal coding candidate | wait: inspected official release metadata did not establish post-2026-07-20 tasks in the frozen official path |

## Why HLE-Rolling is not automatically opened

The project must first prove Decision 2. After that, a source adapter may compare
stable ids against a frozen base-HLE id set without emitting question/answer
content. Only metadata-surviving ids can enter deterministic selection.

If the frozen architecture cannot process the resulting new family without a
post-D2 semantic/executor change, **do not load the rows**. Return to opened
matched validation instead.

## Why HLE-Diamond is not treated as guaranteed unseen

HLE-Diamond was released later than the current frozen Gemma artifact, which is
useful provenance. But it is explicitly described as a refined subset of the
HLE question collection. A later benchmark release timestamp alone therefore
does not prove that every underlying question was absent from earlier public or
private corpora.

## Data-handling boundary

For gated HLE/GPQA sources:

- do not print or commit task text,
- do not re-host raw rows,
- preserve source/canary terms,
- keep raw selected evidence local/private,
- publish only permitted aggregate metrics, ids/hashes when allowed, and
  non-content provenance.

This census itself contains no task rows.
