# Same frozen core: exact reuse map and unbound execution edges

This is an integration specification, **not three working model adapters**.
The notebook cannot call a model, including when hardware qualification passes.

| Edge | Existing API / source | Reuse status |
|---|---|---|
| Frozen model | `experiments/general_multiplier_accelerator_core.py:FrozenAcceleratorCore()` | Actual constructor downloads/loads weights; MUST NOT instantiate during prep. |
| Generate | `core.generate(messages, max_tokens, thinking, deadline_ms)` | Returns raw, input/output tokens, IDs, wall, deadline and peak allocated/reserved VRAM. |
| Frozen audit | `core.audit()` | File map hash and parameter versions before/after; tokenizer vocabulary hash in constructor. |
| Public QA | PR #254 `validate_public`, `format_public_messages`, `extract_answer` | Pinned upstream ABI; not yet integrated into this CP1 branch. |
| Independent QA check | PR #254 `verify_candidate(view, raw, original_checker)` | External exact-original Boolean checker still REQUIRED. ABI cannot supply it. |
| Deterministic tools | `neumann1/general_runtime_v106.py:ToolPool.call` | Exact arithmetic, CSP, bounded Python, bound to old task schemas. |
| Stronger static path | PR #250 `compile_public_requirement` | Known narrow public coding grammar; 12/12 saturation already measured, do not rerun. |
| Structural path | `reduce_original`, CP0 `execute_model_free` | Existing schema-specific certified reduction, not learned discovery or generic QA. |
| Old controller | `general_multiplier_runtime.run_observation` | Hardcoded AM1 compact action format; incompatible with generic QA as a drop-in. |

## Frozen core identity

- `google/gemma-4-E2B-it` / `3e22461f65e89153144f8adb70e3b8c2cc9845a7`.
- BF16, deterministic greedy, no fitting.
- Artifact `bf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66`.
- Tokenizer `8552955a1513c80096c4155aa2de30079a20d4c3f255b9d1acf9162c859b4207`.
- Artifact hash is SHA-256 of the canonical selected-file hash map (JSON,
  safetensors, jinja); tokenizer hash is of canonical `get_vocab()`. These are
  not the SHA-256 of a single checkpoint file or tokenizer download.

## Equal-rights binding requirements, before execution

DIRECT: same frozen core, original public question, no external tools by its
defined ablation. TOOL+: same core with the strongest eligible shared tool pool.
NEUMANN: same core and TOOL+ pool plus explicitly verified structural proposals.
No gold, private checker contents, task IDs or hidden family labels in model
input. Private checkers score all arms but are not an iterative answer oracle.
Same tokenizer, originals, hardware, allowed generation budget, stopping rules
and scoring. TOOL+ and NEUMANN receive equal tools, hints and reuse rights.

Each new original needs a task adapter, trusted checker and eligible strongest
tool binding; generic `short_text/integer/choice` alone does not solve semantics.
NEUMANN also needs an executable structure proposal/certification path applicable
to that original. If it degenerates to TOOL+ without distinct useful structure,
record that fact rather than relabeling deterministic dispatch as learned Q3.
These missing semantic edges are BLOCKED, not replaced with a new architecture.

## Complete-cost receipt requirements

Retain every failed route and checker rejection. Per original and arm record:
model input/output tokens, actual forward count (not inferred from token count),
model/tool/checker calls, structure proposal and verification time, execution,
reconstruction, retries/fallback, cold model startup and its allocation, total
wall and CPU time, peak allocated AND reserved VRAM, hardware/source/core/budget
hashes and raw error receipts. Meter forward calls at the actual model boundary
without modifying frozen parameters. Existing `generate` lacks that counter.
Cost attribution overhead also counts. Missing forward count is UNKNOWN.

Store task successes separately from delivery/parser failures and hardware blocks.
Do not manufacture a success rate from zero executions. Never sum CPU seconds,
GPU seconds and tokens without a preregistered compatible model. FLOPs, energy
and monetary charges without observations remain UNKNOWN. Full cold and failed
work must be present before any cost-ratio claim.

The former AM1 `MultiplierBudget` (4096 context, 512 output, 256 per call,
4 model calls, 4 tool calls, 120s/query, 2s/tool) is available for explicit reuse,
but the >=24-source AM2 EX1 must freeze its own complete matched executable plan
before seeing outputs. No budget or success threshold was changed by this prep.
