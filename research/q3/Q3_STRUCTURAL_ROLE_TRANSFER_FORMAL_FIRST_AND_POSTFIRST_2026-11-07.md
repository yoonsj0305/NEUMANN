# NEUMANN 1 | Q3 structural-operator transfer, 29-family external first, post-first proof

2026-11-07 | Research evidence, source frozen. **Global Q3 OPEN. Q4 OPEN. Q6 OPEN.**

## North star

> Frontier-level problem solving with minimum necessary computation.

Global Q3 requires independent problem families to induce useful NEW representation-constructor *algorithms*, not only new instances of human-coded pattern classes, retrieved answers, or extra enumerative search. Current evidence supports a limited, meaningful cross-input structural transfer and proof.

## Original scientific first, independently authored third-party corpus

- Source: [General Program Synthesis Benchmark Suite](https://github.com/thelmuth/program-synthesis-benchmark-datasets), Thomas Helmuth and Lee Spector; 29 independent problems with original edge/random I/O.
- [Original first GitHub Actions run #42365072610](https://github.com/yoonsj0305/NEUMANN/actions/runs/42365072610), [full immutable receipt artifact #13570743234](https://github.com/yoonsj0305/NEUMANN/actions/runs/42365072610/artifacts/13570743234).
- Source preparation: original git SHA recorded, all 29 problem directories inventoried, 17/29 original edge/random file pairs downloaded under the prespecified 20,000,000-byte per-compressed-file cap; other 12 were infrastructure exclusions, NOT model failures.
- 13/29 original families eligible for single shared input/output contract, 32 independent original random heldout per eligible family (416 test pairs). Exactly **2/13** original families solved 32/32: `number-io` and `sum-of-squares`. Cold SAME constructor core **2/13**, 64/416 exact individual test pairs in each arm.
- Previous coordinate-relation AST was recovered from immutable #717 original POSTFIRST source artifact, source generated program SHA256 `d6108d6e320b8911d380145895b646663700dd9850131ac6dc3dcf250714aa10`, with generic affine index-domain certificate. No human-coded mirror rule in FIRST.
- **Memory reused 0 times in original first, additional correct families 0**; no causal Q3 policy-learning benefit.

## Post-first infrastructure-only expansion, SAME solver/evaluator bytes

- [Post-first streaming run #42365349653](https://github.com/yoonsj0305/NEUMANN/actions/runs/42365349653), [artifact #13570874778](https://github.com/yoonsj0305/NEUMANN/actions/runs/42365349653/artifacts/13570874778). Frozen router Git blob `616aae13f35304fd2572dd5a666499984566b7e6` and evaluator blob `c26e8cb7705fecf53ce5d61deba67103eb0f60aa` unchanged.
- Original gzip random datasets streamed to the same predeclared first 50,000 original cases per family rather than requiring complete 20MB-limited compressed downloads. 29/29 source file pairs acquired, **23/29** eligible, 6 unsupported by input interface. ALL original first 13 eligible results reproduced (13/13).
- **3/23** original families exact 32/32 (`count-odds`, `number-io`, `sum-of-squares`), 96/736 exact test pairs. Cold identical **3/23**, still 0 memory reuse or benefit.
- This is explicitly POST-FIRST; the source families and labels were already exposed in #42365072610.

## Full error census on unchanged 29-family post-first

- [Independent classification run #42365587572](https://github.com/yoonsj0305/NEUMANN/actions/runs/42365587572), [full archive #13570999750](https://github.com/yoonsj0305/NEUMANN/actions/runs/42365587572/artifacts/13570999750).
- **20/29** original families: NOT ONE program could satisfy source I/O within existing three hand-coded constructor families. This is a missing search hypothesis/representation bottleneck, NOT heldout-only overfitting.
- **6/29** original families: unsupported original interface or data type under the fixed parser.
- **3/29** original families: heldout-exact via prior generic typed/fold constructs.
- `RELATION_FRESH` returned `ABSTAIN_TYPE` on all 23 eligible families because the previous discoverer required ONE input sequence and Boolean output, while `mirror-image` uses TWO vectors. The prior source memory was consequently never invoked on the intended structural family. This pinpointed the precise interface mismatch.

## POST-FIRST novel higher-order role-binding of an OLD machine-invented coordinate AST

- New *generic* program adapter accepts two sequence arguments and searches input role bindings `left ∈ {0,1}`, `right ∈ {0,1}`, comparison equality/inequality and all/any quantifiers. The human-written adapter supplies these general possibilities, **not** the correct target role and NOT any coordinate formula. It imports the exact PRIOR generated coordinate expression unchanged from the #717 immutable artifact; matches source I/O to choose a new AST.
- [Original-family post-first transfer run #42365959895](https://github.com/yoonsj0305/NEUMANN/actions/runs/42365959895), [immutable role-transfer artifact #13571970537](https://github.com/yoonsj0305/NEUMANN/actions/runs/42365959895/artifacts/13571970537). All 29 original program families enumerated, 2 were eligible under the two-input sequence→Boolean contract.
- `mirror-image` was solved 32/32 original heldout with generated `DefineRoleAbstraction` AST: `left_role=0`, `right_role=1`, equality/all, equal-length guard, and PREVIOUS generated coordinate expression `['sub',['c',-1],['sub',['i'],['n']]]`.
- That coordinate AST simplifies to `n-1-i` with affine integer coefficients **(-1,+1,-1)**; it was not manually inserted into the GP Suite binder.
- **Causal SEARCH advantage at a capped 64-candidate budget:** learned-source-memory policy solved **1/2 eligible** with one transferred original task; identical cold generic role/coordinate VM solved **0/2** with same 64-candidate budget. Cold same grammar with increased cap 1,200 solved **1/2**. For `mirror-image` itself, remembered expression required **1 candidate check** while cold exhaustive needed **1,105 candidate checks**.
- This is a task-specific 1,105x reduction in CANDIDATE CHECKS, **NOT** a measured 1,105x reduction in discovery+training+proof+execution total cost. Source-memory creation, storage and verification are nonzero; no fleet/energy/total-cost speedup claim.
- **Scientific classification:** a true learned structural *expression* was reused with new automatically selected input-role binding under a preinstalled general meta-grammar. Source+target authors differed, but this is POST-FIRST DEV after the GP Suite original source had already been inspected. It proves a limited role-transfer mechanism, NOT blind cross-author Q3 or a self-invented new fundamental programming-language constructor.

## Independent symbolic proof of exact generated AST, all lengths

- [Z3 proof Actions #42366184295 SUCCESS](https://github.com/yoonsj0305/NEUMANN/actions/runs/42366184295), [full immutable theorem artifact #13572210580](https://github.com/yoonsj0305/NEUMANN/actions/runs/42366184295/artifacts/13572210580). This process loaded the ACTUAL generated GP Suite AST from the previous run, not a human-written substitute.
- Source coordinate program reduced by induction over the **generated AST's** `i`, `n`, `integer`, `+`, `-` grammar; Z3 checked counterexamples to `j(i,n)=n-1-i` over **all positive integer n and 0<=i<n**: **UNSAT**.
- Z3 independently checked index lower bound `j>=0` and upper bound `j<n` for all valid positions: **UNSAT** for counterexample in both cases.
- A deliberately wrong coordinate `j=i` was queried and produced an actual **SAT** counterexample, ruling out a vacuous checker.
- Because the generated role program selects (arg0,arg1), `eq` and `all`, the proven affine coordinate gives for all equal-length finite sequences `A,B`: `∀i, A[i]=B[n-1-i]` iff `A=reverse(B)` by definition. Unequal lengths are rejected by its generated length guard.
- Independent exhaustive two-letter sequences of length 0..7 and additional deterministic larger random heterogeneous sequence tests: **22,865 total**, **0 runtime semantic mismatches**.
- This is a formal correctness theorem for ONE discovered relation under its type assumptions, not an unbounded general intelligence theorem.

## The remaining actual Q3 obstruction

1. Source original problem representations are currently proposed from **three human-coded** constructor families (typed algebra/filter, generic typed state fold, pairwise affine relation). The higher-order role binder is ALSO a human-coded general library. The model invented a program and input binding within that language; it did NOT invent the language/constructor family itself.
2. Cross-input expression transfer succeeded on source-exposed independent-author public tasks, but a new totally-unseen, different-author original corpus **after full generator freeze** is still required to establish blind generality.
3. Test the meta-discovery policy itself: its incremental new constructor creation must measurably increase heldout solution coverage or reduce total end-to-end task cost against an equal-expressivity, equal-compute cold baseline. The current 1-vs-1105 candidate-check result is a valuable scoped signal, not Q4 global.
4. Previous 20/29 missing source programs indicate the need for a machine-generating **new executable representation CONSTRUCTOR ALGorithms**, not just additional hand-coded DSL branches, retrieval templates or brute-force compute increases.
5. Degraded mode remains fail-closed ABSTAIN if no source-proven compatible program or type/invariant proof.

## Next pre-registered independent gate

- Freeze full meta-interpreter, role-composition learner, prior generated source AST and cost contract before opening a genuinely different external original benchmark.
- Require at least two unrelated NEW source-driven representation constructor programs not preinstalled in the human grammar, correct on at least 3 independent examples per heldout original family. This is a target criterion, not a claimed result.
- Independent soundness and nonvacuous negative proof per generated program, cold same expressivity and search-time budget, full original denominator and no retuning on test gold.
- Keep source-first and post-first experiments separate; do not turn the GP Suite re-use into new blind research evidence.

**Final scoped verdict: integration PASS; generative role-binding and cross-argument learned-coordinate transfer PASS with formal proof; Q3 global self-constructing discovery-policy generality OPEN; Q4 global OPEN; Q6 global OPEN.**
