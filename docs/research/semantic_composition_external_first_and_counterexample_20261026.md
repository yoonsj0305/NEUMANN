# NEUMANN 1 · Semantic Program Composition and Causal Baseline · Original External First Evidence

**26 October 2026. Same discovery-policy center. No new RC/PR. All global Q1–Q7 OPEN.**

## Why this actual study matters
Earlier external G0 learned model merely ranked fixed grammar productions: A=B=C0 on exact same problems (3/8), 65× more CPU. To avoid repeating a redundant neural ranker, we now first implement a *non-neural* GENERAL source-only typed substring/regex program-synthesis baseline that builds fresh executable functions from IO. No exact solutions or per-task labels are stored; not claimed to be model-discovered novel base semantics.

## Preregistration, IMMUTABLE source and first predictions
- Exactly 8 previously unopened ORIGINAL Microsoft PROSE task identifiers were frozen under branch commit **eca644fcb46a30d530a7e256e453474c3345bf99** BEFORE their spec examples were read.
- `EmergencyCall.000004,Log.000020,UserAgent.000003,Name.000010,Email.000006,City.000006,Address.000005,Phone.000002`.
- Original source = first two example input-output pairs; new evaluation = next up to 3 ORIGINAL examples. Public training-style corpus, previously known category families; not an official sealed split nor fresh semantic domain.
- Source-only `synthesis.py` SHA256 **092165e7b93d0f8229da47f7f8abed54547b4ecc3e34c3f1df3fc631e122ff47**. A source-built *dynamic program* of parameterized `regex tokens, split, casing, integer cast, multi-input extract, inferred shared literals, concatenation`. Fixed 7 nodes, 1800 maximal state expansions and top 12 programs.
- BEFORE original test-gold review, GitHub SHA-frozen predictions at commit **3215dec6f7ec3d045e90e7dc51465998b18a4745**, full first JSON SHA256 **61c59149633247a4850aae84ac2067e9e64d9fc6b9f4bea7988bddec3fe420e4**. Original PROSE file SHA1 was checked independently for ALL 8 during later grading. No outcome-driven swap.
- FIRST score: **2/8 exact full-task** (Log.000020, Address.000005); **4/8 wrong** (EmergencyCall, UserAgent, Email, Phone) despite source fit; **2/8 HOLD** (Name, City). No claim that source-consensus proves correctness.

## Same task equal input classical-only controls; local process-CPU ONE RUN
| Arm | Exact | Wrong | HOLD | Process CPU |
| --- | ---: | ---: | ---: | ---: |
| Original classical 12 constructor families | 0/8 | 2/8 | 6/8 | 32.581 ms |
| Earlier generic AST composition 13 productions | 0/8 | 0/8 | 8/8 | 143.615 ms |
| New dynamic substring + split AST | **2/8** | **4/8** | 2/8 | 38.095 ms |

This is a limited original-task classical capability gain, but more *false source-consensus*. NO new neural ownweight generator ran, no memory-on / memory-off learning comparison, no verified Q3/C. All whole-system resource measurements and GPT-6/electricity/RAM unknown.

## Post-gold root cause study (DEVELOPMENT ONLY)
The general `semantic_revision.py` infers executable AST `between(left,right)` from observed output span anchors and `optional_suffix(common)` from source equality. It proposes **60** semantically different source-consistent candidates on UserAgent.000003 and **two** for Email.000006 (identity versus conditional common suffix). These disagree on newly-shaped test inputs, so `PROBE_REQUIRES_TRUSTED_ORACLE` emits a probe and NEVER invents its answer. These functions were added **after opening gold**, so even a correct proposal would be retrospective and is NOT first-shot success. It is a bounded causal explanation of the failed assumption `SOURCE_CONSENSUS -> generalization`. Phone.000002 source has no extension examples; any semantics for a test extension needs stronger inductive knowledge or a trusted new observation.

## Reproduction, scope, and research decision
Complete original executable ZIP attached in current conversation:
`NEUMANN1_SEMANTIC_COMPOSITION_CAUSAL_BASELINE_20261026.zip`
SHA256 **403de7d9246a2c7b84ea586a17d1610c120fef693c045297747c59ca0ae9349a**; ZIP CRC PASS 14 members; clean unpack SHA256 manifest **12/12**, tests **8/8**, same-task three classical control scores reproduced. Fresh-run timings vary and are never hash-pinned.
**DO NOT deploy learned rankers when the classical engine already covers those behaviors**. Meta-learning needs a new executable **semantic rewrite action** learned from causal examples and held in model parameters only, not merely a human-fed source-matcher template. Only approve it if trained A beats sham B and strong classical C on **new independently authored tasks** with exact answer/macro memory cleared and real learning, search, verifier, retry and storage costs. The next one-step capability frontier is creation of genuinely new semantic constructions and calibrated discrimination without test-data peeking. This study supplies a more honest robust classical control, not the desired globally learned discovery engine.
