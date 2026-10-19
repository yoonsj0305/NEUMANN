# AM2 actual original SyGuS source-bound candidate checker | first execution

**2026-10-19 KST. First genuine original checker exercise: SCOPED PASS, not a new neural capability or full EX1 admission.**

## Why

The AM2 opened cohort [Issue #265](https://github.com/yoonsj0305/NEUMANN/issues/265) correctly found that a three-repository metadata catalog does NOT give 24 executable original checkers. The current generic response ABI accepts short text/integer/choice but cannot legitimately certify an invariant of an actual SyGuS program. This new adapter is one bounded *actual original checker implementation*: supply a source's cryptographic SHA and a standalone SMT Boolean invariant candidate, rederive original source semantics, check original Pre/Trans/Post induction and have a separate backend confirm original bad conditions. The adapter **does not solve the task** by itself; a caller supplies the candidate.

## First immutable real source input and frozen controls

Preregistered BEFORE the first run in [Issue #267](https://github.com/yoonsj0305/NEUMANN/issues/267). Public source: [SyGuS-Org/benchmarks](https://github.com/SyGuS-Org/benchmarks) Git SHA `13c8deb68a873635879c9a69bc78caebd340f646`.

Two deliberately **ALREADY OPENED** authentic official SyGuS 2018 sources:
- `comp/2018/Inv_Track/cggmp2005_true-unreach-call_true-termination.sl`, previous honest source-only classical Q3 route `BRANCH_AFFINE_NULLSPACE`, a genuine non-Post-only relation.
- `comp/2018/Inv_Track/bkley.sl`, previous `POST_ONLY` control.

Old exact frozen source proposer/semantic checker from [PR #246](https://github.com/yoonsj0305/NEUMANN/pull/246) is re-used unchanged (Git blob `a74b62cc97958e06f70116f3c8cec2f6db3d3b75`), so no hidden answer was inserted into a novel solver or a model. The approved positive invariant comes from that fixed classical proposer; the separate `check_original_candidate(source, submitted_smt_bool, expected_source_sha256)` receives it as untrusted input and validates it independently against **original source**. Actual negative controls send `true`, `false`, changed SHA, and disallowed `(assert false)` SMT command injection. Any malformed/unsupported source/candidate returns ABSTAIN rather than false-positive.

## Exact scientific verification

Checker code: `experiments/am2_sygus_native_three_vc_checker.py` on [Draft PR #268](https://github.com/yoonsj0305/NEUMANN/pull/268).

The checker reads exact source bytes, verifies source digest, parses the original SyGuS source and constructs the actual `Pre/Trans/Post` Z3 relations, checks native-vs-custom parser XOR parity and nonvacuous Pre/NotPost, parses the candidate strictly as ONE Boolean predicate with declarations from the source state variables, then independently verifies each original induction VC:
```
Pre AND not I                    => UNSAT
I AND OriginalTrans AND not I'   => UNSAT
I AND not OriginalPost           => UNSAT
```
For valid candidates, it re-exports these real three SMT-LIB bad-conditions and runs independent `cvc5` on all three. No plain answer string, checker boolean or three unrelated fake-UNSAT scripts can replace a real source-bound original formula under this verifier. It is not, however, a fully independent source parser/proof assistant: cvc5 only checks the emitted SMT-LIB backend query generated from the same source-front-end.

## FIRST ACTUAL RUN evidence

[GitHub Actions #39213484689](https://github.com/yoonsj0305/NEUMANN/actions/runs/39213484689) **SUCCESS**, first artifact ID `12168194288`.

- **2/2** submitted actual invariant candidates certified against real original source Pre/Trans/Post, native Z3 original **3VC x2**, independent cvc5 **6/6 UNSAT**.
- **4/4** deliberately wrong invariants (`true`/`false` on both originals) **REJECTED by the actual original 3VC checker**.
- **2/2** source SHA impersonations **REJECTED**; **2/2** malformed SMT command injections **REJECTED**.
- **Zero model forwards**, GPU, paid APIs, training, new unopened original tasks or sealed cohort data.

Downloaded and independently inspected artifact: ZIP SHA256 `d27b9e4b28b8694cb184af141c46a802119e5865e923ab1580d80175c84143cf`, ZIP CRC PASS, original raw JSON SHA256 `6c5055233beb741ee5255f20dfcc3c2fe7c5645cb3ec74664f5bbd888794b181`. Exact two case records, six preregistered gate booleans TRUE.

## Strict verdict

```text
AM2_ONE_ACTUAL_ORIGINAL_SMT_3VC_CHECKER      = ENGINEERING_SCOPED_PASS
AM2_TWO_ALREADY_OPENED_REAL_ORIGINAL_TASKS  = ORIGINAL_CHECKER_EXECUTED_2_OF_2
AM2_INDEPENDENT_CVC5_BAD_QUERIES             = UNSAT_6_OF_6
AM2_WRONG_CANDIDATES_CAUGHT                  = 4_OF_4
AM2_SOURCE_IDENTITY_SPOOF_REJECTED           = 2_OF_2
AM2_SMT_COMMAND_INJECTION_REJECTED           = 2_OF_2
AM2_COHORT_24_HARD_ORIGINALS_ADMITTED        = FALSE (0/24)
AM2_TRULY_INDEPENDENT_ORIGINAL_SOURCE_FAMILY = UNKNOWN
AM2_NEURAL_MODEL_AND_CAPABILITY_EX1          = NOT_EVALUATED
HISTORICAL_AM1_FIRST                         = FAIL_UNCHANGED
SEALED_D3                                    = BLOCKED
Q1_Q7_GLOBAL                                 = OPEN
```

**STOP:** Do not call a *classical two-case checker adapter* a learned invariant discovery, frontier-grade intelligence, robust unseen family generalization or a 10× resource saving. It verifies a vital **source-candidate-to-original-outcome trust chain** on a real already-known source. Additional source families (real executable Python test, Lean proof kernel), true source license/provenance, hard unsaturated 24+ opened sources, live model and strongest TOOL+ remain blocked; do not fabricate them. Future reusable integration may bind this verified SMT adapter to AM2's typed task interface after separate preregistration and without unauthorized sealed inputs.
