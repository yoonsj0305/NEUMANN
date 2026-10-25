# Q3 RC24 | own PyTorch actor generates a NAND-only Boolean instruction library

**2026-10-25 · RESEARCH-ONLY DRAFT · DO NOT MERGE without independent review.**
North Star: *Frontier-level problem solving with minimum necessary computation.*

**This is the first direct own-trained PyTorch *executable instruction
generation* gate after RC23 used GPT-6 as proposer.** The human supplies just
one base Boolean primitive NAND, two bit input wires, wire-pointer DAG DSL,
STOP, a 6-gate computation budget, source I/O target specifications and a
human-written interpreter, proof gate, CEM elite training rule and compiler.
It is **NOT** absolute invention of an entire metalanguage from nothing.

The model is a torch.nn.Module with trainable categorical policy logits for
wire references and variable program length. An optimizer updates its policy
from **end-to-end Boolean I/O reward alone**, without any circuit-label
supervision or prebuilt XOR/AND/OR program. Actual training code, actual
PyTorch tensors and all byte-frozen outputs are in the COMPLETE original ZIP
delivered in the conversation, NOT this lean GitHub branch.

## Executed source-only first study
- 3 source-defined tasks XOR, AND, OR. Initial 8 independent model restarts
  per task = **24/24 source-perfect sampled-best and 24/24 FINAL GREEDY**.
- Source-only frozen checkpoint before the unseen carry task. Model FIRST
  GREEDY programs emit newly named `AUTO_ce5d5a6bb041` (XOR-equivalent),
  `AUTO_9c0761f0ee85` (AND-equivalent),
  `AUTO_d9745c5341f5` (OR-equivalent).
  All three are executable variable-length NAND DAGs, not entries from a
  menu of finished logic opcodes.
- First frozen integer addition predictions n1..8:
  **87,380/87,380** correct, n16..1024 fresh long 84/84 correct. The
  *ripple full-adder formula is supplied by the human researcher*, only
  the gate bodies were actually trained.
- Different schoolbook shift-add multiplication application reuses the SAME
  frozen 3 new gate programs: n1..6 **5,460/5,460** plus 32 longer tests,
  no retraining. Entire multiplication algorithm is researcher-written.
- After original protocol freeze: disjoint 8 fresh seeds per source function:
  24/24 best source-perfect, 21/24 greedy.
- Formal proof: exhaustive truth tables for all 4 input pairs and
  standard ripple carry bitwise inductive invariant. No unseen gate truth
  assignments claimed.

## RC24.1 semantic closure for ALL sixteen binary Boolean functions
With unchanged 6-gate budget, Adam/CEM source-only actor, and FOUR explicit
source I/O pairs per target, 16 targets ×4 new seeds= **64/64 source-best
valid circuits**, 60/64 final greedy. The 4 failing greedy outcomes are
XNOR=1001; all four had exact sampled-best codes preserved. This establishes
every Boolean two-input instruction semantic can be emitted as a source-fit
NAND program by the OWN-trained model under the PROVIDED Boolean metalanguage.
NAND universality is a well-known logical fact, not newly discovered by
NEUMANN. This also does NOT prove three-input / arbitrary unseen semantics,
external author task generalization, or invention of a universal programming
interpreter/compiler itself.

## Same-rights exceptionally strong classical baseline
Exact exhaustive enumeration of NAND circuits up to 5 gates finds ALL
sixteen Boolean operators in **59,601 circuit endings** and ~**0.0184 process
CPU seconds**. For initial XOR/AND/OR, minimal 4/2/3 NAND gates. Original
24 neural fits consume total ~4.139 CPU seconds, and 64 additional fits cost
much more than single 16-target classical enumeration. Exact timings are
specific to one local process, not physical energy metrics. **Classical is
dramatically faster: Q4 speed-up NOT proven.**

## Scientific and authorization scope
- Original 19 own PyTorch tensors archived, 24 initial+24 fresh+64 other
  training programs replayed in separate temporary directory; exact tensors
  identical for 19 selected .pt checkpoint files and all FIRST prediction
  SHA outputs. Original source train runtimes excluded from equality.
- Parser rejects undefined opcodes, forward references, unsafe host AST and
  missing END. Independent 4-row verifier admits semantic mutants that
  remain correct, rejects incorrect ones. Not a formal proof of arbitrary
  variable-length code, only bounded NAND 2-input functions.
- Global Q1..Q7: **OPEN**. No frontier-labeled ability, all-in 10x,
  independent-author problem family, neural invention of new absolute base
  interpreter or general language metatheory.

## Full self-contained original evidence
`NEUMANN1_Q3_RC24_OWNWEIGHT_BOOLEAN_ISA_CLOSURE_20261025.zip`,
SHA256 **828879bde274396359a5821e080701140a5dd369f3e1963abc2a4eb3f477fda3**.
ZIP CRC+SHA verified; clean extraction `sh REPRODUCE.sh` PASS; isolated
full 112-fit `sh RETRAIN.sh` PASS, retaining first freeze hashes. GitHub
contains only readable extracted human-vetted interpreter, model-emitted
code and scope tests. Do not merge as global Q3.
