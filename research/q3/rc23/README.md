# NEUMANN 1 Q3 · RC23 GPT-proposed new executable syntax

**2026-10-25 · research-only draft, do not merge as global Q3 PASS.**

## What changed (and what did not)

This tests the hardest remaining question: can a model AUTHOR the executable
semantics of new reusable instructions without selecting from an already
enumerated complete-solution grammar? The proposer in this experiment is **GPT-6
in the current conversation**, NOT the small separately trained NEUMANN model.
It was provided natural-language problem specifications and an existing Python
execution/metalanguage substrate. No completed stack/queue operator menu was
provided. GPT-6 authored a new trace syntax and radix-integer semantics:
MAKE(k), WRITE, READ_FRONT, READ_BACK, MATCH, EXHAUSTED.

Original candidate bytes were SHA256 **da19be22e1262b2a5f2462e783d0117c88d390712bec8022e534ac88fbdc0a8e**
frozen BEFORE any independent test/holdout code was written. This branch
contains only an extracted equivalent small runtime, CI smoke and science
boundary; the actual byte-frozen source is in the standalone ZIP.

## Theorems & actual experiment

For k-symbol alphabet and base B=k+1, encode symbol a as nonzero digit a+1,
pack S=B*S+(a+1) with length n; from the right extract S%B-1 and S//=B,
or from the left extract S//B**(n-1)-1 and trim S%=B**(n-1).
Induction on positional expansion proves exact arbitrary-length reversal and
left-to-right replay without prebuilt stack/queue data types.

It solves COPY {w#w} and MIRROR {w#reverse(w)} on all finite strings. For a
fixed length n, every one of the k^n prefix histories is distinguishable by
a matching suffix, requiring >=ceil(n log2 k) state bits in ANY exact
deterministic one-pass machine. The packed payload needs
<=ceil(n log2(k+1)) bits, **PLUS** length-counter/host object overhead.

Actual POST-FREEZE implementation-independent Python reference checks:
- 348,912/348,912 exhaustive source/target string comparisons over 4 alphabet
  sizes, 2,232 positive and 346,680 negative.
- 960/960 class-balanced new long cases up to 1,024-symbol half-length and
  64-symbol alphabet; 18/18 malformed controls; 560/560 trace invariants.
- Third family with *postfreeze authored adapter*, typed Dyck-prefix nesting:
  143,366/143,366 streams; 994,650/994,650 output bits, 480 long
  class-balanced tests up to depth 512. Reuse is proven; this does NOT show
  autonomous zero-shot task planning by NEUMANN's learned core.
- Strong same-information classical direct tuple/slice implementation is
  faster: median CPU slowdown of GPT-proposed bigint solution 9.45x (n64),
  10.01x (n256), 17.39x (n1024). Not a Q4 or Q5 win. GPT-6 model inference
  cost was not measured and must remain UNKNOWN.

Original **9-file ZIP** clean-extracted and bash REPRODUCE.sh PASS:
NEUMANN1_RC23_GPT_PROPOSED_ISA_TWO_NONREGULAR_FAMILIES_20261025.zip
SHA256 **2086388e876e503ae796debc5f0c9b09fbc4a7fcacdf658c51018b964156ade9**.
Original bytes and full reference generator are inside this conversation
artifact, not committed here.

## Scientific gate

SCOPED PASS: GPT-6 generated new macro-instruction semantics and the language
grammar text without a task-specific enumerated candidate set, frozen-first
testing, proof of all-length correctness in 3 formal tasks.

STILL OPEN: NEUMANN own-weight self-invention, discovery of an entirely new
foundation/host ISA, independent external task author, proof without model
assumptions, frontier-level useful gap, full iso-capability Q4/Q5/Q6/Q7
advantage. It is logically impossible to EXECUTE an entirely semantics-free
language without some pre-existing evaluator/input-output contract. This
study defines invention RELATIVE to the minimal provided Python interpreter.

**Do not merge** this as completion of the NEUMANN 1 North Star. The proper
next gate is learned-core proposal provenance and an external-author
evaluation against strong classical and frontier systems at measured costs.
