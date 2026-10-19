# AM2 | First typed SyGuS 3-arm runtime → live original 3VC checker integration

**Date:** 2026-10-19 KST. **Outcome:** scoped ENGINEERING PASS. NOT actual small-model inference, NOT a capability multiplier, NOT a new difficult benchmark result, Q1–Q7 global OPEN.

## Previously missing interface now connected

Before this change, the [AM2 generic public QA ABI](../../neumann1/am2_generic_qa_abi.py) accepted only one-line `short_text`/`integer`/`choice`; its parser rejects multiline SMT Boolean invariants and `<` / `<=` comparison symbols. The [AM2 three-arm runtime](../../neumann1/am2_opened_three_arm_runtime.py) executed original QA callbacks but could not represent a complete source-generated invariant to the separate real [SyGuS source-bound original checker](../../experiments/am2_sygus_native_three_vc_checker.py).

The new **`smt_invariant` typed public-answer kind** allows max 4096 characters between exactly one `<answer>SMT_BOOL_TERM</answer>` marker, including comparison operators and newline. It refuses nested answer markers, thought-only outputs and extra text. **Existing short_text/integer/choice semantics remain unchanged.** The actual original SyGuS source is PUBLIC problem text; the source-bound Z3+cvc5 verifier executable and its decision are never supplied to model/tool/proposer as private evidence. The existing original checker remains the authority for accepted answers.

The actual [Draft PR #270](https://github.com/yoonsj0305/NEUMANN/pull/270) imports the previously frozen AM2 core and ABI from [PR #256](https://github.com/yoonsj0305/NEUMANN/pull/256) without silently changing the old runtime and extends only the typed envelope for SMT output; the real source-checker module remains byte-pinned at Git blob `aca2b543057c968acd8a175e7b1ef8e391ba79b2` from [PR #268](https://github.com/yoonsj0305/NEUMANN/pull/268).

## Predeclared tests and exact provenance

Preregistered before the implementation / first actual CI: [Issue #269](https://github.com/yoonsj0305/NEUMANN/issues/269). No new source selection, no model or GPU access. Public upstream SyGuS-Org/benchmarks exact Git commit `13c8deb68a873635879c9a69bc78caebd340f646`. Same TWO **already-opened** 2018 sources from prior original checker:
- `comp/2018/Inv_Track/cggmp2005_true-unreach-call_true-termination.sl`: previous BRANCH_AFFINE_NULLSPACE non-Post classical relation.
- `comp/2018/Inv_Track/bkley.sl`: previous POST_ONLY source proof.

**Important honesty:** for engineering *positive controls* only, a deliberately `SYNTHETIC_TEST_ONLY` core emits a *previously-known valid classical invariant* (obtained by the pinned source-only proposer). The fake core **does not solve anything**; it exercises exactly the same interface `core.generate(messages,max_tokens,thinking=False,deadline_ms)` used by the proposed future real Gemma frozen-core, under `production=False`. No model weights or neural forwards have occurred. Test tool/provider is transparently `TEST_ONLY_NOT_ELIGIBLE_STRONG_TOOL_PLUS`; it does not represent a strong equal-capability baseline. NEUMANN structural-certificate test callback actually calls the Z3+cvc5 source-bound original verifier before accepting the proposed structure, but this is a classical positive test, not evidence the trained model invented a new operator. All its wall costs are charged within the runtime path.

## First actual end-to-end execution

- FIRST [GitHub Actions #39214602528](https://github.com/yoonsj0305/NEUMANN/actions/runs/39214602528): **SUCCESS**.
- **10/10** typed SMT envelope and unchanged legacy ABI unit tests PASS.
- Both original sources: each DIRECT, TOOL+, NEUMANN path positive = 3/3, so **6/6 actual source-bound checker acceptances**. The checker runs true native Pre/Trans/Post Z3 3VC and standalone cvc5 on each successful submitted candidate.
- **Each source saw 12 actual original checker invocations** and **5 extra structure certificate original checker invocations** (positive and negatives) across integration controls; these are verifier and test counts, NOT model generation counts. Proof obligations were generated and checked, not imported from cached accept labels.
- Both sources' `true` and `false` bad candidate outputs rejected by original checker in all arms; thought-only outputs did not invoke original checker; SMT command injection and original SHA impersonation rejected, and private `gold` field blocked by public input schema.
- Same frozen test core object used per matched set, common TOOL+/NEUMANN provider output SHA parity checked, and real model counts remain 0. No scientific admission is automatically granted.
- First workflow ZIP artifact ID **12168674261** (downloaded, CRC PASS) SHA256 `e517a2703df0305761188bffae9faefdf234b769d628d44cc95cfd3732228809`. Original first integrated JSON SHA256 `c9eac5d7d2023fd486e66c4b7168091f922132a7d5b80dfdd9e4d78f99d3f1bb`. The 2 rows were independently inspected; each passed all 11 preregistered boolean integrity gates.

## Exact verdict

```text
AM2_TYPED_SMT_INVARIANT_PUBLIC_ANSWER_ABI = SCOPED_PASS (10/10)
AM2_REAL_ORIGINAL_CHECKER_THREE_ARM_WIRING = SCOPED_PASS (2 sources x 3 arms)
AM2_SOURCE_BOUND_ORIGINAL_CHECKER_ACTUAL_CALLS = 24 (+10 structure proof checks)
AM2_ORIGINAL_DATA_ACTUALLY_INDEPENDENT_AND_UNSEEN = UNPROVEN
AM2_REAL_SMALL_CORE_MODEL_CALLS = 0
AM2_STRONG_TOOL_PLUS_ACTUAL_COMPARATOR = UNBOUND
AM2_OPENED_24_HARD_ORIGINALS_ADMITTED = FALSE
AM2_COLD_COMPLETE_COST_AND_Q4_Q5 = NOT_EVALUATED
AM2_EX1_ACTUAL_MODEL_MULTIPLIER = NOT_EVALUATED
AM2_SEALED_EX2 = BLOCKED
Q1_Q7_GLOBAL = OPEN
HISTORICAL_AM1_FIRST = FAIL_UNCHANGED
```

**Stop repeating known-original engineering demonstrations:** the missing mechanical output-format → same three-arm model interface → source-bound actual checker link is now exercised. This does **not** repair availability of native BF16 GPU, the absence of 24 difficult task originals from three independently validated families, strong eligible TOOL+, learned ΔΓ outside strongest grammar, or complete monetary/energy/forward costs. Those are separate decisive science prerequisites, not more Boolean unit tests. No paid GPU/API/model download, no new original-task generalization or sealed task access. Further scientific work must preregister source families/checkers/cost and compare a truly frozen model.
