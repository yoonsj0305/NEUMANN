"""D0 allowlisted control/archive availability and rights audit; no inference.

Missing archives are excluded, never reconstructed from reported scores. No
pickle loading, historical source execution, model import or sealed traversal.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent.parent
HEAD = "a0119180e743f5115b21847fdb6ac6741f97bbe2"
GIT = r"C:\Users\Seojun\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
PINS = {
    "P1.1": ("docs/experiments/results/control_plane_p11_first.zip.b64", "6bdc2cc9435cefd8a3e99d1d0bc3589bd3b6ad84e50be83db877b1dde769e3ec"),
    "P1.2": ("docs/experiments/results/control_plane_p12_first.zip.b64", "b27748d76b8abdba24ab11ad85f25eb4012c8c9593a12a83590bfbf8666c98ba"),
    "P1.12": ("../../Continuation/P112_FIRST/NEUMANN_P112_FIRST_EVIDENCE.zip", "12340a660320df390313aaa572542c30f993b0f46aeee92d2ed727021b1118ac"),
    "P1.13": ("../../Continuation/P113_FIRST/NEUMANN_P113_FIRST_EVIDENCE.zip", "265c4bc939ce0cade72b97a29f79f40b9f8afef3b56cd49a440aa873d88c4f2a"),
    "REUSE_R0": ("../../Continuation/REUSE_R0_FIRST/NEUMANN_REUSE_R0_FIRST_EVIDENCE.zip", "8c99a04f92ebc5d75857a823ba3d44a009f3fc069f5d533a612204bea2dc8e92"),
    "CODE_GATE_C0": ("../../Continuation/CODE_GATE_C0_FIRST/NEUMANN_CODE_GATE_C0_FIRST_EVIDENCE.zip", "a137b6d0b3b9c99d709623763fcca1c3470a1cf596b075d69ddbd3ba2868cf1c"),
    "CODE_CACHE_C0": ("../../Continuation/CODE_CACHE_C0_FIRST/NEUMANN_CODE_CACHE_C0_FIRST_EVIDENCE.zip", "06d9bc4fcaf2b8663ba0a4d8c66f20ffb981d5fc9f42a588740415ef0c39b326"),
}
# Metadata only; these first ZIPs are absent from this checkout/workspace.
MISSING = {
    "P1.2-validation": ("control_plane_p12_validation_first_result_2026-10-04.json", "COMPLETE / FAIL"),
    "P1.3": ("control_plane_p13.md", "IMPLEMENTATION; ACTUAL ARCHIVE UNAVAILABLE"),
    "P1.4": ("control_plane_p14_first_result_2026-10-04.json", "COMPLETE / FAIL / RAW_ACCOUNTING_INCOMPLETE"),
    "P1.5": ("control_plane_p15_first_result_2026-10-04.json", "COMPLETE / FAIL"),
    "P1.6": ("control_plane_p16_first_result_2026-10-04.json", "COMPLETE / FAIL"),
    "P1.7": ("control_plane_p17_first_result_2026-10-05.json", "COMPLETE / FAIL / TASK_WALL_CAP"),
    "P1.8": ("control_plane_p18_first_result_2026-10-05.md", "COMPLETE / FAIL"),
    "P1.9": ("control_plane_p19_first_result_2026-10-05.md", "COMPLETE / FAIL"),
    "P1.10": ("control_plane_p110_first_interrupted_2026-10-05.md", "INCOMPLETE; NOT A TERMINAL FAIL"),
    "P1.11": ("control_plane_p111_first_nonevaluated_2026-10-05.md", "NOT_EVALUATED / IDENTITY_ERROR"),
    "P1.11.1": ("control_plane_p1111_first_fail_2026-10-05.md", "COMPLETE / FAIL / P111_SEMANTIC_CAPABILITY_FAILURE"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_zip(raw, expected_sha):
    if sha(raw) != expected_sha:
        raise ValueError("Externally recorded ZIP identity mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        names = [x.filename for x in entries]
        if len(set(names)) != len(names) or sum(x.file_size for x in entries) > 128 * 1024**2:
            raise ValueError("Duplicate/oversized archive")
        for entry in entries:
            p = PurePosixPath(entry.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in entry.filename or ":" in entry.filename or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsafe archive member")
        if z.testzip() is not None:
            raise ValueError("Archive CRC failure")
        members = {n: z.read(n) for n in names}
    mn = next(n for n in ("archive_manifest.json", "archive-manifest.json") if n in members)
    manifest = json.loads(members[mn])
    pins = manifest.get("members", manifest)
    if set(pins) != set(members) - {mn}:
        raise ValueError("Exact member coverage required")
    for n, pin in pins.items():
        expected = pin["sha256"] if isinstance(pin, dict) else pin
        if sha(members[n]) != expected or (isinstance(pin, dict) and len(members[n]) != pin["bytes"]):
            raise ValueError("Member bytes drift: " + n)
    for n, value in members.items():
        if n.endswith("terminal.json"):
            terminal = json.loads(value)
            prefix = n.rsplit("/", 1)[0] + "/" if "/" in n else ""
            for fn, pin in terminal["files"].items():
                if PurePosixPath(fn).name != fn or sha(members[prefix + fn]) != pin:
                    raise ValueError("Terminal receipt byte drift")
    return members


def audit(output):
    output.mkdir(parents=True, exist_ok=False)
    touched = {}
    assets = []

    def original(path, tracked=False):
        raw = path.read_bytes()
        if tracked:
            rel = path.relative_to(ROOT).as_posix()
            frozen = subprocess.run([GIT, "cat-file", "blob", HEAD + ":" + rel], cwd=ROOT, check=True, capture_output=True).stdout
            if raw != frozen:
                raise ValueError("Frozen tracked bytes changed: " + rel)
        touched[str(path)] = sha(raw)
        return raw

    def cost_view(study, name, obj):
        # Keep stages as reported. Sums/retimings are not performed.
        values = {k: v for k, v in obj.items() if any(t in k for t in ("_ms", "seconds", "tokens", "calls", "peak", "startup", "cost", "ledger", "arm_costs", "attribution"))}
        return {"study": study, "source_member": name, "reported_values": values,
                "units": "as_named_in_original_fields", "aggregation": "NOT_SUMMED_COMPONENTS_MAY_OVERLAP",
                "missing_components": None, "energy_flops_money": "UNKNOWN_UNLESS_ORIGINAL_EXPLICIT_MEASUREMENT"}

    costs = []
    for study, (relative, expected) in PINS.items():
        path = (ROOT / relative).resolve()
        stored = original(path, tracked=path.is_relative_to(ROOT))
        raw = base64.b64decode(stored) if path.name.endswith(".b64") else stored
        members = validate_zip(raw, expected)
        reports = {}
        public_members, oracle_members = [], []
        for name, data in members.items():
            if name.endswith(("report.json", "setup.json")):
                obj = json.loads(data)
                reports[name] = obj
                costs.append(cost_view(study, name, obj))
            if name.endswith(("public.json", "/manifest.json")):
                public_members.append(name)
            if any(t in name for t in ("private", "reference", "records", "task_")):
                oracle_members.append(name)
        assets.append({"study": study, "original_path": relative, "stored_sha256": sha(stored),
                       "zip_sha256": expected, "member_sha256": {n: sha(v) for n, v in members.items()},
                       "verification": "EXTERNAL_ZIP_CRC_EXACT_MANIFEST_AND_TERMINAL_BYTES_PASS",
                       "reports_preserved": reports, "evidence_right": "H_AUDIT",
                       "public_view_candidates": public_members, "oracle_or_diagnostic_members": oracle_members,
                       "runtime_public_activation": False, "training_activation": False,
                       "fresh_eval_activation": False, "allowed_use": "audit_and_explicit_fixture_only",
                       "exposure": "OPENED_DEVELOPMENT", "original_task_replay": "NOT_RUN_IN_THIS_BYTE_AUDIT"})

    from experiments.control_plane_p0_v1 import replay_failure
    from experiments.control_plane_p1_replay import replay as p1_replay
    from experiments.general_compact_evidence_v1062 import analyze
    for study, relative, fn in [
        ("Decision1", "docs/experiments/results/v1062_general_compact_first", analyze),
        ("Decision2", "docs/experiments/results/am1_decision2_first_original", replay_failure),
        ("P1", "docs/experiments/results/control_plane_p1_first/p1", p1_replay),
    ]:
        directory = ROOT / relative
        pins = {}
        for p in sorted(directory.iterdir()):
            if p.is_file():
                pins[p.name] = sha(original(p, tracked=True))
        replay = fn(directory)
        report = json.loads((directory / "report.json").read_bytes())
        costs.append(cost_view(study, "report.json", report))
        assets.append({"study": study, "original_path": relative, "file_sha256": pins,
                       "verification": "FROZEN_GIT_BYTES_AND_EXISTING_MODEL_FREE_REPLAY_PASS",
                       "replay": replay, "evidence_right": "H_AUDIT", "allowed_use": "diagnostic_fixture_only",
                       "training_activation": False, "fresh_eval_activation": False})

    for study, (note, reported) in MISSING.items():
        path = ROOT / "docs/research" / note
        raw = original(path, tracked=True)
        assets.append({"study": study, "metadata_path": str(path.relative_to(ROOT)), "metadata_sha256": sha(raw),
                       "historical_status_reported_not_rejudged": reported,
                       "verification": "FROZEN_METADATA_ONLY_ORIGINAL_ARCHIVE_NOT_LOCALLY_AVAILABLE",
                       "evidence_right": "H_METADATA_ONLY", "allowed_use": "audit_only",
                       "raw_training_or_cost_use": "EXCLUDED_PENDING_ORIGINAL_RECOVERY",
                       "missing_cost": None, "training_activation": False, "fresh_eval_activation": False})

    reusable = []
    for relative in ["neumann1/lp_certificate_v081.py", "neumann1/lp_basis_headroom_v082.py", "neumann1/control_plane_v1.py",
                     "experiments/control_plane_p13_catalog.py", "neumann1/reacomp_policy.py", "neumann1/code_gate.py",
                     "neumann1/structural_data_rights.py"]:
        path = ROOT / relative
        if path.is_file():
            raw = original(path)
            reusable.append({"path": relative, "sha256": sha(raw), "right": "B_CODE",
                             "availability": "SOURCE_PRESENT", "checkpoint_restore": "NOT_ATTEMPTED"})
    # Every available coefficient-bearing LP source already passed D0; absent
    # v100/101 arrays and model checkpoints are optional, excluded dependencies.
    for path, expected in touched.items():
        if sha(Path(path).read_bytes()) != expected:
            raise ValueError("Original modified during audit")
    ledger = {"schema": "neumann.d0-control-assets.v1", "status": "D0_AVAILABLE_ASSET_AUDIT_COMPLETE_WITH_EXCLUSIONS",
              "frozen_head": HEAD, "assets": assets, "building_blocks": reusable,
              "summary": {"verified_zip_archives": len(PINS), "verified_raw_bundles": 3,
                          "metadata_only_excluded_studies": len(MISSING), "original_files_checked": len(touched),
                          "sealed_payloads_read": 0, "new_model_calls": 0, "new_solver_calls": 0,
                          "original_mutations": 0, "fresh_eligible_assets": 0},
              "cost_policy": "Preserve original components and environment; UNKNOWN not zero; no cross-environment ranking",
              "scope": "All retained selected assets audited; unavailable originals/checkpoints not made reusable by this ledger",
              "g0_dependency_policy": "G0 uses new public producers and mature CPU solvers; no unavailable historical archive or checkpoint dependency"}
    files = {"control_asset_ledger.json": ledger, "control_cost_coverage.json": costs}
    for name, obj in files.items():
        (output / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {name: sha((output / name).read_bytes()) for name in files}
    manifest["audit_source_sha256"] = sha(Path(__file__).read_bytes())
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(ledger["summary"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    out = parser.parse_args().output
    try:
        audit(out)
    except Exception as exc:
        if out.is_dir() and not (out / "manifest.json").exists():
            (out / "engineering_failure.json").write_text(json.dumps({"status": "D0_ENGINEERING_FAILURE",
                "error_type": type(exc).__name__, "error": str(exc), "model_calls": 0,
                "solver_calls": 0, "historical_verdicts_changed": False}, indent=2) + "\n", encoding="utf-8")
        raise
