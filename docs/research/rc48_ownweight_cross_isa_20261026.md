# RC48: own-weight abstractor across disjoint ISAs / version-space obstruction

**2026-10-26. Research-only DRAFT. Global NEUMANN Q1–Q7 remain OPEN.**
Continues RC47 (#612) and RC46 (#611), under `docs/research/frozen_north_star.md`.

## Actual first learned experiment

A real CPU PyTorch 8→24→1 parameter model was trained with 750 REINFORCE updates on anonymized three-program traces, a fixed equality-feature vector, and MDL-style compression reward. Its learner saw **no 2D grids and no target program labels**. The human, however, supplied the three-opcode meta-ISA, SLOT abstraction grammar, verifier, and reward definition. This is NOT automatic invention of a foundational language. Actual frozen checkpoint SHA256:
`e7a7d54f1665c3b698541e88df6d24fd110611094ba753a37cd7c0149fee1539`.

FIRST source-only predictions SHA256 `250ec027c03199e1267582d678ab37d2afcbf0df1b1527cff12339f7aaadce61` BEFORE private gold. On synthetic 1D sequences, frozen weights create `rotate_left;tail;SLOT`; three new fillers exact, direct 241 candidate evaluations versus learned-prior 10. But 2D grid traces only yielded three incompatible first-fit programs, so the learner returned `UNKNOWN_SOURCE_SCHEMA`, not an invented concept. The original result remains frozen FAIL; grid direct classical fallback was correct 3/3.

## New diagnosis and AFTER-FAIL repair (development, NOT sealed test)

Finite bounded grammar source-consistent version spaces had 7/6/3 candidate programs for three grid training tasks. FIRST source-fit is not a sufficient representation: distinct syntactic programs implement source-compatible and sometimes *semantically identical* mappings (e.g. twice flipped=identity). Preserve the **full version space**, propose shared code schemas, and only then use original unchanged weights to rank candidates.

With original weights unchanged, a posthoc human-revised joint version-space controller proposes
`flip_v;SLOT;transpose`. **Strong deterministic classical anti-unification produces exactly the SAME program schema with zero learned weights**. Frozen RC48b first predictions SHA256 `13651982c42639aafce20749bf9284ba99d84e28d7aaeb2b2188a90beea2e8d1`; THEN grade FOUR separately created but STILL **self-authored synthetic** grid tasks. All direct, neural-prior and strong classic-prior are 4/4 exact. First proposal candidate counts direct `70,10,68,69` = 217; both macro-prior arms `74,1,4,73` =152. Two tasks regress in candidate count; no universal domination.

Independent handwritten array-coordinate matrix interpreter confirmed 1007 source/unseen input-output pairs and rejected deliberate mutated output. Same benchmark author wrote both modules, so this is implementation-independent verification, NOT third-party benchmark independence. Eight later reseeded training runs in SAME opened synthetic setting all produced both local schemas, 8/8, but 13/30 never-trained random initializations succeeded too.

## Complete process-CPU cost: neural FAILS on this workload

Three paired replays, all arms same 4 exact grid task outcomes. Training, source searches, discovery, candidate failures and verifier calls included in scope; fixture construction, cold interpreter start, joules, peak bytes and monetary price not measured.

- Strong direct bounded classical search median **4,313,025 CPU-ns**
- Strong **classical** version-space + reused macro median **21,597,372 CPU-ns**
- **Own-weight** neural training + 1D source search + 2D version-space + macro application median **579,767,046 CPU-ns**
- Neural ~**134.4× SLOWER** than direct, despite fewer prospective candidate evaluations. All are local CPU measures only; no whole-system energy or Pareto assertion.

## Honest gates and architecture decision

SCOPED experimental mechanics: real learned weights trained PASS, 1D trace abstractor PASS, cross-ISA model proposal after human version-space repair PASS, 4/4 original synthetic outcomes PASS.
**Full neural-exclusive B, discovery-policy generalization C to INDEPENDENT external domains, new foundational ISA, frontier gap Q7, full resource 10×, global Q1–Q7: OPEN.**
For this bounded class Q4/Q5 neural all-in CPU advantage **FAIL**. Deploy/default must **delete unnecessary neural inference**, keep strong classical first and archive learned checkpoint solely as falsifiable research evidence. Additional synthetic fixtures designed to reward SLOT cannot resolve the central bottleneck; next valid project requires independent authors, original open-set tasks, a truly new semantically necessary representation, strong equal-rights baselines and real all-resource accounting.

## Replayable complete evidence

Chat archive `NEUMANN1_RC48_OWNWEIGHT_CROSS_ISA_VERSIONSPACE_20261026.zip`;
SHA256 `05ccc33483459e7b2606de1de8cee3d60b5e9dfb3b1b7aaf37792ca0c8b1781b`.
31 members, 30-file immutable SHA256 manifest, actual .pt weight tensor, 2 first prediction files, separate private gold, own PyTorch trainer, independent oracle, baseline/ablation data and cost study. Clean unzip `bash REPRODUCE.sh`: manifest 30 PASS, pytest 6/6 PASS, independent reference 1007 comparisons, first hash identity 3/3. `bash RETRAIN_CHECK.sh`: 8/8 fixed seeds, original first bytes left unchanged. This PR records compact auditable evidence only; original Python + torch binaries are in the conversation ZIP and are NOT falsely presented as committed to GitHub.
