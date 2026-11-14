# External semantic AST G0: actual first-frozen, independently authored PROSE cohort

**2026-10-26. NO NEW RC/PR. Q1–Q7 all OPEN. Failure of current learned-production proposal route is PRESERVED.**

## Experimental chronology and provenance

- Original preregistration **GitHub commit** `79b6200ef8d985512be94847701344b6b448079a` BEFORE exposing eight PROSE test file contents. Eight exact task IDs and pinned file SHA are in `prose_ast_external_g0_prereg_20261026.md`.
- Executed own-weight CPU Torch A, identical 100-step learning B with per-task reward labels permuted, four paired seeds `[3,5,7,11]`, no exact answer or per-task program memory. Proposal policy chooses among 13 AST production categories; executable `post/concat/default` ASTs and parameters are synthesized source-only. It does **NOT** invent underlying primitive semantics. Baselines C0: all prior 12 primitive families, source-consensus; C1: all 13 new AST productions + classical edit-derived generalized regex rewrite, source-consensus.
- **Before scoring any unseen output**, complete 42,512-byte first-predictions JSON SHA256 frozen `1a745f6d36504f8dbf685b633ab8770bdb7096212221219a4212a7ca87daa27f`; GitHub **first-frozen commit** `d26d56e70ed24890b9ea6d28021313ba0a9ef891`.
- THEN checked original Microsoft PROSE test outputs through connected GitHub for **all 8** and authenticated each exact original file blob SHA-1. Every matched A/B seed and C0 produced exactly the SAME first predictions, correct on **3/8** full original tasks (Rating.000002, UserAgent.000002, Email.000005), **5/8 HOLD**, zero confidently wrong. Email has only one original test record; keep this limitation.
- C1 full expanded grammar: **2/8**, 6 HOLD. Rating.000002 has **73** source-consistent ASTs with different next-input predictions, so source-only output correctly **HOLD_SOURCE_AMBIGUITY**; a larger hypothesis space without active information can reduce reliable decision coverage.
- The separate generic source-only regexp constructor identified NEW generalized executable deletion for PREVIOUSLY OPENED PROSE `Team.000003`, alongside a literal rule matching the same two source IO. The candidates disagree on later inputs: MUST HOLD without authoritative oracle. A classical invention mechanism, no NN learned invention proven.
- Active discriminator proposes an ORIGINAL-SOURCE-only query `\r\n(10)` that yields **4 distinct predictions among 73 source-fitting Rating hypotheses**, entropy 1.077333 bits, 1,533 AST inference calls. Oracle label UNKNOWN (NOT invented). This is an information request candidate, not a task solution.

## CPU cost and scientific decision

- C0 strong classical original grammar CPU **35.340525 ms** single run (all 8 tasks).
- C1 fuller classical grammar CPU **136.143477 ms** single run (all 8 tasks).
- A learned policy: **2320.664955 ms** median 4 paired seeds (12 earlier tasks learning + eight task AST proposals).
- B reward-permuted: **2415.481294 ms** median.
- Learned policy **65.67× more CPU** than C0 on quoted non-identical scope and gives **zero incremental task capability**, so DON’T use this selector in NEUMANN's critical path. Not a complete ISO-capability resource Pareto: cold start, energy, peak RAM, transport, license costs and USD UNKNOWN. Training amortization unspecified.
- ALL eight remain public text-transformation benchmark tasks. This does not prove cross-modality C, new base-semantics B, all in Q5, or frontier Q7. Even if a newly composed AST works, the grammar is supplied by a human and the neural net here only ranks productions.

## Replayable source and evidence

Conversation artifact `NEUMANN1_SEMANTIC_INVENTION_EXTERNAL_G0_20261026.zip`
SHA256 `36b2c2d95a78127c882710e8ac365d7fa19c7eb743e24f4711903879c71bf302`, **17 files**, actual runnable source, source-only external fixtures, exact first-unguessed predictions and hashes, script, independent-original-gold grading receipt, and focused tests. Fresh clean extraction: SHA manifest **16/16 PASS**, pytest **8/8 PASS**, first prediction SHA exactly PASS. Historical older PROSE original data was already opened and is only dev material, not independent eval.

## Narrow next step

**G0 learned discovery-policy semantic invention: FAIL TO DEMONSTRATE / OPEN.** The current output space remains hand-authored, regardless of how many synthetic variations or optimizer steps. Pursue an actually self-generated *typed semantic rewrite* policy that emits and verifies new executable programs, not a new ranker for 13 human-coded grammar productions. Confirm A–B gain on a new independent original domain BEFORE costly meta-learning. Strong classical executors and independent verifiers stay first. All first receipts immutable; never retroactively turn opened tasks into prospective successes.
