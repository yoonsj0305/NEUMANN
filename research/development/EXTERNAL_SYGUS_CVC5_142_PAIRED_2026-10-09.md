# NEUMANN 1: Paired official cvc5 1.1.2 vs stable 1.4.2, SyGuS 2019

**Date:** 2026-10-09 KST  
**Scientific classification:** `COMPLETED_OPENED_NATIVE_PAIRED / NO_LEARNED_NEUMANN_HEADROOM / HOLD_LEARNING`.  
**Lineage:** new branch forked from `research/external-sygus-native-g0-20261009@0be10d66a8dd0521ddbc1f6004afc8465ccbb248`; initial NEUMANN research base `c182fd3f8d8b5c711415a214e899bfefe7511a0a` (PR #176), no main merge.

## Pinning and first result

- **Upstream:** `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646`, exact same 8 `Inv_Track` source files selected *before* first cvc5 run.
- Frozen new [paired preregistration](../../docs/experiments/external_sygus_cvc5_142_paired_20261009.preregister.json) SHA-256 `7db71c255b91ea5c5a4b27a2f281f0d217d6cdccdc2fa2796b0bb06391bbc39a`.
- Old native: Ubuntu apt `cvc5 1.1.2`. New native: official stable **cvc5 1.4.2**, released 2026-10-08, static Linux-x86_64 ZIP SHA-256 `7eb18f8c814c36a46c5a7d003983e9cfbc4b0a9828d6dd596239291bd4cc61d8`.
- Both binaries run on one Linux GitHub Actions machine, one CPU thread, shuffled source/version order, **three separate cold-process attempts per source/version**, 15-second per-task timeout; 48 science observations.
- Independent pinned Z3 4.13.4 checks pre ⇒ inv, inv ∧ transition ⇒ inv', inv ⇒ post independently for each returned invariant, accepts only three UNSAT proof obligations. Version timing includes process spawn. Paid comparison also includes the separately measured Z3 verification; binary download/installation/outer harness and energy/money are **excluded or UNKNOWN**.
- [First technical Actions attempt 37893823942](https://github.com/yoonsj0305/NEUMANN/actions/runs/37893823942) **FAILED before any task execution** due cvc5 1.4.2 version output spelling. Failure and artifact preserved; only version preflight regex was corrected.
- [First evaluable successful Actions 37894008795](https://github.com/yoonsj0305/NEUMANN/actions/runs/37894008795) at exact SHA `aedab2182cb279c4ea9981ef53413bdf56739755`; [raw artifact 11598838398](https://github.com/yoonsj0305/NEUMANN/actions/runs/37894008795/artifacts/11598838398).
- Independent raw-artifact audit: ZIP CRC PASS; 48 unique (solver, source, repeat) rows, exactly eight sources × two binaries × three repetitions; all 42 accepted runs have three UNSAT obligations. Artifact ZIP SHA256 `58aa958977e9cb12104fec019bdeb2b04e69b30109a99d5c37ee41b693637ebf`.

## Actual results

| Historical source | Old 1.1.2 median native | Official 1.4.2 median native | old / new paid original-goal checker included | Verdict |
| --- | ---: | ---: | ---: | --- |
| From2018/bkley.sl | 11.91 ms | 15.13 ms | 0.835× | both verified 3/3 |
| From2018/brett.sl | 100.08 ms | 27.33 ms | 3.352× | both verified 3/3 |
| From2018/cggmp2005...sl | 10.84 ms | 13.51 ms | 0.838× | both verified 3/3 |
| From2018/ex1.sl | 8.12 ms | 11.04 ms | 0.745× | both verified 3/3 |
| From2018/fib_01.sl | 19.03 ms | 11.30 ms | 1.570× | both verified 3/3 |
| XC/1.c.sl | 8819.20 ms | 4253.86 ms | 2.072× | both verified 3/3 |
| XC/10.c.sl | 119.60 ms | 46.84 ms | 2.449× | both verified 3/3 |
| XC/100_conf1.sl | 15,017.97 ms timeout | 15,032.27 ms timeout | N/A | both timed out 3/3 |

**Both** independently certified **7/8** source programs on **all 3 repeats** (21/24 observations). Each had three timeouts on the same remaining source, `XC/100_conf1.sl`. On the 7 matched fully certified tasks, the geometric mean of the old/new cost ratio **including independent Z3 validation** was **1.4568×**. Updated solver faster in 4/7; old solver faster in 3/7. Do not count source-by-repeat as independent tasks.

The earlier cvc5 1.1.2 [native first screen](https://github.com/yoonsj0305/NEUMANN/actions/runs/37892991415) had timed out `XC/1.c.sl` at 15 s; in the controlled paired experiment it certified this same source at ~8.8 seconds in all three repeats. The **eight original-to-translated SyGuS source SHA-256 hashes agree 8/8 across prior and current archived receipts**. We do not assign a specific root cause to this inter-run discrepancy; it proves only that the earlier single timeout is not robust evidence of unsolvability.

## Research decision

`HOLD_LEARNING`. On this external cohort, changing to a substantially newer, published strongest-available-in-this-test native does not create a clear NEUMANN opportunity:
- Version changes can improve speed (XC/1, XC/10, brett), but gains are case-specific and not 10x.
- Only one source is unsolved by **both tested cvc5 versions under the registered 15 s budget**. This is **NOT proof no other native solver can solve it**.
- No NEUMANN structure-generation or learned perspective was tried. No causal headroom, no newly certified neural capability, no Q1–Q7 closure.
- The selected eight files were deliberately chosen for difficulty diversity, not unbiased benchmark sampling. Two cohorts and repeat observations do not turn into eight independent mechanism families.

**Next high-value work:** compare the one remaining source with a genuinely different strong native synthesis/invariant technique under identical source, ability and original-goal proof; inspect whether a valid source-derived sufficient perspective both (a) defeats that strong-native comparator and (b) admits cheap certification. Do not declare a discovered gap just from a 15-second timeout or pay for training.

Original 2026-10-09 first technical, corrected first native, and this separate paired run remain historical immutable artifacts. Do not retroactively relabel previous Q34 PASS, Q5/BP/M106 failures, Decision2 FAIL, any P1 failures or global Q1–Q7 OPEN.
