# NEUMANN 1 · Frozen source-neutral Horn IR transfer gate (2026-10-17 KST)

This file is committed **before fetching or inspecting the two new external SMT2 bodies**. Old opened samples square_twice, sum_000 and fib_safe do not count as new transfer.

**Two fixed actual new external source targets** from CHC-COMP 2026, frozen upstream commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`:
1. `hopv/lia/mochi/sigma_sum_000.smt2` (HOPV/Mochi family).
2. `eldarica-misc/LIA/llreve/square_twice_merged_safe.c-1_000.smt2` (Eldarica/llreve family, near earlier opened square_twice and NOT a fully independent semantic-family test).

**Frozen before source access:** Build a **source-neutral, fail-closed semantic Horn IR** accepting an arbitrary number of original universal Horn clauses, any number of declared relation symbols and integer arities, and map names to canonical symbols with an invertible map. Never rewrite guarded arithmetic. The original source / relation count must NOT be altered, and no 9-clause/5-predicate assumptions may remain. Parse an original clause into (forall variable types, body relational atoms, arithmetic guard AST, consequent relation atom/false), record all source symbol dependencies and exact expression SHA. Independently roundtrip *all unchanged quantified clauses* through source-to-IR-to-SMT and verify satisfiability equivalence of each original body against the serialized expression, with Z3 4.13.3 and finite per-clause checks. This first gate tests representation and proof-authority fidelity, NOT automatically proving source SAT/UNSAT.
- If original source uses unsupported types or functional forms, return `ABSTAIN` with precise reason and preserve that as a coverage failure (denominator 2). No manual source-specific parser rewrite after source access; for diagnostic findings, open a clearly separate dev followup later that cannot be regraded as blind transfer.
- On successfully parsed targets attempt **unchanged** previously frozen generic 15-weight accumulator head with exact same source-extractor conditions. If no matched recurrence, `MODEL_ABSTAIN_UNSUPPORTED_OPERATOR`; do not hallucinate a formula. If matched, report exact model output separately from any human-authored scaffold.
- Strong classical original baseline: 8 seconds Z3 4.13.3 on untouched SMT source if runnable. A timeout is not impossibility.
- Total per-source cap 90 seconds, no post-hoc target replacement or new synthetic-source training. Q1-Q7 remain OPEN regardless; this is a critical engineering gate before genuine learned abstraction-family transfer.

**Scientific primary outcome:** 0/2, 1/2 or 2/2 external **source-IR accurate roundtrips**, and among them number of genuinely new-source complete original model proofs. Source-IR success must never be rebranded as autonomous operator discovery or frontier efficiency.
