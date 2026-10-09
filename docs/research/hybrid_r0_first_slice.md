# NEUMANN 1 — Hybrid R0 first running integration (2026-10-09)

**State:** `FIRST_SLICE_ENGINEERING_PASS / FULL_R0_NOT_ADMITTED / R1_NOT_ADMITTED / HOLD_NEW_TRAINING`.  
**Research base:** PR #176 `c182fd3f8d8b5c711415a214e899bfefe7511a0a`. Existing first archives and global Q1–Q7 unchanged.  
**Related design:** [NEUMANN Hybrid Architecture Freeze in Notion](https://app.notion.com/p/3f47830ff3348151abc0e91df83fed1f) · [Minimal experiments plan](https://app.notion.com/p/3f47830ff334812f9759c929af41d47c).

## What is *now executable*

A minimal typed JSON/JSONL CLI: `python -m neumann1.hybrid_runtime_r0`. The same task/goal hash and original-task verifier are used across:

1. `lp.standard_form`: standard-form LP `min c^T x, A x=b, x>=0` using full native HiGHS, classical residual fixed4m, optional *untrusted external ranking* and a **real archived v102 frozen Q34 learned proposal** from exactly retained checkpoint identity. Every restricted solution is lifted to original coordinates and checked using **both primal and dual** original LP certificate. A failed restricted proposal expands/falls back to full native within the paid deadline. Frozen predictor is manually selected, **never an implicit default**.
2. `exact.linear`: exact rational linear-system solving, fast numeric hint followed by original integer-equation verification, exact Gaussian fallback on ambiguity/noninteger answer. Does not read generator ground truth.

Safety properties: unregistered schema rejected, invalid ranking/seed rejected before model import, no executable input, unsupported dependencies and unknown proof are not accepted answers, budgeted work is charged, no implicit GPU/cloud access or seal breaking. Outputs carry task SHA, certificate route, events, observed stage wall, peak process RSS (Linux), unknown cold process startup/training/energy as UNKNOWN or separately disclosed, and whether model inference was used. Import-related startup is included in per-request unassigned wall for a running process; startup before process entry remains unknown.

## How to run

Install in a Python 3.12 virtual environment with `numpy==2.3.5 scipy==1.17.0 scikit-learn==1.9.1 threadpoolctl==3.7.0 highspy==1.15.1`, then `pip install -e . --no-deps`. For **frozen Q34** only, install historical `torch==2.14.0+cpu` from the PyTorch CPU index, and require preserved v100/v101 authority archives.

```bash
printf '%s\n' '{"domain":"lp.standard_form","A":[[1,0,1,0],[0,1,0,1]],"b":[1,1],"c":[0,0,2,2]}' | python -m neumann1.hybrid_runtime_r0
printf '%s\n' '{"domain":"exact.linear","A":[[2,0],[0,3]],"b":[1,1]}' | python -m neumann1.hybrid_runtime_r0
printf '%s\n%s\n' '{"domain":"exact.linear","A":[[2]],"b":[4]}' '{"domain":"exact.linear","A":[[3]],"b":[6]}' | python -m neumann1.hybrid_runtime_r0 --jsonl
```

A frozen LP request specifies `"policy":"frozen_q34","seed":100001` or `100002`; the engine loads and checks the archived models and caches them within the current process. No inference checkpoint is shipped, trained or mutated in the new code. Historical source must be an admitted LP input. A supplied ranking uses `policy="external_ranking"` and is marked **untrusted**, not learned.

## Actual engineer-level evidence: FIRST measurements, no model tuning

- [14-test original smoke](https://github.com/yoonsj0305/NEUMANN/actions/runs/37896972981): 14/14 PASS plus two independent CLI tasks, original-verified.
- [Expanded regression CI](https://github.com/yoonsj0305/NEUMANN/actions/runs/37897731749): **17/17 PASS**, including the real subprocess JSONL and adversarial/invalid certificates.
- [Actual first archived frozen Q34 cold run](https://github.com/yoonsj0305/NEUMANN/actions/runs/37897312107): 1 opened v102 LP view, native, deterministic 4m, frozen model all VERIFIED; cold model 1253.9ms versus native 111.8ms and classical 63.5ms. This negative cold-start comparison is retained.
- [Cold+warm persistent archived model replay](https://github.com/yoonsj0305/NEUMANN/actions/runs/37897620753): same one opened original, Native **111.64ms**, classical fixed4m **63.23ms**, frozen cold **1259.65ms**, frozen same-process warm **52.07ms**; all 4 original LP certificates VERIFIED. 1 model forward per learned answer; warm reuse cache hit, cold cache miss. **This is one previously opened LP**, not multiple independent tests, not a statistically estimated gain, not a complete resource comparison, not evidence of generalizing to new tasks. Warm and cold cannot be mixed to invent a fair speed ratio.
- [P0 reusable code and rights inventory](../research/hybrid_r0_p0_asset_manifest_20261009.json), includes PR/evidence ancestry and sealed Decision3 prohibition.

## Critical unresolved items before declaring full R0

- Frozen learned model is currently a PyTorch CPU checkpoint loader whose **cold model restore dominates latency**. Need persistent-policy queue and measured process RAM, optional lightweight provider for Edge if correct equivalence proven. Windows `resource` compatibility remains an engineering issue.
- Exactly *two* domains have been wired: standard LP and exact linear systems. They are both numerical/algebraic; a genuinely different SMT/SyGuS or program proof adapter is still missing.
- Full total-cost accounting for remote execution, energy/thermal, trained investment under selectable traffic profile, and cold deployment remains missing. Current process RSS and wall do not imply energy.
- R0 typed proposal and conditional fallback are usable but no automatic learned **semantic** parser or novel-sufficient-program composition. `external_ranking` cannot establish learned premium because its generation cost is UNKNOWN.
- No independent fresh-held-out structural family; no official model generalization or Frontier Gap re-evaluation.
- Branch is atop draft PR #176, **not main**, no safe migration or merge into main yet.

## Highest-value next engineering tasks

1. Verify this first slice under integration PR and prevent any source/first-result alteration; close P0 source-provenance holes.
2. Add second qualitatively distinct **SMT/SyGuS** certified adapter from the already built cvc5+Z3 harness, while treating its 8 public tasks as OPENED engineering fixtures.
3. Measure **whole-service warm/cold, peak RSS, fallback** for the archived model and deterministic native baseline on grouped original open tasks. Fix process portability and user-visible engineering errors.
4. Declare `HYBRID_R0_COMPLETE` only once the narrow engineering acceptance criteria pass; one separately preregistered scientific G0 headroom test then decides whether any *new training* is allowed.

**Decision:** retain R0 engineering gains; old scientific `HOLD_LEARNING`, open Q1–Q7, sealed Decision3. Do not repeat fresh experiments just to raise a metric.
