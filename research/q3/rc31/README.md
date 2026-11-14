# NEUMANN 1 | Q3 RC31 META-SYNTHESIS FALSIFICATION AND HYBRID CONTROL
2026-10-25 · RESEARCH DRAFT / DO NOT MERGE as global Q3 PASS.

**Direct hard test:** A single own PyTorch MLP (7,688 learned params)
receives a target truth-table specification and predicts a variable-link
six-NAND program. NO gold programs shown, trained with soft differentiable
end-to-end circuit simulation on 12 specified two-input Boolean functions.
4 fixed independent seeds ×1100 gradient steps. BEFORE independent evaluation,
all four weights and first generated code for 4 *never-trained* functions
(semantics ID6 XOR, ID9 XNOR, ID11 implication, ID14 OR) were SHA-frozen.
**SOURCE exact 29/48; true heldout program exact 0/16.** This FAILS the
general algorithm-invention transfer gate. The goal cannot be marked PASS.

**Separate control (different architecture, non-zero cost rights):**
12 separate own PyTorch CEM+Adam program samplers fitted ONLY on the 12
SOURCE truth specs, with NAND as the sole pre-existing primitive and NO
program-code target labels. 12/12 emit valid variable-length NAND DAG
programs; all 12 weights and code frozen. Actual original source receipt
SHA256 `4d4dd8b585bc51cd22d37ddda8225c8a8328f392e943924dce0e7453885d0265`.
Classical expression-library compiler receives new tasks' target truth
specifications and reuses ONLY the 12 frozen learned programs (NO withheld
training). Generates 4/4 correct new executable ASTs, 16/16 independent
truth rows; 4 proof-gated AUTO instruction names; exact 21,844 fulladder
tests widths1..7 and 64 long widths16..512. A HUMAN wrote the fulladder
wiring. Formula induction requires local fulladder 8/8 gate table identities.
This is HYBRID classical composition, NOT neural standalone zero-shot.

Compositional closure from same 12 own-weight primitives reaches 256/256
3-input Boolean function meanings, independent 2048/2048 truth rows,
CPU ~0.014s + 1.09s program reconstruction/check. This follows already-known
NAND functional completeness, NOT novel theory or neural invention. Strong
direct classical NAND exhaustive compiler reaches all16 2-input semantics
in 59,601 circuit endings / CPU~0.014s; direct three-input NAND DP gets
all256 in ~0.0024s. Twelve own-source neural runs ~2.798 CPU sec, four
single-meta neural fits ~12.23 sec. Strong classical plainly dominates on
this domain. No all-in energy/FLOP estimate or frontier parity.

**Strict provenance and closure:** ZIP includes 16 ACTUAL original Torch
weight files, source-only learners and 4 meta generated FIRST code files,
sealed source12 before symbolic task composition, independent grades, exact
strong classical oracle-free program enumeration, full error-mutation gates,
SHA manifest, clean extraction REPRODUCE PASS plus isolated from-scratch
16-model RETRAIN exact Torch tensor and program equality PASS.

`NEUMANN1_Q3_RC31_META_INVENTION_GAP_AND_HYBRID_CLOSURE_20261025.zip`
SHA256 `f018863bcef25f90a46cc1981318d0e99789c5e2c667fd6ccb22d88c2f95d1e8`,
47 files. GitHub commits ONLY small extracted semantic interpreter, controls,
and evidence boundary; full original programs/weights in user artifact.

**PASS (limited):** trained-source reusable new opcodes, safe symbol registration,
classical recombination, all-width carry proof within human-written controller.
**FAIL:** single neural model zero-shot novel program generator (0/16).
**OPEN:** model itself autonomously inventing base syntax/control/ISA from
non-enumerated external problem; Q3 global, Q4 all-in10x, Q6 independently
authored new-family, Q7 Frontier Gap. Keep these separate.
