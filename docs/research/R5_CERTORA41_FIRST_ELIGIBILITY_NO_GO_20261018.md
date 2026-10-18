# NEUMANN 1 | R5 FIRST source-family original eligibility audit · 2026-10-18

## Precise verdict: R5 candidate eligibility CLOSE / NO-GO; no scientific transfer test occurred

**No original UNSAT transfer or best-classical comparison was executed.** The preregistered first evaluation aimed to use **eight known-unsatisfiable, previously unread** original tasks from 2024 Certora's more expressive SMT-LIB QF_UFNIA family. The exact source corpus has **41 original tasks, all 41 with source status `unknown` and zero with `unsat`**. Therefore zero originals met the prespecified task eligibility criterion and the runner correctly **STOPPED BEFORE executing the structural certifier, Z3 or cvc5 on any chosen task**.

The verdict is `R5_CANDIDATE_ELIGIBILITY=FAIL/CLOSE`, `R5_NEW_SOURCE_LEARNED_PROOF_EFFICACY=NOT_TESTED`. This is NOT evidence that all 41 source formulas are SAT, or that current specialist solvers cannot solve them, or that the frozen structural proof engine fails on eligible unseen UNSAT originals. **A source `:status unknown` header is metadata, not a difficulty label and not a mathematical claim of UNSAT.**

## Pre-registered scientific target

[GitHub Issue #228](https://github.com/yoonsj0305/NEUMANN/issues/228) created **before any of the 41 source bodies or answer headers were inspected**. The exact source family was `SMT-LIB/benchmark-submission-2024` original Git SHA `02e00a1ad661405c438059820d82a5cf5ef11569`, path `non-incremental/QF_UFNIA/20240410-certora/nia-splits/` consisting of exactly **41 original `NNNN.smt2` files**. Prespecified rule: verify all 41 against upstream Git blob SHA1, read original `:status` header only to select **first 8 UNSAT originals in lexicographic file order**, never select on solver outcome, parsed source body, file size or human judgement. If <8 eligible originals, STOP. Mathematical prover was frozen to R3 AST negative prefilter source commit `01acd8153f3268754a7a01e93509259bb97696bc`, Git blob SHA1 `7e378010ac671e34bf7784b83a4a7cf37354769a`, unchanged exact integer-polynomial source prover commit `c051985ceb216c5e2e3685e28c5f5a0e064850e2`, Git blob SHA1 `ff493a21b626733e2797487974388fa6e93b56ec`. Z3 4.15.4 and cvc5 would have been CPU controls **only if** eight known UNSAT were available. They were not.

### Preserved actual first operational failure and next scientific run
- [First Actions execution #39127334838](https://github.com/yoonsj0305/NEUMANN/actions/runs/39127334838) failed at `python -m py_compile` because a **two-line `if` without parentheses** caused `SyntaxError`. **Zero task sources or original results were opened**. This is not a scientific FAIL and no JSON artifact was produced, documented in Issue #228 comment [#6249920571](https://github.com/yoonsj0305/NEUMANN/issues/228#issuecomment-6249920571).
- ONE technical-only fix, commit `99853948358c795f151cc22f42d8ee2b83e4d008`, wrapped **only the existing Boolean prereg decision predicate** in parentheses; froze all 41 original source selection, theorem logic, solver timeouts and target metrics unchanged.
- [Actual first content audit Actions SUCCESS #39127479536](https://github.com/yoonsj0305/NEUMANN/actions/runs/39127479536), immutable [artifact #12136473756](https://github.com/yoonsj0305/NEUMANN/actions/runs/39127479536/artifacts/12136473756), ZIP SHA256 **`9801ded10d769a129eb6bdc4fc7094964f03617d9aa2baad9c9cab1f097f7bd2`**, independently downloaded, ZIP opened and re-read by separate Python audit.
- JSON member `r5_certora2024_frozen_unsat8_first.json`: status `R5_ELIGIBILITY_FAIL_INSUFFICIENT_SOURCE_UNSAT_STOP`, exact **41** directory manifest entries, **41 unique original source SHA-256**, upstream blob validation PASS for all 41, source `QF_UFNIA` parsing of header PASS for all, source answer counts **`unknown:41`**, **`unsat:0`**, `frozen_eligible_unsat_count=0`, no `tasks` solver run. Source download wall `12.056764s`; this is an input integrity/eligibility audit **NOT solving**.
- Both byte-identical historical engines were downloaded and identity checked as part of the setup; **no structure proof execution, no original Z3 or native cvc5 task arm**, no neural training, GPU, paid API or PR.

## FAST-CLOSE and scientific value

This checks a critical prerequisite *before* spending any inference budget. The previous independent-source candidate `20250331-elster` from 2025 happened to contain **only SAT original tasks**, making it unsuitable for probing an UNSAT-only theorem prover. The newly selected independent source family had **only UNKNOWN expected statuses**, again unsuitable under a strict known-UNSAT contract. Both **eligibility defects were discovered and registered, not reinterpreted as structural algorithm failure.** No additional source families will be searched or substituted **inside this R5 campaign**; NO-GO/STOP here, not posthoc cherry-pick.

Preserve earlier genuine source-mathematical certificates (Ultimate original 3 and Hoenicke 4) and bounded R4 same-runner 36 opened originals hybrid pilot **22/36 vs Z3 19/36 at 49.934s vs 51.567s** (one-run, no blind transfer, no best-specialist). They are **not upgraded** by this R5 input audit.

`R5_ELIGIBILITY=CLOSE/FAIL`, `R5_G0_NEW_SOURCE_CORRECTNESS=NOT_RUN`, `G0_FULL_PROSPECTIVE_STRONGEST_CLASSICAL=OPEN`, `G1=HOLD_LEARNING`, `G2=BLOCKED`, **ALL GLOBAL Q1–Q7 OPEN**.

**Forward resource-allocation decision:** The next scientifically useful new benchmark cannot begin with arbitrary submitted paths and hope labels are adequate. First build a provenance-validated dataset with **verified original UNSAT status and available real original source** before preregistration, then compare the strongest native classical solver on it. This would require a NEW independent preregistration and research funding decision, not keep replaying the present branch. Otherwise STOP rather than loop source-selection failures.

Evidence code: `research/evidence/r5-certora2024-unsat/first_eight_unseen_unsat_by_metadata.py`.
