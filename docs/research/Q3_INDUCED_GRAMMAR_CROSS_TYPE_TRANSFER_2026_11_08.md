# NEUMANN 1 | Q3 Invented Program Grammar, Cross-Type Transfer & Classical Baseline
2026-11-08 | scoped development study | PR #732

## The real missing capability

The previous two hand-defined operator constructors (finite associative structures and exact polynomials) did not create a general **program grammar**. The new module \`neumann1/induced_grammar.py\` solves source tasks from raw I/O with a generic typed unary/map AST substrate and extracts:
- new executable **unary grammar productions**, with input holes (unbounded AST length in principle, capped at 4 primitive nodes in this experiment);
- higher-order **metagrammar productions** with callable operator slots, derived by anti-unifying independently solved source programs;
- a persistent program grammar used by \`NeumannEngine\` and \`RegistryEngine\` for subsequent problems.

An example induced rule, NOT present as a source rule, is:

\`G(x,f) := sum(map(f,x))\`, where the operator \`f\` was abstracted from source programs using \`abs\` and \`square\`. It can instantiate a source-unseen \`inc\` operator and apply over a new source-unseen **graph weight matrix** after a generic \`flatten\` operation. It is an actual new syntax production in the live grammar. It is **not** discovery of a new mathematical primitive outside the supplied typed DSL.

No target family labels, expected solution program, source task ASTs, hidden target answers, or target oracle functions enter \`GrammarInventor.solve()\`. Source solutions are automatically synthesized, then programs are mined. Target IO examples alone decide whether an instantiated rule is accepted.

## Local development result (no external independent-author claims)

Six source tasks span characters and signed number arrays; they are deliberately held separate from nine subsequent target tasks involving character manipulation, integer digits, signed arrays and weighted graph adjacency matrices. The matrix tasks are data transformations, **not** graph traversal or graph optimization. The source and target task definitions were all authored for this development experiment, so distribution-specific advantage is possible.

| Metric | Learned metagrammar | Identical base DSL, cold enumerative search |
|---|---:|---:|
| Source discovery candidate checks | 251 | 0 |
| New grammar productions created | 3 | 0 |
| Subsequent different task transforms solved | 9/9 | 9/9 |
| Unseen fresh IO examples correct | 1080/1080 | 1080/1080 |
| Source-specific inferred grammar used | 8/9 tasks | n/a |
| Target semantic candidate checks | 596 | 1108 |
| **Source + target semantic candidate checks** | **847** | **1108** |

- Target-only semantic candidate checks reduction: \`(1108-596)/1108 = 46.21%\`.
- Including one-time source discovery candidate checks: \`(1108-847)/1108 = 23.56%\`.
- **Neither is a CPU/FLOP or total wall-clock claim.** Primitive evaluation overhead, source input preparation, runtime cache, prior R&D, and memory are not captured by this metric.
- The learned search occasionally executes more candidates or takes longer on individual tasks. On one target, the cold solver finds the program first. Do not promote a universal improvement claim.
- Both solvers have the same underlying primitive set and maximum expanded program AST cost of 4. A metagrammar rule counts its expanded primitives against the same cap. The learned grammar only changes search order.

## Genuine falsifications

1. **Graph connected-components counting** is not expressible in the finite unary/map substrate used here. The learner must abstain, not report invented graph reasoning.
2. A function that matches the I/O examples but has one unobserved exceptional input is indistinguishable on source facts and produces a wrong held-out prediction. Fitting samples is not proof.
3. No general transfer into independent-author program synthesis, CSP, graph traversal, ARC-AGI-2, or frontier language reasoning has been shown.

## Prior art / novelty audit

Library induction and program abstraction are established fields. DreamCoder (Ellis et al., PLDI 2021, DOI:10.1145/3453483.3454080) learns symbolic abstractions and search policies; Stitch (Bowers et al., POPL 2023) performs fast cross-program library abstraction. This work is a **scoped NEUMANN runtime integration** plus local synthetic demonstration, not a world-first invention of metagrammar learning.

Research goal remains *Frontier-level problem solving with minimum necessary computation*. Global Q3 (arbitrary novel grammar), Q4 (10x strongest matched full cost), and Q6 (all unrelated original problem families) remain OPEN.

## Required decisive next gate

Freeze an external independently authored multi-domain corpus. Compare this approach against classical program synthesis with mined macros, Stitch/DreamCoder-style library induction and direct enumerative baselines with the same primitive and training budget. Demand:
- unseen task-family accuracy and independent original verifiers;
- source training + target candidate checks + measured wall time + memory, source preprocessing included;
- detection of wrong abstractions and robust abstention outside the grammar;
- explicit novelty audit before any global PASS claim.

## Evidence

- \`neumann1/induced_grammar.py\`
- \`tests/test_induced_grammar_cross_domain.py\`
- \`research/q3/q3_induced_grammar_development.py\`
- \`.github/workflows/q3_grammar_invention.yml\`

The demonstration is reproducible with \`python research/q3/q3_induced_grammar_development.py\`. Development test means **not** a frozen, independently authored external evaluation.
