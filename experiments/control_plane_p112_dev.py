"""Exclusive first P1.12 opened-development runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path
import re
import resource
import subprocess
from time import perf_counter_ns
import traceback

from neumann1.control_plane_v1 import canonical, digest, snapshot
from neumann1.control_plane_p1_contract import manifest as p1_manifest
from neumann1.control_plane_p112 import MODEL, FrozenMiniLMCrossEncoder
from experiments.control_plane_p1_first import write_new
from experiments.control_plane_p112_registration import registration, GATE, BOUNDARY, ROOT
from experiments.control_plane_p112_runtime import run_item, evaluate, totals

REQUIRED_MODEL_FILES = (
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt",
)


def _file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_artifacts(model_dir, manifest):
    model_dir = Path(model_dir)
    if (
        type(manifest) is not dict
        or manifest.get("schema") != "neumann.control-plane-p112-model-artifacts.v1"
        or manifest.get("model_id") != MODEL["model_id"]
        or manifest.get("model_revision") != MODEL["model_revision"]
    ):
        raise ValueError("P1.12 model artifact manifest identity drift")
    files = manifest.get("files")
    if type(files) is not dict or set(files) != set(REQUIRED_MODEL_FILES):
        raise ValueError("P1.12 exact model artifact coverage required")
    if files["model.safetensors"].get("sha256") != "821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae":
        raise ValueError("P1.12 preregistered model.safetensors digest mismatch")
    for name in REQUIRED_MODEL_FILES:
        path = model_dir / name
        row = files[name]
        if (
            not path.is_file()
            or path.is_symlink()
            or type(row) is not dict
            or row.get("bytes") != path.stat().st_size
            or row.get("sha256") != _file_sha256(path)
        ):
            raise ValueError("P1.12 model artifact byte drift: " + name)
    return True


def core_identity(encoder, artifact_manifest, artifact_manifest_sha256):
    torch = encoder.torch
    dtypes = sorted({str(parameter.dtype) for parameter in encoder.model.parameters()})
    return {
        "schema": "neumann.control-plane-p112-core.v1",
        "model": snapshot(MODEL),
        "artifact_manifest_sha256": artifact_manifest_sha256,
        "artifact_files": snapshot(artifact_manifest["files"]),
        "device_type": encoder.device.type,
        "device_name": torch.cuda.get_device_name(encoder.device),
        "precision": dtypes,
        "weights_frozen": all(not parameter.requires_grad for parameter in encoder.model.parameters()),
        "model_training": bool(encoder.model.training),
        "parameters": sum(parameter.numel() for parameter in encoder.model.parameters()),
        "torch": version("torch"),
        "transformers": version("transformers"),
        "evidence_kind": "actual_frozen_semantic_microexecutor",
    }


def core_audit(encoder, identity, model_dir, artifact_manifest):
    torch = encoder.torch
    current = core_identity(
        encoder,
        artifact_manifest,
        identity["artifact_manifest_sha256"],
    )
    try:
        validate_artifacts(model_dir, artifact_manifest)
        artifact_unchanged = True
    except Exception:
        artifact_unchanged = False
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "unchanged": current == identity and artifact_unchanged,
        "after_identity": current,
        "artifact_unchanged": artifact_unchanged,
        "forward_calls": encoder.forward_calls,
        "current_accelerator_allocated_bytes": int(torch.cuda.memory_allocated(encoder.device)),
        "current_accelerator_reserved_bytes": int(torch.cuda.memory_reserved(encoder.device)),
        "max_accelerator_allocated_bytes": int(torch.cuda.max_memory_allocated(encoder.device)),
        "max_accelerator_reserved_bytes": int(torch.cuda.max_memory_reserved(encoder.device)),
        "peak_process_rss_bytes": int(rss) * 1024,
    }


def run(directory, frozen_head, model_dir, artifact_manifest_path):
    if not re.fullmatch(r"[0-9a-f]{40}", frozen_head):
        raise ValueError("exact frozen P1.12 source required")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    model_dir = Path(model_dir)
    artifact_manifest_path = Path(artifact_manifest_path)

    began = perf_counter_ns()
    elapsed = lambda: (perf_counter_ns() - began) / 1e6
    records = []
    refs = []
    error = None
    encoder = None
    identity = {}
    audit = {}
    startup_ms = None
    artifact_manifest = None

    write_new(directory / "study_started.json", {
        "schema": "neumann.control-plane-p1.11-development.v1",
        "frozen_head": frozen_head,
        "first_only": True,
        **BOUNDARY,
    })

    try:
        reg, rows, refs = registration()
        write_new(directory / "manifest.json", {
            "registration": reg,
            "public_rows": rows,
            "frozen_head": frozen_head,
        })

        if subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip() != frozen_head:
            raise ValueError("exact frozen P1.12 source commit required")
        subprocess.run(
            ["git", "diff", "--exit-code", "HEAD", "--"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )

        for package, expected in p1_manifest()["runtime"].items():
            if version(package) != expected:
                raise ValueError("original frozen runtime mismatch: " + package)

        artifact_manifest = json.loads(artifact_manifest_path.read_bytes())
        validate_artifacts(model_dir, artifact_manifest)
        artifact_manifest_sha256 = _file_sha256(artifact_manifest_path)

        import torch
        if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != "Tesla T4":
            raise ValueError("registered Tesla T4 required")
        torch.cuda.reset_peak_memory_stats(0)

        startup_started = perf_counter_ns()
        encoder = FrozenMiniLMCrossEncoder(
            device="cuda",
            model_source=model_dir,
            local_files_only=True,
        )
        startup_ms = (perf_counter_ns() - startup_started) / 1e6

        identity = core_identity(
            encoder, artifact_manifest, artifact_manifest_sha256
        )
        if (
            identity["device_type"] != "cuda"
            or identity["device_name"] != "Tesla T4"
            or identity["precision"] != ["torch.float32"]
            or identity["weights_frozen"] is not True
            or identity["model_training"] is not False
            or identity["parameters"] != MODEL["expected_parameters"]
        ):
            raise ValueError("P1.12 frozen core identity drift")
        write_new(directory / "core.json", identity)

        for index, (row, ref) in enumerate(zip(rows, refs)):
            write_new(directory / ("task_%02d_started.json" % index), {
                "task_id": row["task_id"],
                "view_sha256": digest(row["view"]),
            })
            record = run_item(row, ref, encoder)
            records.append(record)
            write_new(directory / ("task_%02d.json" % index), record)
            print(canonical({
                "task_id": record["task_id"],
                "status": record["status"],
                "accepted": record["accepted"],
                "selected_candidate": record.get("selected_candidate"),
                "raw_top_candidate": record.get("raw_top_candidate"),
                "forward_calls": record.get("neural_forward_calls"),
                "input_tokens": record.get("input_tokens"),
            }), flush=True)
            if elapsed() > GATE["whole_study_wall_ms"]:
                raise TimeoutError("P1.12 complete study deadline")

        audit = core_audit(
            encoder, identity, model_dir, artifact_manifest
        )
    except Exception as exc:
        error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }

    if encoder is not None and not audit:
        try:
            audit = core_audit(
                encoder, identity, model_dir, artifact_manifest
            )
        except Exception as exc:
            audit = {"unchanged": False, "error": str(exc)}

    complete = error is None and len(records) == GATE["observations_exact"]
    whole = elapsed()
    decision = evaluate(
        records,
        refs if complete else [],
        audit.get("unchanged"),
        complete,
        whole,
    )
    report = {
        "schema": "neumann.control-plane-p1.11-development.v1",
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "decision": decision,
        "source_head": frozen_head,
        "observations": len(records),
        "whole_study_ms": whole,
        "selector_startup_ms": startup_ms,
        "core_audit": audit,
        "accounting_complete": complete and all(
            record.get("accounting_complete") is True for record in records
        ),
        "cost_totals": totals(records),
        "fallback_calls": 0,
        "frontier_calls": 0,
        "generated_calls": 0,
        "new_training": False,
        "sealed_data_opened": False,
        "historical_score_reuse": False,
        "p111_task_score_reuse": False,
        "p111_tasks_as_p112_evidence": False,
        **BOUNDARY,
        "error": error,
        "energy_j": None,
        "flops": None,
        "cost_money": None,
        "timing_scope": (
            "whole study includes registration/source/runtime checks, local frozen-model "
            "load, tokenization, one-batch joint cross-encoder scoring, joint cross-encoder logits, selection, "
            "deterministic compilation, cached specialist execution, original verification "
            "and final audit; excludes bootstrap clone/dependency install/model download/"
            "artifact hashing/final serialization/packaging/replay"
        ),
    }
    write_new(directory / "report.json", report)
    pins = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.glob("*.json"))
    }
    write_new(directory / "terminal.json", {
        "files": pins,
        "complete": complete,
        "no_replacement": True,
        "decision": decision["verdict"],
        **BOUNDARY,
    })
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--frozen-head", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--artifact-manifest", required=True)
    args = parser.parse_args()
    result = run(
        args.directory,
        args.frozen_head,
        args.model_dir,
        args.artifact_manifest,
    )
    print(canonical(result))
    raise SystemExit(0 if result["decision"]["verdict"] == "PASS" else 2)
