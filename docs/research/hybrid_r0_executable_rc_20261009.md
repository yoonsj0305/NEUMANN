# NEUMANN 1 Hybrid R0 — Actual Executable Engineering Release Candidate

**Status (2026-10-09 KST):** `R0_THREE_DOMAIN_RC_ENGINEERING_PASS / WHEEL_CLASSICAL_CORE_PASS / FROZEN_SOURCE_MODE_PASS / FULL_HYBRID_PACKAGE_NOT_YET_COMPLETE / SCIENCE_HOLD_LEARNING`.

This report is NOT an independent new model research success. It documents practical integration and a bounded engineering release candidate on top of **PR #176** source SHA `c182fd3f8d8b5c711415a214e899bfefe7511a0a`, without changing historical first experiments or the user-frozen North Star.

## 1. Actual implementation reused

- Single Python module CLI / JSONL: `python -m neumann1.hybrid_runtime_r0`. Typed task, source/goal hash, policy routing, original goal verification and fail closed.
- `lp.standard_form`: paid HiGHS native, existing deterministic residual 4m reduction, untrusted external ranking with original-certificate-gated fallback, optional source-tree archived frozen v102 Q34 pointwise learned ranker, 2m→4m→native expansion. Exact same original LP primal/dual checker.
- `exact.linear`: numeric hint with integer original check, exact rational Gauss-Jordan fallback, full original equations.
- `sygus.invariant`: admitted source syntax, historical SyGuS-IF declaration conversion, external cvc5, independent original init/consecution/safety Z3 obligations.
- Per-request timing stage ledger and total wall; no successful claim from unsupported parsing, invalid learned candidate or unverifiable proof. Cold external calls, memory, startup and offline investment scoped/UNKNOWN, not free.
- No new small language model was trained; only the original archived two Q34 checkpoint seeds are optionally used.

## 2. Actual executable CI receipts

| Gate | Live CI result | Observed original capability and scope |
| --- | --- | --- |
| Base 3-domain 32 tests and official SyGuS original | [Actions 37899428468](https://github.com/yoonsj0305/NEUMANN/actions/runs/37899428468) PASS | 32 engineering pytest checks and three original-goal domains |
| Clean fresh venv, cold and persistent CLI, invalid routes, model-free Edge CPU | [Actions 37902910691](https://github.com/yoonsj0305/NEUMANN/actions/runs/37902910691) PASS | 9 tasks × 2 process modes = 18 receipts; 12 independently certified routes, 6 safe ERROR/UNKNOWN; peak 4ms-sampled whole process tree **164.05 MiB**, model-free; cold outer process calls **1112–1149 ms** |
| Optional existing frozen Q34 neural proposal, cold/warm and 4GiB-class Edge CPU memory | [Actions 37903498335](https://github.com/yoonsj0305/NEUMANN/actions/runs/37903498335) PASS | One opened v102 original × 4 routes, all original LP certified. Measured process high-water RSS **689.94 MiB**, under 4096MiB; Native **107.23 ms**, residual 4m **63.46 ms**, frozen **cold 1260.63 ms** vs **same-process warm 52.42 ms**. NOT unseen generalization or energy verification |
| Standard distributable wheel, installed independently OUTSIDE Git checkout | [Actions 37903680952](https://github.com/yoonsj0305/NEUMANN/actions/runs/37903680952) PASS | Built `neumann1-0.0.106-py3-none-any.whl`; fresh wheel-installed three domains all ORIGINAL VERIFIED; wheel with no historical model assets safely returns UNKNOWN/ERROR for frozen-Q34 requested policy. Artifact [11603656975](https://github.com/yoonsj0305/NEUMANN/actions/runs/37903680952/artifacts/11603656975). |

Note: separate first optional-frozen-memory technical run [37903301328](https://github.com/yoonsj0305/NEUMANN/actions/runs/37903301328) **FAILED AFTER 4/4 original LP certs** because a new test compared policy-scoped wrapper hashes instead of stable original v102 source hashes. Original failure retained, source identity checker fixed, subsequent [37903498335](https://github.com/yoonsj0305/NEUMANN/actions/runs/37903498335) PASS. No task, checkpoint, or original verification authority modified.

See exact first resource receipts and negative/fallback case list: [clean-install report](hybrid_r0_clean_release_gate_20261009.md), [real source-run docs](hybrid_r0_first_slice.md) and Actions artifacts.

## 3. What is actually usable

**Classical-only wheel** (source independent, verified):
- Python 3.12 and installed permitted dependencies (NumPy, SciPy, scikit-learn, HiGHS, Z3, cvc5 for invariant domain).
- A single JSON task via stdin / multi-request `--jsonl`, with JSON answer, `VERIFIED / REJECTED / UNKNOWN / TIMEOUT / ERROR`, typed certificate and cost receipt.
- No cloud or big-model requirement. Supports Edge CPU in tested Linux environment; 164 MiB sampled RSS for the model-free tested workload, no energy/thermal guarantee.

**Optional frozen Q34** (still SOURCE + archives mode only):
- Requires original historical v100/v101/v102 source/authority files, pinned PyTorch CPU dependencies, model seed 100001/100002, both cached and cold accounting.
- Does work on an opened Q34 original; high-water process RSS 690MiB in the tested Linux runner. **It is not included in the distributable wheel**, and no independent external LP generalization or cloud/energy advantage is established.

**Do not misrepresent** the wheel as shipping a new original NEUMANN learned core. Do not merge evidence branches or change PR #174/#175/#176 ancestry blindly. Keep R1/R2 and Decision3 sealed.

## 4. Shortest remaining R0 product closure

1. **One integration review and PR CI:** inspect the actual PR stack, choose an integration base, do not overwrite legacy behavior or import compatibility.
2. **Explicit optional frozen model packaging policy:** either provide a hash-pinned optional authority bundle/installer with no bundled sealed data and a verified source/license provenance, or formally ship Classical Edge R0 while freezing optional learning as cloud/dev mode. We must not silently fetch or train checkpoints.
3. **Import-time/cold-start reduction as measured:** ~1.1s fresh process cost is material compared to <100ms inner solving; avoid sweeping refactors of legacy package `__init__` without full tests. A persistent service/JSONL already works and makes warm reuse practical.
4. **Truthful release artifacts:** the existing built wheel, complete original verifier receipts, capability matrix and dependency manifest, with unknown edge energy and cloud total costs labeled UNKNOWN.

After R0 product freeze, only **ONE** pre-registered external G0 strong-native paid-proof headroom experiment is scientifically required before deciding whether to train a new structural proposal. No P1 treadmill, no retrospective false “10×”, no fabricated Q1–Q7 closure.

**Decision:** `KEEP_R0_RC / FREEZE_FEATURE_SCOPE / FINISH_OPTIONAL_MODEL_PACKAGE_AND_INTEGRATION / HOLD_NEW_LEARNING`.
