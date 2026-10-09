# NEUMANN 1 — Nonlinear Goal-Observable Algebra G0 (Opened Development)
Date: 2026-10-09 KST
Base: `c182fd3f8d8b5c711415a214e899bfefe7511a0a` (PR #176 research head, **not main**)
Outcome: **ENGINEERING_PASS / NONTRIVIAL_CLASSICAL_DISCOVERY_PASS / NO_LEARNED_GAP / HOLD_LEARNING**.

## Why
Previous Krylov, rewriting, and telescoping screens showed substantial structural savings against weak brute-force loops, but classical algorithms found the same structures. This new CPU screen isolates goal-sufficient **nonlinear latent state creation**, with full original-goal algebraic verification and separate discovery/certification costs.

The original repo's `neumann1/representation_program.py` exact-integer verifier was restored byte-for-byte; SHA256 `2b1bff0563c9e0b216fcbb840f3220499d2d0f59d494f73762560f447a42159a`. A candidate must prove `Phi(F(s))=U(Phi(s))` and `G(s)=D(Phi(s))` for all integer input states. Mod-prime execution (p=65521) is a separate numerical runtime demonstration, not the basis of proof.

## First pre-measurement contract and actual completed records
First experiment: five constructed structural goal motifs, each shown once with original and once with variable-renamed surface, ten dependent views total. `3/5` motif goals have exact dimensional reduction (2->1, 3->1, 2->1), `1/5` gives a same-dimension 2->2 representation (no compression), `1/5` negative case does not close under the registered grammar. All positive proposals passed the independent original algebraic checker; five modular test inputs per view agreed.

**Critical first-stage finding:** the three compressed motifs were *already scalar goal-closed* (`G(F)=U(G)`). This is weak as evidence of discovering new latent observables. The positive runtime-only ratios against an **unoptimized sequential** original executor were 2.49x, 2.97x, 4.50x (two renamed-view median), with 256-request stationary cost projections 1.27x, 1.81x, 2.26x. Such projections are not actually timed 256-request batches.

First receipt SHA256: `1e7a7e2137602a622d9b3eca79a1dc6dc039f84b256d30233020b5d4e8cbad67`.

## Separately registered, posthoc nontrivial latent extension
After discovering the goal-closed limitation, a **new separate** developer-only contract was written for four goals (each two variable renamings) on *one shared four-dimensional system*:
`F(x,y,z,w)=(x^2,y^2,z^2,w^2)`.

For `G=xy+zw`, original `G` **is not a sufficient scalar**. States (1,1,1,1) and (1,2,0,1) share `G=2` but have next output 2 versus 4. Yet `Phi=(xy,zw)`, `U(a,b)=(a^2,b^2)`, `D(a,b)=a+b` exactly certify an unambiguous *four-dimensional to two-dimensional* goal-sufficient representation.

Classical SymPy sum-term decomposition, primitive integer monomial normalization and polynomial coefficient matching discovered this without labels, a neural model, or a GPU. Positive goals `xy+zw`, `2xy+3zw`, `(xy)^2+(zw)^2` all certified in both name views (6/6); `xy+zw+xz` deliberately exceeded the registered two-addend grammar and was rejected (2/2). Rejection does **not** prove no mathematical two-dimensional quotient exists.

The positive run-only speedups were 1.86x, 1.99x, and 2.14x by goal (two-view medians); 256-request projections with discovery, exact verification and compilation included 1.35x, 1.55x, 1.43x. Maximum observed speedup across either opened stage was <4.53x against **weak iteration**, not strongest optimized classical execution.

The extension's first technical invocation aborted before completed timing because weighted latent terms introduced 1/2 rational updates incompatible with the integer-only executor. Normalizing weighted terms to primitive monomials fixed this before the **first completed extension archive**. Earlier first results remain unchanged. Extension receipt SHA256: `5e195bc0fce858661f1625dbdbbfdf857321f2a5a45cf2bb561afd4919409ce0`.

## Attribution and decision
- The newly created *latent state* is real for the 4->2 extension, and was exactly proved rather than sample-tested.
- The discovering method is classical CAS/linear algebra; **no learned NEUMANN discovery gap** was demonstrated.
- Paid proof/discovery and runtime still give no 10x headroom even against the tested weak sequential executor.
- More specialized native symbolic/circuit methods can potentially do better; they were not exhaustively timed. This screen is *not* a strong-native comparison.
- Opened constructed cases, shared F with different goals, equivalent renamings and short timing repetitions are not independent fresh generalization evidence.
- No change to historical v102/Q34 PASS, Q5 FAIL, BP/M106 FAIL, Decision2 FAIL, or global Q1-Q7 OPEN. No fresh G0/G1/G2 admission.

**Keep:** goal-preserving semiconjugacy contract, 1D and multi-dimensional exact verifier, negative controls, cost accounting, classical comparator.
**Hold:** additional model training / hype based on these sources.
**Next:** target certified latent families where strong native structure synthesis is demonstrably expensive but a known valid perspective yields large paid-certificate headroom.

## Evidence location
Separate ChatGPT archive: `NEUMANN1_Nonlinear_Semiconjugacy_G0_2026-10-09.zip`, SHA256
`29cdb5b2c4fc4900492e6517727b6657f3e79fea5ae9909e64679d61d63a50db`, with actual `experiment.py`, `extension.py`, contracts, source snapshot, original completed CPU receipts, analysis, tests (12 PASS), Korean report and file hash manifest. **Those raw receipts are not committed here.** GitHub branch stores the decision pointer only.
