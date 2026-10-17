# Q3B · First actual CPU-trained two-relation semantics (2026-10-17)

**Scientific verdict: BOUNDED_SYNTHETIC_TRAINED_RELATION_PASS_CLASSICAL_EQUALS / GLOBAL_Q1–Q7 OPEN.** This is an opened, researcher-authored **synthetic development** family, not fresh real external source transfer, not model novelty across operator families, and not any ≥10× performance win.

## Exact first local training and original proof
- PyTorch 2.10.0+cpu, 40 trained float64 weights (no bias), 1,024 mathematically generated training examples, 8 source/goal numeric features → 5 semantic coefficients defining predicates A(x,y), B(x,y), and inter-predicate affine offset.
- Actual LBFGS optimizer closure evaluations 33; **the archived first receipt field `actual_train_updates=33` is MISNAMED and counts closure evaluations, not independently measured parameter updates**. Original receipt kept untouched.
- First training optimizer wall **87.833465 ms** (excludes data preparation, import and program assembly). Max coefficient train error **5.57e-8**.
- 24 held-out researcher-authored synthetic programs instantiated after checkpoint write, with larger numerical parameter ranges; proposed typed relation semantics verified against **5/5 unchanged original Horn rules per program: 120/120 UNSAT** with native Z3.
- Model predicted EXACT classical semantic tuples in **24/24**. Two negative controls per case produced **48/48 SAT** (bad cross-predicate offset and genuinely changed safety goal).
- Model-free second source-text S-expression parser independently reconstructs original body, model coefficients and checks: **120/120 UNSAT** plus **24/24 zero-head ablation SAT** and a tampered-goal parser rejection. Same Z3 backend across both, so NOT independent solver diversity.
- Candidate-only wall on one CPU run: learned **5.836856 ms** across 24 vs exact classical **0.043728 ms**, **classical ~133.48× faster** for this family. Verification time 12,420.389ms combined for both arms; not a fair end-to-end inference comparison. No GPU, paid tokens, frontier call or external original evaluation.

## First immutable receipt hashes

- `frozen_checkpoint.json` SHA256 `2d557d5d92f4627749ded23c762ec0faf343ee20db679cee0b3222f15bf1b360`.
- `first_receipt.json` SHA256 `69f3aa75a94067866b1e700995496499734b420b6ec42b5ad60dac9f01730be4`.
- Reproducible conversation archive `NEUMANN1_Q3B_TRAINED_TWO_RELATIONS_DEV_20261017.zip`, SHA256 `f8686cb4d60ec04e3c9b13cc2640ea587df9941025f5d07097df7cb00b1b4c56`, 13,663 bytes, 7 members, CRC & 6-member SHA256 manifest PASS, independent audit after fresh extraction PASS. The ZIP is delivered on the ChatGPT conversation surface, and **is not in the GitHub repository** unless separately uploaded. Do not imply it was committed.

## Scientific boundary

The model genuinely learns the mapping for two typed predicate formulas; importantly, the feature extractor contains the **human supplied bilinear primitives** a*p,a*q,b*p,b*q and the target coefficient style is preselected. This is a meaningful test of actual trained learned semantic values, NOT autonomous grammar/operator invention. The equally informed exact classical emitter finds the identical invariant substantially faster; semantic learning **not necessary** here. Zero-weight ablation success demonstrates contribution within this architecture but **does not establish improvement over classical**. No Q3/Q4/Q7 closure.

Next legitimate experiment: frozen source-and-goal-conditioned general relation syntax/semantics proposer on one NEW authentic source-group-disjoint real holdout, complete original proof plus equal-information specialized classical, zero-learned and provider arms as applicable. No additional synthetic leaf/micro-operator sweeps.
