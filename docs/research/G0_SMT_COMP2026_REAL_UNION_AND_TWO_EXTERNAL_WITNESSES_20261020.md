# NEUMANN 1 · SMT-COMP 2026 G0 ACTUAL CLASSICAL UNION and original SAT controls

**2026-10-20 | evidence class: ORIGINAL PUBLIC DATA / CLASSICAL SPECIALIST SCREEN, NOT learned NEUMANN success.**

## 1. Real publicly reproducible benchmark audit (not synthetic)

- Independently auditable [successful one-shot GitHub Actions run](https://github.com/yoonsj0305/NEUMANN/actions/runs/39421585497), `d2794f992cb3c39c4dd1dc0ed0f0e0ad6cfb0dde`, [official contest page](https://smt-comp.github.io/2026/results/qf_nonlinearintarith-single-query/).
- Official processed data sha verified **BEFORE extraction**: `results-sq-2026.json.gz` Git blob `958998e703aa5f5b32b45c253f80e618440824b1` (12,728,309 compressed bytes), `benchmarks-2026.json.gz` Git blob `83afb4e0a83f651e8677caa99872acce843011cb` (3,239,841 compressed bytes).
- Original benchmark metadata: **SAT 1,643 / UNSAT 614 / UNKNOWN 600**, total 2,857. Official scoring **sound_status** inferred after sound-solver consensus: **SAT 1,664 / UNSAT 887 / UNKNOWN 306**. Initial run [FAILED](https://github.com/yoonsj0305/NEUMANN/actions/runs/39421131059) because it improperly assumed those distributions equal. Correction implements official [sound solver consensus scoring](https://github.com/SMT-COMP/smt-comp.github.io/blob/master/smtcomp/scoring.py) and checks winning solver counts exactly; no silent relabeling.
- All **17 distinct solver submissions/configurations** evaluated, 17 sound by metadata non-contradiction; per-SAT/UNSAT solved winners checked against published scores (Z3-alpha2: 1577/831; Z3-Z3++: 1630/778).
- Among original tasks with an accepted SAT/UNSAT competition scoring status, **86** were not resolved by either of the two winning variants; **17** were not resolved by *any* of 17 variants. 17 are **16 SAT + 1 UNSAT**, from **2 separate recorded source-family directories**: `20170427-VeryMax/ITS` = 4, `20220315-MathProblems` = 13.
- **All 17 have already-known original benchmark status** (none of these 17 rely on the inferred-from-solver UNKNOWN metadata); the 2017 source-originals and 2022 source-originals are not semantically interchangeable.

## 2. Two real original SAT witness proofs, not learned

The following TWO SAT originals were among the 17 joint-unresolved contest tasks. They were retrieved from unaltered public [2022 original SMT-LIB source](https://github.com/SMT-LIB/benchmark-submission-2022/tree/master/non-incremental/QF_NIA/20220315-MathProblems) (CC BY 4.0), where each is **a single cubic polynomial equality**; publication of both numerical witness triples predates this study ([known three-cubes solutions](https://mathoverflow.net/questions/138886/which-integers-can-be-expressed-as-a-sum-of-three-cubes-in-infinitely-many-ways)).

| original file | SHA1 Git blob verified | literature witness x, y, z | exact original assert |
|---|---|---|---|
| `STC_0087.smt2` | `f118d05fdcee328b1eb9e4e780b9103c04537f3e` | `4271, -4126, -1972` | `x³+y³+z³ = 87` **PASS** |
| `STC_0795.smt2` | `89baa40165ec499d6b527a4b74159acab33a20db` | `-14219049725358227, 14197965759741571, 2337348783323923` | `x³+y³+z³ = 795` **PASS** |

Locally executed exact Python integer arithmetic with a source SHA-locked original-assertion checker and regression tests **3/3 PASS**. No software NEUMANN system proposed or generated these witnesses. This constitutes a strong **pre-existing classical specialist/library/knowledge-retrieval baseline**. The contest's 1,200-s solver timeout must NOT be reported as equivalent time for human-literature retrieval or learned-model discovery; costs and leakage matter.

## 3. All 17 real source names (original file identities)

```text
non-incremental/QF_NIA/20170427-VeryMax/ITS/From_AProVE_2014__Velroyen08-narrowing.jar-obl-8__p14386_terminationG_0.smt2
non-incremental/QF_NIA/20170427-VeryMax/ITS/From_T2__fun5.t2_fixed__p1007_terminationG_0.smt2
non-incremental/QF_NIA/20170427-VeryMax/ITS/From_T2__nakata.t2__p5330_terminationG_0.smt2
non-incremental/QF_NIA/20170427-VeryMax/ITS/From_T2__tqli.t2__p25231_terminationG_0.smt2
non-incremental/QF_NIA/20220315-MathProblems/MC_07.smt2
non-incremental/QF_NIA/20220315-MathProblems/SC_08.smt2
non-incremental/QF_NIA/20220315-MathProblems/SC_09.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0087.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0228.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0268.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0291.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0588.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0609.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0786.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0795.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0813.smt2
non-incremental/QF_NIA/20220315-MathProblems/STC_0880.smt2
```

## 4. Gate admissions

- `G0_OFFICIAL_ORIGINAL_COMPETITION_UNION_VERIFIED=YES`.
- `G0_SINGLE_ORIGINAL_SAT_PROOF_VERIFIED=YES (2/2 with published external witnesses)`.
- `G0_CLASSICAL_SOURCE_FAMILY_CROSS_TRANSFER_UNTESTED`; raw listed files imply 2 source groups, not an algorithm that generalizes between them.
- `G0_NEUMANN_LEARNED_STRUCTURE_DISCOVERY=NOT_DEMONSTRATED`.
- `G0_MATCHED_HARDWARE_TOTAL_COST_HEADROOM=NOT_DEMONSTRATED`.
- `G1_HOLD`; `G2_BLOCKED`; `Q1..Q7_GLOBAL_OPEN`.
- **Next task only**: choose ONE source-family-isolated original target (exclude both already published STC witnesses from novelty) and preregister an exact structural reframe vs strongest relevant specialized classical and literature baselines with independent original SMT2 checker. No bulk training or new speculative model architecture until genuine headroom.

**Machine-readable official screenshot/log truth:** The actual output line starts `NEUMANN_G0_OFFICIAL_UNION`, followed by `NEUMANN_G0_FAMILY_COUNTS` and `NEUMANN_G0_GAP_PATHS` in the [successful run logs](https://github.com/yoonsj0305/NEUMANN/actions/runs/39421585497).
