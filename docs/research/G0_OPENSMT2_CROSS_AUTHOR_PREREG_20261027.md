# NEUMANN 1 | G0 Cross-author Craig output headroom prospective cohort preregistration — 2026-10-27

## Immutable intended decision
**This is a prospective pre-original-file-content baseline, not a new AI success.** North Star unchanged. Q1–Q7 OPEN; G1 HOLD. Prior SMTInterpol-original 7/7 classical baseline and V2 first 0/7 untouched.

### Authorship and source independence
Different public solver project: `aehyvari/OpenSMT2`, independent of `ultimate-pa/smtinterpol`, pinned Git commit **`76ee514d36e0a033a160da5e0a138f6fd83e1bcc`**. This is *different repository and tool-author lineage*, NOT proof that each benchmark file has different individual author. Several files' code-index *snippets* were visible in search BEFORE preregistration; this is **INDEX_SNIPPET_EXPOSED**, not fully unseen-blind. No complete source file was fetched before this research preregistration.

**Exactly 12 fixed source paths, order retained, without reading their full content**:
1. `regression_itp/uf_bug.smt2`
2. `regression_itp/dec-far2.smt2`
3. `regression_itp/bug_mask_ite.smt2`
4. `regression_itp/itp_bug_small.smt2`
5. `regression_itp/uf_itp_problem.smt2`
6. `regression_itp/distinct_unsat.smt2`
7. `regression_itp/uf-itp-edge-split.smt2`
8. `regression_itp/LIA/lia_itp_split.smt2`
9. `regression_itp/trivial-proof-A.smt2`
10. `regression_itp/trivial-proof-B.smt2`
11. `regression_itp/LIA/issue213_itp.smt2`
12. `regression_itp/dec-far1.smt2`

Original logic/program names not yet evaluated. Filename visibility, source-index snippets, and all prior SMTInterpol authored examples are recorded as exposure. ALL 12 count in denominator. No replacement for missing, unsupported, easier, or SAT cases. Exact original Git blob hash and size are discovered **after** preregistration and preserved in first output. License check mandatory before redistribution; keep original source in runner only, export hashes, IDs and command output, not raw original files.

### Research question
Does a strong existing professional interpolation engine SMTInterpol 2.5 satisfy original OpenSMT2 regression interpolation goals after a **semantic-preserving front-end adaptation**? This probes strong classical headroom. A C2 success forbids claiming a neural necessity on that task. An absent specialist result is only candidate headroom, not proof classical impossibility.

### Pre-approved execution protocol
- Runtime: public GitHub ubuntu-latest; Java 17+; download official Freiburg SMTInterpol JAR with SHA256 `8d42e87614fcdbe6fce5233b91f20563dfd9a854d999127d70cfb42853e091c7`. Source: [official](https://ultimate.informatik.uni-freiburg.de/smtinterpol/docu.html).
- ONLY conversion permitted: remove OpenSMT-specific `(set-option :produce-interpolants ...)`, `(set-option :certify-interpolants ...)`, `(set-option :interpolation-* ...)` in a **separate execution copy**, insert SMTInterpol `(set-option :produce-proofs true)` at the top. Never modify original named assertions, formula, logic, declarations, interpolation partitions, or original query. If other incompatible options/commands exist, HOLD, not ad hoc patch.
- For full binary Craig score eligibility: exactly one `check-sat`, exactly one `get-interpolants A B` with **two literal partition names** (case sensitive), exactly two top-level named asserts, no other asserts, no `get-proof`/extra goals, no `push/pop`, and eligible QF logic. Complex multiple query/partition scripts are recorded `OUT_OF_NARROW_SCOPE`, not deleted from denominator. This is a diagnostic subset, not all 12 original goals.
- Original binary output goal MUST be an actual concrete expression after UNSAT, no unsupported/error, not only solver exit 0. For each candidate I run independent Z3 in fresh processes on A∧¬I and I∧B, require both UNSAT and common declared-symbol restriction; inability to parse or verify = HOLD. Do not use source comments or embedded expected interpolants as candidate-generation input.
- Isolated solver processes, 7s wall, CPU 4s, 800MiB *sampled RSS watchdog* (no RLIMIT_AS on JVM), output/hash/cpu/wall/RSS/error/attempt counts, no paid resources. Sampling peak is lower bound. Preserve FIRST receipts before changing code. First execution may fail on protocol mismatch: record first FAIL/HOLD then post-first modifications in separate log only.
- Comparator `C` is best free domain-appropriate classical interpolation engine (SMTInterpol native); `C_own` is original OpenSMT2 native optional only after reproducible standalone build; generator V2 not scored cross-project without locked port. No pretrained neural weight producer exists here, so A/B/D **NOT RUN**, G1 **HOLD** even if C fails.

### Stop / promotion
If domain-appropriate professional C2 outputs independently checked full Craig witnesses, label `CLASSICAL_SOLVED` and stop trying trained DSL patches on those tasks. If C2 incomplete, `STRONG_CLASSICAL_GAP_CANDIDATE` only after verifying the original goal and permissible implementation translation; don't auto-admit neural study. If no comparable original test or independent checker, `G0_BLOCKED`. **Global Q1–Q7 stay OPEN.**

### Costs and WBS
W1 prereg and adapter compile; W2 verify original commit / source blob IDs; W3 frozen first output; W4 distinct-process Z3 Craig obligations; W5 attribution + costs + status. Fail-closed degraded mode: missing source/JAR/solver/checker = NOT RUN/HOLD rather than model success. Resource usage and source fetching not counted as model computation without full accounting. Do not infer 10x.
