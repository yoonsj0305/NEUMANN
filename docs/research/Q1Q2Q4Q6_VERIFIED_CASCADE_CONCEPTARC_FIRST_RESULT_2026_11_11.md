# NEUMANN 1 | ConceptARC FIRST: exact elimination PASS, zero-investment cascade FAIL
2026-11-11 | Immutable FIRST receipt | Global Q1–Q7 OPEN

> **CORRECTION 2026-11-11 (same day, after a complete PR search).** The statement that ConceptARC was never used
> in this repository is FALSE. The same 160 tasks at the same commit were opened on 2026-10-22 by PRs #468, #474,
> #478, #480 and #487 (unmerged branches). My earlier search covered commits only and its PR query had errored.
> Consequences: this run was the first for the *merged hybrid / cascade engines*, but NOT a first exposure of the
> corpus to the project, so its capability numbers are not fresh-family (Q6) evidence. H1 (output exactness) and
> H2 (classical speed-up) are equivalence/cost facts and are unaffected. The original text is kept below unchanged.

Pre-registration: [Q1Q2Q4Q6_VERIFIED_CASCADE_CONCEPTARC_PREREG_2026_11_11.md](Q1Q2Q4Q6_VERIFIED_CASCADE_CONCEPTARC_PREREG_2026_11_11.md)
(local commit `66c8430`, made before any ConceptARC blob was fetched; the push
to GitHub was refused with HTTP 403 in this session, so the pre-registration
is **not externally timestamped**. The evaluator refuses to run if any of the
seven registered code files or 160 target blob SHA-1s differ.)
Receipt: `docs/experiments/results/conceptarc_verified_cascade_first.json`
(sha256 `dcf0f8c6…dfb2`, registry `4c5b80d0…2084`).

## Result: one run, 160/160 tasks, 0 errors, 480 test outputs

| Arm (same machine, sequential, caches cleared) | Joint tasks | Test outputs | Search wall |
|---|---:|---:|---:|
| classical only (fast, exact) | 3 | 16 | 2.13 s |
| relational only | 4 | 57 | 18.25 s |
| **hybrid, original code (current production)** | **7** | **71** | **26.64 s** |
| hybrid with exact fast classical (composed) | 7 | 71 | 20.37 s |
| cascade classical→relational (composed) | 6 | 69 | 20.19 s |
| cascade, actual router run | 6 | 69 | 19.95 s |
| 1D source-learned family router | refused 160/160 | — | — |

| Hypothesis | Rule | Outcome |
|---|---|---|
| H1 (Q2) exactness | identical fit lists + candidates 160/160 | **PASS** 160/160 |
| H2 (Q1) elimination | classical original/fast ≥ 2.0 | **PASS** 9.31 s → 2.13 s = **4.38×** |
| H3 (Q2/Q4) iso-capability of routing | cascade ≥ hybrid_fast (joint, per-output) | **FAIL** 6 vs 7, 69 vs 71 |
| H4 (Q4) cost | cascade ≤ 0.60 × hybrid_orig and ≤ hybrid_fast | **FAIL** 0.749 × (and 0.979 × hybrid_fast) |
| H5 (Q6) open-set routing | family router refuses all 160 | PASS (structural) |

The lost task, `FilledNotFilled1`: the classical grammar found two
TRAIN-consistent programs, both wrong; relational was right in 1.2 ms. The
design assumption fixed on development data ("a TRAIN-consistent classical
program is never wrong where relational is right", true on 901 1D tasks) is
falsified on the new author.

## Decisions (as pre-committed, no rerun or retuning on these 160)

1. **Adopt** the exact elimination (`classical_grid_fast.fit_all`) in the
   production `HybridArcGridInventor` and `SourceLearnedGridRouter`. It is
   output-identical on 1,461/1,461 tasks (901 1D-ARC + 400 ARC-1 training +
   160 ConceptARC) and cuts hybrid search 26.64 → 20.37 s (−23.5 %) on
   ConceptARC, 41.70 → 27.84 s (−33 %) on 1D-ARC dev, 58.89 → 33.21 s (−44 %)
   on ARC-1 dev, at identical capability by construction. Scoped Q1 PASS for
   this engine; no memory/energy telemetry, so not a Q5 claim. (Old frozen
   research scripts that pin the SHA of these two files will now refuse to
   rerun — intended; reproduce the receipt from commit `66c8430`.)
2. **Do not adopt** the cascade. After exact elimination it saves only 2 % vs
   hybrid_fast and lost one task. North Star deletion rule: it has not earned
   its place. Code is kept unchanged only so the receipt stays reproducible.
3. The 24.77 s learned family router is also dominated: on its own 1D corpus
   the exact-fast hybrid reaches the same 455/901 that the *best possible
   in-sample* family table reaches, with zero training and open-set coverage.

## The real bottleneck exposed (post-hoc diagnostic, not a test)

Precision of "reproduces every TRAIN pair" as a correctness signal:

| Corpus | relational TRAIN-fit → correct | classical TRAIN-fit → correct |
|---|---:|---:|
| 1D-ARC (opened dev) | 794 → 439 (55 %) | 150 → 150 (100 %) |
| ARC-1 training (opened dev) | 66 → 38 (58 %) | 27 → 25 (93 %) |
| **ConceptARC (new author)** | **65 → 4 (6 %)** | **9 → 3 (33 %)** |

On a new author the engines mostly *fit the demonstrations and generalize
wrongly*. More search speed or routing cannot fix this; Q2/Q3 fail at
**hypothesis selection under few examples**, not at search cost. Also: the
relational engine's 450 ms wall-clock deadline makes its output
machine-speed dependent (±1 task between identical runs).

## Next decision-changing experiment (proposal, not run)

Replace "fits TRAIN" with an oracle-free generalization estimate that is
derivable at test time: leave-one-demonstration-out re-induction (does the
method induced on k−1 demos predict the held-out demo?) plus a description-
length tie-break. Pre-register precision of accepted candidates and joint
capability on a *different* unopened author set; ConceptARC's 160 are now
opened and may only be used as development. Make the relational deadline a
deterministic step budget first so capability is reproducible.

Global Q1–Q7 remain OPEN. Capability 7/160 (4.4 %) is far from frontier
level; this run says nothing about Q7.
