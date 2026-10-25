# NEUMANN 1 | Q3 RC33: ONE own-weight model infers unseen recursive grammars

**2026-10-25 · RESEARCH-ONLY DRAFT · no merge as full Q3.**

### What was actually learned
RC32 had separate PyTorch actor per target. This RC33 trains a SINGLE
amortized small PyTorch MLP actor on **1,800 different hidden grammars**,
using ONLY three opaque string source input/output observations for each
(ABC, BCA, CAB) and ZERO target RHS code labels. The actor learns 27-way
latent split selection; an explicit human-coded parser constructs the RHS
text from the source-output substring, and checks whether candidate
rewriting matches all three observed outputs. Training maximizes TOTAL
probability mass on all IO-compatible latent splits. This training feedback
DOES perform classical enumeration of 27 length triples. It is NOT freeform
neural invention of a foundational metasyntax.

### Strictly frozen BEFORE independent hidden-rule grade
Original PyTorch actor tensor SHA256
`5934c2825522982005a3587af7381bb68deb0bf15063f1d3894415e93d418c78`.
FIRST untouched heldout prediction SHA256
`77b968540818b5987bbcdb8b1a5d66d5316aeec865a51896770eef7baf1327e2`.
Actual full code, exact predictions, source data and original source SHA in
the complete conversation ZIP. Independent grade code only authored AFTER
these identities were frozen.

- Same learned weights, **NO unseen-task gradient steps**: **241/250
  observed-source-IO-compatible** generated rules; 1 ambiguity yields source
  correct but wrong actual hidden program, so **ONLY 240/250 exact hidden
  rule definitions / rigorous ALL finite source/depth inductive proofs**.
  Do not claim 241 all-length theorems.
- Unseen start strings A,B,C,ABAC,CABB,ACCB,BACAC and depths1..6:
  **10,092/10,500 exact emitted strings** in independent evaluator.
- Source training 1,800/1,800 exact; four independent initializations
  FIRST heldout compatible scores **241, 239, 240, 236 /250** (one model each).
  Corresponding UNTRAINED weights: **4,11,6,13/250**.
- **4/4 clean isolated from scratch retrain PASS**: exact Torch tensor
  equality and original first emitted program predictions, with NO gold
  oracle script copied to the learning directory.
- Strong CLASSICAL SAME-IO inverse parser tries 27 length triples:
  source-only rule-unique **249/250**; one task is logically underdetermined
  given only the original three observations, so fail-closed UNKNOWN unless
  extra trusted information. With ONE fully-accounted adaptively chosen new
  membership query it recovers **250/250 exact programs** in **0.004630 CPU
  seconds total** for all250. The trained model alone cost **3.9049 CPU
  seconds** plus runtime, so classical wins even without neural fit overhead.
  The extra classical oracle query is NOT free: compare 249/250 with no new
  queries before evaluating the 250/250 with one.
- Grammar expressivity bound: RHS length1..3 and fixed vocabulary ABC.
  Cannot express erasing, any RHS length4 or a fourth symbol D; the parser,
  alphabet, recursion and executor were fully human-provided. External-author
  tasks, universal Q3 ISA creation, Q4 all-in10x, Q6, Q7 frontier gap OPEN.

### Exact original artifact
`NEUMANN1_Q3_RC33_AMORTIZED_META_GRAMMAR_GENERALIZATION_20261025.zip`
**SHA256 c107eeb835867b2d86199a65826db3a6f48bb9c27914eda0f642f4e8a9ad32fb**
contains 25 files including actual FOUR Torch .pt tensors, source-only
training modules, first-frozen predictions, independent hidden grammar
author/grader, 5 tests, 4 fresh seed controls, strong classical baseline,
SHA manifest, REPRODUCE/RETRAIN shell scripts.
CLEAN extraction bash REPRODUCE.sh and CLEAN 4-retrain RETRAIN.sh PASS.
This GitHub PR contains compact runtime-proof and regression, no full weights.
