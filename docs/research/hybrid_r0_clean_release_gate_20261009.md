# NEUMANN 1 Hybrid R0 — Clean-Install and Edge-CPU Engineering Gate (2026-10-09)

**New engineering status:** `HYBRID_R0_CLEAN_INSTALL_ENGINEERING_GATE_PASS / FULL_R0_RELEASE_NOT_YET_ADMITTED / R1_R2_NOT_ADMITTED / HOLD_NEW_LEARNING`.

## Single first executed gate

- Source code commit: `32f06ad20edfe683f16b9ecd137201ddccb4ab78`.
- [Successful GitHub Actions 37902910691](https://github.com/yoonsj0305/NEUMANN/actions/runs/37902910691), first research gate run. [Artifact ID 11603635694](https://github.com/yoonsj0305/NEUMANN/actions/runs/37902910691/artifacts/11603635694), ZIP SHA-256 `f8a18b27047bb5993805a0d2cedfd4204847b331553cf311b89333ebbd63225b`.
- Runner: [`experiments/hybrid_r0_release_gate_20261009.py`](../../experiments/hybrid_r0_release_gate_20261009.py); workflow [`.github/workflows/hybrid_r0_clean_release_gate_20261009.yml`](../../.github/workflows/hybrid_r0_clean_release_gate_20261009.yml).
- Fresh Python 3.12 venv, pinned NumPy 2.3.5 / SciPy 1.17.0 / scikit-learn 1.9.1 / highspy 1.15.1 / Z3 4.13.4.0 / psutil 7.0.0; apt cvc5 installed in host. No frozen Torch or trained models invoked in this gate.
- Official real `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646` `comp/2019/Inv_Track/From2018/ex1.sl` SHA-256 `930b37d15f14baf615c7e7741ef5d607db717390bb8465ad8255a0d12764125c`. It is already OPENED; do not claim fresh external evidence.
- No other GitHub project files, historic result archives, prior CI runs, sealed Decision 3 or frozen North Star were mutated by this work.

## Actual accepted tests and measurements

**Existing engineering regression:** `32 passed in 2.24s` after clean import.

Nine pre-fixed tasks were each executed once in an independent cold Python process, followed by the same nine in one persistent `--jsonl` Python process: **18 receipt records**.

| Scenario | Expected and observed | Original authority |
| --- | --- | --- |
| LP strong Native | VERIFIED | original primal/dual LP checker |
| LP deterministic residual 4m | VERIFIED | original primal/dual LP checker |
| LP deliberately misleading external ranking | VERIFIED **via actual fallback** | original primal/dual LP checker |
| Exact rational (noninteger) | VERIFIED | full original integer matrix equations |
| Exact integral | VERIFIED | full original integer matrix equations |
| Exact singular | UNKNOWN | no fabricated full solution |
| Unsupported task | ERROR | no executor call |
| Real external SyGuS `ex1.sl` | VERIFIED | independent Z3 init/consecution/safety, UNSAT ×3 |
| Unauthorized/unsupported SyGuS option | ERROR | rejected before native cvc5 |

- Certified original-path receipts: **6 per process mode, 12 total**. Failure/unknown receipts: 3 per process mode, 6 total. Every accepted original result has its own certificate event. No model or frontier calls.
- The intentionally incorrect external ranking recorded external proposal cost **UNKNOWN**, not free, and went through the verified full Native fallback.
- Observed **4ms-sampled maximum entire process-tree RSS: 164.0547 MiB** across the cold or persistent runs. Provisional engineering budget 4096 MiB; this *sampled* peak is a lower bound, not a rigorous maximum. It includes the sampled cvc5 process tree and excludes all frozen neural-model runtime.
- Cold fresh-process outer wall, in milliseconds: LP Native 1149.3, residual 1138.0, external-fallback 1141.1, rational 1119.8, integer 1131.9, singular 1144.2, bad domain 1118.7, SyGuS 1146.5, bad SyGuS source 1112.1.
- These 1.1–1.15s wall costs **include process bootstrap, Python imports, I/O and solve/certificate** and expose a potential cold-start improvement opportunity. They must not be replaced with inner solver-only runtimes when claiming whole-service economics.
- Persistent JSONL correctly emitted nine task-bound independent signed hash/certificate results and measured tree RSS. Per-case actual timings are in `first_run_receipts.json`, not retyped as speculative medians.

## Scientific claim boundary

This is an actual ***engineering*** success in a clean environment, NOT an R1/G1 learned improvement, fresh scientific test or Frontier Gap recovery. It does not measure energy, thermals, real deployment, long-run service traffic, worst-case resident memory, Windows behavior, cloud latency or full model lifecycle. R0 is not yet signed as a deployable product release.

Previously checked frozen LP checkpoints: [cold native vs frozen](https://github.com/yoonsj0305/NEUMANN/actions/runs/37897312107), [cold and same-process warm frozen](https://github.com/yoonsj0305/NEUMANN/actions/runs/37897620753). Same one OPENED historical LP; frozen cold **~1260ms**, same-process warm **~52ms**; comparisons not replaceable by this model-free RSS screen, and statistical repeat/generalization is not demonstrated.

## Remaining R0 closure

1. **Cold startup optimization / acceptance:** the ~1.1s clean CLI bootstrap is a likely deployment constraint. Diagnose import path; do not change the public NEUMANN `__init__.py` without full compatibility tests.
2. **Frozen learned Edge mode:** measure sampled process-tree peak, cold/warm lifecycle and ability to operate inside a declared RAM budget with Torch checkpoint. If not, admit classical-only Edge mode, keep learned mode cloud-optional. No silent model swapping.
3. **One distributable R0 entrypoint/release manifest:** reproduce versions, source SHA, test outcomes and cost-receipt schema. Consider existing project as package rather than a separate subsystem.
4. **Contract clarity:** tested three domains with original certificates and negative controls; no new semantic LLM parser or novel sufficient representation generator. All Q1–Q7 OPEN, historical first records frozen, `HOLD_NEW_LEARNING`.

**Decision:** `KEEP HYBRID_R0 ENGINEERING / NEXT: COLD START AND FROZEN MODEL MEMORY / NO NEW SCIENTIFIC G0`.
