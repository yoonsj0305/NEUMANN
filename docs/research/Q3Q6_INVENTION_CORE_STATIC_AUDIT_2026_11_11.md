# NEUMANN 1 | Static validity audit of the Q3/Q6 invention-core FIRST evaluation
2026-11-11 | Written while the frozen TARGET run is in progress, BEFORE any arm C / B / ablation / dc / oeis outcome exists | Global Q1–Q7 OPEN

Purpose: decide in advance what a result will and will not mean. No frozen code, budget, order, core or PASS rule
is changed; nothing here re-judges a verdict. Inputs: the pre-registration
([Q3Q6_INVENTION_CORE_PREREG_2026_11_11.md](Q3Q6_INVENTION_CORE_PREREG_2026_11_11.md)), `research/q3/invention_first.py`,
`neumann1/invention_core.py`, `research/q3/sequence_specialist.py`, `docs/experiments/results/invention_core_frozen.json`,
git history, and SOURCE files only. TARGET facts known at writing time: the two harness log lines rule A 25/125 and
rule A4 34/125. Classification: **BLOCKER** = can invalidate the interpretation of a result; **LIMITATION** = result
valid, claim narrower; **NOTE** = fix in the next experiment. Each item is labelled with the question it bears on.

## 0. Verified facts (passed)

| Check | Evidence | Status |
|---|---|---|
| Pre-registration before SOURCE | prereg commit `f235c8a` pushed 03:10:38 UTC; `train` launched 03:12:48 | OK |
| No code change after pre-registration | SHA-256 of the 3 pinned files at `f235c8a` equals `code_sha256` in the frozen core | OK |
| Freeze before TARGET | freeze commit `0954ed5` created 06:21:06, evaluate launched 06:21:07 (see L1 for the push timing) | OK (local) |
| Tamper checks at run time | `evaluate` refuses on registry hash, frozen-core self-hash, code SHA or any target blob SHA-1 mismatch (l.200–205, 274–287) | OK |
| SOURCE/TARGET disjoint | rule: salted SHA-256 order, halves (l.94–102); oeis: 250/250/499 disjoint slices; dc never in SOURCE (`train` reads only `rule_source`, `oeis_source`, l.212–215) | OK |
| Hidden tests never reach search or learning | `solve()` passes only `task["train"]` to `Search`, `data_constants` and `memory_prims`; `test` is used only after the single program is fixed (core l.1086–1106); probe envs use TRAIN pairs only (l.564–594) | OK |
| No learning across TARGET tasks | a fresh library is built per task (`library_from_spec`, l.1090); the only module-level cache is `_COMPS` (integer compositions) | OK |
| Determinism | budgets are candidate counts; retrieval is sorted by (score, size, id); no wall-clock dependence in search; killed run 1 and run 2 gave identical A 25 and A4 34 | OK |
| Unsupported tasks | stay in `tasks` denominators for every arm and are concordant failures, so they cannot change McNemar or exclusivity (`summarize`, l.337–) | OK |
| Arms match the pre-registration | A `((), uniform, no memory, 200k)`, A4 same at 800k, B `+memory`, C `+inventions +learned prior +memory`; ablations on rule only (l.295–302) | OK |
| McNemar | exact two-sided binomial on discordant pairs, `min(1, 2·P(X ≤ min(b,c)))` (l.255–262) | OK |
| Exclusivity | `E_F` = C solved and none of A, A4, B (+ D on oeis) (l.351–352), as registered | OK |
| Rule hidden tests | every rule SOURCE task has 32 examples ⇒ 8 visible / 24 hidden (same author and format as TARGET) | OK |

No BLOCKER was found for the **as-registered verdicts P2_F, Q3_scoped, Q6a, Q6b, #745 gate**. Three issues below are
BLOCKERs for specific *interpretations* that a good number would invite.

## 1. Harness audit findings

