# NEUMANN 1 Q3 RC32 | OWN-trained recursive grammar productions, not just Boolean truth tables

**2026-10-25 | Research-only DRAFT, DO NOT MERGE as Global Q3 PASS.**

This research responds to RC31 meta-model **0/16** on new Boolean opcodes by
testing whether local NEUMANN own-weight PyTorch policies can generate actual
**variable-length and recursively self-referential grammar production bodies**
instead of selecting prebuilt Boolean or DFA program candidates.

**Experimental substrate, supplied by HUMAN:** three characters A/B/C,
parallel symbol rewrite semantics, RHS length bounded to1..3, input/output
contract, a 36-scalar learnable categorical model, CEM reward-selection plus
Adam, universal interpreter and the proof obligation. Crucially, the full
grammar right-hand sides are **NOT** provided as train labels, predefined
completed program candidates or as an opcode menu; the trained model emits
production LENGTH and every constituent SYMBOL from its learned PyTorch
weights. It is NOT independent invention of the foundational metalanguage.

Three independently specified growing/shrinking recursive rewriting families,
6 source input/output examples each (only composite seed strings, depth1/2):
**18/18** separate train runs find an exact new grammar, **16/18** final
greedy exact. First selected SOURCE-ONLY weights and byte outputs were SHA
FROZEN before calling separate oracle grader:
`FIRST_UNSEEN_PREDICTIONS.jsonl` SHA256
`473fe57b431b57dd32787cfdb80abfc936fd3f467ad0b83629803a5d4a3a8ba7`.
Unseen 1176/1176 (seed, depth) pairs produce 175,942/175,942 correct symbols:
all seeds length1..4 with depths3..5 and unseen longer length12 depth6.
The three generated rule dictionaries exactly match a completely separate
independent-reference program **after source freeze**. Per-symbol equality
gives proof by induction for **all finite seed strings and ALL finite
rewrite depths** of each *discrete compiled program* (not the policy's entire
continuous state). 9 mutated RHS alternatives destroy the rule identity.
18/18 untrained identical-architecture models fail source-exact grammar.

### Information lower bound & hardest real control
Each grammar symbol can rewrite to any of 3+9+27=39 possible non-erasing
RHS words. Equal-information **exhaustive classical 39³=59,319 grammar
candidate search**, using the SAME six source I/O examples, independently
finds a UNIQUE fully source-consistent grammar on each of three tasks.
**All three full classical scans CPU ~0.135s** vs **18 neural CEM+Adam
fit CPU ~90.56s**, demonstrating the model has no classical-cost win.
Minimum examples needed for source uniqueness were only 2/3/2, but actor
performance trained with only those prefixes drops to **5/9** independent
fresh seeds: source identifiability is NOT neural learnability.

### New language compilation and scoped speedup
Model-emitted rules compiled by a HUMAN-written symbolic optimizer into a
3×3 integer symbol-incidence matrix. Exact output symbol count at recursion
depth n is obtained by fast matrix exponentiation rather than linearly
iterating all n recurrence steps. Same output counts confirmed on small
literal expansions, and on the local CPU for task1 with initial ABC,
measured median CPU speedups **29.12× at n2048 and 40.65× at n8192** over
the naive linear-count recurrence. The SAME classical algorithm can apply
this optimization to a classical-found grammar, so this is a SCOPED
**compiler execution speedup, NOT global neural Q4 10×.**

### Reproducibility & source isolation
Full **46-file real self-contained ZIP**:
`NEUMANN1_Q3_RC32_OWNWEIGHT_RECURSIVE_GRAMMAR_20261025.zip`,
SHA256 **3fa634ecc01c6fef971062656f693e0e669c118725b4dfcfa04277d16d7abb98**.
Includes ACTUAL **27 real PyTorch .pt tensors**, 18 original runs,
9 reduced-observation failures/successes, full learned-weight source code,
byte-frozen FIRST outputs, independent oracle only in grader, strong full
classical control, parser/invariant tests, exact algorithmic speed receipt,
and file SHA-256 manifest. Original full ZIP clean-extracted into fresh
directory and `bash REPRODUCE.sh` PASS twice: 5/5 pytest, source SHA,
all hidden holdouts/classical scans. Separate `bash RETRAIN.sh` PASS
**27/27**, equal tensors, emitted grammar code and all frozen first prediction
bytes. In its training sandbox the target oracle Python file is PHYSICALLY
ABSENT. Original first run was created before this isolation refactor;
identical fully isolated retraining removes that provenance concern.

**SCOPED PASS:** own-weight runnable *recursive variable-length grammar*
generation and exact formal behavior of emitted discrete programs within
human-supplied rewrite metagrammar.

**GLOBAL OPEN:** fully autonomous creation of the base alphabet, syntax,
semantics, interpreter, control-flow/memory axioms; Q3 all-family novelty,
Q4 neural-all-in10x, Q6 external independent authors, Q7 frontier parity.
The research question now is model discovery of the metalanguage and
generalization to new structurally different *external* tasks, not
repetition of the three hand-authored toy tasks.
