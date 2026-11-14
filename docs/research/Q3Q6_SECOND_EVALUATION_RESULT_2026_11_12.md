# NEUMANN 1 | SECOND evaluation: result
2026-11-12 | Label: **SECOND** (targets opened by the INCOMPLETE FIRST run; not FIRST evidence) | Global Q1–Q7 OPEN

Pre-registration: [Q3Q6_SECOND_AND_FRESH_PREREG_2026_11_11.md](Q3Q6_SECOND_AND_FRESH_PREREG_2026_11_11.md) (freeze `08c1536d…f639`,
13:58:12 UTC, committed and pushed before launch). Data: `docs/experiments/results/invention_second_rows.jsonl`
(2 436 rows), `invention_second_result.json`, `invention_second_checklist.json`. Verdicts are the unchanged
`invention_first.summarize` output. Nothing in the rules, data, core or budgets changed after the freeze.

## 1. Run accounting

* 2 436 / 2 436 jobs recorded, all `ok`: 0 error, 0 timeout, 0 died, 0 unresolved. Verdicts are therefore the
  registered rules with no completion policy applied.
* **Integrity condition: OK.** Rule A solved 25 and A4 solved 34, exactly the FIRST values, so the executor change
  reproduces the frozen executor's outcomes on the real targets.
* Disclosure: a machine restart at 14:09:37 UTC killed the run at 358 saved rows; it was resumed with the identical
  command at 23:06:49 UTC after the owner's go-ahead. The ≤ 4 jobs in flight were unrecorded and run once
  (no recorded key was re-run). Rows are in the registry-given order, one row per key, none duplicated.

## 2. Registered verdicts (as computed)

| Verdict | Result |
|---|---|
| P1 invention (≥ 5 inventions in core and ≥ 3 distinct in C-exclusive solutions) | PASS (8 inventions; f0, f3, f4, f5, f7 appear in exclusive wins; f3, f4, f5 only in dc) |
| P2_rule (Q3 target) | **FAIL** |
| P2_dc (Q6a cross-author, zero-shot) | **FAIL** |
| P2_oeis (Q6b cross-semantic, shared core) | **FAIL** |
| Q3_scoped | **FAIL** |
| P3 iso-capability 4× (rule / dc / oeis) | NOT_SHOWN |
| #745 gate | **FAIL** |
| Global Q1–Q7 | OPEN |

Kept as they are. This is a negative result for this core on these targets.

## 3. Numbers

Solved tasks (hidden tests all must be reproduced); CPU seconds are summed over tasks.

| Family (usable) | A | A4 | B | C | other | C vs A (McNemar p) | C vs A4 (p) | C vs B (p) | C-exclusive |
|---|---|---|---|---|---|---|---|---|---|
| rule (125) | 25 | **34** | 29 | 28 | C_no_inventions 29, C_no_learned_prior 27 | C+9/A+6, 0.61 | C+5/A4+11, 0.21 | C+3/B+4, 1.0 | 1 |
| dc (199) | 115 | **129** | 95 | 119 | — | C+18/A+14, 0.60 | C+11/A4+21, 0.11 | C+24/B+0, <1e-6 | 8 |
| oeis (178) | 4 | 6 | 4 | 5 | D (specialist) **25** | C+2/A+1, 1.0 | C+2/A4+3, 1.0 | C+1/B+0, 1.0 | 0 |

CPU seconds (rule / dc / oeis):

| Arm | rule | dc | oeis |
|---|---|---|---|
| A | 251 | 218 | 331 |
| A4 | 1 059 | 789 | 946 |
| B | 1 773 | 5 848 | 400 |
| C | 1 721 | 7 106 | 298 |

## 4. What this shows (and does not)

1. **No equal-budget gain.** On rule, C solved 28 against A's 25 (p = 0.61), and 28 against B's 29. On dc, C 119 vs A 115 (p = 0.60). On
   oeis, C 5 vs A 4. None of these is distinguishable from noise, and C is not the best arm in any family.
2. **A 4×-candidate classical search beat C on rule (34 vs 28) and dc (129 vs 119).** Not significant at 0.05
   (p = 0.21, 0.11) but in the direction against the architecture. P3 is NOT_SHOWN.
