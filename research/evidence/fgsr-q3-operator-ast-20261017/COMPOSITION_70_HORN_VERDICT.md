# 2026-10-17 · Q3 compositional operator-AST learning pilot

**Scientific verdict: `FROZEN_LEARNED_COMPOSITION_SYNTHETIC_70_OF_70 / CLASSICAL_70_OF_70_FASTER / NO_AUTONOMOUS_NEW_OPERATOR_INVENTION / REAL_SOURCE_GROUP_TRANSFER_OPEN / Q1_Q7_OPEN`.**

### One executable experiment; not another natural-language theorem prompt

Our previous 15-weight model already produced source-derived polynomial coefficients for an opened genuine external CHC original. It cannot invent arbitrary new relationship operators; its source parsing and former five-relation grammar were researcher-defined. Two initially hidden external sources (Mochi sum, llreve fib) yielded **0/2 full proofs**, followed only by already-opened alpha-renaming regression (2/2), so no real cross-source learning had been established.

This separate controlled **synthetic** pilot trains a real neural model to emit **operator combinations**, not numeric coefficients in one fixed quadratic polynomial. Precisely **seven researcher-defined AST leaves**: `n`, `n²`, `n³`, `n mod 2`, `n mod 3`, `max(0,n−3)`, `max(0,n−6)`. The **sum operator grammar is also researcher-supplied**. A source program has one 2-Int Horn predicate, one initialization, one increment transition whose accumulator delta uses mathematically equivalent finite differences, and a concrete forbidden numeric state goal **with no invariant expression**. Source extractor provides the model exactly 17 source-transition behavioral probes for `n=0..16`; it does not read the original safety clause or the answer labels.

**[Pre-holdout GitHub registration](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-operator-ast-20261017/PREREG_BEFORE_COMPOSITE_HOLDOUT.md)**, frozen source preregistration sha256 `6b17778f356f9e3d5b0f79dc037f6bd60203b494240b7aecf16a911322852a33`.

- Train: exactly **28 unique semantic graphs**, seven single operators and all 21 unordered pairs (source family A), nothing with three or four leaves. Actual gradient-training `torch.nn.Linear(17,7,bias=True)` has **126 trained scalar weights**, LBFGS with backpropagation (115 closure evaluations), optimiser-only wall **56.371ms**, train **28/28**. Freeze Torch matrix, bias, probe standardization mean/std in immutable `.npz`, SHA256 **`990c7ba0b96e017180c35388da622ab292cb9d270d0e8a5fc43b0d65d72d21a3`** **before generating heldout source texts**.
- First implementation attempt completed an optimizer step but stopped **before any heldout files or training receipt** because the generic AST evaluator represented a negative integer incorrectly as the literal string `(- 1)`; the evaluator was repaired without changing model task/split/operator inventory. Subsequent single actual heldout execution is archived; no hidden-source retries after seeing evaluation performance.
- Evaluation: **all 35 unique three-leaf** and **all 35 unique four-leaf** semantic operator sums, with different source variable/relation names and arithmetic operand ordering, **70/70 compositions absent from training**. Source generator seed `20261017019`; learned head unchanged. Outputs are actual typed symbolic AST choices, not snippets extracted from the goal; evaluator checks **ALL THREE original universal Horn clauses** after substituting the candidate, with native libz3 **4.13.3.0**. Negation of every original clause must be UNSAT; no failed proposal repair.
- **Learned: exact 70/70 operator graph match, original Horn full proof 70/70, total 70×3=210 rules.**
- **Strong equal-information classical**: optimize a full-rank linear algebraic inverse of the **same seven primitive transition signatures at the same 17 probes**. **70/70 graphs and 70/70 original proofs**, with lower proposal cost: candidate-only median **4.387µs** vs learned  **47.1395µs**, approximately **10.75× cheaper for classical** on this locally measured substep. Do not use the ratio to claim end-to-end energy or full-solver speedup.
- Untrained random structural head: **1/70** original proofs. Fixed one-operator head: **0/70**. This supports that training can construct unseen *combinations* within the supplied vocabulary, not that training is mathematically necessary compared with exact classical.
- Measured median Z3 verifier+source parse for the neural candidate: **13.925ms** per problem, which is **not included** in either candidate-only timing above. First evaluation total wall **8,078.597ms**. Torch optimizer-only **56.371ms** excludes source synthesis and environment setup; monetary and energy cost unmeasured.

### Independent integrity and falsification

Read-only audit reloaded from a freshly extracted zip, checked **78/78 file SHA256 entries**, checkpoint identity, regenerated all 70 actual source-conditioned model decisions, independently checked **210/210 neural** original rule obligations and **210/210 classical** obligations. Four deliberate corruption tests all correctly failed proof authority:
1. dropped a required operator from model AST,
2. mutated original source transition while keeping original proposal,
3. changed goal to a truly reachable forbidden state,
4. deleted every selected operator.
The initial negative token-AST parser defect is explicitly disclosed. No hidden holdout graph duplicates or train/holdout graph intersections.

**Reproducible conversation ZIP**: `NEUMANN1_LEARNED_COMPOSITION_OPERATOR_AST_20261017.zip`, **54,535 bytes**, SHA256 **`373d5d63f632653e20b6924e2be524ee420ad88a7eb47ffe0a3bde04bac79a2c`**, ZIP CRC PASS, 80 members. Includes `engine.py`, `run.py`, frozen weights, complete 70 source-text files, full detailed original-clause JSON ledger, manifest, pre-holdout contract, `audit.py`, and README. **It is not a real external source dataset**. The executable code resides in the downloadable artifact; this GitHub report retains the registered study, receipt identity and scientific conclusion.

### Conclusion and next legitimate admission gate

**New bounded positive:** actual model weights can select and compose a **novel combination of previously known operator AST nodes** and generate a fully verified inductive invariant across heldout *synthetic combinations*. The 70 heldout graph structures are different compositions, not unseen primitive classes, not new external source families, and not free-form operator invention.

**Learned novelty over strong classical: none; learned cost advantage: none.** In this authored additive-basis regime the exact classical algebraic inverse already solves all 70, about 10.75× faster on candidate-only cost. The classical-first controller should skip the neural head on supported inputs rather than chasing another synthetic percentage.

**Q1–Q7 remain OPEN.** Next strict `GO` requires model-emitted *new relation/abstraction operator constructs* (not just selecting among seven given leaves), frozen typed source semantic IR from at least two real program families, truly separate pre-registered external real source-family heldout with every original clause independently checked, and complete source-matched exact classical/CEGIS/specialist solver baselines plus training/decode/verification cost. Stop scaling this tiny fixed-basis model.
