# NEUMANN 1 | G0 C2 actual professional SMTInterpol baseline and independent Craig audit — 2026-10-27

**Scientific scope**: POST-FIRST professional *classical* replay on prior opened same-author SMTInterpol test corpus. **Q1–Q7 GLOBAL OPEN; G1 HOLD; G2 NOT RUN.** This report adds **no** ownweight neural discovery, no cross-author blind transfer, no full frontier/cost parity. Do not retroactively alter earlier V2 first **0/7**.

## Actual proof-of-execution and chronology

- Official SMTInterpol 2.5-1453-gedae1f37 JAR fetched in a public GitHub Actions Linux runner, binary SHA256 pinned and verified **8d42e87614fcdbe6fce5233b91f20563dfd9a854d999127d70cfb42853e091c7**; source official Freiburg download https://ultimate.informatik.uni-freiburg.de/smtinterpol/download.html
- Original 12 file paths and exact source commit `ultimate-pa/smtinterpol@f65e98f05203f1d2801bf5bd121766bfcd6451ec` retained from frozen prior 2026-10-27 researcher records. No new first-blind corpus is claimed.
- First professional GitHub Actions job **#40442249880**, commit `4524f0851dc9daee66357fb5daf355fb23942971`: official binary fetch/hash and simple smoke interpolate succeeded; **12/12 external original exits 1** due executor limitations, no result promoted. Immutable artifact **#12706991096** and ZIP SHA256 `955921990d86433c2ccbd89b72670ebf0e4b75cddf6652091195d6903d971be6`.
- POST-FIRST environment correction: Java reserves virtual address space far exceeding its live RSS; replaced inappropriate `RLIMIT_AS=800 MiB` check with a process RSS watchdog and Java heap bound. Run [#40442371634](https://github.com/yoonsj0305/NEUMANN/actions/runs/40442371634) from commit `88109458fe29362e5dbc87a8360c08c8c699e5f1`: all **12/12 source files** pinned and executed with **exit code 0**, `unsat` response; individual wall times **0.169936–0.326620 seconds**. These are per-process execution elapsed times, not an all-in cost claim.
- Artifact **[#12707495738](https://github.com/yoonsj0305/NEUMANN/actions/runs/40442371634/artifacts/12707495738)**, ZIP SHA256 `92cd5074742bb2615c56c61b98966336d806bb1f1be1ea94c5ad2ac3d532a00f`. Contains 12 full raw stdout/stderr, hashes, control and Java metadata. A separately named JSON output was accidentally omitted from the artifact due upload path mismatch; it is in the job log. Preserve this provenance defect; don't say the artifact includes a machine JSON.
- RSS samples printed **0 KiB** because watchdog regular-expression escaping was defective: **INVALID TELEMETRY / UNKNOWN**, not actual measured zero resident memory. Java max heap 512MiB and conservative caps are a configuration, **not** whole-system measured memory.

## Independently validated goal subset

Of these twelve, the prior *binary original eligible cohort* was seven: `ufliatest001.smt2`, `ufliatest002.smt2`, `ufliatest003.smt2`, `ufliatest004.smt2`, `uflratest001.smt2`, `uflratest002.smt2`, `uflratest003.smt2`.

- **Professional C2 SMTInterpol** emitted `unsat` and one concrete Craig interpolant for each seven. Earlier fixed V2 first generated checked witnesses **0/7**. That first frozen negative result remains as-is.
- Copy of the 7 **already opened** original scripts' named A/B constraint expressions was reconstructed explicitly. Independently, our Python `ctypes` checker used local **Z3 4.13.3.0** in fresh contexts to query *both* Craig conditions `A AND NOT I = UNSAT` and `I AND B = UNSAT`. Checked that candidate declared symbols are contained in the shared original vocabulary (let-bound locals excluded). Outcome **14/14 UNSAT obligations**, **7/7 declared-shared checks**, **7/7 limited Craig candidate checks PASS**.
- IMPORTANT: this is a syntactic declaration-symbol check and independent solver verdict, *not* a verified proof object, independent proof kernel, exhaustive general parser or blind evaluation. Original A/B were transcribed from already opened source records; erroneous transcription remains a common-mode risk. The downloadable standalone checker includes the exact reconstructed assertions so a reviewer can compare line-for-line to pinned source.
- The source metadata `Desired Interpolant` on `ufliatest002` and `uflratest002` was previously falsified: it lacks necessary `+5` in `f(x1+5)`. SMTInterpol's executable output **correctly includes** that shift, and independent Z3 Craig checks verify the emitted candidate in these two cases. This is *the existing specialist solver's capability*, not a NEUMANN invented fix.

## Decision and remaining missing evidence

- For this *seven-task historical cohort*, G0 specialist classical headroom **does not exist at the original goal level under tested ~0.2–0.3s per-file solver path**: the strong specialist already emits separately-checked full candidates. This is scoped evidence, not a universal headroom impossibility theorem.
- **NO G1 admission** on the seven; prohibit re-training a narrow V2 or evaluating optimizer speed as a substitute for missing task capability. Don't relabel first-blind V2 0/7 as professional first-blind results.
- Whole-system energy, peak resident memory, acquisition and training costs unknown; *10× frontier-level efficiency* unproven.
- Next high-value experiment: **different independent-author, genuinely unopened, original-goal pinned benchmark**, specialist classical C baseline, and independently checked whole-goal outputs. Only if nonduplicated gap survives same-rights classical comparison may an ownweight open-typed REFRAME A/B/D experiment start.

## Preservation

- GitHub CI [actual run #40442371634](https://github.com/yoonsj0305/NEUMANN/actions/runs/40442371634), [raw artifact #12707495738](https://github.com/yoonsj0305/NEUMANN/actions/runs/40442371634/artifacts/12707495738).
- **Standalone post-first verifier bundle**, generated in conversation: `NEUMANN1_G0_POSTFIRST_PROFESSIONAL_20261027.zip`, SHA256 `2f9a3c74a75b536cf06c461400efe940ad646b93d9f1ab031b084f576294039e`, containing 7 independent checks, 12 original raw solver responses, a reproducible Python local Z3 harness and manifest. JSON judgment SHA256 `7be8229d3a6fdf4ef5cc531bc87739fa322db0cbb56e4d23e21aeb281e5881d4`.
- The bundle includes **no third-party original benchmark source file** or JAR.

**Verdict: G0_SPECIALIST_BASELINE_POSTFIRST_SCOPED_PASS_7/7; G1_HOLD; Q1–Q7_GLOBAL_OPEN.**


## Additional post-first telemetry replay — completed, 2026-10-27

Historical measurement runner had missing RSS samples and omitted JSON artifact. A subsequent instrumentation-only edit mistakenly wrote escaped Python newline characters; **GitHub Actions #40442989716 failed at syntax parse** (no original task solved in that attempt). Failure retained, not conflated with research outcome. Following newline repair, [GitHub Actions #40443063729](https://github.com/yoonsj0305/NEUMANN/actions/runs/40443063729), commit `c49259c73f423df1ee1bc7c94add259e9fdf5a14`, **completed all 12** and emitted JSON artifact **[#12707491784](https://github.com/yoonsj0305/NEUMANN/actions/runs/40443063729/artifacts/12707491784)**. All 12 stdout SHA256 identical to earlier successful professional replay. The 7/7 checked Craig conclusion unchanged.

Measured child process samples (12 separate runs; sums do NOT include fetch, harness, independent Z3 verification, storage, network or energy):
- All 12: CPU user **3.232046 s**, system **0.321123 s**, sum per-process wall **1.979776 s**; process wall range **0.107674–0.215692 s**; sampled per-process RSS maxima **51,664–77,900 KiB**.
- Seven binary Craig eligible: CPU user **2.381631 s**, system **0.198167 s**, sum per-process wall **1.334517 s**, sampled per-process RSS maxima **62,772–77,900 KiB**.
- Child CPU can exceed wall due JVM parallelism. RSS is polling-based and can miss transient peaks, so it is a lower bound on actual peak. There is **no measured full-system 10x improvement**, and there is no additional learned capacity.

Raw JSON SHA256 `ac0b19493ae4949e25dbe3d9fc88f03effe1289588219fa52328cdb4defd6f07`. Updated standalone receipt bundle `NEUMANN1_G0_POSTFIRST_PROFESSIONAL_MEASURED_20261027.zip` SHA256 `f4428802083c907ff9f2b37ffc753344082ff2b0bfc073648c2082b56244aeaa`, original 12 stdout/stderr, seven Z3 checks and full matched telemetry JSON; rechecked offline 7/7.

Scientific status unchanged: `G0_POSTFIRST_PROFESSIONAL_7/7_SCOPED_PASS`; `G1_HOLD`; `Q1_Q7_OPEN`.
