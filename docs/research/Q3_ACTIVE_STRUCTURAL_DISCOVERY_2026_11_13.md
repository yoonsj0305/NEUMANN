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

### 7.6 FRESH result (single run; freeze `132053fa…33eb` committed in `94d2a6a` before the run)

111 registered; `mbpp/38` reference inconsistent under T3 (its reference returns a float, the published test an
int) and not run; 110 run; 442 / 442 jobs. Errors: `humaneval/114` in D and E (see defects), counted as unsolved
for D / E and solved for the rivals, as frozen. D and Dq query-answer logs identical in 109 / 109.
Record: `docs/experiments/results/q3_fresh_record.json`; seal: `docs/experiments/q3_fresh_seal.json`.

| Arm | solved (of 110) | CPU s | queries |
|---|---|---|---|
| A passive | 26 | 1 963 | 0 |
| Dq = D's queries, no formation | 25 | 2 619 | 6 468 |
| **D state formation** | **38** | 2 712 | 6 468 |
| E = D + frozen learned policy | 38 | 2 710 | 6 470 |

| Comparison | first only / second only | exact McNemar p |
|---|---|---|
| **D vs Dq** | **14 / 1** | **0.00098** |
| D vs A | 15 / 3 | 0.0075 |
| E vs D | 0 / 0 | 1.0 |
| Dq vs A | 3 / 4 | 1.0 |

| Verdict (frozen rule) | Result |
|---|---|
| V1 executable method invention: net D − Dq ≥ 10, p < 0.05, ≥ 2 structure classes | **PASS** on FRESH (net 13, p = 0.00098; list-state 7, scalar-state 7) |
| V2 latent state discovery: ≥ 5 D-only tasks with an m ≥ 2 machine | **FAIL** (0) |
| Solved only through a new latent component (m ≥ 2, neither A nor Dq solves) | D 0, E 0 |
| V3 learned discovery policy | **FAIL** (E vs D 0 : 0; CPU 2 710 vs 2 712 s) |

What the record shows:
* The 14 D-only tasks are MBPP tasks whose method D invented as a fold over the input from its own
  interventions: 7 sorting tasks (`mbpp/54, 71, 141, 152, 428, 516, 940`: counting, comb, pancake, merge,
  shell, radix, heap sort) solved by the same discovered list-state step — insert the element into the sorted
  answer of the prefix (insertion sort), whatever algorithm the reference uses — and 7 scalar folds (sums and
  counts under sign / parity conditions, first even / odd element: `mbpp/66, 133, 221, 329, 697, 807, 870`).
  All 14 use the answer itself as the state (m = 1).
* No FRESH task was solved through a new latent component. 62 formation attempts added components; one m = 2
  machine (`mbpp/45`, gcd of an array; component "answer after appending 18") reproduced every initial example,
  passed the 3-input challenge and was adopted, and failed the hidden test: an overfit machine, not a latent
  discovery. Another (`mbpp/670`) was rejected by the challenge. The prediction "V2 more likely FAIL" held.
* The frozen policy changed nothing measurable (E = D task by task); the prediction "V3 more likely FAIL" held.
* Query use in D's formation on FRESH: states 2 983, candidate continuations 527, localisation 490; 33 of 176
  formation attempts ended at the query limit.

Defects found in the FRESH run (not repaired in the counted run):
* F9 `humaneval/114` (inputs down to −9 999 999 999 999 999): the order-covering trajectories were drawn from
  `range(min, max)` of the observed values, which exhausted memory. Repaired after the run (trajectory values
  drawn from the observed values and their neighbours when the range is large); the repair is not counted.
* F10 an overfit m = 2 machine passed fold verification and the 3-input challenge (`mbpp/45`): the challenge
  inputs come from a generic generator (0–16) unlike the task's large values; recorded, not repaired in this
  record.

