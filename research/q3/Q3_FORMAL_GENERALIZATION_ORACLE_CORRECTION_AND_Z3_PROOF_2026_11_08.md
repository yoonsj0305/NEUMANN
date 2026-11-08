# NEUMANN 1 | Q3 formal generalization and independent proof audit

**2026-11-08. Scientific verdict: bounded external formal synthesis PASS; global Q3/Q4/Q6 OPEN.**

## 1. Problem redefinition

Can NEUMANN discover and improve a method for generating previously unseen executable programs that meet mathematical specifications, transferring to other tasks while using no hidden solution oracle, with independent proof and total-cost gains over a strong classical solver?

Separate (A) expressing a program, (B) discovering it, (C) proving it, (D) improving a discovery policy and (E) amortizing its cost. Confusing these stages created earlier false positives.

## 2. Assumptions demolished

- Previous synthetic target search admitted a complete private teacher verification callback during selection. That is unrealistically powerful for unknown programs. A new experiment banned private oracle calls until **after candidate selection**.
- Ranking previously successful AST operators was not causally transferable. Classical same-language search consistently needed fewer checks on unfamiliar external formal contexts.
- The first external formal run failed to interpret zero-argument SMT definitions named min and max. Its eight parser errors remain in the immutable first report. A generic syntax repair preceded new untouched cohorts.
- Grammar growth and new macros are not automatically cost-efficient. Tested both and preserved failures.

## 3. Fundamental units and mathematical constraints

Input: original SyGuS-Org inverse-function synthesis specification over 4-bit bitvectors s,t. The finite input space has **16 × 16 = 256** assignments. Output: executable AST with candidate operations from the human-provided grammar. Proof: substitute the AST into the official constraints, negate the required property, and require **UNSAT** from independent SMT solver Z3.

The grammar, SMT parser, typed evaluator, anti-unification, policy scores and maximum expression depth are human authored. We did not independently invent the semantics of an unknown operator.

## 4. Implemented new architecture

Formal spec -> parser/type check -> candidate construction -> source method memory or growth -> full original checker -> independent Z3 audit -> conservative cost-aware router.

- First 16 source formal specifications certified eight programs using exhaustive 4-bit tests, then froze a learned AST-ranking policy.
- New full-domain targets were fetched only after source and method SHA were recorded.
- Failure-triggered grammar closure generated 13,034 new bounded expression DAGs, while retaining the original 966.
- Fully verified source programs yielded two new reusable constant-expression macros, but these provided no additional solves.
- Cost-aware control learned from three prior external original cohorts to delete negative-utility learned stages, favoring classical degraded mode.

## 5. Immutable first-run evidence

Upstream benchmark: SyGuS-Org/benchmarks, commit 13c8deb68a873635879c9a69bc78caebd340f646, 2019 General Track bv-conditional-inverses.

| Run | Fresh disjoint original tasks | Result | Fair control and root-cause |
| --- | --- | --- | --- |
| #42432369260 | 32 bvsle/bvuge original tasks | 20 solved, 8 parser errors, 4 unsolved | Learned 5,784 checks vs cold 4,175, both 20; ranking FAIL |
| #42432544881 | 32 bvult/eq after generic parser fix | 25 solved, 0 errors | Learned 12,491 checks vs cold 7,091; ranking FAIL |
| #42432876840 | 32 bvslt/bvule | Old 966 grammar solved 29; automatic growth to 14,000 expressions solved 30 | Same larger-language classical solved 30; representational gain, not learned superiority |
| #42433082556 | 32 bvugt/ne | Macro-first 30, original cold 30 | Source extracted two valid constant-expression macros; macro-first 31,110 checks and 46.82 ms vs original cold 3,016 checks and 5.55 ms |
| #42433229391 | 15 previously untested bvsgt tasks, with earlier inspected bvshl1 excluded | 10 solved, 0 errors | Historical method deletion chose cold (5,013 checks) over harmful learned ranking (6,926 checks); both solve 10 |

All task names were predeclared and frozen before target content was fetched; old FIRST results were never rewritten.

