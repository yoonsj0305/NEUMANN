# NEUMANN 1 P2.5 · Constraint-induced multi-branch executable program generation
2026-11-05 KST. Frozen before new source implementation and new public evaluation source-body fetch.

## Core question
Does a **typed exact decision-tree program synthesizer**, which generates a multi-branch executable AST from original task TRAIN pairs without any external teacher or task-ID templates, recover original tasks outside the fixed one-guard programs of P2.3/P2.4? This is **task-local classical program induction**, not a neural student, autonomous novel opcode generation or a persistent learned policy.

## Fixed program language
- Reuse original frozen P2.4 `modeOutput,source,primitiveFacts,inGrid` as deterministic pure primitives (same, half_lr, half_tb and four signed unit shifts).
- For each output cell, candidate terminal actions are source pixel `a`, second panel pixel `b` where applicable, or a literal palette color observed in original TRAIN outputs.
- Candidate internal nodes: Boolean tests from **all available P2.4 primitiveFacts**, plus generic `a==k` and `b==k` for each color occurring in original TRAIN inputs; no task-ID or test-output-dependent features.
- Depth at most **3**; recursive branch structure induced by exact leaf-action feasibility on every original TRAIN output cell, with a deterministic bounded beam of first **12** distinct train-discriminating tests at a subproblem, ordered by target-entropy information gain then name.
- Exact fit is mandatory across all original TRAIN grids with no rounding or partial credit. A single predicted TEST candidate is accepted only if **all minimum-cost train-consistent trees agree** on all available original TEST inputs; otherwise ABSTAIN. Other invalid/unsupported outputs ABSTAIN.
- Use typed AST and pure evaluation; no external GPT calls, neural training, or hidden test oracle. No special-case functions for any named ARC task.

## Original cohort
Official `fchollet/ARC-AGI` public `data/evaluation` pinned commit `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude all **168** previously reserved public evaluation IDs (P21=48, P211=48, P22=8, P23=32, P24=32). Choose **32** files from remaining 232 by unsigned FNV1a32('neumann-q3-p25-20261105|'+filename), tie alphabetically. Freeze all source Git blobs and selected task IDs before fetching any new task body.

## Baselines, measured outcomes and first gate
Strong baseline: P1.1 B + P1.6 exact Q + P2.0 goal-directed shape-pruned P20 + P2.1.1 C211 + P2.4 cached S24, all frozen. If accepted baseline predictions conflict, ABSTAIN and do not invoke P25. Otherwise invoke P25 only when prior solvers all abstain (no conflict). All proposals use TRAIN outputs and TEST INPUTS only. Original TEST outputs are opened **only by independent scorer after proposals**.
- A false accepted test prediction is a safety FAIL, not omitted from score.
- **Local original-task capability PASS** iff >=2 previously unsolved whole original public tasks solved by new P25, **zero new false accepted**, and zero baseline loss, with independent replay and source identity PASS. Exactly one additional = INCONCLUSIVE. Zero additional, wrong accepted, or leakage = FAIL. Same first result remains immutable.
- Track number of reachable program ASTs, information-gain features attempted, full train-grid/TEST-input evaluations, study-region Date.now wall time, true accepted vs abstained. Full costs, energy and RAM explicitly UNKNOWN if not metered. No 10× reasoning-cost claim.
- Synthetic constraints used to test two- and three-branch rules are development only. Already-opened P22 or P23 original tasks can be used *after* first run solely as posthoc regression and never as fresh results.

## Deep risk and stop rule
Multi-branch conditional trees can memorize row/column patterns: require stable exact train replay and consensus over best-cost trees; no adaptive post-result threshold changes. If no new original ability appears, stop expanding hand-coded features and prioritize a truly learned program-schema proposal policy from multiple unrelated programs. All global Q1–Q7 OPEN, no mainline or sealed gate mutations.
