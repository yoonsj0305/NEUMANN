# NEUMANN 1 | Pre-registration: SECOND evaluation (opened targets) and FRESH evaluation (never-opened pool)
2026-11-11 | DRAFT until the freeze commits named in §6; binding from then on | Global Q1–Q7 OPEN

Authority: [Frozen North Star](frozen_north_star.md), issue #745, the FIRST pre-registration
([Q3Q6_INVENTION_CORE_PREREG_2026_11_11.md](Q3Q6_INVENTION_CORE_PREREG_2026_11_11.md)) and the owner's instructions
of 2026-11-11 (abort FIRST as INCOMPLETE, fix the executor exactly, disclose any re-run as second, freeze data and
policy before a new independent evaluation).

## 1. What happened to FIRST, and what is and is not changed

FIRST was terminated **INCOMPLETE** (receipts: `docs/experiments/results/invention_first_arm_log_receipts.md`).
Observed: rule A 25/125, rule A4 34/125. Nothing else: no B, C, ablation, dc or oeis outcome exists.

Changed since FIRST: the **executor** only (call-by-need abstraction arguments, faithful vector reuse, a work
meter) and the run infrastructure (checkpoint runner). Code-level argument and differential evidence:
[Q3Q6_EXECUTOR_EXACTNESS_2026_11_11.md](Q3Q6_EXECUTOR_EXACTNESS_2026_11_11.md).

Not changed: the substrate, search, compression, prior, memory retrieval, the frozen core
(`invention_core_frozen.json`, trained and hashed before FIRST), the registry, the splits, the arms, the budgets,
and every PASS rule. No hyper-parameter was touched after FIRST opened its targets.

## 2. SECOND evaluation (plan `second`)

**Disclosure.** This is a second evaluation on targets whose bytes the INCOMPLETE FIRST run already opened. The
developer has seen two aggregate outcomes (rule A 25, A4 34) and the fact that rule B was slow. It is therefore
**not FIRST evidence** and will be labelled SECOND wherever it is cited.

* Targets, frozen core, arms (A, A4, B, C; C_no_inventions and C_no_learned_prior on rule; D on oeis), budgets
  (200 000 / 800 000 candidates) and decision rules P1, P2_F, Q3_scoped, Q6a, Q6b, #745 gate, P3: exactly as in the
  FIRST pre-registration §4–§6. Verdicts are computed by the unchanged `invention_first.summarize`.
* **Integrity condition.** The executor is claimed exact, so rule A must solve exactly **25** and A4 exactly
  **34**. Otherwise every SECOND verdict is **VOID**.
* Interpretation limits fixed in the static audit
  ([Q3Q6_INVENTION_CORE_STATIC_AUDIT_2026_11_11.md](Q3Q6_INVENTION_CORE_STATIC_AUDIT_2026_11_11.md) §1, §5) apply
  and are reported next to the verdicts, never instead of them:
  * P3 may be called "at lower or equal compute" only if CPU(C) ≤ CPU(A4);
  * an exclusive win counts as invention-attributable only if `C_no_inventions` fails it (rule);
  * P2_dc is also reported without tasks having 0 or 1 hidden test;
  * invention use is reported per family;
  * Q6b is a shared-core test, not a transfer test.

## 3. FRESH evaluation (plan `fresh`): first exposure

**Pool.** The 499 OEIS A000 sequences that the FIRST registry set aside as `oeis_reserved_unopened` (salted
SHA-256 order, positions 500–998). Their names and git blob SHA-1s were registered before FIRST; no byte was
fetched (0 of 499 present on disk at registration of
`docs/experiments/second_eval_candidate_registry.json`, sha256 `aa0f7299…d9ae`). The 1 000 A001 files in the same
registry stay unopened for later work.

Examples as in FIRST: index n from %O; the search sees 14 terms, the next 6 are hidden. Sequences with fewer than
20 terms are unsupported and count as failures for every arm.

**Arms** (budgets as FIRST):

