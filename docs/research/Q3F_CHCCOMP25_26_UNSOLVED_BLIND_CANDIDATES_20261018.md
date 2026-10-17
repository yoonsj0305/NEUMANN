# NEUMANN 1 | Q3F competition-grade classical-headroom candidates, escrow BEFORE source inspection

**Date:** 2026-10-18 KST. **This is benchmark provenance and selection, not a NEUMANN model result.** Q1–Q7 OPEN; no model trained, no API/provider called, no original SMT-LIB source body inspected by researchers, and NO winner claimed.

## External evidence, immutable official revisions

CHC-COMP 2025 benchmarks: `chc-comp/chc-comp25-benchmarks@ddd279cab0717db6effe69baad451a8eb04ffd86`. Official README says **absence of expected verdict** on a selected benchmark = **no participating tool solved it in the 2025 competition**. Confirmed metadata only, without opening SMT2:

- Group `tip-adt-lia` (TIP 2015 sorting): `tip-adt-lia/tip2015_sort_StoogeSortIsSort_000.yml`. Metadata has no `expected_verdict`.
- Group `ringen-adt-benchmarks/isaplanner` (IsaPlanner): `ringen-adt-benchmarks/isaplanner/prop_63_000.yml`. Metadata has no `expected_verdict`.

CHC-COMP 2026 benchmarks: `chc-comp/chc-comp26-benchmarks@b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`. Official README explicitly says **if no tool solved a task in CHC-COMP'26 there is NO `majority_vote_verdict`**, and it populates `expected_verdict: true` as a **placeholder**. These two paths have placeholder `true` with no `majority_vote_verdict`, which MUST NOT be counted as solved.

**Interpretation:** legitimate evidence of **competition-reported unresolved status** in the 2025 and 2026 tool evaluations, across TWO source-origin groups. This is stronger than a single 10s Z3 timeout but is NOT a mathematical proof of classical impossibility, an exhaustive modern solver audit, a verified ground-truth target answer, or a solver-run receipt. Competition answer coverage depends on participants, budgets, benchmark selection, and preprocessing; original proofs could still exist.

## Strict blind source and group protocol

- Freeze the metadata-only selection above and the two immutable repository revisions **BEFORE fetching source bodies**. The first SHA escrow job may download the 2026 SMT2 files **only to hash and count bytes**. It MUST NOT print/emit source text, parse it into an invariant, inspect clause counts, benchmark expected answer, or pass it to any learning component. The raw bytes are not uploaded or redistributed.
- Source SHA256, Git blob SHA1, length and metadata provenance are recorded in an auditable immutable GitHub Actions artifact. If 2025/2026 metadata stops meeting the stated conditions, **ABSTAIN_SOURCE_OR_COMPETITION_IDENTITY**. 2025 and 2026 names must agree; fail closed on filenames/path anomalies.
- The two selected source groups are **HOLDOUT EXCLUSIONS**. Exclude both group families (not just filenames) and near-duplicate versions from training, prompt examples, retrieval, in-context lemmas and developer tuning. Both are from the same aggregated competition container and remain externally public, so **no claim of fully secret benchmark**; check semantic duplication against other datasets before any final Q3 claim.
- **No source content delivered to the NEUMANN generator until** its actual trained checkpoint identity, tokenizer, source+goal interface and typed variable-depth AST decoder are frozen with a cryptographic hash, actual training receipt on separate sources, independent complete-original verifier, matching specialist classical baseline execution budget, learned-minus arm and fail-closed costs.
- No safe/unsafe gold from metadata or filename provided to the generator. Authentic question can be posed only after the above conditions. Model must emit **new unprovided full typed semantic relation definitions**, not signs in human-provided source-specific templates, and independently prove **every original Horn clause plus original safety goal**. All comparison arms receive exactly the same source+goal bytes.
- **Q7 admission separately requires authenticated SMALL-fail and FRONTIER-pass on an exact target.** Historical provider evidence absent. No user-authorized paid compute.

## Strict stop-loss

If one of these competition-grade candidates turns out to be UNSAT and independent proof is inaccessible, or too large for small hardware, or specialist baseline solves under the matched budget, **do not massage a target**. Persist `UNVERIFIED/ABSTAIN/CLASSICAL_SOLVED`, open no further "easy" substitutes, and revise research assumptions rather than claiming Q3/Q4/Q7.

The experiment at this stage only closes **source selection and authentic classical-headroom *candidate* identification**. As of preregistration no Q3/Q4/Q7 scientific win is proven.
