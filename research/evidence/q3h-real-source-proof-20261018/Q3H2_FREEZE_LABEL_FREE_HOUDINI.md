# Q3H-2 predeclared classical-first, LABEL-FREE actual C invariant synthesis

2026-10-18 KST. This extension tests **existing already-opened Loopy development original C sources only**. Source files and postconditions can be read (normal safe-program proving), but the published Loopy invariant text MUST NOT be supplied to candidate generation. No claim of fresh blind transfer.

Freeze, BEFORE execution:
1. Real source paths: `LinearArbitrary-SeaHorn/VeriMAP/TRACER-testabs7_VeriMAP_true.c`; `LinearArbitrary-SeaHorn/invgen/simple.c`; `LinearArbitrary-SeaHorn/sharma_splitter/popl.c`, all in published Microsoft Loopy 2024 archive at Git revision `91fe89245a0894ec8ad3741d85ae91ce3b552b2e` and previously source-identified by Q3H independent proof.
2. No published workbook labels to proposer. Permitted source-only inputs: the unaltered original C AST, original assertion, variables/sorts, constants, guard conditions, loop init and transitions.
3. Bounded precise classical candidate grammar: `x<=k, x>=k, x==k, x<=y, x==y, x>=y` with `k` from C source literal constants, plus `0,1,-1`; include guarded implications of those candidates using genuine branch predicates, and optionally their negation. No manually inserted Loopy invariants or target-specific lemma.
4. Classical Houdini strongest inductive subset: delete candidates whose base or step negation is SAT under current conjunction; iterate until fixed point. A candidate is **not a theorem by itself** without all original base/step, postcondition and C signed overflow checks. SAT/UNKNOWN fail-closed.
5. Compare complete proof of the untouched 3 original C safe programs; **postcondition goal false** and weak-empty invariant as falsification controls. Baseline is this exact classical source-only algorithm, not a neural model.
6. If any case remains unknown/unsupported, preserve failure, do NOT retrofit grammar from published labels. No extra syntactic heuristics after viewing results without a separately labeled repair.
7. No independent group claim (opened originals); Q3 neural learned-structure novelty, Q4 cost headroom, Q7 frontier gap remain OPEN. Avoid training neural weights to mimic any faster exact classical candidate.

The goal is a precise **source-conditioned no-label automatic mathematical structure discovery** result, classically implemented, suitable as a strong benchmark for any future neural method. No assertions that classical algorithms are universally optimal.
