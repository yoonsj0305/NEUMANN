# Decision 2 — Architecture Multiplier AM1

Status: **PREREGISTERED OPENED DEVELOPMENT EXPERIMENT.**
No result exists until the accelerator one-shot runner completes.

This is the only active capability experiment after Decision 1 ended the
single-thread CPU harness. It does not open v107 sealed evaluation, call a
frontier model, train weights, or resume LP architecture polishing.

## Question

Does the same frozen Gemma 4 E2B core become materially stronger per measured
end-to-end resource under NEUMANN orchestration than under its strongest matched
baseline?

The experiment is designed to return exactly one of:

- `PASS_ADMIT_ONE_SEALED_GENERAL_EVALUATION`
- `FAIL_ARCHITECTURE_PIVOT`
- `NOT_EVALUATED_INFRASTRUCTURE`

The first two close Decision 2. The third means the accelerator measurement
itself was invalid and may be repaired without changing the architecture or
thresholds.

## Frozen core and rights

Model:

- `google/gemma-4-E2B-it`
- revision `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- BF16
- one CUDA device
- no fitting or parameter mutation

All five Runtime-0 arms run on the same loaded core in one process:

- B0: direct,
- B1: reasoning,
- B2: one-tool baseline,
- B3: strongest iterative matched-tool baseline,
- N: NEUMANN typed-representation path.

The existing Runtime-0 authority contract remains in force. B3 has the same
eligible deterministic tools and certified representation executor rights as N.
The original task checker remains authoritative.

## Opened development set

Exactly 12 author-constructed, fully opened tasks:

- 4 exact arithmetic,
- 4 bounded Python coding,
- 4 finite CSP planning.

This is intentionally small. It is a decision experiment, not a new benchmark.
There is no sealed or frontier-derived task in AM1.

Total observations:

```
12 tasks × 5 arms = 60
```

Generation is deterministic (`do_sample=False`). One observation per arm/task
is retained; there is no favorable repeat selection.

## Strongest matched baseline

The baseline is not named in advance because the requirement is to beat the
strongest matched use of the same core.

After all observations are retained, choose among B0-B3 by:

1. maximum independently verified accepted tasks,
2. on a tie, fewer total model tokens,
3. on a tie, lower complete end-to-end wall time,
4. on a tie, stable arm name.

N is never eligible to define its own comparator.

## Capability

For arm `a`:

```
Q_a = verified accepted tasks / 12
```

Primary architecture multiplier, when baseline capability is non-zero:

```
M_A = Q_N / Q_B
```

The absolute paired task gain is also retained:

```
ΔQ_tasks = accepted_N - accepted_B
```

## Resource efficiency

The primary measured scalar is complete end-to-end wall time on the same
accelerator run:

```
R_a = Σ complete_query_wall_ms
```

This includes model generation, deterministic tools, checking, retries and
failed routes.

Primary efficiency multiplier:

```
M_E = (accepted_N / R_N) / (accepted_B / R_B)
```

This is **verified successes per complete measured second**, not energy and not
FLOPs.

Secondary diagnostics:

- successes per total model token,
- generation milliseconds,
- tool milliseconds,
- peak CUDA allocated memory.

Energy, money and FLOPs remain UNKNOWN unless an external executor adds
independently measured receipts. UNKNOWN is never treated as zero.

## Frozen PASS gate

Decision 2 passes only if every condition is true:

1. infrastructure evidence is complete and the frozen core audit is unchanged;
2. N accepts at least **8/12** tasks;
3. N gains at least **+2 verified tasks** over the strongest matched baseline;
4. N is not worse in any of the three families;
5. N is strictly better in at least **2/3 families**;
6. `M_E_complete_latency >= 1.05`;
7. N peak CUDA allocated memory is at most **1.10×** the baseline peak.

If the infrastructure is valid but any scientific condition fails:

```
FAIL_ARCHITECTURE_PIVOT
```

No threshold tuning, prompt polishing, task replacement or favorable rerun is
allowed.

If infrastructure evidence is invalid, for example CUDA OOM/core drift/token
accounting failure:

```
NOT_EVALUATED_INFRASTRUCTURE
```

Only the infrastructure failure may be repaired. The task set, model revision,
strategy contracts and scientific thresholds remain frozen.

## Accelerator boundary

AM1 refuses CPU fallback. The adapter requires:

- CUDA visible,
- one selected device `cuda:0`,
- at least 14 GiB total VRAM.

The exact accelerator name, compute capability, VRAM, torch/transformers
versions, tokenizer hash and model artifact hashes are retained in `core.json`.

Decision 1 was about the inadequacy of single-thread CPU as the capability
research surface. AM1 therefore makes **no Edge claim** from GPU performance.

## After the verdict

PASS:

```
AM1 PASS
  -> freeze current architecture
  -> ONE sealed general evaluation
  -> jointly measure admitted Q5/Q6/Q7 evidence
```

FAIL:

```
AM1 FAIL
  -> stop current General NEUMANN architecture
  -> architecture pivot
  -> no v107 holdout/frontier/edge work
```

Infrastructure invalid:

```
AM1 NOT_EVALUATED
  -> repair accelerator execution only
  -> rerun same frozen AM1
```
