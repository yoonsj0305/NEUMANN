# NEUMANN 1 — External SyGuS 2019 Native G0: First Actual Opened Screen

**Date:** 2026-10-09. **Decision:** `EXTERNAL_NATIVE_SCREEN_COMPLETE / NATIVE_6_VERIFIED_2_TIMEOUT / NO_NEUMANN_HEADROOM_ESTABLISHED / HOLD_LEARNING`.

**Repo base:** PR #176 head `c182fd3f8d8b5c711415a214e899bfefe7511a0a`, no main merge.
**Frozen upstream:** `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646`, 2019 invariant-synthesis track.
**Pre-measurement contract:** [external_sygus_native_g0_20261009.preregister.json](../../docs/experiments/external_sygus_native_g0_20261009.preregister.json), SHA256 `7cc01003b45ed3ce144fd0ceb82eef8cda8a2b22e8da25fcf5a3252f42f7e2ad`.
**Runner:** [external_sygus_native_g0_20261009.py](../../experiments/external_sygus_native_g0_20261009.py).
**Original first technical execution:** [37892764426](https://github.com/yoonsj0305/NEUMANN/actions/runs/37892764426) (8/8 `SOLVER_ERROR` from deprecated syntax; no scientific performance measurement). 
**Corrected, separately retained first evaluable execution:** [37892991415](https://github.com/yoonsj0305/NEUMANN/actions/runs/37892991415), [raw artifact 11599291132](https://github.com/yoonsj0305/NEUMANN/actions/runs/37892991415/artifacts/11599291132).

The SyGuS 2019 files used the old `declare-primed-var x Int`. That command was removed from SyGuS-IF 2.1; the official equivalent declaration pair `declare-var x Int` and `declare-var x! Int` was inserted. Original `pre-f`, `trans-f`, `post-f`, invariant target and source bytes were not changed; converted inputs were separately hashed and retained. The correction took place only after all first technical parser failures were preserved.

Runtime: Ubuntu apt **cvc5 1.1.2**, one CPU thread, exactly 15-second subprocess timeout, fresh native process each case. An **independent Z3 4.13.4** checks each synthesized `inv-f` with three separate full symbolic obligations: `pre=>inv`, `inv & trans => inv'`, `inv=>post`, each accepted only when UNSAT. Native wall-clock timing excludes subsequent Z3 verification; therefore NO complete-path NEUMANN speedup or energy claim.

| Source | Native seconds | Three independently checked obligations | Outcome |
| --- | ---: | --- | --- |
| From2018/brett.sl | 0.1330 | UNSAT × 3 | VERIFIED |
| From2018/cggmp2005_true-unreach-call_true-termination.sl | 0.0134 | UNSAT × 3 | VERIFIED |
| From2018/fib_01.sl | 0.0258 | UNSAT × 3 | VERIFIED |
| From2018/ex1.sl | 0.0115 | UNSAT × 3 | VERIFIED |
| From2018/bkley.sl | 0.0150 | UNSAT × 3 | VERIFIED |
| XC/1.c.sl | 15.0185 | not attempted (no candidate) | TIMEOUT |
| XC/10.c.sl | 0.1557 | UNSAT × 3 | VERIFIED |
| XC/100_conf1.sl | 15.0159 | not attempted (no candidate) | TIMEOUT |

**6/8** source tasks certified; **2/8** reached the preregistered limit. From2018 5/5 and XC 1/3; these eight represent two source cohorts and were deliberately selected for diversity, **not a randomly representative score**. Mean/median/hardness conclusions across the competition are disallowed. In this source set, timeouts are not a novel learned-discovery gap: cvc5 v1.1.2 is older and other strong native synthesizers were not compared.

No learned NEUMANN proposer was run, no trained predictor or neural model was fitted, and no free oracle perspective was evaluated. Consequently neither task difficulty nor useful headroom beyond strong native is demonstrated.

**Action:** Keep source-pinned ingestion, syntax migration, solver timeout/error taxonomy and independent three-obligation proof checker. Prioritize head-to-head comparison with a stronger modern native baseline on the SAME eight sources and paid-certificate discovery economics before any G1 or model-training admission. Do not chase the two timeouts by changing goals or choosing favorable replacements.

Complete open evidence (first technical archive + corrected first actual receipts, translated files, independent immutable receipt audit, Korean report) is also retained as ChatGPT zip `NEUMANN1_External_SyGuS_G0_Actual_CPU_2026-10-09.zip` SHA256 `baa1b4970e6bab6876d68b209044e2336e4504a11a97e2847131130aae2c32e5`. Only report/runner/contract/workflow are committed to this branch. Scientific receipts remain GitHub Actions artifacts and separately attached zip.

Historical Q34 PASS, Q5/M106/Decision2 FAIL, other first failures and global Q1–Q7 OPEN remain unchanged. This is **an external native baseline collection**, not a scientific NEUMANN performance admission.
