# NEUMANN 1 P1.4 | Zero-teacher-call executable library reuse (PREREG)
2026-11-05 KST. North Star and Q1–Q7 unchanged and OPEN.

## Research question
P1.3 external GPT-6 teacher produced four first-submitted pure JavaScript original-task solvers and separately passed 4/4 registered public ARC-AGI-1 tasks (five test grids). Can those *frozen compiled operators*, without a further neural/teacher call, automatically match a genuinely new public ARC problem from training examples and predict its test output?

**This is a reuse audit, not new autonomous operator invention.** The teacher's original inference cost is unknown. New input tasks are public ARC-AGI-1 training cases, not sealed or frontier.

## Registered arms
- A/B: frozen stronger grid/object classical synthesis P1.1.
- J: frozen P1.2 joint partition, only on B abstain.
- K: **frozen P1.3 teacher program library**, choose among four programs by original training pair exactness, without checking task IDs or test outputs. Explore each program under eight fixed dihedral coordinate conjugations (I, horizontal/vertical flip, 90/180/270 rotation, transpose, anti-transpose), maximum 32 candidates. Conjugation is also a human-defined reusable primitive. Use exact training verification, ambiguous or unsupported => ABSTAIN. Test references withheld until scorer runs.
- K runtime: all four program functions imported from frozen source, no GPT-6 call. Report candidate executions, attempted variants, accepted-but-wrong and abstained tasks; record exact original output for all test inputs. No hidden output oracle for selection.

## New public cohort
Pinned `fchollet/ARC-AGI` at `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude exactly P1.0's 32, P1.1's 24, P1.2's 24, P1.3's 4, and four previously inspected developer tasks. Select **24** filenames from remaining public training files by ascending unsigned FNV1a32(`neumann-q3-p14-20261105|` + basename), tie alphabetically. Freeze cohort IDs and engine SHA before reading bodies.

## Frozen first-run gate
- **Local novel-task library-transfer PASS:** K solves >=1 task not solved by any A/B/J, and K accepted-but-wrong =0 across all 24. Zero added = FAIL/STOP, any wrong accepted = safety FAIL. No post-result retuning and no favorable seed/task exclusion.
- If K solves zero, do not call P1.3 a learned transferable discovery policy. Retain P1.3 4/4 as a first-task teacher-interface success ONLY.
- Counts and JS `Date.now()` execution-region ms are diagnostic; teacher generation tokens, full model costs, energy, RAM remain UNKNOWN. The software raw-material Idiot Index is not defined; cost is total delivered original-task verification/compute.
- No promotion into core or sealed Q5/Q6/Q7, no implied frontier generalization, no claims of new operator primitives.

## Degraded mode
Any absence of a train-consistent library operator, inconsistency among operators on test inputs, invalid output, exception, or uncertain equivalence => ABSTAIN. An accepted but incorrect first output counts as failure, not hidden by fallback.
