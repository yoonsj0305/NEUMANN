# CORE-22 independent supplement: learned typed-law composition and a feature-identity counterexample

Date: 2026-10-16. **STATUS: EXPLORATORY / development-only / Q1–Q7 OPEN.** This report is a *separate audit*, not a replacement for CORE-22's existing 13,026-param ghost-state work (`README.md`). Never conflate the two checkpoints or their training protocols.

## What was actually run
- A different CPU MLP with **5,187 parameters**, trained on 9 synthetic source-operator families (180 train, 45 synthetic validation), proposes human-grammar ASTs for COMMUTE, MAP-IDEMPOTENCE or ABSTAIN.
- Six omitted list-operation compositions give 150 synthetic evaluations. Initial first pilot **141/150**. After feedback and a post-hoc modification of the alternative theorem-label schema, a NEW train run produced **144/150**. The final figure is NOT a preregistered untouched blind score. Both pilot observations are retained.
- An exact formula-based specialized classical baseline on the *same bounded semantic labeling oracle* is **150/150**. 150-proposal batched median neural ~0.096ms, exact algebra ~0.019ms, training extra ~0.24s. This does not include independent original proof for all synthetic combinations.
- Source-specific development original `goal41_000.smt2` SHA256 `bcf9451674dba121a13ad2ca7f09e4c3d031bfa4f2a21c6ed3e989661dab6f34`: learned top candidate AST is take/map commutation; HUMAN-origin induction theorem schema independently checks **3/3 induction UNSAT, all 14/14 authentic Horn UNSAT**, and wrong-law SAT. Original target was seen in earlier research, and an EXACT AST identity guard rejects other sources. No unseen-original transfer is claimed.
- Conservative whole-source semantic mutation rejection is a classical front-end filter, NOT a trained semantics understanding. The neural stage still sees only a lossy 12-dimensional descriptor despite the availability of the CORE-21 whole-source AST.

## New proof of a specific input collision

For f(x)=2x, compare distinct well-typed recursive operators G0(n,L)=take(n,L)++[0] and G1(n,L)=take(n,L)++[1]. The full canonical Horn AST correctly distinguishes the 0 vs 1 constants, but the neural descriptor only has an `append-constant` bit and entirely omits its actual value. **Input vectors and all resulting model output probabilities are identical.**

Yet at n=0 and L=[] the commutation theorem holds for G0 (`[0]=[0]`) and is false for G1 (`[1]!=[2]`). Any deterministic learner restricted to this feature function has >=50% error on the balanced pair regardless of training budget or parameters. This cannot be extrapolated to a full source-AST model. Source-AST SHA-256 signatures differ, so the problem is a lossy feature projection after parsing.

## Replay and provenance

- Package `NEUMANN_CORE22_LEARNED_LAW_SOURCE_AUDIT_20261016.zip`: SHA256 `0bfdd6a04c579a789a27cfe855d650bd0e3f04493334e39df265275e986699ca` (52,744 bytes).
- Frozen checkpoint SHA256 `1c7d259beca83f73c242adf7965b62775d8c1c2b5df635433e0b9657e0e72e99`.
- 17 manifest-hashed files in ZIP, CRC PASS; independently extracted `pytest` **10/10 PASS** and frozen-only `replay.py` PASS with real pinned source supplied via an environment variable.
- The archive bytes and PyTorch checkpoint are **not in this GitHub PR**. GitHub contains this supplemental text and archive identifier only. The original external benchmark is NOT included and must be fetched from pinned upstream Git.

## Admission and next decision

Neither CORE-22 variant closes Q3/Q4/Q6. Stop training restricted fixed-grammar or small descriptor classifiers. Instead a true trainable encoder must consume dependency-complete Horn source structure, typed constructors and numeric literals *directly*, and output previously unprovided helper base/step definitions. A distinct held-out original, full independent original-goal proofs, severe mutation controls and strong matched exact classical synthesis remain mandatory. Retain all earlier receipts and Decision 3.