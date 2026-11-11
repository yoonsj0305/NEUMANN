# NEUMANN 1 | Pre-registration: exact elimination + zero-investment verified cascade
2026-11-11 | Written and pushed BEFORE any ConceptARC task byte is fetched | Global Q1–Q7 OPEN

## 0. Why this experiment (root cause, not another variant)

The 2026-11-08 source-learned lazy router ([doc](Q3Q4Q6_SOURCE_LEARNED_LAZY_STRATEGY_360_INDEPENDENT_2026_11_08.md))
retained 176/186 of hybrid capability at −42.6 % search time, but **Q4 FAILED**:
24.77 s of source learning exceeded what it saved on 360 new originals
(break-even estimated at ~959 future tasks). It also **cannot route any unseen
concept family** (it raises `unregistered category` by design), so it has no
open-set (Q6) behaviour at all.

Two North-Star rules were not applied:

* *Do not learn what can be derived more cheaply.* Whether an engine found a
  usable program is derivable at test time, oracle-free: its program either
  reproduces every TRAIN pair or not. A family→strategy table is unnecessary.
* *Do not compute what can be eliminated.* The 626-program classical engine is
  called with `max_hits=626`, recomputes every program on every demo from
  scratch, and executes all demos before rejecting. All operators are pure, so
  shared prefixes, duplicate intermediates and post-mismatch demos are
  provably redundant.

## 1. Mechanisms under test (code frozen by SHA in the registry)

1. `neumann1/classical_grid_fast.py::fit_all` — memoized prefix/intermediate
   evaluation + early rejection. Claim: **byte-identical** winners (indices,
   order, adapter kind, colour mapping) to `arc2_meta_grid_reasoner.fit_task(...,
   max_hits=626)`.
2. `neumann1/verified_cascade_grid_router.py::VerifiedCascadeGridRouter` —
   order `(classical, relational)`; stop at the first engine with a
   TRAIN-consistent candidate; otherwise escalate. No family metadata, no
   training, 2-attempt cap. Order fixed from opened development only.

## 2. Development evidence used to fix the design (opened data, NOT evidence)

| Opened corpus | hybrid (orig) | cascade | classical orig→fast | cascade / hybrid wall | exact fit lists |
|---|---:|---:|---:|---:|---:|
| 1D-ARC, 901 (all previously opened) | 455 / 41.70 s | 455 / 24.86 s | 17.33→2.72 s (6.38×) | 0.596 | 901/901 |
| ARC-AGI-1 training, 400 (opened) | 61 / 58.89 s | 62 / 32.79 s | 30.96→5.51 s (5.62×) | 0.557 | 400/400 |

Relational-first ordering lost 16/455 on 1D-ARC (relational over-fits
denoising/fill families where a short classical program is right); hence the
classical-first order. The best possible in-sample family→strategy table on
1D-ARC reaches 455 at 27.55 s — i.e. the cascade matches the *optimistic upper
bound* of any family router with zero training and no family labels.
Known noise: the relational engine has a 450 ms wall deadline, so actual runs
can differ by ±1 task (ARC-1: 60/61/62 across arms).

## 3. Target (single FIRST run)

* `victorvikram/ConceptARC` commit `0e67da6af879e4bad3d7cd3c196e8d551b445725`
  (Moskvichev, Odouard & Mitchell 2023): all **160** `corpus/*/*.json` tasks,
  16 concept groups × 10. Denominator fixed = 160 (errors count as failures).
* Never used in this repository: 0 commits / issues / PRs mention ConceptARC.
* File names and git blob SHA-1s registered from a **blobless** clone in
  `docs/experiments/conceptarc_first_registry.json` before content is fetched.
* Engines see TRAIN pairs + test INPUTS only; test outputs are read by the
  scorer after all candidates of that task are fixed.
* Possible contamination: ConceptARC concepts overlap ARC-1 style; the human
  engineers who wrote the engines have seen ARC-1 tasks. Disclosed.

## 4. Hypotheses and frozen decision rules

| ID | Question | PASS rule |
|---|---|---|
| H1 (Q2) | Is elimination output-exact? | `fit_all` == original full fit list AND same classical candidates on 160/160, 0 errors |
| H2 (Q1) | Does elimination reduce computation? | Σ classical wall original / fast ≥ **2.0** |
| H3 (Q2/Q4) | Does zero-investment routing keep capability? | cascade_composed ≥ hybrid_fast on joint tasks AND per-output (same engine runs, routing is the only difference) |
| H4 (Q4) | Is it cheaper end-to-end (search stage)? | cascade_run wall ≤ **0.60 ×** hybrid_original_run AND ≤ hybrid_fast |
| H5 (Q6) | Open-set routing | frozen family router refuses all 160 while cascade answers (structural) |
| Floor | — | if hybrid_fast solves < 5 tasks, H3/H4 = NOT_EVALUABLE |

Primary capability unit = joint task (one candidate correct on all test
inputs), consistent with prior cohorts; per-test-output reported. Cost = wall
clock of candidate search in one sequential process on one machine, caches
cleared before every arm. Source investment of the cascade = 0 s; of the
lazy router = 24.77 s (and it cannot run here).

## 5. What a PASS would and would NOT mean

PASS = scoped Q1/Q2/Q4 mechanism evidence on one new independent author set:
exact redundant work removed and a learned router replaced by a derivable one.
It does **not** show autonomous invention of representations (Q3), frontier
capability (Q7; ConceptARC frontier models score far higher), complete Q5
accounting (no memory/energy, no CI/setup costs), or broad Q6. Failures are
retained unchanged; no rerun, no retuning on the 160 opened tasks.
