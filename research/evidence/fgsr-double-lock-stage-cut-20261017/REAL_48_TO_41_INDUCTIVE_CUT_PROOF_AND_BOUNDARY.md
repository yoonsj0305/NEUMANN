# NEUMANN 1 | 2026-10-17 | genuine CHC-COMP 48→41 source proof via inductive control-stage cut

**Scientific status: `EXTERNAL_48_HORN_LFP_SAFETY_EQUIVALENT_41_CERTIFIED / ORIGINAL_SAFETY_UNRESOLVED / LEARNED_AUTONOMOUS_NEW_RELATION_OPEN / Q1–Q7_OPEN`.**

## Exact original provenance and previous work

Public, actual CHC-COMP 2026 `chc-comp/chc-comp26-benchmarks` upstream commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, source `ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2`, **source SHA256 `2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645`**. Original **48 universal quantified Horn clauses**, single `Inv(A,B,C,D,E,F,G,H)` predicate, false goal. The original is an **OPENED development source**, not a clean heldout evaluation. No trained model used in this theorem synthesis. Earlier mathematical first-order tautology deletion **#27, #30, #31, #33, #34, #45** established a fully FOL-equivalent **48→42** reduction but neither original nor 42-reduced problem was fully proven safe/unsafe (native solvers TIMEOUT or UNKNOWN). Historical 46/48 invariant attempt is **NOT an inductive original safety proof**.

## Newly discovered human-directed classical stage invariant M

Define `M(A,B,C,D,E,F,G,H)` by:

```smt
(and (<= 0 H) (<= H 4)
 (=> (< H 4) (and (= D (- 1)) (= E (- 1))
                  (= F (- 1)) (= G (- 1))))
 (=> (and (>= H 1) (< H 4)) (= A 0))
 (=> (and (>= H 2) (< H 4)) (= C 0))
 (=> (and (>= H 3) (< H 4)) (= B 0))
 (=> (= H 4) (or (= D (- 1)) (= E (- 1)))))
```

This is a **manually/source-conditioned classical relation formula**, not neural-proposed, not a posthoc learned operator discovery. Local native Z3 **4.13.3.0** substituted M for `Inv` in **each of ALL original generative rules 1..45**, set `CHC_COMP_FALSE=false`, and independently refuted the negation of each entire untouched universal rule: **45/45 UNSAT**. The original initializer #3 is included. Therefore the **least reachable `Inv` relation L is a subset of M**, by source-transition induction.

The original source clause **#28** has `H=5` in its antecedent, impossible for any `Inv` tuple satisfying M because `H<=4`. Replace only original consequent with false and prove the quantified implication via fresh Z3 solver: **antecedent UNSAT**. Hence the least fixed point of positive original Horn rules is unchanged if we drop #28. This is a **least-fixed-point CHC satisfiability/safety-preserving reduction**, NOT full first-order equivalence under arbitrary interpretations. The six previous rules #27/30/31/33/34/45 were each rechecked **twice** with completely uninterpreted `Inv` and `CHC_COMP_FALSE`, **12/12 UNSAT** negated source clauses, and may be removed as genuine first-order tautologies. The exact retained original indices (41 total) and deterministic reduced-SMT2 SHA256 **`4a6f0f2af8f2ee979fcab12bda0256b30c2bafb2eafd526095e27a8a18cc2303`** are recorded in the original verification ledger.

**Result: 48 original Horn clauses → 41 least-fixed-point safety-equivalent Horn clauses, total seven proven removals (14.58% fewer).**

### Why this is a valid source safety-satisfiability reduction
Let T be the immediate consequence operator for the source Horn rules (ignore the goal until closure). The original initializer and every original generative rule preserve M, so by induction the least fixed point `L=lfp(T)` is within M. The #28 transition's antecedent requires a member of L with H=5, impossible; it does not add a state to L. The remaining 41 original rules induce the same least reachable relation; six other removed rules were first-order valid in *all* interpretations. Both original error clauses #46 and #47 and final false clause #48 are retained, and the reachability of `CHC_COMP_FALSE` is unchanged. Therefore the two source Horn systems have the same satisfiability status although **arbitrary nonleast first-order `Inv` models need not be literally identical**.

