# NEUMANN 1 | RC15 & RC16 independent state and capacity experiments

**2026-10-25 · Research-only draft · Do not merge without independent review.**

Original full PyTorch weights, source-only proposals, first withheld predictions, independent validators, classical full enumeration and full 36-seed retrain are in the conversation's 31-file clean-extract archive:
`NEUMANN1_Q3_RC15_RC16_NEW_FAMILY_AND_3STATE_20261025.zip`
SHA256: `d71f1ea27fc4aa5e4a43d24747c2cfdefe43b1631715f44024530bf0e44e935c`.
Both `REPRODUCE.sh` and `RETRAIN.sh` were executed in a clean temp environment and PASS. Only lightweight extracted operators, formal guards, tests and scope notes are committed here.

## RC15: fresh families (not zero-shot generalization)

Frozen RC14 multiplication own-weight program without retraining gets **64/98** on prefix parity and **75/98** on seen-one. The identical 28-logit CEM+Adam learned proposer is trained from source-only 30 binary streams widths1..4 (98 output bits per family). Each family: **12/12** randomized train runs find a full source program, **10/12** final greedy scores full. Frozen first models on widths5..12: **8,160 streams and 90,016/90,016 output bits correct PER family**. Pair-product-state equivalence proofs certify ALL finite binary inputs within those semantics. Strong classical full 6,144-program search finds 32/46 source perfect (10/8 of those source-perfect candidates extrapolate incorrectly), and runs much cheaper (~0.24 CPU seconds/family vs neural total 2.14s for 24 training restarts). Previous RC14 weights zero-shot do NOT generalize.

## RC16: genuinely learned 3-state capacity selection WITH human-supplied Mealy grammar

A distinct own PyTorch policy with **33 trainable categorical logits** samples capacity m=1,2,3, transition and emitted-output programs. Learner saw only a **sealed 62-stream / 258-output-bit** source I/O table of the prefix-multiple-of-3 task, not the target formula or hidden states. No hidden-state/transition labels. Human DID provide the type of finite-state machine, possible capacities and generic read/emit interface. 12 initialized policies × 90 rounds × 200 source candidate proposals: **6/12** sampled-best source258/258; **5/12** final greedy. Source-only selected frozen actual table:
`next=(0,1,1,2,2,0)`, `out=(1,0,0,0,0,1)`, initial0, inputs0/1.
Independent unseen all widths6..12 **8,128 input streams; 89,856/89,856 first predicted bits correct**, 250 long n16..1024 test strings correct. Complete product-state bisimulation of learned vs specification has 3 reachable pairs, proves exact ALL finite binary input lengths. Single-entry output or next-state mutants **12/12** fail formal certificate. Degraded fallback explicitly known and measured reference returns correct response.

Classical same-rights full candidate audit: 1-state **4** programs best172/258, 2-state **256** best229/258, 3-state **46,656** exact2/46,656 (both universal), each with same 62 source I/O traces. Exact bound m>=3 is proved by three pairwise-distinguishable residual states. 12-seed neural CPU ~4.615s vs entire 46,916 classical candidate sweep CPU ~0.635s on same process host; neural is **worse**, not a Q4 total-cost win.

### Critical boundaries

- Original formulas in the *source dataset creator* and *independent grader*, not in the trainable RC16 policy/evaluator. Trainer and model receive only sealed output samples with source prefixes. This source-author code is human, and **NOT external independent-author task evidence**.
- Classical elite search provides candidate scores to the neural policy: successful program selection is NOT neural-only autonomous semantic invention. The program language and possible memory classes are HUMAN supplied.
- Important local scoped PASS: discovery of different reusable state rules, selection and proof of minimum 3-state machine on a different task, two cold model fits, honest zero-shot transfer FAIL, strong classical control and failure-recovery gates.
- Frozen North Star Q3 **oracle-free general new representation**, Q4 complete 10x, Q6 independent external-author/open-set/scaling, Q7 frontier capability gap all remain OPEN. Do not relabel as global PASS.

