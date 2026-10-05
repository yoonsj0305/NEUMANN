# P1.11.1 first evaluable Kaggle launch

Date: 2026-10-05

Operator surface only. P1.11 historical first actual remains immutable
NOT_EVALUATED. This note launches the separately named P1.11.1 identity-repair
attempt and does not replace the historical archive.

## Frozen identity

- historical first archive SHA-256: `d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0`
- historical observations/model calls/neural forwards: `0 / 0 / 0`
- historical error: `P1.11 frozen model parameter-count drift`
- P1.11.1 CI-tested source head: `9dcb96a2c1e303c2178776ba9ab8b66eee53913b`
- tested tree: `ce943360e46b0ebd481ba8caad046ff0bc603aaa`
- PR #170 merge main: `5ff5445a530f87f4e611d34e99ee334b7abfb538`
- merged tree: `ce943360e46b0ebd481ba8caad046ff0bc603aaa`
- repair bootstrap: `scripts/control_plane_p1111_kaggle.py`
- repair bootstrap SHA-256: `fb81110e363662a47fe6489599a945d2adb3441a89d8d40fdee4ce5c62acfd7d`
- model: `sentence-transformers/all-MiniLM-L6-v2`
- model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- AutoModel parameters: `22,713,216`
- total artifact/state elements: `22,713,728`
- non-parameter I64 state elements: `512`
- device: Tesla T4 / CUDA
- precision: float32

The task set, private references, runtime gate and semantic registry are byte-for-byte
unchanged from the historical preregistration. P1.11.1 changes model identity
accounting and provenance/namespace only.

## First evaluable one-cell launcher

Use a clean Kaggle session with Tesla T4 and Internet ON.

```python
import hashlib, json, os, runpy, time, urllib.request
from pathlib import Path

started = time.perf_counter()
working = Path("/kaggle/working")

if not working.is_dir():
    raise RuntimeError("Kaggle에서 실행해주세요.")

head = "9dcb96a2c1e303c2178776ba9ab8b66eee53913b"
expected = "fb81110e363662a47fe6489599a945d2adb3441a89d8d40fdee4ce5c62acfd7d"

url = (
    "https://raw.githubusercontent.com/"
    f"yoonsj0305/NEUMANN/{head}/scripts/control_plane_p1111_kaggle.py"
)

raw = urllib.request.urlopen(url, timeout=60).read()
actual = hashlib.sha256(raw).hexdigest()

if actual != expected:
    raise RuntimeError(
        "P1.11.1 bootstrap hash mismatch\n"
        f"expected: {expected}\n"
        f"actual:   {actual}"
    )

path = working / "neumann_p1111_bootstrap.py"

if path.exists():
    if path.read_bytes() != raw:
        raise RuntimeError(
            "Existing P1.11.1 bootstrap differs. "
            "Do not overwrite the repair-attempt environment."
        )
else:
    with path.open("xb") as stream:
        stream.write(raw)

os.environ["NEUMANN_P1111_FROZEN_HEAD"] = head
ns = runpy.run_path(str(path))

try:
    setup, archive = ns["run"](
        working,
        launcher_wall_ms=(time.perf_counter() - started) * 1000,
    )

    print(json.dumps(
        {
            "status": setup.get("status"),
            "runner_exit_code": setup.get("runner_exit_code"),
            "replay_exit_code": setup.get("replay_exit_code"),
            "development_verdict": setup.get("development_verdict"),
            "identity_repair_revision": setup.get("identity_repair_revision"),
            "historical_first_archive_sha256":
                setup.get("historical_first_archive_sha256"),
            "model_artifact_manifest_sha256":
                setup.get("model_artifact_manifest_sha256"),
            "archive": archive,
        },
        ensure_ascii=False,
        indent=2,
    ))
finally:
    ns["display_archive"](working)
```

Expected immutable archive:

`NEUMANN_P1111_FIRST_EVIDENCE.zip`

This archive is separate from `NEUMANN_P111_FIRST_EVIDENCE.zip`.
Preserve PASS, FAIL or INCOMPLETE. Never replace either result.

## Read-only copy-paste result cell

