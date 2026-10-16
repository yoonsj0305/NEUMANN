# NEUMANN CORE-26 | Goal-leakage and cheap classical proof gate



Date: 2026-10-16. Executed CPU-only independent proof. **Scientific result: GOAL LEAKAGE / CLASSICAL SUCCESS, NO LEARNED NEW ABSTRACTION. Global Q1–Q7 OPEN.**



## Exact external original identity

CHC-COMP 2026 original `ADTRem/isaplanner/goal47_000.smt2`, upstream commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, Git blob `e2e8696480c7a6d3619a780453088999a5d187eb`, SHA256 `ac6d859f30fe097d1f321392506c8e9ecbe930f6f2b42d42d41323b723162f94`, exactly 2,126 bytes. Original identity checked byte-for-byte in the live container before proof.



## Executed proof

The CLASSICAL typed goal-variable-join analyzer proposes `height(mirror(T))=height(T)` from Tree->Tree and Tree->Int source relation signatures plus the original failure goal. The researcher HAND-WROTE executable recursive interpretations for mirror(Tree), height(Tree) and nonnegative nmax; no neural weights trained or used.

Independent isolated Z3 certificate: induction leaf/node **2/2 UNSAT**. Only after induction proof, instantiate theorem in relevant goals and independently check negated authentic original Horn clauses: **9/9 UNSAT**. Three false auxiliary checks **3/3 SAT**; two deliberately poisoned authentic source rules **2/2 SAT**. Consistent relation alpha-renaming preserved the candidate type roles. End-to-end interpretation-plus-SMT verification measured around **245 ms** in one run, EXCLUDING the human design cost and therefore NOT valid complete autonomous-compute efficiency evidence.

Raw original Z3 4.13.3 checks returned `unknown(timeout)` at both 2-second and 8-second budgets. This is NOT a comparison against strongest specialized CHC verification, and not neural headroom.



## NEW decisive falsification: goal reveals supposed invention

The original two `ff` safety rules explicitly prohibit the height difference >=1 and <=-1. Their conjunction forces an equality target, so a model that outputs `height(mirror(T))=height(T)` from the final goal may merely be paraphrasing the target. `goal_leakage_audit()` programmatically detects the opposing safety guards and returns `novelty_benchmark_admissible=false`. This is not a theorem validity disproof; the actual inductive proof still matters. It is a strict warning against calling the *form* an independently invented new abstraction.



## Package and reproducibility

`NEUMANN_CORE26_GOAL_LEAKAGE_CLASSICAL_20261016.zip`, 11,709 bytes, SHA-256 **`fd9da9cad74ac8d730cfcdc5573389272e43de1b5d1472e6635eb5b4994b36df`**. GitHub PR #180 has this textual audit and hash ONLY, NOT this raw ZIP binary. Includes source code, isolated C-API Z3 bridge, 11 tests, identity checker/source fetcher, human proof interpretations, raw baseline record, receipt and exact file hash manifest. Third-party original .smt2 omitted pending license, fetched from pinned URL. Independent unpack and separately supplied exact source: **pytest 11/11 PASS**. Original source SHA verified before every official run.



## Stop/go decision

STOP training neural goal paraphrasers, preset nil slots and affine coefficients as 'invention' evidence. To test Q3, require an intermediate recursive representation or predicate not syntactically/semantically recoverable by a cheap goal unifier, on untouched genuinely different-family external sources, with frozen full-source model and matched strong classical synthesis plus full training/verifier/wall cost. Q3, Q4, Q6, Q7 still OPEN and all other official frozen gates unchanged.