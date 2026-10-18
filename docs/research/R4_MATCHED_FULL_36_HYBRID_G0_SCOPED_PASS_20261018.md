# NEUMANN 1 | R4 matched FULL hybrid end-to-end 36-source pilot · 2026-10-18

## Scientific verdict

**R4 SAME-HOST OPENED-DEV FULL SYSTEM GATE = PASS** for its **pre-registered** engineering cost+accuracy scope: on 36 unchanged already-examined QF_NIA originals, the *previously fixed classical* exact integer-polynomial source certifier gated by *previously fixed* R3 AST negative preflight, plus fresh Z3 fallback, delivers **22/36** original SAT/UNSAT verdicts versus ordinary Z3 alone **19/36**; measured same-host CPU wall **49.934357s** including frozen code fetch versus Z3 alone **51.567046s**, and versus the ungated old classical hybrid **60.920883s**. Every historical original source-verified UNSAT certificate (4/4) preserved.

**THIS IS NOT GLOBAL G0, G1, G2 OR Q1–Q7 PASS.** All 36 were OPENED engineering regression fixtures from only two known origin families; the specialized old certifier was manually engineered. Not frontier-level learned generalization, 10×, energy nor strongest classical-specialist gain. The earlier R1 ELSTER independent-origin research campaign remained NO-GO on no additional original SAT solve.

## Same machine, original bytes, fair run execution

