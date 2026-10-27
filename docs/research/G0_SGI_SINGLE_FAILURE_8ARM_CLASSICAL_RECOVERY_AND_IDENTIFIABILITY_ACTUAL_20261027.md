# NEUMANN 1 | SyGuS-SGI residual diagnosis: classical 8-arm search + source identifiability audit | 2026-10-27

## Scientific verdict

**Original frozen 12-task CVC5 source-only benchmark remains 11/12 exact**, NOT 12/12. On the **already opened** failing task `hard/PRE_76_10`, post-first reruns of **eight predefined classical CVC5 configurations** discovered **1/8 candidate** passing its original heldout final ground constraint; **7/8 were independently falsified**. This is `POSTFIRST_CLASSICAL_VARIANT_RECOVERY`, not a general-purpose automatically selected 12/12 model and definitely not NEUMANN own-weight discovery.

- All Q1–Q7 GLOBAL OPEN. G1 HOLD, G2 NOT RUN. No model trained.
- Data/task already known to researchers and public. Do not relabel any retrospective result as prospective blind transfer or frontier-level parity.

## Exact chronology and receipts

1. Original authentic independent [SyGuS-SGI-1](https://github.com/Barnard-PL-Labs/sygus-sgi-1) upstream pinned commit `e7ae840e5546e9243ff94afb1a29064fc050011c`. Source-only CVC5 12/12 original candidate FIRST JSON SHA256 `44047cd18e17e517cf0029329589411b997f53427d8fa3e152b044183d8524f0`, original Z3 independent first grading 11/12 including 1 failing `PRE_76_10`, preserved in [original G0 report](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/docs/research/G0_SGI_SOURCE_ONLY_CVC5_11OF12_AND_BIJECTION_THEOREM_ACTUAL_20261027.md).
2. Post-first fixed eight-arm experiment **preregistered before any re-execution** commit `69fbc6acf223c1ce535f6c9b71656c2019ef10a3`, with fixed source rights: original nine known input/output constraints, original grammar, original tenth heldout OMITTED entirely. Eight arms: default seed0; seeds 1,7,17; `--sygus-enum=smart`; `--sygus-enum=fast`; `--sygus-enum=random --seed=1`; `--sygus-unif-pi=cond-enum-igain`. Each native cvc5 1.1.2, max 15s wall/12s CPU, no oracle feedback.
3. First **actual eight-arm program generation**: [GitHub Actions #40454590527](https://github.com/yoonsj0305/NEUMANN/actions/runs/40454590527), source-only 9 ground constraints, all **8/8 source-fitting candidates generated**, ungraded raw first JSON SHA256 **`32601fd1b243b4fec4d3a94df48ad3253320839a1b31e10756eda00ff9e803f9`**, full stdout artifact [#12711718705](https://github.com/yoonsj0305/NEUMANN/actions/runs/40454590527/artifacts/12711718705), ZIP SHA256 **`d3ac27c9ee202b3ff5fca2c68d154525583ede0f33ec66d8d6dc90b96c26b493`**. Candidate SHA separately sealed BEFORE this new eight-arm grader as GitHub commit **`6299428672d9b2c078c8050c41de8e9ebeba1e3d`**.
4. **Independent actual separate Z3 4.13.3 grader** [GitHub Actions #40455087382](https://github.com/yoonsj0305/NEUMANN/actions/runs/40455087382) re-downloaded both immutable original 12-task first and eight-arm candidate artifacts, verified both first SHA256, checked exact same source Git original and all source + heldout obligations independently for ALL 8. Each source constraint 9/9 PASS. **1/8 heldout PASS**, specifically arm `--sygus-enum=random --seed=1`; **7/8 heldout FALSIFIED**. JSON **`EIGHT_ARM_POSTFIRST_INDEPENDENT_Z3_GRADE.json` SHA256 `b3424e4023e1f94b455889721e5124547b8386ad9525148cbe0568a17e7addfd`**, raw audit artifact [#12712242192](https://github.com/yoonsj0305/NEUMANN/actions/runs/40455087382/artifacts/12712242192), ZIP SHA256 `93b1edcda757914be0163565c15d6c4f40289e68c710895c4ebc7e56a5e37efb`.
5. The source-only `--seed=0` output is **byte-identical** to previous original first `PRE_76_10` candidate, SHA `24994918951ede36df85f83741215bef7a12e3b6cd97183811e93aa924d9b0df`; first remains failed. There are only **3 distinct stdout hashes among 8 settings**: six settings are **the same incorrect program**, `smart` yields a different incorrect one, and `random seed1` yields a different independently validated correct one. Output-byte identity is NOT proof of semantic equivalence across different byte hashes.

## Concrete original residual and source-indeterminacy proof

- Original heldout input `0xb0e0a62e25ee6adc`, withheld correct output `0xa78face8ed08ca91`; default/first CVC5 source-fitted program outputs `0xa78face8ed08ca90`. Exactly one least-significant-bit error.
- First nine source inputs cover **low-two-bit classes 01, 10, 11 only**; none have `x mod 4 = 0` (`00`). Withheld final input is **x mod 4 = 0**.
- Construct two original-SyGuS-grammar-expressible 64bit functions, AFTER seeing heldout original:
  - `F(x)`: immutable first CVC5 program, verified 9/9 source.
  - `M(x)=(bvand #x0000000000000001 (bvnot (bvor x (ehad x))))`, which is 1 iff `x mod 4 = 0` and 0 otherwise.
  - `G(x)=(bvxor F(x) M(x))` also exactly fits 9/9 source, yet `F(x*) != G(x*)` at heldout `x*` and the original gold equals `G(x*)`.
  - This is a constructive witness of **source-only nonidentifiability**, because both programs use only original available symbolic operators (including `ehad=x>>1`). It is not a certificate that no inductive bias can select one, nor that all classical searchers fail.
  - A local independent Python fixed-width replay verified all ten original input/output pairs as described and constructed JSON SHA256 **`27cfae6c089f0e5f9d538c1365f7b4a042353e551d1afca6926e17f6492e035e`**. The explicit alternative was designed after seeing gold, so **NOT a learned, prospective or independent model solve**.

## Real bounded extra cost

The eight source-only classical processes consumed **2.567934 seconds sum of per-process wall**, **2.509151 seconds aggregate user+system CPU**, with measured maximum sampled RSS across the eight executions **28,120 KiB**. That cost is additional to the original 12-task CVC5 first run and does not include install/download, runner overhead, separate Z3 checking, energy, money, storage. Native `random seed1` individually took **0.877995s wall**, vs original default **0.038963s wall**. The eight-arm portfolio is NOT cheaper and the result cannot be converted into a 10x NEUMANN advantage.

## Research consequence and stop condition

**Bounded classical structural search remains strong**: the single residual heldout error is not sufficient to justify neural solver training. It can be addressed by a distinct published cvc5 search mode and fixed earlier grammar, but that conclusion is retrospective. Eight seeds/strategies do NOT yield eight independent programs; six duplicate exact stdout.

The true bottleneck here is **underdetermination of function on the source examples**, not proof of an absent neural operator. To improve a *deployable* method, study source-only verifiable program diversity and/or a genuinely permitted extra labeled counterexample with all oracle and wall costs charged. A prospective new benchmark must freeze policy and models **before** source and gold; do NOT use `PRE_76_10` as new blind.

Next gated experiment: a new independent multi-author exact executable task family, with strong native C first, source/heldout isolation, semantic equivalence quotient, and learned ownweight policy proposed before graded gold. Q1–Q7 unchanged. Research PR #616 remains DRAFT.
