# NEUMANN 1 | Q3 G0 original VeryMax exact reframe: FIRST NO-GO and stop

**2026-11-06. Registered prospective method, historical source-family shortlist. Scientific conclusion: NO NEW ORIGINAL SOLUTIONS (0/4).** Global Q3 learned semantic invention / Q4 all-in >10x / Q6 independent-formalism generalization / Q7 frontier all **OPEN**. This is a useful *negative* architectural result, not an overall research success.

## 1. Fixed original problem, legitimate source

2026 SMT-COMP QF_NIA original per-task all-17-solvers-unsolved intersection had 17 benchmarks, exactly 4 with publisher family `20170427-VeryMax/ITS`. These 4 were **all** included here; 13 MathProblems were excluded due to different problem family and known prepublished witness retrieval, not after seeing outcomes of these 4.

Published 2025 nonincremental SMT-LIB QF_NIA archive from Zenodo record 16740866, 191.2 MB compressed [Estimate from release listing], pinned release MD5 `6a3ae3b7eb10688070c44922ccd940aa`, verified **PASS** before extracting four exact files. Actual downloaded archive SHA256 `4d40ff1ea0c517db1ed80fb5204109c941924d826c4bc173bedb3946eec5013d`. File SHA256 identities in table below. This source selection was informed by published scoreboard statuses, NOT blinded to the experimenter. Same-publisher four tasks, **not** independent-author Q6.

## 2. Rejected or retained assumptions

- **Rejected:** expanding the finite-state Mealy benchmark count can certify new semantic invention.
- **Retained physical/computational prerequisite:** a useful external task must be unsolved *under the actual agreed computation/time budget* by equally privileged strong classical controls.
- **Hypothesis tested:** original unconditional integer interval bounds `L <= x <= U` on a variable appearing inside nonlinear multiplication allow complete, logically exact case splitting into `x=L,...,U`, with at most 64 total cases and at most 3 selected variables.
- **Necessary soundness:** original SAT requires an exact original-formula integer assignment. Original UNSAT requires *all* finite branches proved UNSAT by both original Z3 and independently sourced cvc5. No theorem from one failed branch.
- **What was deliberately deleted:** neural calls, additional handcrafted rules, source-specific parameter tuning, user-ARC original 11-ID reserve consumption, replay of already-run MQTT/TLS/RC39 performance tests.

## 3. First original execution record and independent no-go audit

