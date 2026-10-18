# NEUMANN 1 | R2 exact source-proof necessary-condition gate · FIRST 36-source engineering result · 2026-10-18

**Verdict:** `R2_PROOF_STAGE_NOOP_GATE_OPENED_DEV=PASS`. This is **an implementation-level cost improvement on existing public, opened source fixtures**, not new G0 prospective headroom, not proof of any learned/neural structure, not 10×, not Q1–Q7 global CLOSE.

## The universal, narrowly scoped correctness invariant

The frozen original classical source-proof engine is [original integer polynomial prover](https://github.com/yoonsj0305/NEUMANN/blob/c051985ceb216c5e2e3685e28c5f5a0e064850e2/research/evidence/g0-newton-hoenicke27/one_shot_integer_polynomial_proof.py) with original Git blob SHA1 `ff493a21b626733e2797487974388fa6e93b56ec`. Its only accepting path requires BOTH:
1. A necessary original atomic constraint `(not (= (mod E M) 1))` (either equality operand order), identified in a top-level AND source context; and
2. A necessary guard `(> s 1)`, with positive modulus `M=s` or `M=s*s`, and an exact integer-polynomial proof plus original-source Z3 contradiction.

Consequently, every accepted certificate requires standalone original SMT tokens `not`, `mod`, `1`, `>`. If any of those tokens is absent in the **unmodified** original SMT-LIB text, this **specific frozen prover** cannot enter an accepting path. Rejecting the expensive proof engine at that point and directly falling back to the unchanged original Z3 solver **does not remove a certificate accepted by this frozen engine**. The requirement is a NECESSARY condition, not sufficient. Comments/source headers may cause false positives (extra attempted proofs), but cannot make absence-of-token skip unsound. This is a deterministic soundness claim about the pinned program's certificate acceptance language, NOT general semantic completeness of SMT reasoning or a model-learned router.

For a sequential proof-only-P then fallback-S architecture, an input not certifiable by P forces both `P` and `S`; in an additive work accounting model the extra computational work is `Cost(P)>=0`. For source classes in which proof is impossible, any nonzero P pre-work cannot improve asymptotic total work absent caching/side effects. Thus a cheap sound negative prefilter is a FIRST PRINCIPLES necessity if proof acceptance is sparse.

## One pre-registered exact original experiment, no newly examined holdout

[Issue #225 preregistration](https://github.com/yoonsj0305/NEUMANN/issues/225) fixed **ALL 36 previously opened original source files**, EXACT 27 from 2023 Hoenicke at Git SHA `7f993a017850ba547c6ea19a1bf3b54adf54a449`, EXACT 9 from 2025 Elster at Git SHA `37c6cd5d98edb46057f30cef35ba7c7250fe0161`. Those exact 36 original bytes were downloaded without source labels as gating inputs, individually SHA-256 logged; Elster raw files also verified against pre-registered upstream Git blob identities.

The proof source was downloaded from the exact old Git SHA and passed Git-blob SHA1 identity verification before execution, **with no math proof algorithm changes**. Both arms used independent Python cold processes on ONE GitHub-hosted Ubuntu CPU runner, each up to 4s: A=old unconditionally loaded frozen source math proof, B=4-token cheap scan then old frozen proof only if the necessary token set is complete; otherwise bypass. Per-file A/B order deterministically alternated by registered case index parity. Both arms retained exact original math proof+independent original checker path. The fallback Z3 was logically unchanged, **but this R2 experiment measured the proof-stage only, NOT an actual replay of whole hybrid full cost on both arms**.

## Immutable first successful result

- [GitHub Actions SUCCESS #39121794372](https://github.com/yoonsj0305/NEUMANN/actions/runs/39121794372), [first entire 36-file artifact #12134048011](https://github.com/yoonsj0305/NEUMANN/actions/runs/39121794372/artifacts/12134048011).
- Artifact ZIP SHA256 **`5996e5217d6b03de07b2ced48e959b9285ed3038ee3ae8513775fc4eb0364c1f`**, downloaded and independently opened on local container. Parsed JSON first result `FIRST_36_SOURCE_SOUND_NOOP_GATE_AUDIT_COMPLETE`, 36 unique source SHA256, 36 A/B records, no parse, subprocess or timeout errors.
- Exact original mathematical UNSAT certificates **4/36 preserved, byte-identical old source proof** in `modInvStep`, `modInvStepSimplified`, `modInvVar1`, `modSimpleTest`; all OTHER 32 originals yield no certificate under either arm.
- Unconditional frozen-proof stage **11.191340 sec** across 36 cold original subprocess runs.
- Necessary-token gated frozen-proof stage **6.081670 sec** across same 36 cold subprocess runs.
- **Savings 5.109670 sec = 45.657356%** measured proof-stage wall (one same-CPU experiment; no statistical confidence interval), 23 original cases skipped without importing heavy math prover; no accepted original source proof lost.

**Critical per-family audit to prevent overselling:**

| Already opened source family | Cases | Frozen source certificates | Old proof-stage wall | Gated proof-stage wall | Original tasks skipped |
|---|---:|---:|---:|---:|---:|
| Hoenicke 2023 | 27 | 4 unchanged | 6.680260s | 1.468138s | 23 |
| Elster 2025 | 9 | 0 unchanged | 4.511080s | **4.613532s (slower)** | **0** |
| Total | 36 | **4 unchanged** | **11.191340s** | **6.081670s** | **23** |

**The critical failing-domain limitation:** ALL NINE Elster examples were previously reported SAT. Every one happened to include the necessary generic lexical tokens although NONE had the actual structure needed for the exact UNSAT certificate; therefore this initial four-token scanner did **not** solve the SAT domain's route-to-fallback overhead. It also gave no new SAT capability. Claiming it eliminated R1 cross-origin negative would be false. R2 provides a valid cost filter on 2023 Hoenicke only and a general conditional soundness property of the old prover acceptance language.

## FAST-CLOSE boundaries

- `R2_PROOF_STAGE_NOOP_GATE_OPENED_DEV=PASS` **engineering** cost gate and original-certificate preservation under first execution.
- `R1_ELSTER_UNSEEN_FAMILY=NO_GO` **immutable**, not rerun or re-labeled as PASS. 2025 SAT-only vs UNSAT-only prover remains inapplicable for testing UNSAT-oriented transfer.
- `G0_FULL_FRESH_CROSS_FAMILY_BEST_SPECIALIST=OPEN`; `G1_LEARNED_SEMANTIC_PROPOSAL=HOLD`; `G2_FRONTIER=BLOCKED`; **GLOBAL Q1–Q7 OPEN**.
- 36 opened originals are engineering regression fixtures, not a statistically independent sample for source generalization. The accepted 4 are unchanged classical hand-coded proofs, not model-generated novel relations. No 10× speedup, no energy/VRAM or API price proof; the best specialist portfolio and full hybrid runtime were not tested in this R2 check.
- **STOP this R2 hypothesis here.** Follow-up could in principle use an exact *required original AST shape* preflight to eliminate more irrelevant SAT source work, but that would be a separately preregistered design and new prospective evidence; do not posthoc tune this one-shot scanner to 2025 Elster's known results.

[Exact run script](https://github.com/yoonsj0305/NEUMANN/blob/research/r2-cheap-proof-noop-gate-36-20261018/research/evidence/r2-proof-noop-gate/first_36_originals_sound_gate.py).
