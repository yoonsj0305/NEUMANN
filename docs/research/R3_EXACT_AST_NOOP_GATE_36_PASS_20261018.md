# NEUMANN 1 · R3 sound exact-AST necessity gate · FIRST 36 source originals · 2026-10-18

## Single-scope verdict
**R3 proof-stage cost / certificate preservation: PASS (development engineering only).** A frozen old classical `ZZ[variables]` original-source certifier previously accepted 4/36 exact original UNSAT certificates. R3 uses an inexpensive token prefilter, and only if it passes checks required original **Z3 AST** shapes before invoking the **unchanged, original Git-blob-verified** expensive certifier. It preserved **4/4** mathematical source-certified UNSAT proofs, refused 32 other sources with **no loss of accepted proof**, and measured a reduction in the cold proof-stage wall on one GitHub-hosted Ubuntu CPU runner.

**Do NOT confuse this with global G0/G1 frontier or learned structural discovery PASS**. The 36 are **already OPENED** 27 2023 Hoenicke and 9 2025 Elster original-source fixtures. A new unseen origin has not been evaluated; the original R1 Elster 9/9 SAT and no hybrid accuracy gain, NO-GO, remains unchanged. Full actual Z3 fallback end-to-end workload, power, competing strong specialist and statistical runtime variance are NOT evaluated by this R3 stage-only test.

## Proof-preserving invariant (only for the unchanged old prover)

Pinned original engine source commit `c051985ceb216c5e2e3685e28c5f5a0e064850e2`, exact Git blob SHA1 `ff493a21b626733e2797487974388fa6e93b56ec` (verified in runner). Its sole path to `ORIGINAL_UNSAT_CERTIFIED` requires, from *necessary* original source AND conjuncts:
1. A Z3 AST `not(= (mod E M) 1)` or `not(= 1 (mod E M))`, with `not`, `eq`, `mod` parsed as the *actual* Z3 operators; and
2. A Z3 AST `(> s 1)` where `s` is an uninterpreted Int constant. A later exact integer-polynomial quotient theorem uses a modulus `M=s` or `M=s*s`, and an independent original-source Z3+mathematically justified lemma UNSAT check.

R3 first checks the old R2 required token superset `not,mod,1,>` in exact source text. If any absent, it is safe to bypass old engine under that original engine's recognition language. If all present, R3 reads the original source **unmodified with Z3's SMT-LIB parser**, recursively decomposes *only* top-level required AND conjuncts and checks BOTH necessary shapes, without running SymPy or seeking proof. If missing, bypasses old engine and would route to the unchanged original Z3 fallback. On any AST parse error it **fails open**, running old engine rather than silently rejecting. A keyword-only method was insufficient to reject Elster because these files contain all keywords in unrelated parts of the source; the AST distinction is essential.

This proof is about accepted-certificate-language preservation in that old program (which only accepts that precise pattern), not a general theorem about any future NEUMANN reasoner, QF_NIA satisfiability, or complete arithmetic abstractions. The test also checks all preexisting 4 original positives.

## Preregistered first immutable execution

