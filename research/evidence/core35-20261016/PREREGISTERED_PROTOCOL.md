# CORE-35 frozen external-source protocol — preregistration before reading benchmark contents

Timestamp (KST date) 2026-10-16. The source file(s) below were selected by filename only. At preregistration they have NOT been fetched, read, inspected, edited or used for fitting in this study.

## External holdout and control
- CHC-COMP upstream repository `chc-comp/rust-horn` (`master`) / `trees-2-inc-all-safe.smt2`
- Matched negative control: `trees-2-inc-all-unsafe.smt2`
- This is a different source family than NEUMANN CORE-31/32's `ADTRem/isaplanner/goal52_000.smt2`. Filename hints SAFE/UNSAFE, so benchmark *labels are not blind*. No claims of fully label-blind generalization.
- Freeze the pinned SHA-256 on first fetch and do NOT change files after inspection.

## Frozen decision gate and computational treatment
1. First try the strongest available direct classical Z3 Horn/fixedpoint path on the unmodified actual source, separately for both files, enforcing 10 second timeout per source in a separate process.
2. Record syntax, Z3 version, source hashes, solver response, wall, errors, parser status and actual independent counter-control.
3. If direct solver proves safe and unsafe as labeled, **stop**: no learning required, `CLASSICAL_ALREADY_SOLVES`.
4. If direct source is unsupported or unknown: **ABSTAIN**, record exact blocker, NEVER label a neural success or Q closure.
5. No formula hand-supplied after inspecting benchmark; no renaming, manual theorem skeleton, hypothesis-language tailoring, or training on target permitted. External holdout may never become training data in the same study.
6. Only if a subsequently FROZEN whole-source-plus-goal learner exists before opening a NEW external family, admit learned helper emission and compare with the same strongest classical baseline, original proof and complete cost. Today's experiment cannot satisfy that target.

This protocol tests *a necessary interface/admission boundary*, not Q3 or Q6 learned transfer. All global Q1–Q7 OPEN.

## Runtime
- Native libz3 C API through Python ctypes if `z3-solver` Python package unavailable; invoke `Z3_eval_smtlib2_string` in a fresh subprocess and context for each input.
- Need explicitly handle SMT-LIB2 `(query ...)` vs `(check-sat)` and do not assign a proof verdict to parser failure or UNKNOWN.
- Timeout is a 10 s process kill (wall), not Z3-internal resource guarantee. Count initialization and reading within subprocess timing where measurable.

Freeze recorded before any content fetch.
