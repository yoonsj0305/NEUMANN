# NEUMANN 1 · P2.4 cached typed-guard synthesizer: first decision

Date 2026-11-05 KST. North Star: **Frontier-level problem solving with minimum necessary computation**. Global Q1–Q7 all OPEN.

## What actually changed
P2.4 preserves the exact P2.3 typed AST search and its input/output/ABSTAIN contract. It computes source-grid row/column nonzero prefix/suffix summaries, four-neighbor counts and foreground bounding box **once per grid**, cached in a WeakMap reset at the beginning of each solve invocation. All conditional guards, exact train checker, candidate enumeration and program-ranking tie policy remain as before. This deletes redundant feature recomputation, not problem requirements or hypothesis classes.

## Frozen first public original result
Official public ARC-AGI-1 evaluation at pinned upstream SHA `399030444e0ab0cc8b4e199870fb20b863846f34`. New 32 original tasks selected from filename hashes excluding 136 previously reserved evaluation IDs, with P23/P24 Git blob SHA frozen before task file contents were opened.

- **32/32 exact AST, prediction, abstention reason and train-fit count parity**.
- **Original exact problem solving P23 0/32, P24 0/32**, wrong accepted predictions **0** in both arms.
- **Zero** full consistent-program train replays in this frozen cohort. This is primarily a faster **unsuccessful candidate search**, not a capability improvement.
- **32,556** guard attempts each arm; task-region wall from one JS Date.now run **13,902 ms -> 4,634 ms**, ratio **3.000x**. This meets the **inclusive 3.0x local runtime gate**, but 10x stretch FAIL. Timing precision is coarse and exactly at the threshold; a subsequent independent repeat should assess stability, not retroactively change the first result. The 3x ratio is not end-to-end CPU/GPU/energy/dollar savings.
- Local P2.4 verdict **PASS_BOUNDED_FEATURE_CACHE_PARITY_SPEED**, strictly efficiency-only; all global Q1-Q7 remain OPEN.

### Independent evidence checks
- [First full result](../experiments/results/q3_sound_feature_caching_p24_FIRST_COMPLETE.json) preserved with all four first shards and frozen blobs.
- [Independent summary integrity audit](../experiments/results/q3_sound_feature_caching_p24_INDEPENDENT_AUDIT.json) confirms 32 filename positions, hash consistency, 32 identical original judgments and the exact 13,902/4,634 accounting, PASS.
- **Crucial prior-winner regression**, after frozen first cohort, on previously opened P23 `e345f17b`: P23 and P24 produce exactly the same half-grid equality AST, **49** training-consistent candidates, original **4/4 train and 2/2 test** exact. [Posthoc receipt](../experiments/results/q3_sound_feature_caching_p24_POSTHOC_P23_REPLAY.json) PASS, labelled **non-independent**. One code-run instance measured P23 39ms vs P24 13ms; do not mix with first time gate.
- Synthetic 56-case development differential parity and 7 contract unit tests PASS (development only). No trained model or new semantics.

## Why this is not the quantum jump
The latest first 32 new ARC tasks all remained unsolved with both P23/P24. Cached feature summaries accelerate the existing **finite grammar**; they cannot generate a structural program whose meaning is absent from it. P2.2 external GPT-6 teacher solved 7/8 different, public evaluation problems, but six of those had no train-fitting program in any previous fixed enumerated hypothesis set. Those results are from different cohorts and are **not** comparable as matched model scores. The external teacher is not NEUMANN's autonomous discovery policy and its generation cost was not metered.

## Admission recommendation
Keep P24 as a research-only optimization attached to P23: it is a **verified performance engineering change** under stated assumptions. Do not spend next iterations optimizing the same empty candidate search. The next priority is learning **how to construct additional executable schema types** beyond hand-coded primitives, with original-task independent validation, new-family transfer and full-cost budget. Preserve explicit ABSTAIN and strong Direct fallback.

Risks: cache global WeakMap needs reinitialization each invocation, pure deterministic inputs (mutation after cache construction inside a solve is unsupported), exact grid shape, JS Date.now timing noise, and unknown production CPU/memory costs. Global Q1–Q7 OPEN. No mainline or sealed benchmarks changed.
