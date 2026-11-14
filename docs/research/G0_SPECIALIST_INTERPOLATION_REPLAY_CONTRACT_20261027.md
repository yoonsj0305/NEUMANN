# NEUMANN 1 | G0 specialist interpolation replay contract (2026-10-27)

**Scientific state:** GLOBAL Q1–Q7 OPEN; G1 HOLD; G2 NOT RUN. **This is a pre-execution protocol, NOT a new solver result.** Preserve all RC47–RC51 and 2026-10-27 historical first-run receipts unchanged. This file documents a **new run proposal**, not an actual original-cohort preregistration or benchmark result.

## 1. The one missing fact

The last 7 eligible original SMTInterpol-source tasks produced **0/7 first verified V2 witnesses**, but SMTInterpol itself was NOT RUN. That is a bounded custom generator failure, **not** evidence that professional classical interpolation cannot solve those tasks. Following the separate Ultimate-source 5 check-sat-only / 6 missing interpolants / 1 unmaterialized partition, the correct minimum experiment is an **actual domain-specific classical baseline satisfying the entire original query**, verified independently.

**No neural weights, paid/API/GPU calls, or Dust/MeZO/EGGROLL comparison is justified by these results.** Do not train to achieve a target PASS label.

## 2. External artifact, identity and environment

Official SMTInterpol LGPL-3.0-or-later distribution:
- Primary documented official binary: https://ultimate.informatik.uni-freiburg.de/smtinterpol/smtinterpol-2.5-1453-gedae1f37.jar
- Official published SHA256: `8d42e87614fcdbe6fce5233b91f20563dfd9a854d999127d70cfb42853e091c7`
- Usage and syntax: https://ultimate.informatik.uni-freiburg.de/smtinterpol/docu.html
- SMTInterpol 2026 competition artifact for additional version check, not a replacement without prereg: https://zenodo.org/records/20580131

Pin actual Java version, JAR sha256, container/host identity and evaluator's two solver versions BEFORE looking at results. Run every source file in an isolated process. The official documented invocation is `java -jar smtinterpol.jar original.smt2`; a standalone JAR can also read standard input. Many interpolation scripts require `(set-option :produce-proofs true)` before assertions. **Do not silently patch original scripts**; if an upstream file cannot run unmodified, report unsupported/hold or preregister a separately labeled protocol translation before running.

Official download/verification example (requires outbound network, currently blocked in the interactive container):

```bash
set -euo pipefail
curl --fail --location --retry 2 -o smtinterpol-2.5-1453-gedae1f37.jar \
  https://ultimate.informatik.uni-freiburg.de/smtinterpol/smtinterpol-2.5-1453-gedae1f37.jar
echo "8d42e87614fcdbe6fce5233b91f20563dfd9a854d999127d70cfb42853e091c7  smtinterpol-2.5-1453-gedae1f37.jar" | sha256sum --check
java -version
```

Fail closed as `BLOCKED_BINARY_FETCH` if the JAR fails to materialize or hash check. No run or success count may be synthesized from download metadata.

## 3. Freeze a **new, different-author** cohort BEFORE reading source/gold

1. Choose a separately authored, legally accessible public suite that genuinely asks for executable interpolation results (not only `check-sat`). Do not reuse already-opened Ultimate/SMTInterpol source examples for first-blind success.
2. Preregister EXACT original upstream commit, file list/order, original Git blob SHA1, selection rule, exclusions, identity of original answer metadata, signatures/logic, program time/memory budgets, and the judge implementation hash in a commit.
3. Freeze predicted outputs or abstentions and output SHA **before** opening reference annotations or verifier results. Reserve immutable `FIRST` storage; subsequent fixes go into a separate `POST_FIRST` record.
4. Mark author independence, benchmark-family overlap and source-answer exposure individually; same repo / different subfolder is not independent-authored transfer by itself.
5. At this writing, **cohort NOT SELECTED, prereg NOT CREATED, baseline NOT EXECUTED.**

## 4. Whole-goal correctness contract

