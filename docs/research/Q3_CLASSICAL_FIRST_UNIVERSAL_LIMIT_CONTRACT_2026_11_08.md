# NEUMANN 1 | Classical-First Correctness Gate & Limits of Universal Self-Invention
2026-11-08 | Source-checked runtime change; user North Star unchanged

## The root-cause correction

Previous code called \`StructuralMetaInventor.solve()\` **before** the trusted cold solver whenever no source-only cost-admission record existed. That reversed the intended priority: "what classical solves, classical solves". An earlier cost policy could turn this off only after expensive calibration. The *default* was therefore wrong.

The new \`solve_or_discover()\` order is:

1. If an independent source-only cost/capability gate **admitted INVENTED_FIRST**, try the learned generator first; every result must still pass the original independent verifier. Fall back to classic on failure.
2. Otherwise, when a trusted classical candidate-producing solver is supplied, execute it **first** and check the original task semantics. On success, return with **zero method candidate queries**. The classic-certified program may still be observed to improve the *source* library; that optional observation has a nonzero cost and must not be confused with zero total overhead.
3. When classical fails or is not applicable, and there is no negative source-only utility veto, try the previously learned method candidates with the original verifier. Never claim unverified success.
4. If an independent source-only utility gate indicates loss, do **not** run the invented method even after classic failure. Return the ordinary failure signal (degraded mode).

A separate \`solve_known_classical(task, semantics=...)\` API on **both production engines** completely bypasses invention and source observation when a trusted task adapter declares the exact mathematical meaning of the problem. \`finite_directed_reachability\` uses an independent conventional BFS and never constructs the expensive invention engine at all. The name supplied by a trusted caller is a SEMANTIC CONTRACT, not proof inferred from an arbitrary I/O sample. Unknown semantic contracts fail closed.

When an invented recursive reachability program has the conditional known-graph invariant, \`execute_recursive_control(..., optimized=True)\` also chooses the established BFS rather than the slower delta interpreter. Novel invention work is reserved for problems that existing methods do not cover.

## The two different "universal" theorems

### Theorem A (unconditional universal identification is impossible)

Take any deterministic learner that observes a proper subset S of inputs of an arbitrary black-box function. Let x* be any input not in S, and consider functions f and g with f(x)=g(x) for every x in S but f(x*) != g(x*). The learner receives identical evidence on the two worlds, hence makes identical predictions. It must be wrong in at least one world at x*. This remains true regardless of how the learner updates its grammar, parameters, neural network, proof search, or internal state.

Consequently, **no finite-sample autonomous invention engine can guarantee correct answers on all completely unrestricted unseen tasks**. This is a logical boundary, not a missing implementation. Demanding global PASS under that definition would entail false reporting.

### Theorem B (conditional proof-carrying search has relative completeness)

For a *countable effective* hypothesis set H, a fair enumerator that eventually visits every h in H, and a **sound and complete terminating verifier** V for a specified task obligation, the procedure "enumerate h; accept the first h for which V(task,h)=True" eventually finds a solution whenever a correct h exists in H. This follows directly because the correct h has a finite enumeration index and each earlier verification halts.

**These premises are very strong.** For arbitrary Turing-complete programs, such a terminating sound-and-complete equivalence verifier is unavailable in general. A verification oracle, finite proof certificate, restricted decidable domain or partial/relative completeness is essential. The theorem makes no claim about practical runtime or being faster than classical enumeration.

Thus NEUMANN's honest North Star has three independently measured obligations:
- **Soundness:** accepted answers satisfy independent original semantics, or are explicitly conditional/uncertain.
- **Capability:** self-generated representations and constructors solve task families beyond a frozen strongest classical baseline.
- **Economics:** *full* discovery + verification + inference cost is lower than an equal-accuracy, equal-input, strongest classical baseline (10x remains an aspirational gate, not automatically obtained from source query savings).

## Regression evidence and limits

\`tests/test_classical_first_q3_contract.py\` verifies:
- original-verified classical first even when a learned program generator already exists;
- zero learned-method candidate calls in this case;
- a previously learned generator can fill a demonstrated gap if the classical solver returns no candidate;
- original verifier rejects an incorrect cold proposal;
- only source-verified positive-utility study may choose INVENTED_FIRST;
- a source-verified negative utility study prevents costly invention;
- absent original checker cannot claim success;
- both live engines directly solve known graph reachability **without creating invented grammar state**;
- a constructive indistinguishability counterexample falsifies unconditional guarantees.

The first prior runner comparison on a 1,000-vertex directed chain had:
- conventional BFS: 0.21659 ms;
- generated delta method: 0.44780 ms, **2.07x slower**.

This comparison is benchmark-specific. The new default routing picks BFS for that recognized task rather than paying for a slower re-implementation. It is not a new frontier superiority result.

## Gate status

- Q3: bounded novel recursive grammars and metagrammars **scoped PASS**. General unrestricted primitive/axiom invention **OPEN**.
- Q4: classical-first non-wasteful execution enforced in a new contract **PASS** when independent semantic certificate supplied; total 10x frontier/strongest classical advantage **OPEN**.
- Q6: conditional relational closure across graphs, grids, dependencies and automata **scoped PASS**; unrelated-domain generalized algorithm discovery **OPEN**.
- Full universal invention over arbitrary unknown tasks **logically impossible**; do not describe it as a pending feature that can be made PASS by increasing tests.

## Next research decision

Before adding another custom algebra inventor, test **independently authored gap tasks** and ensure no known strong classical algorithm satisfies the same obligations. Require task-level original verifiers, frozen heldout tasks, proof provenance, matched end-to-end cost, baseline novelty audit and abstention on unsupported claims. Promote a reusable new semantic constructor only if it beats a strong matched classical solver **on a genuine capability gap**.

## Files

- \`neumann1/structural_meta_invention.py\` (classical-first default and source-gated exception)
- \`neumann1/classical_kernels.py\` (direct trusted semantic classical kernel)
- \`neumann1/engine.py\` and \`neumann1/registry_engine.py\` (shared classical-first interface)
- \`tests/test_classical_first_q3_contract.py\`
- \`.github/workflows/q3_classical_first.yml\`
