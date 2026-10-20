# NEUMANN 1 Q3 | First original CI for teacher-free behavioral-loss conditional AST learner

2026-10-20 KST. **Local development already tested and observed the outcome, so this is NOT prospective/blind for synthetic problems.** The file freezes the GitHub Actions full-verifier replication, including an honest expected failure of independently factorized AST logits and a stronger shape-conditional policy. Do not call this a novel mathematical primitive invention.

## One decisive architectural question

Can an actual gradient learner *select its first AST from only example-based loss*, without receiving a correct AST as a teacher/pseudolabel, when its decoder models correlations between tree shape and child decisions? Compared with old PR #299 that DISCOVERED the program via independent stochastic search and ONLY THEN copied exact discovered token IDs into 29 neural logits, the target policy receives **no winning program ID** at any stage.

## Frozen architecture, limitations and attribution

The actual developmental dataset is the same author-created counter-family from PR #299, NOT a new independent real source or blind transfer:
- train k=2..6, exactly 48 true counter recurrence steps for each k (240 observed (a,b,r) triples, no use of Python '%' for training labels)
- heldout k=7,8,9,11, 100 untouched counter recurrence steps each, same author-created program family.
- DSL EXACT previous PR #299: 5 binary tree shapes, 3 internal operator slots from {add,sub,mul,Int div}, 4 leaves from {a,b,1}. Complete `5×4^3×3^4=25,920` programs, typed well, `mod` is NOT a primitive. The successful AST is expressible in this grammar. **All 25,920 candidate programs are evaluated on the training traces up front**, which is complete classical exploration. This step is NOT learned and allows the simplest same-information exact classical solver to succeed with zero model training.
- empirical loss of each AST `L=log(1+mean(abs(program(a,b)-r)))+0.1*(1-exact-match fraction)`. Finite numerical evaluator clips intermediate values to ±10000 for stability. Compute tempered behavior posterior `q(AST)∝exp(-(L-min L)/T)`, fixed `T=0.02` determined from local development. This is a **full-program classical behavioral score distribution**, not a gold AST label nor a neural-only discovery.
- 29-parameter baseline `p(shape)×∏p(op slot)×∏p(leaf slot)` has no way to associate a token with chosen shape. The exactly equivalent reward-weighted behavioral posterior, fit to this independent factorization with gradient Adam (80 steps), yields an incorrect hybrid greedy AST. This failure MUST be preserved.
- New 125-parameter **conditional policy** `p(shape)×∏p(op slot|shape)×∏p(leaf slot|shape)` captures correlated binding of child variables to tree shape. Fit SAME behavioral posterior distribution, via differentiable weighted cross-entropy **without ANY source of correct AST token supervision**, CPU torch Adam, 80 steps lr=0.2. Freeze weights and decode greedy. **The only empirical supervision is program output error on training source states.** No recurrent policy and no newly learned primitive beyond the full closure are claimed.
- Mandatory ablations: untrained greedy wrong, independent 29 greedy wrong, full classical minimum-loss program perfect on heldout, conditional 125 greedy perfect. A shuffled-output negative control on the *same training inputs*, with original heldout kept sealed, should not produce a semantically valid generalizing AST; if it does, report rather than hide. Capturing as development diagnostic is fine.
- For each heldout k, compile the learned AST into exact Z3 syntax and certify full unchanged synthetic original Pre/Trans/Post initial/consecution/safety negated VC UNSAT 3/3 with independent official cvc5 v1.4.2 UNSAT 3/3. A source helper missing learned modulo relation must fail Post. No altered source semantics.
- Measure **candidate grammar enumeration and behavioral score time** plus **gradient fitting time**, not just cheap model inference. Classical full enumeration knows same 240 source labels and may find exact formula before gradient training. Always report this classical dominate/no unique capability.
- No purchased GPU/API, all runs CPU; neural weights & receipt hashed.
- Do not retest already opened external `mannadiv` as if independent: earlier PR #299 Z3 yielded redundant lemma and independent cvc5 returned UNKNOWN.

## Accepted scoped outcome and explicit vetoes

`Q3_CATEGORICAL_BEHAVIORAL_AST_PROPOSAL_NO_GOLD_AST = DEVELOPMENT_SCOPED_PASS` only if learned shape-conditional final greedy AST matches unseen source recurrence behaviors and original synthetic Z3+cvc5 3VCs for all 4 heldout, while shape-independent and untrained 29 fail under identical inputs/training and **no discrete program winner AST is furnished as a training target**.

`Q3_GRADIENT_LEARNED_NEW_OPERATOR_OUTSIDE_BASE_DSL=FALSE` (all candidate ASTs belong to frozen 25,920), `Q3_NEURAL_ONLY_INITIAL_STRUCTURE_DISCOVERY_OVER_STRONG_CLASSICAL=FALSE` (full classical grammar enumerated to make scores), `Q3_UNSEEN_ORIGINAL_SOURCE_FAMILY_BLIND=NOT_TESTED`, `Q4_ALL_IN_10X=NOT_PROVEN`, `GLOBAL_Q1–Q7=OPEN`. Retain all historical first failures. Do not tune on same heldout and rebrand success as prospective.

This is an honest architecture step: **learn correlations in compositional structure from behavioral feedback without a gold AST**, *not* evidence that a neural model was superior to a complete classical solver.