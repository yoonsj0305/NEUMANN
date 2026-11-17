# NEUMANN 1 | THIRD evaluation: result (specification-space core on opened targets)
2026-11-12 | Label: **THIRD** (targets opened by FIRST/SECOND; not first-exposure evidence) | SECOND verdicts: FAIL, unchanged | Global Q1–Q7 OPEN

Pre-registration and design:
[Q3Q6_SPEC_CORE_DESIGN_AND_THIRD_PREREG_2026_11_12.md](Q3Q6_SPEC_CORE_DESIGN_AND_THIRD_PREREG_2026_11_12.md)
(freeze `cab062fc…cad7`, 05:27:37 UTC, committed and pushed before launch as `e7a4fab`). Data:
`docs/experiments/results/spec_third_rows.jsonl` (2 332 rows), `spec_third_result.json`. Verdicts are the output of
the frozen `research/q3/spec_eval.py`. Nothing was changed after the freeze.

## 1. Run accounting

* 05:28–06:24 UTC, one uninterrupted run. 2 332 / 2 332 jobs recorded, all `ok`; 0 error, 0 timeout, 0 died,
  0 unresolved. The verdicts are the registered rules with no completion policy applied.
* Cross-check against SECOND: every task the frozen SECOND arm A4 (800 000 candidates) solved is also solved by
  A@4 here (0 exceptions in all three families).
* Largest CPU used by any job: 6.16 s for the 6 s arms, 24.8 s for A@4.

## 2. Registered verdicts (as computed)

| Verdict | Result |
|---|---|
| V_rule (held-out half of the list-function benchmark) | **PASS** |
| V_dc (DreamCoder list tasks, different authors, never used in development) | **PASS** |
| V_oeis (integer sequences) | **FAIL** (predicted in the pre-registration; not part of the gate) |
| THIRD gate = V_rule and V_dc | **PASS** |
| SECOND verdicts | unchanged (FAIL) |
| Global Q1–Q7 | OPEN |

## 3. Numbers

Solved tasks (every hidden test must be reproduced). Cap 6 CPU s per task; A@4 has 24 s.

| Family (usable) | S | A (equal CPU) | A@4 (4× CPU) | S_no_state | S_no_inverse | D |
|---|---|---|---|---|---|---|
| rule (125) | **62** | 33 | 35 | 45 | 51 | — |
| dc (199) | **151** | 125 | 132 | 149 | 141 | — |
| oeis (178) | 13 | 6 | 7 | — | — | **25** |

| Family | S vs A (S only / A only, exact McNemar p) | S vs A@4 | Solved by S and no rival | Total CPU s: S / A / A@4 |
|---|---|---|---|---|
| rule | 29 / 0, p = 3.7e-09 | 27 / 0, p = 1.5e-08 | 27 | 419 / 587 / 2 229 |
| dc | 27 / 1, p = 2.2e-07 | 26 / 7, p = 0.0013 | 26 | 294 / 439 / 1 507 |
| oeis | 7 / 0, p = 0.016 | 6 / 0, p = 0.031 | 1 (rivals include D; needs ≥ 5) | 958 / 1 017 / 4 032 |

Component ablations (S only / ablation only, p, registered verdict):

| Family | Traversal state removed | Derived inverse operators removed |
|---|---|---|
| rule | 17 / 0, p = 1.5e-05, SHOWN | 11 / 0, p = 9.8e-04, SHOWN |
| dc | 2 / 0, p = 0.5, **NOT_SHOWN** | 11 / 1, p = 0.0063, SHOWN |

How S solved: rule: zfilter 24, chain 22, zmap 11, search 5. dc: zmap 59, zfilter 40, search 28, chain 24.
oeis: rec 11, inverse 2. TRAIN fits that generalise: rule 62 / 62, dc 151 / 163, oeis 13 / 23.

Reference only (the frozen SECOND arms on the same tasks): rule A 25, A4 34, B 29, C 28; dc A 115, A4 129, B 95,
C 119. S against the old invention core C: rule 35 / 1, dc 44 / 12.