Scope: V1 now holds on an independent FRESH source (MBPP + HumanEval, authors' references run in isolation) at
60 queries / 30 CPU s, at an absolute level of 38 / 110. V2 and V3 have failed twice (formal, FRESH).
Q3 as a whole and Q6 remain OPEN.

## 8. Directive "Q3 Autonomous Structural Invention Breakthrough" (2026-11-14) — DEVELOPMENT ONLY

Everything below is development. The FRESH tasks were opened by the single run of section 7; here they are
re-used only for error analysis and development, never as independent evidence. The sealed FORMAL and FRESH
records are unchanged.

### 8.1 Phase A — the bottleneck, separated (classified from the sealed FRESH D rows and the final dev rows)

| D unsolved, by cause | FRESH (71) | list-routines dev (69) |
|---|---|---|
| state conflict detected, then query limit | 26 (+1 with challenge rejection) | 1 |
| Update synthesis failure | 30 (+3 with conflict / rejection) | 31 (+3) |
| query limit without conflict | 6 | 14 |
| undefined domain / unlocalisable counterexample | 3 | 15 (+1) |
| wrong adoption (adopted, hidden test failed) | 2 | 3 |

The decisive finding: on 29 FRESH tasks D *did* detect that the answer is not a sufficient state (two
prefixes with the same answer and different futures), but it could only add continuation components, each a
query-measured value that carries one bit when the answer is boolean. The latent quantity these tasks need —
the last element (is-sorted, monotone trends, adjacent products), the index parity (odd / even position rules),
a counter or a running sum — would take a component per threshold. That is a representation limit, not a
budget limit: continuation states measure the latent variable through the oracle instead of computing it.

### 8.2 Phase B — counterexample-driven state invention (`neumann1/active.py`)

* **Invented variables.** Candidate latent variables are folds `h' = G(h, e)` from an initial value, where `G`
  is every small program of the existing generic substrate (integer and list valued; 809 after removing
  programs that ignore the input or settle on a constant), the same list for every task; computing one costs
  no query.
* **Admission from the contradiction.** On a state conflict (or when no Update exists, or a counterexample
  cannot be localised) a candidate is admissible only if, with `h` added, every observed transition becomes a
  function of (state, element) — it explains the conflict instead of adding a dimension. Candidates that induce
  the same partition of the observed prefixes are collapsed; they are tried in Occam order (size of `G`), at
  most 8: Update synthesis on the extended state, then the fold on every initial example. The simplest whose
  Update exists and leaves at most a quarter of the examples failing is adopted; the next one is kept as the
  rival hypothesis.
* **Failure classification and repair.** A counterexample is localised to its first wrong step (transition
  error: the point is added and the Update re-synthesised); a wrong start of an invented variable is an
  initial-state error (alternative starts are rival hypotheses); a variable that cannot be repaired is a wrong
  structural hypothesis: it is rejected and the next admissible one is invented.
* **Experiments from hypotheses.** Before a formed machine is returned, up to 3 self-test queries are chosen
  where it disagrees with its closest rivals — the same machine from another start, other case trees equally
  consistent with every transition, the runner-up variable — searched over task-distribution inputs and their
  generic edits (sorted, reversed, element replaced / deleted / duplicated). A disagreement observed is a
  counterexample for the repair loop, never a reason to accept.
* **Boolean steps** get case trees (no boolean if-node existed); every case-tree branch must explain at least
  two observed transitions (all wrongly adopted machines in dev special-cased one value).
* **F10.** Self-test, challenge and discrimination inputs come from the task's own observed values, their
  neighbours, duplicates and lengths, with a boundary element in one input of five, never of a sign the task
  was not observed with.

### 8.3 Phase B dev result (60 queries, 30 CPU s, same harness)

| | old D (sealed FRESH run) | new D (dev) |
|---|---|---|
| FRESH tasks solved (of 110) | 38 | 45 |
| D-only vs Dq replaying the same queries | 14 : 1 | 22 : 0 (Dq re-run on the new queries, p = 4.8e-7) |
| D-only with an m ≥ 2 machine | 0 | 8 |
| of which through an invented variable | 0 | 7 (`humaneval/62, 121, 126`, `mbpp/567, 680, 775, 790`; `humaneval/85` via a continuation) |
| adopted but wrong | 2 (`mbpp/45, 635`) | 1 (`mbpp/68`) |
| list-routines dev solved / m ≥ 2 solves | 159 / 5 | 159 / 13 |
| CPU s / queries (FRESH) | 2 712 / 6 468 | 2 753 / 6 520 |

Invented variables in these machines: `h' = e` (last element), `h' = −h` from 1 (index parity), `h' = h + 1`
(position counter). Example (`humaneval/121`, sum of odd elements at even positions): the answer-only state
showed equal (state, element) pairs with different successors; 28 of 809 candidates made the transitions a
function; the simplest, `h' = −h` from 1, was adopted; Update `(if (eq h (mod e 2)) (add s e) s)`; 22 queries.
Caveat: `mbpp/775` passed the hidden test with an alternating-parity rule that is not the reference's semantics
on every input.

### 8.4 Phase C — learned discovery policy (dev cross-validation, separated by author lineage)

Policy fitted on list-routines + HumanEval rows, tested on MBPP; fitted on list-routines + MBPP, tested on
HumanEval. E = invented-variable credit learned from verified outcomes (+1 variable of a machine that passed the
independent challenge and the hidden test, −1 adopted-but-wrong, −0.25 rejected by its own repair loop; a
variable tried but not needed gets nothing); B = experience cache (every adopted variable, outcomes ignored).
Both try their positive variables first, then the 8 cheapest. Run 1 also kept the earlier policy elements
(direction / kind order, formation allotments); run 2 ("acc only") removes them, so E and B differ from D only
in the invented-variable prior.

| (110 FRESH tasks, dev) | solved | vs D (only / D-only) | vs B |
|---|---|---|---|
| D | 45 | — | — |
| E learned, run 1 / run 2 | 42 / 42 | 0 : 3 / 0 : 3 | 2 : 1 / 0 : 1 |
| B cache, run 1 / run 2 | 41 / 43 | 1 : 5 / 1 : 3 | — |

**Phase C: not passed.** The learned prior produced no additional solve and lost three HumanEval latent tasks
(`humaneval/85, 121, 126`) in both runs: variables credited on other tasks (last element, position counter) are
tried before the simplest admissible variable of the new task, are "nearly consistent", get adopted, and lead
to an Update the repair loop cannot finish within the budget. The one exclusive gain is the cache's
(`humaneval/3`, running sum), which the learned credit had suppressed because the same variable had been
part of a wrong machine elsewhere — credit assignment cannot separate a wrong variable from a wrong Update with
this little experience (8 verified latent episodes). Because Phase C did not pass, no new independent evaluation
was pre-registered (directive §7, Phase D).

### 8.5 The two physical-learning principles (review only, no experiment)

* State skipping: the invented variables are its discrete counterpart in query space — the latent state is
  computed from the input, never measured through the oracle, and only the states where hypotheses disagree
  are observed. SS-DFA itself needs a differentiable forward map and a fixed random feedback path; a discrete
  program search has neither, so it was not applied. Credit from the final verified outcome to the discovery
  action is what 8.4 tested; with this little experience it did not help.
* Single map: every invented variable is one shared small map `G` iterated over the input, generated from one
  substrate for every task. No neural single-map generator was built; no independent effect was measured.

### 8.6 Verdicts after this directive

| | Verdict |
|---|---|
| V1 executable method invention | PASS retained (FORMAL and FRESH, sealed) |
| V2 latent state discovery | development PASS (Phase B criterion met on opened tasks: 0 → 8 D-only m ≥ 2, wrong adoptions 2 → 1); **no independent result** — the sealed FRESH V2 FAIL stands |
| V3 learned discovery policy | development FAIL (Phase C): 0 additional solves |
| Q3 overall | OPEN |
| Q6 | OPEN (separate work) |

## 9. Multi-variable state invention and a stage-separated discovery policy (2026-11-14) — DEVELOPMENT ONLY

Same conditions (60 queries, 30 CPU s, classical passive fallback). Opened FRESH tasks and list-routines are
re-used for development; repeated optimisation on them is not independent evidence; no new FRESH was opened.

### 9.1 Audit of `invent()` (code `29b9a66`)

1. A candidate set had to be ONE variable that explained every observed contradiction; a structure needing two
   variables (maximum and minimum, first even and first odd) could not be admitted at all.
2. The candidate class had no case-split fold: the cost-ordered enumeration filled its 700 slots with
   arithmetic on constants, so running maxima / minima, conditional sums and first-of-a-kind were absent.
3. With no contradiction observed (`mbpp/588` max − min), admission was vacuous and the Occam order tried
   arithmetic junk first.
4. Invention ran only after the answer-state loop had used ~95 % of the formation CPU (0.4 s of 18 s left).

### 9.2 Mechanism (one general mechanism; no operator or solver added)

* Contradictions as a set cover: each candidate explains the contradictions whose two prefixes it separates;
  admissible sets are single variables explaining all, or pairs whose explained sets cover all.
* Moore readout: the answer as R(h1[, h2]) of invented variables only. The data are every observed prefix and
  example; sets cover all pairs of points with different answers; R is checked exactly against the first
  small programs of the substrate, and pairs are completed by meet-in-the-middle joins through the inverses of
  the substrate's own add / sub / mul (the partner variable's values are computed, then looked up).
