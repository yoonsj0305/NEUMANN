# NEUMANN 1 | Actual learned typed executable AST generation vs shuffled neural and exhaustive classical · 2026-10-27

## Final research decision

**Scoped G0 learned executable AST compositional generalization: small positive signal relative to shuffled-label control, but overwhelming NEGATIVE vs fully privileged classical C. Global Q1–Q7 OPEN; G1 HOLD; G2 NOT RUN; research PR #616 remains DRAFT and unmerged.**

The prior authentic SGI-1 ownweight reranker was fundamentally confined to three native classical proposals and the finite 11/12 ceiling. This new deliberately **machine-authored** experiment moved beyond reranking: supervised true-gradient torch models generate previously unobserved **three-token typed executable programs** directly from 16 input-output observations. Importantly the original grammar's **logical right-shift operator was already supplied to BOTH neural and classical methods**, so this does not invent a primitive and does not prove unseen independent external domain competence.

## Exact protocol and chronological receipts

1. GitHub [prereg](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/docs/research/G0_OPEN_AST_NEURAL_GENERATOR_8BIT_PREREG_20261027.md) `1d4e7647af965117f2c2aef4b6b3d913eae8c28e` committed BEFORE any test or model training results. Same finite expanded original 8-bit DSL for all methods, 21 typed primitive tokens: 8 ADD(c), 8 XOR(c), 3 ROL(r), 2 SHR(s). All program lengths up to 3 were allowed for classical C.
2. Exact finite 8-bit grammar enumeration **9,723 raw programs**, quotient by **full 256-byte truth tables** produces **3,639 distinct functions** (depth1:20, depth2:262, depth3:3357). Dataset: 2,000 semantic-unique canonical depth-3 TRAIN and **80** semantic-novel canonical depth-3 EVAL with heldout canonical patterns `ASR,SXR,RXS,XSR`; **zero duplicate complete truth tables**. Every heldout exact function noninjective, hence legacy ADD/XOR/ROL-only bijective grammar has a genuine arbitrary-depth impossibility proof. But native classical C includes SHR as explicitly available from the first, so no novel primitive claim.
3. Model access: **16 original (x,f(x)) pairs** at x=`0,1,2,3,4,7,8,15,16,31,63,64,127,128,200,255`. Six torch MLP model seeds normal A 5/13/29, labels shuffled B 5/13/29; same architecture `128→256→63`, Adam lr=.003, decay=.0001, 150 epochs, batch128, top32 *full three-token* program candidates by model-assigned autoregressive positional token scores, accept first source-consistent program. Final grader checks FULL original 256 inputs (240 withheld). B original training labels permuted between tasks once per seed, not merely output score shuffle.
4. First syntax-valid executor SHA256 `a27a8ff1cbfe4e799cf2eb317c2a3c5368a04b37799c93c7ee44a4cf0503afd8`, after prereg and before any training. First run timeout **after 4/6 seeds trained but before evaluation**. Executor-only resumed Torch checkpoint amendment [GitHub `49557b3f265c9dbe807041cdf49deb45916495be`](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/docs/research/G0_OPEN_AST_EXECUTOR_TIMEOUT_RESTART_AMENDMENT_20261027.md), resume code SHA `2536401f20b1c33c74d71b5c78ac79b073f0ec2d46f4f42967eb5c1f76383c8a`; **no algorithm/data rights/hyperparams changed**. The complete train six + grade 80 then crashed **only in C aggregate statistic field**, after performing 80 tasks but before saving JSON. Recorded separately [executor-only key repair GitHub `427828aa8cf646c933d1e5fe1bc7407351acd145`](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/docs/research/G0_OPEN_AST_POSTTRAIN_SCORE_KEY_EXECUTOR_AMENDMENT_20261027.md). Corrected exact Python code SHA `db57697ceac09ad1c3dd8f3de1fb421969061164cfc375dc7c7c77cd3db7a6a4`; six saved checkpoint Torch state_dicts reused unchanged, no model adjustment from the earlier grades. Original logs retained.
5. Complete final machine `G0_OPEN_AST_8BIT_MODEL_GENERATION_ACTUAL.json` SHA256 **`93d66b9b90c1bc33f7b0fa42371e39b9796732794751b7bc810145c10f120efe`**, original train/test canonical truth table manifest hashes, all 80 programs' original full semantic hashes and neural candidate programs, weights and costs included in portable ZIP.

