# NEUMANN 1 — Q3 learned source rewriting, 2026-10-21 decision

## Reproducible hard evidence

- Original raw-state transition learner (official **PR430 / Action 39611027543**) uses **no supplied symmetry-equivalence pairs**. It receives the program transition source sampled at states, a disclosed goal-variable anchor, and a FIXED designer-selected polynomial primitive vocabulary up to degree 3. Adam learned composite integer-polynomial relations across three synthetic programs, each repeated with 8 seeds.
- Successful exact source formula compilation:
  - quadratic accumulator: \`h(x,y) = y - x*x\`
  - cubic accumulator: \`h(x,y) = y - x*x*x\`
  - bilinear running product: \`h(x,y,z) = z - x*y\`
- Trained expression **24/24** independent symbolic exact universal polynomial Pre/Trans/Post proofs. Linear-only degree-1 fitting **0/24**. Paired frozen random untrained coefficient ablation **0/24**.
- Strongest equal-operator polynomial exact classical solver **24/24**, with same transition samples, same monomial dictionary, same exact original verification. Measured local candidate synthesis/matching stage in CI: learned fitting 5230.079752 ms and exact classical synthesis 630.447896 ms summed across all 24 runs. These are **not equal full end-to-end system wall**; no 10x or speed superiority.
- First-three-transition sample ambiguity was tested: a different genuine polynomial transition yields identical first three data rows yet breaks the trained candidate at \`x=3\` (symbolic delta = 6). **No learned candidate can replace authoritative original source verification.**
- Official independently archived raw JSON (SHA-256: \`07a914d0f391119d0089b25fa59afdea0fce87b2aaad1e30e9ee34b3adc14d97\`) was reused WITHOUT modification for **PR431 / Action 39611724354**.
- Independent source-compiler proved **24/24** learned ASTs transform original program states to a single variable \`q=h(s)\`, with \`Pre(q): q=0\`, \`Trans(q,q'): q'=q\`, \`Goal(q): q=0\`. The compiler checks exact universal commuting diagram \`h(T_original(s))=T_abstract(h(s))\`, original pre, original goal and abstraction surjectivity. This is exact for the three synthetic source families and their specified safety goals. Strong classical exact expressions independently compile to THE SAME one-state programs, **24/24**.

## Model-scientific verdict

**SCOPED LEARNED NONLINEAR EXPRESSION GENERATION & SOURCE-LEVEL COMPILATION: PASS.**

**GLOBAL Q3 (new learned source-conditioned representation unavailable to strongest classical method): OPEN.**

**Q1/Q4/Q5 (better total computation than strongest classical alternative, including training amortization and proof): OPEN.**

**Q2/Q6/Q7 (transfer to unrelated, first-source-body-blind real program families): OPEN.**

The model learned COEFFICIENTS of composed polynomial expressions from transitions. Multiplication was a supplied grammar primitive. This is **not autonomous discovery of a new mathematical primitive, full architecture invention, or frontier superiority**. Polynomial exact baseline was cheaper in this measured substage and must remain in the system.

## Minimal next decisive research gate

Freeze actual external **unseen** original programs and an independent strong baseline BEFORE opening their sources. A new model must learn a **source-conditioned transformation not already supplied as an adequate fixed operator vocabulary**, and:
1. Pass the unchanged original-source semantic commuting proof and original target proof.
2. Remove real expensive computation on that original workload relative to strongest baseline.
3. Pass learned-module knockout (without the learner, the advantage vanishes).
4. Be independently replicated on a second unrelated source family, including all attempts, unsupported cases and timeouts.
5. Report paired repeated wall, resource usage, training, search, failures, proof and amortized cost at identical hardware/software settings.

**Falsification/stop rule:** If exact classic synthesis matches or exceeds learned success at equal or lower complete cost, retain the classical path as the degraded/default mode. Never scale gradient steps or create new representation branches solely to improve weak-baseline ratios.

## Safety / degraded behavior

Any failed exact equivalence, unknown proof, source identity mismatch, or missing independent proof must RETURN \`UNKNOWN\` or fall back to certified classical source solver; never claim SAFE. The correct atomic interface is \`(source_sha, learned_AST, proposed_abstract_program, exact_original_semantic_certificate, goal_certificate, detailed_cost_receipt)\`.