**Disjoint external formal task inventory = 143. Distinct externally solved tasks = 115.** The first parser-error cohort remains blocked; totals must not be silently normalized. All tasks still come from the same official benchmark provider and the same bounded inverse-function problem style.

## 6. Independent third-party proof

GitHub Actions run #42433390357 (2026-11-08) uses Z3 4.13.3. A separate translator generates SMT-LIB using the original official problem definitions, candidate AST as a defined inverse function, and a negated original constraint.

- **299/299 distinct program-verification records: UNSAT**
- 0 SAT counterexamples, 0 verifier errors, 0 originally claimed proof successes unconfirmed
- These records correspond to **115 unique tasks, 184 unique task+AST pairs, 84 distinct ASTs**, not 299 independent tasks.
- Synthetic deliberately correct and deliberately incorrect programs were independently verified as UNSAT and SAT respectively.

The result proves full finite 4-bit validity under Z3 SMT semantics. It does not prove global Q3 autonomy, arbitrary word-width transfer, or human-independent semantic invention.

## 7. Corrected no-secret-oracle synthetic experiment

GitHub Actions run #42432759299 selected all programs from observed input/output pairs without querying any secret complete target teacher. Full-domain exactness was only checked **after** selection.

- 16/16 source programs exact.
- 48/48 new-width two-family synthetic tasks solved by learned method; matched-expression-language cold first-consistent baseline 36/48.
- Learned 389 candidate checks vs cold 12,724; zero hidden teacher-oracle calls before selection.

This is a **scoped positive causal transfer** across human-constructed related parameter families, not independent-author Q6 or fully general Q3.

## 8. Cost, risks, and tenfold innovation options

Total marginal research cost = source program discovery + method inference + target synthesis + counterexample checks + independent proof + fallback + regression maintenance. Candidate checks are only one component. No validated end-to-end Q4 10×.

Risks: training-target leaks, same benchmark provider dependence, operator-grammar truncation, success-biased task selection, Python timing noise, reusing exposed targets as supposedly blind, missing domain adapters, and incorrect universal claims. All are explicit acceptance-gate failures.

Four potential redesigns: (1) proof-carrying semantic-constructor invention rather than AST root preference; (2) type-polymorphic semantic role IR usable by strings, arrays, bitvectors and grids; (3) decision-theoretic cost-limited method router with abstention; (4) strictly preregistered new independent-author source and target suites with matched classical full-language budget.

## 9. Recommended next step and gate

**Priority: proof-carrying semantic construction + conservative cost routing.** Stop brute-force grammar widening if the next expression budget yields only one new formal solution. To close global Q3, require a genuinely new **executable constructor method** automatically induced from source proof/counterexamples, then show causal additional exact solves on unknown independent-author domains versus the same-language strong classical baseline. Require formal or independent reference evaluation, no private target oracle in selection, amortized cost and reproducible immutable FIRST records.

**Final status:**
- Bounded 4-bit formal program synthesis: SCOPED PASS (115 unique solved originals).
- Independent SMT program validity: SCOPED PASS (299/299 Z3).
- No-secret-oracle synthetic method transfer: SCOPED PASS (48 vs 36).
- External learned ranking superior to equal-grammar classical: FAIL.
- Bounded automatic grammar growth: SCOPED PASS on one new external task, but classical matches.
- Source-derived reusable macros: syntactic/semantic derivation PASS, utility FAIL.
- Cost-aware degraded-mode method deletion: SCOPED PASS (15-task fresh original check).
- Universal Q3 / 10× Q4 / cross-author cross-domain Q6: **OPEN**.

**GitHub evidence:**
- Full formal FIRSTs: https://github.com/yoonsj0305/NEUMANN/actions/runs/42432369260 ; https://github.com/yoonsj0305/NEUMANN/actions/runs/42432544881 ; https://github.com/yoonsj0305/NEUMANN/actions/runs/42432876840 ; https://github.com/yoonsj0305/NEUMANN/actions/runs/42433082556 ; https://github.com/yoonsj0305/NEUMANN/actions/runs/42433229391
- No-oracle correction: https://github.com/yoonsj0305/NEUMANN/actions/runs/42432759299
- Independent Z3 proof: https://github.com/yoonsj0305/NEUMANN/actions/runs/42433390357
