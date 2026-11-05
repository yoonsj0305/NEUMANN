# NEUMANN 1 | P1.5 Bitter Lesson: general search vs feedback-guided search
Date preregistered: 2026-11-05 KST. This contract is frozen BEFORE any P1.5 task-body fetch or scoring. Project North Star **Frontier-level problem solving with minimum necessary computation**; global Q1-Q7 OPEN.

## Why P1.5
P1.0-P1.2 explicit finite ARC templates generated no added solved tasks; P1.3 an external GPT-6 teacher proposed new executable code 4/4 opened public cases, but P1.4's frozen four-code cache transferred 0/24. The Bitter Lesson suggests general search and learning methods rather than endlessly handwritten task rules. This small test compares **two general program-search policies using the same low-level primitive grammar**, not a claim of a new neural architecture or an entirely invented opcode.

## Common executable language and checker
Input/output: original ARC grids (1..30, palette 0..9) with *all training pairs*, and test INPUTS only for proposal. Each candidate is a typed composition of 1..3 generic grid-array operations sourced from the earlier frozen P1.1 `GRIDOPS` inventory (23 total), with interpreter `applyGrid` and no task-specific template. A program may be executed on test inputs only if every original train pair is exactly consistent including shape and every cell. Multiple consistent programs with conflicting test outputs -> ABSTAIN; unsupported/invalid -> ABSTAIN. Golden original test outputs reach the independent scorer ONLY AFTER all proposals return. No GT reference inside search or routing.

## Main arms and matching budget
- **U:** uniform shortest-first exhaustive enumeration over the same program language, prefix lengths 1,2,3, deterministic primitive-order tie.
- **E:** feedback-guided evolutionary search: evaluate training agreement (exact equality and partially correct grids only on TRAIN), mutate/crossover ASTs within max length 3, preserve best-scoring candidate pool, stochastic policy controlled by frozen seed task-independent `2026110515`. The algorithm may see prior TRAIN evaluation feedback, not test labels.
- **S:** prior strong grid+object Direct P1.1 B as an ancillary historical capability control, not budget matched to U/E.
Both U and E execute at most **1,024 unique candidate ASTs per task**, count invalids and failed attempts and record distinct program executions, nanoseconds if measured, and original exact test accuracy. Adaptive E's own scoring/population bookkeeping is charged. Scores at prefix budgets **128, 512, 1024** are diagnostic only; no threshold shopping.

## New original-task cohort
Pinned source `fchollet/ARC-AGI`, public `data/training` at commit `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude all previously selected P1.0 (32), P1.1 (24), P1.2 (24), P1.3 (4), P1.4 (24) and P0.3 opened developer tasks (4): **112** excluded IDs (verify exact distinct count before selection). Rank remaining filenames by FNV-1a32 of `neumann-q3-p15-20261105|` concatenated with basename, ascending ties by name. Freeze first **32** filenames, source hashes and exact evaluator before opening their task bodies. This is *public training*, not ARC-AGI-2 or independent private evaluation. There is no task ID conditional in the solver.

## Predeclared decision
- Local search-feedback positive evidence: E solves **>=2** more originally exact tasks than U with **no** U lost, OR E solves same >=3 original tasks with at least 25% fewer candidate evaluations until first consistent program and no additional false accepts. Treat all other outcomes FAIL/INCONCLUSIVE, with first result retained.
- Regardless of result, no NEUMANN globally Q3/Q4 pass: this is a known human-defined primitive set, within-task search adaptation, and no learned persistent discovery policy across unseen semantic families.
- E must not use more than 1024 candidate attempts. If U solves a task that E abstains on, report loss. No post-outcome rerun/tuning of the cohort or favorable-seed selection.
- Timed process/host overhead and cost axes must be measured or UNKNOWN; no raw-material software Idiot Index. In JS isolate `Date.now()` is low resolution and excludes connector transfer time. Full model-training cost / energy UNKNOWN; no 10x claim.

## Hard safety, degraded mode and quality
Interpreter accepts *only* whitelisted program primitive identifiers, no eval of model-written code, I/O or network. Standard function failures and bad grids become ABSTAIN. A candidate must not be scored as correct merely because test output shape matches. Independent original checker scores complete grid on every test case; *train* feedback cannot use held-out test results.

## Prior art
Rich Sutton, 'The Bitter Lesson' (2019); DreamCoder (Ellis et al., PLDI 2021); SOAR (Pourcel et al., ICML 2025) motivate this *control*, not invented methods. A genuine positive needs task-disjoint learning of new proposal semantics or a demonstrated full-cost improvement over strong Direct, beyond this bounded ARC smoke test.