* Case-split folds `h' = if P(h, e) then A else B` generated from the substrate's predicates and elementary
  terms (757 → 2 549 candidates); identity starts preferred (G(z, e) = e on observed values).
* Representation change on stagnation (fold failing on half the examples without improvement over two rounds);
  invention CPU capped at 30 % of what is left per call; per-candidate caches shared by all calls.
* Boolean readout search bounded (50 sets, 30 readouts) to keep chance fits unlikely; readout self-tests probe
  the other starts of each variable.

### 9.3 Result (dev)

| FRESH re-used for dev (110) | value |
|---|---|
| D solved / Dq on the same queries | 45 / 23 (22 : 0, p = 4.8e-7) |
| D-only with m ≥ 2 | 8 (`humaneval/3, 62, 85`, `mbpp/476, 567, 588, 680, 790`) |
| **solved with two invented variables, D-only vs Dq** | **3**: `mbpp/588` max − min = readout `h2 − h1` of `h1' = min(h1, e)`, `h2' = max(h2, e)`; `mbpp/476` max + min = `h1 + h2`; `humaneval/3` running balance (the adopted pair contains an unused parity variable: the minimal state is the sum alone) |
| single-variable ablation (`MULTI = False`) on those 3 | 0 solved |
| adopted but wrong | 3 (`mbpp/19, 46, 68`) — one more than the sealed old D (2) |
| list-routines dev | 157 (previous dev 159); lost `count-k(k=10)`, `prepend-k(k=-2) | positions`, `identify-k(k=1) | kth-smallest(k=2)`, `replace-all-k-with-n | sum`; gained 2; m ≥ 2 solves 23 |

