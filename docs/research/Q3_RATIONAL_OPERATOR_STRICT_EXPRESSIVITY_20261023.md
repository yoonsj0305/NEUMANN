# NEUMANN Q3: STRICT expressive-power separation and verified rational AST construction

2026-10-23 KST. Original code [PR #534](https://github.com/yoonsj0305/NEUMANN/pull/534). Dedicated CI [run #39894504718](https://github.com/yoonsj0305/NEUMANN/actions/runs/39894504718): **SUCCESS**. First proof+synthetic case JSON SHA256 `aae6c23f1b485596a5ed0295c55951dcfcc540f6d07ec0d175ec679fa9b38ccf`.

## Core all-parameter theorem
Take any nonzero rational `h` and the rational map `F_h(x)=(x²+h²)/(2x)` over the rational function field `Q(x)`. The source has a nonremovable simple pole at x=0 (residue h²/2 ≠0). Let `p∈Q[x]` have degree `n>=1` and leading coefficient `a_n !=0`. The composition `p(F_h(x))` has a pole of EXACT order n at x=0, because the leading term `a_n F_h(x)^n` has order n and lower terms have strictly smaller orders and cannot cancel its leading singular coefficient. But `p(x)^2` is polynomial and finite at x=0, hence no equality in Q(x):

`forall p∈Q[x], deg(p)>=1: p∘F_h != p²`.

Constant p=0 or p=1 trivially satisfy but are goal-vacuous and excluded explicitly. This argument covers **all finite polynomial degrees**, not just a pre-enumerated depth budget. It is a complete proof of inability for this precise polynomial representation class and dynamical source family, not a general universal limitation of neural networks.

## Witness with strictly richer syntax
Add the operator **DIV** (rational expression) to `CONST, VAR, ADD, SUB, MUL`. Construct

`g_h(x)=(x+h)/(x-h)`

as an executable compositional graph: `DIV(ADD(VAR,h), SUB(VAR,h))`. Exact identity over Q(h,x):

`g_h(F_h(x)) = ((x+h)/(x-h))² = g_h(x)²`.

The reciprocal `1/g_h(x)=(x-h)/(x+h)` is another independently certified solution. The same identity iterates:

`g_h(F_h^n(x))=g_h(x)^(2^n)`

by induction for all integers n>=0 and inputs where compositions are defined. This is classical algebra; no new scientific priority/novelty claim.

## Actual executable source discovery and controls
An independent classical program enumerator generated a source-specific AST of the form `DIV(ADD(VAR,p),ADD(VAR,q))` without being supplied the generator's hidden h label. SymPy checked the exact rational-functional identity before admission. Twelve synthetic source problems `h=1..12`: **12/12 exact certified rational ASTs**. A second strong **equal-authority classical specialist** extracts k=h² from source and uses integer-square-root with the same exact verifier: **12/12**, so no neural-only or even classical-program-exclusive task gains. One universal parametric SymPy identity and a separate machine-checked affine-polynomial impossibility verify the constructive proof.

Six synthetic **nonsquare integer k** controls `k∈{2,3,5,7,11,15}` were rejected **6/6 by the limited integer-shift quotient AST enumerator and square-root specialist**. Do **NOT** claim that all rational expressions or every possible Möbius expression are impossible on those controls. 0 wrong accepted programs in this registered synthetic cohort.

## Scientific interpretation
- **PASS:** strict representation-class expressivity gap for nonconstant polynomial abstractions.
- **PASS:** richer DIV compositional executable grammar admits exact nonvacuous useful relation and sound iteration theorem.
- **PASS:** 12/12 positive conditional classical AST synthesis, 6/6 limited-family negative admissions avoided.
- **OPEN:** an actually TRAINED agent autonomously proposes **DIV** without its human-prescribed new grammar.
- **OPEN:** independently authored external original program successes, cross-author learned transfer, strong classical specialist cost/accuracy dominance, whole NEUMANN >=10x cost, frontier parity.

This separates *extending a representational language to make a previously impossible operator feasible* from *learning to choose or invent that extension*. Prior PR #533's coefficient learner could not solve this family because it only emits polynomial affine `e=1+a*x`; no amount of retraining or wider coefficient range changes the all-degree impossibility.

## Roadmap without artificial new passes
A new G1 learner would have to output a typed executable AST with dynamically chosen operators/arity, not pick a rule from a closed fixed list; certify against original semantics; acquire or propose genuine new syntax when heldout tasks demand it; and beat a classical synthesis tool with the identical extended AST grammar under all-in cost. Until that actually happens, global Q3 learned novelty, Q6 transfer and Q4 frontier/all-cost remain OPEN. No GPU, paid API or neural model was involved in the proof experiment.

**Source code** `research/q3/compositional_rational_necessity.py` and **CI** `.github/workflows/q3_rational_necessity_original_math.yml`, GitHub refs in the PR. Not a third-party source benchmark, all sample cases synthetically generated from declared formulas.
