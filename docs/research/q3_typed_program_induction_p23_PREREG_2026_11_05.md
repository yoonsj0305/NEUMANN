# NEUMANN 1 | P2.3 Goal-conditioned typed program induction without teacher at inference
PRE-REGISTRATION · 2026-11-05 KST · Written before new evaluation task bodies are opened or first scoring.

**Frozen North Star:** Frontier-level problem solving with minimum necessary computation. Global Q1–Q7 remain OPEN.

## Question
The external GPT-6 teacher in P2.2 produced 7/8 correct public ARC evaluation programs while the pre-existing B/Q/P20/C211 fixed candidate sets solved 0/8; on six teacher-solved tasks the previous evaluated grammar contained zero training-consistent candidates. The objective is now to build a **teacher-free, executable typed AST synthesizer** that derives previously unenumerated conditional program compositions from original TRAIN pairs, not simply choose a saved P2.2 source program.

## Mechanism, fixed before first fresh result
**S23** is a classical differentiable-free search/induction student (NOT a trained neural model or learned across-task proposal policy). It constructs executable expression ASTs:
- Source shape modes: whole grid (same shape), two equal input halves composed into a smaller output grid, source foreground bounding-box crop, component-derived reductions where type-safe.
- Terminal expressions: original source cell, second panel cell, task-inferred literal palette color.
- Predicates: local value/zero tests, coordinate/boundary conditions, relational panel equality/Boolean conjunction and row/column contextual relations. Candidate guards are generated from training input features and composed into AND/OR with bounded depth. No completed solution for a particular ARC ID is in the code.
- Synthesis: derive must-change and must-not-change constraints from TRAIN outputs, enumerate typed predicate-expression ASTs, reject inconsistent candidates before execution, exact replay ALL training pairs and score only TEST INPUT proposals. If optimal eligible candidates disagree, or input shape/constraints fail, ABSTAIN. No original test gold read by proposal path.
- Include a fixed tiny global shape-expression grammar as a baseline for component count, foreground crop, shifts, and non-neural structural primitives. All candidate program source/AST, provenance and costs recorded.
- Prohibit task ID, test grid fingerprint, public benchmark answer, GPT-6 forward or teacher code callback from the student.

## Independent original-task cohort
Official public `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`, `data/evaluation/`. Exclude all **104** prior reserved/opened evaluation files (P2.1 48 + P2.1.1 48 + P2.2 8); select next **32** files ranked by unsigned FNV-1a32("neumann-q3-p23-20261105|" + filename), tie filename. Commit immutable complete selected filename list and S23 source SHA **before opening any selected task body**. Earlier P2.2 8 known tasks are developmental regression only, NOT independent validation.

## Strong controls and scoring
Compare the same 32 original public evaluation tasks with B=P1.1, Q=P1.6, P20=P2.0 and C211=P2.1.1 frozen baselines. Strong combined baseline only accepts when all non-ABSTAIN predictions agree, then S23 is attempted only if every old path abstains without conflict. Every original TRAIN output must be matched exactly before a program is considered. Candidate validation may read original TEST INPUTS but never TEST gold. All original TEST outputs read only by separate scorer, after first proposal. A wrong accepted prediction is a **false accept**, not excluded.
- Frozen local capability gate PASS iff **≥2 additional exact original tasks**, **0 new false accepted**, **0 lost baseline wins**, **independent replay + source audit PASS**; 1 additional INCONCLUSIVE, 0 or any false accept FAIL.
- Resource counters: AST proposals, primitive train-grid checks, full study-region elapsed time, abstentions, false accepts; energy, FLOPs, memory, full system cost UNKNOWN unless directly measured.
- Same 32 first-score receipt always immutable; no post-score retune.

## Additional generalization contract (development, separate from 32)
- Replay on P2.2 eight **already opened** teacher tasks to determine how much of the previous external-teacher ability can be reconstructed without an external teacher **at inference**. This is development evidence, not unbiased transfer.
- A future program-generation policy that learns across tasks must be tested in a separate registered study, including withheld **operator families**; this P2.3 classical inductive task-specific compiler cannot close global Q3 learned discovery or Q6.

## Safety and scope
Only trusted, explicitly coded primitives executed. No arbitrary untrusted eval or imported code. Invalid/ambiguous result -> ABSTAIN, fallback to independently verified Direct. A higher score than B/Q/P20/C211 on a public sample would indicate bounded original-task semantic coverage, **not** new-to-science operators, uncontaminated frontier performance, learned policy or full-cost 10x improvement. Stop adding new ARC-specific hand templates after first score.
