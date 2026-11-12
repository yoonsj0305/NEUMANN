# NEUMANN 1 | Learned discovery policy: W1 decisions, common interface, iteration log
2026-11-12 | Development status. Nothing in this document is evidence for a gate. | Global Q1–Q7 OPEN

Authority: [Frozen North Star](frozen_north_star.md); issue #745; the owner's P0 directive of 2026-11-12
("Q3·Q6 decisive bottleneck"). Fixed and sealed: SECOND = FAIL, THIRD = PASS at its stated scope
(`second_evidence_seal.json`, `third_evidence_seal.json`; a test fails on any byte change). The OEIS FRESH 499 and
the A001 1 000 are not fetched. No existing gate or verdict is changed by anything below.

## 1. W1: what is reused, demoted, removed

| Component | Decision | Reason |
|---|---|---|
| Substrate, forward enumerator, executor (`invention_core`) | reuse as execution mechanism | exact, metered, shared by every arm |
| Goal table, derived inverse operators, traversal / history state (`spec_core`, THIRD) | reuse as execution and verification mechanism; **also the list specialist to beat** | THIRD PASS; its fixed schedule is developer-designed and is **not** counted as learned invention |
| Sequence specialist D | reuse as the sequence specialist to beat | strong classical baseline |
| Checkpoint runner, three-valued scoring, evidence seals | reuse unchanged | no rebuild of evaluation infrastructure |
| Macro compression, behavioural retrieval of whole programs as primitives, per-signature unigram prior of the old core | removed from the core path | SECOND FAIL: 10× work per candidate, no added capability |
| Case analysis at task level | stays deleted | no solved task on SOURCE (57 / 57) |
| Fixed schedule of THIRD (40 % for traversal hypotheses in a fixed order, full state only) | replaced by a policy | this is exactly the part that should be learned |

## 2. Minimal common interface (typed, no family names)

| Concept | Definition | Code |
|---|---|---|
| observation | typed examples (I, B, L); per-point specifications derived from an alignment relation read from the examples (equal length, subsequence, consecutive index) | `spec_core.subtasks` |
| hypothesis | `(kind, strategy, scope)`: kind = alignment relation; strategy = `body` (step operator over the full observable state) or `feature` (a latent state variable: a function of a strict subset `scope` of the state, joined to the rest by one shallow readout) | `discovery_core.solve` |
| executable method | a substrate program, or kind + step-operator program; typed inputs and output; returns failure outside its domain | `spec_core.run_solution` |
| verification | the method reproduces every TRAIN example (step operators: every supervised point) | `check` in `solve` |
| counterexample | a point a candidate gets wrong; it joins the sample and the search resumes | CEGIS loop in `solve` |
| policy update | `fit(experience)`: success rate of each hypothesis; description lengths of the symbols of verified methods per context; the latent variables that verified; the verified methods | `discovery_core.fit` |

Contexts are keyed by types, positions and the alignment relation only. The same code and the same policy object
serve lists and sequences.

## 3. Base proposer and policy: designed vs learned

| Designed (generic, identical in every arm) | Learned (the policy; removed in the causal control) |
|---|---|
| the hypothesis space: 3 alignment kinds × {body, feature × scopes} + direct search with inverse goals | how the CPU cap is divided among hypotheses and their order (`weights`) |
| readouts generated from the library by type: derived inverses for integer goals, every binary integer predicate for boolean goals | the generative order of step operators, latent features and direct programs per context (`costs`) |
| verification and counterexample loop | which latent variables to propose first on a new task (`features`): variables that verified earlier, re-instantiated on every scope of matching types and joined by a freshly generated readout |

An untrained policy is uniform and proposes nothing. Memory (complete verified methods of earlier tasks,
re-verified before use) is a separate switch so that "remembering an answer" and "having learned how to look"
can be told apart: a proposal re-uses a discovered latent variable, not a method, and the scope and readout it
ends up with need not be the ones it was discovered with. Arm `Cw` removes the proposals and keeps the weights
and costs, so the three learned parts can be attributed.

What will count as **invention-attributable**: a task solved by the arm with the learned policy and by none of
the same proposer without the learned policy, the memory arm, and the specialist.

## 4. Arms, causal control, cost accounting