### 9.4 V3: stage-separated discovery policy (dev cross-validation by author lineage)

The per-variable experience prior (8.4) was removed. `DiscoveryPolicy` holds two logistic models over the
evidence the current task itself produced (number of contradictions, why invention was called, how finely a set
splits the observed prefixes, description length, structural class of each variable, answer type; no variable
identity): synthesis credit P(Update / readout exists) from 9 407 tried sets of other tasks, repair credit
P(verified machine | adopted, failing fraction) from 124 adopted sets (32 verified). The learned order is
interleaved with D's order, so D's own first choices are always tried.

| (110, dev) | solved | vs D (only / D-only) |
|---|---|---|
| D | 45 | — |
| E selection only | 45 | 2 : 2 (`humaneval/126`, `mbpp/775` / `humaneval/3`, `humaneval/85`), p = 1.0 |
| E selection + learned adoption | 43 | 1 : 3, p = 0.63 |

**Phase C: not passed.** No net additional solve; the two E-only tasks are CPU-borderline tasks that D solved in
earlier dev runs, so they cannot be attributed to the policy; learned adoption lost three. The repair-stage model
has 32 positive episodes; its features cannot separate a wrong variable from a wrong Update.

### 9.5 Verdicts

V1 PASS retained (sealed). V2: multi-variable invention works in development (3 tasks, all failing without it),
with one more wrong adoption and a 2-task list-routines regression; no independent result. V3: development FAIL.
Q3 overall OPEN; Q6 OPEN (not modified).

