# CORE-22 extension | frozen CEGIS candidate repair audit (2026-10-16)

**Do not replace the first-pass CORE-22 result.** This is a separately executed supplementary experiment using the **same** frozen 13,026-parameter checkpoint.

## Independent rerun

- Frozen source file `core22.py` SHA256 `59c7faf4f97f8b467a1962983d7f10df7859403dc1125411e114c11e810fdbea` and checkpoint `frozen.pt` SHA256 `e211be8573f357ca43857e43db4367177fde9cd48661c651d465b698995a10db`, both matching pre-external inspection gate.
- Same 12 source-renamed, synthetic heldout fold/map problems: neural initial proposal **11/12**, correct base and inductive-step checks only.
- One wrong initial base literal produced a genuine **SAT** induction-base counterexample.
- A bounded, deterministic and purely **classical** local candidate search, triggered by the failed component, gave **12/12** certified proof after two additional candidate attempts. Neural weights never updated.
- The exact algebra baseline on identical task inputs achieved **12/12** without search or learning.
- Including Z3 certification: **28** obligations on neural + classical repair versus **24** obligations on exact classical path. Replay median wall ~55.0 ms versus ~53.3 ms; full-system difference is within subprocess-run noise. Training ~3.655 sec is additional cost for neural.
- New tests: combined CORE-22 + CEGIS **12/12 passed**. Same result from a fresh separately extracted release ZIP, including complete replay of all 12 candidates.

## Important scientific constraints

This is a **synthetic** non-Horn `define-fun-rec` affine-list grammar and the helper grammar is **human-supplied**. Six numeric features, not CORE-21's dependency-complete Horn AST, are presented to the neural network. Therefore neither new abstract relation *type invention* nor truly unseen external original-source proof has occurred.

External frozen evaluation target `CHC-COMP 2026 ADTRem/isaplanner/goal43_000.smt2` (Git blob `125e17e95967b4af13f5a1de9031f0d1d533e330`): **ABSTAIN_UNSUPPORTED_GRAMMAR**. No target patch or retraining. The stronger supplementary post hoc coefficient OOD check succeeded 4/8, so broad transfer remains unproven.

## Reproducible artifact (not yet stored on GitHub)

`NEUMANN_CORE22_LEARNED_GHOST_AND_CEGIS_20261016.zip`, 126372 bytes, SHA256 **`b9b5b3f8109c1fc52b806bea709bb2969111b9aaf82d97f4e44c241a47285369`**. Holds frozen weights, SMT bridge, 12 real tests, CEGIS runner, original historical receipts, hash manifest and source program generator.

**Current repository stores this report only, not the ZIP or model weights**. The local vault is downloadable from the ChatGPT producing conversation. Global Q1–Q7 remain **OPEN**. No frontier capability or complete resource advantage demonstrated; classical method still wins.