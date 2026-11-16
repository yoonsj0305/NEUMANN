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

## 13. Phase A of "Information-Driven Structural Invention": counterfactual reliability (2026-11-14) — DEVELOPMENT ONLY

* **Erratum to section 12.** "346 replays, 251 identical" was read from `cf.jsonl` while it was still being
  written (the wait had timed out); the complete file has 357 pairs (all unique, none failed or duplicated) and
  259 CPU-inclusive identical replays; 7 outcome-changing decisions either way. The JSON record was right; the
  section-12 text is kept as written and corrected here.
* **Identity split.** All 357 pairs were replayed again recording the decision evidence before the switched
  decision. Logical identity (why, contradictions, components, invented variables, answer type, failing
  fraction, rounds, undefined region, queries left — everything except the CPU fraction): **352 / 357**
  (195 of them index-0 pairs, identical by construction). The CPU fraction alone differed by at most 0.24 of the
  formation budget; it is now recorded separately (`cpu_left_diff`) instead of deciding identity. The 5 logically
  different pairs (all at index 1, list-routines) are excluded from causal labels.
* **Outcome-changing decisions on logically identical states: 7** — repair better: `count-k(k=10)`#0,
  `prepend-k(k=-2) | positions`#0, `mbpp/775`#0 (semantic mismatch, not a valid label); invention better:
  `humaneval/3`#0 and #1, `mbpp/670`#0, `pow-k(k=3) | index-k(k=2)`#1. Against the first replay set,
  `humaneval/85`#1 no longer changes the outcome and `humaneval/3`#0 now does: the alternative branch itself is
  not perfectly reproducible on CPU-boundary tasks, so a single replay is not a reliable label.
* Gate A (measurement reliability): logical identity is now verified and the counts reconcile; outcome
  reproducibility of the alternative branch is NOT yet verified (it needs repeated replays per pair).

Not done in this session: Phases B–E (a learned experiment-selection policy over the existing disagreement /
sufficiency / Update / start / localisation experiments, intermediate structural-information credit, and the
D / B / E-static / E-learned / E-no-knowledge / E-no-learning comparison). V3 FAIL, Q3 OPEN, Q6 OPEN.

## 14. Reproducibility of the counterfactual labels (2026-11-14) — DEVELOPMENT ONLY

22 decision pairs (7 outcome-changing, 5 logically different, 10 controls fixed by hash before running), each run
3 times as D and 3 times with the one decision switched (132 runs, same code `ea528c6`, seed, budget).
Within each triple the outcome never varied (no UNSTABLE label); but against the single earlier replay:

| group | STABLE effect | NO EFFECT | INVALID |
|---|---|---|---|
| outcome-changing (7) | 4: repair better `count-k(k=10)`#0; invent better `humaneval/3`#0, `humaneval/3`#1, `pow-k(k=3) | index-k(k=2)`#1 | 2: `mbpp/670`#0, `prepend-k(k=-2) | positions`#0 (the earlier "effect" did not reproduce) | 1: `mbpp/775` (semantic mismatch) |
| logically different (5) | 0 | 3 | 2 (prefix differs again) |
| controls (10) | 0 | 10 | 0 |

So 4 valid causal labels remain (2 of them from one task), from 357 decisions. Only the logical evidence
features and the query count were compared; the full execution state (RNG, caches, CPU consumed) was not
captured, so these are same-evidence, not proven same-state, comparisons. With 4 labels a learned
experiment-selection policy has nothing to learn from: per the stop conditions, the hypothesis of section 13
("learned distinguishing experiments") was not implemented, and the scarcity is recorded as the finding —
decision-level outcome changes are rare and the labels needed to learn from them are rarer still.

V1 PASS (sealed). V2 independent OPEN (development results preserved). V3 FAIL. Q3 OPEN. Q6 untouched.

## 15. Structural witnesses in the existing records (2026-11-14) — DEVELOPMENT ONLY, no new runs

Extracted from the D rows of section 11 (FRESH-dev 110 + list-routines 228, code `96f5ea6`); `mbpp/775` counted
as a semantic failure. A witness is a recorded, SOURCE-verified observation that refuted or exposed a structural
hypothesis: an observed contradiction (equal state and element, different successors), a state-sufficiency
refutation, an Update / readout / start counterexample from a self-test, or a rejected invented variable.

| | value |
|---|---|
| witness events | 233 (95 distinct task × kind; 59 % repeats) |
| tasks / lineages | 60: list-routines 22, MBPP 26, HumanEval 12 |
| by kind (events / tasks) | contradiction 88 / 34; rejected variable 98 / 23; Update counterexample 27 / 23; readout counterexample 11 / 8; state refutation 8 / 6; start counterexample 1 / 1 |
| tasks where witnesses led to a verified invented machine | 8 |
| tasks with witnesses but unsolved | 40 |

Unsolved tasks split (the three bottlenecks the directive separates):
* information — no structural witness was ever observed: 95 tasks;
* policy / synthesis — witnesses observed and admissible structures existed, none verified: 40 tasks;
* representation — witnesses but no admissible structure at all: 0 by this record. The audit cannot see
  representation limits hidden behind admissible-but-wrong candidates (`mbpp/19`, `46` need a set of seen values,
  which no candidate expresses, yet junk candidates were admissible), so this split undercounts representation.

The signal is richer than the 4 final-outcome labels (233 events on 60 tasks across three lineages) but heavily
repeated, and only 8 tasks connect a witness to a verified invention. Whether witness prediction can be learned
and improves discovery (directive §5) was NOT tested in this session. V3 FAIL; Q3 OPEN; Q6 untouched.

## 16. Gate A audit: can the existing records teach query value? (2026-11-15) — DEVELOPMENT ONLY, no new runs

Of the 233 witness events of section 15, by how they arose (from the code paths that log them, `neumann1/active.py`):

| kind | events | how it arose | SOURCE query chosen among candidates? |
|---|---|---|---|
| rejected invented variable | 98 | internal: synthesis / fold on data already observed | no query |
| contradiction | 88 | trajectory state queries of a FIXED design (ascending, descending, random) | SOURCE queries, but not a selection |
| Update counterexample (self-test) | 27 | self-test query, chosen where a rival hypothesis disagrees | yes |
| readout counterexample | 11 | readout self-test query | yes |
| state-sufficiency refutation | 8 | sufficiency probe: a pair with equal final states | yes |
| start counterexample | 1 | self-test query | yes |

So 47 events come from SOURCE queries the system selected; 186 are internal checks or fixed-design observations.
For none of the 47 did the run record the candidate set at selection time, the rival each candidate targeted, or
the answers the unselected candidates would have produced (they were never asked). Relative query value is
therefore not learnable from the existing records: **learnable query-selection cases = 0**. Gate A fails on the
records; per the directive the experiment stops here. The minimal addition needed is to log, at each selected
query, the candidate pool size, the rival kind that produced the chosen input, and the hypothesis change after
the answer — and, to obtain counterfactual labels, to ask a second candidate on development tasks under the same
budget. Not implemented in this session.

