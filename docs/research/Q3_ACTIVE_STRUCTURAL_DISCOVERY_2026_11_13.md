# NEUMANN 1 | Q3 Active Structural Discovery — environment, mechanism, probe
2026-11-13 | Development (SOURCE probe split only). No formal run. No FRESH data. Global Q1–Q7 OPEN.

Owner's decision of 2026-11-13: option (b), a queryable SOURCE environment, conditionally approved. All earlier
verdicts (SECOND FAIL, THIRD scoped PASS, iterations 1–4 FAIL, Stage A FAIL, formation/learning FAIL) unchanged.

## 1. Environment (`research/q3/env_listroutines.py`)

* Routines transcribed from lucasem/list-routines (commit 23c8f099, Racket; an independent author's
  interactive dataset for the DreamCoder list domain): evaluate, input constraint, input generator and the
  author's example parameters for 47 list-input routines. Running the original Racket code was refused by the
  session's safety classifier; transcription was used instead (risk: transcription errors; the four
  integer-input routines are excluded because a query on an integer is an answer).
* Tasks: 108 single-routine instances and 120 two-routine compositions (fixed seed; composing is the
  developer's choice, disclosed). Split by a salted hash of the task name, fixed before any run: probe 60,
  formal 168. The formal split has not been run.
* Agent interface: 8 initial examples; queries on valid inputs, charged; inputs equal to a hidden test input
  are blocked and charged; nothing else is exposed. Hidden test: 10 generated inputs.

## 2. Mechanism (`neumann1/active.py`)

| Arm | Definition |
|---|---|
| A | passive core (discovery pipeline with the latent configuration R2) |
| B | A + random queries |
| C | A + committee-disagreement queries (no state formation) |
| Dq | D's queries, answers used as examples, solved passively (D without formation) |
| D | (1) output-as-state hypotheses (prefix / suffix fold) tested by interventions on prefixes / suffixes; (2) if they fail: **latent state from distinguishing experiments** (Myhill–Nerode): state(u) = (f(u), f(u·w)) for generic continuations w (above / below every seen value, first element repeated); the hidden component is made observable by the agent's own experiment; both component steps are synthesised under per-transition supervision (enumeration with probe-refined equivalence, or a per-transition case cover); a candidate machine that fails an initial example is a counterexample: the first wrong step is localised by binary search over prefixes and added; (3) reserved queries test the formed machine on fresh inputs |
| E | D + discovery policy from other folds (not run in this probe) |

Prior art: Angluin's L* and register-automata learning (hidden state from distinguishing experiments), CEGIS.
Claimed as new here only: making the latent component's step learnable by per-transition factorisation.

## 3. Probe (60 tasks; budgets changed on probe evidence before any formal run: 40 queries, 30 CPU s, all arms)

| Arm | solved | fit | wrong fit | CPU s | queries |
|---|---|---|---|---|---|
| A | 31 | 45 | 14 | 556 | 0 |
| Dq | 33 | 36 | 3 | 1 046 | 1 736 |
| D | 31 | 35 | 4 | 1 093 | 1 822 |

D vs Dq: 0 : 2. D vs A: 3 : 3. A latent state was formed on **no** probe task within the budget.

Development observations (self-checks, not evidence): the latent mechanism forms the correct two-component
machine for count-k (latent and answer steps found after 4 counterexample-localised experiments) and
identifies the hidden component "maximum so far" for 2nd-largest from the experiment "append a value above
everything seen", converging from 11 to 3 failing examples before the budget runs out.

## 4. Why it adds nothing here

* Of the 25 probe tasks no arm solves, about 4 need a hidden ordinal state (k-th largest / smallest, a count
  inside a composition). The rest are element-wise maps with large values (x^4, 2^x), modular rotations,
  positions, and compositions of maps and filters, for which the bottleneck is the passive core, not hidden
  state.
* On the hidden-state tasks the mechanism needs more experiments and CPU than the budget leaves after the
  output-state stage and the fallback; 30 s and 40 queries were not enough in the pipeline (standalone with
  ~60 queries it converges on count-k).
* Extra examples from structured queries (Dq) help the passive core slightly (33 vs 31), which by the
  owner's rule is not evidence of structural intelligence.

No formal criterion was registered and the formal split was not opened: the probe gives no reason to expect a
PASS.

## 5. After the owner's directive "Q3 Autonomous Structural Invention" (2026-11-13)

### 5.1 Code audit (verified causes, each with its reproduction in the session record)

| # | Defect | Verified by | Fix |
|---|---|---|---|
| F1 | Dq re-ran D's formation and did not receive D's fallback queries (D 1 822 vs Dq 1 736 queries) | code + probe counts | Dq replays D's exact query inputs; query-answer logs hash-identical (60 / 60) |
| F2 | a machine was adopted without validation when the budget was exhausted (count-k(k=3) wrong machine adopted) | code (`ok_all` stayed true) | independent challenge on 3 fresh inputs; no queries left = not accepted |
| F3 | an adopted wrong machine replaced a correct passive solution | probe (3 tasks) | machine vs passive decided by a discriminating query where they disagree |
| F4 | output-state stage consumed the budget before latent search | probe (`tried: []`) | one formation path: components grown on demand |
| F5 | equivalence pruning hid the correct step after a rejected candidate | reproduction (max) | probe-refined equivalence |
| F6 | a case cover returned only its first tree | reproduction (2nd largest) | case trees enumerated in cost order |
| F7 | counterexample localisation failed inside undefined prefixes | reproduction (2nd smallest) | treated as a representation signal: add an informative continuation |
| F8 | list-valued components had lost the cell construction in the unification | probe (42 / 60 at the query limit) | restored |

### 5.2 Mechanism after the fixes

S(u) = (f(u·w) for w in W), W = [()] at first; a component is added only when (i) two equal (state, element)
pairs have different successors (continuation e·w_j, Rivest–Schapire), or (ii) no Update fits / a
counterexample is hidden in undefined prefixes and a grammar continuation carries information the state lacks
(not a function of the state on observed prefixes, or defined where the state is not). Update per component
by per-transition synthesis (list components: cell construction); fold verified on every initial example;
counterexamples localised by binary search; independent challenge; discriminating query against the passive
solution.

### 5.3 Probe after the fixes (60 tasks, 60 queries, 30 CPU s, every arm)

| Arm | solved | wrong fit | CPU s | queries |
|---|---|---|---|---|
| A | 31 | 14 | 557 | 0 |
| Dq | 35 | 0 | 840 | 3 545 |
| D | **41** | 2 | 1 005 | 3 545 |
| E | 40 | 2 | 1 016 | 3 547 |

D vs Dq 7 : 1 (p = 0.070); D vs A 12 : 2 (p = 0.013); E vs D 0 : 1. Of the 7 D-only tasks, 1 uses a discovered
latent component (2nd largest: W = [(), (16,)], i.e. "answer after appending a value above everything" =
running maximum); 6 are output-as-state machines (counted separately, as the directive requires).
Formation outcomes: 28 machines passed the challenge, 25 attempts ended at the query limit, 7 had answers
undefined on the designed trajectories.

### 5.4 Formal pre-registration (frozen in `docs/experiments/q3_active_formal_freeze.json` before the run)

168 formal tasks (never run), every arm with 60 queries and 30 CPU s; arms A, B, C, D, Dq (replay), E.

| ID | PASS rule |
|---|---|
| V1 executable method invention | net D-only minus Dq-only ≥ 10, exact McNemar p < 0.05, D-only tasks from ≥ 2 structure classes |
| V2 autonomous latent state discovery | ≥ 5 formal tasks solved by D with an accepted m ≥ 2 machine that Dq does not solve |
| V3 learned discovery policy | E-only ≥ 5 vs D with p < 0.05, or solved(E) ≥ solved(D) at ≤ 0.7 × CPU |

Predictions written before the run: V1 uncertain; V2 expected FAIL (few hidden-state tasks); V3 expected FAIL.
This environment is from one independent source (list-routines); it is not a new independent problem family.
