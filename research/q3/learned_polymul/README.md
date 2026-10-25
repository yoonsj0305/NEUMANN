# NEUMANN 1 | Q3 RC7: own-weight local semantics with provided growing-memory topology

**2026-10-25 · RESEARCH-ONLY DRAFT / DO NOT MERGE without review**

RC6.1 proved an online arithmetic multiplication memory-growth necessity but used human-authored rules. This independent RC7 study trains **two differentiable 4-entry binary gates** (8 trainable logits) from end-to-end examples of **GF(2) polynomial carry-less multiplication**, with width1..3 source inputs only (84 complete input/output pairs). This is **not integer multiplication**.

A HUMAN prewired the diagonal convolution structure, retention of operand histories and two-gate composition; weights learn the two *local semantic gate tables*, with **no gate-table/hidden-state labels**. Eight seeds × 550 epochs, chosen by **training loss only** before opening any width>=4 gold. Frozen seed0 learns NAND/XNOR; other seeds learn this or functionally equivalent AND/XOR. All **8/8** seeds achieve84/84 train outputs and all eight exact local invariant rows, establishing all-finite-length polynomial correctness of the *compiled tables*, by induction in the human-supplied dataflow.

Actual sealed own-weights and first outputs independently verified: **87,296/87,296** compiled exhaustive n4..8 pairs and **280/280** compiled random n16,32,64,128,256,512,1024. Separate RAW unfused float neural inference **87,596/87,596** postfreeze inputs (all n4..8 plus 100 each n16,n32,n64). All **8/8** single truth-entry mutants were rejected. First predictions were SHA256-sealed before gold grading. Clean-extract full replay and independently rerun training from scratch both EXIT0. CI file here checks compiled results; the actual .pt checkpoint and model training receipts are NOT committed to this small research branch.

**Full 108KB, reproducible archive in the user conversation:**
`NEUMANN1_Q3_RC7_LEARNED_DYNAMIC_POLYMUL_20261025.zip` SHA256
`ae0efe69059afe05525d54c736f27a821d213d10e6037454824ff81b8aa1a2bb`.
It includes `weights.pt`, frozen prediction binaries/JSON, source-only learner, independent grader, original RAW neural grader, all SHA receipts, manifest, `REPRODUCE.sh` and `RETRAIN_AND_REGRADE.sh`.

**Strong same-rights classical baseline**: exhaustive enumeration of all 256 possible 8-bit pairs of truth tables against the SAME 84 end-to-end examples discovers both equivalent solutions. One local classical CPU measurement ~0.000763s for enumeration vs neural 8-seed training CPU14.749s (measurement-specific, not normalized hardware/cost comparison). NO claim of neural efficiency or classical-beating discovery.

**PASS (narrow)**: a real locally trained own-weight model learns gate semantics within an existing dynamic-memory architecture, generalizes with original raw inference to unseen widths, and symbolic extraction makes an exact all-width operator. **OPEN (global)**: weight model *invents/grows its own representation* rather than receiving the diagonal convolution template, external-author novelty, same-rights classical superiority, Q4 10x all-in, Q6 external, Q7 frontier.

This is scoped operator-learning evidence, **NOT global G1/Q3 PASS**, and neither PR nor CI success should be presented as breakthrough frontier intelligence.
