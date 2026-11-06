# NEUMANN 1 | Eldarica 2.2 strong native COPY baseline: immutable FIRST decision

2026-11-06. **Scientific outcome: BOUNDED_NATIVE_TIMEOUT_BOTH; Q3/Q4/Q6 OPEN.**
This is a read-only decision on one completed FIRST, not a new successful learning experiment.

## Exact provenance

- Source: already-opened CHC-COMP 2025 originals at commit ddd279cab0717db6effe69baad451a8eb04ffd86, not unopened targets.
- COPY2: quic3/data/standard_copy2_true-unreach-call_ground_000.smt2, 6,318 bytes, Git blob 30b3bab8834aa6f834cf493539180e6b92caf16f.
- COPY3: quic3/data/standard_copy3_true-unreach-call_ground_000.smt2, 8,201 bytes, Git blob f8fd0b73c3aa45ee5f49426416a378bcfc462605.
- Strong native comparison: upstream Eldarica version 2.2 release asset eldarica-bin-2.2.zip, downloaded from the publisher release URL. Observed ZIP SHA256: 5b35abf7a8b0a29a048c64e1045a27e7d61196ec9c1d3e869b0dc9caf21746b6.
- Only original source SHA/bytes checked, no source modifications. CLI: eld -ssol ORIGINAL.smt2. Timeout: 60 seconds per original.
- Actual GitHub Actions FIRST: https://github.com/yoonsj0305/NEUMANN/actions/runs/42204574420, conclusion SUCCESS for completing the protocol. Its **science outcome is not solver success**.
- FIRST machine report SHA256: ab1312722d58ab064f3dfd7ced417967545d6169b081b75f575ee9b4f25b42d8.
- Exact source bytes, raw stdout/stderr and report are preserved in artifact 13495189457 at the FIRST run. Raw ZIP upload SHA256 35ca463dd1f854177fcdc2942efdfe5c79ff6cad4b8915a0a73bdcbe10d15dfb.

## Actual first results

| Unmodified original | Eldarica 2.2 native verdict | Native wall time | Independent certificate |
| --- | --- | ---: | --- |
| COPY2 | TIMEOUT_CENSORED | 60.0576 s | NOT RUN |
| COPY3 | TIMEOUT_CENSORED | 60.0899 s | NOT RUN |

Entire two-original process (download of original sources and 2 native executions): 120.41 s wall, peak script process RSS 371,104 kB. These resource values are measured on this GitHub Actions runner, not a controlled inter-solver same-hardware economic benchmark.

## What this does and does not establish

The existing *human-authored* H1 cross-array relation in PR #674 refutes all 9 untouched COPY2 Horn clauses under independent Z3 checks, with a real wrong-store SAT mutant, in 1.51 s measured whole-script runtime (including source retrieval). This shows that a *provided* relational invariant can close the clauses where the tested Eldarica 2.2 configuration did not return within 60 s. These are **not equal-rights all-in discovery runtimes**: H1 required unmetered human semantic design; Eldarica was asked to synthesize from scratch. Therefore **no 40x/10x cost or speedup claim is admissible**.

An Eldarica timeout is not a correctness failure, mathematical inability, or evidence that all competing classical CHC solvers fail. It gives only version/configuration/time-budget-censored headroom. COPY3 has **no corresponding all-clause human-H1 original proof** in this branch, so it cannot be counted as H1 solved.

## Decision and stop rule

1. Freeze this immutable Eldarica 2.2 FIRST; workflow job has been set to if:false. No retuning timeout/options or rerunning the same open originals to manufacture a success story.
2. Do not expand the human H1 by hand to more same-family originals and call that Q3 invention.
3. For a genuine Q3 test: a program must generate a new typed executable cross-array relation *not enumerated in a teacher-provided H1 candidate set*, freeze its search policy/program and operator vocabulary prior to an independently authored unopened benchmark first, prove every original Horn clause with a separate verifier, and compare against a **same-rights classical source-derived CEGIS/inductive synthesis** method. If classical wins, select the classical route.
4. Q6 requires a different independent author and formalism with no refit, no source-head compatibility leak and independent original proof. Q4/Q5 require iso-capability total costs including all discovery/training/proof/failed candidates, setup and amortized reuse.

This is useful **negative information**: it refutes the assumption that simply invoking 2025 Eldarica 2.2 on these two opens within 60 seconds closes them. It does **not** close the original NEUMANN 1 intelligence objective.