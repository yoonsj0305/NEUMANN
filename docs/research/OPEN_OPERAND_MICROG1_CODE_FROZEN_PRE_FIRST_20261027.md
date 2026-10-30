# NEUMANN 1 | open-operand micro G1 code freeze before first training/result

2026-10-27 KST. **Code already written and engineering tested (5/5)**, but training, test prediction, and any test grading have NOT yet been executed at this seal. This is synthetic author-generated data, not an independent author benchmark.

Pre-registered hypothesis and its explicit pre-run revision: [OPEN_OPERAND_UNSEEN_COMPOSITION_CAUSAL_PREREG_20261027.md](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/docs/research/OPEN_OPERAND_UNSEEN_COMPOSITION_CAUSAL_PREREG_20261027.md), amendment commit **8a697ff4d17ef320c5c0436a933fe9f6c43380df**.

- Exact local executable `experiment.py` SHA256 **`47448b8662af9db7e57105ce9d1bcab538355b54d0b8d0a52be9586a59ccd22d`**; actual source packaged in conversation ZIP after run, not claimed as checked into repo.
- PyTorch 2.10.0+cpu, numpy CPU, torch threads 2, no GPU or model APIs. Architecture: bit representation of 6 original source x/y and differences (192 features), 128/96 MLP hidden units with two categorical typed primitive-head outputs. **It cannot create genuinely new primitive operators**, but it may emit any of 6 previously declared two-operator pairs and insert arbitrary source-solved unsigned byte operand (heldout constants 128–255, training constants 0–127).
- A correct semantic type labels; B same architecture and 22 epochs, shuffled program-type label to destroy causal IO-to-program association; three paired seeds **3, 7, 11**; C exhaustive 6 pair types and typed inverse parameter solver. 2400 simulated train tasks, 160 unseen `XR` composition tasks, 160 known-composition task controls; 6 source examples + 6 heldout input positions; fixed seeds 271027/99027/99028.
- First code-level tests pass **5/5**: 8-bit wrap semantics, composition/inversion, oracle-based inverse source feasibility, heldout family isolation, source-vs-future input nonoverlap.
- Full proposal list per model seed and test condition is serialized into `FIRST_PROPOSALS_PRE_GRADE.json` SHA256, `FIRST_SHA256.txt`, with **only source IO and future input visibility**, before any `grade` call reveals target outputs. The grade step asserts immutable SHA prior to grading.
- A/B/C all source-consistency-verify on six source IOs and abstain if surviving programs disagree on the future input vector. All output candidate trials are counted; training CPU and inference wall logged. **The source-conditioned inverse parameter solver is classical** and not model innovation.
- Stop: no G1 admission, Q1–Q7 OPEN regardless of test accuracy; if strong classical C solves all or cheaper, A offers no novel additional capability. If A beats B only, that's narrow ownweight evidence for known-typed-composition prediction, not a new opcode.

This record is strictly **BEFORE first ML training/test first predictions**. Any afterward code changes must keep the initial SHA/proposals preserved and be labeled POST-FIRST, never overwritten.