- Preregistered before fetching four source bodies in `docs/experiments/q3_G0_VERYMAX4_EXACT_BOUNDED_REFRAME_PREREG_2026_11_06.json`; source and 8 controls frozen.
- [#42144201913](https://github.com/yoonsj0305/NEUMANN/actions/runs/42144201913): initial preflight **FAILED** after pinned archive 4/4 fetch and controls 8/8 PASS, before math solver entry because Python root path was incorrect (`parents[3]` instead of `parents[2]`). Original failure artifacts preserved; not scientific FAIL.
- Only that module-root infrastructure path was changed. The error-output shell wrapper was amended so future errors remain visible; original method, chosen original filenames, caps and initial hypothesis unchanged.
- [#42144606986](https://github.com/yoonsj0305/NEUMANN/actions/runs/42144606986): **first actually executed math comparison**, 4/4 source identities pinned, 8/8 controls PASS, workflow SUCCESS but scientific `G0_NO_CERTIFIED_MATCHED_HEADROOM` with **0/4 proven positive**. Full first JSON SHA256 `ea8df5dd7f6f3ce494a096f8dfca88a7e7e556e51608f4e480ce3f4a92a3107a`; immutable original artifact attached.
- [Read-only first audit #42145363969](https://github.com/yoonsj0305/NEUMANN/actions/runs/42145363969): **PASS** independently checked exact original receipt SHA, all four SHA256 input identities, all full outcomes, 0 positives, exact first branch per case, forged 1-positive metric rejected, original solver source **not rerun**.

## 4. Full original denominator and mechanical failure mode

| Original VeryMax/ITS source | Original source SHA256 | Source-derived exhaustive branches | Branches completed | Z3 15s | cvc5 15s | Exact reframe |
|---|---|---:|---:|---|---|---|
| `From_AProVE_2014__Velroyen08-narrowing.jar-obl-8__p14386_terminationG_0.smt2` | `8443699407ec30931eed79834d360229247734109cd67e7e0e6a22f3a267e097` | 9 | 1 | unknown | timeout / unverified | UNKNOWN |
| `From_T2__fun5.t2_fixed__p1007_terminationG_0.smt2` | `a3bb6da0ada1f5fdb3f87f4a3bab49fe975d4ce14768fc9d85d5278a38425f30` | 27 | 1 | unknown | timeout / unverified | UNKNOWN |
| `From_T2__nakata.t2__p5330_terminationG_0.smt2` | `c1a1f5cfd7ffc2935b70400b94cd86479f28296411b0c7f25d5963f194bf1d35` | 3 | 1 | unknown | timeout / unverified | UNKNOWN |
| `From_T2__tqli.t2__p25231_terminationG_0.smt2` | `1872a2978bd3b0238fa660d8fa962402255e9600a9fda821cc5c0119b9e45c17` | 27 | 1 | unknown | timeout / unverified | UNKNOWN |

**Core falsification:** simple bounded coefficient enumeration is not sufficient. Even a *single fixed bounded assignment* in each of these sources remained unproved by Z3 for the allocated wall budget, so enumerating the rest cannot magically remove the hardest residual constraints. Every branch `UNKNOWN_BRANCH_NOT_Z3_UNSAT`, no SAT witnesses, no independent UNSAT proofs, no false claimed certification.

Detailed first-audit included exact source-derived finite-variable names and intervals in the audit JSON; none is a filename-conditioned algorithm branch.

**Fairness caveat**: configured approximate 15s budget per arm, but observed original solver wall times are ~15.04–15.16s, cvc5 ~15.10s each, exact reframe ~15.02, **19.40**, 15.10, 15.13s. The 19.40s case **overshot the intended same-wall budget**, so do NOT call this a strict equal-wall superiority trial. Since method gained **0** verified results even with its extra time, this overshoot cannot conceal a success; it makes any favorable efficiency claim more inadmissible. cvc5 installed on runner, yet the error status `UNKNOWN_CVC5_UNAVAILABLE_OR_TIMEOUT` conflates availability and deadline in code. Installation success plus ~15.10s wall is consistent with timeouts; log status alone is not an independently checked SAT/UNSAT result.

## 5. First-principles interpretation, cost and uncertainty

The transformation is logically sound: if the original source includes the conjunct `L <= x <= U` over integers, then `F` is equivalent to `OR(F AND x=L,...,F AND x=U)`. This is generic, but exactness alone does **not** reduce the complexity of each case. The critical operation must change the **representation of the residual relation**, not just order a finite enumeration.

Measured source-prover calls: at most 1 reframe branch per original within prescribed cap; 4 original cases in all. Absolute native CPU, memory, joules, training amortization and dollars are **not** reliably metered, therefore total lifecycle cost and any product-style `Idiot Index` are **NOT MEASURABLE**, not estimated as 10x.

Risk: claiming a 2026 competition 17-way unsolved file is mathematically unsolvable would be false; modern specialized methods and published external witnesses can close parts of that gap. This trial itself offers **no new classical or learned solution**.

## 6. Next steps, limited to decisive changes

1. **STOP** retraining or fine-tuning a proposal policy on this exact failed finite split. The first result precludes calling a posthoc branch patch a fresh 4/4 experiment.
2. **Strong G0 requirement:** select an external family with native semantic verifier where a *representational* free oracle can beat strongest reproducible same-rights solver AND produce a verifiable original mathematical certificate. Prior classical methods must be granted access to the same representation generator.
3. **G1 conditional only:** once an admissible genuinely new representation makes a demonstrable difference, freeze an actual trained proposal policy and compare four arms (strong classical / neural direct / same system minus learning / full learned) across **independent publisher/formalism** groups and all-in source+model+verification+training expense. No ARC original eval 11 reserve consumption.
4. **Degraded mode:** unknown state bound, no exact witness, unsound/disjunctive interval extraction, wrong source SHA, budget exhaustion => `UNKNOWN`; never rewrite a prior FAIL to PASS.

**Operational decision**: `G0_VERYMAX4_BOUNDED_PROJECTION=NO_GO_0_OF_4`. This does not prove global Q3 failure. Keep program code as negative research evidence, **not** as mainline runtime functionality. Do not claim model-independent transfer beyond the two existing Mealy-encoded protocol families.

## 7. CI hygiene

The normal repository CI initially tried to collect this research-only `z3` test without the optional Z3 dependency and failed `ModuleNotFoundError`; normal CI source must now skip this **optional** module if not installed. The dedicated scientific workflow pins and installs Z3 and executes **all eight controls**, not skipping. This is only an integration fix; the immutable first math source and negative result are not recomputed.
