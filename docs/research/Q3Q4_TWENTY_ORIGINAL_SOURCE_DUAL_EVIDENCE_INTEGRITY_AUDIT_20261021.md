# NEUMANN 1 | Q3/Q4 original safety proof integrity audit · 2026-10-21

## Snapshot verdict

**20 unique genuine published original-source programs certified: 19 SAFE and 1 UNSAFE.** There are no unresolved statuses among this **specifically selected** twenty-source cohort. Each SAFE requires source-native actual Pre/Trans/Post inductive proof independently Z3+cvc5; the one UNSAFE requires a concrete reachable original one-step model with native Pre, Trans and negated Post SAT independently in Z3+cvc5. The two outcomes must never be counted as identical "safe passes."

Exact pinned public original revision: `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646`.

| Original cohort | Distinct source count | Genuine dual-proof disposition | Immutable official GitHub Actions |
|---|---:|---|---|
| `andrew_lustre` original DRAGON_3, FIREFLY_2, FIREFLY_3 | 3 | SAFE, 2-induction native dual | [#39521290383](https://github.com/yoonsj0305/NEUMANN/actions/runs/39521290383) |
| `andrew_lustre` DRAGON_4 | 1 | SAFE, SPACER-extracted actual source invariant dual 3VC | [#39522789343](https://github.com/yoonsj0305/NEUMANN/actions/runs/39522789343) |
| `from_2018` fib_01/fib_04 and `xujie_code2inv` 10.c/12.c | 4 | SAFE, native dual 3VC | [#39523392793](https://github.com/yoonsj0305/NEUMANN/actions/runs/39523392793) |
| First post-frozen six, excluding fib_07 | 5 | SAFE, cheap-first source SyGuS or SPACER + dual | [#39524963975](https://github.com/yoonsj0305/NEUMANN/actions/runs/39524963975) |
| First frozen `fib_07.sl` | 1 | **UNSAFE**, concrete one-step original Pre/Trans/!Post witness, source dual SAT | [#39525472148](https://github.com/yoonsj0305/NEUMANN/actions/runs/39525472148) |
| Second genuinely source-unopened six | 6 | SAFE, genuine source native dual 3VC after generic 0–3 bounded unsafe preflight | [#39526034947](https://github.com/yoonsj0305/NEUMANN/actions/runs/39526034947) |

**Unique original names:** 8 `andrew_lustre`, 6 `from_2018`, 6 `xujie_code2inv`. The three directories do not imply three independent authors. Original-source blobs and initial pre-source-freeze identities are archived in the respective PRs. Follow-up after source opening is clearly distinguished from true first-source results.

## Byte-verified official artifact SHA-256

The six official GitHub Actions ZIP digest values, retained unchanged:

| Official run ID | Artifact ZIP SHA-256 |
|---|---|
| 39521290383 | `15e1aa4dec470d496b865c4979b02e354bb05e8153f605a6928e5ff2a3654e96` |
| 39522789343 | `622576a4a24feb6da8e3871e2a7a74830aac475b4873d662391e9dbd72d281b7` |
| 39523392793 | `25decdc78cd5c2b36ea0c8beb9c1182ef3456e3dcea1b32692cca3f6385e9376` |
| 39524963975 | `c07207c5185aa37903b21acd5c6268bc73246e50a2ca9abc772f0374a8fedcd2` |
| 39525472148 | `3537d724364cc0e6204fcc1011caf80e4d609bb42b196321a79aa66043249a30` |
| 39526034947 | `55aa900f72d7cb9ba414e56d2fc5d3f1b0f189ddf3e39254ad2d96aa3feba14b` |

**Receipt auditor executed**: `AUDIT_ORIGINAL_SOURCE_20_SAFE_19_UNSAFE_1_PASS`, `AUDIT_RECEIPTS_SHA256 6`. The Python-stdlib-only integrity auditor checks ZIP SHA-256, JSON SHA-256, original typed/native semantic parity in Z3 and cvc5, independently original SAT/UNSAT dual verdicts, 20 distinct programs, and cross-run source reconciliation. A deliberately byte-corrupted archive was rejected (fail-closed corruption negative-control).

Reproducible evidence package: `NEUMANN_1_20_VERIFIED_SOURCE_EVIDENCE_BUNDLE.zip` with six downloaded unchanged archives, SHA-pinned result JSON, auditor script, and explanatory README. Package archive SHA256 `0a7a4cdceb42e09e2226a3d378655b9f5b0144fd0c8b8d95393cb7613a980486`. This local bundle is supplied in the user conversation, **not merged into GitHub**. The GitHub original Actions links above remain the primary provenance.

## Scope and Q3/Q4 decisions

- **SCOPED PASS**: twenty named original published program safety dispositions; all are formally and independently source-native Z3/cvc5 certified.
- **SCOPED PASS**: earlier separate six-source Boolean affine complete generating-basis results, *not* a twenty-source blanket claim.
- **SCOPED PASS**: prospective six-source first cheap-first dual coverage 5/6 SAFE and subsequently proved fib_07 UNSAFE; second prospective six-source SAFE 6/6. Exact classical portfolio may solve more cases than one fixed solver, but this is not a learned model invention.
- **Q4 separate result**: first matched eight-source standalone original SyGuS dual 5/8 versus Z3 SPACER+dual 8/8, but common solved set favored original fast SyGuS latency; 3.275 times aggregated PDR/cheap-first observed wall on another first six-source cohort contains censored PDR timeout and differing coverage. **No guaranteed per-task 3.275× speedup, no full Q4 10×.**
- **NOT DEMONSTRATED**: neural learned genuinely new mathematical operator, exclusive benefit over strongest exact classical baseline, independent author-origin unobserved first-pass learned generalization, frontier-equivalent problem solving, Q4 full matched end-to-end 10× compute benefit.
- **Global Q3 = OPEN; global Q4 = OPEN; global Q1–Q7 have no new promotions from this classical-source integrity audit.**
- This is an integrity audit of prior CI proof receipts, **not a fresh independent SMT solver rerun**. Authentic original code, real proof runner versions, and raw CI results are available through linked PRs.

## Cheapest safe next experiment

Stop generating extra same-family classical proofs solely to increase the count. The next falsifiable learning-specific Q3 trial must freeze a **new operator grammar, trained checkpoint, truly unopened author-origin-distinct source identities, exact classical specialist/CEGIS control, and original dual 3VC** before opening programs. Parallel Q4 evaluation should match a *best available conditional classical portfolio*, not a deliberately weak standalone SyGuS timeout, with actual energy/token/wall accounting and an explicit Degraded Mode.
