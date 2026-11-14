# Independent invention audit — frozen before execution

Base: `0d1baec723f249a62a901d100af6e941234a43ac` (Claude's development branch).
This branch changes no discovery policy, solver, historical result, or gate.
Only already opened iteration-2 originals are eligible. No OEIS, SECOND/THIRD
reserve or new capability study is opened.

## Decision and hypothesis

H: the recorded iteration-2 effect survives a separate implementation of
original-task execution and strict paired-cohort validation. The useful causal
chain is SOURCE-derived operation → inverse → goal decomposition → a submitted
substrate program. This audit cannot establish unrestricted autonomous invention.

The single acceptance criterion is: **all** coverage, independent replay and
negative-control checks pass. Any discrepancy is retained; no replacement run
or changed threshold. The existing scientific iteration-2 verdict remains FAIL.

## Fixed work

1. Check all 972 recorded rows: exactly S/V0/V on 125 rule and 199 usable dc
   IDs, no duplicate/missing/extra IDs, nonfinite/negative CPU, invalid booleans,
   or solved-without-fit. Recompute J1–J3 with an independent exact binomial
   calculation and unrounded CPU sums. Historical CPU is retained, not remeasured.
2. Independently parse and interpret every submitted program against every
   original TRAIN and TEST example. The interpreter must not import NEUMANN's
   compiler, executor, task loaders, or scoring functions. Independently parse
   the pinned original author files. Pin paths and git blobs in a manifest.
3. Attack the legacy report using two artificial families with equal row counts
   but disjoint IDs between arms; show whether it admits a false paired PASS.
   The independent checker must reject this and duplicates, absent arms,
   unregistered IDs, invalid CPU and incorrect fit flags. These are validator
   fixtures, never capability data.
4. Reproduce the **12 already published V-only IDs** (postselected, development
   reproduction only), with S/V0/V at 6 process CPU seconds each and the exact
   frozen inverses/inventions. Discovery workers receive TRAIN and an empty
   TEST only. Save and hash all 36 programs/predictions before reproduction
   grading. Original gold is already known to the audit parent from historical
   replay; it is never supplied to the discovery child. This is process-level
   separation on opened data, not a fresh blinded capability evaluation.
   Report every failure/timeout and compare actual CPU,
   candidate counts and substrate-work counts separately. The new run neither
   replaces historical discordances nor supplies an unbiased effect estimate.

Budget: ≤36 synthesis jobs, each 6 CPU seconds, ≤2 workers, hard 30-second wall
timeout per job. Do not retry failed jobs. Original replay is finite and cheap.
No energy, monetary-cost, frontier or tenfold-speed claim is permitted.

## Scope across Q1–Q7

Q1: validate causal elimination mechanism and measure costs on the reproduction.
Q2: original correctness checked by a separately implemented interpreter.
Q3: attribution to previously SOURCE-invented operations; policy learning remains
unproven. Q4/Q5: report missing learning/inverse-derivation investments explicitly;
do not infer end-to-end advantage. Q6: opened development cohorts, no new-family
claim. Q7: no matched frontier run, remains untested.

The recommended architecture decision depends on this audit: a structure earns
reuse only after independent original-task verification; a positive raw count
must never bypass identity, coverage or complete-cost checks. Classical fallback
remains available, and an invalid/incomplete record yields INVALID/INCOMPLETE.
