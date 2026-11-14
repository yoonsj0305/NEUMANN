# Q3 contextual operator promotion (RC0)

**Research-only deterministic compiler, NOT NEUMANN neural primitive invention.**

When an externally generated Python function encodes a literal recolor expression `2 if v==1 else v`, this component converts that executable definition into a reusable parameterized operator `dst_color if v==src_color else v`. It derives the parameter values only from two demonstrated input/output examples, verifies demonstrated behavior, memoizes the compiled function, and abstains if source context is insufficient or contradictory.

Local, full evidence archive: `NEUMANN1_Q3_CONTEXTUAL_OPERATOR_PROMOTION_RC0_20261024.zip` SHA256 `dba8fb2adffa6c21f5e663c9e9c1d4ad5cb90199fe99e7a46cacc5bbc39e0b5e` (provided in ChatGPT conversation, **not committed here**).

Actually executed offline tests on four frozen GPT-6-authored programs for **four PUBLIC ARC-AGI-2 training tasks**:
- after-first historical stress 301/400 unedited → 400/400 bound;
- separate seed 755/1000 unedited → 1000/1000 bound;
- 250/250 third-demo holdout for the adapted periodic operator;
- 600/600 independently calculated further context identities;
- 10/10 negative controls, four frozen outputs replay in subprocess;
- frozen original source SHA256 `dd4704e2b3b4e8e62a81cef57ec39929559c1450da3b5f78e85f7b06f571f016`.

A smaller CI-supported proof is in `tests/test_q3_operator_promotion.py` (200 random palette bindings and source-evidence/AST controls).

**Limits:** The new component is a HUMAN-DESIGNED classical compiler around GPT-6's previously authored code, not an independently trained NEUMANN model, nor newly unopened author tasks; all palette tests are transformations of the same four already-opened public tasks. No neural-only improvement over a classical semantic binder. The AST whitelist is **not** a secure sandbox, which would require OS isolation for hostile model-produced code. Global G1/Q3, all-in Q4 10x, Q6, Q7 remain **OPEN**. Do not merge into main without safety review.