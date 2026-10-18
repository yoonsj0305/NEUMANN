# NEUMANN 1 | G0 FIRST SAME-CPU HYBRID COST GATE · BOUNDED PASS (2026-10-18 KST)

## Decision

**Mathematically certified exact source UNSAT proofs + Z3 4.15.4** achieve **20/27 accepted original-source UNSAT results** in **21.290438 seconds conservatively charged** versus **17/27** results in **29.103975 seconds** for ordinary Z3 alone, on the **same free GitHub Actions Ubuntu CPU runner**, with the **same source bytes**, fixed 3-second external subprocess wall cap and no gold answer hints. This is a **single-run, previously opened DEVELOPMENT source-family, one-baseline, bounded G0 hybrid gate PASS**, **NOT** global NEUMANN Q3/Q4/Q7 frontier success, or a validated 10× speedup.

- Accuracy: 20 original correct UNSAT answers vs 17, +3 extra/27, 17.65% more solved relative to Z3 17.
- CPU wall: 21.290438s hybrid (including source-engine program fetch + import/initialize **0.514038s**) vs 29.103975s Z3-only; **7.813537s (26.847%) less wall**, speed ratio **1.3670×**.
- Shared original source download (27 files, pinned git): 4.088150s and identical bytes shared between both arms, **excluded symmetrically** from the comparison. Counting it as a once-per-arm end-to-end transaction yields Z3-only **33.192125s** versus hybrid **25.378588s**. These only include the inside-job benchmark transaction; neither CI job scheduling nor Python package installation are included. Do not confuse these totals with datacenter GPU joules/dollars.
- Source UNSAT correctness: 4/27 original certificates from previously validated exact `ZZ[variables]` source-derived integer-polynomial relations and independent original Z3+sound lemma check; 1 overlaps Z3 ordinary UNSAT, **3 additional originals** are `modInvStep.smt2`, `modInvStepSimplified.smt2`, `modInvVar1.smt2`. `modSimpleTest.smt2` is solved fast by both and brings no unique increase.
- Correctness scope: historical original expected statuses all `unsat`; current Z3 ordinary UNSAT outputs are source status labels and solver claims, not fully external independent UNSAT certificates. The 3 added source proofs have explicit mathematical certificates.

## Original task and algorithms were frozen before new measurement

The source family `SMT-LIB/benchmark-submission-2023/QF_NIA/20230328-sqrtmodinv-hoenicke` Git commit `7f993a017850ba547c6ea19a1bf3b54adf54a449` comprises precisely 27 original SMT-LIB source files, all previously opened during old developer experiments. The complete original filename list was held unchanged. Both algorithms used the **same in-process cached source bytes**; for each file, a cold Z3-only subprocess was executed and a distinct cold hybrid fallback Z3 was executed if the exact-source structural prover did not certify UNSAT. Baseline and hybrid ordering alternated deterministically by pre-frozen filename index parity to reduce ordering artifacts. They **did not reuse the same Z3 baseline outcome** for the hybrid.

Frozen structural algorithm was downloaded as *exact original source* from NEUMANN Git commit `c051985ceb216c5e2e3685e28c5f5a0e064850e2`, Git blob SHA1 `ff493a21b626733e2797487974388fa6e93b56ec`, and then imported unmodified. Frozen Z3 harness source was pinned to `8908cee332c6984752be8edb8d0764ce3ea84312`, Git blob SHA1 `c60ba47adc8a0a9b811ee7318bf3599491075de9`. Original sources were never changed. No model training, no paid API, no GPU.

## Independent first receipt

1. [Issue #223 pre-registration](https://github.com/yoonsj0305/NEUMANN/issues/223) created BEFORE executing this specific matched cost test, preserving original benchmark set and exact gate conditions.
2. [GitHub Actions first SUCCESS #39119117181](https://github.com/yoonsj0305/NEUMANN/actions/runs/39119117181), CI head `cc3de09f002e4eb87d9b12bccb8f12e675b7ea91`.
3. [Immutable full first artifact #12133152837](https://github.com/yoonsj0305/NEUMANN/actions/runs/39119117181/artifacts/12133152837), ZIP SHA256 `65d9b8a3be5952856f40afb1c371e1ce57dfe60e1c72217fbcec065154942390`, 27 per-file SHA256, both independent execution outcomes, wall times, certificate status, script blob SHA, source bytes and conservative startup overhead included.
4. Independently re-read downloaded receipt ZIP and recomputed the 17, 4, 20, 3 union with 27 exactly distinct original SHA256 values, all matching the first-run report. Recomputed speed ratio `1.3669974755803518` and time reduction `26.846975370202852%`. No tampering, no dropped source cases.
5. Source code: `research/evidence/g0-hybrid-matched27/frozen_hybrid_same_cpu_first.py` on research branch `research/g0-hybrid27-matched-allin-20261018`, one-shot free GitHub Action `.github/workflows/g0-hybrid-27-matched-allin.yml`.

## Falsification / external validity

- **First run only**, 27 opened public source cases from one generator. Source specificity and posthoc original theorem discovery limit generalization. No untouched independent-domain blind test for this new Newton method, no learned controller and no frontier-model calls. The result demonstrates a classical structural solver **portfolio** benefit, not a novel learned architecture.
- Z3 4.15.4 is **one** mature baseline but NOT the strongest available full nonlinear integer specialist portfolio; qfn2l optimized C++/native, other tactics, and alternate long wall caps were not matched here. A stronger algebraic tactic may already discover all four quickly and dominate both methods. Therefore this result is NOT universal classical-specialist headroom.
- Evidence supports improvement in measured CPU wall, not hardware power or parameter count; no energy meter, no GPU comparison, no data leakage-safe training comparison. Accuracy+compute development result does NOT close overall frontier-level goal.
- Since the hybrid first runs its source proof on all 27, then calls Z3 only for unproved cases, it makes genuine extra source-certified correct claims **without rejecting any of Z3's previously solved cases** in this run. However an adversarial unseen corpus might have a slow prover and no extra solve, so performance guarantee is **NOT** established.

## FAST-CLOSE bounded gate status

| Gate | This exact scope |
|---|---|
| G0 classic structural source proof exists | **PASS** (4/27, with 3 new vs Z3 capped) |
| G0 same-runner one-baseline hybrid more answers at less total compute wall | **PASS** (20/27 vs 17/27; 21.29s vs 29.10s) |
| G0 strongest classical specialists and source-family-isolated prospective transform gap | **OPEN** |
| G1 autonomous neural structural invention/generalization | **HOLD / NOT TESTED** |
| G2 frontier-level quality for minimum necessary compute | **BLOCKED** |
| Q1–Q7 GLOBAL | **OPEN** |

**Next scientifically justified move:** freeze the whole **hybrid**, including detection order and fallback/verification cost, on a genuinely NEW source-family-isolated corpus *before opening source or answers*, compare with the strongest specialist under equal CPU and total cost, and require positive original verified union. Otherwise stop and preserve this bounded PASS as a useful classical-hybrid proof of concept rather than falsely mark global questions closed.
