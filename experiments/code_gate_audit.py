"""Model-free integrity/receipt audit; official Linux checks are in the receipts.

Does not execute generated Python on the local Windows host, or certify universal
function correctness. Does not load the private reference pickle.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

from neumann1.code_contract import admit, public_view


FIRST = "a137b6d0b3b9c99d709623763fcca1c3470a1cf596b075d69ddbd3ba2868cf1c"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive(path, expected=None):
    raw = path.read_bytes()
    if expected is not None and digest(raw) != expected:
        raise ValueError("original archive hash mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or any(Path(name).name != name for name in names):
            raise ValueError("unsafe or duplicate evidence members")
        if z.testzip() is not None:
            raise ValueError("archive CRC failure")
        data = {name: z.read(name) for name in names}
    manifest = json.loads(data["archive-manifest.json"])
    if set(data) != set(manifest) | {"archive-manifest.json"}:
        raise ValueError("incomplete member manifest")
    for name, expected_hash in manifest.items():
        if digest(data[name]) != expected_hash:
            raise ValueError("member hash mismatch: " + name)
    return data, digest(raw)


def audit(first_path, cache_path=None):
    data, first_hash = archive(first_path, FIRST)
    reg = json.loads(data["registration.json"])
    freeze = json.loads(data["freeze.json"])
    report = json.loads(data["report.json"])
    public = json.loads(data["public.json"])
    private = json.loads(data["references.private.json"])
    rows = [json.loads(x) for x in data["records.jsonl"].splitlines()]
    if freeze["registration_sha256"] != digest(data["registration.json"]):
        raise ValueError("registration freeze mismatch")
    if digest(data["source-overlay.zip"]) != reg["upstream_overlay_sha256"]:
        raise ValueError("upstream/source freeze mismatch")
    if freeze["overlay_sha256"] != digest(data["source-overlay.zip"]) or freeze["task_count"] != 16:
        raise ValueError("overlay/task-count freeze mismatch")
    if json.loads(data["model-artifacts.json"]) != reg["model"]:
        raise ValueError("downloaded model artifact receipt mismatch")
    if sum(meta["size"] for name, meta in reg["model"]["files"].items()
           if name.endswith(".safetensors")) != freeze["model_weight_bytes"]:
        raise ValueError("frozen weight byte mismatch")
    with zipfile.ZipFile(io.BytesIO(data["source-overlay.zip"])) as overlay:
        for name, expected in reg["source_sha256"].items():
            if digest(overlay.read(name)) != expected:
                raise ValueError("registered implementation mismatch")
    for name, expected in reg["data_sha256"].items():
        if digest(data[name]) != expected:
            raise ValueError("registered input mismatch")
    ids = reg["task_ids"]
    if len(set(ids)) != 16 or any([x["task_id"] for x in items] != ids for items in (public, private, rows)):
        raise ValueError("registered task alignment mismatch")
    if public != [public_view(task) for task in private]:
        raise ValueError("private authority leaked into public task fields")
    for task, row in zip(private, rows):
        admit(row["source"], task["entry_point"])
        if row["admission_error"] is not None or set(row["checks"]) != {"base", "plus"}:
            raise ValueError("admission receipt mismatch")
        for group, check in row["checks"].items():
            count = len(task[group + "_input"])
            if check["total_cases"] != count or not 0 <= check["passed_cases"] <= count:
                raise ValueError("test count mismatch")
            if check["status"] == "pass" and check["passed_cases"] != count:
                raise ValueError("invalid test pass claim")
        if row["joint_correct"] != all(x["status"] == "pass" for x in row["checks"].values()):
            raise ValueError("joint correctness mismatch")
        if not row["ended_at_eos"] or row["output_tokens"] > reg["max_new_tokens"] or row["input_tokens"] > reg["max_input_tokens"]:
            raise ValueError("generation budget/termination mismatch")
        for key in ("generation_seconds", "parse_seconds", "verification_seconds", "complete_seconds"):
            if not math.isfinite(row[key]) or row[key] < 0:
                raise ValueError("invalid measured duration")
    for key in ("input_tokens", "output_tokens"):
        if sum(x[key] for x in rows) != report[key]:
            raise ValueError("aggregate token mismatch")
    passed = sum(x["joint_correct"] for x in rows)
    if (passed, len(rows), len(rows), passed >= reg["capability_floor"]) != (
            report["passed"], report["total"], report["model_calls"], report["baseline_admitted"]):
        raise ValueError("aggregate capability mismatch")
    if report["model"] != reg["model"] or report["registration_sha256"] != digest(data["registration.json"]) or report["receipts_sha256"] != digest(data["records.jsonl"]):
        raise ValueError("report identity mismatch")
    for row_key, value in (("complete_seconds", report["complete_items_seconds"]),
                          ("generation_seconds", report["cost_attribution"]["generation_seconds"]),
                          ("verification_seconds", report["cost_attribution"]["verification_seconds_all_attempts"])):
        if not math.isclose(sum(x[row_key] for x in rows), value, abs_tol=1e-8):
            raise ValueError("duration aggregate mismatch")
    result = {"status": "PASS", "first_archive_sha256": first_hash,
              "original_linux_test_result": f"{passed}/{len(rows)}",
              "base_test_cases": sum(x["checks"]["base"]["total_cases"] for x in rows),
              "plus_test_cases": sum(x["checks"]["plus"]["total_cases"] for x in rows),
              "all_generations_eos": True,
              "meaning": "archive/contract/receipt integrity; Linux official checker already executed, no local code execution or universal proof"}
    if cache_path:
        cached, cache_hash = archive(cache_path)
        cache_report = json.loads(cached["report.json"])
        cache_rows = json.loads(cached["records.json"])
        cache_freeze = json.loads(cached["freeze.json"])
        if cache_freeze["first_archive_sha256"] != first_hash or cache_report["freeze"] != cache_freeze:
            raise ValueError("cache freeze identity mismatch")
        with zipfile.ZipFile(io.BytesIO(cached["source-overlay.zip"])) as overlay:
            for name, expected in cache_freeze["source_sha256"].items():
                if digest(overlay.read(name)) != expected:
                    raise ValueError("cache source mismatch")
        if [x["task_id"] for x in cache_rows] != ids or cache_report["model_calls"] != 0:
            raise ValueError("cache alignment/budget mismatch")
        for row, cached_row in zip(rows, cache_rows):
            if cached_row["source_sha256"] != digest(row["source"].encode()) or cached_row["checks"] != row["checks"] or cached_row["same_test_results_as_first"] is not True:
                raise ValueError("independent full checker replay mismatch")
        if cache_report["passed"] != passed or cache_report["total"] != len(rows):
            raise ValueError("cache aggregate mismatch")
        if cache_report["first_receipts_sha256"] != digest(data["records.jsonl"]):
            raise ValueError("cache origin receipt mismatch")
        if json.loads(cached["process.json"])["returncode"] != 0:
            raise ValueError("cache subprocess failure")
        for row_key, aggregate in (("lookup_seconds", "lookup_seconds"),
                                   ("verification_seconds", "verification_seconds"),
                                   ("complete_seconds", "complete_items_seconds")):
            if not math.isclose(sum(x[row_key] for x in cache_rows), cache_report[aggregate], abs_tol=1e-8):
                raise ValueError("cache duration aggregate mismatch")
        result.update(cache_archive_sha256=cache_hash, independent_linux_cache_replay="PASS",
                      cache_model_calls=0)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.first, args.cache)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
