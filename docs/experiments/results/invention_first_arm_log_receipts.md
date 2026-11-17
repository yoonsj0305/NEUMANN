# Q3/Q6 invention-core FIRST: arm-level log receipts (INCOMPLETE until the result JSON exists)

## FINAL STATUS: FIRST evaluation INCOMPLETE (terminated 2026-11-11 11:53:50 UTC on the owner's instruction)

* Terminated by SIGTERM to process group 4138 after the owner approved the abort recommended in
  [the operational diagnosis](../../research/Q3Q6_INVENTION_FIRST_OPERATIONAL_DIAGNOSIS_2026_11_11.md). No
  evaluation process remained (verified). `invention_first_result.json` was **never written**.
* **Observed results (aggregate log lines, both runs agree):** rule A **25 / 125**, rule A4 **34 / 125**.
* **rule B: no result.** "124 / 125" is the number of tasks the workers had *returned*, inferred from pipe
  syscall counters (2 reads + 1 write per task in CPython 3.13 `multiprocessing`). It is **not** a solved count.
  B's solved count is unknown; the last task had run ≥ 1 h 45 min (worker 4152, 03:29:48 CPU) when stopped.
* Every other arm and every verdict (P1, P2_rule, P2_dc, P2_oeis, P3, Q3_scoped, Q6a, Q6b, #745 gate) is
  **INCOMPLETE**. No PASS and no FAIL is declared. The pre-registered rules stay unchanged.
* Preserved verbatim in `invention_first_incomplete/`: `eval_run2.log` (sha256 `b26d0334…df80`),
  `eval_run1_killed.log` (`baa4a5d6…175d`) and `final_state_2026_11_11T1153Z.txt` (process table and
  `/proc` counters 8 s before termination).

What this file is: verbatim copies of the lines the frozen harness prints to stdout (`eval.log`) when one arm
of one family finishes, committed as soon as each line appears so that they survive a loss of the container.

What this file is NOT: it is not the result. It holds **arm-level aggregate counts only** (solved / tasks and the
arm's wall seconds, as printed by `research/q3/invention_first.py`). It contains no per-task rows, no TRAIN-fit
counts, no McNemar test, no exclusivity and no verdict. Those exist only in
`docs/experiments/results/invention_first_result.json`, which the harness writes once, after every family and arm.
Until that file exists, **every verdict (P1, P2_rule, P2_dc, P2_oeis, Q3_scoped, Q6a, Q6b, #745 gate) is
INCOMPLETE**, whatever the counts below suggest. Nothing here may be used to declare a PASS.

Provenance: run 2 launched 2026-11-11 08:21:44 UTC (detached, PID 4138, 4 workers), command
`python research/q3/invention_first.py evaluate <bigbench> <ec> <oeis>`, frozen code as in
`docs/experiments/results/invention_core_frozen.json`. Run 1 (launched 06:21:07) was killed by the tool time limit
after two arms; its lines are kept below for the record. The source log is never edited; each receipt records the
log's SHA-256 at copy time.

## Run 2 (the evaluation of record)

| # | Family | Arm | Printed line (verbatim) | Log mtime (UTC) | Copied (UTC) | eval.log SHA-256 at copy |
|---|---|---|---|---|---|---|
| 1 | rule | A | `rule A solved 25 / 125 wall 70.4` | ≤ 08:28:08 | 10:45:31 | `b26d0334…df80` (2 lines) |
| 2 | rule | A4 | `rule A4 solved 34 / 125 wall 312.2` | 08:28:08 | 10:45:31 | `b26d0334…df80` (2 lines) |
| 3 | rule | B | INCOMPLETE (terminated 11:53:50 before printing; no line printed; ~124/125 tasks finished, inferred from pipe counters, count unknown; see the operational diagnosis) | | | |
| 4 | rule | C | INCOMPLETE (not started) | | | |
| 5 | rule | C_no_inventions | INCOMPLETE (not started) | | | |
| 6 | rule | C_no_learned_prior | INCOMPLETE (not started) | | | |
| 7 | dc | A | INCOMPLETE (not started) | | | |
| 8 | dc | A4 | INCOMPLETE (not started) | | | |
| 9 | dc | B | INCOMPLETE (not started) | | | |
| 10 | dc | C | INCOMPLETE (not started) | | | |
| 11 | oeis | A | INCOMPLETE (not started) | | | |
| 12 | oeis | A4 | INCOMPLETE (not started) | | | |
| 13 | oeis | B | INCOMPLETE (not started) | | | |
| 14 | oeis | C | INCOMPLETE (not started) | | | |
| 15 | oeis | D (specialist, no log line) | INCOMPLETE (computed in-process, appears only in the result JSON) | | | |
| — | all | result JSON + verdicts | INCOMPLETE | | | |

Arm start time = the previous arm's log time (arms run strictly in the order above; `pool.map` returns only when all
tasks of an arm are done). `wall` is the arm's wall-clock seconds with 4 workers; budgets are deterministic
candidate counts, so wall time never enters a decision.

## Run 1 (killed, not of record)

`eval_killed_run1.log`, SHA-256 `baa4a5d6…175d`, mtime 06:29:01 UTC:

```
rule A solved 25 / 125 wall 63.1
rule A4 solved 34 / 125 wall 281.0
```

Same solved counts as run 2 (deterministic budgets); wall differs by machine load only.
