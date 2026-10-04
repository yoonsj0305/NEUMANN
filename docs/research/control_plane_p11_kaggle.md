# P1.1 first development — frozen Kaggle bootstrap

This publishes an execution interface, not a Gemma result. Real P1.1 is still
NOT RUN. The original twelve P1 views remain DEVELOPMENT ONLY. Development
PASS does not admit P2 or Decision 3; fresh validation is still unregistered.

## Two independent source pins

The experiment checkout is **always** PR134 merged commit
`4e6db9926a27c94f63c8d539d0c6e57c34b49336` (tree
`9edde3693e0effbbff3a8678c9351d8e1459192b`). Its architecture, model identity,
runtime, eight maps, code audit and diagnostic thresholds are unchanged.
The bootstrap has its own immutable GitHub commit published with the final
launch cell; its SHA256 is in `docs/experiments/control_plane_p11_bootstrap.freeze.json`. The final launch
cell must use that published bootstrap commit, never `main` or a branch URL.
Verify the downloaded bootstrap bytes against the frozen SHA256 before
executing them. Separating these two pins avoids a self-referential commit hash.

## Kaggle interface

Use a Tesla T4 notebook with Internet enabled. Keep the registered existing
CUDA packages: Torch `2.11.0+cu128` and torchvision `0.26.0+cu128`. A child
interpreter checks these before any download and again after dependency setup.
Pip constraints prohibit substituting those packages; the bootstrap never
installs a different Torch, CUDA stack, model, revision or quantization.
Transformers remains `5.16.1`. No credentials are requested or printed by the
bootstrap. The retained core uses its original access path and identity audit.

The published notebook cell downloads and checks the bootstrap, loads its
definitions with `runpy.run_path`, calls `run(launcher_wall_ms=...)` exactly once, then calls
`display_archive(Path('/kaggle/working'))` in the notebook process. Importing
the script does not execute an experiment; do not use `run_name='__main__'`
inside a notebook because kernel arguments are not bootstrap CLI arguments.
No additional task/model/directory arguments are accepted by the launch cell.

Stages: CUDA preflight, pinned checkout, constrained dependencies, fresh-process
preflight and package inventory, source registration, first P1.1 development,
independent model-free replay, exclusive evidence archive. Each subprocess
has a retained exit/status/wall-ms receipt. Runner non-PASS is replayed and
preserved. A missing terminal, replay error or development/admission mismatch
fails closed. Timeout and keyboard interruption terminate and reap the owned
process group before packaging; there is no automatic retry or fallback.

Operational timeout caps in seconds: preflight60, clone180, checkout60,
dependency installation600, second preflight60, package inventory60,
registration60, runner2700, replay60. These are abort limits, not runtime
estimates. Runner's registered study/controller/token limits are unchanged.
The launch cell measures bootstrap download/hash/loading wall time in ms and
passes it as accounting metadata (not a model or budget setting). Bootstrap
setup+runner wall time, the launcher+setup+runner sum and per-stage wall times are reported
separately from the original study cost; archive packaging time is in the
hash receipt. Do not count the wrapper as free or mistake timeout limits for
measured latency. Energy, FLOPs and monetary cost stay UNKNOWN.

## Preserve the first attempt

An exclusive `neumann_p11_first_setup.json` reservation is written before
dependency changes or downloads. Any prior setup, output, checkout, archive,
hash receipt, log, replay output or constraints blocks execution. This is a
notebook-filesystem guard; it cannot prevent manual deletion or a different
session. Never delete the directory/reset the session to replace an outcome.
Retain a failed setup attempt too; any repair requires an explicit separately
registered decision after inspecting the original evidence.

The archive is `NEUMANN_P11_FIRST_EVIDENCE.zip`. It includes the original
bootstrap bytes, setup receipt, package/runtime log, constraints, replay stdout
and all available development files. `archive_manifest.json` records exact
member sizes and SHA256 values. The separate
`NEUMANN_P11_FIRST_EVIDENCE.sha256.json` records the whole archive hash, byte
count and packaging duration. Neither archive nor receipt can be overwritten.
These file hashes establish integrity, not real inference or capability.

Download the ZIP through the notebook link or Kaggle Output panel. The link
uses `/files/NEUMANN_P11_FIRST_EVIDENCE.zip`, avoiding an absolute local
`/kaggle/working` URL. Upload the original ZIP without editing its members.
If the kernel is forcibly stopped before packaging, preserve partial files.
The **same byte-verified bootstrap** has `--package-existing` for evidence-only
recovery; it blocks while a recorded child PID exists and never starts scoring,
installs packages or changes original receipts. Missing timings/work remain
UNKNOWN. Use it only for a previously started attempt, never to rerun inference.

## Readiness and next gate

CI executes only model-free orchestration/failure/timeout/archive fixtures.
The unchanged P1.1 contracts and real frozen tokenizer readiness are also
checked, with no model weights, task scoring or GPU study. Synthetic PASS
does not supply a real development observation.

After the first actual development attempt, preserve and independently replay
its uploaded archive before evaluating the diagnostic gate. Only development
PASS permits architecture freeze and fresh opened-validation registration,
with task-source/deduplication/checker/cost pins frozen before seeing scores.
Fresh validation PASS precedes P2 registration; Decision 3 stays blocked until
P2 and the generic-interface requirement pass. Q1–Q7 remain globally OPEN.
