# FGSR · Full nonlinear original-source DAG verifier, first actual receipts

**2026-10-16 | Development-only | Q1–Q7 all OPEN | NOT an original SAT/UNSAT proof.**

## The missing semantic step was implemented and independently tested

The preceding bounded linear error-path study skipped **17 original triple-premise Horn rules**, rendering all negative reachability claims inherently incomplete for the target. The new executable [full_nonlinear_dag_one.py](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-single-independent-family/full_nonlinear_dag_one.py) reads **all 48 untouched original Horn assertions** directly with Z3 4.13.3, including every original triple-premise relation. It builds a bounded *DAG of facts*; each new fact must cite a source Horn rule with its exact parent facts and original integer guard obligations. A potential UNSAFE witness is accepted only after independently replaying every derivation node in a new solver, applying an original error rule and the terminal false clause.

Original pinned CHC-COMP SHA256 `2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645`. Source is external and previously opened; not a clean neural test. No source clauses changed. Source rule premise-arity counts including error and terminal: 0:2, 1:29, 2:0, 3:17. The proof-DAG constructive choices are **classical, not learned**, and select 45 Inv-concluding rules; terminal guards are taken from original error clauses rather than written by researchers.

### First original execution (do not overwrite)

[GHA #38922634276](https://github.com/yoonsj0305/NEUMANN/actions/runs/38922634276), artifact #12055920869:
- 6 nodes: UNSAT in 268.891ms (SMT solver portion, build excluded)
- 10 nodes: UNSAT in 1,440.620ms
- 14 nodes: UNKNOWN at 25,016.862ms
- 18 nodes: UNKNOWN at 35,030.723ms
- Total 64,957.495ms. **No certified concrete original error DAG**. No safety proof.

### Critical semantic bug caught by independent tests; repaired without editing external target

The initial candidate generator hardcoded `state[-1][3] in {0,1}`. That happened to coincide with the opened target's error rules, but failed an unrelated tiny nonlinear-Horn verifier test, proving the verifier was NOT portable to arbitrary goals. The actual mechanism was corrected to build the terminal error-goal disjunction from **each original `CHC_COMP_FALSE` Horn rule's own guard and premise**. It never inserts a hand-chosen goal into a new source. The correction preserves the meaning for the original 48-Horn case.

The [9 independent verification regression tests](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-single-independent-family/test_nonlinear_dag_certificate.py) confirmed a 2-input conjunctive join lemma's finite proof graph is valid and rejected: forged future parents, dropped nonlinear parent, corrupted final state, tampered original source goal, wrong source rule number and source-clause count. This synthetic microcase checks *soundness of the certificate mechanism*, NOT general learned intelligence or hard-original solution.

**First checker regression run #38923215279 failed 8/9** (one incorrectly generic test expectation exposed goal-hardcoding). Retained in CI history, NOT concealed. Source-goal correction is [commit 7bb5c2c](https://github.com/yoonsj0305/NEUMANN/commit/7bb5c2c89ac0e8767b3dae770d6f7e7cf5f22840). Retest [GHA #38923476216](https://github.com/yoonsj0305/NEUMANN/actions/runs/38923476216): **9/9 PASS**, including exact nonlinear 2-parent joining and goal tamper refusal; real original was run fresh:

| DAG fact nodes | Original-source-goal-bound check | Z3 solve wall |
|---|---|---:|
| 6 | UNSAT | 410.044ms |
| 10 | UNSAT | 2,289.477ms |
| 14 | UNKNOWN | 25,016.903ms |
| 18 | UNKNOWN | 35,031.648ms |

Full parent wall **67,579.445ms**. Authentic certificate count **0**. Exact first corrected receiver artifact ID **12056120918**, SHA256 archived receipt ZIP `34d341ae8d98258a5e76b3b7eda873e114fb8fa37802f9d4b77d2b749a5fbc65`.

**Scientific verdict: `NONLINEAR_DAG_PROOF_CHECKER_CONTRACT_PASS / ORIGINAL_SAT_OR_UNSAT_STILL_UNPROVEN / NO_LEARNED_MODEL / Q1_Q7_OPEN`.** A 6/10-node UNSAT shows *bounded witness absence*, not global Horn safety; 14/18 UNKNOWN show finite capped compute, not a classical impossibility. No claim of advantage or frontier equivalence.

## Next decision

Stop more opened-original classical bounded-depth runs. A learned, source-conditioned proposer must independently emit useful **symbolic content** (new invariant formula OR exact Horn proof DAG) against this source-bound validator, then face original proof, ablation and matched specialist classical controls on a **separate preregistered source group**. The current task implemented and tested the validator, **not the learned proposer**. Do not promote Q3/Q4/Q7 or claim 10x. Q7 provider SMALL-vs-FRONTIER receipts remain unavailable.
