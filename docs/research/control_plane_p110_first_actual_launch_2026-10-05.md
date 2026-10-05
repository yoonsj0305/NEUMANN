# P1.10 first actual Kaggle launch

Date: 2026-10-05

Operator surface only. No frozen experiment/task/gate/model/runtime/source file is modified.

## Frozen identity

- CI-tested source head: `0c9b04954ffffe83051fcc2fcb675101717021ad`
- tested tree: `2c3ea1d8eb3fef15523d46228ea1c00367dfd44c`
- merge main after PR #161: `de785b8a76e29c1dc621781fcbba3c4daa0f2c45`
- merged tree: `2c3ea1d8eb3fef15523d46228ea1c00367dfd44c`
- bootstrap SHA-256: `8dffa777f716604365ac0c8d95da5d0bc437addda8edd46203f56a502c46c572`
- accelerator: Tesla T4
- torch: `2.11.0+cu128`
- torchvision: `0.26.0+cu128`
- transformers: `5.16.1`

## First actual one-cell launcher

```python
import hashlib, json, os, runpy, time, urllib.request
from pathlib import Path

started = time.perf_counter()
working = Path("/kaggle/working")
if not working.is_dir():
    raise RuntimeError("Kaggle에서 실행해주세요.")

head = "0c9b04954ffffe83051fcc2fcb675101717021ad"
expected = "8dffa777f716604365ac0c8d95da5d0bc437addda8edd46203f56a502c46c572"
url = f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{head}/scripts/control_plane_p110_kaggle.py"

raw = urllib.request.urlopen(url, timeout=60).read()
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise RuntimeError(f"P1.10 bootstrap hash mismatch: {actual}")

path = working / "neumann_p110_bootstrap.py"
if path.exists():
    if path.read_bytes() != raw:
        raise RuntimeError("existing P1.10 bootstrap differs; do not overwrite")
else:
    with path.open("xb") as stream:
        stream.write(raw)

os.environ["NEUMANN_P110_FROZEN_HEAD"] = head
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

Expected archive: `NEUMANN_P110_FIRST_EVIDENCE.zip`.

Preserve PASS, FAIL or INCOMPLETE. Never replace the first result.

## iPad / no-download copy-paste result cell

```python
import json
from pathlib import Path

working = Path("/kaggle/working")
result_dir = working / "neumann_p110_first"

def read_json(path):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

setup = read_json(working / "neumann_p110_first_setup.json")
report = read_json(result_dir / "report.json")
core = read_json(result_dir / "core.json")
terminal = read_json(result_dir / "terminal.json")
hash_receipt = read_json(working / "NEUMANN_P110_FIRST_EVIDENCE.sha256.json")

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
            "oriented_pairs": sr.get("oriented_pairs"),
        }
        passes = sr.get("passes")
        if isinstance(passes, list):
            out["selector_passes"] = [
                {
                    "mode": p.get("mode"),
                    "status": p.get("status"),
                    "batch_size": p.get("batch_size"),
                    "order": p.get("order"),
                    "actual": p.get("actual"),
                    "matrix": p.get("matrix"),
                    "peak_accelerator_memory_bytes": p.get("peak_accelerator_memory_bytes"),
                }
                for p in passes if isinstance(p, dict)
            ]
    tasks.append(out)

bundle = {
    "P110_COPY_PASTE_BUNDLE": True,
    "archive_identity": {
        "archive": "NEUMANN_P110_FIRST_EVIDENCE.zip",
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

print("===== BEGIN P1.10 COPY-PASTE RESULT =====")
print(json.dumps(bundle, ensure_ascii=False, indent=2, default=str))
print("===== END P1.10 COPY-PASTE RESULT =====")
```

## Frozen gate

- observations = 8
- accepted >= 6/8
- model calls = 8
- neural forwards = 16 exactly
- generation = 0
- feasibility calls = 23
- selector receipts complete = 8/8
- selector <= 60 s
- item <= 90 s
- study <= 900 s
- frozen identity unchanged
- model-free replay reproduces the decision

PASS remains opened-development only. P2, Decision3 and Q1-Q7 remain blocked/open.
