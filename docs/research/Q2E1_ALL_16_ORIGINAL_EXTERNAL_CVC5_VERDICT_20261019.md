# Q2-E1 · Original structural proofs independently checked with cvc5
2026-10-19 KST · First immutable original-experiment receipt

## Actual scientific result

**SCOPED PASS:** All **16/16** existing source-derived inductive invariants (drawn from 18 already-opened original LoopInvGen SyGuS source files) passed all **48/48** original inductive safety obligations when a different native SMT backend, **cvc5**, independently evaluated the proof queries. There were **2/18 SPACER source-only original safety outcomes** with **no claimed inductive proof certificate**. A forged trivially UNSAT three-query receipt can still fool the older naive query replay, but **strict original source-bound replay rejected it**, as intended.

This is a real verification experiment, not a model-vs-model performance comparison. It is NOT new learned semantics, NOT a fully independent original-source front end, and NOT global Q2/Q1–Q7 closure.

## Authority, prospective design, historical boundaries

- Registered **before coding and first GitHub Actions**: [Issue #259](https://github.com/yoonsj0305/NEUMANN/issues/259).
- First success [GitHub Actions #39209949533](https://github.com/yoonsj0305/NEUMANN/actions/runs/39209949533), archival artifact ID **12167222444**.
- Raw JSON first receipt SHA-256: `dd755383434011ae348e0e60c2bee8c323fa5b773b5348e103a04e4ad0a30777` (verified from CI and the downloaded ZIP).
- ZIP SHA-256: `48e6c454c690bd2e188d400072c4bfa88912b627468b7341ab28c18cc1d3af31`, matches archived GitHub artifact SHA-256 digest; ZIP CRC clean, two files (raw JSON receipt, stdout log).
- Original git revision **6ac90265b11431c9477dfbd33e3e3380234c0499**, 18 **distinct actual original source SHA-256**.
- Reused the **UNCHANGED** `experiments/q3_source_prove.py` proposer, original semantics extraction and 3VC construction, and unchanged prior cvc5 one-operand unary-plus *syntax-only* normalization. No source, grammar, problem/route or solver admission threshold adjusted.
- Original historical first AM1 (36/36 terminal, DIRECT/TOOL/N each 0/12) remains **FAIL**, newer performance comparator and sealed Decision-3 are still NOT_EVALUATED/BLOCKED. No neural forward/GPU/frontier/API/paid execution.

## What was actually checked

For each **original source input**:
1. Compute actual source SHA-256 from bytes obtained from the pinned upstream repository.
2. Run the unchanged, gold-free original Q3 source prover; require original Z3 inductive 3VC on 16 only. On remaining 2 source-only SPACER results do NOT invent inductive original 3VC queries.
3. Verify that three emitted original proof queries have the correct `initial`, `consecution`, `post` names, `expected=unsat` and exact SHA-256.
4. Apply only previously audited, equivalence-preserving unary SMT-plus normalization. Invoke native installed **cvc5** on each actual query. Demand zero exit and *exactly* one observed `unsat` status, not a log substring. 48/48 independently checked.
5. Run real native cvc5 **SAT** control and trivially forged UNSAT control; both yield the expected result. Recompute all three forged-script hashes to show that unbound query replay accepts them; **the existing strict source-bound replay rejects** the forged contents, verifies a real non-Post original invariant and refuses mutated original source bytes. All controls PASS.
6. Raw run logs show exact original safety statuses, query SHA, solver wall times and error receipts. 18 original-source SHA unique. Reuse originally opened known sources only, no unseen independent family PASS claims.

## Statuses and boundaries

```text
Q2_ORIGINAL_3VC_EXTERNAL_SOLVER_16_OF_16          = PASS_SCOPED_CLOSE
Q2_ORIGINAL_BAD_CONDITION_CVC5_UNSAT_48_OF_48     = PASS_SCOPED_CLOSE
Q2_FORGED_QUERY_SET_SOURCE_BOUND_REJECTION        = PASS_SCOPED_CLOSE
Q2_SPACER_ONLY_NOT_MISREPRESENTED_AS_3VC          = 2_OF_2
Q2_FULLY_INDEPENDENT_SOURCE_FRONTEND              = NOT_ESTABLISHED
Q2_GENERAL_SEMANTIC_PRESERVATION_ACROSS_TASKS     = OPEN
Q3_LEARNED_NEW_OPERATOR                           = UNPROVEN
Q1_TO_Q7_GLOBAL                                   = OPEN
AM1_FIRST_SCIENTIFIC_VERDICT                      = FAIL_UNCHANGED
```

### Exact stop decision

**DO NOT** add more routine source-family-specific Q3/Q2 original source replays or new tiny classical toy controls. This closes the **already-opened original Q2 external solver verification gap** with one decisive run. The remaining global Q2 proof requires original-task correctness preservation of an **actual neural/structural NEW AM2 execution system** across authentic, sufficiently difficult task families, not further cvc5 repetitions. Separate matched opened EX1 and admitted sealed EX2 remain blocked by source/checker/tools/genuine model access. These are science gates, not artifacts of this proof-checking experiment.

[Implementation + initial CI PR #261](https://github.com/yoonsj0305/NEUMANN/pull/261) (DRAFT stacked on [Q3 original source CLI PR #246](https://github.com/yoonsj0305/NEUMANN/pull/246)).
