# NEUMANN 1 Q3: representation range expansion is not primitive invention

Status: **SCOPED PASS / GLOBAL Q3, Q4, Q6 OPEN**. Date: 2026-10-22.

## Exactly verified
- PR #441, Action 39625778248. Four synthetic source programs x'=x+k for k=23,29,31,37. The old frozen categorical representation m in 2..20 has 19 candidates, all 76 genuine induction checks are SAT in independently pinned Z3 + cvc5. There is **no model training schedule or additional model capacity** that can choose a valid candidate from that exact finite hypothesis class.
- PR #442, Action 39687539419. Four actually updated models, 350 scalar Adam steps each, fit only raw transitions from six development source increments and a designer-provided periodicity/highest-period inductive bias. No per-source modulus labels. Frozen weights generate the previously unavailable parameter AST m=k for four heldout larger primes, each tested four times: **16/16 independently Z3+cvc5 full Init, Consecution and Goal UNSAT**.
- In the EXACT SAME 16 original sources, untrained model weights give **0/16** full original proof. Source transition mutation to k+1 has independent SAT counterexample **16/16**.
- Source-matched classical **GCD also proves 16/16**, with no learned model needed. Measured candidate-only costs are 115.882057 ms across FOUR trainings versus 0.424059 ms across SIXTEEN GCD extractions. These have unequal task counts and do not establish a total cost ratio.
- PR #443, Action 39688044756. Independently replayed fresh native Z3 + cvc5 source checks from SHA256-pinned official artifacts: all 76 original historical list failures, all 16 new trained SAFE 3VC, all 16 untrained counterexamples, all 16 classical control certificates and 16 mutated original counterexamples.

## Scientific meaning
1. **PROVEN:** The old list's problem was representation-range incompleteness, not a bad gradient optimizer. The 76 SAT witnesses are conclusive for that exact class.
2. **PROVEN, SCOPED:** A continuously parameterized, actually trained, source-conditioned constructor can issue a **new AST instance outside an exhausted fixed output list** and independently prove the source goal on controlled previously known OOD synthetic examples.
3. **NOT PROVEN:** No fundamentally new mathematical primitive was learned. MOD and periodicity were human supplied. The generator reuses a human-designed scale feature and favors maximal compatible period. An exact source GCD generates the identical ASTs more economically.
4. **NOT PROVEN:** Genuine real external source-body-blind transfer, learned uniqueness over strongest classical solver, complete cost efficiency or frontier 10x.

## Architecture decision
- Delete the hard-coded finite list of operator *parameters* as a universal representation limit. **Do not** replace it with expensive neural parameter learning when an exact source algorithm (such as GCD) is sufficient.
- Keep the source-conditional output-AST interface and original independent source-verification mechanism as reusable research infrastructure.
- Next trial must challenge the **operator grammar itself**, not merely generate a different numerical parameter. First pre-register untouched original problems, learn source-grounded **guarded composition / auxiliary state / nonlinear mixed relations not anticipated by its frozen output grammar**, independently certify original source semantics and goal, and compare with powerful equally authorized classical synthesis.
- If the learned step is defeated at equal or lower complete cost, default to classical and keep GLOBAL Q3 OPEN.

This is a decisive negative scientific admission boundary, not a new frontier neural architecture.
