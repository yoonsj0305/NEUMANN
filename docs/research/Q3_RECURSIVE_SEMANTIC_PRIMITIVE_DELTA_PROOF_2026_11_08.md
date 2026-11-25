# NEUMANN 1 | Q3 New Recursive Instruction Semantics and Verified Delta Compiler
2026-11-08 | PR #732 | CONDITIONAL CAPABILITY GAIN, NOT GLOBAL Q3/Q4/Q6 PASS

## Failure root cause

The former \`GrammarInventor\` supported only a finite vocabulary of unary \`call\` and \`map\` ASTs. Cross-task abstraction changed the **order** in which such existing programs were enumerated but not the expressible operational semantics. In particular it had no finite-relation image, mutable state, or data-dependent iteration. Correctly, it abstained on graph connectivity.

The second failure was to count source/target samples and ignore whether the induced control rule was stable under longer paths; a bounded-two-hop predictor can fit short demonstrations while failing on a new chain. The third was to execute a discovered set-expansion loop by rescanning all edges for every round, even when nothing previously visited could add new information.

## New implemented capability

\`neumann1/induced_fixpoint_grammar.py\` introduces a **typed, bounded structural metalanguage** of:
- initial state: seeds, empty, universe;
- relation image: forward or backward;
- state combination: union, replace, difference, intersection;
- control: one step, two steps or iterate until stable.

These are interpreter primitives, **human designed**. The **composed program AST**, including the new loop, is learned from source input/output, rather than chosen from the old program/task library.

\`RecursiveGrammarInventor.invent\` searches candidate ASTs using only SOURCE I/O, requires additional independent SOURCE verification tasks, then promotes a program. The observed promoted AST is:

\`('iterate', 'seeds', 'rel_image', 'forward', 'union', 'stable')\`.

\`RecursiveGrammarInventor.revise_with_source_counterexample\` first revokes a falsified program, re-synthesizes using the counterexample, and refuses to serve an unverified successor. Controlled diagnosis: source tasks with two-hop paths induce \`'two'\`; a longer SOURCE counterexample changes the constructed CONTROL FLOW to \`'stable'\`. This is more significant than tuning a learned parameter.

**Actual generic DSL promotion:** The \`NeumannEngine\` and \`RegistryEngine\` methods \`learn_recursive_control\`, \`revise_recursive_control\`, and \`execute_recursive_control\` connect to \`GrammarInventor.register_generated_primitive\`. A new hashed-name primitive is dynamically registered in the same program-generation grammar used by \`synthesize_with_invented_grammar\`. Before training this operation was not expressible by that call/map language. Only a source-discovered AST with the conditional mathematical certificate may enter the primitive inventory; invalid rules fail closed.

## Mathematical conditional proof

Let \`R(S) = {v: exists u in S, edge(u,v)}\` and \`S_(t+1)=S_t union R(S_t)\` with \`S_0 = seeds\`. By induction on t, \`S_t\` comprises exactly nodes reachable from the seeds by a path of length at most t. In finite V the increasing sets stabilize within |V| iterations. Therefore the discovered program computes **the full directed reachability closure for every finite graph**, *provided the actual task semantics truly are that relational closure*. Fitting source examples cannot establish that premise for arbitrary adversarial oracles.

A structural optimization is then generated using relational-image distributivity over union:

\`D_0 = S_0\`, \`D_(t+1) = R(D_t) minus S_t\`, \`S_(t+1) = S_t union D_(t+1)\`.

This is classic semi-naive/delta evaluation, not a new theorem. It preserves the source-invented program's semantics. It avoids redundant rescans by processing only newly reached states. We do not call this a novel alternative to BFS.

## Exact test evidence and transfer boundaries

A separate classical BFS oracle independently checks **all 512 edge sets × all 8 seed sets for 3 labeled vertices = 4,096 inputs**, with both naïve and delta execution exact. The same frozen synthesized rule was used without domain-specific retraining for 100 grid flood-fill trials, 100 opaque-name finite-state-machine trials and 100 dependency propagation trials. These are different encodings/engineering applications of **the same mathematical relation-closure problem**, not genuinely unrelated mathematical problem families.

GitHub Actions first committed replay \`Q3 Recursive Control Invention and New Primitive\` run 42455907861: **20/20 focused current+previous grammar tests passed**, 4,096 exhaustive n3 checks, external classic BFS comparison and timing experiment PASS. Full repository CI is a separate check.

An intentional exceptional target oracle agreeing with all source observations but disagreeing at one new target remains a formal failure case for global extrapolation. This cannot be made universally correct from finite source observations without additional assumptions.

## Measured timing, strong classical baseline

Python one-process CPU benchmark, 21 warm/cold-agnostic repeated execution timings per method after a warmup. Static chain inputs contain n vertices and n−1 directed edges.

| n | First learned AST median | Generated delta median | Independent strong BFS median | Delta / naive improvement | Delta / BFS slowdown |
|---|---:|---:|---:|---:|---:|
| 100 | 0.47627 ms | 0.04528 ms | 0.02259 ms | 10.52× | 2.00× |
| 250 | 2.62795 ms | 0.10652 ms | 0.05230 ms | 24.67× | 2.04× |
| 500 | 10.17894 ms | 0.21193 ms | 0.10375 ms | 48.03× | 2.04× |
| 1000 | 38.55967 ms | 0.44780 ms | 0.21659 ms | 86.11× | 2.07× |

Measurements above are from the GitHub Actions runner in the initial reproducibility check, not universal hardware performance. A separate local container run reported ~103.1× at n=1000; the difference underscores timing variability. **The optimized inventor is still slower than classical BFS.** Neither speedup includes source discovery cost; end-to-end Q4 10× vs strongest matched classical is NOT supported.

## Gate decisions and structural costs

- Q3 **scoped PASS**: a genuinely new recursive AST, synthesized loop control, falsification/repair, and a new executable primitive added to the original program grammar. **Global arbitrary invention grammar OPEN**: the typed semantics and instruction basis are provided by people, not invented.
- Q6 **scoped PASS**: unchanged generated control law transfers across graphs, grid regions, dependency DAGs and finite automata. **Global unrelated mathematics OPEN**.
- Q4 **not passed** against strong classical BFS. The 10×-86× numbers compare to the naïve first-generated AST only, so are internal optimization results, not frontier efficiency.
- Security/risk: unsupported input types, absent source verifier, unproven semantic transformations, nonmonotone loops, missing rule or counterexample with no valid repair all fail closed.
- Cost model: in software, a raw-material Idiot Index is meaningless. Count source discovery and verification, wall time for execution, and memory of relation indices separately. Do not infer full-program economics from candidate checks.

## Next decisive scientific test

Freeze independent-author original tasks in unrelated mathematical/algorithmic families. Demand that NEUMANN **construct a new semantic operator not in this fixed metagrammar**, not only synthesize one of 72 loop ASTs. Benchmark against equal-input classical synthesis/CEGIS/BFS and expose honest abstentions on impossible/fake-law cases. Until then global Q3/Q4/Q6 remain OPEN.

## Implementation and reproduction

- \`neumann1/induced_fixpoint_grammar.py\`
- \`neumann1/induced_grammar.py\` (new typed primitive registry)
- both live engine APIs
- \`tests/test_induced_fixpoint_grammar.py\`
- \`research/q3/q3_recursive_grammar_first.py\`
- \`.github/workflows/q3_recursive_grammar.yml\`
