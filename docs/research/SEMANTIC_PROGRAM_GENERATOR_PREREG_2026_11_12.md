# New work: observation-conditioned program generation

Base `0d1baec723f249a62a901d100af6e941234a43ac`. Separate from Claude's
discovery-policy scheduling/latent-feature work, and from the earlier audit.

## Single hypothesis

A trainable conditional generator of typed program TREES, learned from its own
execution-verified program experience, can produce new executable semantics
on original unresolved SOURCE tasks that the same grammar's classical search,
untrained generator, learned context-free prior and whole-program replay do not
produce under the same process CPU cap. This is not a new formalism or global Q3.

## One bounded implementation and experiment

The model is a 128-hidden-unit NumPy MLP. It takes paired-observation statistics
and the partial tree, and emits primitive/variable/constant tokens with a typed
grammar mask. There is no Transformer, pretrained model, task ID, program ID
selection, learned schedule, fixed shallow-readout inventory or benchmark route.
Human inputs are the same basic functional execution substrate, token grammar,
observation features, random selfplay sampler and optimizer. The new learned
object is a conditional generative distribution over recursive program structure.

Selfplay: seed 917, up to 150,000 random AST draws, at most 3,500 distinct finite
behaviours, AST size 4–28, three output types. Every teacher output is measured
by actually executing a generated AST. No original benchmark observations are
used for training. Keep the full generation receipt, including rejections and
root distribution. The last 64 accepted behaviours are the fixed mechanism
validation set; all earlier accepted behaviours train the model. Train 64 epochs,
batch 512, seed 31, learning rate .002, unchanged thereafter. Hidden-test outcomes
never train the model. Semantic duplicates are excluded on 16 fixed probes;
this is not proof of universal semantic disjointness.

Original cohort: select 24 prior-unresolved rule SOURCE IDs by ascending
SHA-256(`neumann-semantic-generator-v1:` + ID), using the pre-existing
`spec_core_dev_source.json` S outcomes only. No choice based on new outcomes.
This is an opened development cohort, not a fresh independent-author holdout.
Read only its original-author files from the pinned BIG-bench commit. Original
TEST values never enter a discovery worker. Save submitted programs before
independent final grading. No reserve or new benchmark family is opened.

Arms, same 3 process CPU seconds per task, max 2,048 generated-program attempts:

- C: trained observation-conditioned program generator.
- U: identical initial weights (learning removed).
- P: trained generator with observation features removed, same tree context.
- M: replay all selfplay TRAIN teacher programs, type compatible, no edits.
- E: uniform classical search with exactly the same vocabulary, constants,
  variable rights and primitive library; binder allowance increased to match.
- S: current strongest specification-space core with its derived inverses.
- V: the frozen inverted-inventions core, including its previously learned
  operation library. Added before any new-original run so the comparator also
  includes the newer list mechanism, not just the older S core.

CPU includes proposal and TRAIN verification, failures are retained. No arm gets
original TEST labels for adaptation. Finite random generation and CPU cutoffs
are deterministic by seed/proposal limit except for the explicit timing cutoff.
All proposals and costs are recorded. Do not retry any target after scoring.

## Decision

Mechanism evidence needs a learned-generated TRAIN-and-TEST correct program
whose exact AST is absent from the training set and from M's accepted program.
Original learned-exclusive evidence needs at least one original-task win by C
over ALL U/P/M/E/S. The stronger development gate requires at least five such
wins AND paired exact p < .025 against E and S, without increased total test CPU.
These are local thresholds fixed before running, not global Q3/Q6 closure.

If no learned-exclusive original win exists, record FAIL and the proposer-signal
diagnosis; do not add teacher count, epochs, bigger networks, benchmark families
or reruns on revealed original TEST. Valid syntax, loss reduction and synthetic
success alone never promote the original capability gate.

Full costs: record selfplay CPU, training CPU, checkpoint bytes, inference and
verification CPU separately. Energy/monetary costs and frontier gap are UNKNOWN.
Idiot Index is inapplicable without a defined product/raw-material cost model.
Original-source grading and UNKNOWN/classical fallback are mandatory. This work
does not change the frozen North Star, old failures, or Claude's working branch.

## Pre-evaluation implementation correction

The initial data-readiness execution (before any original or heldout scoring)
accepted zero boolean-output teachers: a common `distinct outputs >= 3` guard
was impossible for booleans. Correct this to >=2 for B and retain >=3 for I/L.
The first receipt/checkpoint is preserved as `readiness_v1`, not a capability
trial. The training schedule is fixed at 64 epochs before the first scoring;
the initial 8-epoch training loss was 1.889 nats/token. No original outcome was
used to select this schedule, and no post-scoring schedule change is permitted.
