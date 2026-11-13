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

## 6. FORMAL result (168 tasks, first run; frozen `2fd5f3bd…b1f6`; 1 008 / 1 008 jobs, 0 errors)

Record: `docs/experiments/results/q3_active_formal_record.json`; rows `q3_active_formal_rows.jsonl`. Scored by
`research/q3/active_formal_score.py` (written after the freeze and before any formal row was seen; it checks
the freeze hash, the code hashes and the task list hash). D and Dq query-answer logs: identical in 168 / 168.

| Arm | solved | CPU s | queries |
|---|---|---|---|
| A passive | 99 | 1 425 | 0 |
| B random queries | 101 | 2 160 | 10 080 |
| C disagreement queries | 101 | 2 385 | 10 067 |
| Dq = D's queries, no formation | 104 | 2 037 | 9 956 |
| **D state formation** | **115** | 2 473 | 9 956 |
| E = D + learned policy | 116 | 2 462 | 9 954 |

| Comparison | first only / second only | exact McNemar p |
|---|---|---|
| **D vs Dq (formation, same information)** | **12 / 1** | **0.0034** |
| D vs C | 15 / 1 | 0.0005 |
| D vs A | 24 / 8 | 0.0070 |
| Dq vs C | 4 / 1 | 0.375 |
| C vs B | 1 / 1 | 1.0 |
| B vs A | 12 / 10 | 0.83 |
| E vs D | 1 / 0 | 1.0 |

| Verdict (frozen rule) | Result |
|---|---|
| V1 executable method invention: net D − Dq ≥ 10, p < 0.05, ≥ 2 structure classes | **PASS** (net 11, p = 0.0034; list-state 8, scalar-state 3, m ≥ 2: 1) |
| V2 autonomous latent state discovery: ≥ 5 D-only tasks with an m ≥ 2 machine | **FAIL** (1: `prepend-k(k=-2) \| positions`, component w = (3,) derived from an inconsistency) |
| V3 learned discovery policy | **FAIL** (E vs D 1 : 0) |

What the record shows:
* More queries alone do not help (B vs A 12 : 10, C vs B 1 : 1); the same queries without formation help
  little (Dq vs C 4 : 1). The gain is from what D does with the queries: it intervenes on prefixes to make the
  answer's step structure observable, synthesises the step under per-transition supervision, verifies the fold,
  repairs it with localised counterexamples and accepts it only after an independent challenge.
* 11 of the 12 D-only tasks use the answer itself as the state (count-k, has-k, filters composed with maps,
  interleavings); 1 uses a component the system added because two equal states had different successors.
  New latent variables beyond the answer remain rare in this environment, so V2 fails as predicted.
* Cost: at equal queries D uses 21 % more CPU than Dq (2 473 vs 2 037 s); 81 of 168 formation attempts ended at
  the query limit.
* Scope: one independent source (list-routines, transcribed), with developer-chosen compositions; not a new
  independent problem family; no FRESH evaluation. A PASS of V1 is a partial Q3 result at this scope only.

## 7. After the owner's directive "Q3 후속 연구 승인 및 실행 지시" (2026-11-13)

The 168 formal rows, the freeze `2fd5f3bd…b1f6` and the seal are unchanged. Everything in 7.1–7.4 is
development on list-routines (re-tests of tasks already used, including the 168 formal ones); none of it is
counted as an independent result.

### 7.1 V2 bottleneck: where the queries went

* Formal rows (dev reading only): 84 formation attempts ended at the query limit; 128 "counterexample not
  localisable" events led to 102 component additions; 62 of the 84 were list-output tasks.
* Instrumented re-run (each query tagged by purpose: trajectory states / candidate continuation / counterexample
  localisation) on 40 dev tasks with a query-limit machine: 576 / 310 / 117 queries. The dominant pattern
  (25 of 40): the prefix machine with the answer as its only component finds no Update, the candidate check
  spends 4 kinds × 8 prefixes = 32 queries, finds nothing informative, and the suffix machine is left with ~10
  queries.
* In the dev experience the 8-prefix candidate check added 32 components, none of them in an accepted machine;
  the 2-prefix decisive check added 36, 5 of them in accepted machines (all 5 solved).

### 7.2 Changes (each from the evidence above; no criterion changed)

1. Candidate continuations are decided on two decisive prefixes only: two prefixes the current state merges, or
   the two undefined prefixes nearest the definedness boundary; a blocked or invalid answer is skipped.
   A continuation is added only if its two answers differ (new information), never speculatively.
2. Virtual values for undefined components: only where a state is partly undefined (never as wasted rounds of
   a one-component machine); both candidates (below / above every value seen) are compared on the observations
   already made, without a query; they apply to transitions into and out of undefined states and to the
   counterexample search, so a failure at the definedness boundary becomes localisable.
3. Observations, transitions and counterexample points are reused throughout (memoised answers; a new
   component queries only its own values); the purpose of every query is recorded.
