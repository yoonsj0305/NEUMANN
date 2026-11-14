# Q3 RC34–RC35 | decisive grammar-class failure and learned context expansion
2026-10-25 · RESEARCH-ONLY, Draft not merged. Frozen North Star unchanged.

## RC34: actual existing ownweight meta fails on unseen grammar types
The *original identical RC33 trained checkpoint* SHA
`5934c2825522982005a3587af7381bb68deb0bf15063f1d3894415e93d418c78`
was frozen, no refit, then assessed on 288 newly generated opaque I/O tasks:
96 ERASING (epsilon rules), 96 RHS width4, and 96 ABCD NEW ALPHABET.
Hidden correct actual learned outputs: only **7/288**, all strict admission
checks UNKNOWN/not sufficient for true globally certified new syntax.

Classic bounded RHS<=4 inference: **264/288 unique** from source IO alone,
**42 real extra membership queries** to reach 288/288.
Classic *unbounded RHS* parser: only **262/288 unique** from the exact same
observations, requiring **46 real extra membership queries** to reach 288/288.
Extra ambiguity from greater expressivity is scientifically essential.
Both classic results conditional on human supplied deterministic one-symbol
parallel-rewrite meta-interpreter. Additional unseen ABCDE + epsilon + len5
extension: 12/12 exact, zero queries. Model invents NONE of this.

## RC35: true context-dependent expressivity beyond that meta grammar
The OLD arbitrary RHS-length independent rewrite class is MATHEMATICALLY
incapable of these tasks. Singleton outputs prove A->A, B->B, C->C, but
AB->AC, BC->AC, CAB->CBB contradict any position-independent morphism.

Small actual own PyTorch neural feedforward grammar policy trained from only
WHOLE string input/output observations. Nine independent seed fits across
three different tasks PREV/NEXT/BOTH. All nine first frozen weight models
generate 48-condition context-dependent execution rules; each **48/48 full
local context universe** independently verified, yielding mathematical
all-finite-length behavior under the PROVIDED window-of-3 and ABC contract.
9/9 original source data fit; FIRST heldout 1125/1125 strings and
154575/154575 chars exact. New safe lexical rule grammar
`WHEN PREV=A CUR=B NEXT=* EMIT=C` etc is AUTO-COMPILED from original
9 learned weight tables. Model did NOT invent lookbehind/lookahead access
or the host interpreter. Classical same-source IO direct table inferer
also fits exact 48 context rows per task in about **0.0025 process CPU sec
total**, compared with 9 neural fit runs about **7.65 CPU sec**.

## Complete original frozen full checkpoint evidence
Exact **combined 68-entry** cleanly reproduced conversation ZIP:
`NEUMANN1_Q3_RC34_RC35_FOUNDATIONAL_GRAMMAR_BOUNDARY_20261025.zip`
SHA256 `62fe175777d790910715efc30988eac6e19b897bf988327a9e746032ab4b64f6`.
Contains ORIGINAL RC33 actor .pt and OOD first frozen predictions,
RC34 source / independent afterfreeze hidden grader / two bounded vs
unbounded classical methods / 288 cases+12 ABCDE controls; plus
ALL NINE new RC35 Torch .pt, source-only trainer, original SHA-frozen
neural source tables, generated full new grammar, private author, first
1,125 independent heldout examples, 6 rigorous regression tests and clean
9-seed exact retrain from source-only isolated temporary directory.

`bash REPRODUCE.sh` and `bash RETRAIN.sh` both clean-extracted EXIT0,
and RC34 4/4 + RC35 6/6 scientific tests PASS.

**SCOPED PASS:** actual model learned and generated new CONTEXTUAL rule
semantics that old grammar cannot express; all-length independently checked
with fixed human-supplied 3-neighbor input architecture.
**FAIL:** original model own autonomous transition to previously unseen
grammar families, 7/288. **OPEN:** self-invention of fully novel foundation
metalanguage/control/window representation by neural actor, Q3 global,
Q4 all-in10x, Q6 independent outside author, Q7 frontier gap. Cost strongly
favors classical, no claim of foundational intelligence breakthrough.