- [GitHub Issue #226](https://github.com/yoonsj0305/NEUMANN/issues/226), hypothesis, source IDs and PASS/FAIL gate declared **before run**.
- Frozen input sources: all 27 `SMT-LIB/benchmark-submission-2023/non-incremental/QF_NIA/20230328-sqrtmodinv-hoenicke` Git `7f993a017850ba547c6ea19a1bf3b54adf54a449`, all 9 `SMT-LIB/benchmark-submission-2025/non-incremental/QF_NIA/20250331-elster` Git `37c6cd5d98edb46057f30cef35ba7c7250fe0161`. 36 unique original SHA256, Elster original Git blobs pinned; original correct/incorrect label metadata NEVER accessed by the filter. All 36 are **opened fixtures**.
- One same-runner three-arm design: **old** unconditional proof; **R2** four-token precheck; **R3** four-token then exact-Z3-AST necessary shape check then unchanged old proof. All independent cold Python subprocesses with 5s external cap; order `old,R2,R3` deterministically cyclically permuted per source-index to damp ordering bias. Zero errors, zero timeout, all return statuses and process peak RSS recorded.
- [GitHub Actions FIRST SUCCESS #39122904861](https://github.com/yoonsj0305/NEUMANN/actions/runs/39122904861), [first immutable artifact #12135191752](https://github.com/yoonsj0305/NEUMANN/actions/runs/39122904861/artifacts/12135191752), downloaded and SHA256 verified **`217af940fec8ccd6518d6f5792959f6b8e1933a4a1c7d92fc1e86a03154a8b85`**. Independent JSON auditor reopened and recalculated all per-group metrics and exact 4 names.

### Measured source-proof stage results, first run only

| Stage/Group | 27 Hoenicke old DEV originals | 9 Elster old DEV originals | All 36 |
|---|---:|---:|---:|
| unconditional frozen old proof | 5.983353 s | 4.056189 s | **10.039542 s** |
| R2 token-only required preflight | 1.345310 s | 4.062536 s | **5.407846 s** |
| R3 exact-source-Z3-AST required preflight after tokens | 1.347079 s | 2.232401 s | **3.579480 s** |
| valid independently original-certified UNSAT | 4/27 | 0/9 | **4/36, same across all** |
| R3 prefilter bypasses | 23/27 | **9/9** | **32/36** |

R3 compared with token-only R2: **1.828366s** less total 36-source stage work, **33.8095%** reduction on one CPU runner; compared with unconditional original, **6.460062s less = 64.3462%** reduction. Note on already R2-screened Hoenicke R3 was ~1.8ms SLOWER, because it had no additional cases to exclude there; all R3 speedup came from rejecting 9/9 Elster before the full heavy SymPy-based certifier. Elster group: 4.062536→2.232401s (**45.05% less stage wall**).

All original four certificates from Hoenicke retained exactly: `modInvStep.smt2`, `modInvStepSimplified.smt2`, `modInvVar1.smt2`, `modSimpleTest.smt2`. No extra counterfeit certificate. This is a **correct-by-construction negative gate for this frozen certifier with directly tested preservation on 36 originals**.

## Scientific adjudication

- `R3_DEVELOPMENT_SOURCE_PROOF_STAGE_GATE=CLOSE/PASS`, **4/4 original certificates and 33.81% stage wall reduction vs R2** under one-run conditions.
- `R2_DEVELOPMENT_TOKEN_STAGE_GATE=PASS` preserved; R3 improves it on Elster SAT by 9 avoided heavy proof attempts.
- `R1_2025_ELSTER_NEW_FAMILY_FULL_HYBRID=NO_GO` preserved; R3 does **not** solve any new 2025 SAT original and did not replay a full Z3 fallback end-to-end solve here. It only reduces useless work.
- `G0_FULL_NEW_SOURCE_STRONGEST_CLASSICAL=OPEN`, `G1_NEURAL_AUTONOMOUS_STRUCTURE_DISCOVERY=HOLD`, `G2_FRONTIER=BLOCKED`, **Q1–Q7 GLOBAL OPEN**. No 10x frontier parity, learned structure, new independent-source success, or GPU/energy efficiency evidence.
- **STOP this R3 cheap-filter cycle after the preregistered first run.** No posthoc token/AST pattern tweaking based on observed Elster. To test real deployable end-to-end gains, integrate on a separate frozen external cohort and preregister comparisons to best specialized solver; do not rebrand this stage microbenchmark as system-level gain.

Executable original regression script: [R3 source on research branch](https://github.com/yoonsj0305/NEUMANN/blob/research/r3-exact-ast-proof-gate-36-20261018/research/evidence/r3-exact-ast-gate-36/one_shot_old_vs_token_vs_exact_ast.py).