4. Tried and rejected (dev evidence, reverted): filling added components on the order-covering trajectories
   only — the saved state queries moved into counterexample localisation and kth-largest(k=3) still exceeded
   the limit.

### 7.3 V3 policy: what is learned, what dev cross-validation rejected

Learned from D's experience on other tasks (5 hash folds; a task never sees a policy fitted on its own fold),
per observable feature bucket of the initial examples: the order of reading directions, the order of
continuation kinds that became components of accepted machines, the most frequent accepted structure,
a formation gate (no accepted machine on ≥ 5 tasks → formation skipped, queries go to the committee) and a
per-machine query allotment (what every accepted machine needed, +25 %).

Dev cross-validation of a first version (E 146 vs D 158, 1 : 13, p = 0.0018) rejected three elements:
* a CPU allotment — synthesis splits its deadline into stages, so a shorter deadline changed what it found even
  where D finished in 0.15 s;
* restricting continuation kinds to those seen in accepted machines — kth-largest and kth-smallest share every
  observable feature and need opposite kinds; a restriction learned from a handful of machines removed the one
  experiment needed;
* query allotments learned from 2–4 machines — they cut formations that needed more.
The frozen version keeps ordering, structure prior and gate, and an allotment only where ≥ 10 accepted machines
support it.

### 7.4 Dev re-tests on list-routines (228 tasks, 60 queries, 30 CPU s; not independent results)

| Code | D solved | m ≥ 2 solves | query-limit machines | other |
|---|---|---|---|---|
| `9883e42` (V2/V3 commit before this section) | 155 | 1 | 101 | |
| `dfff806` virtual values compared without queries, 2-prefix screen + 8-prefix check | 157 | 5 | 106 | |
| `d690d7b` 2-prefix decisive check only | 158 | 4 | 35 | Dq 139 (D : Dq 21 : 2, m ≥ 2 D-only 4); logs identical 228 / 228; first-version E 146 (1 : 13) |
| final (undefined prefixes nearest the boundary first) | 159 | 5 | 34 | revised E 158 (E : D 0 : 1) |

The m ≥ 2 solves are kth-largest(k=2), kth-smallest(k=2), identify-k(k=1) | kth-smallest(k=2) (a component
"answer after appending a value above / below every value seen" = the next order statistic, found by the
decisive check) and prepend-k(k=±2) | positions (a component derived from an inconsistency). kth-…(k=3) finds
the right three-component structure but needs about 60 formation queries; the budget stays at 60.
On this dev set V2's count (4–5) is at or below the frozen threshold of 5, and the revised policy does not beat D.

### 7.5 FRESH data and pre-registration (before any FRESH task was run)

* Sources (`docs/experiments/q3_fresh_registry.json`): MBPP `google-research/google-research@f8d6d14a`
  (`mbpp/mbpp.jsonl`, sha256 `ccf64cea…2a9f`; repository Apache-2.0, dataset CC-BY-4.0) and HumanEval
  `openai/human-eval@b9453e8f` (`data/HumanEval.jsonl.gz`, sha256 `b796127e…979ef`, MIT).
* Selection (mechanical, `research/q3/fresh/registry.py`, decided before any task text or outcome was read):
  T1 every test assert is `f(<int list literal>) == <int | bool | int list literal>` with one positional
  argument (MBPP test_list + challenge_test_list; HumanEval: every assert of `check` on `candidate`, ≥ 2);
  T2 the reference passes a static audit (imports from a fixed whitelist, no forbidden names, no dunder
  attributes). 111 selected (84 MBPP, 27 HumanEval), 0 excluded by T2; registry sha256 `25724ce8…30d`.
  T3 (at run time, before any arm): a reference that fails its own published tests is reported, not run.
* Isolation (`research/q3/fresh/sandbox.py`): `unshare -n` (no network interface), `python3 -I -S`,
  RLIMIT_CPU 60 s, RLIMIT_AS 1 GiB, RLIMIT_FSIZE 0, RLIMIT_NOFILE 16, empty working directory and environment,
  restricted builtins, import whitelist, 1 s alarm per call.
* Observation protocol (`research/q3/fresh/env_fresh.py`): initial = the published tests, then generated inputs
  answered by the reference, up to 8; hidden = 10 further generated inputs, never queryable; generator elements
  from the published input values ± 1, lengths in [min − 1, max + 1], seed = sha256 of the task id.
* Arms A (passive), D, Dq (exact replay of D's queries), E (D + the policy frozen in
  `docs/experiments/q3_fresh_policy.json`, fitted on the final dev D rows); 60 queries, 30 CPU s.
* Criteria and predictions: `docs/experiments/q3_fresh_freeze.json` (the same V1 / V2 / V3 rules as the formal
  run; tasks solved only through a new latent component are reported separately). The single run follows
  the commit of the freeze.
