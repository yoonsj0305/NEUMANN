# Decision 2 first actual accelerator result — retained FAIL

Date: 2026-10-03

## Frozen execution identity

- Frozen source head: `716e71834fe5b585e7369e7c1394919c61b3d9e9`
- Model: `google/gemma-4-E2B-it`
- Revision: `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- Precision: bfloat16
- Accelerator: Tesla T4
- Driver: 580.178.04
- Framework: torch 2.11.0+cu128 / transformers 5.16.1
- Opened tasks: 12
- Arms: DIRECT, TOOL, NEUMANN
- Terminal observations: 36/36
- Model-free evidence replay: VALID
- Terminal hash mismatches: 0
- Frozen-core audit: unchanged

The user-retained complete evidence archive is
`NEUMANN_D2_OFFICIAL_EVIDENCE.zip`, 89,766 bytes, SHA-256
`468893d7be2ac5587edee3b7f87ad4310919f8c883800df8e1f8d41150556355`.

## Frozen verdict

```
Decision 2 = FAIL
next = ARCHITECTURE_PIVOT
Decision 3 = BLOCKED
```

This verdict is retained exactly as produced by the preregistered evaluator.
It must not be relabeled as NOT_EVALUATED merely because the failure mode is
shared across all three arms.

Results:

| Arm | Successes | Model calls | Tool calls | Output tokens | Complete ms |
|---|---:|---:|---:|---:|---:|
| DIRECT | 0/12 | 24 | 0 | 6144 | 438365.942284 |
| TOOL | 0/12 | 24 | 0 | 6144 | 435523.924754 |
| NEUMANN | 0/12 | 24 | 0 | 6144 | 437706.011753 |

The strongest baseline under the frozen tie-break is TOOL. Because baseline
capability is zero, the architecture multiplier is undefined. NEUMANN's latency
ratio to that baseline is 1.0050102575.

## Failure fingerprint from all 36 retained receipts

A post-result, model-free forensic pass over the immutable receipts finds:

- 72/72 model calls emitted exactly the 256-token per-call maximum.
- 72/72 raw generations began in `<|channel>thought`.
- 0/72 generations reached `<|channel>final`.
- 0/72 generations began with a JSON action object.
- 72/72 action parses were rejected with
  `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.
- 0 tool calls executed in TOOL.
- 0 tool calls executed in NEUMANN.
- 0/72 model receipts reported a generation deadline.
- Every observation terminated as `CAPABILITY_OR_BUDGET_UNREACHED`.

The accelerator therefore removed the earlier CPU wall-time confound, but the
AM1 control protocol still failed before any TOOL or NEUMANN executor path was
entered.

## Proximate cause

The frozen runtime calls the Gemma core with thinking enabled for every control
generation. The model spent the complete 256-token per-call allowance in the
thought channel. The parser accepts only the final action object, so no valid
DIRECT final action, TOOL action, or NEUMANN representation action was ever
available to the runtime.

Observed path:

```
problem
  -> free-form thought
  -> 256-token cap
  -> no final action
  -> JSON parse rejection
  -> retry
  -> free-form thought
  -> 256-token cap
  -> no final action
```

This is the immediate measured cause of the first Decision-2 failure.

## Interpretation boundary

This result falsifies the tested AM1 architecture:

```
free-form generative reasoning
  -> compact JSON control action
  -> tool / structural executor
```

under the frozen Gemma E2B, tasks and budgets.

It does **not** show that structural compression, structure discovery, executor
selection, or minimum-necessary-computation are globally false. Those
mechanisms were not exercised in this run because neither TOOL nor NEUMANN
entered an executor path.

Likewise, this result does not justify a favorable rerun with a larger token
budget, parser rescue, different prompt, hidden-thought extraction, or altered
PASS threshold. The one-shot Decision-2 result is final.

## Architecture pivot requirement

The next opened-development architecture must separate control from free-form
reasoning. A control decision with a small finite action space should not require
hundreds of generated reasoning tokens before it can be consumed.

The next candidate should therefore test a non-generative or tightly bounded
control plane, for example finite-option scoring / constrained selection for:

1. whether direct neural reasoning is needed,
2. which public information is relevant,
3. which executor is cheapest and sufficient,
4. whether verification warrants additional compute.

Generative decoding should remain only where the task payload itself requires
generation, such as bounded program synthesis. The controller itself should be
measured and charged.

Any pivot must return to opened matched validation before Decision 3. Sealed
Decision-3 task content remains unopened.
