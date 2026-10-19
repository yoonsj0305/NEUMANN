# AM2 Colab / matched opened development preparation — 2026-10-19

**Preparation completed; actual Colab GPU qualification NOT_MEASURED;
matched model comparison BLOCKED / NOT_EVALUATED.**

## Inspected authority and preserved facts

Remote main inspected at `55178a211962caf5ce677deb37edd30bfb4fdccc`.
The new research branch starts at CP1 PR #248 head
`193a1bf269cfe667defcb9af57c0ebeb7ec3dec6`. PR #254 ABI was inspected at
`0c4ba37d18dd6a2a9363f5d2bb326edfe484beea`; PR #250 static challenger at
`c9be5910a5641a1ab055cc5236b8847005e188c4`. These are open Draft dependencies,
not merged main functionality. No upstream history was rewritten.

Authority: [Issue #253](https://github.com/yoonsj0305/NEUMANN/issues/253),
especially [the protocol correction](https://github.com/yoonsj0305/NEUMANN/issues/253#issuecomment-6258775374),
`frozen_north_star.md`, `core_question_gates.md`, `critical_path_v1062.md`,
`frontier_gap_evaluation.md`, and `decision3_sealed_gate.md`.

AM1's first real accelerator FAIL, 36 terminal observations and 72 thought-only
generations remain immutable. The bounded classical Q3 proofs are retained;
learned structural discovery is unproven and global Q1–Q7 remain OPEN.
The old R0/F0/L0/NC checkouts and evidence are not edited.

## Colab deliverable

`notebooks/AM2_Colab_Native_BF16_Gate0.ipynb` is a hardware-only notebook.
It downloads only hash-pinned public preparation source files from an immutable
commit; no package install, model download, training or inference cell exists.
It reuses the unchanged `experiments/am2_cp1_native_bf16_preflight.py`.

Select a runtime ONLY if the Colab UI confirms it is free and available to the
current account. Do not select a premium resource, purchase units, or cycle
allocations to obtain a different GPU. Confirm the notebook's free-runtime flag
only after that UI check. Operator confirmation is labeled as such; it is not
an independent account billing audit. Otherwise no physical probe runs.

The notebook checks CUDA access, CC >= 8.0, total VRAM >= 14 GiB and native
`is_bf16_supported(including_emulation=False)`. The companion receipt records
PyTorch/CUDA-runtime/driver versions and currently free GPU memory separately
from capacity. A T4 fails before any model loading. No BF16 emulation, FP16,
quantization or compute-kernel experiment is used. CUDA metadata queries may
initialize a CUDA context; this is not inference or a model-memory fit test.
Free VRAM is telemetry, not proof that the frozen model fits.

Receipts use a new directory and exclusive file creation. Download the result
ZIP before disconnecting the ephemeral runtime. Even hardware PASS authorizes
no inference: cohort, original checkers and matched executable arms are blocked.
Colab does not guarantee a GPU type or availability; its free policy alone does
not establish account eligibility ([official FAQ](https://research.google.com/colaboratory/faq.html)).

The current desktop's accessible application inventory exposed no Colab session.
No allocation, paid service or repeated local GPU diagnosis was attempted.
`GPU_QUALIFICATION.json` honestly records NOT_MEASURED rather than a simulated
physical PASS or a new hardware FAIL.

## Actual integration assessment

See `AM2_THREE_ARM_WIRING_20261019.md`. Reusable core and verification primitives
exist, but connecting PR #254's generic QA to the old AM1 runner is not sufficient:
that runner hardcodes the old 12 tasks, 36 observations, compact-JSON actions and
their original private checkers. The CP0 discriminator recognizes only three
specific public schemas. A generic final-answer ABI is neither a tool controller
nor an independently verified representation mechanism.

No eligible opened >=24-original / >=3-independent-origin manifest with licensed
source hashes, trusted full-original checkers and strong TOOL+ evidence was found
in the inspected preparation assets. The published 12 tasks are intentionally
excluded, not duplicated or renamed. No sealed source rows or new benchmark
dataset were fetched. The empty new cohort manifest means **zero admitted tasks
for this new preparation**, not a claim that the entire repository has no data.

## Prospective decision order

Gate0 requires free eligible hardware, frozen runtime identity, opened task
provenance, original-checker authority, credible nonsaturation, shared budgets
and complete accounting. It must NOT require measured Frontier Gap membership:
that belongs to EX2 after EX1, avoiding the dependency deadlock corrected in #253.

EX1's prospective Issue-253 development criterion is >=3 extra original successes
over strongest TOOL+ under the frozen shared budget, OR >=2x complete latency
AND compatible per-task cost improvement at equal capability, with relevant
ablations. No actual EX1 success/failure was measured here. Unknown costs are not
zero. Its exact executable cohort/tool/budget freeze is still missing; inherited
AM1 budget values are only a reuse reference, not authority to replay AM1.

Original Decision 3 stays sealed and unarmed. Its retained +2 / <=1.25x or equal
correctness / <=0.50x multiplier; G>=6 across>=3 families; >=50% recovery with
>=1 recovery in families having>=2 gap tasks; and >=2x one measured compatible
resource axis with no measured regression>1.25x are unchanged. The Issue body's
18/90%/10x ambitions cannot replace these historical gates. No marker is flipped.

## Actual execution and next action

Only new preparation code/receipt-boundary tests and notebook static checks were
run locally; their receipts and SHA-256 are in
`docs/experiments/results/am2_colab_preparation_20261019/`.
No previous 12-task/Q3/AM1 experiment was repeated. No model, GPU computation,
training, frontier/API query or package installation occurred. Additional paid
resource requests: 0; historical failures and unavailable metrics are retained.

**Next single action:** open the committed Colab notebook once in a confirmed
free runtime and retain the physical qualification receipt. If native BF16 is
unavailable, stop. If it qualifies, report those resources together with the still
missing cohort and arm bindings before any model run. Do not advance to EX2.