| Arm | Definition |
|---|---|
| S | frozen THIRD core (specialist for lists; also run on sequences) |
| D | finite differences + Berlekamp–Massey (specialist for sequences) |
| A | base proposer, untrained policy, no memory |
| B | A + memory of verified methods; no policy learning. **This is the control with only the learned policy removed.** |
| C | B + learned policy (weights, generative costs, latent-variable proposals) |
| Cw | C without latent-variable proposals (attribution only; not part of the criterion) |

All arms: the same CPU cap per task, everything included (hypothesis generation, failed hypotheses, verification,
memory replay). Recorded per task: CPU, candidates, every hypothesis tried with its CPU and outcome. Recorded
once: CPU of the SOURCE experience run and of policy fitting. Candidate counts are never reported as compute.

## 5. Iteration protocol

One hypothesis, one criterion fixed before the run, one immutable record (§7). A FAIL is analysed by cause
(policy / representation capacity / counterexample learning) before anything is added. No independent family is
registered or opened while the SOURCE criterion fails.

## 6. Iteration 1 (defined before its run)

**Hypothesis H1.** A policy fitted on verified SOURCE experience (hypothesis weights + generative costs) lets the
same proposer, at the same CPU cap, solve held-out SOURCE tasks that it does not solve without the learned policy
(B), without memory (A), and that the specialists do not solve.

**Data.** SOURCE only: rule SOURCE (125 list functions) and OEIS SOURCE (187 sequences). 5-fold cross-validation
with a salted hash of the task id. Experience = the base proposer with the untrained policy on every SOURCE task
(`wake`), cap 120 CPU s on lists and 30 CPU s on sequences: the untrained policy divides the cap among up to 20
hypotheses on a list task, and a probe showed that the first latent features cost about 2 CPU s each. For a fold
the policy is fitted on the experience of the other four folds, both domains pooled (one policy). Only TRAIN-verified outcomes reach the policy; hidden tests never do. Evaluation cap:
6 CPU s per task for every arm.

**Criterion K (all four, in both domains).** Family-wise α = 0.05 over the four tests (2 domains × {C vs B, C vs A}),
Bonferroni: each exact two-sided McNemar p < 0.0125.

| | Condition |
|---|---|
| K1 | C vs B: at least 5 tasks solved by C and not B, and p < 0.0125 |
| K2 | C vs A: solved(C) > solved(A) and p < 0.0125 |
| K3 | at least 5 tasks solved by C and by none of A, B, S (and D on sequences) |
| K4 | total CPU(C) ≤ total CPU(B) |

PASS → W4 (register two independent families). FAIL → cause analysis; no family is opened.

**Stated in advance.** A feasibility probe on rule SOURCE (untrained policy, 20 s cap, an earlier version of the
proposer) solved 7 of the 68 tasks the THIRD core does not solve. If the experience run finds a similar number,
K1 at p < 0.0125 (8 : 0 or better) is at the edge on lists; on sequences the bound is not yet known. The
criterion is not adjusted to that.

## 6b. Iteration 2 (defined before its run; added while iteration 1's experience run was still in progress)

**Why now.** The experience run of iteration 1 finished its list half: with the untrained policy and 20× the test
cap it solved 7 SOURCE list tasks beyond the THIRD core (3–55 CPU s each). A policy that only re-allocates and
re-orders the same hypothesis space can amortise at most those. The binding limit is what the hypothesis space
can express, not how it is searched. Iteration 1 is still completed and recorded as defined.

**Idea.** SECOND: an invented operation used forward, as one more primitive, adds nothing. THIRD: an operation
used backward, through its inverse, removes most of the search. So every operation the system invents is tested
on self-generated data for recoverability of each argument from the result (`inverted.derive_op_inverses`); a
recoverable argument turns the invention into a decomposition operator. Goals are decomposed recursively and
every sub-goal is matched by hash against the forward bank (`inverted.RSearch`). The chain is:
experience → invented operation → derived inverse → new decomposition → solved task.

**Hypothesis H2.** The eight operations the system invented on SOURCE (the abstractions in
`invention_core_frozen.json`, unchanged since before FIRST), once inverted, let the goal-directed search solve
list tasks outside SOURCE that the same search without the inventions (V0) and the THIRD core (S) do not solve,
at the same CPU cap.

**Data.** Development validation: rule TARGET (125) and dc (199 usable). SECOND failed on these sets and they
are development-only from now on; they can never again be first-exposure evidence. No task content was read to
build the mechanism; it was built on SOURCE and self-authored tasks. Cap 6 CPU s per task.

