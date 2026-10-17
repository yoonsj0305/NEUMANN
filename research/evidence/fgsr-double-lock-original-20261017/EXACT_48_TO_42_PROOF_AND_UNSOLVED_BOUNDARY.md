# NEUMANN 1 · 2026-10-17 · original double-lock 48-Horn proof-carrying simplification

**Exact scientific verdict: `EXACT_FIRST_ORDER_TAUTOLOGY_ELIMINATION_6_OF_48_CERTIFIED / SOURCE_EQUIVALENT_42_HORN / UNBOUNDED_ORIGINAL_SAFETY_STILL_UNRESOLVED / Q1_Q7_OPEN`.**

## Original pinned independent benchmark, historical headroom
Genuine externally authored CHC-COMP 2026, `chc-comp/chc-comp26-benchmarks` at upstream `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, `ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2`, **exact source SHA256 `2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645`**, 13,095 bytes, **48 universally quantified original Horn assertions**, among them **17 three-premise rules**. Previous hand-coded Houdini hypotheses yielded 46 of 48 original assertions whose negations were UNSAT; TWO remained, so that was **NOT a valid complete safety proof**. No learned model originally solved this family, and Q1–Q7 remain OPEN.

## Original Z3 strong baseline, preregistered one-shot
[Preregistration](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-double-lock-original-20261017/PREREG_ONE_SHOT_STRONGER_ORIGINAL_STATUS.md) before running four actual separate solver arms. [GitHub Actions first #39022107999](https://github.com/yoonsj0305/NEUMANN/actions/runs/39022107999), immutable artifact id **12096971794**:
- Native original 12s budget: **TIMEOUT** (~14s subprocess wall including Python overhead);
- `z3.SolverFor("HORN")` 12s: **UNKNOWN / timeout**;
- Spacer and BMC erroneously checked internal fixedpoint rule count after using a parser that had *not registered rules*: 0, **INFRA ERROR**, *not* actual mathematical solver failures.
Fix ONLY the source parser/registration: independently show original last rule `CHC_COMP_FALSE=>false` is equivalent to query for `CHC_COMP_FALSE`, then register all preceding **47 exact source rules** as fixedpoint and query the same condition. No arithmetic guard or source theorem altered. [GitHub Actions corrected #39022285837](https://github.com/yoonsj0305/NEUMANN/actions/runs/39022285837), immutable artifact id **12097650356**:
- Spacer 16s source `Z3Exception: canceled` at actual 16.217s (no verdict);
- Direct original native Z3 12s **TIMEOUT**;
- Fixedpoint BMC 8s **UNKNOWN**;
- Horn SolverFor original 12s **UNKNOWN: timeout**.
**Original unbounded SAT/UNSAT remains UNKNOWN**, no fabricated trace or safety certificate.

## New substantive proven mechanism: remove six globally tautological original Horn clauses

[Removal prerequisite contract](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-double-lock-original-20261017/PREREG_EXACT_TAUTOLOGY_REDUCTION.md) and [actual source-verifying code](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-double-lock-original-20261017/exact_tautology_reduce_original.py). For every original universally quantified rule `∀v.Φ(v)`, independently instantiate fresh uninterpreted Int/Bool symbols `c` and check Z3 satisfiability of `¬Φ(c)` **without ANY inductive invariant or reachability assumptions**. Only if two separately constructed fresh solvers both return **UNSAT**, discard original rule as a **first-order tautology for every interpretation** of `Inv` and `CHC_COMP_FALSE`. If SAT/UNKNOWN, KEEP. Do not remove a clause because it looks irrelevant or a bounded trace omits it.

[GitHub Actions first actual exact-reduction #39022632743](https://github.com/yoonsj0305/NEUMANN/actions/runs/39022632743), immutable actual JSON artifact id **12096349513**, Z3 4.13.3:
- **Original clauses precisely `[27,30,31,33,34,45]`** independently refuted as always-valid, each in two fresh solver contexts, all UNSAT. Examples: original #27 contains `Inv(...,v_7)` and `v_7=4=v_8`, so its head `Inv(...,v_8)` is identical to antecedent. Original #30, #31, #33, #34, #45 all include their **identical head as an antecedent**, so are trivially true regardless of source reachable states.
- Original **48 → logically equivalent 42** quantified Horn rules, **12.5% exact reduction**, NOT a bounded approximation or missing rule relaxation. Each discarded clause's universal logical validity means the entire conjunction over all uninterpreted relations is logically equivalent to the original conjunction. All 48 original equations parsed, all other 42 source constraints retained as actual original quantified SMT ASTs, source SHA pin verified. Original completely unchanged upstream.
- Reduced canonical source SHA256 is recorded in first result JSON receipt, and original→reduced index map for all 42 retained is recorded for independent replay.
- On reduced **equivalent** 42-clause problem, exact Horn solver 20s **UNKNOWN / timeout**, native Z3 16s **TIMEOUT**, no solution.
- Thus **NO proof that the original benchmark is SAT or UNSAT**, **NO 48/48 Horn certificate**, **NO neural discovery or total cost speedup**. No supported inference about success on other external problem families. State of main research questions: **Q1–Q7 OPEN**.

## Decision / STOP
The largest genuine progress was eliminating irrelevant constraints **with machine-checkable universal first-order receipts**. Simple extra solver-time extensions do not turn this into a full proof. Source's **17 joint three-premise transitions** and disjoint finite-PC/lock state correlations remain the unsolved relational structure; previous 46/48 failure shows that existing fixed list of local predicates does not suffice. The next NEUMANN model must propose **cross-thread, cross-premise conditional relation operators**, in a typed graph/AST grammar, and supply independent fully original proof receipts with equally strong classical/CEGIS controls before any Q3/Q4 closure. No more unbounded repeats of neural numeric-coefficient toy tasks; the true source status is UNKNOWN, not a hidden PASS. All Q1–Q7 OPEN.

### Authentic evidence links
- [First original first 4-arm attempt and preserved parser error](https://github.com/yoonsj0305/NEUMANN/actions/runs/39022107999)
- [Only parser repaired, same budgets and full original](https://github.com/yoonsj0305/NEUMANN/actions/runs/39022285837)
- [Exact proven tautology elimination first execution](https://github.com/yoonsj0305/NEUMANN/actions/runs/39022632743)
- [Actual generator and independent per-original-clause verifier](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-double-lock-original-20261017/exact_tautology_reduce_original.py)

Correctness proof: `∧_{i=1}^{48} C_i ≡ ∧_{i∉{27,30,31,33,34,45}} C_i` since each removed `C_i` is a first-order validity in arbitrary models, independently checked twice. **This is the only newly closed original external problem claim.**
