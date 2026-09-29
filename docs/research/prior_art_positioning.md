# Prior-Art Positioning — Working Map

Status: working research map, not a novelty opinion or patent analysis.

## Operating assumption

For research design purposes, NEUMANN should assume that **most component ideas already have strong prior art**.

The burden is therefore not to find a new label for:

- neuro-symbolic reasoning
- solver use
- intermediate representations
- program execution
- verification
- structure discovery

but to formulate and test a narrower claim that survives comparison with those traditions.

## High-risk neighboring lines

Working watchlist supplied by the current literature review:

- SELF-DISCOVER
- PAL
- Program of Thoughts
- Logic-LM
- LINC
- AlphaGeometry
- IR2Solve
- COVER
- related symbolic-chain / verifier / solver-routing work
- mature solver presolve/ordering and learned presolve (including L2P-MIP)
- e-graphs and equality saturation for representation and reuse

These names are maintained here as a review checklist.

`SymbolLKG` was removed from the bibliography watchlist because its original
source could not be independently verified. Do not restore without a primary
source. IR2Solve/COVER details also require primary-source verification before
quoting any number, submission date or precise mechanism.

Performance numbers, dates, exact mechanisms, and novelty comparisons must be independently verified before publication.

## NEUMANN positioning rule

Do not claim novelty from:

    Problem -> structure -> reasoning

or:

    Problem -> symbolic representation -> solver

or:

    Problem -> IR -> compiler -> verifier

or:

    neural proposal + symbolic execution

in isolation.

Candidate research territory:

    Problem
      -> discover structure
      -> remove computationally unnecessary degrees of freedom
      -> emit a sufficient reduction certificate
      -> solve only the retained structure
      -> reconstruct
      -> independently verify the original problem
      -> measure whether compute scaling changes

## Strongest candidate novelty questions

1. Can a learned system discover a **minimal sufficient computational structure**, rather than merely formalize the original structure?

2. Can reductions be accompanied by machine-checkable **sufficiency certificates** so learned compression never holds execution authority?

3. At iso-verified-accuracy, how much of the apparent problem size can be removed before solving?

4. Does verified reasoning work empirically scale with retained computational degrees of freedom rather than apparent problem size?

5. Does Structural Compression change the observed compute-growth curve over increasing problem complexity?

Novelty is not the gate for choosing an experiment. The primary decision is
verified capability at **lower measured total compute** versus a strong,
deployable baseline, including the solver's native presolve, discovery,
repair and verification. Reuse a mature method whenever it wins that test.
Separate diagnostic per-instance oracles from deployable policy costs.

## Novelty discipline

Use the following language internally:

- "candidate differentiator"
- "research hypothesis"
- "working novelty axis"
- "no direct duplicate found in current review"

Avoid:

- "first"
- "novel architecture"
- "unprecedented"
- "no prior work"

unless a systematic literature and patent review supports the statement.