**Arms.** S (frozen THIRD core); V0 (recursive goal graph, primitive inverses only: the control with the
inventions removed); V (V0 + inverted inventions). Self-play recoverability: f7 (append) both arguments, f3
(power) both, f0 and f2 one each; of these only f7 has list arguments and acts on list goals.

**Criterion J (all three, in both families).** Bonferroni over the two tests: exact McNemar p < 0.025.

| | Condition |
|---|---|
| J1 | at least 5 tasks solved by V and not V0, and p < 0.025 |
| J2 | at least 5 tasks solved by V and by neither V0 nor S |
| J3 | total CPU(V) ≤ total CPU(V0) |

**Stated in advance.** On SOURCE, where the inventions were learned (so not a clean test): V 62, V0 56, S 57;
V only 6, V0 only 0, p = 0.031. None of the 6 was solved by the old core, so none is a replay. The same count on
rule TARGET would miss J1 (6 : 0 gives p = 0.031; 7 : 0 is needed). The criterion is not adjusted to that.
Integer goals (sequences) are not covered by this iteration; a PASS on lists would be followed by the same
mechanism on integer goals, not by W4.

## 6c. Iteration 3 (defined before its run; owner's conditional approval of 2026-11-12)

**Fixed.** Iterations 1 and 2 stay FAIL. No further work on dividing the cap or re-ordering generation inside
the same hypothesis space. SOURCE only. No FRESH data, no new framework, no family-specific inventor, no new
model dependency. Q6 is not developed here.

**Mechanism (`neumann1/opgen.py`; one generic procedure, no operation written by hand).** For every SOURCE task
that arm B fails to TRAIN-verify, the system
1. proposes the function and type of an operation it lacks, as a gap specification (pieces → open goal): the
   pieces are the cheapest forward values of the context, or what is left of a list goal after an embedded
   piece is removed; the goal is the task's target, an unsolved sub-goal of the goal graph, or the per-point
   target of a traversal sub-specification;
2. synthesises an executable definition over the pieces alone (the task input is not visible to it);
3. runs the definition on self-generated arguments: it must be defined on at least half, not constant and not
   a projection; its behaviour there is the signature that identifies the operation across tasks;
4. tests on self-generated data which arguments are recoverable from the result; a recoverable argument makes
   the operation a decomposition operator in the goal graph;
5. keeps an operation only if gaps of at least two different tasks produced it (at most 8 per fold).
Vocabulary of definitions: the substrate plus `len`, which the system derived earlier as the inverse of `range`.

**Hypothesis H3.** Operations generated this way from the failures of other SOURCE tasks let the same system
solve held-out SOURCE tasks that it does not solve with the generation removed.

**Data and arms.** The 5 folds of iteration 1. For a fold, the policy and the operation set use the other four
folds only. Failures are defined by TRAIN verification; hidden tests never reach the generator. Cap 6 CPU s.