```python
import json
from pathlib import Path

working = Path("/kaggle/working")
result_dir = working / "neumann_p1111_first"

def read_json(path):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

setup = read_json(working / "neumann_p1111_first_setup.json")
report = read_json(result_dir / "report.json")
core = read_json(result_dir / "core.json")
terminal = read_json(result_dir / "terminal.json")
artifact_manifest = read_json(
    working / "neumann_p1111_model_artifacts.json"
)
hash_receipt = read_json(
    working / "NEUMANN_P1111_FIRST_EVIDENCE.sha256.json"
)

tasks = []
for i in range(12):
    rec = read_json(result_dir / f"task_{i:02d}.json")
    if rec is None:
        tasks.append({
            "index": i,
            "started": (result_dir / f"task_{i:02d}_started.json").exists(),
            "completed": False,
        })
        continue

    sr = rec.get("selector_receipt")
    tasks.append({
        "index": i,
        "started": True,
        "completed": True,
        "task_id": rec.get("task_id"),
        "status": rec.get("status"),
        "accepted": rec.get("accepted"),
        "executed": rec.get("executed"),
        "selected_candidate": rec.get("selected_candidate"),
        "raw_top_candidate": rec.get("raw_top_candidate"),
        "eligible_indexes": rec.get("eligible_indexes"),
        "selection": rec.get("selection"),
        "selection_error": rec.get("selection_error"),
        "semantic_ir": rec.get("semantic_ir"),
        "candidate_entities": rec.get("candidate_entities"),
        "lexical_baseline": rec.get("lexical_baseline"),
        "selector_decision": rec.get("selector_decision"),
        "model_calls": rec.get("model_calls"),
        "neural_forward_calls": rec.get("neural_forward_calls"),
        "generated_calls": rec.get("generated_calls"),
        "input_rows": rec.get("input_rows"),
        "input_tokens": rec.get("input_tokens"),
        "padded_tokens": rec.get("padded_tokens"),
        "feasibility_calls": rec.get("feasibility_calls"),
        "tool_calls": rec.get("tool_calls"),
        "verifier_calls": rec.get("verifier_calls"),
        "accounting_complete": rec.get("accounting_complete"),
        "selector_complete": rec.get("selector_complete"),
        "complete_ms": rec.get("complete_ms"),
        "execution": rec.get("execution"),
        "error": rec.get("error"),
        "selector_receipt_summary": (
            {
                "status": sr.get("status"),
                "similarities": sr.get("similarities"),
                "forward_calls": sr.get("forward_calls"),
                "input_rows": sr.get("input_rows"),
                "input_tokens": sr.get("input_tokens"),
                "padded_tokens": sr.get("padded_tokens"),
                "tokenize_ms": sr.get("tokenize_ms"),
                "forward_ms": sr.get("forward_ms"),
                "pooling_similarity_ms": sr.get("pooling_similarity_ms"),
                "complete_ms": sr.get("complete_ms"),
            }
            if isinstance(sr, dict)
            else None
        ),
        "selector_partial_receipt": rec.get("selector_partial_receipt"),
    })

bundle = {
    "P1111_COPY_PASTE_BUNDLE": True,
    "historical_first": {
        "archive_sha256":
            "d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0",
        "verdict": "NOT_EVALUATED",
        "observations": 0,
        "model_calls": 0,
        "neural_forward_calls": 0,
    },
    "archive_identity": {
        "archive": "NEUMANN_P1111_FIRST_EVIDENCE.zip",
        "archive_sha256": (
            hash_receipt.get("archive_sha256")
            if isinstance(hash_receipt, dict)
            else None
        ),
        "archive_bytes": (
            hash_receipt.get("archive_bytes")
            if isinstance(hash_receipt, dict)
            else None
        ),
    },
    "setup": setup,
    "model_artifacts": artifact_manifest,
    "report": report,
    "tasks": tasks,
    "core": core,
    "terminal_summary": {
        "complete": terminal.get("complete") if isinstance(terminal, dict) else None,
        "decision": terminal.get("decision") if isinstance(terminal, dict) else None,
        "no_replacement": terminal.get("no_replacement") if isinstance(terminal, dict) else None,
    },
}

print("===== BEGIN P1.11.1 COPY-PASTE RESULT =====")
print(json.dumps(bundle, ensure_ascii=False, indent=2, default=str))
print("===== END P1.11.1 COPY-PASTE RESULT =====")
```

## Frozen gate

Unchanged from P1.11:

- observations = 12
- accepted >= 9/12
- model calls = 12
- neural forwards = 12
- generation = 0
- feasibility calls = 35
- selector complete = 12/12
- lexical unique selections = 0
- selector <= 10 s/item
- item <= 15 s
- whole study <= 240 s
- exact model/artifact identity unchanged
- model-free replay reproduces the terminal decision

A PASS remains `OPENED_P111_MICROEXECUTOR_DIAGNOSTIC_ONLY`.
It does not register fresh validation, admit P2/Decision3, close Q1-Q7, or
establish overwhelming/category-changing advantage.
