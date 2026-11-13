# NEUMANN 1 | First-principles redefinition after SECOND, THIRD and iterations 1–4
2026-11-13 | Owner's "Frontier Research Mandate" | Global Q1–Q7 OPEN | Nothing in this document is a PASS

Preserved unchanged: the Frozen North Star and Q1–Q7; SECOND = FAIL; THIRD = PASS at its stated scope;
iterations 1–4 = FAIL (`Q3Q6_DISCOVERY_POLICY_W1_AND_ITERATIONS_2026_11_12.md`); all raw rows and seals.
The FRESH reserve (499 OEIS A000) and the A001 pool are unopened.

## 1. The problem, restated from first principles

A problem is given as a specification: observations (examples) that a method must reproduce, and hidden
observations it must predict. Finding a method by generate-and-test costs about b^s candidates for a method
of description size s under b choices per step, because each candidate is checked against the specification
as a whole: one bit of feedback per candidate.

Every measured success so far has the same cause: the specification was **factorised** into many smaller
specifications, each with its own feedback, so the cost became Σ b^(s_i) instead of b^(Σ s_i).

| Result | Factorisation that removed the computation |
|---|---|
| THIRD (rule 62 vs 33/35 at equal and 4× CPU; dc 151 vs 125/132) | per-position supervision (equal-length and subsequence alignments); goal decomposition by the derived inverse of cons |
| Iteration 2 (12 : 2 pooled, below threshold) | goal decomposition by the inverse of an operation the system invented |
| Iteration 4 (26 : 1 pooled, below threshold on two of three families; dc 14 : 0, p = 1.2e-4) | per-cell supervision with alignments read from observed equality relations, any number of arguments; 15–38 % less CPU |

Every measured failure has the complementary cause: it changed what is searched without creating new
feedback.

| Result | Why it did not remove computation |
|---|---|
| SECOND (macro inventions) | a macro abbreviates programs already reachable; ~10× work per candidate |
| Iteration 1 (learned allocation and order) | re-weights one hypothesis space; what it can reach is found anyway |
| Iteration 3 (operations from failure gaps) | definitions searched as whole programs: 8 of 20 standard constructors reachable, the rest at cost level 12–33 |

**Restated problem.** Structural discovery is the discovery of factorisations: intermediate observables that
split one specification into several independently checkable ones. Transfer is reuse of a factorisation
*principle* (which relation creates the split), not of a program. Compute reduction is the ratio
b^(Σ s_i) / Σ b^(s_i), and it grows with problem size. That is the scaling signature the North Star asks for.

## 2. The six assumptions of the mandate, against the record

| Assumption | Status | Evidence |
|---|---|---|
| Intelligence must search inside a fixed program language | **rejected as the bottleneck** | the language is not the limit: all 12 constructors iteration 3 missed are expressible (witnesses); whole-program search is the limit (level 12–33) |
| Inventing operations needs more primitives | **rejected** | iteration 4 reached 10 of those 12 with no new primitive, by changing what is supervised |
| The state space must be defined by people | **open; partly addressed** | THIRD's state was designed; iteration 4 constructs the alignment per task from observed relations, but the cell coordinates and the equality relation are designed |
| Transfer is substitution of programs or relations | **rejected for program substitution** | macros (SECOND) and memory (iterations 1, 3) gave no gain; transfer of a relation type is untested |
| Learning needs large parametric models | **not supported by the record** | the gains so far come from structure, at 0 learned parameters; the record also contains no successful learning of any kind |
| All computation must be repeated on each new problem | **open** | no cross-task reuse has paid so far: what recurred was cheap to rediscover (§3) |

## 3. Why cross-task learning has never paid here, and when it would

Reuse saves computation only for structures that are **both expensive to rediscover and recurrent**. Measured:
* the inventions that recurred (append, cons-chains, fold idioms) are found in under 0.1 CPU s from scratch;
* the structures that are expensive (cost level ≥ 12 as whole programs) never recurred as whole programs.

