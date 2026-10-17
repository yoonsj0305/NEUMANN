# NEUMANN 1 · Q3E authentic Lists-3 recursive invariant closure (2026-10-18)

## Verified scoped theorem

Immutable original source: `chc-comp/rust-horn` commit `e5a86a1ad252fe1df75e06814769ec1d14540032`, `lists-3-inc-some-safe.smt2`, SHA256 `caca97e89ef8cd7a089d107d7b74971a50b5135deab68d268dc7f01b0a87786d`. This source was already opened in Q3B/Q3C/Q3D and is NOT a blind Q3 transfer case.

Define a mathematical list sum recursively, a state-change delta for lists and Int, and 7 typed relation interpretations corresponding to the original relations. Independently verify all **12 unchanged universal original Horn assertions**, by checking the negation of each. A valid model witnesses the original source's safety. Falsify the source goal (`%main true`→`%main false`), and the original source with the same mathematical witness must generate **SAT**.

An initial hand-written conservation formula with `ΔList(m) + ΔHead(h) + ΔList(rest) = ΔReturned(n)` produced original **12/12 UNSAT**, changed-goal **SAT** in local native Z3 4.13.3.0. This is an actual external whole-source safety certificate.

## Genuine automated classical synthesis within a human-supplied grammar

Freeze **two structures** after examining the source: three possible list aggregation operators
`{constant_zero, head_only, recursive_sum}`, and one five-relation conservation equation with three signs `(-1,0,+1)^3`.

- First experiment: 27 possible signs with recursive fold fixed, **only (1,1,1) verifies all 12 original rules**. 26 rejected by SAT.
- Second experiment: 3 folds × 27 signs = **81 different complete candidate interpretations**. **Only (recursive_sum, 1,1,1)** verifies all 12 original rules. The other 80 fail at an original clause with SAT counterexample; UNKNOWN=0. The corrupted safety goal is SAT.
- First local native verification took about 13.097 seconds across the 81 candidate search and source checks; a fresh portable replay took about 6.203 seconds. These are uncontrolled single-run CPU figures, NOT a reproducible end-to-end efficiency comparison.
- Independent GitHub Actions Z3Py 4.13.3.0 replays: [27-sign search](https://github.com/yoonsj0305/NEUMANN/actions/runs/39045996275) PASS, artifact 12105638218; [81-operator search](https://github.com/yoonsj0305/NEUMANN/actions/runs/39046208703) PASS, artifact 12105862442. Two Z3 wrappers share underlying solver, so independent implementation plumbing but not solver diversity.
- Source code `research/evidence/q3e-recursive-sum-auto-20261018/`. The conversation ZIP `NEUMANN1_Q3E_REAL_RECURSIVE_OPERATOR_81_PROOF_20261018.zip`, 17,041 bytes, SHA256 `38c4cd68d9101bfa2dd5cbe28f3ce5fbb9851f461f84f7262fe045effffa8034`, 14 members; manifest and fresh extraction 27/81 replay PASS. The ZIP remains on the conversation surface, not committed to GitHub. Original upstream SMT2 bytes are not redistributed.

**Scientifically correct label: `Q3E_ONE_EXTERNAL_SOURCE_POSTHOC_CLASSICAL_OPERATOR_SEARCH_COMPLETE`.**

This closes a **scoped exact classical invariant-selection problem** that the previous fixed Q3D six templates could never represent. It does not prove that the learned NEUMANN model discovered recursive sum/delta, that its structure has unseen family generality, that neural inference reduced complete compute, or that it is close to a frontier model. **Q1–Q7 all OPEN.**

## Single highest-value next test, with stop-loss

Do not extend the same source/fold/sign grammar and relabel it "AI" or invest GPU compute in mimicking a 6-second classical exhaustive search. Instead use this as a **positive labeled training/development example only**, and:

1. **Learn the typed AST mathematical *operator graph* itself** from actual source+goal program structure, not its sign coefficients or a fixed template class.
2. Freeze model, candidate syntax decoder, grammar and source-group holdout before seeing any target sources.
3. Require every source relation has a well-typed model-emitted semantic interpretation and all original Horn negations UNSAT; mutation controls SAT.
4. Before claiming learned value, run strongest available specialized classical solver / source-conditioned grammar enumerator + removal-of-learning under the SAME source bytes and complete costs. Conditional finite-time gaps, not absolute classical impossibility. If equal-information classical solves more cheaply, STOP that neural design.
5. Q7 frontier parity and Q4 compute gap remain separate contracted benchmarks, NOT established here.

The test must seek a **genuine cross-family headroom case**; no new rounds on already opened RustHorn sources can count toward blind model validation.
