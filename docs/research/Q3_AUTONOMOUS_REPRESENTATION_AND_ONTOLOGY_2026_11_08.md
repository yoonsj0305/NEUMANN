# NEUMANN 1 | Autonomous Invention of Representations and Hidden Ontologies
2026-11-08 · PR #732 · scoped Q3/Q6 mathematical experiment · NOT global Q3/Q4/Q6 PASS

## The bottleneck eliminated in this stage

The old ARC object/relational inventions synthesized executable rewrites **from a fixed, human-specified object feature language**. To invent a representation, the system must instead create and test **new latent feature dimensions** absent from the original input and then discover when multiple features denote one reusable semantic object.

This experimental pipeline actually has three different learned layers:

1. **Source-induced feature language**: From unlabeled raw bit coordinates and SOURCE I/O, generate interacting monomials to the needed degree; solve the exact polynomial via GF(2) elimination. The discovered coefficients and interaction masks become a NEW executable AST, rather than a choice among given object features.
2. **Symmetry-orbit representation**: Find unlabeled graph substructure patterns and symbol-position stencils that generate the ENTIRE learned set of interaction features. Reject incomplete source orbits. Compile discovered structural motifs to different input sizes without re-learning on larger target outputs.
3. **Hidden ontology inversion**: From source-learned triadic interactions over 10 arbitrarily permuted RAW variables, infer graph vertex stars, underlying edge endpoints and an unlabeled motif. No graph edge metadata or graph vertex IDs enter the source learner. Compile the discovered ontology to an executable program.

All three invoke established classical mathematics where those tools already suffice. This is a research integration and autonomous hypothesis construction, **not a claim of discovering new mathematical algorithms**.

## Independent source and exhaustive finite validation

| Source meaning used ONLY by source oracle and scorer | SOURCE probe count | Independent source verification | Full finite-domain checks | Newly created interaction monomials |
|---|---:|---:|---:|---:|
| 12-bit numeric algebraic invariant | 79 | 70 | 4,096 / 4,096 | 4 (one linear and three quadratic) |
| 5-vertex graph triangle parity, 10 raw edge variables | 176 | 50 | 1,024 / 1,024 | 10 cubic motifs |
| 12-symbol occurrence of ordered 101 pattern, parity | 299 | 90 | 4,096 / 4,096 | 20 degree-2/3 interactions |
| 5-vertex 4-cycle parity | 386 | 50 | 1,024 / 1,024 | 15 quartic motifs |

Every finite-domain example is checked against a separately defined reference law. The invention engine receives neither named domain semantics nor target outputs, only source input/output observations, a finite source-degree bound and independent source verification.

**Structural transfer to dimensions never used for source-fitting:**
- Learned triangle motif from 5-vertex source → **all 32,768** labeled 6-vertex graphs correct; 1,000 sampled 7-vertex and 400 sampled 8-vertex graphs correct.
- Learned 4-cycle motif from 5-vertex source → **all 32,768** labeled 6-vertex graphs correct; 600 sampled 7-vertex graphs correct.
- Learned ordered-symbol motif from length-12 source → 400 sampled cases each at lengths 13, 20, 37 and 64 correct. The original finite-dimensional polynomial **cannot execute** at those widths; the invented structural feature generator can.

**Hidden semantic ontology:** Source raw coordinate positions are independently permuted five different ways. The learner has no source graph schema. In all five variants it recovers 5 vertex stars, assigns all 10 input variables to two recovered vertices, induces a structural motif, and predicts all **5 × 1,024 = 5,120** possible source-width raw inputs exactly. Additional 6-vertex target cases use a separately declared target coordinate schema.

## Mathematical evidence, not conjectural universality

### Theorem A: rank-complete class-relative feature identification

