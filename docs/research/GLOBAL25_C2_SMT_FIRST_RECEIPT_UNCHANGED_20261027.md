# G0 original SMT first RUN, immutable BEFORE integrity refinement (2026-10-27)

Original prereg commit: a809f1ab4a84aea93f7643a6f73d4fdf74392a75
Fixed source script SHA256: 1e8032820bef84e49e40c40bf43b7f702263e711000b97700b5b53b565b2c5f3
First untouched results SHA256: **e4cc996d8c04836a957f6fc85942ac19eb8ba465e4c92155ce776b314bbb44c0**
Selected 12 original SMT-LIB files pinned to `ultimate-pa/ultimate` upstream commit 8e820cde14696c5a3bc8fdf2e3f7420dea35310e. Source bytes transferred via connected GitHub, SHA1 checked locally: **11/11 exact**, 12th `ring_2exp4_3vars_1ite_unsat.pri-smtinterpol.smt2` unavailable as raw bytes in local runtime (**NOT RUN, no substitution**).

FIRST, original returned statuses from local libZ3 4.13.3 C API (NOT subsequently changed):
- bignum_lra1: sat
- bignum_lra2: unsat
- pidgeonhole5: HOLD_UNSUPPORTED_OR_ERROR (original metadata says sat, Z3 internally reports unsat/error, unsupported interpolant)
- pidgeonhole8: unsat **PLUS unsupported interpolation request**
- qfhard: unsat **PLUS unsupported interpolation request**
- qfsimple: unsat **PLUS unsupported interpolation request**
- nl: sat
- mccarthy: unsat, unsat **PLUS unsupported interpolation requests**
- arrayextest: unsat
- qfexists: unsat **PLUS unsupported interpolation request**
- ring_2exp4: NOT EXECUTED because original source could not be materialized
- mbqi-z3: unsat

**CRITICAL correctness finding AFTER original run:** The preregistered wrapper mistakenly marks some scripts `VERDICTS` when `Z3_eval_smtlib2_string` contains `unsupported` on stdout after the SAT/UNSAT line, because it only scans answer tokens. Thus for whole ORIGINAL SMT-LIB script purposes these are NOT solved. Preserve the full original first result and code; add a **POST-FIRST targeted verifier correction** and score the complete script separately. Many files include a `get-interpolants` command whose original goal is interpolant production, NOT mere unsat classification. This gate must not promote partial SMT query answers into full task solves.

No model training, no ownweight, no code change to main/RC originals, no Q1–Q7 PASS. Domain-specialist Z3 can provide partial classical baseline, but Z3 ALONE is NOT an independent dual proof checker and the published `:status` metadata is not trusted authority when inconsistent. This study is a G0 prerequisite integrity audit, not G1 admission.

Complete original files and receipts distributed in conversation package with SHA checks; third-party original script licenses have NOT been reviewed for redistribution. GitHub holds a receipt only, not copied originals.