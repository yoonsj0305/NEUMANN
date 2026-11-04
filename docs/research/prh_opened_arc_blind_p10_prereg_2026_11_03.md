# NEUMANN 1 P1.0 | BLIND OPENED ARC-AGI-1 TRANSFER AUDIT

**PRE-REGISTERED BEFORE TASK CONTENT FETCH**, 2026-11-03 KST. Highest authority remains frozen North Star. Global Q1–Q7 OPEN. This is public ARC-AGI-1 **training** split (opened, NOT sealed official evaluation), not frontier validation.

## Strict source identity and cohort selection
Source: `fchollet/ARC-AGI`, `data/training/*.json`, Apache-2.0. Pin default-branch HEAD commit SHA before reading task bodies. Get **filenames only** from upstream directory metadata; exclude only the four already manually inspected opened developer cases `007bbfb7`, `08ed6ac7`, `0d3d703e`, `05f2a901`. Score remaining filenames by 32-bit FNV-1a over ASCII `neumann-prh-p10-20261103|` + basename. Sort ascending by score then basename; select first **32**. No substitutions by perceived difficulty, no after-the-fact exclusions or task-specific rules.

## Frozen solver routes
1. **P0.3 fixed classic mini-DSL baseline**: identity, horizontal/vertical flips, rotations 90/180/270, transpose, tile 2x2/3x3, two Kronecker mask variants, column height-rank recoloring, train-inferred pixelwise palette map. Fit on all training input/output pairs; on test input predict only if all train-consistent candidates yield the same exact grid, else ABSTAIN. These are existing human-written primitives.
2. **P0.7 typed relational macro** only when route 1 abstains. Two monochrome connected, unequal-area objects; larger/smaller moving roles; infer an exact clearance 0..4 from training bbox translation; verify every original train output; on any disagreement, non-axis-projection, unsupported input, collision, ambiguity or other failure ABSTAIN. No test output use.
3. **P0.9 local rule rowwise** only when first two routes abstain, for two-symbol binary grids with same train input/output shapes. Infer smallest radius 0..2 and boundary from train rows, with complete table coverage, unique boundary and train replay. Execute rowwise test. No arbitrary new neural/JEPA processing.

All three stages must use the already frozen semantics, not mutate them based on selected task content. Source test output grids are inaccessible to every route and are passed **only to scorer after prediction**. Count routes attempted, task-level exactness (every ARC test input), actual abstentions and complete per-route CPU-region costs if instrumentable. Any errors are ABSTAIN with reason; no reference-guided rescue, no oracle hints.

## Outcome and stop policy
Report raw `baseline P0.3 / cascade P0.3+P0.7+P0.9` exact-task successes over all 32 selected IDs, net additional wins, abstentions, solved family mechanisms, and discovery costs if measured. An added neural architecture is NOT justified by a zero-gain result. If cascade gains zero, do not tune this public cohort: keep first result and pivot to genuinely different structural discovery or data acquisition. If >0, it is only opened public mechanism evidence; further fresh family and strong Direct/Frontier Gap validation needed.

The three stages **cannot claim new opcode invention merely by working**. A strong classical Direct in the same capability class is not yet measured. Q1–Q7 globally OPEN, official sealed benchmarks unopened, no auto-merge.
