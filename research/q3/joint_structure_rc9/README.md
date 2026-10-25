# NEUMANN 1 · Q3 RC9.1 · neural joint operator + indexing topology

**2026-10-25 | RESEARCH-ONLY | DO NOT MERGE without independent review**

## Why this matters

Prior Q3 RC7 trained local NAND/XNOR or AND/XOR, but a HUMAN supplied the
exact (j,i-j) convolution routing. RC9.1 removes this privileged routing
choice and starts with RANDOM initialized weights for both the local gates
and the routing. It is a new **scoped own-weight topology-selection PASS**.

## Actual experiments, frozen before independent withheld truth

Trainable scalars: **44** = Boolean gate G (4), gate H (4), and a 36-choice
routing softmax. The 36 routes come from 6 human-specified indexing rules
for each operand. Human also supplies the growing-memory loop, accumulator,
task I/O type and short training examples. There are **84 end-to-end**
1-,2-,3-bit GF(2) carryless polynomial multiplication examples, **no**
supervision of AND/XOR tables or index labels. Each of 12 separately
initialized neural restarts trains 600 Adam epochs from scratch.

All **12/12** compiled programs match training84/84 and choose either
(i-j,j) or (j,i-j), AND/XOR or NAND/XNOR. Selected seed7 uses
AND/XOR with (i-j,j) by source loss only. First exact frozen output bytes
SHA256 a28b2677e6ae94c84b78ba8d068ba6dbd25f582cc137e3d1c11eb5ef8ebba26a.
Independent grade **87,296/87,296** holdout width4..8; original unfused
float-neural output **5,376/5,376** width4..6; long width16..256 150/150.
All eight local transition truth cases imply an all-length inductive proof,
not just finite benchmark extrapolation. Eight 1-entry gate mutants rejected.

**Strong same-rights classical**: independently enumerate all 36 × 16 ×
16 = 9,216 candidate programs. Exactly **4** agree with all 84 source
examples and every one has the same provably correct all-length behavior.
Classical CPU time ~0.01548 s vs neural 12-seed CPU ~29.08 s
(a single machine/implementation, not normalized). Therefore
**NO neural efficiency advantage**; using a strong classical solver is
preferred within this known-small grammar.

Source-compatible adversary diverges at length4 after switching routing,
so outside the trusted complete grammar finite training cannot certify
general behavior. Human-authored integer carry extension reuses the
model-selected connections and local gate at n1..8: 87,380/87,380 low
integer products. This is NOT neural creation of carry logic.

## Full original raw evidence

Reproducible actual weights, all 12 seed training receipts, byte-frozen
source-only first predictions, independent gold grader, same-rights full
classical enumeration, mutation and adversarial tests, clean extraction
and fresh-from-random retrain all PASS in 15-file conversation archive:

`NEUMANN1_Q3_RC9_JOINT_NEURAL_STRUCTURE_20261025.zip`
SHA256 `eefae9a05b609eeb5a21bf287c14c0bdf0dc4389b368f06e697a010ff4ab4745`.

Inside: `bash REPRODUCE.sh` verifies SHA manifest and independently grades
frozen predictions; `bash RETRAIN.sh` reruns 12-seed training in a new
temporary directory, grades again and asserts all 12 recovered structures
match. Both were executed successfully. This GitHub branch contains only
the frozen compact extracted operator, regression controls and this
scope note, NOT the raw PyTorch checkpoint.

**PASS scoped**: neural jointly chooses gate semantics and the routing
from finite predefined templates; exact all-length GF(2) operation
induction, independent frozen holdout, full matched classical audit.
**OPEN global**: model self-invents novel representation language or
dynamic memory mechanism rather than picking a human-written grammar;
strong-classical superiority and Q4 10x all-in; Q6 independent external
authors; Q7 frontier task competence.
