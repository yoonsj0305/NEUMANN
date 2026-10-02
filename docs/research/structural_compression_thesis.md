> Historical mechanism thesis, retained through v104. The user-frozen
> [Frozen North Star](frozen_north_star.md), dated 2026-10-02, is now the highest
> authority. Structural compression is a hypothesis/mechanism, not a permanently
> required architecture or an LP-only objective. Q1–Q7 are fixed under the new
> namespace; see [current gates](core_question_gates.md). The historical text and
> original decisions below are retained, not promoted to frontier proof.

# NEUMANN 1 Research Thesis — Structural Compression

Status: research direction freeze after v0.0.31

## Core redefinition

NEUMANN 1 is not defined as:

- LLM + symbolic solver
- structure-first reasoning alone
- IR generation alone
- solver routing alone
- verification alone

Those components should be treated as substantially covered by prior work unless a narrower claim is independently established.

NEUMANN 1 is now centered on:

> **Structural Compression: discover a minimal sufficient computational structure before solving, so the system removes work that does not need to be performed.**

Canonical pipeline:

    Raw Problem
        ↓
    Semantic Parse
        ↓
    Structural Discovery
        ↓
    Structural Compression
        ↓
    Minimal Structural IR
        ↓
    Algorithm / Solver Router
        ↓
    Deterministic / specialized execution
        ↓
    Independent Verification
        ↓
    Result
        ↓
    Canonical Structure Memory

## Distinction that matters

    Structure discovery ≠ Structural compression

Structure discovery asks:

> What structure is present?

Structural compression asks:

> Which variables, constraints, dependencies, distinctions, or degrees of freedom are actually necessary for correct execution and verification?

A system that rewrites twelve variables into a twelve-variable JSON object has formalized the problem but has not necessarily compressed it.

A Structural Compression system should be able to transform, where valid:

    12 apparent variables
        ↓ symmetry / dependency / invariant analysis
        ↓ safe elimination
        ↓ canonicalization
        ↓
    3 computational degrees of freedom

while preserving enough information to reconstruct and verify the original solution.

## Minimal Structural IR

The target object is not merely a serialization format.

A Minimal Structural IR may contain:

- retained variables
- eliminated variables with reconstruction rules
- constraints
- reduced constraints
- dependencies
- invariants
- symmetries
- equivalence classes
- redundant-variable certificates
- degrees of freedom
- objective
- uncertainty / unresolved facts
- applicable algorithms
- solver preconditions
- verification conditions
- reconstruction conditions
- provenance for each reduction

The word **minimal** is a research target, not a claim that global minimum representations can always be found.

Until a stronger proof exists, NEUMANN must distinguish:

- globally minimal
- minimal under a declared transformation system
- locally irreducible
- merely reduced

## Primary research question

> **Can an AI reduce reasoning cost by discovering a minimal sufficient computational structure before solving?**

Stronger scaling question:

> **Does structural compression change how required reasoning compute grows with problem complexity?**

Operational version:

Let:

- (P_n) be a problem whose apparent size is (n)
- (S(P_n)) be a sufficient structural representation
- (k(P_n)) be the retained computational degrees of freedom after valid compression
- (C_N) be learned / neural work
- (C_D) be deterministic compression, execution, and verification work

The central empirical question is not merely whether:

    compressed path < direct learned path

for one benchmark.

It is whether there exist problem families where:

    k(P_n) grows more slowly than n

and this reduction causes the verified total work of the structural path to scale more favorably than a non-compressing baseline.

## Structural Compression primitives

Candidate transformations include:

### Variable elimination
Remove variables exactly reconstructible from retained variables.

### Dependency reduction
Collapse dependency chains that do not need independent reasoning.

### Invariant discovery
Replace many state variables with conserved or sufficient quantities.

### Symmetry detection
Identify states or variables that are equivalent under a transformation group.

### Equivalence-class formation
Operate on classes rather than repeated interchangeable entities.

### Redundant-constraint removal
Delete constraints implied by the retained set.

### Canonicalization
Map many surface forms to one execution-equivalent structure.

### Dimensionality reduction
Reduce effective computational dimension while preserving exact task sufficiency.

These operations must produce evidence that an independent verifier can check.

## Sufficiency before minimality

Compression is invalid if it removes information required for correct solution or verification.

Therefore the order of authority is:

    candidate compression
        ↓
    sufficiency check
        ↓
    execution
        ↓
    reconstruction
        ↓
    independent verification

Only after sufficiency is established should reduction magnitude be rewarded.

NEUMANN must never optimize compression ratio at the cost of silent semantic loss.

## Compression certificate

Every nontrivial reduction should carry a machine-checkable certificate containing at least:

- original structure identity
- reduced structure identity
- retained variables
- eliminated variables
- reconstruction map
- removed constraints
- justification for each removal
- declared invariants / symmetries used
- solver preconditions
- verification obligations

The verifier should be able to reject an invalid compression without trusting the learned proposer.

This extends the existing principle:

> **Learned Suggestion ≠ Execution Authority**

to:

> **Learned Compression Proposal ≠ Valid Reduction**

## Primary metrics

NEUMANN should report at least four separate layers of cost.

### 1. Apparent problem size

Examples:

- token / character count
- variables
- constraints
- graph nodes / edges
- search branching factors

### 2. Retained computational structure

Examples:

- retained variables
- retained independent constraints
- effective degrees of freedom
- reduced graph size
- canonical-state count

### 3. Learned work

Examples:

- parameters
- learned weighted-sum proxy
- model calls
- tokens where applicable
- diagnostic latency

### 4. Deterministic work

Examples:

- compiler steps
- elimination steps
- solver operations
- search expansions
- verifier operations

Do not collapse unlike units into a single synthetic score unless a defensible cost model is explicitly defined.

## Core ratios

Useful descriptive quantities:

    variable compression ratio
      = original variable count / retained variable count

    constraint compression ratio
      = original constraint count / retained independent constraint count

    degree-of-freedom reduction
      = original apparent DOF - retained DOF

    solver-work reduction
      = baseline solver work / compressed solver work

    verified retention
      = verified solutions after compression / verified baseline solutions

A high compression ratio is meaningless if verified retention falls.

## Scaling target

The strongest future result would not be:

> compression saved 40% on one fixed benchmark.

It would be evidence that, for a controlled family:

    C_baseline(n) ~ O(f(n))

while:

    C_compressed(n) ~ O(g(k(n)))

with empirically measured:

    k(n) << n

and a slower observed growth curve over a pre-registered range.

This is the scaling-exponent question.

## Relationship to v0.0.26–v0.0.31

v0.0.26 showed amortization from exact structure reuse.

v0.0.27–v0.0.28 established learned-proposal measurement and authority boundaries.

v0.0.29–v0.0.31 showed that, on controlled 2x2 linear systems, allocating small learned models to structure recognition can preserve much more verified task quality than asking matched models to predict final answers directly.

Those versions did **not** yet test Structural Compression.

They are now treated as enabling infrastructure and motivation, not the central novelty claim.

## Novelty posture

NEUMANN should assume that most individual components have substantial prior art.

Working prior-art watchlist includes:

- structure-discovery reasoning
- LLM-to-symbolic formalization
- program-aided language models
- neural + symbolic execution
- typed IR + solver compilation
- dynamic solver routing
- independent verification
- structure reuse

The research should not claim novelty from the existence of these components.

The candidate differentiator to test is their use in a system whose explicit objective is:

> **remove unnecessary computational degrees of freedom before execution, measure the reduction, certify sufficiency, and test whether the reduction changes verified compute scaling.**

No novelty claim is considered established without a systematic literature review and, if relevant, patent review.
