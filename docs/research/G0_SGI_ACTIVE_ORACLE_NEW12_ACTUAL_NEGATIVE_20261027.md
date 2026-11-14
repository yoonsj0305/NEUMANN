# NEUMANN 1 | Authentic SGI-12 Active Information Gate, FIRST vs independent original grade | 2026-10-27

**Final scientific verdict: classical selective-observation heuristic provides a label-count/accuracy/CPU tradeoff; no whole-system or trained-policy superiority.** Global NEUMANN **Q1–Q7 OPEN, G1 HOLD, G2 NOT RUN**. Zero NEUMANN ownweight models trained/called in this experiment.

## 1. Genuine new public original cohort, prereg, freeze, actual execution

- Pinned public external [Barnard-PL-Labs/sygus-sgi-1](https://github.com/Barnard-PL-Labs/sygus-sgi-1) @ `e7ae840e5546e9243ff94afb1a29064fc050011c`. Deterministic filename-only SHA256 selection of 12 new hard PBE-BV/SyGuS source paths, excluding exactly the nine hard originals already inspected in the preceding G0 baseline. [Protocol prereg](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/docs/research/G0_SGI_ACTIVE_ORACLE_NEW12_PREREG_20261027.md) commit **`68d11bac161b08b1fdbda47a146c616478157fdb`**. All **12/12 eligible**, no replacements. One *source project family*, NOT 12 guaranteed distinct benchmark authors; public benchmark, not LLM-pretraining-sealed.
- First code [actual proposer](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/research/q3/discovery_policy/sgi_active_oracle_v1.py) frozen at **`1bd0715ff3722ab8310a4bc5ed15e628734cc238`**. Original each task's first N−2 authentic ground constraints to native `cvc5` arms (`seed=0`, `seed=1`, `sygus-enum=random --seed=1`). All original grammar/helper functions preserved.
- Strict original-answer separation: source pack retains *penultimate and final original input values only*, not their outputs. Github Actions stage prepares source-only pack, then **removes the entire original upstream repo from FIRST candidate executor's disk**, before source-only cvc5 and separate Z3 program execution on unlabeled *probe input*. No future label is passed to candidate generation. Original source and full withheld ground constraint SHA kept.
- [Actual first run #40456478489](https://github.com/yoonsj0305/NEUMANN/actions/runs/40456478489), [raw 36 original source-only stdout/stderr and machine FIRST artifact #12712249788](https://github.com/yoonsj0305/NEUMANN/actions/runs/40456478489/artifacts/12712249788), raw artifact ZIP SHA256 **`3fc67e377ec83a8905ba57b78d7615ab9b0a522d6a5b32d600785a246f12d66f`**.
- Initial **12 source-only candidate sets and query decisions** (six request / six skip) FIRST JSON SHA256 **`a2713cee7e4a54506501927c07ff65f78d4ad110e4c9568892d937f3a0aa8185`**, independent GitHub [pre-GOLD freezing record](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/docs/research/G0_SGI_ACTIVE_ORACLE_NEW12_FIRST_SEALED_BEFORE_GOLD_20261027.md), commit **`14d3bf66c4d5822318b2496cb416adde68292dbc`**. The candidate and requests were fixed **before** original probe/future targets were read for grading.
- After freeze only, actual separate [post-first Z3 grade #40456919763](https://github.com/yoonsj0305/NEUMANN/actions/runs/40456919763), first SHA hard-checked, pinned original upstream, independent Z3 4.13.3.0 checks on the exact original source and omitted final ground example, **all 12 original penultimate/final INPUTS were distinct from the earlier source inputs**. The grade runner used a separate efficient one-SMT-query source checker rather than re-running CVC5 to alter first candidates. [Graded machine artifact #12712876198](https://github.com/yoonsj0305/NEUMANN/actions/runs/40456919763/artifacts/12712876198), grade JSON SHA256 **`484ac6ec6a3fe165f0cb15af48fe750300cc3aec4931d2abc94dd61d9cc76c7d`**, ZIP SHA256 **`6cb6d1d2de3e446adef4372b421fe6dabed38b9d72fb15f9d960cf8e0f46e5d6`**.

## 2. Real source-only original grade: denominator 12, every incorrect/HOLD retained

| Arm with same original task IDs | Heldout EXACT | WRONG | HOLD | Additional original labeled probe requests |
|---|---:|---:|---:|---:|
| C0 native strong classic default first N−2 source only | **7** | **3** | **2** | 0 |
| C1 native strong classic default first N−1, all 12 receive extra real probe output | **10** | **1** | **1** | 12 |
| Cactive native 3-arm disagreement/uncertainty source-only then conditional refit with probe | **9** | **2** | **1** | **6** |

**Six requests were genuinely decided without probe target labels**: indices **0,2,3,4,6,7**. Among them only index **3** (`PRE_79_100`: C0 HOLD to C1 EXACT) and **7** (`PRE_32_10`: C0 WRONG to C1 EXACT) were beneficial. Indices **0,2,4** had already been C0 EXACT; index **6** (`PRE_92_100`) remained HOLD after buying a label. Thus **2/6 requested labels increased exact-coverage**, 4 did not, conditional on this 12-task sample. **One actionable extra label was MISSED**: index **8**, `PRE_icfp_gen_10.10`, three output candidates were unanimous on the unlabeled probe input, so Cactive skipped, resulting in C0 WRONG while C1 with one authentic probe label was EXACT. This is a **concrete falsification of 3-candidate unanimity as a guarantee of semantic uniqueness.** Another skipped index 9 `PRE_100_10` stayed WRONG even with full-one-probe C1.

Among the three actual C0-not-exact→C1-exact tasks (IDs 3,7,8), Cactive requested only **2/3**, failing 1; all numbers are POST-GRADE diagnostics, not knowledge given to initial policy.

## 3. Real resource costs and tradeoffs

**Observed sums over CVC5 child processes only**, not Python/Z3/network/energy:

| Cost scope | CPU seconds |
|---|---:|
| Native C0 first-configuration proposals (all twelve) | **20.942895** |
| Native C1 complete source+probe refits (all twelve) | **17.138598** |
| Cactive's 3-arm source-only portfolio (all twelve) | **77.791170** |
| Cactive's conditional six refits | **15.113955** |
| **Cactive portfolio + conditional refits** | **92.905125** |
| C0 + C1, although a deployable C1-only policy need not pay C0 | **38.081493** |

Cactive spent **six fewer external labels** but needed much more solver CPU (5.42x C1-only CPU, 2.44x even the exploratory C0+C1 study), and was **one exact original task worse**. This is a genuine three-way tradeoff because external label acquisition latency/currency is *unmeasured*, so it is not valid to claim that C1 Pareto-dominates Cactive across all dimensions; nevertheless there is **NO demonstrated same-capability 10x, full-computation, or original-task accuracy superiority** for Cactive.

Resource omissions: Z3 proposal evaluation; Z3 original source/future checking; Python cold startup/preparation; source data fetching; network, memory, electricity, dollars, human label latency. A future claimed monetary gain would require pricing six saved labels and the observed 75+ seconds extra solver CPU, and normalizing accuracy.

## 4. Scientific meaning and architectural stop

- Three source-consistent classical candidates are NOT a complete source-consistent version space. A three-way unanimous output at one probe **input** is not a certificate that all possible programs agree, or even that the three agree on *future* input.
- A new learned NEUMANN policy has NOT participated. No model-specific representation innovation, policy improvement from learned reward, independent-author transfer, or frontier parity established.
- First evidence prevents cherry-picking; preserve unchanged. Current active heuristics do not deserve additional complex learned ranking or large-model compute. A stronger C1 already solves 10/12 original new test cases with less native CPU, granted the extra real labels.
- Before an ownweight A/B/C study, a meaningful new experiment must certify candidate **semantic inequivalence** and explicitly justify information acquisition, ideally using verifiable version-space counterexamples (not bounded unanimity). Compare against strong equal-rights existing classical methods including active CEGIS/oracle policies, not only naïve query-all.
- **Final status: Q1–Q7 OPEN, G1 HOLD, G2 NOT RUN, research PR #616 DRAFT**.

## 5. Full portable integrity package

`NEUMANN1_SGI_ACTIVE_ORACLE_G0_FULL_EVIDENCE_20261027.zip` SHA256 **`b07f9543ded766e14c5b8442e1fb9c4bbc78ad76cf2124ea3177d0d202b8c067`**, 5 files: original GitHub Actions first binary artifact ZIP and separate grade ZIP, README, runnable portable `verify_receipts.py`, complete SHA256 manifest. Clean bundle ZIP CRC PASS; verifier **PASS** checking both original JSON content hashes, all 12 original task identities, six fixed request decisions, three-arm false unanimity, original exact/wrong/HOLD counts, and CPU sums. **No upstream original benchmark files redistributed, no NEUMANN weights because none trained.**

[Consolidated evidence GitHub root](https://github.com/yoonsj0305/NEUMANN/tree/research/rc51-intelligence-spend-gate-20261026/docs/research). The full raw code and frozen machine stdout/grade are linked above; don't claim the GitHub report itself contains every binary artifact.

## 6. Integrate the discovery failure into executable safety/evidence guards

- [Research-only bounded-consensus evidence gate](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/research/q3/discovery_policy/portfolio_consensus_evidence_gate.py), committed `01b56b574b62ea4aae489ee13039b70a1b16cd5e`. Three equal executable program predictions are explicitly `BOUNDED_PORTFOLIO_UNANIMITY_NOT_VERSION_SPACE_CERTIFIED`; the decision may save a label if its risk is justified but **cannot certify a unique semantic solution** or close global Q gates.
- [Focused six regression tests](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/tests/test_q3_portfolio_consensus_evidence_gate_20261027.py), commit `d95c234003d55e368fbcfd1789f516180ceda6d4`, cover actual false-unanimity/incorrect future, missing candidates, observed disagreement, real 9/12 versus 10/12/cost, scoped-success non-promotion, invalid inputs.
- **Real GitHub Actions [run #40457984862](https://github.com/yoonsj0305/NEUMANN/actions/runs/40457984862) completed SUCCESS: pytest 6/6 PASS** (`6 passed in 0.04s`). This is an engineering regression test, **not a research Q1–Q7 success**. Full repo-wide CI is separately running and not asserted PASS.
- Portable ZIP content and hash validated in a clean local test. SHA256 of original first nested artifact `3fc67e377ec83a8905ba57b78d7615ab9b0a522d6a5b32d600785a246f12d66f`; grade nested artifact `6cb6d1d2de3e446adef4372b421fe6dabed38b9d72fb15f9d960cf8e0f46e5d6`; portable outer ZIP `b07f9543ded766e14c5b8442e1fb9c4bbc78ad76cf2124ea3177d0d202b8c067`. Verified 5 archive entries, CRC PASS and `verify_receipts.py` PASS with exact FIRST/post-grade receipt digests and all statistics.
