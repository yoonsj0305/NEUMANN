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


## RC8 follow-on: eliminate needless learning when grammar is only 256 candidates

A model does not have to train on all 84 inputs if the finite operator
grammar is already available. The newly committed `active_two_query_certifier.py`
chooses each query using ONLY candidate partitions, before calling the
unknown function. On the same exact GF(2) multiplication target:
first q=(n3, a1,b1) -> y1 leaves30/256; second q=(n3,a3,b6) -> y2
leaves two internally distinct but universally equivalent operators
(NAND/XNOR and AND/XOR). Their 8-entry composed transition table is identical.

An INDEPENDENT posthoc one-query lower-bound check enumerates ALL 84
potential single queries and ALL 256 programs. The most informative
single observation for this target leaves >=4 candidate programs with
>=2 different effective transition functions. **2 queries are optimal**
among the precommitted pool on this target.

Compared to acquiring all84 training pairs: **42x fewer oracle calls**
(2 instead of84) and **38x fewer observed output bits** (6 vs228).
Source-only candidate precomputation+adaptive selection local CPU
0.01856s in one measurement. This eliminates the need for neural training
*for this restricted known-grammar instance*, NOT Q4 global compute
superiority or novel external-author structural invention. Without an
externally trusted grammar completeness promise, this runtime returns
UNKNOWN_UNTRUSTED_GRAMMAR rather than a false universal certificate.
A separate 5-file stdlib ZIP and SHA receipt:
`NEUMANN1_Q34_RC8_OPTIMAL_2_QUERY_STRUCTURE_DISCOVERY_20261025.zip`,
SHA256 `d270e283d52648aac3d28cd89e965d78316b08aef021fd037e02d283b866d444`.
3/3 standalone unit tests PASS. Research draft remains unmerged.
