# AM2-CP0 first control-plane pivot result | 2026-10-19

**Status: FIRST CI SCOPED CONTROL-PLANE PASS; AM2 ARCHITECTURE MULTIPLIER NOT_EVALUATED.**

## Why the architecture changed

The first actual accelerated AM1 decision was **FAIL**, not NOT_EVALUATED: Gemma 4 E2B frozen BF16 Tesla T4, all 36/36 attempted, DIRECT/TOOL/NEUMANN each **0/12**. All 72 generated model calls exhausted the 256-token allowance in the thought channel, **0/72 valid final action JSON**, 0 tool calls in TOOL/NEUMANN. Preserve frozen AM1; **no favorable prompt/parser retuning of the historical AM1**. See [authoritative critical path](critical_path_v1062.md). Earlier AM1 setup documents stated "not performed" and were stale.

The new CP0 candidate removes free-form generated action JSON control *only for publicly well-typed exact arithmetic and finite CSP*. Its route is derived from the source's public field schema, NOT from source-private family/id labels. Both TOOL and NEUMANN have equal deterministic tool execution rights; NEUMANN additionally computes an exact `reduce_original` certificate. The separately budgeted tool and original checker remain authoritative. Unknown or modified source form is rejected.

**Coding tasks are NOT solved by this code.** They return `NEEDS_ACTUAL_FROZEN_MODEL` with zero neural calls. The optional `source_candidate_syntax_only` routine is a future model-code structural filter; it cannot invent or certify source and never invokes it. Do not report 12/12 successes or new Gemma 4 ability.

## First science evidence

Preregistered before implementation: [Issue #243](https://github.com/yoonsj0305/NEUMANN/issues/243). Code [PR #244](https://github.com/yoonsj0305/NEUMANN/pull/244) (DRAFT).

- First [CI #39187612518](https://github.com/yoonsj0305/NEUMANN/actions/runs/39187612518) was **environment NO EVALUATION**, missing `scikit-learn` upon importing the repo's existing `neumann1/__init__.py`. Artifact `12158149566` preserved. No original observations executed.
- Only environment repair installed **unchanged existing** `pyproject.toml` declared requirements; experiment code/task identities/thresholds untouched.
- **First valid [CI #39187717376](https://github.com/yoonsj0305/NEUMANN/actions/runs/39187717376) SUCCESS**, artifact `12158633024`, ZIP SHA256 `18775795638ffbe2bdb7b9bbe89151db833317add08202e5c511fec83e9ed5a8`, raw JSON SHA256 `7e31d129a2e593955b2e0e82d060bf87a0daab6504a1a5f021a1247349a53f97`, source task Git blob `357f4bb4827543b0a2c9f8d809c8911b51040820` pinned. The artifact was downloaded and independently checked: CRC PASS, first JSON SHA matches, 24 unique arm/task pairs, 16 accepted original checker reports, 0 learned/model calls.
- Original 12 opened tasks × TOOL/NEUMANN (24 terminal controls): **each** 4/4 math and 4/4 finite CSP original checker pass (**8/12**), and 4/4 coding explicitly no model / no pass. Same answer on all eight TOOL-vs-NEUMANN identical deterministic tasks. Neumann adds the exact reduction certificate but does not expand capability on those tasks.
- Failing answer and trust tests: wrong rational rejected, invalid full CSP assignment rejected, tampered model view rejected, malformed and unsafe Python source rejected. Source candidate syntax-only acceptance explicitly NOT safety/correctness certification.
- TOOL deterministic tool calls 8, NEUMANN calls 16 (8 reductions + 8 executors), and model calls 0. **This is not an empirical conclusion about cold full complete latency**; warm submillisecond jitter cannot establish economy and CPU tests cannot qualify as BF16 accelerator performance.

## Formal no-free-advantage observation

For all eight non-code sources `t` in the exact CP0 opened set, the source `Post`/original checker sees identical candidates:

`Candidate_TOOL(t) = Candidate_NEUMANN(t)` (8/8 actual checked),

`Accepted_TOOL(t) = Accepted_NEUMANN(t) = True` (8/8),

and neither architecture calls a neural model. Therefore **AM2-CP0 alone produces 0 differential original-checker successes** under this strong matched deterministic baseline. Adding the representation check does not create new mathematical operators by itself. The AM1 admission requirements (N ≥2 additional solves, or ≥same solves with ≥2× less complete wall) are NOT tested on a real frozen model by CP0. The 4 code tasks need actual learned source generation to complete an architecture multiplier.

## Scientific verdict and next path

- `AM2_CP0_FIRST_MODEL_FREE_TYPED_CONTROL=SCOPED_PASS`.
- `AM2_CP0_EIGHT_DETERMINISTIC_TASKS_MATCHED_ADDITIONAL_CAPABILITY=ZERO`.
- `AM2_E2B_MULTIPLIER=NOT_EVALUATED`; `ACTUAL_AM1_FIRST_VERDICT=FAIL_UNCHANGED`.
- `NEURAL_Q3/GENERAL_Q1_Q7=OPEN`; `Q5_FULL_COST_10X/FRONTIER_Q7=UNPROVEN_OR_BLOCKED`.
- `NO_NEW_MODEL_TRAINING=TRUE`; `NO_PAID_API/GPU=TRUE`.

Next high-value step is NOT further CP0 CPU demos or toy-task tuning. Freeze an AM2-CP1 **matched** model execution protocol in which (1) DIRECT has a true comparable same-core, (2) TOOL shares full deterministic and source-generation rights, (3) NEUMANN alone may add verified nontrivial representation discovery, but must pay its cost, (4) code creation must be emitted directly as code without a gratuitous free-form JSON action, with original checker authority and complete resources, and (5) a real BF16 accelerator satisfies identity requirements. No hardware/authority -> **BLOCKED_HARDWARE**, not fake PASS. Do not unseal v107 or run frontier reference until an actual matched opened gate passes.

**Record is architecture discovery, not final NEUMANN or global Q3 proof.**