**BLOCKER (Q1/Q4 claims, P3 label) — "4× compute" means 4× candidates, not 4× CPU.** The budget counts candidates
(`self.n`, core l.695). One B/C candidate may run a whole stored program; at the same 200 k budget rule A took 70 s
of wall time and B is still running after more than 60 min. The P3 label `C_BEATS_CLASSICAL_AT_4X_COMPUTE` is
therefore **false as worded if C's CPU seconds exceed A4's**. Pre-stated rule: P3 may be described as
"C beats A4 at lower or equal compute" only if Σ CPU s(C) ≤ Σ CPU s(A4) on that family (per-task `seconds` are
recorded); otherwise it must be reported as "C beats classical search given 4× the candidates but X× less CPU than
C used", and no claim that NEUMANN needs less computation follows from P3. SOURCE investment (1,895 s wall × 4
workers) must be added for any Q4 statement.

**BLOCKER (conditional, dc only) — tasks with zero or very few hidden tests.** `split_examples` (l.116–119) gives
`k = ceil(2n/3)` when n < 12, so n ≤ 2 ⇒ **zero** hidden tests and `all([]) == True`: a TRAIN fit is scored as
solved. n = 3–5 gives 1 hidden test. Rule (24 hidden) and oeis (6 hidden) are unaffected; dc example counts are
TARGET content and were not inspected. Pre-stated sensitivity analysis (does not replace the verdict): after the run,
count dc tasks with 0 and with 1 hidden test; report P2_dc both as registered and with those tasks removed. If the
verdict differs, P2_dc is reported as **not robust** and Q6a is not claimed.

**BLOCKER (Q3 attribution) — "invention used" is syntactic, not causal.** `used_inventions` (l.265–271) lists the
`f\d+` names that appear in C's returned program. It does not show that the task would be unsolved without them.
Causal evidence exists only on rule, from `C_no_inventions` (same memory and learned base prior, no invented symbols).
Pre-stated rule: an exclusive C win counts as **invention-attributable** only if `C_no_inventions` fails it.
Q3_scoped is reported as registered; the attributable count is reported next to it, and if it is < 5 the
Q3 claim is restricted to "C (inventions + learned prior + memory) beats A, A4, B" without attributing the gain to
autonomous invention.

**LIMITATION (P1) — P1 pools invention use across families.** `excl_inv` accumulates over rule, dc and oeis
(l.356–357, 379–382) while Q3_scoped = P1 ∧ P2_rule. P1 can therefore be met by inventions occurring only in dc or
oeis exclusive wins. This matches the registered wording ("C-exclusive TARGET solutions"), so the verdict stands;
the per-family breakdown is reported. P1's first half (≥ 5 inventions) was known true (8) before TARGET.

**LIMITATION (P1 substance) — some inventions are small macros.** `f0 = (cons (head ?0) ?1)` (2 substrate
nodes) counts the same as a higher-order abstraction. Report each invention's expanded size with its use count.

**LIMITATION (Q6, statistics) — task non-independence.** DreamCoder list tasks are known (paper) to contain
parametric families (one concept × several constants); BIG-bench c-functions also contain related variants. McNemar
assumes independent tasks, so p-values on dc in particular are optimistic. Report exclusive wins grouped by concept
where the system's own programs make the grouping evident.

**LIMITATION (Q6b) — the oeis test is shared-core, not transfer.** The frozen core learned from OEIS SOURCE (11 of
45 stored programs; the `I>I` prior is fitted to them). Already recorded in the bottleneck analysis; restated here
because it bounds what P2_oeis can mean.

**LIMITATION (procedure) — two launches of the "single FIRST run".** Run 1 (06:21) was killed by the tool's
30-minute limit after printing A and A4; run 2 (08:21) is the identical command on identical code. The pinned budgets
are deterministic and both values reproduced exactly. Disclose this in the result; it does not change any verdict.