## 10. Structural knowledge and autonomous invention (2026-11-14, directive "Q3 Structural Knowledge") — DEVELOPMENT ONLY

Same conditions (60 queries, 30 CPU s, classical fallback, Dq replay); opened FRESH and list-routines re-used;
no new data opened; Q6 untouched.

### 10.1 Phase A — regressions, wrong adoptions, minimal state

* Regressions (`count-k(k=10)`, `prepend-k(k=-2) | positions`, `identify-k(k=1) | kth-smallest(k=2)`,
  `replace-all-k-with-n | sum`): in the 159-version each was solved by repair or the continuation route
  (6–16 CPU s); in the 157-version invention ran first at "counterexample not localisable" / "no Update",
  used 14–18 of the 18 formation seconds, and in `identify-k | kth-smallest` adopted a junk pair that passed
  the fold and failed the challenge. Cause: CPU allocation, not the representation. Change: all invention
  calls of one machine share 40 % of its CPU.
* Wrong adoptions: `mbpp/46` (boolean readout of a hash-like variable) and `mbpp/19` — wrong STATE (both need
  a set of seen values, which no candidate expresses); `mbpp/68` — wrong UPDATE (constant special cases) on
  plausible variables; `mbpp/476` (earlier run) — wrong START. Changes: (a) state-sufficiency refutation —
  two inputs whose machines end in the same state must have the same answer; a pair is searched among
  task-distribution inputs and their edits and asked (≤ 2 queries); different answers reject the
  representation, not an Update; (b) a readout counterexample explained by another START of the same variables
  switches the start instead of rejecting the variables (this had cost `mbpp/588`).
* Minimal state: every machine with ≥ 2 invented variables drops each in turn and re-synthesises; a variable
  stays only if the machine without it cannot reproduce every observation. `humaneval/3`: the parity variable
  is removed (the machine is the running sum alone); `mbpp/476`, `mbpp/588`: neither of min / max can be
  removed (no readout of the other alone) — within this substrate, not a claim of mathematical minimality.

| dev | 157-version | now |
|---|---|---|
| FRESH-dev D / Dq | 45 / 23 | 45 / 24 (21 : 0) |
| two invented variables, both required (removal fails) | 2 (+1 with an unused variable) | 2: `mbpp/476`, `mbpp/588` |
| adopted but wrong | 3 | 2 (`humaneval/40`, `mbpp/68`); state refutations fired on 4 tasks |
| list-routines (159-version = 159) | 157 | 158: still lost the four above and `rotate-k(k=1) | identify-geq-k(k=2)`; gained 4 |

Gate A: the multi-variable structures are preserved and wrong adoptions no longer exceed the sealed D (2);
the four named list-routines regressions are NOT recovered (net −1 against the 159-version). Not passed.

### 10.2 Phase B — Structural Knowledge Units (minimal, `active_dev.structural_knowledge`)

A unit is made only from a machine of another task that passed the independent challenge and the hidden test and
uses invented variables. It reuses what the run already records: observed contradiction (why invention was
called, how many contradictions), structural relation (the variable definitions), representation, transition,
readout, preconditions, counterexamples, verification, discovery procedure (the event log), minimality,
cost. On a new task (`_apply_knowledge`) a unit is a hypothesis: its relation is rebuilt from the current
candidates with values recomputed on THIS task's observations; arm E proposes it only if it explains the
current contradictions (or separates every pair of differently answered points); transition and readout are
re-synthesised on the current data, never copied; D's own order follows unchanged.

### 10.3 Phases C/D — causal comparison (lineage split: units from list-routines + the other FRESH source)

