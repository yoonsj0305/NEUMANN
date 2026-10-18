# Q3O: first source-pinned external LIA + NIA SyGuS original proof AST seed experiment

Date 2026-10-18 KST. Frozen before first execution. All global Q1–Q7 OPEN.

**New real source**, different from Loopy C and the Q3F two unopened CHC holdouts:
- `SaswatPadhi/LoopInvGen` Git commit `6ac90265b11431c9477dfbd33e3e3380234c0499`, repository MIT license in `LICENSE.md`, Git blob SHA1 `1e853cd500e1317b7c2ad0a2514b548c32c46f5e`. The two real benchmark bodies remain exclusively in their upstream pinned repository; individual benchmark provenance/rights require further audit before distributing any material.
- LIA first fixed original: `benchmarks/LIA/2016.SyGuS-Comp/array.sl`, Git blob `b1c26aaddfcbab90f2dd47b6e84faaae973be200`.
- NIA first fixed original: `benchmarks/NIA/2018.CHI_InvGame/s10.desugared.sl`, Git blob `f066be50786c6a41bdaf0b0e2df399c579469f3f`.
Both source group and exact source files selected before running new solver. No source-specific candidate lemma or solution formula is supplied.

**Source language / proof:**
1. Parse actual SyGuS-INV source with balanced SMT-LIB s-expressions. Require exactly one `synth-inv` and matching original `inv-constraint`, `define-fun` pre/trans/post and exact typed integer state signatures. Reject unsupported commands/operators/functions or malformed source. Never infer unknown cases as passed.
2. Derive authentic original Z3 state symbols and original pre/trans/post relation AST from those formulas, not approximate the C code or substitute a synthetic task.
3. Build a direct `Reach` and `BadExit` CHC with Z3 SPACER, fixed 5s per case, strong classical baseline. A theorem PASS requires original reachable BadExit **UNSAT**; `sat` is not a success; unknown/timeout are unresolved.
4. Obtain an inductive cover candidate, if solver offers one, through `get_cover_delta`. Independently prove **all three unchanged original VC obligations** `Pre=>I`, `I & Trans=>I'`, `I=>Post` UNSAT under the same typed state variables. Only then count it as a reusable original-proof-backed typed AST seed. Any nontrivial formula must use bound original state slots and have valid Int/Bool sorts. Never claim all `unsat` CHC queries automatically provide a verified trainable invariant.
5. Compare first two source groups, record actual solver result, cover extraction and soundness, source SHA, wall and queries, with zero model or Q3F use. No hiding failed files, no retrofitting after seeing result. If only direct proof succeeds without reusable cover, report that candidly and decide on proof-carrying extraction adapter.
6. No claim of learning a novel Q3 operator, Q4 efficiency 10x, Q7 frontier parity, or representatively independent source-group generalization from just these two cases. Future training must exclude separately registered evaluation families and avoid duplicates across benchmark mirrors. Q1–Q7 OPEN.