| Arm | Definition |
|---|---|
| A | fixed operation and representation space (iteration 1's arm A; rows re-used) |
| B | A + learned policy and memory (iteration 1's arm C; rows re-used) |
| Cn | B + recursive goal graph, no generated operation = **C with the generation removed** |
| C | Cn + generated operations (in every search at a fixed cost of 2; backward where recoverable) |
| S, D | THIRD core; sequence specialist (rows re-used) |

**Criterion G (all five, in both domains; lists = rule SOURCE, sequences = OEIS SOURCE).** Bonferroni over the
two domains for the causal test: exact two-sided McNemar p < 0.025.

| | Condition |
|---|---|
| G1 | a held-out task is solved by C with a generated operation whose behaviour on self-generated arguments differs from every primitive, from `len` and from each of the eight operations of the old core |
| G2 | at least 5 held-out tasks are solved by C with a generated operation in the method |
| G3 | at least 5 tasks solved by C and not Cn, and p < 0.025 |
| G4 | those tasks involve at least 2 distinct generated operations, none accounting for more than three quarters of them |
| G5 | total CPU(C) ≤ total CPU(Cn); the CPU of generation (specifications posed, definitions synthesised, failures) is reported |

Reported, not gating: C against B, A, S, D; tasks solved by C and by no other arm; the operation table per fold.

**Stated in advance.** On self-authored tasks the generator re-derives append from gaps (same behaviour as
the old core's f7) and nothing else. If SOURCE gives the same, G1 and G4 fail by definition even if G3 holds.
Constructors that the remaining list failures appear to need (interleave, insert at a position, merge) have no
short definition in this substrate, which has no simultaneous traversal of two lists; the generator is not
expected to find them. If the iteration fails, the next step is an analysis of the definition language, not a
larger budget.

## 7. Iteration records

| # | Hypothesis | Criterion | Result | Record |
|---|---|---|---|---|
| 1 | H1 | K1–K4, both domains | **FAIL** (lists: K1–K4 all fail; sequences: K1–K3 fail) | `docs/experiments/results/discovery_iter1_source_cv.json`, `discovery_iter1_cv_rows.jsonl`, `discovery_iter1_experience_rows.jsonl.gz` |
| 2 | H2 | J1–J3, both list families | **FAIL** (rule: J1, J2 fail; dc: J1 fails on p) | `docs/experiments/results/discovery_iter2_inverted_inventions.json`, `discovery_iter2_rows.jsonl.gz` |
| 3 | H3 | G1–G5, both domains | **FAIL** (every condition, both domains) | `docs/experiments/results/discovery_iter3_source_cv.json`, `discovery_iter3_ops_rows.jsonl`, `discovery_iter3_cv_rows.jsonl`, `substrate_probe_definitions.json` |

### Iteration 2 result (2026-11-12, 08:26–08:47 UTC; 972 / 972 jobs)

| Family | V | V0 (inventions removed) | S | V only / V0 only | McNemar p | Solved by V and neither V0 nor S | CPU s V / V0 |
|---|---|---|---|---|---|---|---|
| rule TARGET (125) | 63 | 60 | 61 | 4 / 1 | 0.375 | 3 | 395 / 429 |
| dc (199) | 158 | 151 | 151 | 8 / 1 | 0.039 | 8 | 243 / 304 |

**Verdict: FAIL** by the criterion fixed before the run (J1 needs ≥ 5 and p < 0.025 in both families).

What the record shows, without re-reading the criterion:
* The effect is real and has the predicted sign in both families: every task V gains is solved through the
  inverse of the invented append (rule: constant blocks before and after the input; dc: "append the k-th
  element", "repeat the input k times"), in 0.002–2.6 CPU s, and none is solved when the inventions are removed.
  Three of the five discordant tasks that are not of this kind (rule/c172, rule/c112, dc/078) are solved by the
  traversal state, which the inventions do not touch: they are timing noise of the CPU cap.
* The effect is small: +3 and +7 tasks. Pooled over the two families it is 12 : 2 (p = 0.013), which is not the
  registered test.
* Cause: of the eight inventions only one (append) is both recoverable and applicable to list goals. The
  mechanism is limited by how many invertible operations the system has invented, not by the search.
* The run shared the machine with the experience run of iteration 1 (8 processes on 4 cores); caps are process
  CPU time, and all three arms were affected alike.

### Iteration 1 result (2026-11-12; experience 07:51–09:00 UTC, cross-validation 14:13–14:43 UTC; 1 747 / 1 747 jobs)

The machine restarted between the experience run and the cross-validation; the experience rows (312 / 312) were
complete and were committed before the cross-validation started. No row was re-run.

Solved held-out SOURCE tasks, cap 6 CPU s (5-fold; the policy of a fold never saw its tasks):

| Domain | S (THIRD) | D | A (untrained) | B (A + memory) | C (B + learned policy) | Cw (C without proposals) |
|---|---|---|---|---|---|---|
| lists (125) | 57 | — | 58 | 59 | 59 | 58 |
| sequences (187) | 15 | 33 | 17 | 17 | 21 | 20 |

| Domain | K1: C only / B only, p | K2: C only / A only, p | K3: solved by C and no other arm | K4: CPU C / B |
|---|---|---|---|---|
| lists | 4 / 4, p = 1.0 — FAIL | 6 / 5, p = 1.0 — FAIL | 2 — FAIL | 392.4 / 390.6 — FAIL |
| sequences | 4 / 0, p = 0.125 — FAIL | 4 / 0, p = 0.125 — FAIL | 1 — FAIL | 1 001 / 1 020 — pass |

**Verdict: FAIL.** W4 is not started; no independent family is registered or opened.

Experience cost: 6 884 CPU s on lists (cap 120 s), 4 979 CPU s on sequences (cap 30 s). It verified 73 list tasks
(8 through a latent feature) and 25 sequences (7 through a latent feature).

Cause, by the three candidates of the protocol:
* **Representation capacity (binding).** With 20× the test cap and the untrained policy, the hypothesis space
  reached 7 list tasks beyond the THIRD core, each at 3–55 CPU s. A policy that re-divides the cap and re-orders
  generation inside that space had at most those to gain, and gained none: on lists the 4 tasks it wins and the 4
  it loses against B are both mostly cap-timing differences (one win comes from a proposal).
* **Policy.** It did learn (weights 0.57 for the list step operator against 0.03 for a latent scope; 72 verified
  methods; a list of latent variables) and it was used (10 list tasks and 4 sequences were solved through a
  proposal). But what it proposes on lists is what the proposer finds anyway. On sequences it adds 4 tasks, of
  which 1 is beyond every other arm including the specialist.
* **Counterexample learning.** Not the limit here: the candidates the policy needed were never generated.

Read together with iteration 2: the only learned component with a causal effect so far is an operation the
system invented and then inverted (12 : 2 pooled over two list families, below the registered thresholds). The
hypothesis space itself is still supplied by the developer. That, not the policy, is what Q3 has to change.

A third mechanism (splitting output positions by a searched predicate) was prototyped during the wait and then
withdrawn before any evaluation: it is one more developer-written decomposition and is not in the repository.

### Iteration 3 result (2026-11-12, 23:10–23:34 UTC; generation 223 / 223 tasks, cross-validation 624 / 624 jobs)

Generation, measured: 223 failed SOURCE tasks, 1 823 CPU s, **6 011 gap specifications posed, 11 definitions
synthesised** (10 distinct, in 6 tasks; none on sequences). One has support from two tasks: append, with the
same behaviour as the old core's f7. It is in the operation set of three of the five folds; the other two folds
have no generated operation.

| Domain | A | B | Cn (generation removed) | C | S | D |
|---|---|---|---|---|---|---|
| lists (125) | 58 | 59 | 59 | 57 | 57 | — |
| sequences (187) | 17 | 21 | 21 | 21 | 15 | 33 |

| | lists | sequences |
|---|---|---|
| G1 new operation used | none — FAIL | none — FAIL |
| G2 tasks solved with a generated operation | 3 — FAIL | 0 — FAIL |
| G3 C only / Cn only, p | 2 / 4, p = 0.69 — FAIL | 0 / 0 — FAIL |
| G4 at least two operations in the gain | one (append) — FAIL | none — FAIL |
| G5 CPU C / Cn | 405.2 / 404.6 — FAIL | 1 008 / 1 002 — FAIL |

**Verdict: FAIL.** Nothing is handed to Q6. No budget was increased.

Limits of this run itself: 6 list and 8 integer pieces per context, the root and the first open sub-goal of each
type, 0.25 CPU s per specification. A wider pool would re-derive append in more tasks. It would not change what
follows.

### Limit analysis: what the definition language can express (`research/q3/substrate_probe.py`)

Twenty standard constructors were specified by self-generated examples and given to the same synthesiser with
240× the per-specification budget (60 CPU s each; a found definition was re-checked on 40 fresh arguments).

| Found (definition holds on fresh arguments) | Not found in 60 CPU s (3.5–7.5 million candidates, cost level 8 completed) |
|---|---|
| append (0.2 s), reverse (0.2 s), last, sum, drop (0.1 s), count (0.5 s, through `len`), nth (1.1 s), snoc (9.3 s) | take, init, rotate, replace_at, insert_at, interleave, zip_add, gather, repeat, maximum, sort, unique |

* Reachable: one fold over one list, and "drop / nth through `range`". Not reachable: selection or edit by
  position, any simultaneous traversal of two lists, repetition, order statistics, de-duplication.
* The list failures that remain on SOURCE are of exactly the second kind (insertions and interleavings,
  positional swaps and rotations, counts and maxima inside a step, sorting).
* Several of the unreachable operations are easy for the THIRD core as a traversal with index and remaining
  count (take, init, replace_at). That state representation was written by the developer, and a generated
  definition cannot use it: a definition is a plain substrate program over its arguments.

**Conclusion of iterations 1–3.** Re-dividing the cap (1), inverting operations obtained by compression (2) and
synthesising operations from failure gaps (3) all fail their registered criteria, for one reason: what the
system can invent is bounded by the language its inventions are written in, and that language is weaker than
the developer-designed representation that produced THIRD. Autonomous invention in the sense of Q3 is **not
shown**. A larger search budget does not move this boundary (cost level 8 at 60 s; the missing definitions need
level 12 and beyond).