**LIMITATION (exposure) — the designer is a language model.** The pre-registration says "No language model is
involved, so there is no pretraining-contamination channel". That holds for the *system*, which contains no model.
The substrate and hyper-parameters were written by an LLM assistant that may have seen BIG-bench `list_functions`,
DreamCoder list tasks and OEIS in pretraining. This is a design-contamination channel (choice of `map`, `filter`,
`range`, constants 0–9). It cannot leak answers into search, but it weakens "independent author" for capability
levels. The statement should be corrected in the result document.

**LIMITATION (freeze timing) — the external timestamp of the freeze trails launch by ~4 s.** The freeze commit
was made 1 s before evaluate started, but GitHub recorded the push at 06:21:11 UTC. The frozen file was written at
03:44 from SOURCE only, and it is a deterministic function of pre-registered code and SOURCE, so it is
independently reproducible. Next time: push, then launch.

**NOTE — hash coverage.** Coverage is limited to the 3 files the evaluation runs. Python version (3.13.18),
`difflib.SequenceMatcher` and `random.Random` semantics, and `neumann1/__init__.py` (imported, 15 KB, not hashed)
are outside it. Record the interpreter version in the receipt; import the core as a standalone module next time.

**NOTE — one worker exception aborts the whole run.** `pool.map` propagates exceptions with no per-task guard.
This is safe (no silent bias) but costly. Next time catch per task and record the exception as a failure.

**NOTE — no recorded test-set size per task.** The result rows do not store n_hidden. Add it to the schema.

## 2. Memory-driven negative transfer (static analysis of `memory_prims` and `solve`)

Paths by which memory can **hurt** generalisation:

1. **Replay preemption.** If any stored program reproduces all TRAIN pairs, `solve` returns the smallest one and
   **never searches** (`if ast is None and used < budget`, l.1098). A SOURCE program that fits 8 TRAIN pairs but is
   wrong on the hidden ones blocks the correct program that A's search would have found. Possible on rule (34 stored
   L→L programs from the same author) and on dc int→int / list→list tasks.
2. **Cheap overfitting compositions.** Retrieved programs are priced `$mem = 3` (l.1097). Compositions such as
   `cons(k, m_i(tail $0))` are reached early and can fit TRAIN without generalising, winning the minimum-cost race
   against a longer correct substrate program.
3. **Branching dilution.** Eight extra L→L symbols at low cost enlarge every level. At a fixed candidate budget, B and
   C reach smaller program depth than A, so tasks that A solves near its budget edge can be lost.

Answers to the posed questions:

* **Can B be below A?** Yes, through all three paths. `summary.C_vs_*` does not cover B vs A; compute it from rows.
* **Can C lose the chance to use its inventions because of memory?** Yes. Path 1 skips search entirely. For path 2 a
  hidden factor matters: `$mem` is fixed at 3 in every arm, but the other costs differ by arm. Under C's learned
  L→L prior most L symbols cost 4–5 and **every invention costs 4–5**, while a memory call costs 3. Only `$in:L` (2)
  is cheaper, and `tail` ties at 3. Under the uniform prior of A/B, L symbols cost 3, the same as memory. So in C,
  memory is *relatively more* favoured than in B, and cheaper than any invention. C may prefer stored whole programs
  to its own abstractions. The arms therefore differ in four factors, not three: inventions, learned prior, *and*
  relative memory priority. The fourth is uncontrolled.
* **Is enough recorded to identify this?** Partly. Rows store `fit`, `solved`, `via` (`replay`/`search`),
  `candidates`, `program` (memory calls appear as `m<id>` in the program string) and `inventions`. Identifiable after
  the run: wrong replays (`via == "replay"` ∧ ¬solved, where A solved), memory-composition overfits (`m<id>` in a
  fitted-but-wrong program), budget exhaustion (`candidates == budget` ∧ ¬fit). **Not** identifiable: what C would do
  without memory (no `A + inventions + learned prior` arm), and which 8 programs were retrieved (names are not stored).

