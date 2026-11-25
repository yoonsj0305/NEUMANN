# NEUMANN 1 | Q3: Autonomous Finite Operator and Representation Construction

2026-11-08. **Scoped PASS (conditional finite associative algebras). Global Q3/Q4/Q6 OPEN.**

## Why this changes the NEUMANN core

Previous PR #731 selected among three human-provided search engines. This implementation **creates a previously absent executable binary operation and its intermediate representation** rather than routing among task-specific known operators. It is wired into both `NeumannEngine.synthesize_binary_operator` and `RegistryEngine.synthesize_binary_operator`.

Runtime inputs: only binary ground facts `(a,b,result)`. No domain name, known group, Cayley table, modulus, known generator list, or gold target outputs are passed to `invent_operator`. The benchmark author supplies the **complete left-action rows** for the true identity and a generating set, so active data acquisition is not autonomous.

The algorithm searches for identity evidence, discovers which observed full left-action rows generate the input symbols, deletes unnecessary generators, constructs shortest generator words for each element by graph traversal, and compiles an interpreter applying these action rows to new pairs.

## Proof of bounded correctness

For any **finite associative binary operation with a two-sided identity** `e`, write `L_g(x)=g*x`. Suppose complete source rows `L_g` are supplied for a generating set `G`. BFS from `e` constructs for each `a` a word `g1,...,gk` such that

`a = L_gk(...L_g1(e)...)`.

Then define an **invented operator**

`I(a,b) = L_gk(...L_g1(b)...)`.

By associativity and identity, `I(a,b)=a*b` for **every** `(a,b)` in the observed universe squared. This is a conditional proof under an existing mathematical theorem, not a theorem invented by the AI or an unconditional deduction of associativity from sparse examples.

The needed representation is a newly constructed map `symbol -> shortest generator word`, rather than a copied lookup table or one of four provided domain-specific formulas.

## Local FIRST run results

Script: `PYTHONPATH=. python research/q3/q3_operator_invention_first.py`. Reference oracle functions are separate from the inventor; the withheld answers are consulted only after compiling the new operation.

| Distinct algebra | Source input-output triples | Exact unobserved cells | Generated representation |
|---|---:|---:|---|
| Relabeled cyclic group of size 31 | 62 | **899/899** | one generator, max word 30 |
| Noncommutative permutation group S3 | 18 | **18/18** | two generators, max word 2 |
| Noninvertible 3-state transformation monoid | 18 | **18/18** | two generators, max word 3 |
| Idempotent union semilattice of size 16 | 80 | **176/176** | four generators, max word 4 |
| **Total first four** | **178** | **1,111/1,111** | Four algebra classes |

Additionally, 100 independent deterministic symbol re-encodings, 25 per structure family, yielded **7,775/7,775** exact withheld pairs with identical inventor code; grand total **8,886/8,886**. These symbol re-encodings are **isomorphic** to the underlying families, not 100 newly authored mathematical problems. The mathematical reference oracles themselves were written for this experiment, not independently sourced external benchmarks.

For Z31, 62 observed cells support an executable operator defined on 961 pairs, a **15.5x extension in covered input pairs**, *not* a 15.5x compute speedup. An exhaustive memory-only lookup using identical evidence does not cover any withheld pairs. A classical algebraic completion program given the **same monoid axioms** performs equally well; a hardcoded privileged reference oracle given the real domain rule also performs perfectly. No novel scientific theorem, frontier equivalence or Q4 advantage to the strongest baseline has been established.

## Falsification and degraded mode

Source with contradictory triples, an incomplete row preventing full generation, missing identity evidence, malformed inputs or unobserved query symbols fails closed with `EvidenceInsufficient`. All known source facts, including optional extra facts from rows not chosen as generators, must be reproduced exactly.

**Critical counterexample:** a nonassociative operation can agree with every source row and disagree on an unobserved pair. Thus the source observations alone cannot distinguish the true monoid from a false friend. Global model-independent automatic law discovery is still OPEN.

No `eval`, no generation of arbitrary executable Python source, no target-output leak, and no claim that a finite data set can uniquely identify arbitrary functions.

## Gate decisions

- **Q3 scoped PASS:** executable operator + normal-form representation constructed from I/O under a stated associative-identity prior. **Global Q3 OPEN:** autonomous axioms/primitives, universal operations, nonassociative structures, automatic oracle queries and independent original benchmarks.
- **Q4 OPEN:** no matched, capability-preserving compute benchmark against the strongest algebra synthesis algorithm. The new implementation executes generator words, which can cost `O(k)` per query; an explicit table could execute `O(1)` with `O(n^2)` storage. Coverage multiplication is not compute efficiency.
- **Q6 scoped PASS:** same synthesis logic applies to four distinct algebra classes and many new symbolic encodings. **Global Q6 OPEN:** transfer beyond finite monoids to unconstrained programs, continuous dynamics and external frontier problems.
- **Idiot Index:** material-production cost index is inapplicable to an abstract operator learner. Track source facts, interpreter steps, compiled memory and end-to-end CPU cost instead.

## Next falsifiable experiment

Do NOT spend research budget multiplying relabeling seeds. Give the engine authority to **propose a law, select a discriminating oracle query, reject false premises and change its own representation family**, then compare under identical oracle budgets against classical CEGIS, monoid completion, and a general program synthesizer on independently authored tasks. Maintain fail-closed behavior when no sufficient causal rule is supported. Preserve PR #731's prior 1D-ARC results as a different benchmark.
