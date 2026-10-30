# NEUMANN discovery policy: external counterexample FIRST freeze before future labels

Prior prereg commit: `1da319b9cfd491d0fcf6bc0a7c94829eca5ada54`. Global Q1–Q7 OPEN.

Full complete **source/feedback-only first predictions JSON** was generated in local runtime `/mnt/data/neumann_next/FIRST_NO_FUTURE_GOLD.json`, SHA256 **`9bb34e9f727f3b5dc4278a12eb809799f003ddf974520885af62d889852e5fd6`**. Full intermediate has 12 task IDs, original upstream blob SHA1, candidate version spaces, source search costs, and first predictions of C0 (two observations), C1 (same candidates pruned by independent example3), C2 (strong classical re-synthesized with 3 observations). C0/C1/C2 code version prereg: `ea6d5b3e0f54bf64728cad4ed73a6aeec6b3e82a0579f314ab282876c43eaa64`. **No original future example 4–5 labels examined at freeze**.

Before independent future-gold:
- INELIGIBLE: `FilePath.000002` (4 original examples, next4–5 insufficient for a feedback+2 future task), `Address.000008` (3 examples).
- 10 eligible originals.
- `UserAgent.000006`: initially **5** bounded source-consistent ASTs across **2** future-prediction classes; the explicitly supplied third original example prunes **2**, leaving **3** candidates and one future-prediction class. C0 HOLD_AMBIGUITY, C1 SOURCE_CONSENSUS_ONLY, C2 SOURCE_CONSENSUS_ONLY. Neither is guaranteed correct.
- `DateTime.000007`: initially **7** source-consistent ASTs, one prospective class, but the third original example **contradicts ALL 7**; C0 SOURCE_CONSENSUS_ONLY, C1 HOLD_NO_SOLUTION, C2 HOLD_NO_SOLUTION.
- `Phone.000005, Currency.000004, Name.000013, ShippingCode.000002`: original first consensus and feedback-compatible (one candidate / source behavior); C0 and C1 both SOURCE_CONSENSUS_ONLY.
- `Number.000006, DateTime.000006, Email.000009`: HOLD_NO_SOLUTION without representation. `City.000009`: a source program exists but outputs invalid/absent on future; HOLD.
- All proposals are **CLASSICAL**. No new neural weights, no learned semantic policy tested. Third example is a *purchased or externally provided authoritative feedback*, not user-free autonomy; future verified feedback at inference has nonzero real cost. Count this cost when claiming efficiency.
- Source search caps 3000 state expansions, 100 full programs, depth6, at most14 explored per state; stronger separate baseline 1800 expansions 12 complete programs. Bug in support-only runner for source null was corrected BEFORE first prediction SHA, without changes to fixed candidate code, no opened future labels.

Any future outcome scoring is retrospective to this GitHub freeze and must preserve negative first outcomes. Exact task IDs and SHA1 in full portable evidence ZIP to be attached in current turn.
