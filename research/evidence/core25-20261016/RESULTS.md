# NEUMANN CORE-25 | Frozen typed shape-relation proposal and honest cross-family transfer verdict

**2026-10-16 · DEVELOPMENT-ONLY · NO Q1–Q7 admission.** See PREREGISTERED_GATE.md (committed **before original heldout source inspection**) and FROZEN_BEFORE_HELDOUT.md (committed before inspection, with source/checkpoint hashes). Frozen script SHA256 `b2449d4189f69c6bbfed33e8c4757cf73fb90e8394c1b32cd061bbf8aca16f7b`; neural weight SHA256 `75b287c41ecdb9c7a4fd25c3f349f02c3290ea6761aed145eb3a5859c21f4e81`. Model/grammar unmodified during prospective check.

## Research question and explicit non-novelty boundary
The new source-dependent output kind is a typed relational *nil-shape* invariant, distinct from CORE24's function-composition equation. The **researcher supplied the entire nil-implication grammar** `R(x0,x1,x2) => (xi=Nil(Ti) => xj=Nil(Tj))`; a 6,977-param CPU MLP proposes typed slot indices `i,j`. The neural network does **NOT** invent this candidate type. It observes **42 hand-crafted lossy features extracted from all source clauses**, not the full dependency-complete AST. It was trained on 5,600 synthetic candidate rows from 1/2-sort Horn programs in 1.439 sec CPU.

## Real, already-studied external development original (not blind)
`chc-comp/chc-comp26-benchmarks/ADTRem/isaplanner/goal46_000.smt2` at commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc` exact Git blob `9a0a1392f0cfb994a8d1501017c6ed6eb2f758ca`, 1701 bytes, SHA256 `2406793ceb3dd10f252639dfc8ecc6fa4a0fc8e43b235cc3e2aa44d4af4a7020`.
- Frozen neural TOP1: `zip(x0,x1,x2) => (x1=nil_listInt => x2=nil_listPair)`; structurally valid in clauses 1-3 but **insufficient for original Horn goal**: clause 4 SAT counterexample.
- Frozen neural TOP2: `zip(x0,x1,x2) => (x0=nil_listInt => x2=nil_listPair)`, which independently satisfies **5/5 negated original Horn assertions UNSAT**. A poisoned extra base rule violates it (`SAT` on extra clause); harmless relation alpha-rename leaves neural ranking invariant.
- Exactly matched classical exhaustive typed nil-implication enumeration also finds the sufficient helper among 6 total possibilities; no learning or training required.

## Prespecified 4 real external unseen originals, frozen support check
GitHub connector fetched exact pinned original declarations only to test immutable parser coverage. **No neural call / all-original proof was executed for any of them**:
| Source | Registered blob | Verdict |
|---|---|---|
| `goal47_000.smt2` | `e2e8696480c7a6d3619a780453088999a5d187eb` | unsupported tree height, mirror, numeric codomain |
| `goal48_000.smt2` | `f2c9f3160f90d3231f7ed71e8c5ea4815755d1eb` | unsupported multiple relations and scalar codomain |
| `goal50_000.smt2` | `bec4891e62d9a01c2a179e5d09d3552e2a53fbbf` | unsupported mixed ADT and Int, length/take |
| `goal52_000.smt2` | `f27b6a56e752498b2a67cb59bd739aebbb7dd179` | unsupported count, append, reverse predicates |

**Cross-family external original transfer: 0/4 source-signature supported**. This is NOT 0/4 neural inference correctness or original solver failure. No target-aware change was made.

## Synthetic new-type-count heldout and strongest exact classical control
- After training on 1/2 typed list sorts, run **512 freshly seeded THREE-sort synthetic full Horn original programs**. Only **92** had a source-goal-sufficient lemma within the supplied nil-implication grammar.
- Frozen neural ranks the **goal-sufficient** pair TOP1 in **49/92** cases, TOP3 in **90/92**, TOP6 exhaustive **92/92**. Selecting an inductively true but goal-irrelevant lemma is not a successful original proof.
- **Actual strong classical certification on ALL 512 original synthetic CHCs**: source-goal exact join produces 92/92 candidates with full independent original-Horn Z3 proofs and correctly rejects all 420 invalid targets with SAT counterexamples. **1,229 separate original-clause SMT checks, ZERO unknown/crash**, total observed CPU wall **24.137 s including subprocess overhead**.
- Neural complete cost on those 512 was **not** measured; no iso-capability cost comparison. Classical wins verified reliability and requires no neural training.

## Audit, artifact and honest disposition
Source package `NEUMANN_CORE25_TYPED_RELATION_FROZEN_20261016.zip`, **70,023 bytes**, SHA-256 `b37c9409311ddc73e3540f75d84953b84c6fae58aa2eba496d7c55677fae0ba6`; 14 payload entries, all internal SHA256 and CRC checked. Fresh independent extraction plus **original source copied separately**: `pytest` **10/10 PASS**. The third-party CHC original is excluded from ZIP; source fetch/hash instructions included. Frozen source and weights unchanged from pre-unseal registration. The GitHub PR presently stores this RESULTS text and checksum identity, not ZIP/model binary bytes.

**Verdict: NARROW_NEURAL_TYPED_NIL_RELATION_COMPONENT / THREE_SORT_SYNTHETIC_PARTIAL_TRANSFER / REAL_CROSS_FAMILY_UNSUPPORTED_0_OF_4 / EXACT_CLASSICAL_STRONGER / AUTONOMOUS_NEW_ABSTRACTION_KIND_NOT_PROVEN / Q1_Q7_OPEN.**

## One genuinely decisive next gate
Stop tuning nil-shape ranking. The next architecture must encode complete typed source dependencies and synthesize a helper's **definition language itself** (base clauses, recursive rules, and a goal-sufficient relation) without a per-problem researcher-specified nil/commutation/theorem template. Fix unseen **different-family** original inputs before weights; grant specialist classical synthesis the identical program grammar and independent certificates. Do not close global gates without real original proofs + all-in efficiency wins.