# NEUMANN 1 | Q3 Higher-Order Discovery-Method Self-Invention

2026-11-09 · PR #732 · **Scoped Q3 method-level PASS, universal Q3 OPEN**

## 1. What failed, and what was deleted

The prior Q3 meta core chose among complete, researcher-authored search policies such as \`+1\`, \`+2\`, \`×2\` and an integer source-verification budget. It improved its *selection* but could not create an algorithm with a different control structure. It could not demonstrate autonomous algorithm-generation rather than tuning.

This study deletes the list of complete search procedures. It exposes only typed VM atoms: read current/next state, project a feature, test equality, negate a predicate, apply a supplied transition operation, run bounded straight-line sequences and bounded conditional loops. The **control program AST is assembled by the program synthesizer from those atoms, selected by source I/O and revised on source counterexamples**. The resulting program is itself a higher-order *solver generator*:

\`compile(source_invented_method_ast, new_domain_classical_transition) -> new_executable_solver\`

Classical graph expansion, string rewriting, Euclidean arithmetic and order-search transition operations are **supplied**, not re-invented. The same discovered control AST works without labels or dedicated training on those semantics.

## 2. Real counterexample-driven control-program invention

SOURCE meta-training: 8 small tasks, four graph closure and four lexical rewrite examples. Multiple finite-depth methods fit; choosing source-correctness then state-transition count yields **a new two-step straight-line controller**:

\`("sequence",2,("apply","transition"))\`.

SOURCE feedback, 4 longer graph/string cases: finite unrolling fails. A new source-consistent AST is constructed from \`while\`, \`not\`, \`equal\`, \`project-length\`, and \`apply\`:

\`while length(current) != length(next): apply(T)\`.

SOURCE feedback, 2 length-preserving sorting cases: that loop incorrectly stops when values change without changing sequence length. The learner changes **the type of its discovered termination test**, not only a numeric search parameter:

\`while current != next: apply(T)\`.

This last AST is built compositionally, is absent from the earlier finite-unroll candidate family, and compiles to a reusable executable algorithm without copying any task answer.

The compiled method uses a maximum transition budget and returns \`ABSTAIN_BUDGET\` instead of inventing a result for non-converging dynamics. If a trusted classical solution exists, a separate SOURCE verifier must pass before classical-first bypass is allowed.

## 3. New problem-family generalization

Meta-development examples: 8+4+2. The learned AST is frozen *before independent heldout scoring*. Additional SOURCE-only family verifiers: 15 examples, disjoint from target IDs. Fixed targets: deterministic-seed synthetic tasks.

| New mathematical family | Fresh heldout correct |
|---|---:|
| Euclidean integer arithmetic (not meta-trained) | 60/60 |
| Unique-element projection of finite tuples (not meta-trained) | 60/60 |
| Binary interval search (not meta-trained) | 100/100 |
| Longer sorting permutations | 7/7 |
| Larger finite graph closure | 25/25 |
| **Total convergent target cases** | **252/252** |
| Non-convergent finite periodic cycles | **10/10 correct abstentions** |

Previously learned bounded two-step method correctly handles only **2/252** convergent target cases. The revised method solves 250 additional controlled cases, with no domain-name routing.

**Independent interpreter correctness contract:** All 4^4=256 deterministic transition functions over 4 states × all 4 initial states, **1,024 cases**, are exhaustively tested. All cases converging to a fixed point return the correct value; non-converging cycles return the finite-budget abstention. 100 additional fresh bounded binary-search interval tasks also pass under the same method.

Local frozen prediction SHA and scoring artifacts are available in the companion source archive. GitHub Actions reruns the program and its independent test suite. The original source and score functions are separated by SHA-256 freeze; no hidden target output is read in the proposer.

## 4. Conditional theorem: scope of algorithmic transfer

**Theorem.** Let \`T:S→S\` be a deterministic pure transition on a state type supporting exact equality. If for input \`x\` some integer \`m\` satisfies \`T^m(x)=T^(m+1)(x)\` with \`m+1≤B\`, the new compiled method with budget \`B\` returns \`T^m(x)\`.

**Proof.** Inductively after \`j\` executions the current state is \`T^j(x)\`. Each iteration computes \`T^(j+1)(x)\` and compares its entire value to \`T^j(x)\`. The first equality is a fixed point because \`T(s)=s\`, and deterministic application cannot leave it. Thus the method returns that fixed point by the \`m+1\`-th call. If no equality is witnessed within \`B\` calls, no valid terminal result is claimed.

This theorem holds for **all** deterministic, pure, finitely convergent transitions meeting the interface contract, independent of the underlying state's domain. It does **not** prove that an arbitrary unknown problem asks for a fixed point or that a supplied \`T\` correctly represents that problem. It does not infer \`T\` from scratch.

## 5. Honest limitations

- Predefined VM primitives include the control instruction \`while\` and general equality, just as a CPU instruction set is predefined. The novel discovered artifact is their *composed procedure*, not a new computational primitive.
- The meta task family deliberately shares a convergent-transition structure. The three novel target semantics differ, but this is not arbitrary general intelligence or independent-author frontier performance.
- Source examples contain expected outcomes for **method learning**; the unseen target oracle is not exposed to the proposer before predictions are frozen.
- A target transition may have cycles, side effects or a wrong problem specification. Correctness is only conditional on the theorem's assumptions.
- Not evidence that NEUMANN can invent new domain-specific operators from an unknown input format, learn every inductive bias, or solve arbitrary ARC/novel mathematics.
- Q4 cost optimizations are deferred as requested. If a strong domain-specialized classical solution is already source verified, use it.

## 6. Reproduction

- \`neumann1/higher_order_method_inventor.py\`: typed VM + compositional control-program synthesis + counterexample revision.
- \`neumann1/engine.py\`, \`neumann1/registry_engine.py\`: \`meta_learn_higher_order_method\`, \`meta_revise_higher_order_method\`, \`meta_compile_higher_order_method\`.
- \`tests/test_higher_order_method_inventor.py\`: both live engines, generated 75-control-method space, four-family transfer, classical-first bypass, all 1,024 finite-state maps and 100 interval-search cases.
- \`research/q3/q3_higher_order_method_blind.py\`: source-first prediction SHA-256 freeze followed by independent 262-case scoring.
- \`.github/workflows/q3_higher_order_method.yml\`, \`.github/workflows/q3_higher_order_blind.yml\`.

**Decision: Q3, self-invention of a bounded higher-order solver generator and two source-driven procedural rewrites = scoped PASS upon independent CI. Universal unrestricted Q3 and Q6 = OPEN. Q4 = intentionally deferred.**
