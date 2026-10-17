# NEUMANN Q3 · Counterexample-Selected Source Query & Automatic Ramp-AST Repair
**Preregistered 2026-10-17, before generating or inspecting the 12 new evaluation programs.**

## Frozen science question
The earlier verified adaptive controller hard-coded extra behavioral probe index 17. Here the controller MUST get the **next query index from a fresh SMT counterexample over an original source transition under the current candidate relation**, with an exact `minimize n` in integer SMT. The model's existing 126-weight label-free AST checkpoint **e43208341dba128ba4c853ab42abe7ad8bd12ffdc292b1649ca0eb0eb74465ff** stays unchanged. The first 17 delta probes are all 1, so its prediction should be exactly `N` for each evaluation case. No learned weights or grammar tuned on evaluation outputs.

## Twelve source programs, first-run holdout generated only after this contract
Seed **202610171220**. Exactly **5 step** sources, **5 finite-plateau** sources, **2 periodic-pulse** sources. Threshold K from **18..65**, positive jump amplitude **1..3**; plateau L=K+(5..18); periodic period **3 or 4**. Source generated with variable/relation renaming and operand-association variants. Source has two Int arguments in one uninterpreted predicate and **three original universal Horn clauses** (init, transition and forbidden state), no hidden target relation in forbidden goal. n'=n+1, accumulator transition increment:
- step: `1 + a * indicator(n>=K)`,
- plateau: `1 + a * indicator(K<=n<L)`,
- periodic pulse: `1 + a * indicator(n>=K and (n-K) mod P ==0)`.
Goal names a single **unreachable** concrete state after dynamics; no full invariant text.

## Frozen controller
1. Check previous learner frozen checkpoint, source_probe 0..16 and proposed `N`; substitute its current candidate into **all original 3 Horn clauses** and accept only 3/3 UNSAT.
2. If candidate fails, derive **the least n>=0 satisfying a local induction counterexample** by SMT Optimize on the original source transition AST: `delta_source(n) != candidate(n+1)-candidate(n)`. The n is obtained from the SMT model, not guessed from the source-name, hidden K, goal or user.
3. At that **actual SMT-selected index** ask exactly one new source delta query (the probe count must be measured). Let residual `w=observed_delta - predicted_delta`; append `w * max(0,n-index)` to candidate AST. This synthesizes instances of a **human-prescribed ramp operator grammar**. Repeat only upon full-original proof failure, max **3 adaptive queries**, then ABSTAIN.
4. All original Horn clauses are checked using native Z3 **4.13.3** with fresh contexts for each. A local sampled fit does NOT count as proof. The minimization solver's result is corroborated with unsat for all earlier n and sat at selected n.
5. Equal-info strong classical code examines original guard AST directly and returns exact jump/plateau ramp macro under a predeclared syntax class; it requires **0 extra behavioral queries** and must independently prove originals. Pulse is unsupported by this direct step/plateau syntax class, MUST ABSTAIN (unless source solver directly finds a different full proof). Fixed `N` baseline, frozen learner without queries, controller and exact symbolic baseline all reported; training, inference, query and verifier work separated.

## Reporting
Expected bounded outcomes: step **one** adaptive query; plateau **two** adaptive queries; pulse likely **ABSTAIN** at the cap. This is a predeclared expectation, not guaranteed performance. The evidence must include all 12 sources, all solver attempts, selected query indices, candidate ASTs, per-clause independent UNSAT/SAT/UNKNOWN, negative mutated goal/transition tests and full cost. Failures count. Do not tune and rerun heldouts for a pass. No claim of **neural invention**: it is SMT-guided **classical** operator-instance creation. The next true Q3 requires frozen learned AST generator to invent operator **types** on new real external families and exceed expert classical controls. Q1–Q7 remain OPEN.