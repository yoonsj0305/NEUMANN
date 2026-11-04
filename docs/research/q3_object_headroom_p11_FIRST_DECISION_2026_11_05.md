# NEUMANN 1 · P1.1 first empirical decision (2026-11-05)

North Star: **Frontier-level problem solving with minimum necessary computation**. All Q1–Q7 globally OPEN. Original P1.0 failure 0/32 retained.

## Registered experiment and immutable result

P1.1 was registered before the 24 test-task bodies were fetched. It compared a stronger classical grid program synthesizer (A) against the same bounded family plus object-centric components and relational operations (B). Both were **classical**: no JEPA, neural model or learned embeddings.

- Official *public ARC-AGI-1 training* repository `fchollet/ARC-AGI` pinned to `399030444e0ab0cc8b4e199870fb20b863846f34`, filename-hash preselected 24 tasks, excluding the 32 P1.0 tasks and four developer-inspected examples.
- Frozen source `experiments/q3_object_headroom_p11.mjs`, blob SHA `e2583c641426a51b1945b8fff7b1f9bba5bf9982`. Exact full first result: `docs/experiments/results/q3_object_headroom_p11_FIRST_COMPLETE.json`.
- **A: 1/24 original tasks solved; B: 1/24; added B wins 0; lost A wins 0.**
- Correct task `7468f01a` was independently re-executed as flip-horizontal then crop-nonzero; match exact original grid and dimensions.
- A attempted 12,000 hypotheses and performed 24,813 train-grid executions. B attempted 12,000 hypotheses and performed 28,051 train-grid executions. The extra object representations increased executed operations, without increasing task success.
- Study-only JS monotonic? **No**: `Date.now()` wall-clock millisecond resolution, measured program fitting and prediction only. A 1,508 ms summed across 24 task-local regions; B 1,958 ms. Source download/connector overhead, full-system cold start and standalone model/checkpoint costs are NOT included. These 24 results are NOT an iso-capability full-resource Pareto result. Energy, FLOPs, peak memory and monetary costs UNKNOWN.
- Both arms were capped at 500 hypotheses per task. B uses 260 of the same prefix of A's grid hypotheses and allocates 240 to object/relational hypotheses; the complete hypothesis sets are NOT identical, only budget, original instances and checker conditions.
- The new dedicated audit verified source identity, exact winner using an independent fixed operation, and that mutating the public test output changes only original-task score, not the program proposal. Result: **AUDIT PASS, first hypothesis FAIL**.
- Public training tasks are *new to this experimental code*, not a sealed frontier or ARC-AGI-2 leaderboard. The 4 older pre-inspected tasks (A 3/4, B 4/4) were only regressions, never included in the 24 scores.

## Causal conclusion and STOP

The missing ability is not simply detecting color-connected components, sizes, bounding boxes or simple relative motion: these human-specified object constructs produced **zero additional capability** over a substantially broader grid-only program catalog. Do not spend on learned good-view training C, since the registered admission precondition of structural headroom B>A failed. Do not modify this 24-task cohort with further operators and claim independent first-run gains.

**Important limited proof:** Within a frozen executable hypothesis set H and training observations D, if consistent candidates `H_D = {h∈H: ∀(x,y)∈D, h(x)=y}` is empty, a selector/router restricted to H cannot recover a verified program consistent with D, regardless of representation rank. Adding a learned proposer can help only if it generates new executable candidates outside H, changes the observation mapping meaningfully, or corrects the compiler. It does not follow that no general learned solution exists.

## Rebuild the research interface, not the benchmark score

Recent relevant prior research: DreamCoder (2021, PLDI; later refinements) learns new abstractions and a search policy; ARC object-centric neurosymbolic work (2026) emphasizes that object definitions themselves are task-dependent. NEUMANN should **compare fairly** against these conceptual precedents rather than call ordinary object grouping a new invention.

Proposed next gate (NOT RUN): jointly infer object partition hypotheses and transformation grammar, compile a typed executable AST, independently verify the original task, measure full discovery/execution/fallback cost, and test on a NEW cohort under a separately frozen protocol. Prioritize testable novelty over extending a list of manually coded ARC operators. Strong A and separate no-neural B must remain credible baselines. Continue to veto learning if no verified capability headroom.

No mainline merge. P1.12, Q1–Q7, and sealed Decision 3 unchanged.
