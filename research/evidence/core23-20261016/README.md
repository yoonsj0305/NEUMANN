# NEUMANN CORE-23 | Exact external CHC original certified with typed classical goal-backchaining

**2026-10-16 · DEVELOPMENT-ONLY. Q1–Q7 remain OPEN. No learned original-family transfer or compute advantage is claimed.**

## Exact original and pinned evidence
- Source: [CHC-COMP 2026 goal43_000.smt2](https://github.com/chc-comp/chc-comp26-benchmarks/blob/b4fa7a708e5863bbcdb5de50d692ead3a67cbedc/ADTRem/isaplanner/goal43_000.smt2)
- Git commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, original Git blob `125e17e95967b4af13f5a1de9031f0d1d533e330`, **4,286 bytes**.
- Original SHA-256 `07202db07e74154416379c8e0e548fd1a46f4c4553b1c56d07c76da306865449`. Exact byte identity was verified before proof.
- Original Z3 4.13.3 `libz3` alone: **UNKNOWN(timeout)** at both 2-second and 8-second budgets. This is ONE baseline configuration, not proof of difficulty for all specialized CHC tools.

## Source-derived structural candidate and independently certified meaning
A **CLASSICAL** typed goal-backchaining algorithm inspected original Horn predicate *type signatures and variable joins*, identifying that two unary list relations from the same input are joined by a ternary list relation and tested against their original input. It proposed exactly ONE candidate:
`forall L:listOfInt. append(takewhile(L),dropwhile(L)) = L`.

The semantics of the three operators and induction obligations were **human-implemented**, not learned by a neural model. Z3 independently checked the **3/3** cases (nil, head predicate true with tail IH, head predicate false) as UNSAT; only after these certificates was the lemma instantiated at the final original safety clause. Under explicit mathematical interpretations of ALL source relations, each of the **18/18 actual original Horn clauses** was independently checked as UNSAT in its negated form.

Three wrong lemma controls and four individually poisoned original Horn clauses each returned **SAT**, rejecting invalid candidates. A relation alpha-renaming test preserved the typed candidate. Test suite **8/8 PASS** and **8/8 replay PASS** from independent ZIP extraction with the pinned original separately supplied.

## Learned comparison and honest verdict
The frozen CORE-22 neural path returns `ABSTAIN_EXTRA_CLAUSE_OR_PROTOCOL` on this `HORN` source, since its decoder supports only a synthetic `ALL` / `define-fun-rec` affine-list grammar. It did **not** invent or propose this theorem and was not tuned to it. The classical typed backchaining generator and proof are a new functional proof route, not a demonstration of a learned structural intelligence breakthrough.

The target had previously been nominated during CORE-22, so this run is NOT a strictly unseen blind evaluation. The raw Z3 timeout and manually constructed helper-admitted verifier are also NOT strongest-capability-matched classical comparisons. **Q3, Q4, Q6 and Q7 remain OPEN**; all other frozen Q-gates unchanged.

## Archive identity
`NEUMANN_CORE23_EXTERNAL_CLASSICAL_CERT_20261016.zip` SHA-256 `83d31e146beb92181d59e35e7d92f5f0e98da7023c7f433848527c26dd4f76d1`, **13,363 bytes**; fresh-unzip test 8/8 PASS. It contains source code, isolated Z3 bridge, independently replayable receipts, tests, source fetcher and manifest. Upstream source bytes are excluded (license unverified) and fetched with pinned Git identity check.

**The original ZIP binary is NOT mirrored into GitHub yet**; this public branch contains this written evidence, not the executable ZIP.

## Decisive next gate
Freeze a learned model consuming source-complete Horn syntax and outputting a complete NEW typed auxiliary *definition*, with no task-specific human semantics. Pre-register a fresh cross-family original before examination, require independent inductive certificates and matched strongest classical synthesis, and measure end-to-end cost. No promotion of historic verdicts.