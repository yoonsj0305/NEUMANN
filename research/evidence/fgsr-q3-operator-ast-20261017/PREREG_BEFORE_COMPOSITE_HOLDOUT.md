# NEUMANN 1 · Operator-AST composed-structure learning pre-holdout contract (2026-10-17)

## Correct scientific scope
This is **controlled synthetic research**, not an independent external source-family proof and not a Q1–Q7 closure. Seven researcher-specified operator leaves (n, n², n³, n mod 2, n mod 3, ramp(n−3), ramp(n−6)) may be combined with +. This explicitly defined grammar is not an autonomously invented new operator family.

### Frozen TRAIN → HOLDOUT semantic graph split
- Training: exactly 7 one-leaf graphs plus 21 two-leaf graphs. A gradient-trained PyTorch mapping consumes **17 source-derived transition-behavior probes**, never the original Horn safety goal or AST graph label at inference, and predicts a seven-bit AST leaf-selection graph. No three/four-leaf graph occurs in training.
- Holdout: exactly 35 distinct three-leaf and 35 distinct four-leaf graphs, **70 unseen semantic combinations**, fully enumerated. Distinct source rendering/variable naming. No post-holdout retraining/tuning.
- Every generated source has exactly three unchanged quantified Horn assertions: initial state, recursive transition, and a concrete forbidden point *without an invariant equation*. An independent native libz3 4.13.3 parser checks the negation of each original universally quantified clause after inserting the model's emitted compositional SMT AST. Only all 3 UNSAT counts.
- Stronger classical alternative uses the **same 17 numeric source probes** and an exact rational linear solve against seven same predefined primitive-delta signatures. Compare untrained identical NN, fixed one-leaf baseline, training and candidate-only cost, SMT verifier cost separately.
- All results remain scoped to researcher-generated programs. Classical equivalent or faster means **no proof of learned necessity/efficiency**, even if model generalizes to unseen compositions. Native independent real-source-family Q3 and frontier Q7 remain open.

Local frozen preregistration SHA256 `6b17778f356f9e3d5b0f79dc037f6bd60203b494240b7aecf16a911322852a33`. Original source expression probes are extracted from the transition recurrence AST with no direct access to the hidden proof target.
