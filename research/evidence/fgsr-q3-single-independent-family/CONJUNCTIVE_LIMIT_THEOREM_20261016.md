# FGSR-Q3: bounded conjunctive relational language exhausted on authentic hard 48-Horn original

Date: 2026-10-16. **Disposition: completed scoped negative gate, NOT NEUMANN Q3/Q4/Q7 progress to PASS.**

## Grounded original and two actual CPU experiments

Original external CHC-COMP benchmark: `ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2`, 48 unchanged original Horn clauses, source SHA256 `2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645`. Opened-development case, not unseen heldout.

**First run** [GHA #38917508224](https://github.com/yoonsj0305/NEUMANN/actions/runs/38917508224), 1105 fixed researcher-authored hypothesis predicates, including cross-thread control stage exclusions and control-conditioned numeric equality, Z3 4.13.3. Stop at registered 8-pass cap: **360 SMT checks**, **880/1105** still surviving, **79,941.418ms** wall; `INCOMPLETE_ROUND_CAP`. Original-gate verdict not issued at this stage. Immutable GHA artifact ID **12053011801**.

**Completed fixed-point follow-up** [GHA #38918111890](https://github.com/yoonsj0305/NEUMANN/actions/runs/38918111890), **identical 1105 candidates / exact same original bytes / no added theorem**. Changed elimination scheduler to immediately discard refuted conjuncts and revisit affected rules until fixed point, rather than bulk iterations:
- **779 exact SMT checks**, **506 counterexample-guided refinements**, **5 passes**, **130,697.145ms** complete wall.
- **971** refuted conjuncts eliminated; **134** surviving conjuncts form a genuine inductive fixed point over original relational transition clauses.
- Final verification of **every original 48 Horn rule** with the retained invariant: **46 UNSAT, rule 46 SAT, rule 47 SAT, rule 48 UNSAT**.
- `INDUCTIVE_RELATION_INSUFFICIENT_ORIGINAL_GOAL`: two SAT are models of the negated safety clauses under this *incomplete overapproximating candidate*, **not** proven reachable program error traces. Hence source SAT/UNSAT still unknown, no complete certificate.
- Neural forwards = **0**, NEUMANN trained abstraction mechanism = **NOT RUN**, Q1–Q7 **ALL OPEN**. CPU time cannot be called efficiency win.

## What actually became a scoped theorem (conditional on independent SMT correctness)

For a fixed finite predicate set C, standard conjunctive Houdini starts from C and removes any p for which a source Horn transition has a satisfying assignment to current C in every premise, yet the head violates p. A subset invariant containing p is impossible because the same assignment satisfies any weaker subset's premises. This inductively excludes every removed predicate from any inductive conjunction over C. On convergence the remaining conjunction itself is inductive. Therefore it is the **greatest inductive conjunction in this one 1105-predicate hypothesis language**, and its failure at source goals 46 and 47 means **no conjunction drawn from this fixed language can establish the original goal**. This is *not* a classical impossibility theorem. A relational invariant not expressible as this conjunction, such as phase-disjunctive, quantified, numeric cross-variable comparisons, or a richer abstraction language, could still work.

## Cost/authority and research disposition

- No candidate learned content was generated, no new neural training, no speed advantage and no Q gate closed.
- Do not turn these into 1105 neural supervised labels and claim autonomy: all hypothesis *kinds* came from a researcher.
- Do not rerun further source-tailored Boolean/Houdini/solver-timeout variants on this already opened hard original. The **next valid scientific experiment** must introduce a *learned semantic abstraction-kind proposer*, trained only on other source groups and frozen before distinct-source family holdout, with original full proof, strongest classical equal-information source-aware abstraction baseline, explicit learned-minus ablation, and all costs. Q7 still requires authenticated actual SMALL-fail/FRONTIER-pass paired executions.
- Captured evidence archive available via conversation artifact `NEUMANN_FGSR_RELATIONAL_BOUND_GATE_20261016.zip` (7,899 bytes; SHA256 `3d043e4f366b702ae0cfab3ab6bda22b54544d9abc940d3fe7612f1adb3aecc4`), comprising both raw GHA receipts, independent consistency audit, 2 mutation rejection checks, README and SHA manifest. Source original intentionally not redistributed; raw artifact ZIP not itself uploaded to GitHub. `audit.py` only audits receipt integrity, NOT an independent re-run of the source with a second solver.

Code:
- [Frozen initial hypothesis language and original verifier](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-single-independent-family/relational_houdini_single_gate.py)
- [Completed original fixed-point continuation](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-single-independent-family/relational_houdini_fixpoint.py)

**Scientific verdict: `FIXED_CONJUNCTIVE_LANGUAGE_FULLY_EXHAUSTED / ORIGINAL_48_UNPROVEN / LEARNED_Q3_UNPROVEN / Q1_Q7_OPEN`.** This closes the restricted-language screening question, not any global Q.