For every full original script:
- Capture stdout, stderr, exact exit status, wall/user/system CPU time, peak RSS and deadline/timeout per process. `unsat` is only the prerequisite when interpolation is requested, not full-script success.
- Treat `unsupported`, `unknown`, errors, missing `get-interpolants` output, incorrect interpolant count, malformed SMT terms, and lost originals as **HOLD**, not PASS. `SAT` on an expected-unsat interpolation query is a separate disagreement for investigation, not a generated interpolant.
- For each original binary Craig pair `(A,B)` and emitted `I`, check **all three**: `A ∧ ¬I` is UNSAT, `I ∧ B` is UNSAT, and `I` uses only shared nonlogical symbols of A and B (respecting sorts, bound variables, theory symbols and SMT-LIB scoping). For sequences/trees check the corresponding inductive obligations for every node, not only a final conjunct.
- Validate obligations in fresh independent solver processes, preferably two implementation-diverse solvers with recorded exact versions. Solver agreement without proof objects is **dual-solver checked**, not proof-kernel certified. If a checker does not understand an interpolation-specific theory, label that case UNKNOWN, never retrofit the formula.
- Original comments, `set-info :source`, `Desired Interpolant`, downstream answer blobs, oracle output and post-first human repairs must **never** be candidate-generation input. Retain their exact original bytes for source provenance and post-first audits separately.
- Avoid parsers based only on `unsat` substring matching or a regex that counts commented-out script commands as real commands. When no complete parser is available, the only authorized output is HOLD.

## 5. Matched comparison and promotion gate

All approaches receive identical source visibility, task selection, timeout/CPU/RAM limits, original verifier rights and one declared test budget:
`C`: strongest free professional domain-appropriate classical solver.
`A`: frozen own-weight NEUMANN proposal policy **only after G0 admits**.
`B`: same-budget sham/shuffled-feedback own-weight control.
`D`: memory/retrieval-allowed version, explicitly NOT conflated with weight learning.

Track (i) additional original goals fully solved, (ii) newly executable operator/semantic type first proposed **by own weights**, (iii) new-author and new-family unseen transfer, (iv) cost including program proposal, classical execution, oracle calls, training, verification, reruns, source acquisition, and model/token/GPU/CPU/RAM accounting. Partial solver CPU alone cannot establish 10x all-in benefit. Run prior held-out abilities again to measure regression and forgotten capabilities.

**Stop rule:** If the professional classical solver supplies full correct original witnesses within the frozen budget, there is no credible new capacity gap on those items; `G1_HOLD` remains. If it fails, that is only **bounded headroom candidate**, not a proof that all classical solvers fail; evaluate same-rights alternatives and prerequisites before own-weight training. If no independent executable original judge, G0 is `BLOCKED`. G2 and global Q1–Q7 remain OPEN until independently supported.

## 6. Current execution receipt / degraded mode

- Local interactive environment confirmed OpenJDK 21 exists (2026-10-27), but outbound network fetch of official JAR failed; there was **no completed official SMTInterpol run** in this continuation.
- The historical post-first 4/6 reference checks and two **human repairs** cannot be recounted as first V2 successes. Historical V2 first **0/7** unchanged.
- Newly provided here: pinned executable distribution/identity, whole-goal scoring contract and admission/stop conditions. This document itself does **not** improve the Q1–Q7 score.

## 7. Minimal handoff/WBS

**W1** Download, validate JAR sha256, runtime check (fallback BLOCKED_BINARY_FETCH); **W2** external independent original cohort source/prereg commit (fallback NO_SOURCE); **W3** sealed first classical run; **W4** independent whole-goal checks and first-result archive; **W5** fair cost and G1 HOLD/ADMIT decision; **W6 only if admitted** A/B/C/D ownweight design. Reserve a separate retriable buffer for environment failures without changing first-run contents.

**Interface priority:** original script bytes → dedicated professional classical executor → full goal/artifact parser → fresh obligation checker → immutable evidence ledger → G1 policy gate.

**Do not auto-merge or spend resources; do not change prior adjudications.**