3. **C used more compute, not less.** In CPU, C cost 1 721 s on rule (A4 1 059 s; A 251 s) and 7 106 s on dc
   (A4 789 s). At equal candidate counts the memory arms do roughly 10× the work per candidate (rule: 16.2e9 work
   units for C vs 1.4e9 for A), so under this accounting a candidate-matched baseline is far cheaper. The
   hypothesised saving ("most computation is not needed") is not observed in these arms. The one place C is
   cheaper per solved task is oeis (298 s vs A4 946 s), but it solves 5 tasks.
4. **Search-cost reduction on tasks both solve exists but is small relative to overhead:** rule 329 k vs 608 k
   candidates on 19 shared tasks; dc 1.37 M vs 1.88 M candidates on 101; oeis 197 vs 177 905 candidates on only 3.
   Candidates are not CPU: the above point 3 shows the overhead exceeds the candidate savings in CPU terms.
5. **The memory arm is not a free improvement.** B vs A on rule: B_only 9, A_only 5; on dc B_only 5, A_only 25
   (B solves 95 vs A 115). Fitting to memory programs causes wrong replays and wrong generalisations
   (rule: B fit 33, solved 29; dc: fit 105, solved 95).
6. **Invention attribution is thin.** The single rule-exclusive win (`rule/c066`, `(tail (f7 (f0 $0 nil) $0))`)
   is not solved by `C_no_inventions`, so it is attributable to inventions (n = 1). `C_no_inventions` solves 29 on
   rule, one more than C: inventions have no net effect on the rule family. dc has 8 exclusive wins, seven of
   them using at least one invention (f0, f3, f4, f5, f7); dc has no `C_no_inventions` arm, so attribution there is untested. P1 PASS counts
   distinct inventions in exclusive wins across families; it is true as registered but does not establish a
   benefit.
7. **Q6b (transfer to integer sequences)**: C solves 5/178 sequences, A4 6, D (finite differences +
   Berlekamp–Massey) 25. The classical specialist dominates by 5×; the shared core gives nothing. This is the
   expected behaviour for a core that learned lists and recurrences with a 14-term view, but it is a failure by the
   registered rule.
8. All tasks have the full hidden-test count (rule 24, dc 7, oeis 6), so the 0/1-hidden-test sensitivity is moot.

Against the owner's ultimate question ("why does the baseline need this much compute and NEUMANN does not?"), the
SECOND evidence does **not** support the premise for this core: on these three families, the core did not discover
a structure that makes most of the computation unnecessary. What is supported: the executor fix is exact; the
infrastructure now yields complete, unforgeable results; and a 4×-candidate baseline is a strong, cheap rival.

## 5. Limits

* SECOND, not FIRST: the targets were opened by FIRST (two aggregate outcomes seen, A 25, A4 34). It does not
  qualify as an independent confirmation; it does qualify as a complete measurement of the frozen design.
* One core, one substrate, one seed. A FAIL says this core's gains were not detected at these budgets; it is not
  a proof that no such core exists, and it says nothing about Q7 (frontier) or Q5 (full accounting).
* `compute_comparison_list_functions_second.json` (post-hoc, not pre-registered) puts C's measured CPU at
  ≈ 138 G primitive operations per task (upper bound) vs PaLM-535b's ≥ 8.8e13 FLOPs per query; per-query
  inference cost of the LMs is 1–640× C's per-task search cost, yet PaLM-535b is perfect on 25 tasks, C solves 28. The LM training cost (≥ 3e8× C's SOURCE
  investment) is listed in the JSON. SOURCE investment for C is ≤ 7 580 CPU s. This
  comparison uses different protocols (≤ 5 demonstrations vs 8; per-query vs per-task) and is not a verdict.

## 6. Next

The FRESH plan (first-exposure OEIS pool; F1 frozen core, F2 lists-only core) remains draft. Given §4, its
expected outcome is a further negative on F1/F2 unless the lists-only core behaves differently; it should be run
exactly as registered if the owner still wants it, with the same single-attempt policy. No architecture changes
have been made, and none are implied by this result.
