# Q3N · First typed AST and genuine source/original-proof training admission

**Date:** 2026-10-18 KST. Frozen before first Q3N execution. Global Q1–Q7 OPEN.

**Problem:** Q3G already trained an untyped character GRU on 105 publicly labeled Loopy C programs and obtained 0/32 original proof on group-heldout sources. It failed on undefined variable names and malformed/unterminated math. Q3M subsequently exposed and fixed a source-to-assertion location defect, re-proving the 13 previously established **classical** original-C proofs. Instead of random architecture search, measure whether genuine *independently verified, typed source/lemma pairs* exist in sufficient disjoint families to train a meaningful learned variable-depth semantic AST operator.

### Frozen exact corpus and partition

Microsoft Loopy at commit `91fe89245a0894ec8ad3741d85ae91ce3b552b2e` with workbook Git blob `3e974edea4c856fee68d723cf867140d57094957` and dataset Git blob `17cac0f6734a39f0fe73558199cc2ad8d5c1a810`. Exactly previously admitted **150** Apache-2.0/BSD-3-Clause ancestor-license program/label pairs (398 total mapped but 248 excluded). No new license cases, no source modification or Q3F sealed benchmark source reads.

Preserve previous Q3G original group-heldout partition: groups `dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP` and `dataset/loop_invariants/sv-benchmarks/loop-lit`; **entire groups are evaluation only, not supervised model training**. This audit may read holdout *published labels for metrics*, but no model is trained or fitted to them; future neural training must not read them at all. No additional heldout results should be called blind because the corpus was previously studied.

### First audit, no neural train

1. Parse exact original source with strengthened Q3M pycparser annotation-site guard.
2. Parse all semicolon-separated public Loopy invariant clauses into **structural typed AST** nodes preserving arity and operators, with program-bound variable slots, exact source-local integer names, no undeclared symbols, and no synthetic placeholders. Arithmetic Int vs Boolean Bool sorts must be validated on the exact original C loop-state variables. Reject unsupported tokens, call/access, nullary assertion or failed typing. Preserve per-source formula and source SHA256 only in committed receipt, no third-party invariant/code text.
3. Independently replay Q3H original base/consecution/exit/overflow plus two negative controls for an entire candidate *published* invariant. Mark **PROVEN** only if all gates pass, including Q3M source assertion-site check; otherwise **NOT PROVEN**. A parsed AST without a proof is NOT a theorem or a valid positive training target.
4. Count exact SHA-unique original programs, source groups, full proof successes in **TRAIN and HOLDOUT separately**, bounded-variable references, AST clause counts, expression depths and operator vocabulary. Count all unsupported/failed originals and their reasons. This measures how many labels are defensible as proof-carrying learned-supervision seeds.
5. Proposed practical STOP/GO screening threshold **at least 20 independent source-origin training groups with 2 or more verified examples in each (40+ original proof pairs)**, and a separate source-group heldout set. This is an engineering admission threshold, not a mathematical lower bound or claim no models can learn from fewer. If unmet, STOP general Q3 claims and model training on this corpus alone; seek more authentic source-group-disjoint replayable examples. Do not pretend augmenting many clauses from the same four programs creates independent data.
6. Exclude the two still-sealed Q3F competition benchmark source families from all training and rule engineering. No paid provider or model calls. All Q1–Q7 OPEN.

This one audit resolves an essential **data adequacy / formal syntax / original proof** uncertainty, not the global learned Q3 mathematical invention theorem.
