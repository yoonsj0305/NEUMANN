# NEUMANN 1 | OpenSMT2 cross-project original Craig gate — actual results (2026-10-27)

**Decision**: `G0_C2_CROSS_PROJECT_SCOPED_PASS_7_OF_7_ELIGIBLE` / `Q1–Q7_GLOBAL_OPEN` / `G1_HOLD` / `G2_NOT_RUN`. This is a result about the **existing classical specialist SMTInterpol**, **NOT** about NEUMANN trained weights or novel operator invention.

## 1. Freeze / execution provenance

- Source, externally separately developed interpolation regression suite: [aehyvari/OpenSMT2](https://github.com/aehyvari/OpenSMT2) @ `76ee514d36e0a033a160da5e0a138f6fd83e1bcc`. It is an independent project from `ultimate-pa/smtinterpol`, but it is **one author's/project family's regression suite**, not 12 unrelated authors nor a sealed frontier benchmark.
- 12 exact original paths, methodological contract, and search-index snippet exposure frozen **before full file body access** at prereg GitHub commit `8ae6dc5f9b7127b72bfb7d5875a7501f8f780981`: [frozen prereg](https://github.com/yoonsj0305/NEUMANN/blob/8ae6dc5f9b7127b72bfb7d5875a7501f8f780981/docs/research/G0_OPENSMT2_CROSS_AUTHOR_PREREG_20261027.md).
- Original candidate generation by professional Java **SMTInterpol** official pinned binary `8d42e87614fcdbe6fce5233b91f20563dfd9a854d999127d70cfb42853e091c7`. The permitted adapter filters only OpenSMT-specific solver options from a separate execution copy; original logical assertions, declarations, names and query are retained.
- **Failed first executor** [GitHub Actions #40446804675](https://github.com/yoonsj0305/NEUMANN/actions/runs/40446804675), raw artifact ID 12708143989: coding error `stdout,stderr=''` before producing any scored case. This is `EXECUTOR_FAIL`, **not a scientific negative**. Preserve historical run.
- **Post-first environment-only repair** [GitHub Actions #40446877079](https://github.com/yoonsj0305/NEUMANN/actions/runs/40446877079), commit `ea0cb595cfa23a53bb2a8eaada3c48e74bd0133a`, raw specialist artifact ID **12708163766**, ZIP SHA256 `f7a72dfe2d64ba3c91e3f77afb0396dc5b2d510deb800229fa24f99aaf4081e1`. 12 original source IDs and raw stdout/stderr frozen in the artifact. JSON summary originally written under renamed path and therefore **omitted from the first post-first ZIP**, a known archiving defect, not silently repaired; published step logs show 7 output candidates, 3 restricted-scope holds and 2 execution/parser error holds.
- Initial raw classifier was a deliberately narrow regex-based gate, *not* independent output proof. Later exact A/B checks used the original pinned files and **previously frozen solver stdout**, not a new C2 candidate generation.

## 2. Actual independent original Craig conditions

- Judge script: [independent checker](https://github.com/yoonsj0305/NEUMANN/blob/research/rc51-intelligence-spend-gate-20261026/research/q3/discovery_policy/opensmt2_external_craig_postfirst_audit.py), no source solution annotations accepted as candidate input. Full original typed declarations and named A/B extracted with fail-closed s-expression parser. Candidate I extracted solely from prior C2 raw stdout.
- [Actual independent auditor Actions #40447318767](https://github.com/yoonsj0305/NEUMANN/actions/runs/40447318767) used independent **Z3 4.13.3.0** parser/solver in fresh Python subprocesses, two obligations `A & (not I) = UNSAT`, `I & B = UNSAT`, plus declared-symbol shared-vocabulary check.
- SHA256 of immutable auditor `POSTFIRST_INDEPENDENT_CRAIG.json`: `bb59b41ed7eee747db123fded501c19ff06aceec110dccbc8ed8cf12b1b6eea2`. Artifact ID **12708707649**, ZIP SHA256 `dccca9891f94ff5008d6af94158b1448d3aaca040984c744079c33fdf994f9b0`.
- Result: **7/12 independently checked classical Craig witnesses; 7/7 fully eligible attempts, 14/14 independently checked UNSAT implications, 7/7 common declared-symbol checks.** The other **4/12** had original script outside strictly two-assertion/two-partition-one-query judge scope; **1/12** lacked an UNSAT prerequisite after original parser/executor difficulty. No candidate was silently promoted, replaced, or excluded from overall denominator.

| Source original | Specialist independent Craig |
|---|---|
| `regression_itp/dec-far2.smt2` | Z3 obligations 2/2 UNSAT; shared-symbol OK |
| `regression_itp/bug_mask_ite.smt2` | Z3 obligations 2/2 UNSAT; shared-symbol OK |
| `regression_itp/itp_bug_small.smt2` | Z3 obligations 2/2 UNSAT; shared-symbol OK |
| `regression_itp/distinct_unsat.smt2` | Z3 obligations 2/2 UNSAT; shared-symbol OK |
| `regression_itp/LIA/lia_itp_split.smt2` | Z3 obligations 2/2 UNSAT; shared-symbol OK |
| `regression_itp/trivial-proof-A.smt2` | Z3 obligations 2/2 UNSAT; shared-symbol OK |
| `regression_itp/trivial-proof-B.smt2` | Z3 obligations 2/2 UNSAT; shared-symbol OK |

The 7 are solver verdicts from distinct SMT solver implementations, **not proof objects checked by a proof kernel**, not a certified comprehensive SMT parser, and not a genuinely held-out unseen author + unseen paradigm performance evaluation. As the source benchmark itself is another interpolation tool's regression suite, source/project independence is not equivalent to strong general-discovery transfer.

## 3. Cost, causality, and what the result means

- C2 actual wall/CPU/RSS values were measured in the hosted runner in its 12 tasks, but the initial renamed JSON output **was not successfully archived**. Do not invent an aggregated numerical cost or compare to a model not run; full system time, power, resource cost and an all-in Pareto ratio remain UNKNOWN.
- The seven successful executable outputs were generated by **a published classical algorithm with zero ownweight NEUMANN forward/training**. Therefore `NEUMANN_EXCLUSIVE_DISCOVERY_DELTA=0` on evaluated tasks; this is not proof of impossibility for unseen tasks.
- A second independent code lineage resolving these externally authored tests removes the justification for learning a narrow new fixed DSL there. `G1_HOLD`, `G2_NOT_RUN`, no Dust/MeZO/EGGROLL and no funding consumption. Do not merge the draft research PR based on this metric alone.
- The remaining missing capability is **actual own-weight invention of an open typed executable relation/algorithm, causal learning from independently verified failures, and transfer beyond author/project/representation families** under matched same-rights classical baselines.

## 4. Decision: stop repeating interpolation tests as a proxy for general intelligence

**Delete** further patches to fixed candidate generators that only replay these original Craig tasks. **Keep** SMTInterpol+Z3 as a bounded classical tool, not an intelligence score. The next decisive task should be a different problem type with independent verifier and strict sealed multi-author transfer (not another more elaborate interpolation pipeline). Run the strongest equal-rights domain classic C *first*; only allow A/B/D trained proposer if C leaves a clearly scoped verified representation gap and the proposer proposes an actual executable new typed operator **from its own weights**. Existing open questions remain unchanged.

## 5. Known defects, corrections and degraded mode

- `INDEX_SNIPPET_EXPOSED`: GitHub code-search snippets of some sources visible pre-registration. This is prospective relative to full source access, not sealed blind.
- Initial semantic equivalence adapter strips only declared OpenSMT-specific options; not an automatic equivalence proof for all unsupported input constructs.
- Checker excludes complex interpolant sequences and s-expressions with unsupported binders. HOLD is not a claim of failure by all classical solvers.
- Artifact first-result JSON path discrepancy is an archival defect, not a missing source output: 12 stdout/stderr files are immutable in preserved artifact.
- Unrun independent formal kernel check / whole-system energy / exact combined source-acquisition overhead stay UNKNOWN.
