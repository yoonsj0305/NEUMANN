# NEUMANN 1 | Q3 Cross-Theory Math Generalization and New Constructor

2026-11-08. **SCOPED PASS. Global Q3/Q4/Q6 OPEN.**

## Scientific question

Can NEUMANN transfer source-discovered Boolean inclusion invariants into **unbounded integer arithmetic**, learn a reusable program constructor, and after a provable method failure select a DIFFERENT constructor and transfer across unseen function arities and thresholds with independent formal proof and fair classical controls?

All input source/target registries and code were frozen before untouched target documents were downloaded. Official SyGuS-Org/benchmarks original problems, pinned commit 13c8deb68a873635879c9a69bc78caebd340f646. **All integer inputs** means arbitrary mathematical Z3 Int values, not finite 4-bit enumerations. Programs were substituted into the original formal constraints.

## Frozen source from unrelated mathematical type

Prior Bool function meta-library at source SHA-256 0d322823dca4d4d0dbd26932a5cffa400475cad11c7582edeebd285e9e9fbc76 generated 16 executable 2-input truth functions and 32 safe laws. One learned OR law transfers to conditional integer expression correctness: if an integer result is chosen from two branch values, it must equal one branch. Z3 proved this over all Int and exhibited a counterexample against the incorrect assumption that both branches must equal the output.

The Boolean meta-closure and the integer adapter remain human-coded.

## Initial learned integer fold and universally quantified formula

Official source max2 and max3 originals. A human-coded 12-program fold grammar was searched against source formal specs. Four candidate programs satisfied max2; the first source-verified generalization to max3 was frozen SHA-256 b9690bb6a14a565e5ecb3b11abf09a9d671ad757d0673a537108b95c6c5cbde4.

- FIRST #42436072641: 12/12 unseen max4..max15 official original problems passed independent unbounded integer Z3 proof. Learned 12 proof requests, 68.46296 ms; same-language cold 72 requests, 340.92350 ms.
- FIRST #42436279062: differently named max16..max20 5/5 passed. Out-of-family arraysearch 0/4 eligible (one arity parsing error); other sum/guard 0/2 eligible (two constraint-interface errors). Never call these non-results PASS.
- FIRST #42436418885: source-verified selector satisfies commutativity, associativity, idempotence, selectivity, upper bound and monotonicity. An incorrectly hypothesized zero identity was REFUTED. Five Z3-proven induction-step premises plus ordinary induction prove the frozen max-fold works for **any finite input arity >=1 and any integer inputs**. The proof shape was designed by a human.

## Method failure led to a different EXECUTABLE control structure

Previous source-learned max-fold failed with an actual Z3 SAT counterexample on two other source originals for a conditional adjacent-pair function.

A HUMAN-CODED 16-option constructor-grammar search identified a NEW executable first-hit scan control structure: from left to right, compute each adjacent pair's sum and return the first one exceeding a threshold, else zero. The parameter threshold remains a typed hole bound from numerals in the *target mathematical specification*, not the filename or a hidden reference solution.

New constructor frozen SHA-256 d4fa44c78bf4e37d6979b04cb61e423936683d95f327ab563d1aa518a7bfd325 before any new target document.

FIRST #42436650641: **13/13** untouched formal LIA originals proven correct over ALL integer values, including **7/7 with a NEW threshold 15**, after learning on source threshold 5. Same 16-program classical grammar also 13/13.

- New constructor: 13 Z3 requests, 33.49535 ms.
- Same-language cold baseline: 117 Z3 requests, 379.98239 ms.
- Target-only Z3 time improvement: **11.3443x**.
- Including the measured initial scan source-discovery Z3 time 24.7325 ms: **6.5258x**.
- Initial fold source-proof amortization across its first 12 targets: **4.0145x**; both source-proven constructor studies combined: **5.0360x**.
- THESE ARE SMT PROOF TIMES ONLY, not end-to-end compute time, not network/preprocessing/CI costs or prior Boolean research time. Overall Q4 10x is OPEN.

## Independent original verification

FIRST proof audit #42436876716 uses a **separately implemented** original SMT translator and pinned Z3. It takes the 12 initial max, 5 differently named max, and 13 first-hit scan external original programs, checks original file SHA-256, inserts generated programs into original mathematical constraints, and checks UNSAT of the negation.

**30 / 30 distinct official external original programs independently proven over unbounded Int; 0 incorrect claims and 0 verifier errors.** Two deliberately FALSE programs produced 2/2 SAT counterexamples. The benchmark publisher is still one provider, so independent-author generalization has not been established.

## Root cause and failures

Old Boolean rule and max-fold are NOT generic program-invention policies. They do not solve source arraysearch or adjacent-pair first-hit tasks. Search-policy content had to change from folding a binary selector to executing ordered conditional checks. The system selected and verified the new method only WITHIN a human-provided 16-template grammar. The source code still dictates what classes of procedures are imaginable.

The old original error counts (1 unsupported arity and 2 too-few-constraints) remain immutable; do not retroactively correct them for a first-run score.

## Priority

1. Synthesize the meta-constructor CONTROL GRAPH ITSELF from proof and counterexample structure, rather than choosing a human-written fold/scan option.
2. Target a genuinely separately authored benchmark across Int, strings, graphs and constraints with frozen source-only method.
3. Use total amortized cost: method discovery + typed compilation + original proof + fallback + network/CI. Prioritize safe classical degraded mode when evidence is insufficient.
4. Automatically discover semantic invariants beyond OR-inclusion and algebraic fold, e.g. monotonicity, extrema, symmetry and injectivity, with independent certificates.

## Explicit conclusion

**SCOPED PASS:** BV-to-unbounded-Int theorem, unbounded-arity max fold, old-method-failure-triggered new scan selection, new threshold 15 transfer, and 30 independent Z3 original proofs.

**GLOBAL Q3 self-invention, Q4 end-to-end 10x, Q6 independent-author cross-domain are OPEN.**

Run evidence:
- https://github.com/yoonsj0305/NEUMANN/actions/runs/42436072641
- https://github.com/yoonsj0305/NEUMANN/actions/runs/42436279062
- https://github.com/yoonsj0305/NEUMANN/actions/runs/42436418885
- https://github.com/yoonsj0305/NEUMANN/actions/runs/42436650641
- https://github.com/yoonsj0305/NEUMANN/actions/runs/42436876716