Representation vs information vs policy (section 15's split, revisited): `mbpp/19` and `mbpp/46` reached
contradictions and state refutations (information present) but no candidate holds a set of seen values; the
admissible candidates there were chance fits. They are representation-limited, which section 15's count of 0 hid.

V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.

## 17. Query decisions recorded and compared at the same observation state (2026-11-15) — DEVELOPMENT ONLY

* **WBS-1 (code `neumann1/active.py`):** at every self-test query of a formed machine the run now records
  `query_decisions`: index, pool size and a hash of the deterministic pool, the candidates (for each rival, closest
  first, the first pool input where it disagrees: kind = another start / another equally consistent Update / the
  runner-up variable), the chosen candidate, the SOURCE answer, and the hypothesis change (counterexample or none),
  with the queries used before. `QUERY_SCHEDULE` makes one query take the second candidate instead.
* **WBS-2:** every dev task whose earlier D run made a self-test query (188: FRESH-dev and list-routines) was run
  twice on the same seed and budget — first candidate vs second candidate at the first self-test query. A pair is
  comparable only if that decision had ≥ 2 candidates and the query history and pool before it are identical in
  both runs. Cost: 5 860 CPU s, 21 936 queries (development data collection).
* **WBS-3:** comparable pairs **13** (HumanEval 5, MBPP 7, list-routines 1); candidate kinds start/start 10,
  start/update 3 (no variable rivals). The evidence differed in 6: the second candidate found a counterexample the
  first did not in `humaneval/57`, `mbpp/567`, `mbpp/680`, `mbpp/775` (semantic mismatch, not a valid label); the
  first found one the second did not in `humaneval/85`, `identify-k(k=1) | kth-smallest(k=2)`. Counterexamples:
  first 3 / 13, second 5 / 13. The full chain occurred once: `mbpp/680` — second candidate → counterexample →
  invented variable `h' = e` → verified machine → solved (the first branch fails).
* **Stop (directive §7):** 13 comparable decisions, 5 valid evidence differences, one causal solve: too few to fit
  or evaluate a learned query policy across lineages; WBS-4 (Static / Learned / Learned-ablated) was not run.
  Why so few: most first self-test queries had a single candidate (one rival with a disagreement in the pool), and
  self-tests occur only after a machine is formed.

V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched. Full regression 1148 passed, 53 skipped.

## 18. Observation choice BEFORE a machine exists: trajectories (2026-11-15) — DEVELOPMENT ONLY

* Code: `TRAJ_SHIFT` draws the trajectory values with another permutation under the same generation rule
  (ascending / descending / random over the observed range); `first_contradictions` records how many
  (state, element) pairs of the FIRST transition table have more than one successor — evidence available before
  any machine is formed.
* Run: the 195 dev tasks where D had invoked invention (list-routines 117, MBPP 54, HumanEval 24), D's draw vs one
  alternative draw, same seed / budget / synthesiser; the decision (first queries) differs by construction and
  nothing precedes it, so all 195 pairs are comparable. Cost 9 666 CPU s, 23 224 queries.
* Pre-formation evidence differed rarely: contradiction present in one draw and absent in the other in **5** tasks
  (HumanEval 3, MBPP 2); more contradictions with D's draw 2, with the alternative 3.
* Downstream effects were larger and mostly NOT explained by that evidence: invented structure differed in 16
  tasks, the solve in 8 (alternative only: `humaneval/121` with `h' = −h`, `mbpp/366` with `h' = e`; D's draw only:
  `identify-is-mod-k(k=7)`, `identify-k(k=-2)`, `mbpp/516`, `mbpp/670`, `pop | is-evens`, `uniq`); solved 77 vs 73.
  The outcome is sensitive to which values are observed, but the sensitivity runs through synthesis and repair,
  not through a contradiction the observation exposed.
* Pilot criteria (Assumption, directive §5): ≥ 30 comparable decisions — 195 met; ≥ 10 with differing structural
  evidence — 5, not met; ≥ 2 lineages — met; ≥ 2 hypothesis kinds — only state sufficiency was compared (the
  continuation path `represent()` was not instrumented in this session), not met. **Stop: no learned policy was
  built; Static / Learned / D / B comparison not run.**

V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched. Full regression 1148 passed, 53 skipped.

## 19. First causal divergence of the 8 trajectory-dependent outcomes (2026-11-15) — DEVELOPMENT ONLY

Both draws re-run (code `d479ed4`; raw: `docs/experiments/dev/q3_first_divergence_dev_2026_11_15.json`).
`uniq` failed in BOTH draws on this re-run (it had differed in section 18): an unstable outcome, excluded.

| task (solving draw) | first difference | class |
|---|---|---|
| `humaneval/121` (alt) | no contradiction in either table; "no progress" invention: alt tried 6 sets and adopted `h' = −h` (14.9 s); base tried 28 without an adoption, used 18 s | B search / synthesis |
| `mbpp/366` (alt) | no contradiction in either; alt adopted `h' = e` after 4 tries and its machine passed the challenge; base reached `h' = e` only after 38 tries + a contradiction, its machine FAILED the challenge (a different Update), suffix ran out of CPU | B synthesis (wrong Update) + CPU |
| `identify-is-mod-k(k=7)` (base) | base: answer-state machine at round 3, no branch point; alt: Update not found → invention (46 tries) → nothing | B synthesis |
| `identify-k(k=-2)` (base) | both fail the prefix machine; base's suffix machine verified, alt's suffix machine formed in 0.1 s and FAILED the challenge | B synthesis (wrong Update) |
| `mbpp/516` (base) | identical first invention call (2 admissible, 39 tries, none); base's suffix machine formed at round 0, alt's suffix found no Update | B synthesis |
| `mbpp/670` (base) | **alt observed 1 contradiction in the first table, base 0**; both later invented `h' = e`; base's machine verified at round 19, alt's failed the challenge | A observation present in alt, outcome B (Update) |
| `pop | is-evens` (base) | base observed a contradiction → invented the running sum `h' = h + e` (verified); alt saw no contradiction → "not localisable" path → `h' = e` → no machine | **A information**: the contradiction was what made the right variable admissible |
| `uniq` | fails in both draws on re-run | UNKNOWN (unstable) |

Summary: in 1 task the observation itself decided the invention (`pop | is-evens`, information); in 6 the
observations carried no differing contradiction and the outcome split in synthesis / Update choice / CPU (search
and synthesis); 1 mixed (`mbpp/670`); 1 unstable. No representation limit appeared among these 8.

Gate A (first divergence recorded per task): met. Gate B (a reproducible case where changing an observation
changes the invention): one candidate (`pop | is-evens`); its reproducibility and a single-observation
add/remove test were NOT run. Gate C: separated as above — the dominant bottleneck is synthesis / repair, not
information. Gate D: not met (one information-driven case). Per the directive's final question the next step is
the synthesis / repair bottleneck, not query-selection learning. `represent()` was not audited in this session.

V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.

## 20. Counterexample-guided repair of a refuted machine (2026-11-15) — DEVELOPMENT ONLY

* Code (`neumann1/active.py`): `challenge(..., detail=)` returns every SOURCE check (input, answer, prediction,
  queries used) and, with `REPAIR`, stops at the first confirmed counterexample; on a refuted machine `run_arm`
  re-forms the SAME direction with the counterexample added to the observations and the invented variables kept
  (`form_machine(prior_acc=...)`), and adopts the result only if it passes a NEW independent challenge on inputs it
  has not seen; otherwise the classical fallback stands. Baseline = `REPAIR = False` (the refuted machine is
  discarded).
* Runs (2 repeats each, same seed and budget; raw `docs/experiments/dev/q3_repair_dev_2026_11_15.jsonl`):

| task (condition) | refuted Update | SOURCE counterexample (input → answer, predicted) | repair result | solved base / repair |
|---|---|---|---|---|
| `mbpp/366` | `(if (lt s (mul h h)) (mul h e) s)` with h = last | [4,5,6,3] → 30, predicted 18 | kept `h' = e`; no machine re-formed within the remaining budget | F / F |
| `identify-k(k=-2)`, alt. trajectory | relcells step with `(mod $4 3)` piece | [-16, 10] → [0, 0], predicted (2, 0) | no machine re-formed | F / F |
| `mbpp/670`, alt. trajectory | case tree with `(lt (mod e 7) 5)` | [-2,-2,-2,-2,-2,0] → True, predicted False | kept `h' = e`; no machine re-formed | F / F |
| `identify-k(k=-2)`, `mbpp/670`, D trajectory | — (no refutation) | — | — | T / T |

* Cause classification: in all three the refuted Update special-cases a constant or a squared term (an Update
  error on a plausible variable — `h' = e` is the right variable for `mbpp/366` and `mbpp/670`), but re-synthesis
  with the counterexample did not produce a machine in the time left (refutation happens at ~17–18 of the 18
  formation seconds): recorded as "representation or search", not proven. Gate A (counterexample kept): met.
  Gate B (repair keeping the structure): mechanism in place, no successful repair. Gate C / D: not met (0 repaired
  solves). Gate E: no regression on the tasks run (`identify-k(k=-2)`, `mbpp/670` solved in both conditions on D's
  trajectory). What could not be fixed: the repair runs after formation has used almost all of its CPU, so the
  re-synthesis has seconds left; giving it budget would mean reserving CPU before formation — not done here.

V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.
Full regression: 1148 passed, 53 skipped (with REPAIR off by default).

## 21. Why the repair fails: diagnostic with extra CPU (2026-11-15) — DEVELOPMENT ONLY, not an official result

* Code: the counterexample is added once (duplicates removed from the observations); the repair records the CPU
  and queries left when it starts; `REPAIR_EXTRA_CPU` (default 0, diagnostic only) gives the re-synthesis extra CPU.
  Raw: `docs/experiments/dev/q3_repair_diagnostic_dev_2026_11_15.jsonl`.

| task | repair started with | extra CPU | outcome of the re-formation (same representation kept) | cause |
|---|---|---|---|---|
| `mbpp/366` | 0.29 s, 31 queries | 0 | rounds 0–2, failing 15 → 11 → 20 examples, deadline | CPU |
| `mbpp/366` | 20 s, 31 queries | 20 | counterexample not localisable → kept `h' = e` REJECTED by its own repair loop → no Update → query limit | search (the re-formation threw the right variable away) |
| `mbpp/670` (alt. trajectory) | 20 s, 20 queries | 20 | rounds 10–12, failing 7 → 4 → 4, deadline | CPU even with 20 extra s, then queries |
| `identify-k(k=-2)` (alt.) | 26 s, 4 queries | 20 | query limit (kept accumulator list was empty: a continuation-state machine) | queries |

None repaired. With CPU no longer the binding limit the re-formation still failed: it re-runs the whole
localise / invent / repair loop, spends queries on it, and in `mbpp/366` rejects the very variable it was told to
keep. This confirms the directive's premise: re-forming with `prior_acc` is NOT an in-place repair. The in-place
mechanism (re-synthesise only the conflicting Update from the stored transitions, keeping W, the transitions and
the start) was NOT implemented in this session — it requires `form_machine` to return its internal state.
Gates B–D not met. V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.

## 22. In-place counterexample repair (2026-11-15) — DEVELOPMENT ONLY

* Code (`neumann1/active.py`, `REPAIR = "inplace"`; default off): when a machine is formed, its internal state is
  kept in memory only (`_LAST`, never in a record): the transition table (W, invented variables and their starts),
  the observation set, the synthesis and fold functions. When the independent challenge refutes it, the SOURCE
  counterexample is added once; the prefix transitions of the counterexample join the stored table (their states
  are SOURCE queries); the same state space is kept and only the synthesised Update components are re-synthesised
  (`attempt`; invented variables keep their own known updates); the repaired machine must reproduce every
  observation and pass a NEW challenge on unseen inputs. Repair CPU: at most 8 s, inside the 30 s cap (taken from
  the classical fallback's share). No `form_machine` restart, no re-invention, no variable rejection.
* Same seed, 30 CPU s, 60 queries; raw `docs/experiments/dev/q3_inplace_repair_dev_2026_11_15.jsonl`:

| task | arm | repair started with | Update before → after | new challenge | hidden test | semantic |
|---|---|---|---|---|---|---|
| `mbpp/366` | baseline / re-form | — | — | — | F / F | — |
| `mbpp/366` | **in-place** | 12.3 s, 36 queries | `(if (lt s (mul h h)) (mul h e) s)` → `(if (lt s (mul h e)) (mul h e) s)` (state: answer + `h' = e`) | pass | **T** | **yes**: max over adjacent products |
| `mbpp/670` alt. | baseline / re-form | — | — | — | F / F | — |
| `mbpp/670` alt. | in-place | 13.1 s, 25 queries | `…(if (eq h 1) (lt (mod e 7) 5) (lt h e))` → `…(if (eq h 1) (lt (mod e 7) 6) (not (lt e h)))` | pass | T | **no**: the `h = 1` special case survives |
| `identify-k(k=-2)` alt. | in-place | 26.6 s, 9 queries | relcells step | — | F | 13 examples still fail on this state space (continuation state; representation or synthesis, not resolved) |

* Gate A: partly — the counterexample's prefix transitions are SOURCE-observed and the conflicting one is among
  them, but the FIRST wrong transition was not singled out and recorded. Gate B: met for these machines (W,
  invented variable, start and table kept; only the answer component re-synthesised). Gate C: met in one task
  (`mbpp/366`: repaired, new independent challenge passed, semantically correct). Gate D: one additional semantic
  solve over baseline and re-form (`mbpp/366`), 1 : 0 — a single development task, not significant. Gate E: the
  repair is off by default; regression of previously solved tasks under `REPAIR = "inplace"` was not measured
  across the dev set. `mbpp/670` counts as a semantic failure (hidden-test pass without the reference semantics).

V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.
Full regression: 1148 passed, 53 skipped (REPAIR off by default).

## 23. Repair ownership and falsifiability of the repaired Update (2026-11-15) — DEVELOPMENT ONLY

* Ownership: the global `_LAST` is gone; each formed machine's function carries its own `repair_state` (W,
  invented variables and starts, transition table, observations, synthesis functions, the alternative Updates);
  nothing of it is written to a record.
* `REPAIR = "inplace+disc"`: after the in-place re-synthesis, inputs are searched (task-distribution inputs and their
  edits) where the repaired Update disagrees with (a) the refuted Update, (b) every other equally consistent Update,
  (c) each variant obtained by pruning ONE case split of the repaired Update — the rival that differs exactly where
  that split's branch is reached, so rare-condition branches are probed without naming any constant. The rarest
  disagreement is asked first (≤ 3 rounds); a wrong repaired Update gets the counterexample and is re-synthesised on
  the same state space; then the new independent challenge.
* Result (same seed, 30 CPU s, 60 queries): `mbpp/366` — 3 probes confirmed the repaired Update, solved and
  semantically correct (preserved). `mbpp/670` alt. — 3 probes ([-2,0,4,0], [1,-1,0], [2]) all agreed with the
  repaired Update; the `h = 1` special case was probed once ([1,-1,0], where it happens to give the right answer)
  and survived; the machine is still adopted with a hidden-test pass and a semantic mismatch. **Not fixed.** The
  disagreement region of a spurious branch is reached, but one probe in it is not enough when the branch is right on
  part of that region.
* Not done: the dev-set comparison (Baseline / In-place / In-place + discrimination: solved sets, regressions, wrong
  adoptions, cost). Core question (more semantic solves without more wrong adoptions) not answered.

V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.
Full regression: 1148 passed, 53 skipped (repair modes off by default).

## 24. Branch necessity in repaired Updates (2026-11-15) — DEVELOPMENT ONLY

* `REPAIR = "inplace+necessity"` (default off): after an in-place repair, every case split of the repaired Update
  is removed in turn, jointly with every start of the invented variables; a simpler Update that still reproduces
  EVERY SOURCE observation so far is a rival. New SOURCE inputs where the two disagree are asked, chosen for
  distinct predicted outcomes (up to 3, not one per branch); the refuted one is dropped; if neither is refuted the
  simpler is kept (description length; a selection principle, not a proof of the semantics). No constant, task id
  or answer is used.
* Result (same seed, 30 CPU s, 60 queries; raw `docs/experiments/dev/q3_branch_necessity_dev_2026_11_15.jsonl`):
  `mbpp/366` — no split removable on the evidence; repair as before; solved, semantically correct (Gate C kept).
  `mbpp/670` alt. — one split removable: the simpler Update `(if (not s) False (not (lt e h)))` with another start
  of `h' = e` reproduces every observation; probes [1,-3,-3,-3], [-1,-1,-1,-1,3], [-1]: the complex Update (with the
  `h = 1` special case) refuted 3 times, the simpler 0; the simpler kept, passed a new challenge, solved — and it is
  the reference semantics (non-decreasing check). Gate D: the wrong semantic adoption is resolved on this task.
* Not done: Gate E — the dev-set comparison (Baseline / In-place / In-place + necessity: semantic solves,
  regressions, wrong adoptions, branch counts, cost). Two development tasks; not independent evidence.

V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.
Full regression: 1148 passed, 53 skipped (repair modes off by default).

## 25. Gate E status (2026-11-15 03:23 UTC) — IN PROGRESS, no verdict

* Code under test: `c43a427` (no code change since). Arms baseline / in-place / necessity on the 338 opened dev
  tasks (FRESH-dev 110, list-routines 228), same seed, 30 CPU s, 60 queries per run.
* The first launch stopped after 3 + 8 rows per arm (the runner processes were gone; no corrupt or duplicate rows).
  Relaunched detached at 03:22 UTC; the runners skip rows already present, so only the missing tasks run. Expected
  ~1.5–2 h. On completion the pipeline writes `docs/experiments/dev/gateE/summary.json` and commits it with the full
  raw rows ("Q3 Gate E dev comparison").
* Until that commit exists, Gate E is OPEN / INCONCLUSIVE. The analysis the directive asks for (semantic audit of
  every new solve, per-stage cost, branch counts, first-wrong-decision analysis of losses) remains to be done on
  the completed rows. V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.

## 26. Gate E result (2026-11-15) — DEVELOPMENT ONLY

Code `c43a427`; 338 tasks × 3 arms = 1 014 valid runs (+ `mbpp/38`, reference inconsistent, not run, in every arm);
no errors, no duplicates; raw rows and `summary.json` in `docs/experiments/dev/gateE/` (commit `b133843` + this one).

| arm | solved (hidden test, known mismatch excluded) | vs baseline new / lost |
|---|---|---|
| baseline | see summary.json | — |
| in-place | +2 net | new `mbpp/366`, `mbpp/940`, `rotate-k(k=1) \| identify-geq-k(k=2)`, `slice-k-n(k=3,n=4) \| repeat-k(k=5)`; lost `identify-is-mod-k(k=2) \| append-k(k=10)`, `keep-mod-k(k=2) \| pow-k(k=3)` |
| necessity | +3 net | same four new; lost `mbpp/345` |

Causal attribution: a solve is caused by the mechanism only where a repaired machine was adopted. Repairs were
attempted on 8 (in-place) / 9 (necessity) tasks and adopted after a new challenge on 5: `mbpp/366`, `mbpp/775`,
`add-k(k=2) | identify-k(k=10)`, `pow-k(k=2) | is-odds`, `rotate-k(k=1) | identify-geq-k(k=2)`. Of these only `mbpp/366`
(development case, semantics VERIFIED) and `rotate-k(k=1) | identify-geq-k(k=2)` (semantics UNKNOWN) are new solves;
the other two were solved by the baseline too. The remaining differences (`mbpp/940`, `slice-k-n…`, the two in-place
losses, `mbpp/345`) involve no repair at all: the repair modes stop the challenge at the first counterexample, which
changes query use and the random stream — perturbation of the same size (+2 / −2) as the effect. Branch necessity
acted on one task (`mbpp/775`, simpler Update kept; still excluded, program unaudited).

Verdict: Branch Necessity vs In-place — **DEVELOPMENT FAIL** (net +1 consists only of perturbed tasks; 0 causal solves).
In-place vs Baseline — **INCONCLUSIVE** (one causal new solve outside the development cases, semantics unverified,
within perturbation). Answer to "is NEUMANN smarter on new problems?": not demonstrated.
Bottleneck: refuted-but-formed machines are rare (≤ 9 of 338 tasks), so repair cannot move the solve count; most
failures happen before any machine is formed (sections 18–19: synthesis / search). Stage costs NOT MEASURED.
V1 PASS (sealed). V2 independent OPEN. V3 FAIL. Q3 OPEN. Q6 untouched.

## 27. Pre-formation failure causes (2026-11-15) — DEVELOPMENT ONLY, no new runs

From the Gate E baseline rows (code `c43a427`; `docs/experiments/dev/gateE/preformation_causes.json`), the 138
unsolved development tasks by the first cause visible in the record:

| cause (directive §1 numbering) | tasks | list-routines / MBPP / HumanEval |
|---|---|---|
| 2 consistent state, no Update synthesised | **62** | 29 / 21 / 12 |
| 4 queries exhausted | 27 | 14 / 10 / 3 |
| 4 CPU exhausted | 12 | 4 / 5 / 3 |
| 1/5 state undefined on short inputs | 12 | 11 / 1 / 0 |
| 1 state insufficient (counterexample not localisable) | 10 | 7 / 2 / 1 |
| 3 wrong candidate adopted first (refuted by the challenge) | 6 | 1 / 5 / 0 |
| other (fold still failing at the end, etc.) | 9 | — |

The dominant cause, in every lineage, is (2): the state is consistent on the observed transitions but no Update is
found within the substrate and time — synthesis, not candidate choice (6 tasks) and not representation (the record
cannot separate (2) from (5) when admissible structures exist; see section 16). The directive's candidate-selection
improvement targets cause (3), 6 tasks; the larger lever is Update synthesis on consistent states (cause 2, 62
tasks). Not done in this session: any algorithm change, causal experiment or dev-set extension. Q3 OPEN; V3 FAIL.

## 28. Goal-directed residual Update synthesis (code `f127bc3`, opt-in `GOAL_UPDATE_SYNTH`) — DEVELOPMENT ONLY

* Implementation check: `synth_goal_update` and `synth_list_delta_update` (from another session's commits
  `5ad1adc`, `9e8f0a7`, `f127bc3`) are off by default; `tests/test_active.py` 8 passed; the list delta synthesiser
  builds `cons` / `foldrL` ASTs and compiles them with `compile_ast` (executable, not a display string).
* Comparison: the per-task transition tables at failure time are not stored in the logs, so instead each task was
  run with the same seed, budget (30 CPU s, 60 queries) and policy, residual synthesis off vs on; the runs are
  identical up to the first synthesis call (same queries), so the first synthesis sees the same table. Raw:
  `docs/experiments/dev/q3_residual_synthesis_dev_2026_11_15.jsonl`.

| task (Update synthesis failed in Gate E) | baseline | residual |
|---|---|---|
| `pow-k(k=4)` | not formed | **formed at round 0, challenge passed, solved**: Update `(foldrL (cons $2 $3) (cons (mul (mul e (mul e e)) e) nil) s)` = append e⁴ (residual: the new last cell; intermediate: e·e·e·e) |
| `pow-base-k(k=2)`, `identify-is-mod-k(k=7)`, `identify-k(k=10)` | not formed | not formed |
| `mbpp/45`, `mbpp/22`, `mbpp/200`, `mbpp/281` | not formed | not formed (`mbpp/45`, `mbpp/22`: residual run ends at the CPU deadline instead) |

SYNTHESIS PASS on one development task (list-routines): a previously unsynthesisable list Update was built from
the observed residual (the appended cell) and executed correctly on the hidden test. Not shown: a second lineage,
the dev-set extension, regressions, semantics of the other tasks; on two MBPP tasks the residual stage consumed
the CPU. DEVELOPMENT PASS not reached (one lineage); GENERALIZATION OPEN. V1 PASS (sealed), V2 independent OPEN,
V3 FAIL, Q3 OPEN, Q6 untouched.

## 29. Fixed-transition comparison of the Update synthesisers (code `cb5cb65`) — DEVELOPMENT ONLY

* `tests/test_active.py` 9 passed. Snapshots of the first failed Update synthesis were captured for all 91 screen
  candidates of `q3_update_snapshot_screen.json` (list-routines 42, FRESH-dev 49; FRESH tasks regenerated from the
  opened registry with matching hashes; no sealed data opened); 41 + 48 distinct snapshots (by SHA-256). Each was
  replayed WITHOUT any SOURCE query: baseline synthesiser vs goal-directed residual synthesiser, same table, types,
  grammar and 5 CPU s each. Raw snapshots, replays, SHA256SUMS and summary: `docs/experiments/dev/update_snapshots/`.

| family (snapshots) | residual only | both | neither | baseline only (regression) |
|---|---|---|---|---|
| list-routines (41) | 1: `pow-k(k=4)` | 11 | 29 | 0 |
| FRESH-dev (48) | 1: `mbpp/940` | 0 | 47 | 0 |

* SYNTHESIS PASS on 2 frozen transitions in two lineages: the residual synthesiser built an executable Update the
  baseline synthesiser could not on the same table (`pow-k(k=4)`: append e⁴; `mbpp/940`: see `summary.json`).
  No loss. These are component Update fits on fixed transitions, not solved tasks and not semantic verifications.
* 11 list-routines snapshots are fitted by BOTH synthesisers given 5 s on the frozen table: there the Gate E
  failure was not synthesis inability but the time available at that point of the run.
* 76 of 89 snapshots are fitted by neither: the next bottleneck is Update synthesis/representation on these
  transitions (not separated further here). DEVELOPMENT PASS (whole-task causal solves) not evaluated in this step.
V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched.
* Correction to the row above: the `mbpp/940` fit of the residual variant is a `relcells` cell program (the existing
  R2 construction), not a goal-directed residual decomposition; it appears only through a different call path / time
  share in that variant. Only `pow-k(k=4)` (cons / foldrL with the residual cell e·e·e·e) is a residual construction:
  SYNTHESIS PASS for residual decomposition = 1 transition, one lineage.

## 30. Budget recovery on the 11 "both synthesisers fit" snapshots (2026-11-15) — DEVELOPMENT ONLY

* The snapshots do not record the CPU left at the failure, so item 1 of P0-A (actual remaining budget) could not be
  read from the records.
* Policy tested (`MIN_SYNTH_CPU`, default 0 = unchanged): each main-round Update synthesis gets a floor of 5 CPU s
  within the formation deadline (a reallocation, total 30 s / 60 queries unchanged). Same seed; only the floor
  differs. Raw: `docs/experiments/dev/update_snapshots/budget_floor_lr11.jsonl`.
* Result: 1 of 11 newly solved — `prepend-k(k=-2) | positions` (m = 2 machine, challenge passed); 0 losses;
  `prepend-k(k=10) | positions` moved from query limit to the CPU deadline. The other 9 fail as before ("no informative
  continuation" or, for `rotate-k(k=1) | identify-geq-k(k=2)`, a machine refuted by the challenge).
* Reading: for 10 of the 11 the Update that is fittable on the frozen first-failure table does NOT turn into a formed
  machine even with a 5 s synthesis floor — the binding failure lies after that synthesis (fold / localisation /
  continuation search), not in the synthesis budget. Capability recovery: 1 development task, semantics UNKNOWN.
  Structural synthesis and generalisation: not addressed this round. Next bottleneck: what happens between a fitted
  first Update and a formed machine on these 10 tasks.
V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched.

## 31. Post-synthesis first failure on the 11 tasks (2026-11-15) — DEVELOPMENT ONLY

Same seed, A = `MIN_SYNTH_CPU` 0 vs B = 5; the existing step events of `form_machine` (round results, no Update,
self-test counterexample, invention, localisation, limits) give the path; no new instrumentation (so no change to
queries or the random stream). Raw traces: `docs/experiments/dev/update_snapshots/post_synthesis_trace_lr11.jsonl`;
table: `post_synthesis_first_failure.json`.

* First failure (A): **10 / 11 "Update found, fold fails"** — the first round synthesises an Update that fits the
  observed transitions but folds wrongly on 1–7 of the initial examples; 1 / 11 (`pow-k(k=4) | product`) "Update not
  found in the run" (found with the floor in B, then the same fold failure). The final "no informative continuation"
  is the end of the repair that follows: the counterexample loop cannot turn the wrong-but-consistent first Update
  into one that folds correctly, and the continuation search finds nothing to add.
* B solved 2 in this run (`prepend-k(k=-2) | positions`, `rotate-k(k=3)`); section 30's run of the same setting solved
  only the first — `rotate-k(k=3)` is not stable across runs and is not counted.
* DIAGNOSIS PASS (for these 11): the first wrong decision is the adoption of an Update that fits the observed
  transitions but not the examples' folds — the transitions on the trajectories under-determine the Update (the
  same pattern as the wrong-Update refutations of sections 19–22). Not done: the fixed-Update injection experiment
  (P0-C) and a causal fix (P0-D). Next single mechanism: choose among Updates equally consistent with the
  transitions by the initial examples' folds before committing (the alternatives already exist in `upd_alts`).
V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched.

## 32. Fold-aware Update selection: interface audit (2026-11-15) — DEVELOPMENT ONLY, no new runs

* `upd_alts` is filled only by `synth_cover` (alternative case trees, for the answer component j = 0); `synth_multi`
  returns its first fit; `synth_cells` (`lt.solve`, R2 cell construction) returns exactly one program and has no
  interface for alternatives.
* The 11 tasks' fixed-transition fits (section 29 replays): 10 are `cells` programs, 1 (`pow-k(k=4) | product`) a
  `foldrI` expression from `synth_multi`. So for all 11, the in-run Update was produced by a synthesiser that offers
  NO alternative transition-consistent candidates: fold-aware selection among alternatives has nothing to select
  from on these tasks.
* Directive CASE 2 (alternatives not generated): candidate selection is not developed further; the open question is
  candidate GENERATION in the cell construction (several distinct cell programs consistent with the same
  transitions, then the initial examples' folds to choose) — or, if the cell language cannot express a program that
  folds correctly, the representation. Neither was tested in this session. `FOLD_AWARE_SELECTION` was not added.
* CANDIDATE PASS / FOLD PASS / MACHINE PASS / DEVELOPMENT PASS: not reached (no experiment). GENERALIZATION OPEN.
V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched.

## 33. Observable-equivalence pruning in the cell construction: audit only (2026-11-15) — no new runs, no code change

Where alternative transition-consistent programs are discarded on the main list-state path
(`active.synth_cells` → `latent.solve` → `solve_cfg` → `construct`):
1. `discovery_core.FSearch._keep` (line ~87): an expression whose value vector on the search inputs equals one
   already kept is dropped (`if v in seen: return`) — observational equivalence on the supplied rows only.
2. `latent.construct` (lines ~267–281): cell pieces are deduplicated by (key, coverage mask) and predicates by mask
   (`seen` / `pseen`), with caps `MAX_PIECES` / `MAX_PREDS` — two pieces with the same coverage on the observed
   transitions are one candidate even if they differ elsewhere.
3. `active.synth_cells` returns the first solution `lt.solve` produces; there is no alternatives interface
   (section 32). `cells._cover` (cells.py:159) is not on this path.
Not done in this session: the experimental probe-signature refinement (P0-B), the candidate / fold comparison on the
fixed snapshots (P0-C/D) and the machine-level experiment (P0-E). CANDIDATE PASS / FOLD GAIN not evaluated.
V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched.


## 34. Probe-signature candidate retention in Q3 cell synthesis (2026-11-15) — DEVELOPMENT ONLY

Implementation after audit `0deaca7`: `discovery_core.FSearch` can retain up to four top-level expressions per observed value vector when their locally constructed probe signatures differ; `latent.construct` can retain up to four probe-distinct cell/predicate pieces and return complete candidates through `latent.solve_candidates` and `active.synth_cells_candidates`. All settings are opt-in; the official `active.synth_cells` and `attempt` path remains first-fit. Scope limitation: binder/subexpression contexts still use original pruning; synthetic probes are NOT independent SOURCE verification.

An initial immediate-diversification variant regressed candidate discovery on the fixed 10 list-cell cases (4 programs total, one evaluable fold; zero gain). Baseline-first diversification increased that to 8 programs and five evaluable folds; still zero fold gain. The final variant preserves legacy first-cover search/order and enables diversification only after a valid first program.

**Final frozen development experiment:** workflow run [43700395880](https://github.com/yoonsj0305/NEUMANN/actions/runs/43700395880), baseline snapshot files from Gate E, `PYTHONHASHSEED=0`, 5 CPU seconds PER synthesiser per fixed transition, at most four candidates, no SOURCE queries. Artifact `q3-latent-candidate-lr11-dev`, artifact ID 14156470654, ZIP digest `sha256:2fe169ec093d717f26bf350e8410bd196e4d85bd297d6e37b47d116c95d3153a`.

| Metric | Result |
|---|---|
| List-cell snapshots attempted | 10 (the 11th is a `foldrI` case outside this mechanism) |
| Existing single-solution synthesis fits | 10 / 10 |
| Programs emitted by opt-in candidate synthesis | 12 total |
| Tasks with >1 probe-distinct candidate | 2 / 10 (`add-k(k=10) | identify-is-prime`, `prepend-k(k=-2) | positions`) |
| Tasks with comparable initial-example fold evaluation | 7 / 10 |
| Fold-error improvements against baseline | **0 / 7** |
| Whole-machine / independent SOURCE challenge / original semantic verification | **NOT EVALUATED** |

**Interpretation:** A limited CANDIDATE GENERATION mechanism has been demonstrated on two opened list-routines tasks; however the extra programs did not reduce fold errors in the seven evaluable cases. This is NOT FOLD GAIN or DEVELOPMENT PASS. Only the original gate-independent evidence remains: V1 PASS (sealed); V2 independent OPEN; V3 FAIL; Q3 OPEN; Q6 untouched. Do not expand to FRESH or new generalisation based on this experiment. CI full-suite result was not confirmed in this record.

**Next decisive question:** Is the lack of fold improvement due to missing latent state/incorrect initial state, or because the permitted cell representation cannot express the correct transition? Perform one matched, SOURCE-free, original-initial-example refit/oracle headroom check on already opened list-routines; if no correct Update exists under fixed W and initial state, stop adding top-K candidates. No per-task hardcoding.


## 35. Reachability-guided structural synthesis (2026-11-15) — DEVELOPMENT ONLY

Directive "Q3 Reachability-Guided Structural Synthesis". Questions: why do the transition-consistent Updates of the
10 list-cell tasks fold the initial examples wrongly; is more state actually needed; does using the folds'
reachable states as a synthesis constraint reduce fold errors and solve tasks causally. Raw evidence:
`docs/experiments/dev/reachable_state/` (JSONL rows per run, `summary.json`, `SHA256SUMS`).

**P0-A audit.** Run 43700395880 (head `cb63174`), job log: 10 rows, 12 candidates, 7 fold-evaluable, fold gains `[]`;
artifact 14156470654, digest `2fe169ec…153a`, as recorded in section 34. CI on the base `d8a95b1` (run 43700686483):
success, so there was no regression to repair. Locally (Python 3.11, the CI pins) the Q3 test files pass. One
CPU-budgeted test (`test_policy_is_updated_by_verified_experience_only`, 8 CPU s per task) failed once while five
experiment processes saturated the cores; it passed when rerun alone on this code and on `d8a95b1`. That failure is
load timing, not a regression. Full CI on the head carrying this section's code (`efb00ec`, run 43705723009): success.

**Method note: the budget unit.** The synthesisers stop on `time.process_time()` deadlines, and the same 5 s first fit
fitted or failed on the same table between runs (CI: 10/10 fits; local real-clock reruns: 7/10, 7/10, and 5/10 under
heavy load). So two units are reported:
* **virtual clock** (`research/q3/vclock.py`, harness only): virtual s = 3.0e-7 · `invention_core.WORK` + 5.0e-5 ·
  clock reads, least-squares fit on 30 real first-fit calls (`vclock_calibration.json`). Every synthesis module and
  the harness read it, so fixed-table runs are byte-identical across reruns. GitHub's runner regenerated
  `reachable_diagnosis.jsonl` and `fold_reach_replay.jsonl` and matched the committed rows exactly (workflow
  `q3-reachable-fold-dev.yml`, run 43705722762 on `efb00ec`, artifact 14158208864). In the machine runs, query logs, events
  and adopted Updates were identical in 3 reruns of 4 (arm, task) pairs; only the final CPU total of the passive
  fallback phase varied.
* **real clock**, replicated. This is the official unit.

The virtual unit is **not neutral**. It under-counts formation-phase Python work (≈ 3× fewer virtual than real
seconds) and C's Python-level fold checks: in 5 real CPU s, C judged 28 candidates on `identify-is-mod-k(k=7)`,
against 351 in 5 virtual s. Results that hold only in the virtual unit are labelled so and are NOT counted as
improvements under the official budget. A first harness version mixed real and virtual deadlines (inflated, unequal
budgets); those runs were discarded and are not reported.

### 35.1 Reachable-state diagnosis (P0-B, P0-C)

For each frozen first-failure table T (section 29 snapshots), the states every initial example's fold actually
reaches were observed from SOURCE by DIAGNOSTIC queries: S(u) = (f(u·w) for w ∈ W) on all prefixes u. These used a
separate unlimited Env with the same seed; hidden tests stay blocked, the routine is never read, and the 21–83
diagnostic queries per task are outside every agent budget. R = these reachable transitions. A = the existing first
fit on T (5 virtual s). Script `research/q3/reachable_state_diagnosis_dev.py`; rows in `reachable_diagnosis.jsonl`.
In the column "its folds / fresh", fresh = 20 random SOURCE inputs (diagnostic).

| task | \|T\| | \|R\| (new pairs) | A fold err | conflict on T∪R | Update fitting T∪R (existing cell language) | its folds / fresh | verdict |
|---|---|---|---|---|---|---|---|
| `add-k(k=10) \| identify-is-prime` | 13 | 37 (32) | 4 | no | not found (20 s cap) | — | unresolved |
| `identify-is-mod-k(k=7)` | 15 | 14 (8) | 2 | no | found (4.5 s) | 0 / 20/20 | representable |
| `identify-is-prime` | 14 | 26 (18) | 4 | no | not found (20 s cap) | — | unresolved |
| `positions \| append-k(k=3)` | 14 | 25 (19) | 0 | no | found (2.6 s) | 0 / 15/20 | representable |
| `prepend-k(k=-2) \| positions` | 14 | 30 (24) | 2 | no | found (1.3 s) | 0 / 20/20 | representable |
| `prepend-k(k=10) \| positions` | 10 | 29 (24) | no fit | **yes** (witness below) | — | — | **W insufficient** |
| `replace-all-k-with-n(k=5,n=0) \| rotate-k(k=1)` | 16 | 36 (27) | 4 | no | found (9.3 s) | 0 / 20/20 | representable |
| `rotate-k(k=-2) \| replace-all-k-with-n(k=1,n=2)` | 12 | 21 (20) | 1 | no | not found (20 s cap) | — | unresolved |
| `rotate-k(k=1) \| identify-geq-k(k=2)` | 17 | 28 (19) | 1 | no | found (0.1 s) | 0 / 13/19 | representable |
| `rotate-k(k=3)` | 10 | 28 (27) | 3 | no | found (9.2 s) | 0 / 20/20 | representable |

* **Where the folds fail.** All 21 first divergences of A's folds (failing examples with an observed path) occur at a
  reachable (state, element) pair that T never observed. In 20 of them the state just before is observed and correct;
  in the 21st that prefix is a blocked hidden-test input. 7 occur at a state longer than any in T (T's trajectories are
  4-element sequences, while the examples reach length 7), and 5 involve an element value T never contained. The
  adopted Update is right on everything it was shown. It is wrong where the examples go and the agent did not look.
* **Is more state needed?** Only for `prepend-k(k=10) | positions`. SOURCE observed state `[0,1,2,3,4]` with element 6
  going to `[0,1,2,3,4,6]` after prefix `[7,8,9,1,0]`, and to `[0,1,2,3,4,5]` after `[11,10,5,6]`: the answer-as-state
  W = [()] cannot carry len(u) once u contains zeros. The witness is the proof. This is the one task where W is
  insufficient. The existing distinguishing-continuation rule (section 2) adds the component e·w = (6,), but only if
  the conflict is observed, and T's synthetic trajectories never reach it (confirmed in 35.4).
* **Representable under fixed W and z (no new state): 6 tasks.** With R observed, the EXISTING cell synthesiser builds
  an Update that reproduces every reachable transition, hence every initial fold. On 20 fresh SOURCE inputs it scores
  20/20 on 4 of them (`identify-is-mod-k(k=7)`, `prepend-k(k=-2) | positions`,
  `replace-all-k-with-n(k=5,n=0) | rotate-k(k=1)`, `rotate-k(k=3)`), and 15/20 and 13/19 on the other two. The
  readout is exact on every task (observed f(x) = the example's answer). The initial state is the observed S(()),
  except `rotate-k(k=3)`, whose S(()) is blocked; the sentinel () is consistent with every observation there.
  `positions | append-k(k=3)` already folds correctly from T: its run-time failure was the CPU share at that moment
  (sections 29–30), not the fold.
* **Unresolved: 3 tasks** (`identify-is-prime`, `add-k(k=10) | identify-is-prime`,
  `rotate-k(k=-2) | replace-all-k-with-n(k=1,n=2)`). There is no conflict, and no Update fitting T∪R was found within
  the synthesiser's own phase limits at a 20 s cap. They are NOT declared inexpressible: no complete impossibility
  argument for the restricted grammar was built. (Primality needs a membership relation over e; the rotate-by-−2
  Update needs at least 4 cases where the cover builds at most 3.)

### 35.2 A / B / C on the frozen tables (P0-D, P0-E part 1)

All arms use the same table, types and initial state (the observed root in T, else the machine's sentinel), the
same cap per component, and no SOURCE query.
* A = the first fit.
* B = the section 34 probe-diversified candidates (k = 4), best fold kept.
* C = `synth_cells_fold` → `latent.solve_fold` (opt-in). The legacy enumeration runs to its first complete candidate,
  which is identical to A's first fit on 10/10 in every run. If the machine with it folds an initial example wrongly,
  the SAME enumeration continues to the cap. Observational equivalence is refined on the cell coordinates of the
  states that candidate's own fold reaches (no query). Every later complete candidate is judged by all
  initial-example folds; the first with 0 errors is returned, otherwise only the best is kept, never a candidate
  list. Observed transitions stay hard constraints. For a 2-component W, C acts on the last component and the
  earlier one is as in A.

Script `research/q3/fold_reach_replay_dev.py`. Cells: fold errors on the 8 initial examples / reachable transitions of
R reproduced (diagnostic) / fresh SOURCE inputs (diagnostic). Bold = a new Update from C.

**5 virtual s per component** (`fold_reach_replay.jsonl`, byte-identical in two runs):

| task | A | B | C | C candidates judged |
|---|---|---|---|---|
| `add-k(k=10) \| identify-is-prime` | 4 / 30/37 / 9/20 | 4 / 30/37 / 9/20 | **2 / 35/37 / 10/20** | 690 |
| `identify-is-mod-k(k=7)` | 2 / 12/14 / 13/20 | 2 / 12/14 / 13/20 | **0 / 14/14 / 19/20** | 351 |
| `identify-is-prime` | 4 / 18/26 / 6/20 | 4 / 18/26 / 6/20 | 4 / 18/26 / 6/20 | 20 |
| `positions \| append-k(k=3)` | 0 / 25/25 / 15/20 | 0 / 25/25 / 15/20 | 0 / 25/25 / 15/20 | 1 |
| `prepend-k(k=-2) \| positions` | 2 / 21/30 / 15/20 | 2 / 21/30 / 15/20 | **1 / 29/30 / 16/20** | 2040 |
| `prepend-k(k=10) \| positions` | no fit | no fit | no fit | 0 |
| `replace-all-k-with-n(k=5,n=0) \| rotate-k(k=1)` | 4 / 25/36 / 13/20 | 4 / 25/36 / 13/20 | 4 / 25/36 / 13/20 | 1 |
| `rotate-k(k=-2) \| replace-all-k-with-n(k=1,n=2)` | 1 / 18/21 / 9/20 | 1 / 18/21 / 9/20 | 1 / 18/21 / 9/20 | 753 |
| `rotate-k(k=1) \| identify-geq-k(k=2)` | 1 / 26/28 / 11/19 | 1 / 26/28 / 11/19 | **0 / 28/28 / 13/19** | 525 |
| `rotate-k(k=3)` | 3 / 24/28 / 10/20 | 3 / 24/28 / 10/20 | 3 / 24/28 / 10/20 | 1 |

**Equal real cap of 40 CPU s per component, all arms** (`fold_reach_replay_real40.jsonl`): fold errors per arm, the
number of candidates C judged, and real CPU used by A/B/C.

| task | A | B | C | C judged | CPU A/B/C |
|---|---|---|---|---|---|
| `add-k(k=10) \| identify-is-prime` | 4 | 4 | **2** | 1028 | 2.6 / 19.2 / 40.0 |
| `identify-is-mod-k(k=7)` | 2 | 2 | **0** | 351 | 2.4 / 19.4 / 18.9 |
| `identify-is-prime` | 4 | 4 | **3** | 1039 | 2.6 / 19.3 / 40.0 |
| `positions \| append-k(k=3)` | 0 | 0 | 0 | 1 | 1.7 / 18.0 / 1.5 |
| `prepend-k(k=-2) \| positions` | 2 | 2 | **1** | 1896 | 0.9 / 5.4 / 40.1 |
| `prepend-k(k=10) \| positions` | 3 | 3 | 3 | 1302 | 2.0 / 18.5 / 40.0 |
| `replace-all-k-with-n(k=5,n=0) \| rotate-k(k=1)` | 4 | 4 | 4 | 1 | 0.6 / 20.0 / 40.0 |
| `rotate-k(k=-2) \| replace-all-k-with-n(k=1,n=2)` | 1 | 1 | 1 | 1449 | 1.9 / 18.7 / 40.0 |
| `rotate-k(k=1) \| identify-geq-k(k=2)` | 1 | 1 | **0** | 525 | 0.0 / 18.8 / 1.4 |
| `rotate-k(k=3)` | 3 | 3 | 3 | 778 | 2.5 / 19.2 / 40.0 |

* **Fold errors.** Virtual 5 s: A 21, B 21, C 15 over 9 evaluable tasks; C improves 4, B 0. Real 40 s: A 24, B 24, C 17
  over 10; C improves 5 (2 to zero: `identify-is-mod-k(k=7)`, `rotate-k(k=1) | identify-geq-k(k=2)`), B 0. C is never
  worse, because it returns A's first fit unless a candidate folds strictly better. At 40 s, C runs exactly the
  virtual-run searches again (351 and 525 candidates). These are new executable Updates that fit T, reproduce more of
  R, and are at least as good on fresh inputs (`identify-is-mod-k(k=7)` 19/20 vs 13/20). None is fully correct on fresh
  inputs.
* **Under the official per-call share** (real 5 CPU s, `fold_reach_replay_real5_run{1,2}.jsonl`), the gain mostly
  disappears: C improves on 0 of 6 and 1 of 6 jointly evaluable tasks. C judges about 10× fewer candidates per
  real second than the virtual unit allowed, and A itself fits or fails between the two runs (7/10 fits each).
* **Cost.** A stops at its first fit (0.04–2.6 s). C's gains need up to 19–40 real CPU s per synthesis call: 7–15× A's
  CPU, and more than the share a formation round gives a component. B spends about 19 s for no gain.
* `replace-all…| rotate-k(k=1)` and `rotate-k(k=3)` gain nothing, although 35.1 shows a fold-correct Update in the
  language. With T's points only, the enumeration does not reach it within the cap.

### 35.3 Whole machine (P0-E part 2)

Script `research/q3/fold_reach_machine_dev.py`: `run_arm("D")` exactly as `active_dev.job` (Env(spec, 0, budget = 60),
cap 30 s, seed = sha256(name) mod 1000) on the 11 section 31 tasks. Only the last list component's synthesis call
differs (`FOLD_REACH_SYNTH`; B goes through the same hook). Each (arm, task) runs in a fresh process.
Solved = the hidden test of the opened development task (evaluation only). Challenge = the machine's own independent
SOURCE challenge.

| unit (runs) | A solved | B solved | C solved | C lost vs A |
|---|---|---|---|---|
| virtual (1; decisions reproduced in 3 reruns) | 0 | 0 | 1 (`identify-is-mod-k(k=7)`) | 0 |
| real, run 1 | 0 | 0 | 0 | 0 |
| real, run 2 | 0 | 0 | 0 | 0 |

* **The virtual-unit solve is causal but indirect, and not robust.** In C's run, the prefix machine formed at round 0
  with a C-built Update that folds all examples (153 candidates judged). The independent challenge **refuted** it.
  The task was then solved by the suffix machine, whose Update is the legacy first fit (C's search was not triggered
  there). A's prefix machine instead spent its budget in repair rounds, and A's suffix machine never got an Update.
  The difference is a budget and path effect, not a correct C-built Update. Under the real clock (run 1) C judges only
  60 candidates at round 0 and does not form. **Counted: 0 causal new solves for C under the official budget; 0 losses.**
* Formation CPU per arm is equal within 5% (virtual sums A 169.6, B 178.6, C 173.0 s). The passive fallback overshoots
  the cap in every arm under the virtual unit.
* A fold-consistent Update is not a correct one. The 8 final outputs do not identify the Update, as the refuted C
  prefix machine shows. The intermediate reachable states do: the T∪R fits in 35.1 score 20/20 fresh on 4 tasks.

### 35.4 Follow-up: observing the reachable states (`REACH_TRAJ`, opt-in). Not part of the matched comparison

The diagnosis locates the deficit in observation, not in the candidate set. So one observation-policy change was
tested within the SAME 60-query and 30 s budget: the agent's state trajectories are the initial examples' own
prefixes (their reachable fold states) instead of the synthetic ascending / descending / random ones. Synthesis is
as in A (arm D), or as in C (arm CD). This changes WHICH states are queried, not how many.

| arm | virtual (1 run) | real, full pass (1 run) | `rotate-k(k=1) \| identify-geq-k(k=2)`, real ×3 |
|---|---|---|---|
| A | 0 / 11 | 0 / 11 (A/B/C runs 1–2) | A 0 / 3 |
| D | 1 / 11 | 1 / 11 | **D 3 / 3** (challenge passed each time) |
| CD | 1 / 11 (the same task) | not run | — |

* **New solve, one task: `rotate-k(k=1) | identify-geq-k(k=2)`.** D's prefix machine queried 20 reachable states. Its
  round-0 Update already folds all examples. Two self-test counterexamples were localised and repaired, then the
  machine passed the independent challenge and the hidden test. On 300 random diagnostic SOURCE inputs it is
  correct 293/293 (`semantic_check_random300.jsonl`). With the same seed and budget, A forms a machine after 15 rounds
  (rounds 0–14, with an invented accumulator), and the challenge refutes it. D's trace is identical on both units. This is stable on both units (virtual 1/1, real 3/3,
  plus the full real pass) and caused by the observation policy alone (D = A's synthesis). Semantics: correct on the
  sampled inputs, not proven.
* **`prepend-k(k=10) | positions`.** The conflict of 35.1 is observed at round 0, and the existing rule adds the
  predicted component w = (6,) (W = [(), (6,)]) — the state change the diagnosis said was necessary, made by the
  existing mechanism. It then fails to synthesise that component's Update, and its 45 state queries exhaust the
  budget.
* **`identify-is-mod-k(k=7)`.** Round 0 folds all examples, but self-tests keep finding transition errors, and the 36
  state queries exhaust the budget. No other task is solved; C adds nothing on top of D (CD = D).
* Full prefix observation costs 20–45 of the 60 queries. That cost, not the language or the candidate set, is what
  stops the other representable tasks.

### 35.5 Decision (P0-F)

* **Why the programs fail.** The adopted Updates are right on every transition the agent observed and wrong on the
  reachable states of the initial examples, which the synthetic trajectories never visit (21/21 divergences). They
  fail because those states were not observed, not because the program set is too small: B adds candidates with no
  fold gain.
* **Is new state needed?** Proven for 1/10 (`prepend-k(k=10) | positions`, conflict witness), not for 6/10
  (constructive: a fold-correct Update in the current language with fixed W and z), open for 3/10. For the one proven
  case, the existing distinguishing-continuation rule produces the needed component once the conflict is observed
  (35.4). No new state-invention mechanism is justified by these 10 tasks yet.
* **Fold-constrained synthesis (C).** Fold gains occur at an equal 40 s real cap (5/10, A and B 0), but not within the
  official per-call share, and they did not turn into a robust solve. Per the directive's rule, fold gain was carried
  to machine formation (35.3), where it produced no causal solve under the official budget. Candidate expansion stops
  here: neither B nor C is a lever under the current budget.
* **Next mechanism, measured at development scale only.** The bottleneck is observing the folds' reachable states
  economically. That means choosing which example prefixes to query, so that the component conflict (positions) and
  the length / element cases (rotations, identify-*) are observed within the 60-query budget, and making the per-call
  synthesis cheap enough to use them. Development evidence for this direction: D newly solves 1 of 11 under the
  official budget (3/3 real replicates, A 0/3). That is one task in one lineage, so not a DEVELOPMENT PASS;
  GENERALIZATION OPEN. Not done: any FRESH or independent evaluation, query-economical prefix selection, or any change
  to the default path (`REACH_TRAJ`, `FOLD_REACH_SYNTH` stay off).

V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched. No FRESH / FORMAL seal opened, no per-task
answer coded, PR #780 stays Draft.


## 36. Budgeted reachability discovery (2026-11-15) — DEVELOPMENT ONLY

Directive "Q3 Budgeted Reachability Discovery": obtain the reachable-state information that formed the D solve
(section 35.4) with fewer SOURCE queries, and show whether it causes more machines and solves within the same
60-query / 30 CPU s budget. No new synthesiser and no candidate expansion. All CPU figures in this section are real
`time.process_time()`; the virtual clock of section 35 is not used for any verdict. Raw evidence:
`docs/experiments/dev/budgeted_reach/` (JSONL rows per run, `summary_*.json`, `freeze_E.json`, `SHA256SUMS`).

### 36.1 Where D's SOURCE queries go (P0-A)

Instrumentation (`research/q3/budgeted_reach_dev.py`; no effect on decisions):
* `active.QUERY_HOOK` sees every formation-state query call, whether it is answered from the cache or charged.
* A wrapper on `env.query` records every SOURCE charge and its phase (formation tag, challenge, committee,
  discrimination).
* Charged state queries are classified in the order they were charged, per machine direction: initial state,
  added state component, new length (a parent length above all observed ones), new element, or known region.

Findings, from the code and the base A/D/E pass:
* **Cache.** `Env.query` charges every call; there is no SOURCE-side cache. De-duplication is the agent's:
  `form_machine`'s `memo` (seeded with all earlier observations of the run), `challenge`'s `seen` set, and the
  committee and discrimination filters. On the 11 tasks D made 7 648 state reads, of which 7 062 (92 %) were cache
  hits. Only 3 SOURCE charges repeated an input, all inputs whose earlier answer was undefined: `obs` keeps only
  defined answers, so the next machine's `memo` lacks them. Calls and charges are reported separately below.
* **Total vs formation queries.** After formation, `committee_queries` spends whatever budget is left, so total
  queries are about 60 in every arm. Only formation-phase queries measure observation cost.
* **D's state queries (11 tasks): 498** = 6 initial + 107 new length + 129 new element + 177 known region (same
  lengths and elements already covered) + 79 for added state components.
* **The second (suffix) machine is the largest single waste.** With `REACH_TRAJ`, `trajs = examples`, and
  `form_machine` receives `ex + obs`. So D's suffix machine walks the prefixes of every earlier observation, not just
  the 8 initial examples. It spent 190 state queries (38 % of D's) at 6.3 CPU s in total and hit the query limit
  before any synthesis on 7 tasks.

D per task, base seed: formation calls / charged queries, then the charged queries by category.

| task | calls / charged | initial | new length | new element | known region | added component (states / screen) | localise | self-test | challenge | prefix / suffix machine queries (suffix CPU s) |
|---|---|---|---|---|---|---|---|---|---|---|
| `add-k(k=10) \| identify-is-prime` | 941 / 55 | 0 | 12 | 15 | 20 | 0 / 8 | 0 | 0 | 0 | 37 / 18 (0.0) |
| `identify-is-mod-k(k=7)` | 1453 / 55 | 0 | 14 | 6 | 22 | 0 / 0 | 9 | 4 | 0 | 23 / 32 (0.001) |
| `identify-is-prime` | 744 / 55 | 0 | 11 | 15 | 21 | 0 / 8 | 0 | 0 | 0 | 24 / 31 (0.001) |
| `positions \| append-k(k=3)` | 783 / 55 | 0 | 6 | 8 | 6 | 25 / 10 | 0 | 0 | 0 | 55 / - (-) |
| `pow-k(k=4) \| product` | 415 / 55 | 2 | 10 | 20 | 15 | 0 / 8 | 0 | 0 | 0 | 31 / 24 (0.0) |
| `prepend-k(k=-2) \| positions` | 917 / 55 | 0 | 6 | 9 | 10 | 30 / 0 | 0 | 0 | 0 | 55 / - (-) |
| `prepend-k(k=10) \| positions` | 838 / 55 | 1 | 7 | 8 | 7 | 24 / 8 | 0 | 0 | 0 | 53 / 2 (0.0) |
| `replace-all-k-with-n(k=5,n=0) \| rotate-k(k=1)` | 307 / 55 | 1 | 12 | 16 | 26 | 0 / 0 | 0 | 0 | 0 | 25 / 30 (0.001) |
| `rotate-k(k=-2) \| replace-all-k-with-n(k=1,n=2)` | 621 / 50 | 0 | 12 | 8 | 18 | 0 / 12 | 0 | 0 | 0 | 13 / 37 (6.289) |
| `rotate-k(k=1) \| identify-geq-k(k=2)` | 337 / 32 | 0 | 5 | 7 | 8 | 0 / 0 | 5 | 7 | 3 | 32 / - (-) |
| `rotate-k(k=3)` | 292 / 55 | 2 | 12 | 17 | 24 | 0 / 0 | 0 | 0 | 0 | 27 / 28 (0.0) |

### 36.2 Policy E (P0-B): `BUDGETED_REACH_TRAJ` (off by default), frozen in `1e1ddba`

* **Candidates.** Only transitions along the GIVEN initial examples' prefixes (`env.initial()`), in both machine
  directions.
* **Stage 1, before any Update.** A greedy plan maximises gain / marginal uncached SOURCE cost. The cost counts the
  state components of parent and child that are neither cached nor already planned. Gain = 2·new length +
  2·new element + 1·conflict probe (a seen element at an unseen parent length) + (examples sharing the prefix − 1);
  minimum gain 2, so known-region transitions are not observed. The whole plan is fixed from input-side signals
  before any planned answer is seen, then executed; a candidate whose cost exceeds the remaining budget is skipped.
* **Stage 2, after an Update exists and folds INITIAL examples wrongly.** On each failing example, E takes the
  first step whose predicted (state, element) pair was never observed (gain 3 + novelty). It replaces that round's
  binary-search localisation when it adds a usable transition.
* **Budget.** At most `REACH_BUDGET = 20` charged queries per run, shared by both machines (a development
  assumption, not a tuned optimum), with no duplicate charge. Already-observed candidates and candidates known to be
  undefined are excluded.
* **Mode.** The selected reachable transitions REPLACE the synthetic trajectories. Degraded mode: fewer than 3 usable
  reachable transitions → the synthetic trajectories (existing path); budget exhausted → no further E query, and the
  existing localisation / representation path continues. Both cases are recorded per machine.
* **Logged per candidate:** stage, example, step, features, gain, estimated and actual cost (equal in every
  executed case), usability, and the SHA-256 prefix of the observed transition.
* **Tuning on the 11 development tasks only.** The rejected variant E2 (synthetic + reachable) also solved
  `rotate-k(k=1) | identify-geq-k(k=2)` but used 545 vs 406 formation queries. Two defects found while tuning were
  fixed before freezing: stage 2 could re-select a cost-0 transition whose child is a blocked hidden-test prefix
  (an endless round loop), and it could take failing examples that were self-test counterexamples rather than
  initial examples. The freeze manifest records the code blob and the transfer task lists, both fixed before any
  transfer run.

### 36.3 A / D / E on the 11 development tasks (P0-C)

Same task set, seed rule, synthesiser, state grammar, challenge, fallbacks and 60 / 30 budget as `active_dev.job`.
Each (arm, task, seed) runs in a fresh process; rows in `dev11_ADE_run{1,2,3}.jsonl` (same seed) and
`dev11_ADE_seeds1_2.jsonl` (seeds sha256(name) + 7919·k).

| task | solved A / D / E (3 same-seed runs) | formation queries A / D / E | reach-state queries D / E | reachable transitions observed A / D / E | round-0 fold failures A / D / E | E degraded / fallback machines |
|---|---|---|---|---|---|---|
| `add-k(k=10) \| identify-is-prime` | 0/3 / 0/3 / 0/3 | 45 / 55 / 31 | 47 / 20 | 3 / 37 / 22 of 37 | 32 / — / 28 | 1 / 0 |
| `identify-is-mod-k(k=7)` | 1/3 / 0/3 / 0/3 | 15 / 55 / 42 | 42 / 16 | 5 / 14 / 12 of 18 | 3 / 0 / 3 | 0 / 0 |
| `identify-is-prime` | 0/3 / 0/3 / 0/3 | 45 / 55 / 38 | 47 / 20 | 11 / 26 / 22 of 26 | 31 / — / 25 | 1 / 0 |
| `positions \| append-k(k=3)` | 0/3 / 0/3 / 0/3 | 55 / 55 / 54 | 45 / 20 | 10 / 27 / 24 of 27 | 13 / — / 1 | 1 / 1 |
| `pow-k(k=4) \| product` | 0/3 / 0/3 / 0/3 | 34 / 55 / 36 | 47 / 20 | 1 / 24 / 17 of 32 | — / — / — | 1 / 1 |
| `prepend-k(k=-2) \| positions` | 0/3 / 0/3 / 0/3 | 55 / 55 / 55 | 55 / 20 | 7 / 30 / 21 of 32 | 9 / — / 13 | 1 / 1 |
| `prepend-k(k=10) \| positions` | 0/3 / 0/3 / 0/3 | 55 / 55 / 55 | 47 / 20 | 4 / 29 / 22 of 29 | 11 / — / 18 | 1 / 1 |
| `replace-all-k-with-n(k=5,n=0) \| rotate-k(k=1)` | 0/3 / 0/3 / 0/3 | 29 / 55 / 20 | 55 / 20 | 12 / 36 / 26 of 36 | 7 / — / 4 | 1 / 0 |
| `rotate-k(k=-2) \| replace-all-k-with-n(k=1,n=2)` | 0/3 / 0/3 / 0/3 | 30 / 50 / 25 | 38 / 20 | 7 / 21 / 17 of 21 | 10 / — / 1 | 1 / 0 |
| `rotate-k(k=1) \| identify-geq-k(k=2)` | 0/3 / 3/3 / 3/3 | 52 / 32 / 30 | 20 / 16 | 13 / 24 / 22 of 30 | 16 / 0 / 3 | 0 / 0 |
| `rotate-k(k=3)` | 0/3 / 0/3 / 0/3 | 27 / 55 / 20 | 55 / 20 | 4 / 28 / 17 of 36 | 5 / — / — | 1 / 0 |

Totals over the 11 tasks, run 1:

| | A | D | E |
|---|---|---|---|
| formation SOURCE queries | 442 | 577 | **406** |
| state-observation queries (D: states; E: reach + states) | 283 | 498 | 290 |
| formation query calls / of them cache hits | 6 821 / 6 375 | 7 648 / 7 062 | 7 313 / 6 905 |
| reachable transitions observed (answer component, of 324) | 77 | 296 | 222 |
| verified state conflicts (component added from an inconsistency) | 2 | 3 | 2 |
| Updates synthesised (rounds with an Update) | 47 | 12 | 40 |
| machines formed / challenge passed | 2 / 1 | 1 / 1 | 1 / 1 |
| solved, same seed ×3 | mod7 1/3 | geq 3/3 | geq 3/3 |
| solved, seeds 1 and 2 | 0, 0 | 0, 0 | 0, 0 |
| formation CPU (real s) | 168.2 | 113.9 | 152.7 |

* **Stability.** D and E are stable on the base seed: same solve in 3/3 runs, formation queries 577 (D) and
  406–407 (E) in every run. A's mod7 solve appears once in three same-seed runs (timing), so it is not counted.
* **Robustness to the query path.** With seeds 1 and 2, neither D nor E solves anything. The geq solve depends on the
  self-test and challenge inputs that the base seed draws.
* **Query efficiency.** On the solved task E uses 30 formation queries (16 reachable) where D uses 32 (20); over the
  11 tasks 406 vs 577 (−30 %), observing 222 of D's 296 reachable transitions. E's planning cost is negligible:
  formation CPU is 152.7 s for E vs 168.2 s for A.

### 36.4 Transfer of the frozen E (P0-E)

Frozen policy and task lists in `freeze_E.json` (committed in `1e1ddba` before any transfer run):
* 60 list-routines tasks unsolved in the Gate E baseline (all except the 11);
* 24 Gate E-solved tasks as a regression check.

No policy change after freezing. D was run on the first 18 of the 60 only; it was dropped to finish within the
session. FRESH-dev (the other opened lineage) was NOT run: it needs the pinned MBPP / HumanEval files fetched and
sandboxed reference execution.

| set | A solved | D solved | E solved | E new vs A | E lost vs A | formation queries A / E | formation CPU A / E |
|---|---|---|---|---|---|---|---|
| 60 unsolved | 1 | 2 (of 18 run) | 4 | 3 | 0 | 2 144 / 2 186 | 663 / 664 s |
| 24 solved | 24 | — | 21 | 0 | **3** | 507 / 649 | 72 / 120 s |

Replicates of every task whose outcome differed between A and E: 3 same-seed runs plus seeds 1 and 2, so 5 runs
per arm (`transfer_changed6_*.jsonl`). Correctness = random diagnostic SOURCE inputs (outside the budget).

| task | A solved | E solved | E correct on random inputs | reading |
|---|---|---|---|---|
| `identify-k(k=-2) \| remove-mod-k(k=2)` | 0 / 5 | **5 / 5** | 271 / 271 | robust new solve by E |
| `count-k(k=10)` | 2 / 5 (seeds 1, 2 only) | **5 / 5** | 298 / 298 | E robust; A only on other seeds |
| `uniq \| is-squares` | 0 / 5 | 3 / 5 | **247 / 270** | hidden test passed, semantically wrong: not counted |
| `reverse \| identify-is-mod-k(k=7)` | 4 / 5 | 4 / 5 | 295 / 295 | the base-run loss was noise |
| `keep-mod-k(k=2) \| pow-k(k=3)` | 4 / 5 | **0 / 5** | — | **robust regression** |
| `remove-mod-k(k=3) \| add-k(k=-2)` | 5 / 5 | **0 / 5** | — | **robust regression** |

* **Where E's new solves come from.** Both come from formed state machines with the independent challenge passed.
  E observed the reachable transitions that A's synthetic trajectories miss: round 0 already folds every example on
  `identify-k(k=-2) | remove-mod-k(k=2)`. On the 18 tasks D was run on, D solves the same two with more formation
  queries: 27 and 31, against E's 23 and 23.
* **Where the regressions come from.** Both are CASE 2. A forms at round 0 on its short synthetic table in 0.3–1.4 s.
  E's reachable-only table gives "no update for component 0" in both machines, and E's frozen fallback (only when
  fewer than 3 reachable transitions are usable) does not return to the synthetic table. On the 24 solved tasks E
  also costs more: 649 vs 507 formation queries, 120 vs 72 formation CPU s.

### 36.5 First failures (P0-F)

First failure of every run, from machine events (`research/q3/budgeted_reach_cases_dev.py`):

| arm, set | solved | CASE 1 (query limit before an Update) | CASE 2 (no Update on the first observed table) | CASE 2b (Update, fold fails, re-synthesis fails) | CASE 3 (added component's Update) | CASE 4 (fold passed, self-test / challenge refutes) | other |
|---|---|---|---|---|---|---|---|
| A, dev 11 | 1 | 0 | 1 | 5 | 3 | 1 | 0 |
| D, dev 11 | 1 | 0 | 6 | 0 | 3 | 1 | 0 |
| E, dev 11 | 1 | 0 | 4 | 2 | 2 | 2 | 0 |
| A, transfer 60 | 1 | 2 | 15 | 15 | 1 | 1 | 25 |
| E, transfer 60 | 4 | 4 | **22** | 2 | 1 | 4 | 23 |
| E, solved 24 | 21 | 0 | **3** | 0 | 0 | 0 | 0 |

"other" covers undefined states (too few defined transitions), counterexamples that cannot be localised, and
machines whose fold passed but that did not form before the limits.

* **CASE 1: 20 queries do not suffice.** Rare as a first failure (4/60). The budget mostly runs out in the SECOND
  machine: 42 transfer machines were degraded and 27 fell back to the synthetic trajectories. The prefix machine
  uses 5–20 of the 20 queries (median 15), so the cause is how the budget is split across machines, not missing
  information.
* **CASE 2: the needed states are observed but no Update is synthesised.** This is the dominant failure of D and E,
  and the cause of both E regressions. Replay on E's own tables (36.6) shows the unchanged synthesiser finding
  correct Updates at a 10–20 s per-call cap (about 5 s used). The cost of using the new transition constraints is
  therefore CPU allocation within a round, not candidates or language.
* **CASE 3: a conflict or continuation component is added, then its Update is not synthesised.** The positions tasks
  (2/11) and 1/60. This is the problem of executing a new state component; it is separated and not addressed here.
* **CASE 4: the fold passes, then the self-test or the challenge refutes.** mod7 (dev) and 4/60. The observed range is
  overfitted. The refuting counterexamples are kept as recorded; no verification criterion was relaxed.
* **CASE 5: candidate computation cost cancels the SOURCE saving.** Not observed: planning is negligible, and E's
  formation CPU is 152.7 s against A's 168.2 s (dev) and 664 s against 663 s (transfer 60). But where A forms quickly
  (the 24 solved tasks), E's CASE 2 failures cost more CPU (120 vs 72 s).

### 36.6 Follow-up for CASE 2: the existing synthesis CPU floor. Not part of the frozen comparison

The CASE 2 replay (`case2_replay.jsonl`) captured E's own first Update-failure tables and gave them to the UNCHANGED
synthesiser at real caps of 5 / 10 / 20 / 40 s:
* `rotate-k(k=3)` fits at a 10 s cap, using 4.8 s: fold errors 0 and **40 / 40** fresh SOURCE inputs.
* `replace-all-k-with-n(k=5,n=0) | rotate-k(k=1)` fits at a 20 s cap, using 4.9 s: fold 0 and **40 / 40**.
* `rotate-k(k=-2) | replace-all-k-with-n(k=1,n=2)` (suffix table) fits at 5 s: fold 0, 29/39 fresh.
* `identify-is-prime` and the `pow-k(k=4) | product` prefix table do not fit even at 40 s.

The synthesiser's internal phase limits are fractions of the cap, so the per-round share in a machine (about 4.5 s)
misses fits that need only about 5 s of actual CPU at a 10–20 s cap. This is CASE 2 ("needed states observed,
Update not synthesised") resolved as a CPU-allocation problem, not missing information or language.

The existing `MIN_SYNTH_CPU` floor (section 30; 10 s; a reallocation inside the same 30 s) was therefore run on A
(AF, control) and E (EF) on the 11 tasks, 3 same-seed runs (`followup_floor_run{1,2,3}.jsonl`):

| arm (3 same-seed runs) | solved per run | formation queries per run | formation CPU per run |
|---|---|---|---|
| A (no floor; runs 1–3 of 36.3) | mod7 in 1 of 3 runs | 442 / 470 / 470 | 168 s (run 1) |
| E (no floor) | geq (3/3) | 406 / 407 / 407 | 153 s (run 1) |
| **AF** = A + floor | `prepend-k(k=-2) \| positions` 3/3, `rotate-k(k=3)` 3/3 | 351 / 397 / 355 | 183 / 185 / 183 s |
| **EF** = E + floor | mod7 **3/3**, geq **3/3**, `prepend-k(k=-2) \| positions` 2/3, `rotate-k(k=3)` 2/3 | 381 / 387 / 385 | 158 / 156 / 149 s |

* The floor alone (AF vs A) adds 2 stable development solves.
* E's observations plus the floor (EF) add mod7 3/3, which neither AF nor E solves (0/3 each), and keep geq 3/3,
  which AF does not solve (0/3). EF's two floor-only solves are less stable (2/3 each).
* All solves are correct on 271–297 random inputs.
* This follow-up was designed after seeing the 11 tasks and has NOT been frozen or transferred, so it counts only as
  a development indication.

### 36.6b Verdicts (P0-D)

* **QUERY EFFICIENCY PASS (development, narrow).** E obtains the reachable information behind every D solve with
  fewer SOURCE queries, and loses no D solve on the 11 tasks or on the 18 transfer tasks D ran:
  * geq: 30 vs 32 formation queries (16 vs 20 reachable), identical in 3/3 runs;
  * `count-k(k=10)`: 23 vs 27; `identify-k(k=-2) | remove-mod-k(k=2)`: 23 vs 31;
  * all 11 development tasks: 406 vs 577.
  Real CPU is not higher than A's on the 11 (152.7 vs 168.2 s) or the 60 (664 vs 663 s), but it is higher on the
  24 already-solved tasks (120 vs 72 s).
* **CAUSAL DEVELOPMENT PASS: NOT reached.**
  * Development 11: E solves geq 3/3 where A solves it 0/3, but D solves it too (no gain over D), and with seeds 1 and 2
    neither D nor E solves anything.
  * Frozen transfer: E has 1 fully robust new solve (`identify-k(k=-2) | remove-mod-k(k=2)`, 5/5 vs 0/5) and 1
    seed-robust one (`count-k(k=10)`, 5/5 vs 2/5). It also has 2 robust regressions (`keep-mod-k(k=2) | pow-k(k=3)`
    0/5 vs 4/5; `remove-mod-k(k=3) | add-k(k=-2)` 0/5 vs 5/5), with more CPU on those tasks.
  * Net change in correct solves vs A is 0 under the same caps. Fewer queries alone is not claimed as more
    intelligence.


### 36.7 Decision and the next first failure

* **Observation economy works as designed.** Observing only what has novelty (new parent lengths, new elements,
  post-Update path gaps) keeps every D solve with about 30 % fewer formation queries. Most of D's extra cost was
  known-region states and a second machine that re-walks every earlier observation.
* **The binding constraint after observation is CASE 2.** On the reachable tables the needed states are present
  (constructive: 40 / 40 fresh-correct fits on `rotate-k(k=3)` and `replace-all…| rotate-k(k=1)` from E's own
  tables), but the per-round synthesis share is too small for the synthesiser's own phase fractions.
* **E's replace-mode table is also harder than A's synthetic table on tasks A already solves** — the two robust
  regressions. A fallback that triggers only on observation shortage does not cover a synthesis shortage.
* **Not implemented here** (it would need a new freeze and a transfer set not used in this section): E whose
  fallback also returns to the synthetic table when the first reachable table yields no Update, combined with a
  per-round synthesis floor. The floor follow-up (36.6) is the development indication for this. The 84 transfer tasks
  of 36.4 are now used and cannot serve as its held-out set.
* No new synthesiser, no candidate expansion, no change to the default path (`BUDGETED_REACH_TRAJ`, `REACH_TRAJ`,
  `MIN_SYNTH_CPU` stay off). Q6 core untouched.

V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched. No FRESH / FORMAL seal opened, no per-task
answer coded, PR #780 stays Draft.


## 37. CASE-2 synthesis fallback: opt-in implementation only (2026-11-15) — NOT A NEW DEVELOPMENT RESULT

The section 36 frozen policy E reduced formation SOURCE charges 577→406 on the 11 tasks (−29.6% against D); its transfer had two robust wins but two robust regressions against A. In the failed tasks, E's reachable-only transition tables failed to yield an Update within the available CPU share. This observation motivates a narrowly scoped safety fallback, but the original 84 transfer tasks are *spent for this policy selection* and cannot be presented as fresh evidence for a revised E.

**Change:** `active.E_SYNTH_FALLBACK = False` is a new opt-in flag (the default is unchanged). If E is active in `REACH_MODE="replace"`, its reachable-only main-round `attempt` returns no Update and the formation deadline has not expired, the machine:
1. records `reachability synthesis fallback: synthetic trajectories`;
2. clears the active reachable transition-point list (does not erase already paid SOURCE observations, cache or audit log);
3. restores the original synthetic trajectories and tries synthesis again on the following round;
4. permits this fallback only once per machine, preserving the SAME global 30 CPU-s and 60 SOURCE-query caps.

This is a *degraded-mode intervention* against SECTION 36 CASE 2. It does not modify the synthesiser, repair, independent challenge, Q6 or any sealed material. The independent `MIN_SYNTH_CPU` policy is already available and remains off by default. A targeted test checks that fallback is absent when disabled, occurs at most once when enabled after forced no-Update and never exceeds the SOURCE limit.

**Important limitations:** fallback is not guaranteed to recover A's successes because E has already spent resources observing reachable states, and the resumed synthetic search receives only the remaining budget. Neither independent performance nor 84-task net gain nor actual cost advantage has been measured for this intervention. Do not call this CAUSAL DEVELOPMENT PASS. The next experiment requires a NEW preregistered evaluation set: freeze all code and policy parameters, run matched A / E / E+fallback / E+fallback+10s-floor arms on new opened development tasks, and inspect both gains and regressions with actual `time.process_time()`. The additional CPU-floor option must be accounted as reallocation within, not an extension beyond, total formation deadline. Retain original semantics checks and challenge.

**Official gate unchanged:** V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN; Q6 untouched.


## 38. CASE-2 recovery on a pre-registered new evaluation set (2026-11-15) — DEVELOPMENT ONLY

Directive "Q3 CASE-2 Recovery & Independent Transfer". Question: does the section 37 synthetic fallback remove E's
Update-synthesis regressions while keeping E's SOURCE economy, and does any E-family arm solve more than A within the
same 30 CPU s and 60 SOURCE queries? Constraints: no candidate expansion, no new grammar, no increase of the total
CPU cap. All CPU figures are real `time.process_time()`. Raw evidence: `docs/experiments/dev/case2_recovery/`.

### 38.1 Fallback check (P0-A)

* **Code review of `E_SYNTH_FALLBACK`** (`85fa80a`, `5f2d517`, by another session):
  * It fires once per machine, only when E's reachable-only table (replace mode, synthetic trajectories still
    unused) returns no Update in a main-round attempt before the formation deadline.
  * It restores the synthetic trajectories and clears only the active reachable points. Paid observations, cache
    and audit log are kept.
  * After it fires, E's stage 1 and stage 2 are off. The SOURCE and CPU caps are unchanged, and so are the
    challenge, repair and the synthesiser.
* **Tests and CI.** Locally the Q3 test files pass (32 / 32, Python 3.11, CI pins), including the new fallback test.
  CI on the base `5f2d517`: all four checks pass (CI, sequence experiment, receipt contracts, and the
  reproduction of the section 35 evidence).
* **Functional debug, NOT counted.** On the two section 36 regression tasks (`keep-mod-k(k=2) | pow-k(k=3)`,
  `remove-mod-k(k=3) | add-k(k=-2)`; already used, so debugging only):
  * E fails both again ("no update for component 0" in both machines);
  * EFb and EFbc recover both: the fallback fires once, round 1 folds every example, the challenge passes, and the
    random diagnostic inputs are 298 / 298 correct, with 23–24 formation queries;
  * EFbc spends 10.8–11.5 s of prefix-machine CPU against EFb's 4.8–6.1 s, because the 10 s floor is first spent on
    the failing reachable table.

### 38.2 New evaluation set (P0-B), committed in `f9a14d7` before any run on it

`research/q3/case2_eval_set_dev.py`; `eval_set.json`, `prereg.json`.
* **24 new two-routine compositions** of the independent author's routines (same lineage):
  * the composition rule of `env_listroutines.tasks()`, with the seed string `compose:neumann-q3-case2-eval-v1`;
  * the existing 228 names are excluded;
  * the unchanged Env and input generator (8 initial examples, 10 hidden tests);
  * output-type quotas proportional to the existing 120 compositions: L 18, I 4, B 2 (29 candidates drawn).
* **12 regression tasks:** Gate E-solved and never used in a policy-E experiment, first 12 by a salted hash.
* Each task's name and the SHA-256 of {name, train, test} were committed before any run. The hidden tests enter only
  the hash.
* The counts are a development design assumption with no statistical power claim. The tasks share the list-routines
  lineage, so success would not show transfer to another problem domain.

**Arms (frozen in `prereg.json`), each with 30 CPU s and 60 SOURCE queries:**

| arm | observation | synthesis-failure fallback | per-round synthesis floor |
|---|---|---|---|
| A | synthetic trajectories | — | 0 |
| E | budgeted reachability (section 36, frozen) | — | 0 |
| EFb | budgeted reachability | once per machine | 0 |
| EFc | budgeted reachability | — | 10 s (a reallocation inside the formation deadline) |
| EFbc | budgeted reachability | once per machine | 10 s |

Verified solve = the hidden test passed AND every random diagnostic SOURCE input correct. The first pass is all
5 arms × 36 tasks on the base seed. Every task whose verified outcome differs between arms was rerun twice more on
the same seed and on seeds 1 and 2, for all 5 arms.

### 38.3 First pass: 5 arms × 36 tasks, base seed (`run1_all36_5arms.jsonl`)

| arm | verified new 24 | verified regression 12 | hidden-test solved (36) | challenge passed | formation SOURCE queries | reach queries | first-Update success (machines) | fallback runs / then verified | total CPU s | formation CPU s | CPU s per verified solve |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 14 | 11 | 26 | 22 | 976 | 0 | 34 / 53 | 0 / 0 | 697.1 | 251.9 | 27.9 |
| E | 15 | 11 | 26 | 19 | 951 | 586 | 30 / 51 | 0 / 0 | 691.2 | 228.1 | 26.6 |
| EFb | 15 | 11 | 27 | 20 | 1108 | 586 | 29 / 51 | 11 / 4 | 700.5 | 249.2 | 26.9 |
| EFc | 16 | 11 | 27 | 19 | 936 | 579 | 32 / 49 | 0 / 0 | 714.0 | 276.4 | 26.4 |
| EFbc | 16 | 11 | 27 | 18 | 942 | 538 | 31 / 43 | 9 / 4 | 718.1 | 280.5 | 26.6 |

* **No arm has a verified loss against A in this pass.** Every arm verifies 11 of the 12 regression tasks. The 12th,
  `identify-k(k=1) | kth-smallest(k=2)`, is semantically wrong in every arm that passes its hidden test (231–233 of
  234 random inputs), so it counts for nobody.
* **The fallback fired in 11 EFb runs and 9 EFbc runs, and changed no verified outcome.** On every task where it fired,
  A and E already had the same verified result. The section 36 regression type — A solves, E fails because its
  reachable-only table yields no Update — occurred on none of the 36 tasks.
* **Formation SOURCE queries:** the fallback raises EFb's to 1 108, against A's 976, because after a fallback the
  synthetic states are observed in addition to the reachable ones already paid for. The floor arms use fewer:
  EFc 936, EFbc 942.

### 38.4 Replication of every task whose outcome differed (3 same-seed runs + seeds 1 and 2)

Raw rows: `changed3_runs2_3.jsonl`, `changed3_seeds1_2.jsonl`. Verified solves over 5 runs:

| task | A | E | EFb | EFc | EFbc | A + floor (post hoc, not in the pre-registered verdict) |
|---|---|---|---|---|---|---|
| `rotate-k(k=1) \| intersperse-k(k=0)` (new) | 1 / 5 | **5 / 5** | **5 / 5** | **5 / 5** | **5 / 5** | 1 / 5 |
| `mult-k(k=10) \| rotate-k(k=-2)` (new) | 0 / 5 | 1 / 5 | 1 / 5 | **5 / 5** | **5 / 5** | 5 / 5 |
| `identify-k(k=1) \| kth-smallest(k=2)` (regression) | 0 / 5 (4 wrong hidden-test passes) | 0 / 5 (2) | 0 / 5 (4) | 0 / 5 (0) | 0 / 5 (0) | — |

Every verified solve is correct on all random inputs: 297 / 297 and 270 / 270.

Attribution:
* **`rotate-k(k=1) | intersperse-k(k=0)`: the reachable observation.** Every E arm solves it 5 / 5; A and A + floor
  solve it 1 / 5. A's machine passes the challenge but fails the hidden test, so the challenge did not catch A's
  wrong Update.
* **`mult-k(k=10) | rotate-k(k=-2)`: the CPU floor alone.** A + floor solves it 5 / 5, and E without the floor 1 / 5.
* **`identify-k(k=1) | kth-smallest(k=2)`:** the fallback restores the hidden-test pass rate (E 2 / 5, EFb 4 / 5,
  A 4 / 5), but the recovered program is wrong. This is the case where too few counterexamples let a wrong Update be
  adopted.

### 38.5 Verdicts (P0-E)

* **REGRESSION RECOVERY PASS: not established on independent evidence.**
  * The pre-registered set contains no instance of the section 36 regression type, so the fallback had nothing to
    recover. It fired 11 times without changing a verified outcome.
  * It introduced no new regression: EFb has 0 verified losses against A, and 11 / 12 on the regression set, like A.
  * The mechanism itself works on the two section 36 cases (2 / 2 recovered, challenge passed, 298 / 298), but those
    tasks were used to build the fallback, so they are not counted.
* **CAUSAL DEVELOPMENT PASS: reached on development data, narrowly.** The pre-registered criterion — more verified
  solves than A on the 24 new compositions, robust over the replicates, with no robust verified regression on the 36
  tasks — is met by:
  * **EFc and EFbc: +2** (5 / 5 vs ≤ 1 / 5 on two tasks);
  * **E and EFb: +1**.
  The post-hoc A + floor runs show that the second EFc / EFbc task is solved by the floor alone. So the gain
  attributable to E's reachable observation is 1 task; the floor contributes 1 more on A or E alike. 24 tasks in the
  same lineage; no statistical claim.
* **EFFICIENCY PASS: not established.**
  * Every E arm has accuracy ≥ A's (26–27 vs 25 verified).
  * Total real CPU is equal within ±3 %: E 691 s (−0.8 %), EFb 701 (+0.5 %), EFc 714 (+2.4 %), EFbc 718 (+3.0 %),
    against A's 697. The only reduction, E's −0.8 %, is within run-to-run variation.
  * CPU per verified solve is 4–5 % lower in every E arm (26.4–26.9 vs 27.9 s), but only because there are more
    solves at about the same total.
  * Formation SOURCE queries: E −2.6 %, EFc −4.1 %, EFbc −3.5 %, EFb +13.5 %.
  Accuracy and cost are recorded separately as directed; no cost improvement is claimed.
* **GENERALIZATION: OPEN.** All tasks are in the same list-routines lineage.

### 38.6 The single bottleneck addressed (P0-F): exact memoisation inside the cover

* **Where the remaining failures are.** No verified regression remains to diagnose. Of the 8 new tasks that no arm
  solves, 6 have the same first failure in E: no Update on the first observed table (CASE 2). The floor also
  repeatedly turned a missed first fit into a solve.
* **What dominates synthesis time.** Profiling the unchanged synthesiser on a captured E table where it needs a 10 s
  cap (`rotate-k(k=3)`, `cover_memo_extra_table_rotate3_E.json`):
  * 31 % of the time is in `cells._cover`;
  * 2.1 s of 9.7 s is one linear scan, "the first piece whose coverage contains a mask", repeated from scratch at every
    enumeration level although the piece list only grows by appending.
  This is duplicate search over the same structure, not candidate order and not state representation.
* **The fix (opt-in, default off): `latent.COVER_MEMO`.** It memoises, within one construction, the first covering
  piece of each mask, scanning only pieces appended since the last lookup. This is exact on the default first-fit path
  (`_cover_memo` = `cells._cover` with the scans replaced). No candidate, grammar or budget change.
* **Check** (`research/q3/cover_memo_check_dev.py`, `cover_memo_check.jsonl`) on the 10 section 31 tables and the
  captured E table:
  * identical programs on 11 / 11 tables under the deterministic virtual clock, and the same AST 11 / 11 at real caps
    of 10 s and 40 s;
  * real CPU to the first fit −15 % (20.8 → 17.7 s at the 10 s cap; 21.2 → 18.0 s at 40 s, summed over the tables);
  * at the 5 s cap, 9 vs 9 fits — the speed-up is not yet enough to change fits at the official per-round share.
  * A test (`tests/test_fold_reach.py`) checks that the default is off and that the program is identical.
  This gain was measured on fixed tables only. Its machine-level effect needs a new pre-registered set: the 36 tasks
  here are now used.

V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched. No FRESH / FORMAL seal opened; earlier tasks
are not re-counted; no per-task code; PR #780 stays Draft.

## 39. Predictive State Invention (2026-11-16) — DEVELOPMENT ONLY

Directive "Q3 Predictive State Invention" (base: PR #780 at `50f27cf`; work on the separate branch
`ccr-99abe820-3phmf0`). Question: when the current state merges two prefixes u, v (z(u) = z(v)) whose futures differ
(F(u‖w) ≠ F(v‖w)), can the agent discover that distinction by experiment, invent a minimal executable latent state
z' = U(z, x), synthesise the method with it, and show with an ablation that the latent is necessary? All CPU figures are
real `time.process_time()`; every arm has 30 CPU s and 60 SOURCE queries. Raw evidence: `docs/experiments/dev/psi/`.

**Result in one line.** On the development tasks PSI invents the length counter that two positions tasks need, and the
ablation shows it is necessary. On the pre-registered independent set (46 latent-need tasks + 12 ordinary) PSI
adopts no latent at all, gives no invention evidence and loses 2 tasks to A robustly. The development success did not
transfer.

### 39.1 Phase 1 — the deficit (development tasks only)

* **Which tasks need a latent.** Developer-side classification with the reference function (never visible to the
  agent): the answer-as-state W = [()] is insufficient when two prefixes with the same answer and the same next element
  get different next answers. 15 of the 228 tasks are insufficient in both directions. With 3 positions compositions
  that are insufficient in the prefix direction, these give the 18 development tasks (`dev18_names.json`).
* **The existing invention already had the right latent and starved it.** On `prepend-k(k=10) | positions` the
  existing `invent()` listed the length counter among 267 admissible candidates. It gave each tried latent 0.03 of
  the remaining CPU (`INVENT_SYNTH_SHARE`), and no Update was found.
* **Oracle check** (`research/q3/psi_deficit_check_dev.py`, `phase1_deficit_check.txt`, unlimited oracle, not an agent
  result). It fits the list Update from the reachable transitions of the 8 initial examples with the unchanged R2 cell
  construction:

  | task | conflicting (state, e) | no latent, cap 20 s | latent h = len(u), cap 5 s | latent, cap 20 s | fresh fold |
  |---|---|---|---|---|---|
  | `prepend-k(k=10) \| positions` | 1 | no fit (12.9 s) | no fit (0.6 s) | fit in 0.68 s | 197 / 197 |
  | `prepend-k(k=-2) \| positions` | 2 | no fit (12.8 s) | no fit (0.6 s) | fit in 0.99 s | 199 / 199 |

  The fitted Update is `relcells m=(add $0 (mod 1 (add $2 1))) | ((eq $0 $3) ? value (add $4 1) : copy 0[$0])`.
  Without the latent no Update exists in the space searched. With it, the fit is fast but needs a large enough
  deadline *span*: the construction allots its stages as fractions of the span. This fact returns in iteration 11.

### 39.2 Mechanism (opt-in, default off; `neumann1/psi.py`, hooks in `neumann1/active.py`)

| directive interface | implementation | failure reasons it returns | cost it returns |
|---|---|---|---|
| `discover_distinctions` | `psi.discover_distinctions`: Bayesian experiment design over latent hypotheses (prior 2^(−size/6), soft down-weight 0.3 per equal outcome, hard elimination on a distinction). Pairs come from observed merged prefixes and from constructed pairs u, u·e, u·e·e (e an element that left the state unchanged), with confirmation of the merge. Each experiment is the (pair, suffix) that maximises the split entropy of hypothesis classes. | query budget, deadline, no informative experiment within budget, constructed pair rejected | SOURCE queries, tests, CPU |
| `invent_state` | `psi.invent_state`: candidate folds h' = G(h, e) of the generic substrate (`accumulators()`, the same list for every task) from starts 0 / 1 / below / above. A candidate is admissible if it separates every distinction and makes the observed transitions functional. Pairs of variables are used only if no single one is admissible. Ranking is by posterior or by the learned score. | no distinction observed, no admissible latent in the construction grammar | candidates, admissible singles, CPU |
| `synthesize_method` | the existing `attempt()` with the latent joined to the state, at `PSI_SYNTH_SHARE` = 0.6 of the remaining formation CPU, for the top `PSI_K` = 2 latents. The adopted Update is cached and reused while the table is unchanged; repair keeps a PSI latent after an "update not found" revision. | no Update within the synthesis budget; Update found but n initial examples fold wrongly | per-attempt remaining CPU |
| `verify_necessity` | the Pno arm: the same experiments and the same invention, with the latent withheld. Controls AR (repair only) and AF (CPU floor only). The independent SOURCE challenge and 300 random diagnostic inputs. `research/q3/psi_verdict_dev.py` | — | — |
| `update_discovery_policy` | `psi.update_discovery_policy`: class-balanced logistic regression on `psi.features` of every tried latent. Label = adopted AND the machine passed the challenge. `research/q3/psi_learn_dev.py` | — | experiences, positives |

**Where PSI is called:**
* (a) on inconsistent transitions, before the existing invention;
* (b) when no Update is found;
* (c) at an unlocalisable counterexample, only after the existing repairs (virtual value, invention, new
  continuation) found nothing.

**Degraded Mode:** every PSI failure returns False, and the unchanged existing path continues with whatever CPU and
queries remain. PSI's SOURCE queries come out of the same 60.

### 39.3 Development iterations (all on the 18 development tasks or the 68 training tasks; none on the evaluation set)

| it. | hypothesis | change | pass criterion | evidence |
|---|---|---|---|---|
| 1 | Ranking by fewest false splits finds the latent | false-splits-first ranking | P verifies a positions task that A does not | fail: parity was chosen over length |
| 2–5 | Distinction experiments were too few or badly chosen | Bayesian design, constructed pairs, soft per-test update, flatter prior, (u, u·e·e) pairs | the length counter ranks first on the positions tasks | intermediate raw runs `dev_iter_run1–4` (which iteration each file belongs to was not recorded): runs 1–2 on 18 tasks, P 3 = A 3; run 4 on 4 positions tasks verifies both `prepend-k \| positions` |
| 6 | The adopted latent was lost to re-synthesis | `psi_cache` reuse of the Update found with the latent | no loss after adoption | positions solves kept |
| 7 | The positions failure also shows up as an unlocalisable counterexample | PSI hook there; share 0.6; in-place repair for PSI arms and the AR control | no regression | kept; see iteration 12 |
| 8 | `revise()` discarded the correct latent after one synthesis failure | protect a PSI latent; one re-synthesis with the PSI share (tol = 0 was too strict, reverted in 9) | positions solved | — |
| 9 | Full run on 18 tasks | — | P ⊇ A and P-only > 0 | `dev18_iter9_A_AR_P_Pno`: verified A 3, AR 3, **P 5**, Pno 3. P-only: both `prepend-k \| positions`. No verified loss. |
| 10 | kth tasks starve in discovery (identical suffixes, deadline) | hypothesis-class collapse, suffix rotation | kth(k=3) solved | `train68_iter10_P` (and an 8-task subset run, `dev_iter_run6`): kth(k=3) not solved. **Regression: kth-smallest(k=2) and kth-largest(k=2) lost** (PSI spent up to 12.1 s at the unlocalisable hook) |
| 11 | A per-machine PSI CPU allowance gives a Degraded-Mode guarantee | `PSI_CPU_FRAC` 0.35, and the unlocalisable hook moved after the existing repairs | P ⊇ A on dev, both positions solves kept | `train68_iter11_cap035_P_rejected`: kth(k=2) back, **`prepend-k(k=-2) \| positions` lost**. The correct latent ranked first but had a 2 s span (the construction's stage fractions, 39.1) → **rejected** |
| 12 | The hook order alone removes the regression | `PSI_CPU_FRAC` = 1.0 (no allowance), hook order of 11 kept | as 11 | `train68_iter12_P` + `dev18_iter12_Pno`: P verifies A's 3 + both positions tasks. Pno verifies A's 3 only → **pass, frozen** |

### 39.4 Invention evidence on the development tasks (not counted as a new result)

Both evidence lines are from iteration 12 (`train68_iter12_P.jsonl`); A, AR and Pno fail both tasks.

* **`prepend-k(k=-2) | positions`**
  * *Why the old representation failed:* the answer `positions(u)` merges prefixes that differ by zeros.
  * *Distinctions:* 3, found in 10 queries, e.g. u = [], v = [0, 0], w = [3] → [0, 1] vs [0, 3].
  * *New state:* h' = h + 1 from 0, chosen among 1830 admissible single latents.
  * *Update:* the relcells program of 39.1.
  * *Ablation:* Pno is not solved.
  * *Independent verification:* challenge passed, 297 / 297 random inputs correct.
* **`prepend-k(k=10) | positions`**
  * *Why the old representation failed:* same merge as above.
  * *Distinctions:* 2, in 9 queries, e.g. [0] vs [0, 0] with w = [1].
  * *New state:* the same counter, chosen among 1841 admissible.
  * *Update:* the same program.
  * *Ablation:* Pno fails.
  * *Independent verification:* challenge passed, 295 / 295.

The tasks are development tasks and the mechanism was iterated on them, so this is evidence that the mechanism *can*
work, not a result.

### 39.5 Phase 4 — discovery-policy learning

* **Experience.** Every latent PSI tried in the P runs of iterations 10 and 12 on the 68 training tasks: the 18
  development tasks plus the 60 section 36 transfer tasks, 10 of which overlap. Iteration 11 is excluded (it had a
  different synthesis budget).
* **Data.** 27 experiences from 12 tasks, 4 positives. The positives come from only 2 tasks (the positions counter,
  once per iteration).
* **Weights (`policy.json`).** reads_e −3.62, keeps_h +1.47, granularity −0.64, start_0 +0.61, size +0.52; the rest are
  small. The policy effectively learned "prefer a counter that does not read the element."
* **Caveat.** This is too little data for a general claim. The policy was frozen before the evaluation and compared
  there with the description-length order (Pl vs P).

### 39.6 Pre-registered independent evaluation (frozen in `2932a52` before any run on it)

* **Set** (`research/q3/psi_eval_set_dev.py`, `eval_set.json`, name + SHA-256 per task; the resolver refuses any
  mismatch):
  * `latent_need30`: the first 30 new two-routine compositions that are latent-need in both directions (seed
    `compose:neumann-q3-psi-eval-v1`; the 228 tasks and the section 38 compositions excluded; 654 drawn);
  * `ordinary12`: the first 12 that are not latent-need (regression check);
  * `fst16`: the first 16 latent-need hidden finite-state transducers of a second, developer-authored family
    (`research/q3/psi_fst_family.py`, seed `neumann-q3-psi-fst-v1`; 86 drawn).

  No evaluation task was in the training or development data.
* **Arms** (`prereg.json`):
  * A — baseline;
  * AR — A + in-place repair;
  * AF — A + the existing 10 s synthesis floor (the A+CPU-floor control);
  * P — PSI;
  * Pno — latent withheld;
  * Pl — learned policy;
  * PDq — P's queries replayed, solved passively.

  latent_need30 and fst16 got all six formation arms, ordinary12 got A and P, and PDq ran on the 12 tasks P solved.
* **Replication.** Every task whose verified outcome differed between arms got 2 more same-seed runs and seeds 1, 2.

**First pass, base seed** (`eval_run1_base.jsonl`; CPU in seconds; formation SOURCE queries):

| arm | verified latent_need30 | verified fst16 | verified ordinary12 | PSI rounds / adoptions | PSI CPU / queries | total CPU | formation queries |
|---|---|---|---|---|---|---|---|
| A | 6 | 0 | 7 | — | — | 1545.8 | 2431 |
| AR | 6 | 0 | — | — | — | 1331.4 | 1987 |
| AF | 5 | 0 | — | — | — | 1338.5 | 1577 |
| P | 5 | 0 | 6 | 77 / **0** | 276.9 / 292 | 1541.6 | 2423 |
| Pno | 6 | 0 | — | 68 / 0 (withheld) | 119.6 / 260 | 1330.7 | 2105 |
| Pl | 5 | 0 | — | 63 / **0** | 267.0 / 227 | 1333.7 | 1933 |

**Replicates** (`eval_replicate_*.jsonl`):
* `prepend-k(k=-2) | kth-largest(k=2)`: verified in A 4/5, AR 4/5, Pno 3/5; AF 0/5, P 0/5, Pl 0/5.
* `replace-index-k-with-n(k=2,n=10) | identify-k(k=1)` (ordinary): verified in A 5/5, P 0/5.

Both P losses are robust. No other task differs between arms.

### 39.7 Verdicts (rules frozen in `prereg.json`; computed by `psi_verdict_dev.py`, `eval_verdict.json`)

* **INVENTION EVIDENCE: none (0 of 46).** P adopted no latent on any evaluation task.
* **REGRESSION: 2 robust P losses against A**, both caused by PSI (39.8). They are reported, not excluded.
* **V1 rule (P vs A): not met.** P-only 0, A-only 2, net −2, p = 0.5.
* **V2 rule: not met.** 2 tasks are solved with an accepted m ≥ 2 machine that PDq does not solve, against a threshold
  of 5. Both (`identify-k(k=1) | kth-smallest(k=3)`, `modulo-k(k=2) | kth-largest(k=3)`) are solved identically by
  every arm through the *existing* invention, not by PSI.
* **V3 rule (Pl vs P): not met.** The solved sets are identical (6 = 6 on the 46 tasks) and CPU is equal
  (1333.7 vs 1333.1 s). With no adoption, the learned order never decided anything.
* **Official verdicts unchanged:** V1 PASS (sealed), V2 independent OPEN, V3 FAIL, Q3 OPEN, Q6 untouched.
* **The evaluation set is spent.** Any change made from here on turns it into development data.

### 39.8 Why PSI adopted nothing (post-hoc; no verdict depends on it)

* **Rounds on the evaluation set.** Of 77 P rounds, 53 observed no distinction (discovery stopped on "no informative
  experiment", the deadline or the 10-query budget), and 1 was cut by the SOURCE query limit. In the other 23, none of
  the top-2 latents led to an Update: 38 attempts found no Update in the budget, and 8 found one that folded the
  initial examples wrongly.
* **The hidden state is mostly outside the hypothesis space**
  (`research/q3/psi_posthoc_representability_dev.py`, `posthoc_fst_representability.txt`). The test asks whether the
  true automaton state is a function of some candidate fold. That holds for only 3 of the 16 FST tasks, among 2326
  integer candidates. Counters modulo k and predicates with task constants (x ≥ 10, x mod 3 = 0) are not small
  programs of the substrate.
* **Where the state is representable, the evidence is too thin to identify it.** In those 3 tasks PSI observed 2
  distinctions, which left 3087–5180 admissible single latents. The prior then ranked small wrong folds first
  ((sub $1 $0), (mul $0 $1), $1), and the capturing folds (size 19 and 29) were never tried with PSI_K = 2.
* **Regression 1** (`prepend-k(k=-2) | kth-largest(k=2)`). At "update not found", PSI spent 8.5 s on two wrong latents.
  The existing path then hit the deadline before it could add the second component that solves the task for A
  (Pno, which spends 3.6 s, keeps the solve). This is the iteration-10 failure type at a different hook.
* **Regression 2** (`replace-index… | identify-k(k=1)`). PSI's unlocalisable-counterexample round spent its 10 SOURCE
  queries without a distinction. The suffix machine then had 11 queries instead of 21, and the passive fallback that
  solves the task for A no longer did.

### 39.9 Next first failure

Identifiability, not discovery mechanics. A 10-query experiment budget yields at most 2–4 distinctions while
thousands of fold candidates stay admissible, so a prior over program size picks the wrong latent. The hypothesis
space also lacks modular counters and constant-bearing predicates (13/16 FST states). A next step must:
* (i) make experiments eliminate classes of candidates faster than queries are spent;
* (ii) widen the latent space without widening the admissible set;
* (iii) not charge a failed PSI round against the existing path. Both regressions came from PSI consuming the CPU or
  queries that A's path needed. A CPU allowance alone fails, because the latent construction needs its full span
  (iteration 11).

The dependent multi-variable latents of kth(k=3) (top-2 values) remain out of reach, as in development. Any such
change is development on a spent set and needs a new pre-registered set.

### 39.10 Reproduction

```
git checkout 2932a52        # frozen code, set, policy, criteria
export PYTHONHASHSEED=0 NEUMANN_PSI_POLICY=docs/experiments/dev/psi/policy.json
python -c "import json;e=json.load(open('docs/experiments/dev/psi/eval_set.json'));json.dump([t['name'] for g in ('latent_need30','fst16') for t in e[g]],open('/tmp/n46.json','w'));json.dump([t['name'] for t in e['ordinary12']],open('/tmp/o12.json','w'))"
python research/q3/budgeted_reach_dev.py --names-file /tmp/n46.json --arms A,AR,AF,P,Pno,Pl --out run1.jsonl --workers 4 --semantic
python research/q3/budgeted_reach_dev.py --names-file /tmp/o12.json --arms A,P --out run1.jsonl --workers 4 --semantic
NEUMANN_REPLAY_ROWS=run1.jsonl python research/q3/budgeted_reach_dev.py --names-file <P-solved names> --arms PDq --out pdq.jsonl --workers 4 --semantic
python research/q3/psi_verdict_dev.py --base run1.jsonl --reps rep2.jsonl rep3.jsonl seeds.jsonl --pdq pdq.jsonl
python research/q3/psi_learn_dev.py --rows docs/experiments/dev/psi/train68_iter10_P.jsonl docs/experiments/dev/psi/train68_iter12_P.jsonl --out policy.json
python -m pytest -q tests/test_psi.py
```

No FRESH / FORMAL seal opened, no sealed verdict changed, no section 35–38 task counted, no per-task code, no budget
increase; Q6 untouched; PR #780 stays Draft.
