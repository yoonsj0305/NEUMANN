# NEUMANN 1 | Two-array relational H1 actually proves CHC-COMP original copy2

**2026-11-06. Scoped human-designed expressive operator success, NOT a self-weight invention.** Global Q3/Q4/Q5/Q6/Q7 remain OPEN.

## Evidence retained, not just a symbolic toy

The parent [PR #672](https://github.com/yoonsj0305/NEUMANN/pull/672) used independent Z3 on eight symbolic obligations: destination-only H0 cannot represent source-dependent array equivalence, while a new two-array quantified COPY_PREFIX relation is inductive under explicit source-stability premises. H0/H1 symbolic proof [FIRST #42200556736](https://github.com/yoonsj0305/NEUMANN/actions/runs/42200556736): **8/8** with a nonvacuity witness and wrong-store SAT witness.

[THIS actual first external original #42202057136](https://github.com/yoonsj0305/NEUMANN/actions/runs/42202057136) verified an already-opened CHC-COMP 2025 published quic3 original, `standard_copy2_true-unreach-call_ground_000.smt2`. Original source Git blob `30b3bab8834aa6f834cf493539180e6b92caf16f`, SHA256 `d026a64fc1cffd476428726eb9f883133f18044be6fc9081c2831297451afcda`, exact length 6,318 bytes.

The new human-authored typed interpretation uses 3 loop relations:

- Pair-filling two arrays with the same store value preserves `forall j<i: A[baseA+j] = B[baseB+j]`.
- Copying from B to C preserves `forall j<i: C[baseC+j] = B[baseB+j]`, while the completed earlier full-range A=B relation stays invariant.
- Completed copy yields A=C over the whole range; the final verification loop therefore cannot reach its error predicate.

The independent verifier uses `z3` against **every unchanged original Horn implication**, negated individually, refusing to replace or omit a source clause. **9/9** original proof obligations returned UNSAT. A deliberate wrong operator `C[j]=B[j]+1` yielded a real SAT counterexample in an original clause.

- `SCOPED_REAL_ORIGINAL_H1_PASS`: actual original clauses 9/9.
- `WRONG_COPY_MUTANT_SAT`: detected.
- First whole script including source retrieval and independent per-clause proof: wall **1.51 seconds**, peak process RSS **39,784 kB**. No claim this is the amortized discovery/training wall, since the human operator invention time is unmetered.
- First JSON result SHA256: `0f10e478184ff28ecf1aaab6012270dd7fff7f98126579372973c3d53bc01bd3`.
- Full source-frozen .smt2 obligation scripts retained in GitHub Actions artifact `NEUMANN-Q3-H1-REAL-COPY2-OPENED-DEV-FIRST`.

The original source was already openly studied in earlier G3 research. This is **development**, not unopened, not an independent-author formalism transfer, not a trained own-weight novel operator. A bounded 15s raw Z3 unknown/timeout from the prior G3 original does not prove mathematical impossibility of a classical algorithm, and the new H1 is itself a strong classical *human* solution.

## Decision

We now have two complementary proofs:

1. **Language limitation:** the old one-array H0 cannot express a required source-dependent equality for arbitrary source arrays.
2. **Correct richer semantics:** a human-specified two-array universal relation actually proves all clauses of a previously unresolved published original and rejects wrong variants.

This establishes that expanding the representation **can be necessary** in this scoped formal theory and is **sufficient** for this one actual problem. It does not establish that the NN discovered that representation itself.

**Stop engineering G3 size-N special cases.** The only next Q3 experiment worth paying for must create, without original target-specific labels or code from human, an executable cross-array relation **outside frozen H0**, freeze the own-weight proposer and first original task registry before source evaluation, independently prove original CHC clauses, and compare both strong native and a classical same-language structural synthesizer. If a classical generator finds the same relation faster, record it and avoid neural overengineering. Do not claim 10x without all-in equal-capability costs.

PR #674 stays DRAFT and stacked on #672. No merge to main as global Q3.
