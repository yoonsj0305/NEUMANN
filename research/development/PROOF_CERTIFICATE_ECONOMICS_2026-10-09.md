# Opened proof-certificate economics screen (2026-10-09)

**Decision:** `ENGINEERING_PASS / NO_LEARNED_DISCOVERY_GAP / HOLD_LEARNING`.  
**Scope:** one synthetic exact-integer product-of-sums family, four sizes, **not** a fresh G0/G1 admission, official PASS or independent structure generalization. Global Q1–Q7 OPEN.

Research basis: `c182fd3f8d8b5c711415a214e899bfefe7511a0a`. Original exact verifier, builder and compiler fetched from source at SHA256 `2b1bff0563c9e0b216fcbb840f3220499d2d0f59d494f73762560f447a42159a`. [Source snapshot workflow](https://github.com/yoonsj0305/NEUMANN/actions/runs/37887951446) succeeded; historic files are unmodified.

Opened developer-only experiment source and full receipts are separately retained in ChatGPT artifact `NEUMANN1_Certificate_Economics_G0_2026-10-09.zip` with its own SHA manifest. This GitHub note is **not** a substitute for the raw receipts, which are *not* in the repo.

Problem: `E = sum_j [ (product_i(x_i+y_i))*b_j ]` versus `F = (product_i(x_i+y_i))*(sum_j b_j)`. Exact universal integer identity. Same NEUMANN typed DAG, same DCE/hash-consing compiler on native source and factored candidate.

| n,k | Repo expansion verifier | Exact contextual rewrite trace | Existing native mul vs factored | median execution native/factored |
|---|---|---|---|---|
| 10,4 | PASS, 20.037ms | PASS | 13 vs 10 | 1.220× |
| 14,8 | NOT_VERIFIED, 71.543ms | PASS | 21 vs 14 | 1.220× |
| 16,12 | NOT_VERIFIED, 82.955ms | PASS | 27 vs 16 | 1.283× |
| 18,16 | NOT_VERIFIED, 92.071ms | PASS | 33 vs 18 | 1.346× |

The opened trace verifier applies only locally checked ring identities, especially `ab+ac=a(b+c)`, across explicit AST paths. Its accepted trace time on the first execution was 0.015–0.080ms, but the verifier is intentionally incomplete. This is a legitimate certificate-economics engineering observation, **not a 10× full-problem improvement**.

The powerful counterargument: **SymPy 1.14 `factor_terms` discovered the same factored form in 4/4 cases** (~22–50ms); a simple deterministic source-only proof-producing factoring rule also discovered it in 4/4 (~0.027–0.253ms, median of 15). Therefore there is **no demonstrated gap for learned perspective invention** on this source family. Same-answer runtime gains of 1.22–1.35× are already available to a classical solver.

11 negative/positive tests passed. No model training, parameter or threshold search, GPU, sealed set, history rewrite, model superiority, energy claim, or Q closure.

**Action:** KEEP a short exact proof-carrying rewrite certificate as a possible verifier interface; HOLD training and evaluate future candidates only when strong symbolic discovery is expensive but free valid perspective plus *paid certification/execution* has material residual room.
