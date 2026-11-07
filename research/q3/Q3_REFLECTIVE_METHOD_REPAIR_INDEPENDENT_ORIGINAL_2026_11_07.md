# NEUMANN 1 | Q3 Reflective Repair of an Invented Constructor
**2026-11-07 • Source-frozen independent original evidence • GLOBAL Q3/Q4/Q6 OPEN**

## Scientific verdict

**SCOPED PASS:** An executable *source-induced program-constructor method* was automatically generalized in response to a independently verified counterexample to its former hard-coded source-derived representation. The new method was fixed before a third, untouched 24-problem original cohort and solved **4/24**, vs the unmodified previous learned constructor **3/24**. One full-original gain is causally attributable to making the guard index a parameter.

**Global Q3 remains OPEN:** The universal typed interpreter, graph expression search, antiunification algorithm, guard predicate family, and policy control are HUMAN-WRITTEN. The complete classical search over the same hypothesis language also solved 4/24. No new independent-author family, self-authored primitive interpreter, model weights learning or global 10× compute advantage was demonstrated.

## Three independent original source-frozen gates

| Cohort (all from pinned Barnard-PL-Labs/sygus-sgi-1 commit) | Original 64-bit tasks | Scoped result | Control | Immutable execution |
| --- | ---: | --- | --- | --- |
| PRE_30_100..PRE_53_100 (first graph gate) | 24; 68 source, 32 heldout each | Branch+graph 6/24, restricted graph 1/24 | Fair interpretation: DIFFERENT representational expressivity, not a learned-policy accuracy win | [FIRST #42370828681](https://github.com/yoonsj0305/NEUMANN/actions/runs/42370828681) [artifact #13573572617](https://github.com/yoonsj0305/NEUMANN/actions/runs/42370828681/artifacts/13573572617) |
| PRE_54_100..PRE_77_100 (source-learned method gate) | 24; 68+32 each | Learned fixed BIT(0) constructor 1/24; same-grammar classical full search 2/24; hybrid 2/24 | No learned method improvement. This FAIL created the repair counterexample: **PRE_60_100 BIT(3)** | [FIRST #42371171010](https://github.com/yoonsj0305/NEUMANN/actions/runs/42371171010) [artifact #13572909283](https://github.com/yoonsj0305/NEUMANN/actions/runs/42371171010/artifacts/13572909283) |
| PRE_1_100..PRE_24_100 (third source-frozen untouched gate) | 24; 68+32 each, 0 data errors | **Reflectively repaired learned method 4/24**, old fixed learned method **3/24** | Same-grammar classical **4/24**, no advantage; hybrid 4/24 | [FIRST #42371505766](https://github.com/yoonsj0305/NEUMANN/actions/runs/42371505766) [artifact #13573623632](https://github.com/yoonsj0305/NEUMANN/actions/runs/42371505766/artifacts/13573623632) |

All source and heldout examples are published ORIGINAL I/O; no \`.sl\` reference solutions or target heldout outcomes enter the generator. All source-method artifacts are frozen before the target download in CI; preflight independently validates SHA/guard/template. No previous FIRST score is rewritten.

## Actual novelty witness: meta-method modifies its own generator language

1. Prior source experience: five original-heldout-verified learned programs, IDs PRE_41_100, PRE_42_100, PRE_49_100, PRE_51_100, PRE_53_100. The human-authored generic anti-unifier generated the executable higher-order **method AST**:
   \`ite(bit(0), HOLE_0, HOLE_1)\`.
2. Independent original failure/verified correction: new source PRE_60_100 was solved by the full classical search using **bit(3)**, while the old learned method could not represent it. PRE_55_100 and PRE_60_100 original heldout tests certify two additional source programs (32/32 each).
3. Without a human choosing the new index, the **same source-data-driven antiunifier** generalized the *method program itself* to
   \`ite(bit(HOLE_0), HOLE_1, HOLE_2)\`.
   The original program set supplied allowable source-inferred indices **[0,3]**. The meta-language hash was frozen to **\`48263eb78a1d4078cccd4b6d90666c3a9d3fe01f3fdb31513b6c5bd4f6c719f9\`** before the third new cohort was downloaded.
4. On the third cohort, old learned constructor solved PRE_3_100, PRE_11_100, PRE_19_100. Expanded constructor retained those and additionally solved **PRE_10_100** by autonomously generating
   \`ite(bit(3), add(shr(x,16),1), and(1,not(x)))\`.
   All **32/32 original heldout** on PRE_10_100 were exact.

This is a **genuine bounded third-order source-data-guided method generalization with a new original causal witness**. It is NOT a fully autonomous invention of arbitrary meta-learning procedures; an antiunification interpreter still specifies how to make holes.

## POST-FIRST independent bounded-grammar necessity audit

[Post-first original audit #42371754200](https://github.com/yoonsj0305/NEUMANN/actions/runs/42371754200) (development only, no new FIRST). For PRE_10_100, exactly 68 source pairs and a finite **116-member** human-coded expression vocabulary:
- Wrong old BIT(0) partition: **0 candidate expressions match either source partition** (counts [0,0]).
- New source-inducted BIT(3) partition: **1 expression matches each partition** ([1,1]).
- The generated BIT(3) AST matches 32/32 previously preserved original heldout; negative control with guard changed to BIT(0) and everything else identical matches **11/32**.
- This is an exhaustive impossibility statement *within the bounded 116-expression vocabulary and the 68 source I/O observations*, NOT an impossibility theorem over all programs.

## Compute budget and counterfactuals (24 third-cohort originals)

| Method | Exact originals | Source candidate checks | Source discovery time on GH runner |
| --- | ---: | ---: | ---: |
| Fixed prior learned method | 3 | 8,352 | 231.92 ms |
| **Reflectively repaired learned method** | **4** | **13,920** | **233.76 ms** |
| Full-grammar classical search | 4 | 359,136 | 352.89 ms |

- Nominal candidate checks: full / repaired = **25.8×**. Not an end-to-end cost multiplier; different search structures count candidate matches differently.
- Source discovery time full / repaired = **1.51×** (measured GH environment; these exclude upstream data/CI and shared prior learning).
- Hybrid learned-plus-fallback **modeled sequential replay** total = 527.81 ms, versus cold full 352.89 ms. Thus naïvely adding a learned stage before classical fallback can be **1.50× slower**. Actual CI ran independent comparator arms, not an isolated hybrid end-to-end trial.
- One-time in-memory pattern induction measured ~0.267 ms; it excludes prior source program discovery, frozen artifact acquisition, network/CI setup. No assertion of Q4 10× end-to-end advantage is supported.

## Root cause and smallest next necessary change

Prior Q3 0/24 ICFP local-bit tables: wrong unit of computation, omitted 64-bit compositional arithmetic, conditional branches and global bitwise operations.

After graph representation expansion: 6/24 first original evidence, valid capability, still human-provided construction grammar.

After extracting a method from five prior programs: overfitting of the **discovery policy** itself, fixed BIT(0) and negative external 1/24 vs full 2/24.

After reflective repair: guard index becomes a generated variable and exact gains 3→4, but restrictive two-branch form still prevents many examples and identical full grammar can solve the same four.

**Next decisive hypothesis:** Rather than increasing the bit-index range or adding ad-hoc macro names, synthesize general graph-constructor control structures with variable-depth recursive expressions, conditionals and structure-licensed grammar growth, and learn the *selection policy* by minimizing expected verification cost on held-out source families. Pre-register a **new independent-authored** benchmark, not another same-generator slice. Demand causal memory advantage versus the same expressive classical solver under equal total compute; certify generated executable semantics and retained utility on multiple unseen author families. Any failure stays OPEN.

## Operational invariants

- NO first-run retune; no golden solution consumption prior to source freeze.
- Fail closed on malformed bitvectors, unsupported source constraints, missing artifacts; preserve 0 and errors.
- Provenance: GitHub source blob + SHA256 frozen learned meta method + run/artifact IDs + exact denominators.
- Degraded mode: full-grammar classical fallback on ABSTAIN, but invoke only if estimated additional utility exceeds estimated checking cost; previous naive sequential fallback was slower and is NOT Q4 PASS.
- Explicitly protect negative controls, out-of-support inputs, multiple independent author sources, and costs that include source discovery and verification.
