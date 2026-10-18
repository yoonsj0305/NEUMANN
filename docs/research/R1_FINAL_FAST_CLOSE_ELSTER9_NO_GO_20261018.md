# NEUMANN 1 | R1 FAST-CLOSE Research Decision · 2026-10-18

**Campaign R1 candidate decision: CLOSE / NO-GO. Global Q1–Q7 remain OPEN.**

## Source-frozen independent original corpus and honest result
The issue [#224 preregistration](https://github.com/yoonsj0305/NEUMANN/issues/224) pinned **all nine** `SMT-LIB/benchmark-submission-2025/non-incremental/QF_NIA/20250331-elster` original files **BEFORE opening the raw source bodies or source labels**. Upstream commit `37c6cd5d98edb46057f30cef35ba7c7250fe0161`; each file's upstream Git blob SHA1 checked unchanged. This is a separate source-family from all opened 2023 Hoenicke and Ultimate Automizer originals. Pinned algebraic proof code and Z3 4.15.4, native cvc5, CPU timeouts as preregistered, same GitHub-hosted Ubuntu machine. All original source labels were read only AFTER all arms completed.

**First-run SUCCESS** was the **workflow execution** of the complete audit, NOT a scientific G0 PASS: [GitHub Actions #39120351485](https://github.com/yoonsj0305/NEUMANN/actions/runs/39120351485) / immutable [artifact #12133279011](https://github.com/yoonsj0305/NEUMANN/actions/runs/39120351485/artifacts/12133279011), ZIP SHA256 `a6edb75a8c7a7713eeb293d4811e747ea318c425d575be9b81c1dcac32cfedc2`. Downloaded full JSON independently recalculated and matched all 9 original file hashes.

**CRITICAL finding:** ALL NINE `:status sat`. The old source-only algebraic lemma generator can ONLY independently prove UNSAT and, exactly as predicted by its soundness, provided **0/9** UNSAT certificates on these satisfiable original formulas. This observation **does not falsify prospective UNSAT-domain lemma discovery** because this SAT-only corpus was not a fair test of that conditional capability. It **does** mean the preregistered frozen architecture generated no additional capability on these nine original tasks. No gold status was fed to any proposer or solver.

The first auto-generated receipt's `*_unsat_claims=0` reports are UNSAT-specific only; do NOT misquote as 'none of the classical solvers solved any new source tasks'. Original per-task raw answers instead reveal:

| Original file | Z3 alone | native cvc5 | frozen source math certifier | hybrid Z3 fallback |
|---|---|---|---|---|
| `A_1` | SAT | SAT | no UNSAT certificate | SAT |
| `B_1` | SAT | external wall timeout | no UNSAT certificate | SAT |
| `B_2` | UNKNOWN | external wall timeout | none | UNKNOWN |
| `C_1` | UNKNOWN | external wall timeout | none | UNKNOWN |
| `C_2` | external wall timeout | external wall timeout | none | external wall timeout |
| `D_1` | UNKNOWN | external wall timeout | none | UNKNOWN |
| `D_2` | external wall timeout | external wall timeout | none | external wall timeout |
| `E_1` | UNKNOWN | external wall timeout | none | UNKNOWN |
| `E_2` | UNKNOWN | external wall timeout | none | UNKNOWN |

**No independent SAT model verification** for the SAT return values, which are only solver claims, consistent with the source statuses. Avoid calling 2 reported SAT results two independently certified original solutions.

**Measured same-runner CPU-host transaction:** Z3-only 9 files **21.731136s**; cvc5-only 9 files **24.396968s**; structural certifier + conditional Z3 fallback **26.840112s** cases + **0.222211s** pinned solver fetch overhead = **27.062323s**. Excluding same original download **3.567130s** symmetrically, hybrid was **5.331187s / 24.532% slower** than Z3 and delivered the SAME two SAT *reported* results. No statistical multiple-seed replication; this is an exact first-run observation, not an infinite-case impossibility theorem.

## Earlier opened 2023 Hoenicke **positive result remains valid**
The already-opened 27 original `20230328-sqrtmodinv-hoenicke` developmental corpus yielded **17/27** Z3 UNSAT reports, **4/27** exact source-polynomial independently certified UNSAT, 1 intersection, **20/27** hybrid combined with three extra exact UNSAT proofs, and **29.103975s** Z3-only versus **21.290438s** hybrid including pinned-code fetch/startup in one same GitHub CPU run ([Actions #39119117181](https://github.com/yoonsj0305/NEUMANN/actions/runs/39119117181), [artifact #12133152837](https://github.com/yoonsj0305/NEUMANN/actions/runs/39119117181/artifacts/12133152837), SHA256 `65d9b8a3be5952856f40afb1c371e1ce57dfe60e1c72217fbcec065154942390`). The bounded 26.847% wall reduction was real against Z3 4.15.4 in an *opened*, single-family, classical hand-coded structural portfolio. It is **not** new learned semantic invention or a frontier-scale 10× win.

## FAST-CLOSE final adjudication

1. **R1 current registered source/algorithm funding decision CLOSE / NO-GO.** The only new independent source-family study generated no extra correct original work and did not reduce total CPU time. That family turned out all SAT, so it is **not an adequate falsifying test** of transfer among previously unseen UNSAT originals. No posthoc benchmark replacement allowed.
2. **G0 FULL = NOT ADMITTED.** Original/proof mechanism valid in narrow opened development cases, but no independent UNSAT-family prospective method advantage over the strongest classical specialist at matched total cost. An optimized 2026 nonlinear solver portfolio was not included.
3. **G1 = HOLD_LEARNING, G2 = BLOCKED.** No learning experiments/GPU/paid frontier calls in this campaign, no authenticated frontier-pass/small-fail same-task result.
4. **Global Q1–Q7 remain OPEN**, not CLOSE/PASS or CLOSE/FAIL. A stopped campaign and a mathematically closed universal research hypothesis are different. Q1/Q2 have bounded original structure/verifier results; Q3 autonomous neural discovery UNPROVEN; Q4/Q5 end-to-end greater-than-baseline success only opened 2023 and no cross-origin generalization; Q6 learned source-family transfer UNPROVEN; Q7 authenticated frontier-parity BLOCKED.

**STOP this R1 campaign here**, retain the raw first receipts and original hashes. A genuinely new independently-originated, preregistered UNSAT-family corpus and a benchmark-matched specialist would be a **separate future project**, not a continuation until a favorable result. Preserving a correct bounded positive is more valuable than falsely 'closing' Q1–Q7.

### Key evidence
- [GitHub Issue #224 pre-registration and correction](https://github.com/yoonsj0305/NEUMANN/issues/224)
- [2025 source-isolated first run](https://github.com/yoonsj0305/NEUMANN/actions/runs/39120351485)
- [2023 opened-dev positive hybrid first run](https://github.com/yoonsj0305/NEUMANN/actions/runs/39119117181)
- [Notion authoritative FAST-CLOSE contract](https://app.notion.com/p/3fd7830ff3348158a431cddafdd760c9)