PRE-REGISTERED [GitHub Issue #227](https://github.com/yoonsj0305/NEUMANN/issues/227) before new R4 same-host cost measurement. Exactly:
- **27** original `SMT-LIB/benchmark-submission-2023/QF_NIA/20230328-sqrtmodinv-hoenicke`, original Git SHA `7f993a017850ba547c6ea19a1bf3b54adf54a449`;
- **9** original `SMT-LIB/benchmark-submission-2025/QF_NIA/20250331-elster`, original Git SHA `37c6cd5d98edb46057f30cef35ba7c7250fe0161`.
- All **36** original SHA256 unique and input identities logged; Elster Git blob IDs also checked. Same pinned original source bytes fed independently to all three arms. No source expected SAT/UNSAT status fed into any solver or router.

Three arms ran on ONE free Github ubuntu-latest CPU job, with **deterministic A/B/C order rotated by original index**, using separate **cold subprocesses**:
A. `z3-solver==4.15.4.0` original Z3 alone, external 3s wall cap per file.
B. Old full hybrid: frozen original independent-SMT-LIB-verifying integer-polynomial certifier, external 5s cap; if NO mathematically independently source-certified UNSAT, fresh cold original Z3 3s fallback. Does not reuse A's result.
C. Exact R3 gated full hybrid: cheap 4-token necessary-condition plus independently original Z3 AST required-pattern inspection (fail-open on unsupported parse), invokes **same exact B certifier** only if admissible, otherwise immediately invokes **fresh original Z3** 3s fallback. No change to fallback solver or proof mathematics. Does not reuse A/B's results.

Old source proof originally pinned Git SHA `c051985ceb216c5e2e3685e28c5f5a0e064850e2` with Git blob SHA1 `ff493a21b626733e2797487974388fa6e93b56ec`. Original R3 router pinned commit `01acd8153f3268754a7a01e93509259bb97696bc` with Git blob SHA1 `7e378010ac671e34bf7784b83a4a7cf37354769a`. Both were **fetched and hashed BEFORE execution**, byte-for-byte identical to past registered algorithm. `z3==4.15.4` version enforced. Neural inference/training, GPU or paid API calls ZERO.

Shared 36 original source downloads **and** package installation happen once on same runner for all three arms and are deliberately excluded symmetrically. Pinned structural algorithm source fetch **0.199981 seconds** is instead charged equally to both hybrid arms as conservative startup overhead. The benchmark includes all separate cold Python engine imports, original parsing, attempted proof, independent original verification, routing and fallback solver time. It is **not** a full production cloud-cost/energy meter including environment provisioning and CI scheduler latency.

## Immutable first run and independent artifact audit

- [FIRST Github Actions SUCCESS #39126237235](https://github.com/yoonsj0305/NEUMANN/actions/runs/39126237235). Workflow success is an execution outcome, NOT global frontier success.
- [FIRST entire original receipt artifact #12135583479](https://github.com/yoonsj0305/NEUMANN/actions/runs/39126237235/artifacts/12135583479), downloadable ZIP SHA256 verified locally **`76a019ad0b27ecf8066b25050e7ab171d7eadd1ea718a5759107324422e4296a`**, receipt member `r4_all36_samehost_first_full_system.json`. Independently opened JSON, re-counted 27+9 exact original SHA256 unique, 4 original named certificates, full per-file statuses and all measured transaction wall numbers, 0 proof errors.
- Exact original mathematical certificates (4/4 in B and C): `modInvStep.smt2`, `modInvStepSimplified.smt2`, `modInvVar1.smt2`, `modSimpleTest.smt2`; all from Hoenicke 2023. 32/36 failed to meet exact mathematical proof prerequisites and used independent fresh original Z3 fallback.
- All 9 Elster tasks were originally SAT according to their source reference, but the two `sat` accepted answers are *raw Z3 solver claims*, **not independently verified SAT assignments**. Separate mathematical source certificates are only for the 4 UNSAT originals; the remaining 16 ordinary UNSAT claims are standard original solver returns, source-status consistent but not separately proof-certified.

| Arm | Accepted source outcomes | SAT claims | UNSAT cert or raw claims | 36 cold-case wall | + pinned code fetch when applicable |
|---|---:|---:|---:|---:|---:|
| A: standalone original Z3 | **19/36** | 2 | 17 | **51.567046s** | N/A |
| B: old structural proof then Z3 fallback | **22/36** | 2 | 20, incl 4 certs | 60.720902s | **60.920883s** |
| C: R3 gated old proof then Z3 fallback | **22/36** | 2 | 20, incl 4 certs | 49.734376s | **49.934357s** |

Compared with B, C **saves 10.986526s (18.0341% lower full-corpus CPU wall)** with **no original accuracy/certificate regression**. Compared with A, C adds **three mathematically independently proven original UNSATs**, completing 22 vs 19, and uses **1.632689s (3.1661%) less** measured total wall on this one runner. Ratio versus A `51.567046/49.934357≈1.0327×`; this is **not 10×** and not a robust statistical benchmark. No shared-source fetch artificially credited.

### Family-specific counterexample (must not conceal)

| Family | Z3 alone | B old hybrid | C R3 hybrid | Correct extra certificates |
|---|---:|---:|---:|---:|
| Hoenicke 2023, 27 | 29.511991s | 30.983536s | **23.316313s** | 3 additional correct originals versus Z3 |
| Elster 2025, 9 | **22.055055s** | 29.737366s | 26.418063s | **0** |

R3's real gains are concentrated on already-explored Hoenicke unsatisfiability proofs. On 2025 original SAT source Elster, it successfully removes useless heavy proof attempts yet still costs **4.363008s MORE** than ordinary Z3 alone, because even original Z3-AST preflight and cold-process overhead have a cost. Thus **no unconditional cross-domain routing economic superiority is proven**. The observed full-corpus advantage against Z3 is a weighted distribution benefit and may disappear on an unfamiliar task mix. Any new universal routing claim needs a new prospective independent provenance source.

## Gate adjudication: R4 is CLOSED precisely, global questions remain OPEN

- `R4_OPENED_DEV_FULL_36_SOURCE_CERTIFICATE_PRESERVATION=PASS` (4/4 exact mathematical proofs preserved, with source identity).
- `R4_OPENED_DEV_FULL_36_COMPLETE_CPU_G0_VS_OLD_AND_Z3=PASS` (22/36 vs 19/36 accepted, 49.934s vs 60.921s old hybrid and 51.567s Z3, one cold-process same-host trial).
- `R4_2025_SAT_ONLY_ELSTER_VS_Z3_COST=FAIL` (26.418s vs 22.055s, zero new answers).
- `G0_FULL_UNSEEN_INDEPENDENT_SOURCE_STRONGEST_CLASSICAL=OPEN`, **`G1=HOLD_LEARNING`**, `G2=BLOCKED`, **GLOBAL Q1–Q7 OPEN**.
- This is hand-designed **classical symbolic computation plus conventional solver portfolio**, not a learned NEUMANN model or a verified frontier small-parameter model. R1 original source-family candidate NO-GO preserved.
- STOP this targeted router-cost optimization campaign after ONE preregistered first receipt. The first-run results and negative cross-domain subgroup are decisive; no posthoc case selection, per-family bypass based on gold labels, benchmark-timeout inflation, model training, paid API/GPU or new PR.

Reproduction: [R4 executable full 36 runner](https://github.com/yoonsj0305/NEUMANN/blob/research/r4-matched-endtoend-36-20261018/research/evidence/r4-matched36/one_shot_all36_old_vs_r3_full_hybrid.py), [R4 registered issue](https://github.com/yoonsj0305/NEUMANN/issues/227).
