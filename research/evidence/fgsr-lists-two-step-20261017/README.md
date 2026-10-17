# Real RustHorn Lists-4, developer-opened formal certificate attempt

2026-10-17. Development-only and **post-inspection human conjecture**, never an unseen neural holdout. The source was preregistered for the earlier Z3 screen (commit `02c0b6e`) and is already opened. That first 10-second native Z3 run returned TIMEOUT_OR_ERROR; Eldarica v2.3 30-second run TIMEOUT. Neither proves the source impossible or learned necessity.

**Candidate statement:** For a recursive list transducer that picks and mutates an element and residual list, track the total sum change by a typed tuple's `Δhead + Δrest_sum` rather than enumerating individual list states. The second `take_some_rest` call changes its head by one while leaving its residual list unchanged; the first call changes its head by one and its residual list by the second call's output. Hence whole-list sum changes by two. This structure is conjectured by a human *after reading* this exact benchmark, not by NEUMANN or a frozen learner.

Exact original identity: upstream `chc-comp/rust-horn` `e5a86a1ad252fe1df75e06814769ec1d14540032`, `lists-4-inc-some2-safe.smt2`, SHA256 `a73dd31be612a9d01efee2c9d1aad59ae7c3ec9a84ba51d5d450ca4100a5b6db`, git blob `5386fa67ac0248f9e8a3c4eb15465e1cac61d0b9`.

**Verification contract:** every original universally quantified Horn assertion remains unchanged; definitions are total recursive SMT functions for `SUM` and `DELTA` and concrete interpretations for seven original relations. Each original clause is independently negated and fed to an isolated Z3 process. Only 12/12 `UNSAT` plus two falsifications `SAT` earns the bounded exact safety proof. UNKNOWN, source mismatch, parser failure or timeout = ABSTAIN, no false positive. The 10s Z3/30s Eldarica historical first results may never be revised based on this posthoc witness.

Full Q3/Q4/Q7 remain OPEN. No fair computational speed comparison: hypothesis invention was uncharged; the original has already been inspected; no learning contribution, model baseline or frontier evidence.

Reproduce on Linux with native z3 and Python 3.11:
```bash
python research/evidence/fgsr-lists-two-step-20261017/original_lists_formal_proof.py --source /path/to/exact/pinned/original.smt2 --output /tmp/fgsr_lists_result.json
```