| arm (110 FRESH-dev) | solved | vs D (only / D-only) | adopted but wrong |
|---|---|---|---|
| D | 45 | — | 2 |
| E: relevance-gated reconstruction | 47 | 3 : 1, p = 0.63 (`humaneval/121, 126`, `mbpp/690` / `mbpp/670`) | 1 |
| B: verified memory, no relevance check (= E-no-relevance here) | 47 | identical to E | 1 |
| ES: knowledge-task link shuffled | 42 | 0 : 3 (`mbpp/567, 670, 790`) | 2 |

Relevance check: 1 709 applications passed, 2 013 were refused as not explaining the current contradictions,
1 490 relations could not be formed from this task's candidates.

* Gate B (E beyond D AND beyond B, causally from relational learning): **not passed**. E = B task for task: the
  relevance gate changed nothing measurable. E vs D 3 : 1 is not significant; `humaneval/121` and `126` are
  CPU-borderline tasks that D solved in earlier dev runs.
* Gate C (negative transfer): knowledge linked at random costs three tasks (ES); with real links neither E nor B
  lost more than one task — wrong links harm, but this run cannot show that the relevance judgement is what
  prevents it, because B (no judgement) did not lose either.
* Gate D (invention beyond reuse): not shown — no E-only solve is attributable to a reconstructed unit.
* What was NOT done: a learned policy over discovery ACTIONS (explore / apply / test applicability / invent /
  combine / repair / prune / reject) with counterfactual credit. The stage-separated policy of section 9 remains
  the only learned element; it failed there.

### 10.4 Verdicts

Full regression suite: 1148 passed, 53 skipped (code `189112a`).

V1 PASS (sealed). V2: development only; Gate A not passed (list-routines regressions). V3: development FAIL
(Gate B). Q3 overall OPEN. Q6 OPEN (Codex). No independent evaluation was pre-registered.

## 11. Learning discovery ACTIONS from counterfactual pairs (2026-11-14) — DEVELOPMENT ONLY

Same conditions; opened FRESH and list-routines re-used; nothing new opened; Q6 untouched.

* **Instability (P0-A).** `humaneval/121, 126`, `mbpp/680`, the four list-routines regressions and
  `rotate-k(k=1) | identify-geq-k(k=2)`, 3 repeats each on the same code and seed: identical outcomes every time.
  These are deterministic failures of a discovery decision, not CPU-boundary luck: each fails right after a
  branch point ("no progress", "counterexample not localisable", a contradiction) where invention ran first.
* **Decision made explicit (`choose`).** At every branch point the machine either invents new state now or
  keeps repairing the current representation (localise, continuation, virtual values); the other route remains
  the fallback. Each decision is logged with its evidence (why, contradictions, components, invented
  variables, answer type, failing fraction, CPU and queries left, rounds, undefined region). D = invent first;
  the counterfactual arm runs repair first at every branch point on the same task, seed and budget.
* **Learning (V3).** A pair whose outcomes differ labels the first decision's evidence; logistic policy, acting only
  when |p − 0.5| > 0.15, otherwise D's decision stands. Author-lineage split: MBPP policy from list-routines +
  HumanEval pairs (5 pairs), HumanEval policy from list-routines + MBPP pairs (7 pairs).

| FRESH-dev (110) | solved | CPU s / queries | adopted but wrong |
|---|---|---|---|
| D (invent first) | 45 | 2 758 / 6 516 | 2 |
| D-repair (repair first) | 43 | 2 758 / 6 524 | 0 |
| best fixed action per task (oracle union) | 47 | — | — |
| **E (learned action policy)** | **47** | 2 757 / 6 512 | 2 |
| B (verified-structure cache) | 48 | 2 747 / 6 508 | 1 |
| Dq | 24 | 2 648 / 6 516 | 0 |

* D and D-repair split 4 : 2 (`humaneval/3`, `mbpp/567, 588, 670` need invention first; `humaneval/121`,
  `mbpp/775` need repair first). E solved all six: E vs D 2 : 0 (`humaneval/121` with decisions
  repair, repair, invent; `mbpp/775`), E vs D-repair 4 : 0. Without the learned policy (either fixed action)
  E's two extra solves disappear: a causal contribution of the learned decision, on deterministic tasks.
