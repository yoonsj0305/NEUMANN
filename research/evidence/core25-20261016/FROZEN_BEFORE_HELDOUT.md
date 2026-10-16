# CORE25 frozen implementation evidence prior to external source inspection

2026-10-16. Pre-registered four evaluation Git paths in PR prior to any clause inspection. This is supplemental **pre-evaluation immutable execution identity**.

- Program: `core25.py` SHA-256 `b2449d4189f69c6bbfed33e8c4757cf73fb90e8394c1b32cd061bbf8aca16f7b`.
- Trained **6,977-parameter CPU MLP** binary artifact: `frozen.pt` SHA-256 `75b287c41ecdb9c7a4fd25c3f349f02c3290ea6761aed145eb3a5859c21f4e81`.
- Training: **5,600** synthetic positive/negative candidate sample inputs, 1.439 sec CPU, only **one- or two-sort typed** Horn algebra programs. Heldout original source identities given in the adjacent first PREREGISTERED_GATE file.
- Human-designed output grammar: `R(x0,x1,x2) => (xi=Nil(Ti) => xj=Nil(Tj))`, all i!=j. Neural independently predicts a ranked slot pair; derived ghost formula uses the real source type constructors.
- Critically: Neural features are **42 manually engineered partial source summary features**, NOT full CORE21 raw whole-Horn tensor; they omit some semantic details. The parser reads the full clauses to derive these features, but the network does not see all exact tokens.
- **Previously studied development** original `goal46_000.smt2`, Git blob `9a0a1392f0cfb994a8d1501017c6ed6eb2f758ca`, exact 1,701 bytes: frozen neural top1 candidate (arg1 nil => arg2 nil) is inductively true but insufficient; original clause 4 has SAT counterexample. **Top2** (arg0 nil => arg2 nil) is source sufficient, **5/5 independent original Horn clauses UNSAT**, external from trained synthetic sorts but **development original NOT blind**. Exact classical enumeration finds same successful theorem by testing all 6 pairs.
- Do not change source code/checkpoint or target-grammar support after opening four heldout files; no backfilled successes. Global Q1-Q7 OPEN.

The source and weights are currently in working container and not remotely uploaded; this preregistration commits their hashes only.