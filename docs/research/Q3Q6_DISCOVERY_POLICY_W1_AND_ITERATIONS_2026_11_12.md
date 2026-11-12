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

## 7. Iteration records

| # | Hypothesis | Criterion | Result | Record |
|---|---|---|---|---|
| 1 | H1 | K1–K4, both domains | (pending) | (pending) |
