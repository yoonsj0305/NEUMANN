# NEUMANN 1 | G0 professional classical solver original-goal integrity audit · 2026-10-27

**Mainline scientific state**: frontier-level problem solving with minimum necessary computation. **GLOBAL Q1–Q7 OPEN. G1 HOLD; G2 NOT RUN.** No new neural weights, API/GPU/paid charges or new RC. Existing Draft PR #616 research branch only; `main` and historical original findings unchanged.

## Why this changes the scientific diagnosis
The previous fresh Microsoft PROSE classical baseline solved 3/7 string transformation tasks, 0 WRONG, 4 HOLD. But these four HOLDs show only bounded-DSL failure; they **do not** justify costly G1.

To test a substantially stronger domain-appropriate classical executor from ANOTHER PUBLIC ORIGINAL SOURCE, this independent experiment uses Z3 4.13.3 already installed in the local free CPU runtime. No z3-solver pip package, cvc5, accelerator, frontier API or paid infrastructure is needed.

**Source provenance:** `ultimate-pa/ultimate`, pinned upstream commit `8e820cde14696c5a3bc8fdf2e3f7420dea35310e`, directory `trunk/examples/smtlib/`. Exactly 12 original public source FILE NAMES and evaluation budget frozen **BEFORE reading their original content**, GitHub prereg commit **`a809f1ab4a84aea93f7643a6f73d4fdf74392a75`**. Original byte sequence Git blob SHA1 matched 11/11 actually materialized originals; one 16 KB interpolation script selected but original bytes were not transferred into this runtime, legitimately NOT RUN with NO task replacement. Historical 12 IDs in prereg. Some scripts are deliberately interpolation regression examples and contain expected `:status` annotations. They are NOT a sealed benchmark for frontier generalization, nor different independent original authors for every file.

### The preserved ORIGINAL first run
Pre-registered executable first wrapper `z3_sharedlib_solver.py` SHA256 **`1e8032820bef84e49e40c40bf43b7f702263e711000b97700b5b53b565b2c5f3`**, 3 CPU seconds/5s subprocess wall (Z3 timeout 3000ms), <=800MB process address space, fresh context/process per file. Four pre-source engineering tests SAT/UNSAT/invalid/missing-query PASS.

Original **FIRST machine receipt** `G0_SMT_ORIGINAL_FIRST.json` SHA256 **`e4cc996d8c04836a957f6fc85942ac19eb8ba465e4c92155ce776b314bbb44c0`**. Sealed in GitHub at commit **`e7c97b4efa19cf8756a426dd059656e1de55e7bb`** BEFORE applying verifier integrity corrections.

**Original-result parser bug exposed, NOT erased:** the first wrapper treated a script with stdout `unsat\nunsupported\n; get-interpolants...` as a successful full-script verdict. The original script's `get-interpolants` request FAILED! Solver `unsat` on the assertions alone is NOT proof/interpolant generation. In `pidgeonhole5.smt2`, published metadata says `:status sat` yet the actual formula places 5 pairwise distinct integers in a 4-element domain, whose unsatisfiability was verified independently by exhaustive 4^5 enumeration; naive trust in metadata would also be wrong. These two faults justify fail-closed independent original-goal checking.

### Clearly POST-FIRST corrected gate
Correction code `z3_integrity_v2.py` plus reusable research-only `original_goal_authority.py` and tests. Interpreter stdout errors/unsupported and extra goals `get-interpolants`/proof/model/core prevent **FULL original objective** promotion. The added regex detector is deliberately a conservative gate, NOT a complete SMT parser or a formal proof kernel.

**Exact post-first results**, fixture SHA256 `4ff47405b3b7df40ddd4e3fef3efe65de1f2ce5e4ebc3b01ec744befda2f7597`:
| Objective-complete interpretation | Among preselected 12 files |
|---|---:|
| Z3 returned all original SAT/UNSAT check-sat verdicts with no additional original goal; no independent proof certificate | **5** |
| Original asks for interpolation that Z3 did not provide (some did yield an UNSAT subquery) | **6** |
| Selected original source unavailable locally, not executed | **1** |

The 5 SAT-only original scripts: `bignum_lra1` SAT, `bignum_lra2` UNSAT, `nl` SAT, `arrayextest` UNSAT, `mbqi-z3` UNSAT. Others fail original interpolation support, including a `mccarthy` script with two UNSAT subqueries but **no interpolants**. The baseline's limited task-complete 5/12 does NOT establish a learned proposer could add a useful operator or that other specialist interpolation engines cannot solve the remaining six.

Eleven local process-level runs' sequential wall total in post-first audit ~**8.25 seconds**, including C library loading and subprocess startup per file; time cap 3s CPU, 5s process wall. Neural forwards, GPU, paid external calls **zero**. Data download/connector usage, power, full RAM/energy/$ accounting **UNKNOWN**, and Z3 4.13.3 is not a 2026 state-of-the-art interpolation engine. Cross-solver validation/proof objects NOT RUN. Under this scope no total-compute Pareto claim.

## Actual tested code and portable reproduction
- Reusable goal-authority gate **committed on same research branch**: `research/q3/discovery_policy/original_goal_authority.py` GitHub commit **`e7b35421a4936125b822e2cfba2ec2f1a40a44e6`**.
- Corresponding repo regression tests: `tests/test_q3_original_goal_authority_20261027.py`, commit **`5ccfb4f037ac952cd9584261d5c29ad9183b67bd`**.
- Full conversation ZIP **`NEUMANN1_G0_SMT_ORIGINAL_GOAL_INTEGRITY_20261027.zip`** SHA256 **`1be0ea91d80afb50ccac1ea007d00c4644d92b7802ce79e27bdb59f0e55d7d5b`**. ZIP contains all original written-by-NEUMANN code, frozen first and corrected receipts, original upstream Git SHA1 manifest, optional opt-in fetcher and tests; it **does not repackage third-party SMT scripts or Z3 binaries** because upstream source license for these files wasn't confirmed.
- Clean independent ZIP extraction and `bash REPRODUCE.sh`: **15/15 SHA256 files**, **17/17 engineering tests**, frozen 12-task status-summary replay, independent finite pigeonhole counterexample test PASS. External original full re-execution is OPTIONAL and requires independently fetching exact pinned source bytes on a network-enabled runtime; the historical original 11 files were executed and verified in the current runtime, not falsely described as embedded in portable ZIP.
- No user-owned immutable RC results or earlier G0 first receipt replaced.

## Decision
**G0 professional-baseline feasibility: scoped and correctly audited, but G1 NO ADMISSION.** Interpolation is a separate executable output requirement; Z3's answer to SAT-only subqueries cannot be offered as a complete solution. A specialist interpolation generator and an independent checker would be needed for a fair next external original problem cohort, and *then* an actual ownweight open-expression REFRAME A versus fake-feedback B, strong specialized classical C and memory-allowed D if original headroom + trainable examples exist. A gradient optimizer bake-off (BP/MeZO/EGGROLL/Dust) is not admitted. Failure of this bounded run is not proof of the impossibility of learned new semantic methods.

**NEXT ONE experiment, if available without paid resources:** original cross-author interpolation benchmarks with their real output oracle and a professional free classical interpolation solver, sealed before source inspection and whole-goal scoring. Until those are available, report **HOLD**, not repeat static template macros or charge neural GPU costs. Preserve original program output and authentic verifier evidence.