Factorisation changes this. A factorised structure (a relation that splits the specification) is cheap to
*apply* and can be expensive to *find* when the relation is not equality. So the first place where learning can
pay is the **relation** that creates a factorisation: if a relation found on one problem (for example "this cell
equals that cell plus something") is reused to split problems in another semantic domain, the split is not
rediscovered. This is the hypothesis to test, and it is falsifiable.

## 4. Architecture hypotheses compared

| # | Hypothesis | What would be learned | Status |
|---|---|---|---|
| H-a | A larger or better-ordered program language | priors over programs | rejected by SECOND, iterations 1 and 3 |
| H-b | A neural or LLM proposer over programs | parameters | excluded as the core engine by the mandate; would also inherit H-a's one-bit feedback |
| H-c | Library learning of program fragments (DreamCoder, Stitch) | fragments | the old core is this; rejected here (SECOND) |
| **H-d** | **Relational factorisation**: discover relations between observed cells (inputs, the answer's own earlier cells) that split the specification; carry the relation, not the program, to new problems | which relations split specifications, and where | **selected**: the only line with measured causal gains (THIRD, iterations 2 and 4) |

### What H-d takes from prior work, and what it does not claim

* Taken: witness functions and inverse semantics for top-down decomposition (FlashMeta / PROSE, λ²),
  counterexample-guided synthesis (CEGIS), analytical induction from input-output traces (IGOR, Magic Haskeller
  ideas), bottom-up enumeration with observational equivalence, library learning (DreamCoder), predicate
  invention (Metagol, Playgol).
* Different here: the decomposition rules are not written per operator (PROSE writes witness functions by hand);
  they come from relations observed between cells and from inverses the system derives itself.
* Not claimed: a new principle of synthesis. The claim to test is narrower: one relational principle,
  constructed per task from observation, factorises problems in two different semantic domains (list
  transformations; integer sequences), and its removal removes the added solving ability.

## 5. Stage A (this iteration): one relational principle, two semantic domains

**Mechanism (`neumann1/relcells.py`).** Iteration 4 related output cells only to input cells, only by equality.
Generalised, with no operation written for a problem:
1. **Sources of observed cells**: every list argument, **and the answer's own earlier cells**. For a sequence,
   the earlier terms; for a list output, the cells already produced. The first cells of a sequence are its
   initial conditions (data), as in any recurrence.
2. **Relations**: equality (copy) and **linked**: answer cell = op(observed cell at idx, value), where op ranges
   over the binary operations whose inverse the system derived itself (`spec_core_inverses.json`: add, sub,
   mul). The residual a linked relation leaves is computed through that derived inverse and matched by hash
   against every value the enumerator produces.
3. Coordinates gain the aligned earlier answer cells (y[t−1], y[t−2]) and, for sequences, n and the reversed
   history. Case splits, length functions and TRAIN verification are those of iteration 4.

A sequence and a list are handled by the same code path; nothing distinguishes the domains except the types.

**Expected, stated before the run.** Self-relations with an index function reach divide-and-conquer recurrences
(a(n) from a(⌊n/2⌋)) that THIRD's history state and the classical specialist do not; linked copies reach
"move and change" list tasks. The classical specialist D (finite differences, Berlekamp–Massey) stays ahead on
sequences overall; the claim is about added ability, not about beating D's total.

### Stage A pre-registration (fixed before any run on tasks)

Arms, cap 6 CPU s per task, everything included; the learned policy and memory of iteration 1 in every arm
(5-fold policies on SOURCE):

| Arm | Definition |
|---|---|
| R | relational cells: self sources + linked relations (30 % of the cap, before the direct phase) |
| R0 | the same construction with self sources and linked relations removed: **the causal control** |
| Cn, C4 | iteration 4: no cells; iteration-4 cells (rows re-used, same code path and cap) |
| A, B, S, D | iteration 1 / THIRD / specialist rows, re-used |

R and R0 share the coordinates of each domain and the cover order (cheapest consistent description first; a
change made during development after iteration 4 showed wrong case splits): the only difference is the two new
relation types.

**Gating domains (SOURCE):** lists = rule SOURCE (125); sequences = OEIS SOURCE (187). Bonferroni over 2 domains.

| | Condition (each domain) |
|---|---|
| A1 | at least 5 tasks solved by R and not R0, exact McNemar p < 0.025 |
| A2 | at least 3 tasks solved by R and by none of A, B, Cn, C4, R0, S (and D on sequences) |
| A3 | at least 80 % of the tasks R gains over R0 use a self or a linked relation in the constructed representation |
| A4 | total CPU(R) ≤ 1.05 × total CPU(R0) |

Stage A PASS = A1–A4 in both domains. Reported only: rule TARGET and dc (already used by iteration 4).
Development disclosure: the mechanism and the cover order were developed on self-authored tasks; SOURCE task
contents were read during earlier iterations. A PASS would be SOURCE evidence only and would lead to Stage B,
not to a Q3 or Q6 claim.

### Stage A result (2026-11-13, 01:03–01:23 UTC; 1 272 / 1 272 jobs) — **FAIL**

Record: `docs/experiments/results/stage_a_record.json`, rows `stage_a_rows.jsonl`.

| Domain | A | B | S | D | Cn | C4 | R0 | **R** | R only / R0 only | p | solved by R and no other arm | CPU s R / R0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lists: rule SOURCE (125) | 58 | 59 | 57 | — | 59 | 65 | 65 | **68** | 6 / 3 | 0.51 | 4 | 322 / 341 |
| sequences: OEIS SOURCE (187) | 17 | 21 | 15 | 33 | 21 | 19 | 21 | **28** | 7 / 0 | 0.016 | 4 | 940 / 941 |
| rule TARGET (reported) | — | — | 62 | — | 59 | 64 | 64 | 65 | 2 / 1 | 1.0 | 2 | 347 / 349 |
| dc (reported) | — | — | 151 | — | 148 | 162 | 162 | 162 | 0 / 0 | — | 0 | 182 / 179 |

| Condition | lists | sequences |
|---|---|---|
| A1: ≥ 5 and p < 0.025 | 6 : 3, p = 0.51 — **FAIL** | 7 : 0, p = 0.016 — pass |
| A2: ≥ 3 solved by R and no other arm | 4 — pass | 4 — pass (none of them solved by D) |
| A3: ≥ 80 % of the gain through a self or linked relation | 1 of 6 — **FAIL** | 7 of 7 — pass |
| A4: CPU R ≤ 1.05 × R0 | pass | pass |

**Verdict: FAIL** (the rule requires both domains). Stage B is not started; nothing is registered or opened.

What the record shows, kept apart from the verdict:
* **Sequences: a causal gain that the removal of the new relations removes (7 : 0).** All seven gained
  sequences are solved through a relation from the answer's own earlier cells, linked by an operation whose
  inverse the system derived: popcount A000120 as a(⌊n/2⌋) + (n mod 2); A000999 through a(⌊(n+2)/5⌋);
  A000255, A000297 through a(n−2); A000984 and A000125 through a fixed earlier cell. Four of them are solved by
  no other arm, including the classical specialist; A000120 is a divide-and-conquer recurrence that neither the
  THIRD history state nor finite differences / Berlekamp–Massey express. The specialist still solves more
  sequences overall (33 against 28; 13 it solves that R does not, 8 the reverse).
* **Lists: no attributable gain.** Of R's six extra list tasks, one uses a linked relation (rule/c176, each
  element plus its successor); the others are cap-timing and cover differences, and R loses three that R0
  solves. On rule TARGET and dc, R = R0 within one task. The list failures that remain need structures this
  relation vocabulary does not produce (aggregates inside a cell, ranks for sorting, counting).
* The cover order changed in development (cheapest consistent description first) is shared by R and R0; R0
  alone equals C4 on every list family (65, 64, 162), so it neither helps nor hurts at this scale.

Cause, by the kill criterion: the principle "an answer cell is a linked copy of an observed cell" carries to the
second domain where the observed cells include the answer's own past, and adds ability there that the strong
specialist lacks. On lists the binding limit is the relation vocabulary (equality and three derived inverses),
not the search and not the budget.

## 6. Kill criteria for the programme

* Stage A fails → the relational principle does not carry across domains as constructed; the next step is an
  analysis of which relations were missing, not a larger budget.
* Stage A passes → Stage B: learned relations (relations used in verified solutions of one domain, abstracted of
  constants, proposed first in the other) with ablation; then registration of two never-opened families in two
  semantic domains, frozen before any byte is read, and a full-cost comparison (Q5) only after that.
