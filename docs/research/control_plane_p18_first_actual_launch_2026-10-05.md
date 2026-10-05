# P1.8 first actual Kaggle launch

Date: 2026-10-05

This note is an operator surface only. It does **not** change the frozen P1.8 experiment, tasks, gates, model, runtime, or source hashes.

## Frozen identity

- tested P1.8 source head: `4e48320c2c67f15f8a41b0b4721caabd0c9b6df3`
- tested source tree: `2a48be262af2b3c83d80357320211d34d9f51b42`
- merged main after PR #152: `9b8e28d6e1d7bf31e2a1ab7c25628dd470257f49`
- merged tree: `2a48be262af2b3c83d80357320211d34d9f51b42`
- bootstrap: `scripts/control_plane_p18_kaggle.py`
- bootstrap SHA-256: `19de12d24316b7122720404f0c4252f1b2c1fa3f179958e28e597ac75c18a49c`
- registered accelerator: Tesla T4
- registered torch: `2.11.0+cu128`
- registered torchvision: `0.26.0+cu128`
- registered transformers: `5.16.1`

The tested PR head and merged main have the same tree. The first actual run intentionally checks out the exact tested head above.

## Before the one irreversible cell

In Kaggle, select **Tesla T4**, enable Internet, and ensure the account can fetch the frozen `google/gemma-4-E2B-it` revision. Start from a clean session whose `/kaggle/working` does not contain prior P1.8 first-attempt artifacts.

Do not launch the cell merely to test setup. The bootstrap creates the first-attempt receipt before runtime preflight. A setup failure is retained evidence and must not be replaced by a favorable rerun.

## First actual one-cell launcher

```python
import hashlib, json, os, runpy, time, urllib.request
from pathlib import Path

started = time.perf_counter()
working = Path("/kaggle/working")
if not working.is_dir():
    raise RuntimeError("Kaggle에서 실행해주세요.")

head = "4e48320c2c67f15f8a41b0b4721caabd0c9b6df3"
expected = "19de12d24316b7122720404f0c4252f1b2c1fa3f179958e28e597ac75c18a49c"
url = f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{head}/scripts/control_plane_p18_kaggle.py"

raw = urllib.request.urlopen(url, timeout=60).read()
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise RuntimeError(f"P1.8 bootstrap hash mismatch: {actual}")

path = working / "neumann_p18_bootstrap.py"
if path.exists():
    if path.read_bytes() != raw:
        raise RuntimeError("existing P1.8 bootstrap differs; do not overwrite")
else:
    with path.open("xb") as stream:
        stream.write(raw)

os.environ["NEUMANN_P18_FROZEN_HEAD"] = head
ns = runpy.run_path(str(path))

try:
    setup, archive = ns["run"](
        working,
        launcher_wall_ms=(time.perf_counter() - started) * 1000,
    )
    print(json.dumps({
        "status": setup.get("status"),
        "runner_exit_code": setup.get("runner_exit_code"),
        "replay_exit_code": setup.get("replay_exit_code"),
        "development_verdict": setup.get("development_verdict"),
        "archive": archive,
    }, ensure_ascii=False, indent=2))
finally:
    ns["display_archive"](working)
```

Expected terminal artifact:

`NEUMANN_P18_FIRST_EVIDENCE.zip`

Preserve it for PASS, FAIL, or INCOMPLETE. Do not delete it and do not create a replacement first result.

## Interrupted-session packaging only

This is **not a rerun**. Use it only if the original P1.8 bootstrap already started, its child process is no longer alive, and the evidence directory exists but the ZIP was never packaged.

```python
import hashlib, os, runpy, urllib.request
from pathlib import Path

working = Path("/kaggle/working")
head = "4e48320c2c67f15f8a41b0b4721caabd0c9b6df3"
expected = "19de12d24316b7122720404f0c4252f1b2c1fa3f179958e28e597ac75c18a49c"
url = f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{head}/scripts/control_plane_p18_kaggle.py"
raw = urllib.request.urlopen(url, timeout=60).read()
if hashlib.sha256(raw).hexdigest() != expected:
    raise RuntimeError("P1.8 bootstrap hash mismatch")

path = working / "neumann_p18_bootstrap.py"
if not path.exists() or path.read_bytes() != raw:
    raise RuntimeError("exact original P1.8 bootstrap required for recovery")

os.environ["NEUMANN_P18_FROZEN_HEAD"] = head
ns = runpy.run_path(str(path))
result = ns["package_existing"](working)
print(result)
ns["display_archive"](working)
```

## Frozen interpretation

The preregistered PASS gate remains unchanged:

- 8 observations exactly
- total accepted >= 7/8
- A = 4/4 accepted
- B >= 3/4 accepted
- A model calls / neural forwards = 0 / 0
- B model calls = 4
- B neural forwards = 144
- generation = 0
- feasibility calls = 24
- tool / original-verifier calls = 8 / 8
- selector <= 180 s
- item <= 240 s
- whole study <= 1800 s
- complete accounting and model-free replay

Even a PASS is only `OPENED_P18_A_B_DIAGNOSTIC_ONLY`. It does not admit P2 or Decision 3 and closes none of Q1-Q7.
