# NEUMANN 1 | H0 impossible for relational COPY, minimal H1, actual source evidence

Date: 2026-11-06. Global Q3/Q4/Q5/Q6/Q7 OPEN.

## Delete the wrong search
The trained own-weight four-token G3 invariant student [PR #671](https://github.com/yoonsj0305/NEUMANN/pull/671) proved init2/init3 2/2 with unchanged original Horn clauses, but the explicit human template also solved 2/2. This student only emits predicates about ONE destination array compared against absolute constants. Training it longer cannot express the general relation between an independently varying source S and destination D.

For any Boolean predicate P(D) of destination D alone, fix D and compare two different S values (same copied cell versus different copied cell). The truth value of P(D) is unchanged while the desired cross-array copy relation changes. Thus P(D) cannot represent that relation for every possible S and D, regardless of learning budget.

## Real source-free symbolic proof
[First successful 8/8 Z3 obligations #42200556736](https://github.com/yoonsj0305/NEUMANN/actions/runs/42200556736). Original initial 4/8 checker run #42200244464 and diagnostic #42200411446 failed on SAT-witness syntax; failures remain in immutable CI history. The corrected witness avoids unsupported const-array constructors in Z3 4.8.12. No benchmark source files are read by the theorem runner.

The minimal new typed atom is COPY_PREFIX(S,D,src_base,dst_base,cursor), representing universally quantified equality D[dst_base+j] = S[src_base+j] for each j in [0,cursor).

Under explicit assumptions of unchanged S, bounded cursor, and writing exactly the matching source element into D:
- H0 universal representation impossibility: UNSAT; genuine distinguishing witness: SAT.
- Empty-prefix initialization: UNSAT counterexample query.
- Preservation by one source-selected store: UNSAT.
- Untouched destination suffix: UNSAT.
- Completion at an arbitrary in-range index: UNSAT.
- Nonvacuous prefix model: SAT.
- Deliberately corrupted store: SAT counterexample.

Total actual Z3 process wall in this source-free batch: 79.703 ms. This is NOT whole-system cost and the conditional theorem does not prove an entire external original CHC source.

## Real, previously opened external-author COPY source audit
[First operator-interface audit #42200953203](https://github.com/yoonsj0305/NEUMANN/actions/runs/42200953203) of pinned CHC-COMP 2025 repository commit ddd279cab0717db6effe69baad451a8eb04ffd86.

- standard_copy2 original, 6318 bytes, Git blob 30b3bab8834aa6f834cf493539180e6b92caf16f: loop relations contain 3, 2 and 3 array operands, 1 same-original-clause linked store/select copy motif.
- standard_copy3 original, 8201 bytes, Git blob f8fd0b73c3aa45ee5f49426416a378bcfc462605: loop relations contain 4, 3, 4 and 2 array operands, 2 linked copy motifs.

Both sources are TYPE INCOMPATIBLE with H0's one-array per-loop input contract. This is a measured representation mismatch, NOT a successful solution or original-clause proof for these COPY benchmarks.

## Critical next capability gate
An actual own-weight student must propose a NEW typed operator beyond H0 from evidence without a human preassigning the semantic answer. Compare untrained, same-budget classical CEGIS, existing human H1, and strong native, with exact original Horn-clause verification, pristine independent original FIRST, and end-to-end amortized costs. The present H1 is HUMAN-CONSTRUCTED and independently proved only for an abstract loop. Cross-family Q6, novel Q3 and total-cost 10x remain OPEN.

Degraded mode: on unsupported source relations, ABSTAIN or use strong classical fallback. Do not retry H0 or claim new ability from static motif counts. No ARC EVAL task IDs used.
