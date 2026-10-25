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


## RC10: delete unnecessary training and adapt information acquisition

A CLASSICAL 9,216-program complete DSL observer `active_grammar_9216.py`
uses only CANDIDATE output partitions to choose each membership query, never
reads target result before choosing its query. On original GF(2) source, four
queries (n3,a1,b2), (n3,a2,b6), (n3,a4,b3), (n2,a3,b3) leave four candidates,
all independently symbolically proven equivalent for every finite length.
Compared with 84 full training I/O examples, **21x fewer actual target
queries**. Without independently trusted grammar completeness, it returns
UNKNOWN. A delayed change at index3 is an explicit outside-grammar witness.

A separate AFTER-FIRST post-hoc bitset auditor finds a two-query witness
for this SPECIFIC target, so the live source-only adaptive minimax strategy's
four calls are not universally or target-optimal. Gold was NOT used to tune
the original query chooser. Candidate simulation prep1.156s + active
selection0.055s measured process CPU versus previous eager full-sample
classical checker0.0155s. Active's 80 saved oracle calls justify this only
if marginal oracle cost is large enough: under explicit equal-call-cost
assumption, break-even near **15ms per call** in this measured environment.
This is not a measured energy / remote query result nor global Q4 pass.

Full distinct reproducible 8-file classical archive:
`NEUMANN1_Q34_RC10_ACTIVE_9216_CERTIFIER_20261025.zip`,
SHA256 `c95076a510193400961437779cebdc08955de8e05346d163bc2224ea4efb56db`.
Run `bash REPRODUCE.sh` to verify original SHA manifest and clean-room
first-decision replay. RC9 and RC10 are mechanism evidence only, both
remaining subordinate to frozen Q1-Q7 and Frontier Gap requirements.


## RC9.2 independent RNG cohort, architecture frozen beforehand

A NEW, DISJOINT 12-seed cohort (20261201..20261212) was executed AFTER
the original RC9.1 architecture/600 epochs/Adam learning rate/84 source
examples/selection contract were frozen. ZERO retuning. All **12/12**
new initializations inferred equivalent accurate local logic and route.
Frozen model RAW neural n4..6 **5,376/5,376**, compiled n4..8
**87,296/87,296**, random width16..256 **150/150**, and 8-entry universal
inductive proof all PASS after source-only prediction SHA seal. Independent
full retraining initial cohort12/12 plus fresh cohort12/12 gives 24/24
across 24 distinct initializations, though the first cohort reused four
exploratory initializations. Fresh cohort measured training CPU25.6463s,
same-rights classical full9216 enumeration CPU0.0158s. This provides a
seed-robustness evidence only, not new external family/Q6 or Q4 win.

Full distinct 17-file fresh sample/real weights/first predictions/replay ZIP:
`NEUMANN1_Q3_RC9_FRESH_12_SEED_VALIDATION_20261025.zip`,
SHA256 `ffd35466868516954996eeadc09d4e941aaea120b88b14eb4e27ec5828857220`.
Local independent grade+full receipt replay EXIT0. Same human-bounded DSL
scientific caveat; global G1/Q3, Q4, Q6, Q7 still OPEN.
