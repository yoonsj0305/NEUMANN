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
- exact and learned MIS reductions: KaMIS and LearnAndReduce
- e-graphs and equality saturation for representation and reuse

These names are maintained here as a review checklist.

`SymbolLKG` was removed from the bibliography watchlist because its original
source could not be independently verified. Do not restore without a primary
source. IR2Solve/COVER details also require primary-source verification before
quoting any number, submission date or precise mechanism.

Performance numbers, dates, exact mechanisms, and novelty comparisons must be independently verified before publication.

## Graph-specific boundary confirmed after v0.0.73

The primary paper by Großmann, Langedal and Schulz,
*Accelerating Reductions Using Graph Neural Networks for the Maximum Weight
Independent Set Problem* (ACDA 2025; extended arXiv:2412.14198), and its
official `KarlsruheMIS/LearnAndReduce` repository already use a GNN as a
screening mechanism for expensive reduction rules. They retain exact
reduction semantics and lift the reduced result to the original graph.
Their graph-specific combination is substantially closer than a generic
"neural proposal + solver" citation. Sources:
https://arxiv.org/abs/2412.14198 and
https://github.com/KarlsruheMIS/LearnAndReduce . Reuse type: ideas and
baseline specification only; **no code, data or weights copied**. The
repository advertises MIT licensing, but check exact components and
submodules before any future code import.

KaMIS itself provides exact `weighted_branch_reduce` and `struction`
executors as well as heuristic programs such as `redumis`. Do not
mistake a heuristic solution for certified optimum in an iso-capability
comparison. Its default kernelization may itself remove twins and much
more; compare a native/default exact configuration before claiming a
benefit from our own simple quotient. See
https://github.com/KarlsruheMIS/KaMIS . The repository documents MIT
with some BSD-3-Clause components; license and commit checks are required
at integration. No KaMIS binary is in the current v0.0.73 experiment.

Consequence: "a GNN predicts profitable graph reduction locations" and
"a learned screen plus exact graph reductions" are **not** NEUMANN novelty
claims. A new graph-learning experiment needs a precisely identified
residual bottleneck not solved by LearnAndReduce and a full-cost comparison
against its applicable configuration. The v0.0.73 four-network negative
gate provides no such headroom. This does not settle NEUMANN's broader
multi-domain, reusable minimum-compute question.

## NEUMANN positioning rule

### Elimination-order boundary (v0.0.74)

Kask, Gelfand, Otten and Dechter, *Pushing the Power of Stochastic Greedy
Ordering Schemes for Inference in Graphical Models* (AAAI 2011), studies
iterative randomized greedy elimination orders minimizing induced width
and state-space size: https://ojs.aaai.org/index.php/AAAI/article/view/7828 .
Khakhulin, Schutski and Oseledets, *Graph Convolutional Policy for Solving
Tree Decomposition via Reinforcement Learning Heuristics* (2019), is a
direct learned-decomposition predecessor: https://arxiv.org/abs/1910.08371 .
Song et al., *Learning Variable Ordering Heuristics for Solving Constraint
Satisfaction Problems* (2019), learns ordering for backtracking CSP search:
https://arxiv.org/abs/1912.10762 . CSP branching is not sum-product elimination.
Do not call learned elimination or learned ordering a NEUMANN invention.
Current reuse: ideas/baseline specification only; no external code/data/weights.
v0.0.74 is a bounded **unlearned** complete-cost screening experiment, not a
comparison to these full learned systems or a new structure discovery method.

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
