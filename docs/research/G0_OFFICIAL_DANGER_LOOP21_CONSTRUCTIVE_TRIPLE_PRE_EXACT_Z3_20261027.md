# NEUMANN 1 | Official danger-loop21 analytic executable triple, POSTFIRST pre-Z3 reproduction freeze 2026-10-27

**IMPORTANT CHRONOLOGY**: external official benchmark source fully OPENED and native classical CVC5 1.1.2/1.4.2 results KNOWN. This is a **retrospective, assistant-authored symbolic construction** after seeing original problem, not ownweight training, not blind unseen discovery, not frontier solver-proof and not a claim the model learned it. Global Q1–Q7 OPEN / G1 HOLD.

## Pinned external original, two strong C actual baselines

- Official original source `SyGuS-Org/benchmarks` pin `13c8deb68a873635879c9a69bc78caebd340f646`.
- Exact original task `lib/General_Track/cegist-cav18/inv/danger-loop21.sl`, original bytes SHA256 **`8b3fa6aa436f67ec10b1112c3f7e8ffb1eb0e920b0268bcae5d3adf8cced539c`**, git blob SHA1 `2ce6e6131a90f0035d6936166455cec0af35ce8b`.
- Professional old CVC5 1.1.2 FIRST native source-only? **FULL native official original constraint input** (not a leave-one-out), 12s child CPU/15s wall/800MiB RSS, **TIMEOUT ~13.457s wall**. Original first entire 16 JSON SHA256 `a648346b162b3c76d4c60283f339c1a3c54016ad374128c1b4135453c27a5ba5`.
- Professional latest CVC5 **1.4.2**, verified official release ZIP SHA256 `0af677313c8277dc558d3049b192389db4d975d31c968fbd6f31cf0849ee411d`, same task and exact CPU/RSS budget: **TIMEOUT ~13.746s wall**. Modern 2-task JSON SHA256 **`7f7f57f960508b21db406880949f4567cce010c37393b9f503f9bb719887dec2`**, [native GitHub Actions #40492626599](https://github.com/yoonsj0305/NEUMANN/actions/runs/40492626599). The latest CVC5 solved the *other* old 1.1.2 timeout task `95.c.sl` by returning a candidate in 4.683s; that candidate is **not independently proved valid**; no two-hard-gap claim survives.

## Frozen analytic 32-bit actual program construction

Original task synthesizes three functions `D: BV32×BV32→Bool`, `R: BV32×BV32→BV32`, `S: BV32×BV32→BV32` simultaneously. Author's original G/B_x/B_y/A helpers, original `declare-var` and THREE `constraint` statements remain untouched, identical source hash.

Define candidate native SyGuS-compatible BV32:
```smt
(define-fun D ((x (_ BitVec 32)) (y (_ BitVec 32))) Bool
  (or (= x y) (and (= x #x00000000) (= y #x00000001))))
(define-fun R ((x (_ BitVec 32)) (y (_ BitVec 32))) (_ BitVec 32)
  (bvsub #x00010003 x))
(define-fun S ((x (_ BitVec 32)) (y (_ BitVec 32))) (_ BitVec 32)
  (ite (and (= x #x00000000) (= y #x00000001))
       #x00000001 #x00000000))
```

Reasoning: on initial state x=0,y=1, S=1 makes original helper B_y(y,S) SKIP increment once; then (x,y)=(1,1) and for every subsequent x<65539, y=x and S=0 increments y together with x. D admits either equal states or that initial exception. R=65539−x strictly decreases from positive to 0 across all original guard-valid source states x<65539. Outside original guard G, D implies x=y. The original constraints quantify OVER ALL 32bit x,y; manual trajectory argument alone is insufficient, so formally prove using an independent 32bit SMT solver.

**Independent formal check precommitted AFTER local preliminary success**: a local `libz3.so.4` `Z3_eval_smtlib2_string` first checked a MANUALLY RECONSTRUCTED copy of all three original constraints with these D/R/S definitions; result `unsat` and ~0.029s wall, file `/mnt/data/neumann_dangerloop21_constructive.smt2`. The hand-transcribed check is promising but **not** the final independent source-file identity guarantee. The next reproduction MUST fetch pinned exact original Git path, check its exact SHA, automatically parse all ORIGINAL three top-level constraint forms and all original helper definitions, substitute only the three candidate `synth-fun` declarations with these matching `define-fun`, replace SyGuS `declare-var` with free SMT `declare-const`, negate original conjunction and separately negate each original constraint. Require **4/4 UNSAT** on Z3 4.13.3.0, no manual transcribed formulas accepted for final certification. Failure/UNKNOWN must be recorded as HOLD and no celebratory claim.

## Scientific credit and scope

- A triple candidate backed by Z3 `unsat` of all 3 original constraint-negations is a **verified formal solution to this original logical benchmark's full semantic specification** (assuming source and parser validation). Grammar membership needs independent verification if original benchmark used restrictive grammars; here all original synthesized functions lack a restrictive grammar in `(synth-fun...)`.
- The **constructive reasoning itself was assistant-guided** on a fully exposed original task, not gradient-learned NEUMANN ownweight policy, not generalization to new independent tasks, and not against all possible classical algorithms. Native published CVC5's bounded timeouts do not prove other symbolic/manual solvers impossible.
- Local Z3 runtime to CHECK known candidate cannot be compared directly to published native CVC5's time to FIND candidate; do not report 500x fair solve-cost speedup or NEUMANN 10x frontier advantage. Real manual construction time, Z3 eval/serialization, data acquisition and tools costs are not included.
- Preserve original first and modern native receipts intact; no Q1–Q7 CLOSE and G1 stays HOLD.

Next after exact automatic proof: isolate this structural template (domain D, ranking R, control S) for a future *learned* program synthesis experiment on independent original task families, training A vs shuffled B and strong modern C from same original rights. This task is now DEV only; never call it blind again.