| Arm | Definition |
|---|---|
| A, A4 | substrate, uniform prior, 200 k / 800 k candidates |
| B, C | the FIRST frozen core (memory; memory + inventions + learned prior). It learned from rule SOURCE and OEIS SOURCE |
| D | classical specialist: finite differences + Berlekamp–Massey |
| B_L, C_L | a core trained on **lists only**: the same code and recipe (3 rounds, 600 k candidates per task) on the 125 rule SOURCE tasks, no integer-sequence task. `train_lists` reads only `rule_source`; the result is hashed in the freeze file before the pool is opened |

**Hypotheses and rules** (the FIRST P2 rule, unchanged in form):

| ID | Claim | PASS rule |
|---|---|---|
| F1 (Q3, sequences, first exposure) | the frozen core's experience gives new capability on never-seen sequences | solved(C) > solved(A) and > solved(B); exact two-sided McNemar p < 0.05 for C vs A and C vs B; ≥ 5 tasks solved by C and by none of A, A4, B, D |
| F2 (Q6, cross-semantic zero-shot transfer) | what was learned from list functions alone transfers to integer sequences | the same rule with C_L for C and B_L for B (rivals A, A4, B_L, D) |

Reported, not gating: inventions used in exclusive wins; TRAIN-fit precision; candidates, work and CPU per arm;
C vs A4.

**What a PASS would and would not mean.**
* F1 PASS = first-exposure evidence, on one semantic family and one author community, that the core's experience
  yields capability that equal-budget search, 4×-candidate search, a memory baseline and a classical specialist
  lack.
* F2 PASS = evidence of transfer across semantics. Stated in advance: F2 is expected to be hard. A lists-only core
  has no stored I→I program, so B_L ≈ A, and any gain must come through the learned prior and inventions.
* Neither would establish invention of new representations, frontier capability (Q7), complete resource
  accounting (Q5) or global Q3/Q6.
* A FAIL is kept as it is.

**Exposure, disclosed.**
* Earlier branches used a handful of OEIS recurrences (#545–#557).
* The reserve comes from the same A000 block as the OEIS SOURCE the frozen core learned from (in-distribution for
  F1).
* The substrate and hyper-parameters were written by an LLM assistant that may have seen OEIS in pretraining:
  a design-contamination channel, not an answer channel.
* Nothing was tuned between the FIRST freeze and this pre-registration.

## 4. Policy common to both plans

* **Budget policy P0**: deterministic candidate counts, as in FIRST. No work cap and no fuel.
  `wall_cap_s` (value in the freeze file) is an operational safety cap only.
* **Unresolved rows** (error / timeout / died / not run) are never counted as failures automatically. Every rule is
  evaluated under two completions:
  * ADVERSE: an unresolved C-type row is unsolved, an unresolved rival row is solved;
  * FAVOURABLE: the reverse.

  **PASS** iff the rule passes under ADVERSE; **FAIL** iff it fails under FAVOURABLE; otherwise **INCOMPLETE**.
  With no unresolved row this is exactly the registered rule.
* **Single attempt**: a recorded key is never re-run.
* Per-task rows (status, fit, solved, via, program, candidates, work, CPU seconds, peak RSS, number of hidden
  tests) are appended to `docs/experiments/results/invention_<plan>_rows.jsonl` and committed while the run
  proceeds. A loss of the container cannot lose finished rows.
* No PASS rule is modified after any outcome is seen. Every outcome is kept.

## 5. Gates before either freeze

1. The differential test of the executor on all development data has completed and is reported in full (mismatches
   and timeouts by executor). Any mismatch between the frozen and the new executor blocks both plans.
2. A timing sample of every arm on SOURCE tasks at the real budgets, with the checkpoint runner, is reported
   (per-task CPU and work percentiles), and `wall_cap_s` is set at least 10× above the maximum observed.

## 6. Freeze records (filled at freeze time)

| Plan | Freeze file | freeze_sha256 | Commit |
|---|---|---|---|
| second | `docs/experiments/invention_second_freeze.json` | (pending) | (pending) |
| fresh | `docs/experiments/invention_fresh_freeze.json` | (pending) | (pending) |