## Actual 80-task full 256-byte exact function match

| Policy | 80 heldout semantic-new tasks exact | Matched source16 | Max generated proposals considered/task |
|---|---:|---:|---:|
| A true-gradient seed5 | **11/80** | 11/80 | 32 |
| A true-gradient seed13 | **8/80** | 8/80 | 32 |
| A true-gradient seed29 | **4/80** | 4/80 | 32 |
| B shuffled-target seed5 | **0/80** | 0/80 | 32 |
| B shuffled-target seed13 | **0/80** | 0/80 | 32 |
| B shuffled-target seed29 | **3/80** | 3/80 | 32 |
| C classical full grammar length≤3 | **80/80** | 80/80 | **9,723** available hypotheses |

A>B in three paired seed comparisons. Thus genuine gradient learned *some* heldout **executable AST compositions with complete new truth tables** that label-shuffled controls were less likely to propose. This is a **synthetic small-scope compositional generalization signal** only. No observed A dominates C, and the original classes are all drawn from a single artificial grammar known in advance.

### Even stronger full-program semantic audit

A separate exact classification over **all 9,723 classical programs** showed that the 16 provided source IO labels already partitioned the entire expanded grammar sufficiently to isolate **a SINGLE possible 256-byte complete truth table for each of the 80 test tasks**. So in this fixed grammar C should solve all 80 from source IO alone; it indeed did. A neural model does not face an independently hard open-world discovery problem here. This identifies the benchmark as **too weak**, rather than a loss of NEUMANN's general objective.

### Actual computation scope

- Classical grammar construction and semantic index **0.103398 process CPU s**, classical exhaustive candidate source comparison across all 80 **0.446413 process CPU s**, total **0.549811 CPU seconds**. Full grammar and semantic index used by benchmark author were charged to the classic computation.
- Six torch real training runs combined **44.386999 process CPU s**. All six models evaluating all 80 tasks and checking top-32 source candidates **0.281667 CPU s**. A single model can amortize its fraction of training but is STILL weaker in this tiny exact grammar and cannot claim a 10× total advantage.
- Above **does not include** pre-experiment exploration, initial timeout and failed executor costs, dataset provenance, loading/installation, total RAM/energy/cloud money. The interrupted runs consumed additional uncounted resources; hence numbers are component CPU only, **not complete wall-clock resource advantage**.

## Independent integrity and provenance

- Portable original Python source, actual six torch `.pt` checkpoints, complete machine JSON, original failed runs and final run console receipts, README, verifier and SHA manifest in **`NEUMANN1_G0_LEARNED_EXECUTABLE_AST_A_B_VS_CLASSICAL_20261027.zip`**, outer SHA256 **`c5ae25416af469cf27bda156342ee19dd22df76c7ce715001a8d0a5d9c1d32a9`**, 14 entries, 1,133,260 bytes, ZIP CRC PASS, manifest 13/13 SHA PASS.
- Independent, separately written **pure Python scalar** verifier `verify_receipts.py` is included. In a **newly extracted clean temporary directory**, it reenumerated **all 9,723** grammar programs (without importing torch/numpy), validated all 3,639 full semantic classes, regenerated the canonical 2,000/80 train/test manifests and zero full-table overlap, checked **80/80** unique 16-source signatures against the **entire classical grammar**, checked all 480 A/B program outputs plus all 80 C outputs and executable exact correctness, confirmed all score numbers and Q1–Q7 OPEN/G1 HOLD. **Verifier PASS**.
- The original user's GitHub research G0 doc is documentary mirror; the exact runnable final Python source and weight files are in the portable package. No source-file claim should be made until the exact bytes have been separately committed.

## Stop condition and next research investment

**Do NOT train a larger neural generator on this exact trivial finite grammar, nor count model-generated old-grammar compositions as NEUMANN discovering a previously absent primitive.** The next step must introduce externally authored *unseen executable problem families* with actual classical CVC5/CEGIS capacity gaps and semantic AST novelty / independent model-weight causal A/B, including compute/label total. The 80 artificial heldout functions are now opened development, never blind evaluation again.

Global Q1–Q7 remain OPEN; G1 HOLD; G2 NOT RUN.