Any function \`f : {0,1}^d -> {0,1}\` with algebraic normal form degree at most \`k\` has exactly \`D=sum_{i=0}^k binom(d,i)\` unknown GF(2) coefficients. Probe input bitsets of weight at most k. Their incidence matrix against all <=k interaction monomials is triangular under inclusion order with all diagonal elements one; hence it has rank D. Exact elimination recovers a **unique polynomial within that degree-bounded class**. The system explicitly refuses extrapolation when rank is insufficient, outputs conflict, or independent source checks fail.

This is established Boolean algebra and classical elimination, not an original general learning theorem. **No finite source set proves that an arbitrary unknown function is actually degree <=k**.

### Theorem B: conditional feature-orbit transfer

An interaction motif is an unlabeled monomial template. If every source monomial belongs to an orbit under the declared source symmetry action, the original learned representation can be reconstructed from those orbit templates. The compiled program generates the same templates over larger declared input structures. When the true target function on those structures is the XOR of motif embeddings, the generated program is correct by construction. This remains a **conditional structural hypothesis**, not a proof that all unseen problems have the same law.

### Theorem C: graph ontology inversion in an identifiable special case

For complete graph K_n with n >= 5, each raw input coordinate denotes an edge but is presented in an UNKNOWN permutation. If source interaction monomials are exactly the indicator products of all triangles, two coordinates co-occur in a monomial exactly when their edges share a vertex. Their co-occurrence graph is the line graph L(K_n).

Its n maximal cliques of size n-1 are precisely the original vertex stars (n-1 >=4 distinguishes them from three-edge triangles). Every raw edge coordinate lies in exactly two stars, recovering its two latent endpoints **up to vertex relabeling**. A final orbit-closure certificate rejects ambiguous or incomplete source. This is a mathematical existence/uniqueness result under the stated complete-triangle hypothesis, **not general ontology discovery from arbitrary data**.

## Classical-first Q4 accounting

Rank-complete SOURCE queries alone versus learning an arbitrary full binary truth table:

| Synthetic source class | SOURCE queries / total possible inputs | Raw truth-table / SOURCE ratio |
|---|---:|---:|
| 12-bit degree-2 | 79 / 4,096 | 51.85× |
| 10-bit degree-3 | 176 / 1,024 | 5.82× |
| 12-bit degree-3 | 299 / 4,096 | 13.70× |
| 10-bit degree-4 | 386 / 1,024 | 2.65× |

Independent source verification adds 70, 50, 90 and 50 checks respectively. Ratios compare to a **weak full truth-table baseline**. A conventional classical degree-bounded polynomial learner uses the same Gaussian elimination and can obtain the same query savings. Therefore **Q4 strong-classical full-cost 10× is NOT proven**. When a trusted classical candidate is available and independently source-verified, the runtime chooses it without inventing new features.

## Falsification controls

- Frozen linear feature grammar cannot fit newly discovered quadratic number relation.
- Source design matrix rank deficient: ABSTAIN.
- Separate source verifier refutes proposed feature law: ABSTAIN rather than refit on verifier.
- Unknown function differing at one genuinely unseen input is indistinguishable from all observed facts; unrestricted universal Q3 is mathematically impossible from finite source.
- Unstructured or partially observed graph monomials cannot be promoted to an invented ontology.
- Non-translation-invariant source rule cannot masquerade as a universal sequence stencil.
- Graph and symbolic target input sizes must have declared topology/position interface; no magical inference of target encoding.
- These oracles are author-constructed mathematical tasks, not original ARC-AGI-2 independent-author FIRST or frontier problems.

## Reproducible files

\`neumann1/causal_representation_inventor.py\`, \`neumann1/symmetry_orbit_inventor.py\`, \`neumann1/latent_graph_ontology.py\`; two production engine adapters; three corresponding independent tests and dedicated GitHub Actions.

**Gate status:** Q3 new feature and identifiable-ontology invention **scoped PASS**; Q6 cross-size graph/symbolic structural-transfer **scoped PASS**; complete autonomous unrestricted Q3, cross-ontology unrestricted Q6 and best-classical total Q4 **OPEN**.
