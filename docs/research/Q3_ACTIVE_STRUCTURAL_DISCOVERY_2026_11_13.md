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
