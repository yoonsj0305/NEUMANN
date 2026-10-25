# Q3 RC36: learned information-access instruction and relative-address syntax
2026-10-25 · Research-only Draft · Global Q3/Q4/Q6/Q7 OPEN.

## What actually changed since RC35
RC35 human-supplied PREV/CUR/NEXT context features. RC36's own PyTorch
37-scalar continuous actor sees only RAW ABC STRING input/output examples
(576 source pairs /task, lengths17,23,31). It learns a REAL-VALUED relative
read address (one trainable scalar) and 3×4×3 output lookup meaning, from
end-to-end output labels, with no supplied correct offset/neighbor rule.
A HUMAN supplies generic Gaussian attention over raw positions,
READ_REL interpreter and alphabet/base limits. Model weights are discretized
to compile executable new code: `ACCESS READ_REL -2,+2,-3` plus 12 CASE
rows each. Not an original base ISA/host syntax from nothing.

3 source-author tasks require neighbor at offset-2,+2,-3 and cannot be
expressed by any prior 3-position PREV/CUR/NEXT-only mapping. Independently
constructed two words share identical 3-position neighborhood but require
different output, exact mathematical expressivity separation.

### Actual evidence, no fabricated successes
6 own PyTorch seed runs each/task = **16/18** source-perfect,
other two (A seeds1234,1235) FAIL with learned wrong offsets +7,+5.
First 18 original Torch checkpoints and ALL first 18 program outputs SHA
FROZEN **BEFORE** independent hidden task grader, original FIRST prediction
SHA256 `f8e1fa39c5feee619dad876fa952c2be8638aa5b9869107693a178ed0ef7f864`.
First unseen 224 strings/model (length1..1024):
**3956/4032 whole strings**, **353086/355680 chars**, includes failures.
**16/18** model-proposed programs independently certifiably correct
for ALL finite ABC strings under human-supplied READ_REL contract:
exact signed offset & exhaustive 12/12 local-output table equal reference.
Raw CONTINUOUS actor all-length behavior NOT proven.
Unseen length1..8 full ABC exhaust (one first successful seed/family)
29520/29520 words, 221436 output characters.
Postfreeze strictly balanced remote-only one-cell intervention:
16/18 models each300/300 pairs, 2 failed 0/300,
total **4800/5400**, deliberately avoiding class imbalance illusions.

Source-only separated fresh temp learning with no teacher/gold/verifier copied:
**all 18/18 identical PyTorch tensors + emitted ASTs + first prediction
SHA** in separately invoked isolated RETRAIN batches. Actual original
checkpoint files archived unchanged. Human-authored afterfreeze grammar
compiler/strict parser and proof-gated registry refuse wrong/mutated offsets,
uncertified semantics and unrecognized host code (4 independent pytest PASS).

## Strong SAME-IO classical control
Classical raw-string semantic synthesizer searches integer offsets -7..+7
and infers complete 12-cell lookup tables from EXACT same source outputs;
**unique source-perfect offset for all 3 tasks**. Its measured total
CPU time ~0.0106-0.0174s over repeated runs. Fresh isolated neural retraining
one successful seed PER task measured process CPU seconds
1.01939+1.03413+1.14307=3.19659, ~184-301x slower depending on classical run;
the full18 neural campaign is more expensive. Energy/GPU cost unknown.
No Q4 all-in10x frontier efficiency gain.

## Reproducible original user archive
**60 files**, original source-only I/O, 18 ACTUAL Torch .pt, all receipts,
original first output bytes & SHA-freeze, independent all-length proof and
adversarial verifier, same-IO classical comparator, actual runnable parser,
4 regressions, 18-seed isolated retrain, manifest:
`NEUMANN1_Q3_RC36_OWNWEIGHT_INFORMATION_ACCESS_GRAMMAR_20261025.zip`
SHA256 **62929a0ec9323d9185e383f79d68ba5b2be46f4e52f5f84ec31689ff545a6df0**.
CLEAN temp ZIP extraction SHA manifest PASS, `bash REPRODUCE.sh` PASS,
and new clean extracted four representative success/failure isolated
checkpoint/first-output RETRAIN PASS; all 18 seed isolation passed in
separate batched commands.

This PR holds only readable compiled programs and compact proof smoke, NOT
the real 18 saved PyTorch model tensors (in conversation artifact).
**SCOPED PASS** learned unlisted relative address/semantics and executable
syntax under given generic input substrate. **NOT PASS** model invention of
READ_REL itself, metasyntax/compiler, unbounded memory, independent-author Q6,
frontier Q7, all-in Q4. All global gates remain OPEN, North Star unchanged.


### RC36.1 extra postfreeze direct float-actor replay
We also loaded ALL 18 original frozen PyTorch checkpoint tensors and reran the
CONTINUOUS soft-attention models themselves, without discrete program
compilation, over the same 224 independent inputs per model. Their empirical
finite-string predictions exactly agree with the compiled-program predictions:
**3,956/4,032 complete strings, 353,086/355,680 output characters** across
ALL successes and failures. This is POST-FIRST-FREEZE analysis, not a
pre-graded raw-continuous model proof. It does NOT certify all finite lengths
for continuous floating-point actor. FINAL original ZIP has **60 files**
including raw-actor replay Python and its original receipt, SHA256
`62929a0ec9323d9185e383f79d68ba5b2be46f4e52f5f84ec31689ff545a6df0`. Both clean full REPRODUCE.sh and clean isolated 4-seed RETRAIN
PASS; full 18 isolated Torch tensor/first-code retrains also already passed
in separately batched invocations.
