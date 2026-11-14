# NEUMANN 1 | G0 open AST semantic generator actual executor freeze

The 8-bit typed AST generator experiment protocol was committed **before** any neural train / heldout accuracy measurement in GitHub `1d4e7647af965117f2c2aef4b6b3d913eae8c28e`.

The executable Python 3 + PyTorch/NumPy runner is independently source-frozen locally before execution, sha256 **`a27a8ff1cbfe4e799cf2eb317c2a3c5368a04b37799c93c7ee44a4cf0503afd8`** `open_ast_g0.py` (portable artifact packaged with source and receipts on completion).

**Pre-run fixture audit** (no network/external answer):
- All 21 distinct typed 8-bit primitives and params; exact grammar <=3 depth **9723 raw programs**.
- Exact 256-byte full truth table semantic equivalence classes **3639** (depth1 20, depth2 262, depth3 3357).
- Deterministic heldout canonical class patterns ASR/SXR/RXS/XSR; 80 exact heldout unique noninjective full truth tables available; **train 2000** canonical distinct full functions; **0 exact bytewise truth-table overlap**.
- Task labels seen only on selected 16 input pairs at proposal time; separate benchmark fixture computes ground truth to grade 240 additional input points.
- Heldout operators include logical SHR, so **cannot be synthesized using only ANY-depth legacy A/X/R bijective grammar**; the strong classical C has SHR in SAME full expanded language and 9723 hypotheses and is not arbitrarily restricted.
- Torch generated programs output exact 3 typed op IDs with actual full parameters; this is AST composition learned from input-output, **not** new base primitive invention. Three normal A and three shuffled B training runs. Full classical source-only C scans same full grammar.
- FAIL/HOLD are counted; no seed/beam changes post-grade and no Q1–Q7 promotion from machine-authored 8-bit suite.

The first Python source had two syntax typos corrected (`'model'=>` and an accidental multiline doc literal) **before model training**, with no changes to benchmark, operator classes, dataset, architecture, beams, seeds or hyperparameters. The above exact SHA is the final executable freeze.