## 4. Where the computation went

Tasks S solved that the baseline did not solve with four times the CPU:

| Family | Tasks | S CPU s (total; median) | A@4 CPU s on the same tasks | Candidates, median: S / A@4 |
|---|---|---|---|---|
| rule | 27 | 23.8; 0.058 | 649 (no task solved) | 4 893 / 2 232 576 |
| dc | 26 | 38.1; 0.38 | 625 (no task solved) | 52 098 / 2 052 608 |

* Measured: when it fails, the forward enumerator has completed cost level 7 after 6 CPU s (about 0.5 M
  candidates) and level 8 after 24 s (about 2.2 M) in both families.
* The chain solutions among these tasks have 10 to 55 substrate nodes (rule) and 12 to 40 (dc). They lie 2 to 47
  cost levels beyond what 24 s of enumeration completes; each level costs 5–7× more (extrapolation, not a
  measurement). S reaches them because every sub-goal it searches has a few nodes.
* On tasks both arms solve, S used 16.3 s against A's 33.0 s (rule, 33 tasks) and 34.6 s against 54.8 s
  (dc, 124 tasks).

This is the measured answer, at this scope, to "why does the baseline need this much computation": it tests whole
programs against whole examples, so the cost is exponential in the size of the whole program. S reads from the
examples which positions are kept, where each output element comes from and how a term follows from earlier
ones, and searches only the pieces.

## 5. What this does and does not show

1. **Shown (THIRD scope).** On a held-out half of the benchmark used in development and on a list family by
   other authors that development never touched, S solves significantly more tasks than classical enumeration
   with equal CPU and with 4× CPU, while using less CPU in total.
2. **Component attribution.** On rule both generated components are necessary. On dc the derived inverse
   operators are necessary and the traversal state is **not shown** necessary (149 without it, 151 with it): the
   two components largely cover the same dc tasks. Removing the inverses costs 10 tasks, removing the state 2.
3. **Losses.** On dc, A@4 solves 7 tasks that S does not (6 where S found nothing in its smaller forward share,
   1 where a backward step fitted TRAIN and failed the hidden tests); A at equal CPU solves 1 of them.
4. **Sequences.** S 13 against the classical specialist's 25; S solves 3 sequences D does not, D solves 15 that
   S does not. V_oeis fails, as predicted. The mechanism is not a sequence solver.
5. **Not first exposure.** These targets were opened by FIRST and SECOND. The developer knew the SECOND aggregates
   and nine program strings (listed in the pre-registration). rule TARGET is in-distribution with the SOURCE
   tasks S was tuned on. dc is the cleaner test.
6. **Time-dependent margins.** CPU caps make outcomes near a stage boundary depend on timing: one S solution
   on rule came after 80 % of the cap (A: 2, on dc A: 1). The margins in §3 are 26–29 tasks.
7. **Scope.** List transformations whose structure is positional, element-wise or a short recurrence. Outputs
   that are neither aligned with nor a subsequence of the input, aggregates inside the step and whole-list
   conditionals are not covered. Nothing here addresses Q5 (complete cost against strong Direct) or Q7
   (frontier tasks).
8. **Prior art.** Inverse semantics, deductive decomposition and counterexample-guided synthesis are known. The
   result is a measurement of this design against enumeration, not a claim of a new principle.
9. **SECOND is not affected.** The macro-invention core failed its gates and that record stands. S is a
   different mechanism; it has no memory and learns nothing across tasks, so it does not answer the #745
   A/B/C contract about cross-task invention.

## 6. FRESH and the next verification

FRESH (499 OEIS A000) and the 1 000 A001 files remain unopened. They are integer sequences; development and THIRD
both show the specialist D ahead of S there, so a FRESH run of S would be expected to fail its exclusive-win
criterion. A first-exposure test of this mechanism needs a list-transformation family that has never been
fetched, registered by blob hash before any byte is read, with the same arms, cap and rule. Neither step is taken
without the owner's decision.
