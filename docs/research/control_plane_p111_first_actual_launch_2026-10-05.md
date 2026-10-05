# P1.11 first actual Kaggle launch

Date: 2026-10-05

Operator surface only. This note does not modify the frozen P1.11 experiment,
tasks, gates, model, runtime or source.

## Frozen identity

- CI-tested source head: `8094b4ea90fc48f4d3c0d8142ff378dbe73afc59`
- tested tree: `e356ea6d1d7c2bc54002f4b3235f236f40659cc8`
- merge main after PR #167: `d5ad6d9e2f53d8bec27a269406cc756df4b8f947`
- merged tree: `e356ea6d1d7c2bc54002f4b3235f236f40659cc8`
- bootstrap: `scripts/control_plane_p111_kaggle.py`
- bootstrap SHA-256: `07d3f606ba9fe5beb9c79f4181e1525731a2699e9b77b361042158794ca120de`
- model: `sentence-transformers/all-MiniLM-L6-v2`
- model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- registered accelerator: Tesla T4
- registered precision: float32
- registered torch: `2.11.0+cu128`
- registered torchvision: `0.26.0+cu128`
- registered transformers: `5.16.1`

The tested PR head and merged main have the same Git tree. The first actual run
intentionally checks out the exact CI-tested head.

## Before the irreversible cell

In Kaggle:

1. choose **Tesla T4**,
2. enable Internet,
3. use a clean session whose `/kaggle/working` has no P1.11 first-attempt files,
4. do not use the first-attempt cell as a setup test.

The bootstrap preserves setup/runtime failures as first evidence. It downloads
only the exact-revision registered model/tokenizer files before the timed study,
records byte size + SHA-256 for each artifact, and the study then loads only from
that local snapshot.

## First actual one-cell launcher

```python
import hashlib, json, os, runpy, time, urllib.request
from pathlib import Path

started = time.perf_counter()
working = Path("/kaggle/working")

if not working.is_dir():
    raise RuntimeError("Kaggle에서 실행해주세요.")

head = "8094b4ea90fc48f4d3c0d8142ff378dbe73afc59"
expected = "07d3f606ba9fe5beb9c79f4181e1525731a2699e9b77b361042158794ca120de"

url = (
    "https://raw.githubusercontent.com/"
    f"yoonsj0305/NEUMANN/{head}/scripts/control_plane_p111_kaggle.py"
)

raw = urllib.request.urlopen(url, timeout=60).read()
actual = hashlib.sha256(raw).hexdigest()

if actual != expected:
    raise RuntimeError(
        "P1.11 bootstrap hash mismatch\n"
        f"expected: {expected}\n"
        f"actual:   {actual}"
    )

path = working / "neumann_p111_bootstrap.py"

if path.exists():
    if path.read_bytes() != raw:
        raise RuntimeError(
            "Existing P1.11 bootstrap differs. "
            "Do not overwrite the first-attempt environment."
        )
else:
    with path.open("xb") as stream:
        stream.write(raw)

os.environ["NEUMANN_P111_FROZEN_HEAD"] = head
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

`NEUMANN_P111_FIRST_EVIDENCE.zip`

Preserve PASS, FAIL or INCOMPLETE. Never replace the first result.

## iPad / no-download copy-paste result cell

This cell is read-only. It performs no model inference, no rerun and no evidence mutation.

```python
import json
from pathlib import Path

working = Path("/kaggle/working")
result_dir = working / "neumann_p111_first"

def read_json(path):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

setup = read_json(working / "neumann_p111_first_setup.json")
report = read_json(result_dir / "report.json")
core = read_json(result_dir / "core.json")
terminal = read_json(result_dir / "terminal.json")
artifact_manifest = read_json(working / "neumann_p111_model_artifacts.json")
hash_receipt = read_json(
    working / "NEUMANN_P111_FIRST_EVIDENCE.sha256.json"
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

    out = {
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
        "feasibility_nodes": rec.get("feasibility_nodes"),
        "feasibility_constraint_checks":
            rec.get("feasibility_constraint_checks"),
        "tool_calls": rec.get("tool_calls"),
        "verifier_calls": rec.get("verifier_calls"),
        "witness_cache_hits": rec.get("witness_cache_hits"),
        "accounting_complete": rec.get("accounting_complete"),
        "selector_complete": rec.get("selector_complete"),
        "extraction_ms": rec.get("extraction_ms"),
        "feasibility_ms": rec.get("feasibility_ms"),
        "ir_ms": rec.get("ir_ms"),
        "lexical_ms": rec.get("lexical_ms"),
        "selection_ms": rec.get("selection_ms"),
        "compile_ms": rec.get("compile_ms"),
        "routing_ms": rec.get("routing_ms"),
        "execution_ms": rec.get("execution_ms"),
        "verification_ms": rec.get("verification_ms"),
        "complete_ms": rec.get("complete_ms"),
        "execution": rec.get("execution"),
        "error": rec.get("error"),
    }

    sr = rec.get("selector_receipt")
    if isinstance(sr, dict):
        out["selector_receipt_summary"] = {
            "status": sr.get("status"),
            "semantic_ir_sha256": sr.get("semantic_ir_sha256"),
            "similarities": sr.get("similarities"),
            "forward_calls": sr.get("forward_calls"),
            "input_rows": sr.get("input_rows"),
            "input_tokens": sr.get("input_tokens"),
            "padded_tokens": sr.get("padded_tokens"),
            "tokenize_ms": sr.get("tokenize_ms"),
            "forward_ms": sr.get("forward_ms"),
            "pooling_similarity_ms": sr.get("pooling_similarity_ms"),
            "device": sr.get("device"),
            "complete_ms": sr.get("complete_ms"),
        }

    partial = rec.get("selector_partial_receipt")
    if isinstance(partial, dict):
        out["selector_partial_receipt"] = partial

    tasks.append(out)

bundle = {
    "P111_COPY_PASTE_BUNDLE": True,
    "archive_identity": {
        "archive": "NEUMANN_P111_FIRST_EVIDENCE.zip",
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
        "complete": (
            terminal.get("complete")
            if isinstance(terminal, dict)
            else None
        ),
        "decision": (
            terminal.get("decision")
            if isinstance(terminal, dict)
            else None
        ),
        "no_replacement": (
            terminal.get("no_replacement")
            if isinstance(terminal, dict)
            else None
        ),
        "terminal_file_count": (
            len(terminal.get("files", {}))
            if isinstance(terminal, dict)
            else None
        ),
    },
}

print("===== BEGIN P1.11 COPY-PASTE RESULT =====")
print(json.dumps(
    bundle,
    ensure_ascii=False,
    indent=2,
    default=str,
))
print("===== END P1.11 COPY-PASTE RESULT =====")
```

## Frozen interpretation

PASS requires all integrity/accounting/timing gates plus:

- exactly 12 observations
- accepted >= 9/12
- exactly 12 model calls
- exactly 12 neural forwards
- generated calls = 0
- feasibility calls = 35
- selector receipts complete = 12/12
- lexical-overlap unique selections = 0
- selector wall <= 10 s per item
- complete item wall <= 15 s
- whole study <= 240 s
- exact frozen model identity unchanged
- local artifact files unchanged
- model-free replay reproduces the terminal decision

A PASS is only `OPENED_P111_MICROEXECUTOR_DIAGNOSTIC_ONLY`.
It does not register fresh validation, admit P2 or Decision3, close Q1-Q7, or
establish overwhelming/category-changing advantage.

Energy, FLOPs and money remain UNKNOWN unless actually measured.
