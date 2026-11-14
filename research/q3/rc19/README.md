# Q3 RC19: learned growable-memory program versus finite-state impossibility

**2026-10-25 · RESEARCH ONLY · DRAFT, DO NOT MERGE without review.**

Frozen North Star: Frontier-level problem solving with minimum necessary computation.

Unlike prior limited Mealy/finite-gate tests, this is a **two-/multi-type well-nested delimiter stream recognizer**. Every prefix emits 1 iff it is valid and entirely closed, else 0; invalid prefixes are sticky. At depth d and k>=2 opening types, the k^d distinct unmatched opening histories are pairwise distinguished by their matching close suffix. Thus ANY exact deterministic online finite-state recognizer must have at least k^d states / ceil(d log2 k) state bits. Unbounded depth => no fixed finite-state program can be exact. A growable last-in-first-out typed-cell memory is asymptotically sufficient for this formal class. See full independent proof in ZIP.

Real NEUMANN-own PyTorch policy has six categorical parameters, **16 total trainable scalar logits**, and chooses from 128 HUMAN-defined low-level program compositions. The candidate axes specify opening interpretation, storage type (stack/queue/last-only/none), matching type, sticky failure, emission, and stored token type. Source data **340 streams (k=2, lengths1..4), 1,252 output bits**. First 12 neural restarts trained via CEM/Adam (with classical reward/elite selection): **12/12 best AND 12/12 greedy** exact. Frozen selected code `(0,0,0,0,0,0)` selects **LIFO growable memory + exact top-of-stack type matching + sticky invalid bit + output on empty valid**. A second DISJOINT seeded 12-run cohort was executed AFTER source/architecture freeze: also 12/12 best and 12/12 greedy.

The FIRST postfreeze selected-program predictions were SHA-sealed before gold was read. Independent **k=3, n=5..7 334,368 unseen streams/2,278,368 output bits all correct**, including 33,453 positive output labels. Post-first adversarial class-balanced 1,200 valid +1,200 near-miss invalid correct (2,400/2,400), type counts3/8/16, nesting depth to256. Additional depth up to511 positive/negative32/32, six single-choice mutants all rejected. Independent pairwise distinction checks at k3 depth1..5 cover 33,033 pairs. Separate all-depth induction proves correctness, not just benchmark extrapolation.

A NEW lexical token `LEARNED_DMEM_691cce3b103f` is deterministically generated from the frozen program and registered only after a HUMAN-authored soundness gate. Unknown invalid program stays UNKNOWN, degraded-mode independent reference available. **Human supplied the whole lower-level metalanguage, list VM, primitive operations, syntax compiler, proof criterion, all data and optimization. NEURAL model did not self-invent the concept of a stack or basic programming language.** Scoped program/composition selection PASS, GLOBAL Q3 oracle-free new meta-language OPEN.

Strong same-information classical exhaustive checks ALL128 programs, finds only one source-perfect, with measured CPU ~0.04115 s; neural 12 initial fits ~1.18570 CPU seconds, ~28.81× **slower**. Even before all costs, no neural advantage and no Q4 full-resource 10×. Q6 independent-author/open-family and Q7 actual Frontier Gap all OPEN.

**Full actual self-contained 19-file ZIP** with original .pt tensor, 12+12 own training receipts, source-only dataset, SHA-sealed FIRST unseen bytes, independent gold grader, balanced errors, classical baseline, formal lower-bound proof and reproducibility scripts:
`NEUMANN1_Q3_RC19_GROWING_MEMORY_STRUCTURE_20261025.zip`
SHA256: `369f3f04f4e00aeb451ba53c8454216bef58a5d5bacdea41d4eb2cb4d666b217`.
On clean ZIP extraction, `bash REPRODUCE.sh` and `bash RETRAIN.sh` both EXIT0 with first and disjoint-seed exact-weight checks. GitHub PR intentionally contains only compact extracted runtime, proof summary, and regression tests; NOT original full .pt.

**Bounded conclusion:** exact finite-state lower bound and learnable dynamic-memory **selection** are PASS, self-invented foundational ISA/grammar, 10x neural savings, unseen external authors and frontier parity are OPEN. Do not inflate local CI to global Q3 PASS.
