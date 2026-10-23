# NEUMANN Q3/Q4: one 8x8 oracle call on 600 externally sourced 2D CA tasks

Date: 2026-10-23 KST. Scope: independent-author AutomataBench; **augmented** 8x8 controlled full-state one-step calibration under known reversible 2x2 Margolus rule class.

## Result identity
- Implementation PR: https://github.com/yoonsj0305/NEUMANN/pull/526
- Source/grader separated GitHub run: https://github.com/yoonsj0305/NEUMANN/actions/runs/39883639089
- Run jobs: original calibration construction **PASS**, frozen source-only learner **PASS**, after-seal independent original-author grader **PASS**.
- Original upstream pinned Git SHA: `7d86373fdb63fe1bd3592ddf71d923ceebc5acd9`.
- Dev original source raw SHA256: `ae709b00492d1cd6e539d140997f47049efd0cc24f587ffef9cac3d091ec0cbb`.
- Eval original source raw SHA256: `9cf0cf5219876e14beb7ad3898403020727165b82b9c26aa35a518146a5cf795`.
- Blind generated dev source SHA256: `1b4a6a392a3135da649d62131405a9c76b00256ca53644c55e26d22906beebf0`.
- Blind generated eval source SHA256: `272c7361e02f06348578b702ba825ba4dba917843fc176a27ef1d455688e7f23`.
- Before-grade dev prediction SHA256: `5297b93976921d9925bb752f96573090cb21a0ffc422fac9408d08bad98abc8f`.
- Before-grade eval prediction SHA256: `f69dbcbbd5445695f96e58ae5876749715634fcbf18604be11779a65b03d0159`.
- Independent original-author official verifier SHA256: `200f09b844e410671220cc6913aaa66aaa74ba7878e82b7cb787220d5437dd38`.
- Frozen unchanged learner blob: `9c74ec9761bd983de62f70669155d20a05cc02e6`.
- Frozen native CA blob: `623e63d92b100502b47896adc45f76e028d0cf07`.

## Independent original-author grade
| Original split | Tasks | All 16 hidden rule entries reconstructed | True initial state exact | Wrong submissions |
| --- | ---: | ---: | ---: | ---: |
| public_dev | 300 | 300 | 300 | 0 |
| public_eval | 300 | 300 | 300 | 0 |
| Combined | **600** | **600** | **600** | **0** |

Pre-grade source-only inference CPU: dev **0.480844264 s**; eval **0.380665012 s**; combined **0.861509276 s**, on distinct GitHub runner jobs.

## Constructive proof and lower bound
A phase-0 reversible 2x2 Margolus cellular automaton has an unknown arbitrary permutation `p: {0,...,15} -> {0,...,15}`. An 8x8 grid has 16 mutually disjoint 2x2 phase-0 blocks. Set the sixteen source blocks to the 16 distinct four-bit input patterns. One full-state `8x8 at t=0 -> 8x8 at t=1` oracle observation therefore determines all 16 output patterns and the entire rule exactly, for **every** possible permutation, not only a sample. Zero oracle calls cannot in general distinguish between 16! possible permutations; hence exactly one full 8x8 call is query-optimal under this interface. A full 4x4 observation covers at most four distinct blocks, and four 4x4 calls are necessary and sufficient for universal complete permutation recovery.

The one 8x8 call and four 4x4 calls both involve exactly 64 known input bits and 64 observed output bits. **This is a fourfold oracle call count reduction, not a fourfold total information-bit, CPU or energy reduction.** The 8x8 controllable source oracle is an additional calibration assumption not supplied by the unmodified original author's benchmark. The benchmark's original task initial-state answers are nonetheless independently validated.

The pre-grade jobs use the same existing frozen rule discovery/exact original solver, with one real 8x8 source observation only, split virtually into four 4x4 arrays. The original permutation, answer and metadata are physically absent during inference. Authenticated original inputs and truth are provided only to the separate grader after prediction seals. On independent seed and generated-family tests, 10,000 randomly sampled hidden permutations were exactly recovered.

## Paired native calibration-generation work (original 600 rule cohort; same CPU process; seven alternating rounds)
- Four 4x4 `roll_one` calls per original task: median **0.008193050 s** for all 600.
- One 8x8 `roll_one` call per original task: median **0.006914453 s** for all 600.
- Scoped native forward generation speed ratio **1.1849x**, not 4x.
- No physical measurement of real external-oracle latency, energy or intervention setup; no training cost.

## Admitted decisions
- Q3 scoped rule identification under known CA family and controllable complete one-step oracle: **PASS**; two author splits, 600/600.
- Q3 information-efficient deterministic experiment design query count: **PASS**, 4 -> 1 with fixed 64+64 observed bits.
- Q4 scoped **native calibration generation CPU**: measured modest improvement; **not** 10x.
- Q4 prior 25.812x original 4x4 source-solver vs SAT: independently retained from PR #515; not caused by one8.
- NEUMANN original learned new primitive, model-agnostic transfer to unknown families, frontier-level generalized intelligence, and 10x full-system compute/energy savings: **OPEN**.

## Degraded mode / interface
If 8x8 controlled full-state one-step intervention is unavailable, fall back to four designed 4x4 observations if that oracle exists. Without either interface, do not impute hidden permutations or claim full-rule identification; return UNKNOWN with an ambiguity witness when possible. Zero wrong is required for admission.
