"""Frozen Q34 optional Edge mode: check real archived first cold/warm and resident memory.

Retrospective engineering-only, one OPENED v102 original. This imports and runs
the previously retained smoke exactly once in a fresh GitHub Actions process.
"""
from __future__ import annotations
import hashlib
import json
import runpy
from pathlib import Path

OUT = Path("research/development/hybrid_r0_frozen_memory_gate_20261009")
SOURCE = Path("research/development/hybrid_r0_first_slice/opened_q34_three_route_smoke.json")
LIMIT_KB = 4 * 1024 * 1024

def main():
    # Existing authoritative frozen smoke uses only historical sealed-in-time
    # OPENED archive and frozen checkpoint. No retraining, retuning, new source.
    runpy.run_module("experiments.hybrid_r0_frozen_opened_smoke", run_name="__main__")
    binary = SOURCE.read_bytes()
    payload = json.loads(binary)
    entries = payload["records"]
    wanted = ["native", "classical_fixed4m",
              "frozen_q34_seed100001_cold", "frozen_q34_seed100001_warm"]
    if [x["route"] for x in entries] != wanted:
        raise RuntimeError("frozen original route population drift")
    for x in entries:
        if x["receipt"]["status"] != "VERIFIED":
            raise RuntimeError("noncertified path in optional frozen mode")
        if x["receipt"]["answer"]["certificate"] != "neumann.lp-standard-form-certificate.v1":
            raise RuntimeError("original LP dual proof absent")
        if x["receipt"]["original_task_sha256"] != entries[0]["receipt"]["original_task_sha256"]:
            raise RuntimeError("different original task entered")
    cold, warm = entries[2]["receipt"], entries[3]["receipt"]
    fc = [e for e in cold["events"] if e["kind"] == "frozen_q34_learned_proposal"]
    fw = [e for e in warm["events"] if e["kind"] == "frozen_q34_learned_proposal"]
    if (len(fc) != 1 or len(fw) != 1 or
        fc[0]["checkpoint_cache_hit"] or not fw[0]["checkpoint_cache_hit"] or
        cold["cost"]["model_calls"] != 1 or warm["cost"]["model_calls"] != 1):
        raise RuntimeError("model restore/call accounting mismatch")
    peaks = [x["receipt"]["cost"].get("process_peak_rss_kb") for x in entries]
    if any(type(x) not in (float, int) or x <= 0 for x in peaks):
        raise RuntimeError("resident Linux RSS metrics unavailable")
    # resource.ru_maxrss is a process high-water mark on Linux, unlike the
    # sampled process tree telemetry in the model-free clean-install gate.
    max_peak = max(peaks)
    summary = {
        "status": "OPTIONAL_FROZEN_Q34_EDGE_MEMORY_ENGINEERING_PASS"
                  if max_peak < LIMIT_KB else "OPTIONAL_FROZEN_Q34_EDGE_MEMORY_OVER_BUDGET",
        "frozen_source_scope": "ONE_OPENED_V102_LP_ORIGINAL_ONLY",
        "route_count": 4, "independent_originals": 1,
        "originals_verified": 4, "checkpoint_cache_reused": True,
        "peak_rss_kb_by_route": dict(zip(wanted, peaks)),
        "maximum_process_peak_rss_mib": max_peak / 1024.,
        "declared_edge_budget_mib": LIMIT_KB / 1024.,
        "observed_wall_ms_by_route": {x["route"]: x["receipt"]["cost"]["observed_wall_ms"]
                                      for x in entries},
        "source_receipts_sha256": hashlib.sha256(binary).hexdigest(),
        "cpu_only": True, "training": False, "frontier_calls": 0,
        "energy_j": "UNKNOWN", "thermal": "UNKNOWN",
        "no_fresh_neural_generalization": True,
        "disclaimer": "Engineering resident memory on one Linux GitHub CPU; no thermal, "
                      "energy, continuous service, or independent new-problem proof",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2)+"\n")
    (OUT / "source_smoke_retained.json").write_bytes(binary)
    print("FROZEN_EDGE_RSS_GATE=" + json.dumps(summary, sort_keys=True), flush=True)
    if max_peak >= LIMIT_KB:
        raise RuntimeError("optional frozen LP proposer exceeded declared 4GiB edge limit")
    return summary

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "fatal.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        raise
