# Frozen implementation identity before FIRST evaluation source generation

2026-10-17. Full runnable Python source in conversation ZIP; GitHub retains the pre-holdout identity and science boundary. Previous original control cases at K=17 have been used ONLY for source-independent development. No twelve-test source files exist at this point.

SHA256 of execution inputs (locally generated and frozen, **before** evaluating 12 cases):
- `cex_engine.py`: `38d460b1602f072e7bbcce6f2380bf9da44b27c1be5b38eff6591011a417794b`
- `source_suite.py`: `0850451aa7df7f02e4ab4a6eff680665ce7dbc8b3ca4f7a1a2036b4b3631b195`
- `first_run.py`: `06261ab294144a01cd9a432bc41968f6f7a704f95cf8c59a027eac595047cac0`
- `test_controller.py`: `f8a007aa8555a741faa2ebd7b3748d9886003412ec33871c7445127e8850e70e`
- exact previous source parser `engine.py`: `e5d8800fe0d3796fb9221f6c1545d1cb9ceab142a8434d1e1072d65249502599`
- previous trained frozen 126-weight model `FROZEN_LABEL_FREE.npz`: `e43208341dba128ba4c853ab42abe7ad8bd12ffdc292b1649ca0eb0eb74465ff`.

Implementation details: original SMT-LIB transition AST source parsed, existing frozen neural proposes initial `N` for first 17 identical probes, Z3 Optimize minimizes integer counterexample query index **from original transition**. An ordinary independent Z3 check proves no smaller counterexample and SAT at the chosen index. Exactly one behavioral query at that index produces residual, then the classical proposer adds `residual*max(0,n-index)` to an AST. Full original init/step/false rule reverified after each repair, at most 3 queries. Pulse unsupported and must ABSTAIN. Expert strong classical baseline parses exact original guards and generates step/plateau ramp AST directly with **ZERO behavioral queries and no neural model**. No research claim of neural operator-type invention, frontier parity or clean external transfer.

Preflight 12/12 existing unit regressions PASS, including exact checkpoint identity, source goal mutation, incorrect invariant negation, minimal-counterexample checks at several non-17 indices and pulse fail-closed. The **first 12-case evaluation does not yet exist** at this commit.
