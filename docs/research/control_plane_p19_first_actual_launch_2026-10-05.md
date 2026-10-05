# P1.9 first actual Kaggle launch

Date: 2026-10-05

Operator surface only. This note does not modify the frozen P1.9 experiment, tasks, gates, model, runtime or source.

## Frozen identity

- CI-tested P1.9 source head: `d5811f44a018e86660769ba9bebb542168ee97fd`
- tested source tree: `a16c98cc71a7027ae0e2de54eaf18a3f095b3654`
- merge main after PR #157: `c8ef8089b140875acb93ecc2374b460e4488894d`
- merged tree: `a16c98cc71a7027ae0e2de54eaf18a3f095b3654`
- bootstrap: `scripts/control_plane_p19_kaggle.py`
- bootstrap SHA-256: `a37e29f91a98d183e3f6906fd53643096eab2baae4a7bb5af034c3f1c8ee36a6`
- registered accelerator: Tesla T4
- registered torch: `2.11.0+cu128`
- registered torchvision: `0.26.0+cu128`
- registered transformers: `5.16.1`

The tested PR head and merged main have the same Git tree. The first actual run intentionally checks out the exact CI-tested head.

## Before the irreversible cell

In Kaggle, choose **Tesla T4**, enable Internet, and ensure the account can fetch the frozen `google/gemma-4-E2B-it` revision. Use a clean session whose `/kaggle/working` does not contain prior P1.9 first-attempt artifacts.

Do not use the first-attempt cell as a setup test. The bootstrap retains setup/runtime failures as first evidence.

## First actual one-cell launcher

```python
import hashlib, json, os, runpy, time, urllib.request
from pathlib import Path

started = time.perf_counter()
working = Path("/kaggle/working")
if not working.is_dir():
    raise RuntimeError("Kaggle에서 실행해주세요.")

head = "d5811f44a018e86660769ba9bebb542168ee97fd"
expected = "a37e29f91a98d183e3f6906fd53643096eab2baae4a7bb5af034c3f1c8ee36a6"
url = f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{head}/scripts/control_plane_p19_kaggle.py"

raw = urllib.request.urlopen(url, timeout=60).read()
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise RuntimeError(f"P1.9 bootstrap hash mismatch: {actual}")

path = working / "neumann_p19_bootstrap.py"
if path.exists():
    if path.read_bytes() != raw:
        raise RuntimeError("existing P1.9 bootstrap differs; do not overwrite")
else:
    with path.open("xb") as stream:
        stream.write(raw)

os.environ["NEUMANN_P19_FROZEN_HEAD"] = head
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

Expected immutable archive:

`NEUMANN_P19_FIRST_EVIDENCE.zip`

Preserve PASS, FAIL or INCOMPLETE. Never replace the first result.

## iPad / no-download copy-paste result cell

This cell is read-only. It performs no model inference, no rerun and no evidence mutation.

```python
import json
from pathlib import Path

working = Path("/kaggle/working")
result_dir = working / "neumann_p19_first"

def read_json(path):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

setup = read_json(working / "neumann_p19_first_setup.json")
report = read_json(result_dir / "report.json")
core = read_json(result_dir / "core.json")
terminal = read_json(result_dir / "terminal.json")
hash_receipt = read_json(working / "NEUMANN_P19_FIRST_EVIDENCE.sha256.json")

tasks = []
for i in range(8):
    rec = read_json(result_dir / f"task_{i:02d}.json")
    if rec is None:
        tasks.append({"index": i, "missing": True})
        continue

    out = {
        "index": i,
        "task_id": rec.get("task_id"),
        "status": rec.get("status"),
        "accepted": rec.get("accepted"),
        "executed": rec.get("executed"),
        "selected_candidate": rec.get("selected_candidate"),
        "eligible_indexes": rec.get("eligible_indexes"),
        "selection": rec.get("selection"),
        "selection_error": rec.get("selection_error"),
        "model_calls": rec.get("model_calls"),
        "neural_forward_calls": rec.get("neural_forward_calls"),
        "generated_calls": rec.get("generated_calls"),
        "evaluated_tokens": rec.get("evaluated_tokens"),
        "padded_tokens": rec.get("padded_tokens"),
        "feasibility_calls": rec.get("feasibility_calls"),
        "feasibility_nodes": rec.get("feasibility_nodes"),
        "feasibility_constraint_checks": rec.get("feasibility_constraint_checks"),
        "tool_calls": rec.get("tool_calls"),
        "verifier_calls": rec.get("verifier_calls"),
        "witness_cache_hits": rec.get("witness_cache_hits"),
        "accounting_complete": rec.get("accounting_complete"),
        "selector_complete": rec.get("selector_complete"),
        "selector_decision": rec.get("selector_decision"),
        "complete_ms": rec.get("complete_ms"),
        "error": rec.get("error"),
        "execution": rec.get("execution"),
    }

    sr = rec.get("selector_receipt")
    if isinstance(sr, dict):
        out["selector_receipt_summary"] = {
            "status": sr.get("status"),
            "complete_ms": sr.get("complete_ms"),
            "generated_calls": sr.get("generated_calls"),
            "ledger": sr.get("ledger"),
            "error": sr.get("error"),
        }

    tasks.append(out)

bundle = {
    "P19_COPY_PASTE_BUNDLE": True,
    "archive_identity": {
        "archive": "NEUMANN_P19_FIRST_EVIDENCE.zip",
        "archive_sha256": hash_receipt.get("archive_sha256") if isinstance(hash_receipt, dict) else None,
        "archive_bytes": hash_receipt.get("archive_bytes") if isinstance(hash_receipt, dict) else None,
    },
    "setup": setup,
    "report": report,
    "tasks": tasks,
    "core": core,
    "terminal_summary": {
        "complete": terminal.get("complete") if isinstance(terminal, dict) else None,
        "decision": terminal.get("decision") if isinstance(terminal, dict) else None,
        "no_replacement": terminal.get("no_replacement") if isinstance(terminal, dict) else None,
    },
}

print("===== BEGIN P1.9 COPY-PASTE RESULT =====")
print(json.dumps(bundle, ensure_ascii=False, indent=2, default=str))
print("===== END P1.9 COPY-PASTE RESULT =====")
```

## Frozen interpretation

PASS requires all integrity/accounting/timing gates plus:

- exactly 8 observations
- accepted >= 6/8
- exactly 8 model calls
- exactly 39 neural forwards
- generation = 0
- feasibility calls = 23
- all 8 selector receipts complete
- selector wall <= 60 s
- item wall <= 90 s
- whole study <= 900 s
- frozen model identity unchanged
- model-free replay reproduces the decision

A PASS is only `OPENED_P19_PROPOSITION_DIAGNOSTIC_ONLY`. It does not register P2, admit Decision 3, or close Q1-Q7.
