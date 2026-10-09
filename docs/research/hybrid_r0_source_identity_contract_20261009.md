# Hybrid R0 original-problem identity contract (2026-10-09)

**Scope:** Engineering hardening on top of Hybrid R0 PR #177 head `5cbda9d363d877438da9d3f227307f6ddc17d8a9`. No new task corpus, model calls, fitting, threshold tuning, Decision 3 access, scientific admission or claims of frontier capability.

## The bug addressed

The pre-existing receipt `original_task_sha256` hashes the entire request, including LP `policy`, `ranking`, `seed`, and `budget_s`. Thus identical original mathematics under Native, residual4m and learned execution get **different** request hashes. Pairing by that legacy field is invalid for iso-capability evaluation.

## Additive, backward-compatible resolution

- `original_task_sha256`: **unchanged legacy request hash** for reproducibility of older receipts. Existing evidence is immutable.
- `execution_request_sha256`: explicit alias of the legacy request hash, so policy/seed/budget changes must change this digest.
- `original_problem_sha256`: digest of only source-level original mathematical content **after accepted validation**:
  - LP: `{domain,A,b,c}` only.
  - Exact linear: `{domain,A,b,variables}`; omitted default variable names are normalized.
  - SyGuS: `{domain,source}` only.
  - Invalid input: `null`, never a falsely validated problem identity.

Identity uses canonical sorted-key JSON. Equality of identity proves equality of these canonical input fields, **not** algebraic equivalence of differently encoded mathematical problems. Family IDs, semantic normalization, reference solutions, model rankings and solver-derived answers do not enter the digest.

`original_problem_sha256` is suitable to match execution policies on a single identical original. It is **not** a substitute for independent `source_group_id` in structure-family generalization, a human-reviewed license/source ledger, or the certificate itself.

## Engineering tests

Four regression checks in `tests/test_hybrid_runtime_r0.py`:
1. Identical LP under Native / deterministic classical / untrusted external ranking has one original hash and three request hashes, with all results originally verified.
2. Changing LP objective changes original-problem hash.
3. Omitting versus explicitly specifying default exact-linear variable names yields the same original hash.
4. Invalid boolean coefficient receives no validated original hash.

Retest frozen original BP and Q34 controls as already opened engineering regression; do **not** promote those views to fresh validation.

## Release and research gate

Do not claim `R0_COMPLETE` solely from these tests; packaged classical wheel, optional model source/archive boundary, integration CI and released artifact manifests still require final review. F0 frontier paired comparisons must use **original_problem_sha256** together with original source/group provenance and the independent verifier receipt. F1 remains blocked until actual authenticated frontier/small paired successes/failures under equivalent tools, model revisions, resource accounting, fresh family splits and external certification.

Decision: `SOURCE_IDENTITY_HARDENING_IMPLEMENTED_PENDING_CI / HOLD_NEW_LEARNING / Q1_Q7_OPEN`.
