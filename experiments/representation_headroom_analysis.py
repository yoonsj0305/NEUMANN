"""Post-result phase diagnostics; no modified pass rule or replacement verdict."""
from collections import Counter
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.representation_headroom import digest, save


def analyze(output, destination, workspace):
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    observations = [json.loads(line) for path in (output / "observations").glob("*.jsonl")
                    for line in path.read_text(encoding="utf-8").splitlines()]
    diagnostics = []
    counts = {r: Counter() for r in ["first_query", "reuse64"]}
    for case in report["cases"]:
        for regime in counts:
            counts[regime]["/".join(case["metrics"][regime]["best_native"])] += 1
        first = case["metrics"]["first_query"]
        route, backend = first["best_free"]
        free = [o for o in observations if o["case_id"] == case["spec"]["id"] and
                o["route"] == route and o["backend"] == backend]
        diagnostics.append({"case_id": case["spec"]["id"], "first_free_backend": backend,
            "free_first_verification_fraction": statistics.median(o["verification_seconds"] / o["first_query_seconds"] for o in free),
            "free_first_compile_fraction": statistics.median(o["compile_seconds"] / o["first_query_seconds"] for o in free),
            "first_ratio": first["ratio"], "reuse64_ratio": case["metrics"]["reuse64"]["ratio"]})
    first_receipt = json.loads((workspace / "Continuation/G0_PREPARATION/first-result-receipt.json").read_text(encoding="utf-8"))
    originals = {"preregister_sha256": workspace / "Continuation/G0_PREPARATION/preregister.json",
                 "manifest_sha256": workspace / "Continuation/G0_FIRST/manifest.json",
                 "report_sha256": workspace / "Continuation/G0_FIRST/report.json",
                 "replay_sha256": workspace / "Continuation/G0_FIRST/replay.json"}
    assert all(digest(path) == first_receipt[key] for key, path in originals.items())
    result = {"status": "DIAGNOSTICS_ONLY_ORIGINAL_VERDICTS_UNCHANGED",
              "first_report_sha256": digest(output / "report.json"),
              "prior_G0_v1_external_pins_still_match": True,
              "best_native_counts": {r: dict(c) for r, c in counts.items()},
              "median_case_free_first_verification_fraction": statistics.median(d["free_first_verification_fraction"] for d in diagnostics),
              "median_case_free_first_compile_fraction": statistics.median(d["free_first_compile_fraction"] for d in diagnostics),
              "cases": diagnostics,
              "limits": ["These phase shares are observed implementation costs, not unavoidable lower bounds.",
                         "No verification cost removed from registered result.",
                         "A new proof-carrying representation would need a separate source/contract and strong baselines."]}
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError("Preserve first analysis")
    save(destination, result)
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}))


if __name__ == "__main__":
    analyze(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