## 3. Causal decomposition of a C advantage

| Effect | Contrast available | Families | Confounds left |
|---|---|---|---|
| 1. program memory | B − A | all | — |
| 2. learned search prior | C_no_inventions − B | rule only | prior learned on inlined programs; relative `$mem` priority shifts |
| 3. invented abstractions | C − C_no_inventions | rule only | relative `$mem` priority (inventions 4–5 vs memory 3 in C) |
| 3′. inventions under uniform prior | C_no_learned_prior − B | rule only | the uniform prior over the extended library raises **all** base costs (L 3→4, I 4→5), so this is not "B + inventions, prior fixed" |
| 4. more real CPU | none | — | budgets match candidates, not CPU; A4 is 4× candidates (~4.5× A's wall) while B/C cost far more CPU per candidate |
| interactions | C − C_no_inv − (C_no_LP − B) | rule only | memory × invention interaction unidentified (no memory-free C) |

On dc and oeis nothing separates effects 2–4. A C advantage there is evidence for the *package*, not for invention.

## 4. Decision table (fixed before the outcome)

| Outcome | Interpretation | First hypothesis to test next |
|---|---|---|
| **C ≤ B** on rule | Inventions + learned prior add nothing over memory at this budget; Q3 FAIL as registered | **The learned prior, not the inventions, causes the deficit** (prior overfit to SOURCE, plus memory made relatively cheapest). Decidable from existing rows: if C_no_learned_prior ≥ B > C, the prior is harmful; if C_no_inventions ≈ C < B, inventions are irrelevant. No new run is needed for this test. |
| **C > B, but E_rule < 5 or p ≥ 0.05** | C reorders search toward tasks the rivals can also reach; no new capability; Q3 FAIL | **C's gains lie inside A4's reach** (invention = shortcut only, closure B1). Check: fraction of C-solved tasks also solved by A4; nearest SOURCE program to each C win. If confirmed, the FDSA design already written applies. |
| **Q3_scoped PASS** | Scoped evidence that the package beats A, A4, B on same-author TARGET | **The exclusive wins survive when compute is matched and are invention-attributable.** Check now: CPU(C) vs CPU(A4), and C_no_inventions on each exclusive win. Then a labelled post-hoc diagnostic (TARGET is opened, so dev status): A at a candidate budget giving CPU equal to C's, on the exclusive tasks only. If A then solves them, the gain is compute, not invention. |
| **Q3 PASS, dc FAIL** | Inventions are author-specific (Rule's function style) | **The inventions do not occur in dc solutions because dc concepts need different building blocks.** Check invention use in all C dc programs, and how many dc failures are unsupported or memory-less signatures. |
| **Q3 PASS, oeis FAIL** | The core does not carry to integer sequences | **OEIS failures are dominated by recurrences that D (Berlekamp–Massey) solves but the substrate cannot express**: index-based programs with a single fold accumulator cannot carry a(n−1), a(n−2). Check: share of D-solved, C-failed tasks that are low-order linear recurrences. |

Whatever the outcome, every verdict is written exactly as `summarize` computes it. The checks above are reported
next to the verdicts and never replace them.

## 5. Post-result checklist (read-only, from recorded rows; written now so it cannot be chosen after seeing numbers)

1. Verdicts as registered.
2. CPU seconds per arm per family; P3 wording per §1.
3. dc tasks with 0 / 1 hidden test; P2_dc sensitivity.
4. Exclusive wins: per family, inventions used, attributable to inventions (C_no_inventions fails, rule only),
   expanded invention sizes.
5. B vs A discordance; wrong replays; memory-composition overfits; budget exhaustion per arm.
6. TRAIN-fit precision (solved / fit) per arm and family.
7. Disclosures: two launches, freeze-push timing, LLM-designer exposure, task non-independence, oeis shared-core scope.
