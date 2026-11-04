# P1.2 | Joint scene partition + executable transformation inference (PRE-REG, 2026-11-05)

North Star unchanged: Frontier-level problem solving with minimum necessary computation. All global Q1–Q7 OPEN. Prior P1.0 first 0/32 and P1.1 first 1/24 (B-A=0) remain immutable.

## New causal hypothesis
Fixed same-color component segmentation can discard the functional notion of an object. Instead of adding a longer DSL with the same parser, jointly select **(scene partition, object role/selector, extraction semantics, geometric transformation, learned palette map)** from training examples, compile a typed AST, and verify on original task output. Compare to frozen P1.1 object approach B (a much stronger comparator than P0.3).

This is entirely **classical and human-specified meta-grammar**, not neural, a JEPA or autonomous creation of novel opcodes. The novelty tested is *jointly selecting the interpretation and the rule*, within a known finite space.

## Source selection and anti-contamination
Use public ARC-AGI-1 `fchollet/ARC-AGI` upstream pinned commit `399030444e0ab0cc8b4e199870fb20b863846f34`. Select from *filenames only*, after freezing this protocol and evaluator. Exclude all P1.0 32 IDs, P1.1 24 IDs, and four pre-inspected development IDs. Sort by FNV1a32(`neumann-q3-p12-20261105|`+filename), ascending ties by filename; first **24**. Commit cohort file before reading task bodies. Do not retune this cohort.

## Arms and limits
- **B**: untouched P1.1 object-augmented 500-hypothesis classical engine.
- **J**: B predictions retained, then *only on B abstention* run a separate learned-from-example inverse-witness joint partition/transform synthesizer over up to **2,000** attempted typed ASTs; rank-free matching; ambiguous predictions ABSTAIN. No oracle test output or task ID may enter generation.
- Try partition modes: connected same-color (4/8), connected any-nonzero (4/8), all cells of a color, contiguous nonzero row-runs, contiguous nonzero column-runs. Select unique object by area or position/extent (max/min area, top/bottom/left/right, widest/tallest); extract isolated object crop, bounding-box raw crop, or original-size object canvas; transform by identity, flips, 90/180/270 rotation or transpose; optionally learn training-wide color map. These perception and transformation primitives are human-defined, so any solution is **inductive composition, not a new primitive invented by the model**.
- J includes all B results and may consume more CPU. This is **capability headroom**, NOT equal-search-budget, equal compute or 10x efficiency test.
- Unknown colors, inconsistent AST, conflicting predictions, malformed grids, incomplete/ambiguous object role, runtime failures => ABSTAIN and retain B if independently valid.
- Original test outputs delivered solely to independent scorer after both arms propose all grids. Whole original task exact including every test case and dimensions.

## First-run decision (frozen)
- Local J structural-perception headroom PASS only if J adds **at least 2 new original-task exact successes** over B, with zero lost B tasks, and anti-leakage audit passes. One added win is exploratory INCONCLUSIVE; zero added is FAIL and STOP on this cohort.
- All statuses must preserve first result. No cherry-pick reruns or changing 24 cohort, candidate order, or thresholds after results. Seed is deterministic; no stochastic optimization.
- Record attempted programs, grid executions, abstentions, time in ms (`Date.now` coarse JS isolate), and unknown memory/energy/monetary costs as null. J is expected to be more expensive; no full-system iso-capability claims.
- Even if J passes, Q3/Q4 global and frontier target remain OPEN. Next decisive gate needs genuinely new executable operator semantics, independent proof on unseen domains, matched strong Direct and complete discovered/verified cost; only then would learned good views/JEPA be considered.

## Reference theory and claims
DreamCoder PLDI 2021 introduced wake-sleep domain program library growth, and 2026 object-centric ARC research emphasizes task-dependent object identity. This experiment does not claim either idea as new. Its purpose is a decisive failure-or-headroom audit on original ARC inputs, not another synthetic-only benchmark.
