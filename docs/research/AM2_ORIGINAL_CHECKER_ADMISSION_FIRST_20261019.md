# NEUMANN 1 · AM2 original-task checker admission readiness

**Date:** 2026-10-19 KST. **Outcome:** checker/admission guard ENGINEERING PASS; actual scientific cohort NOT ADMITTED. The first matched Gemma 4 E2B experiment and all global Q1–Q7 remain OPEN / NOT_EVALUATED.

## Why this was essential rather than another performance demo

The existing [AM2 generic QA interface](../../neumann1/am2_generic_qa_abi.py) recognizes `short_text`, `integer` or `choice` inside a single short `<answer>VALUE</answer>` field. Those do **not** by themselves verify a SyGuS inductive invariant, runnable Python function under original test suites, or Lean formal theorem. Treating any textual `PASS`, gold-answer field or forged boolean as independent original-task verification would invalidate the entire Q2/Q3 and Q7 evidence chain. The initial REAL opened AM2 original registry has **0/24 admitted original tasks**, and we must not fabricate a cohort from benchmark hyperlinks.

## Real public candidate benchmark producers, not admitted original tasks

Catalog pinned before code to real upstream Git commits (metadata only):

| Candidate benchmark repository | Pinned Git commit | Required trusted original verifier | Current gate |
|---|---|---|---|
| [SyGuS-Org/benchmarks](https://github.com/SyGuS-Org/benchmarks) | `13c8deb68a873635879c9a69bc78caebd340f646` | source-derived Pre/Trans/Post 3VC, independently replayable SMT proof | NOT ADMITTED, source-level license/reuse not verified |
| [openai/human-eval](https://github.com/openai/human-eval) | `b9453e8f1865df0a0057a1383767caa400acfbcf` | trusted isolated executor running ORIGINAL hidden code tests | NOT ADMITTED, Python multi-line candidate ABI not bound |
| [facebookresearch/miniF2F](https://github.com/facebookresearch/miniF2F) | `e4f113090ad82d64f8ce064d2f55b613a9b6bded` | actual Lean proof kernel / checked formal proof, fixed project toolchain | NOT ADMITTED, proof-term ABI not bound |

These are **three different benchmark producers / checker modalities**, not independently sourced 24 tasks. The official SyGuS benchmark README explicitly warns there may be errors or duplicates. Formal authorship, exact task/source licenses, split contamination and equivalent-task dedup are not independently proven. HumanEval and miniF2F may be widely known/model-pretrained; a benchmark reference alone is not evidence of unseen Q6.

## What was implemented

The [pre-registered Issue #265](https://github.com/yoonsj0305/NEUMANN/issues/265) required a zero-GPU fail-closed admission layer. Added `neumann1/am2_original_checker_admission.py` and `tests/test_am2_original_checker_admission.py` on [Draft PR #266](https://github.com/yoonsj0305/NEUMANN/pull/266).

The gate refuses a benchmark record with an unknown provenance repository or changed pinned Git commit, an invalid original-source path or SHA, missing verifier executable artifact identity, incompatible original-checker modality, unapproved source license, private gold/solutions leaking into the public question, self-attested simulated PASS receipts, or a short-text QA interface mislabeled as executable SMT/code/Lean proof. It rejects duplicate original task IDs and byte-identical source SHA. Requiring ≥24 records with ≥8 per each of ≥3 origins is necessary but NOT sufficient: real independently executed source-bound original checker, source licensing, unsaturated strong-tool eligibility and typed solution runtime must be established separately. The current module intentionally **cannot authenticate those external processes**, so `scientific_admitted=False` until separately implemented and independently audited. This is an honest blocker, not a silent PASS.

## First evidence and preserved failures

- Initial [Actions #39212314258](https://github.com/yoonsj0305/NEUMANN/actions/runs/39212314258): 17/17 negative tests PASS but CLI unable to import optional declared project dependency `sklearn`, so CI FAILED. Preserved.
- Second [Actions #39212438693](https://github.com/yoonsj0305/NEUMANN/actions/runs/39212438693): dependency repair, tests 17/17 PASS, actual readiness JSON correctly BLOCKED, but final CI assertion incorrectly treated vacuously true uniqueness-on-empty-set as invalid. Assertion FAIL preserved.
- First valid [Actions #39212585226](https://github.com/yoonsj0305/NEUMANN/actions/runs/39212585226) **SUCCESS**, same unchanged 17 tests, actual metadata-only readiness `BLOCKED_NOT_AN_ADMITTED_OPENED_24_COHORT`. Final assertion fixed to require **science-critical admission gates** false, not incorrectly demand that no predicates over an empty set be true.

Actual validated artifact `12167593753`: downloaded ZIP SHA256 `6264a84239db1fe8ddee9899d51cea6c9325c82824916fa5066bc0f351f6ecaf`, CRC PASS, 3 members (17-test log, stdout, actual readiness JSON). Actual readiness JSON SHA256 `84ca960758bca31cdd9c2374f64265bba729c2cf99c090199cede38e33c9293e`.

**Actual outcome:** real original tasks 0/24, candidate repositories 3, same original-checker runtime/adapters not implemented or run, no original task contents imported by this new gate, no model forwards/GPU/frontier/paid calls, sealed original D3 unopened. This software controls PASS is **not a positive Q2/Q3/Q6 validation result**, because no new original source was exercised.

## Core next action and STOP

The next single genuinely useful CPU work is **ONE real original-checker adapter with source-identity binding, strict candidate output type, an actual positive/negative checker pair, and an original-task receipt**. Reuse the verified SyGuS source-only 3VC pipeline where applicable instead of reimplementing a fake checker. Then integrate one actual HumanEval sandboxed evaluator only if its execution isolation and testing are independently trustworthy. Do not proclaim all three origins ready without matching Lean toolchain. Real model experiment EX1 remains blocked until ≥24 hard independently source-verified originals with 3 independently checked families and strong matched TOOL+, and eligible authorized accelerator. No further invented positive toy benchmark tasks. Historical AM1 first actual FAIL unchanged; Q1–Q7 GLOBAL OPEN.

```text
AM2_CHECKER_ADMISSION_FAIL_CLOSED_ENGINEERING = SCOPED_PASS
AM2_ACTUAL_VERIFIED_DIFFICULT_OPENED_ORIGINALS = 0_OF_24
AM2_VERIFIED_FULL_ORIGINAL_CHECKER_FAMILIES = 0_OF_3
AM2_SCIENCE_EX1_OPENED_MODEL = NOT_EVALUATED
AM2_SEALED_EX2 = BLOCKED
Q1_TO_Q7_GLOBAL = OPEN
```