* Not significant (2 : 0, p = 0.5); the policy was fitted on 5 and 7 pairs; `mbpp/775` is the task whose
  hidden-test pass is not the reference semantics (section 8.3).
* **E vs B: 2 : 3** (E: `mbpp/670, 775`; B: `humaneval/85, 126`, `mbpp/690`). Gate B (E beyond D AND B) not passed.
* Gate D (new invention): E's extra solves come from choosing between two existing routes, not from a new
  structure. Not shown.
* List-routines (Gate A): invent-first 158 (still loses `count-k(k=10)`, `prepend-k(k=-2) | positions`,
  `replace-all-k-with-n | sum`, `rotate-k(k=1) | identify-geq-k(k=2)`); repair-first 160 (recovers
  `count-k(k=10)` and more, loses `pow-k(k=3) | index-k(k=2)`). The named regressions are not all recovered by
  either action; E was not run on list-routines. Not passed.
* SKU audit (P0-B, not changed): `preconditions` holds only the answer type and a constant flag,
  `counterexamples` is always empty, `discovery_procedure` is the raw event log without the decision that
  mattered, and equivalent variable definitions are separate units — the unit stores programs more than
  relations. The decision log of this section is the first record of WHICH decision led to the solve.

Verdicts: V1 PASS (sealed). V2 development; Gate A not passed. V3: first causal evidence that a learned
discovery DECISION adds solves over D on deterministic tasks (2 : 0, development, not significant), but not over
the verified-structure cache B: development FAIL (Gate B). Q3 OPEN; Q6 OPEN. No independent evaluation.
Full regression: 1148 passed, 53 skipped (code `96f5ea6`).

## 12. Decision-level counterfactuals and the factorial comparison (2026-11-14) — DEVELOPMENT ONLY

* **Audit of section 11's labels.** They were task-level: two whole runs under one fixed action, attributed to the
  first decision. Replaced by decision-level replay (`ACTION_SCHEDULE`, code `ea528c6`): the same task, seed and
  budget re-run with exactly ONE decision (index 0 or 1) switched to repair. 346 replays; the decisions before the
  switch were identical in 251 (the evidence includes the CPU fraction left, which varies with timing — a
  limitation of the identity check, recorded). Only **7** decisions changed the outcome: repair better at
  `count-k(k=10)`#0, `prepend-k(k=-2) | positions`#0, `humaneval/85`#1, `mbpp/775`#0; invention better at
  `humaneval/3`#1, `mbpp/670`#0, `pow-k(k=3) | index-k(k=2)`#1. Two of the list-routines regressions are thus
  located exactly: inventing at the first branch point blocks the repair route that solved them (Phase E).
* **Factorial arms** (FRESH-dev 110, lineage split; policy from 5 outcome-changing decisions per fold; knowledge
  units from the other lineages; `mbpp/775` counted as a semantic failure):

| arm | knowledge | learned decisions | solved (semantic) | adopted but wrong |
|---|---|---|---|---|
| D | – | – | 45 | 2 |
| D-repair | – | fixed repair | 42 | 0 |
| B | cache | – | 48 | 1 |
| E-action (decision-level) | – | yes | 45 (vs D 1 : 1) | 2 |
| E-joint | relevant | yes | 48 | 1 |
| E-joint-ablated | relevant | – | 47 | 1 |

* E-joint = B task for task (0 : 0); E-joint vs E-action 4 : 1; E-joint vs its ablation 1 : 0 (`humaneval/85`).
  The decision-level policy did not reproduce section 11's 2 : 0 (E-action 45 vs D 45). Every gain of E-joint is
  also B's: the verified-structure cache, not the learned discovery decision, carries it.
* Answer to the directive's question, in development: NEUMANN currently remembers WHAT it found (the cache
  helps); evidence that it learned HOW to discover is limited to one non-significant, non-reproduced comparison.
  The signal itself is scarce — 7 outcome-changing decisions in 346.

Verdicts: V1 PASS (sealed). V2 development (two-variable cases preserved; list-routines regressions located,
not recovered). V3 FAIL. Q3 OPEN. Q6 OPEN. Full regression: 1148 passed, 53 skipped. Seals intact.