## Critical falsification: the core multi-premise structural obstacle

A stronger but false guess replacing `H=4 => (D=-1 OR E=-1)` with **exclusive OR** is disproven by original clause #25, which allows H=4 while D=E=-1: source negated induction query **SAT**.

Most importantly, original triple-premise guards **#29, #32, #35, #36** have **SAT** antecedents when each `Inv` call is interpreted by M. They cannot be dropped. Each three-premise rule joins separately permitted states, so pointwise `D=-1 or E=-1` on *every* tuple does **not** imply that simultaneously supplied antecedents cannot carry D=2 and E=2 in different `Inv` facts. **This is source-grounded evidence of why a single-tuple local abstraction is insufficient**. The remaining task genuinely needs a multi-state/cross-premise relation construction or proof strategy rather than deleting source clauses using invalid independence assumptions.

Additionally, candidate M alone yields **SAT** counterexamples to the original safety clauses #46 and #47, while the final CHC false-link rule #48 is UNSAT after negation. Therefore **no complete 48/48 or 41/41 safety certificate** is admitted. Direct native unbounded solver run on exact 41-clause reduced source, 9-second CPU subprocess limit: **TIMEOUT**. Full original safety SAT/UNSAT remains UNKNOWN.

## Two independent proof implementations + tangible artifacts
1. **Native libz3 local executable:** source-pinned `inductive_stage_certificate.py` checks all 45 original generative clauses, all six original arbitrary-predicate tautologies twice, source #28 infeasible, four original three-premise guards SAT, both safety clauses SAT under M, false exclusive-OR variant SAT. Same resulting reduced source SHA. Independent fresh temp archive extraction replayed this full actual proof and verified offline manifest and receipt.
2. **Independent GitHub Actions Z3 4.13.3 python verifier:** [workflow run #39025969490](https://github.com/yoonsj0305/NEUMANN/actions/runs/39025969490) **SUCCESS**, exact upstream SHA pinned. Actual artifact ID **12098686947**, `original_generative_inductive_unsat=45`, six original uninterpreted tautologies all UNSAT, source #28 antecedent UNSAT, original #29/32/35/36 antecedents SAT, #46/47 original safety SAT under M, same retained 41 and exact canonical reduced SHA. [Independent executable](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-double-lock-stage-cut-20261017/independent_48_to_41_z3py.py).
3. **User downloadable full local source/evidence ZIP** `NEUMANN1_REAL_48_TO_41_INDUCTIVE_STAGE_20261017.zip`, **9,244 bytes**, SHA256 **`bc3b9d2e83292228ccc679209e2870de0d68557f8094cbf3fecb939f36d189b7`**, 6 files, ZIP CRC PASS, 5/5 manifest hashes PASS, actual **fresh directory and source byte** re-proof of all original claims PASS. Includes original source fetcher (no redistribution of public benchmark bytes), standalone ctypes/native 4.13.3 independent verifier, source-specific explicit M, exact clause ledger, independent audit and README. After `python fetch_pinned_source.py`, run `python inductive_stage_certificate.py --source source_48.smt2` and `python audit.py`.

**Strict scientific admission:** `SOURCE-SPECIFIC_CLASSICAL_INDUCTION_AND_SOUND_LFP_REDUCTION_POSITIVE` only. One additional original CHC clause eliminated beyond first-order tautology screen. No neural training, no learned model inference, no unseen external source transfer, no frontier/economics gain, and **Q1–Q7 OPEN**. Stop repeated textbook polynomial head training and source-count gaming. Next genuine capability gate requires an independently validated **multi-state conditional/cross-premise relational operator generator**, on preregistered externally sourced unseen program families with full original safety proof and strongest classical CEGIS/full inference cost baseline.
