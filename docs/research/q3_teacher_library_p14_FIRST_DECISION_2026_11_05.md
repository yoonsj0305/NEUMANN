# NEUMANN 1 · P1.4 first frozen program-library transfer

Date: 2026-11-05 KST. Same North Star and Q1–Q7 all OPEN.

## First registered original-task result
- Source: official public ARC-AGI-1 **training** at upstream `399030444e0ab0cc8b4e199870fb20b863846f34`, 24 filename-hash selected new-to-this-development cases, excluding all P1.0, P1.1, P1.2, P1.3 and pre-inspected dev examples.
- K: four **unchanged** P1.3 GPT-6 teacher-written executable JS operators, matched strictly on training pairs, optionally conjugated by eight geometric symmetries; no teacher/neural calls.
- **24/24 ABSTAIN**, original-task exact **0/24**, **zero accepted wrong**, no new capability against frozen A/B/J (also 0/24).
- **768** attempted hypotheses (32 per task) and **768** train program calls, summed in-isolate `Date.now()` region **69 milliseconds**. This is not deployment cold start, measured model inference, full Q4 cost or hardware energy.
- First result `docs/experiments/results/q3_operator_library_p14_FIRST_COMPLETE.json` and three first shards remain unchanged.

## Decision: local P1.4 FAIL_NO_LIBRARY_TRANSFER
Correctly selecting an already known rule for the original four P1.3 problems worked 4/4 without using task IDs to route, but provides no real cross-task/family headroom. On 24 newly fixed original tasks, the four-rule library provided **no transferable executable rule**, despite correct abstention. Do not claim original NEUMANN policy internalization from P1.3's 4/4 or metamorphic 52/52, and do not tune the 24 scored cases.

## First-principles cost criterion
For N independently verified applicable deployments, the compiled approach's total cost is

`C_hybrid(N) = C_propose + C_compile + C_validate + N*(C_match + C_execute + C_verify) + C_fallback`.

To justify 10× complete-cost reduction against a same-accuracy Direct baseline,

`C_hybrid(N) <= 0.1 * N * C_Direct`.

A breakeven N exists only if `0.1*C_Direct > C_match + C_execute + C_verify`; then `N >= (C_propose+C_compile+C_validate+C_fallback)/(0.1*C_Direct-C_match-C_execute-C_verify)`. All direct/model costs here are **UNKNOWN**; 69ms in-isolate does not yield a numerical N, nor does a raw-material software Idiot Index have a defined meaning.

## Stop / next source of progress
- STOP reusing the same 4 exact source programs as if they were a broad learned library. Keep them only as verified local contracts and debugger regressions.
- A proper NEUMANN policy needs semantic generalization across discovered operators: learn what makes a new operator applicable; learn how to **propose new program semantics** when none exists; and reuse learned abstractions across tasks with independently verified original outputs.
- A strong fixed classical synthesizer remains the Direct baseline. External GPT-6 teacher remains a **separate costed teacher**, not NEUMANN's autonomous learner. Require fresh-source transfer and full-system cost before Q3/Q4 joint admission. No sealed evaluation opened.
