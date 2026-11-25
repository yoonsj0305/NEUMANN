# NEUMANN 1 | Q3 Meta-Method Invention from Small Executable Programs
2026-11-08 | Research extension of PR #732

## The previously missing causal mechanism
Earlier Q3 branches picked among three predesigned strategies or constructed program instances from specific hand-coded mathematical classes. The core unclosed question is whether **previously solved tasks can generate a reusable executable procedure for tasks of a larger arity**. Here the source learner constructs both an initial Boolean circuit **B** and an unknown binary continuation circuit **H** from exact input/output evidence, then persists that generated constructor in both live engines.

The only gate built into the expression language is **NAND**; no XOR/AND/OR/NOR/implication transition is supplied as the answer. Semantic enumeration synthesizes all sixteen possible two-input Boolean maps into NAND-only expression trees. A reusable method object is deposited in the engine inventory; the same learned method executes unseen arities without additional oracle calls.

## Conditional theorem explaining transfer
Let `B: {0,1}² → {0,1}` be **surjective** and suppose the true source family follows the recurrence:

`f₂(x₁,x₂)=B(x₁,x₂)`

`f_(n+1)(x₁,…,x_(n+1)) = H(f_n(x₁,…,x_n),x_(n+1))`

with the SAME unknown Boolean transition `H` for all n ≥ 2.

A full arity-2 truth table uniquely gives B. Because B produces both 0 and 1, for each state s and next input b, some pair (x,y) satisfies B(x,y)=s. Consequently the full arity-3 truth table determines **each of the four values H(s,b)**. Contradictions in this table falsify the proposed one-bit continuation language. A full arity-4 truth table is checked as separate source evidence.

Given the recurrence axiom and exact B,H, an elementary induction proves the invented program correct for ALL n≥2. But the learner **cannot establish the recurrence axiom for arbitrary functions** by checking the first three lengths; a source-identical counterexample can diverge at length 5. This conditional guarantee is mathematical, not a universal autonomous intelligence result.

## Synthetic exhaustive class experiment
File `research/q3/q3_boolean_meta_fold_first.py` and frozen snapshot `research/q3/q3_boolean_meta_fold_first_results.json`.

- Enumerated all 16 possible two-input Boolean base functions. Two constants are excluded because H would be underidentified; **14 remain**.
- For each of these 14 base functions, enumerated all **16 different transition functions** as independent AUTHOR-SUPPLIED hidden oracles.
- The inventor received only the **complete source tables for lengths 2/3/4**, 4+8+16=28 observations per problem, plus a common human-supplied fold grammar. It was NOT passed the 224 enumerated function IDs or transition formulas.
- Inferred **224/224** different reusable procedure constructors, with **6,272** original source observations.
- The source-frozen methods correctly answered **50,176/50,176** withheld target inputs for lengths 5,6,7, across all 224 families.
- Maximum NAND count in either compiled base or transition expression was 12 in this tiny grammar (local measured). Small expressions are generated at runtime rather than selected from a 224-entry method lookup table.
- Both `NeumannEngine` and `RegistryEngine` now expose `learn_boolean_constructor` and `execute_boolean_constructor`, storing the discovered method fingerprint for reuse without repeating source queries.
- An arity-3 nonfold counterexample and arity-4 disagreement correctly cause refusal.
- **Adversarial negative:** A hidden original program that agrees with true parity on all source lengths 2,3,4 but differs on one length-5 input is accepted and predicts that target wrongly. This falsifies an unconditional generalization claim.

## Relation to the actual NEUMANN research question
This is more than source-label routing: the engine forms a **new executable meta-program H** from previously solved smaller problems and uses that program recursively on targets of previously unobserved input sizes. It demonstrates a real, bounded self-extension of the solution program language.

Nevertheless the meta-grammar itself, the use of NAND, the one-bit state limitation, the source arities, and the complete-truth-table acquisition were written by humans. The learner did **not** autonomously invent its own meta-language, new meta-search algorithm, or a universally valid recursion axiom. This is a scoped mechanism, **not global Q3 PASS**.

### Cost and baseline honesty
A classical recurrence-identification algorithm given the same one-bit fold prior can recover B and H just as efficiently; a Boolean synthesis tool can likewise compile any of these functions. The 50,176 correct unseen predictions and 6,272 source observations are separate counts, NOT a 10× CPU/GPU advantage over such a baseline. Exact full-target tabulation would require 50,176 additional target oracle evaluations, but it is a different resource and cannot be equated to model FLOPs or inference speed. Q4 remains OPEN.

### Generalization honesty
224 different base/transition pairs span **one explicitly bounded compositional class**. This is arity extrapolation and constructor generality, not independent-author transfer to graphs, ARC, mathematics broadly, or frontier scientific discovery. Q6 global remains OPEN.

## Next decisive gate, not more in-family seed runs
Dynamically learn the **state dimension and the recursion grammar itself**, from independent-author black-box transformations. Source should contain both successful and failed program forms; NEUMANN must generate a new state representation and edit its method induction algorithm based on counterexamples. Freeze before independent targets and compare against classical automata learning, meta-program synthesis, and ARC-level general solvers at matched full cost.
