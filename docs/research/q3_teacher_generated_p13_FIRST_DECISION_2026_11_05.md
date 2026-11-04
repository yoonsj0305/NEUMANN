# NEUMANN 1 · P1.3 first generated-operator feasibility decision

Date: 2026-11-05 KST. North Star: **frontier-level problem solving with minimum necessary computation**.

## Registered first result
- Four novel-to-this-proposal-stage ARC-AGI-1 *public training* task IDs, chosen by frozen filename hash after excluding 84 prior opened development IDs. All original task bodies were read with **test outputs redacted from the model-visible tool response**.
- External frontier GPT-6 teacher wrote one general pure JS function for each task using visible training examples and test *inputs*, without original test answers. All four program sources were committed to `experiments/q3_teacher_generated_p13_FIRST_PROPOSAL.mjs` **before first scoring**, blob SHA `52bf8a757c7315951ef9a50f527949cb74ba506a`.
- Independent train-only replay gave **15/15** exact examples. Original scorer then found **4/4 entire tasks** and **5/5 individual test grids** exactly solved; frozen stronger grid A, object B, joint segmentation J **0/4 each**. Net added verified solutions over all three fixed template baselines = **4**.
- A separately coded independent cell-by-cell scorer replayed all 15 train + five test outputs, confirmed no invalid output shapes, errors or changed source, and a mutated reference changed the score without changing the candidate code. **Independent audit PASS**.
- Post-scoring metamorphic audit, *not independent natural tasks*, used flips, 180° rotation and added background margins on public examples: **52/52 transformation checks PASS**, original first source not modified.
- These four programs include a nontrivial motif replication rule, row-shift operator, intersection of empty cells in two separator-delimited grids, and 3×3 block transfer indexed by a marker's within-block coordinates. The functions apply to arbitrary matching input configurations rather than memorized test-output grids. Their semantics were nevertheless designed by **external GPT-6** and are not proven novel to computer science.

## Causal interpretation
**P1.3 local interface feasibility = PASS.** A model-proposed executable program can escape a small human-coded ARC DSL, be frozen, and pass an independent original-task checker without target output entering generation. This is not evidence that the NEUMANN learning system itself invented primitives, learned to improve its discovery policy, transferred to new problem families, achieved frontier capability or reduced complete computation. Public ARC-AGI-1 examples may have been included in frontier-model pretraining, which prevents a clean unseen-data inference. The four-task sample is too small for general accuracy claims.

No model-generation tokens, latency, dollar price or energy were metered; wall time for compiled program execution is **not** model-proposal cost. Any full-cost or 10× claim is prohibited. Model calls were made via this chat, not a reproducible fixed NEUMANN model API with a known versioned sampling policy. The source functions are first-seen *candidate programs*, not safely sandboxed production operators.

## Immediate follow-up evidence
P1.4 independently evaluated automatic reuse of precisely the four frozen programs (plus eight geometric conjugations) on another pre-registered 24-task public cohort. **0/24** additional task success, all 24 ABSTAIN. This distinguishes *task-specific candidate generation* from *transferable structure learning*. First P1.3 PASS remains valid only for its stated interface.

## Next interface
- Freeze a strongly typed, sandboxed executable program protocol with independent original goal-verifier and provenance.
- Extract abstract, task-independent operator signatures, not source code/task-ID caches; require semantic deduplication and fresh-family transfer checks.
- Compare learned proposal policy against strongest classical Direct and an identical compile/verifier budget at total train+inference+verification+fallback cost. Let discovery cost `C_discovery` be compared to amortized saved work `C_saved` only after measuring model and compiler bills.
- If only external GPT-6 can produce successful programs, treat it as an expensive **teacher** until a smaller transferable student/policy is independently verified. Do not silently promote teacher evidence into Q3 or Q4 global PASS.

## Refs
- First program source: `experiments/q3_teacher_generated_p13_FIRST_PROPOSAL.mjs`
- First score: `docs/experiments/results/q3_teacher_generated_p13_FIRST_SCORE.json`
- Independent replay: `docs/experiments/results/q3_teacher_generated_p13_INDEPENDENT_AUDIT.json`
- Metamorphic: `docs/experiments/results/q3_teacher_generated_p13_METAMORPHIC_AUDIT.json`
- Source selection: `docs/experiments/q3_teacher_program_p13_COHORT_FROZEN.json`

**Global Q1–Q7 OPEN.** Decision 3 and all sealed sets untouched. Draft research PR only.
