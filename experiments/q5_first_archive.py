"""Immutable first Q5 archive authority, not an execution or rerun entry point."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from experiments.q5_register import evidence_module

SOURCE_HEAD = "9ce2d1b22917b31d298de763e113c5826dc2bb0c"
SOURCE_MANIFEST_SHA256 = "684a1e54656a0e491f67438a730799af91cca9f0e401ad9da94068fd1deaed64"
SOURCE_TERMINAL_SHA256 = "8746b5a6eadcc4f4c1d01760353dfa0cb5a531fbc2d035ba08d36f928cf7ee6f"
EVALUATION_HEAD = "99e59fe9ceec4102d023ce0f9eb2e510017062c4"
REPORT_RAW_SHA256 = "1f7a3ad5a1038e42234b734b0b00f185c0be4a5a1d11a3d3d6e96ace92d546e3"
REPORT_SHA256 = "55f3908bee428b5a5370d715fef7ae23ce0d2adf61b9cf8af58743cabbe4397b"
RESULT_TERMINAL_SHA256 = "3858c871ec2b7f61ca8deda3436ed9150c591a342c4518749087085a8c06d691"
DECISION = "Q5_SCALING_CAPABILITY_OR_ACCOUNTING_UNREACHED"


def source_pin(directory):
    """Check externally pinned first bytes before costly semantic replay."""
    ev = evidence_module()
    directory = Path(directory)
    raw = (directory / "manifest.json").read_bytes()
    if ev.digest(raw) != SOURCE_MANIFEST_SHA256:
        raise ValueError("Q5 first source manifest replacement")
    manifest = json.loads(raw)
    rows, terminal = ev.read_events(directory)
    if (manifest["frozen_head"] != SOURCE_HEAD
            or terminal["last_sha256"] != SOURCE_TERMINAL_SHA256
            or terminal["status"] != "sources_frozen"
            or len(rows) != 98
            or terminal["manifest_sha256"] != ev.digest(ev.canonical(manifest))):
        raise ValueError("Q5 first source receipt replacement")
    return manifest


def result_pin(directory):
    ev = evidence_module()
    directory = Path(directory)
    raw = (directory / "report.json").read_bytes()
    if ev.digest(raw) != REPORT_RAW_SHA256:
        raise ValueError("Q5 first report replacement")
    report = json.loads(raw)
    rows, terminal = ev.read_events(directory)
    reservation = json.loads((directory / "reservation.json").read_text())
    if (ev.digest(ev.canonical(report)) != REPORT_SHA256
            or report["frozen_head"] != EVALUATION_HEAD
            or report["source_manifest_sha256"] != SOURCE_MANIFEST_SHA256
            or report["summary"]["decision"] != DECISION
            or terminal != {"status": "completed", "events": 3084,
                "last_sha256": RESULT_TERMINAL_SHA256, "report_sha256": REPORT_SHA256,
                "observations": 1536, "decision": DECISION}
            or reservation != {"schema": "neumann.q5-attempt.v1", "stage": "first_evaluation",
                "frozen_head": EVALUATION_HEAD, "rerun": False}):
        raise ValueError("Q5 first result receipt replacement")
    return report, rows


def replay_first(sources, results):
    """Independently verify first witnesses/costs, forbidding fresh execution."""
    source_pin(sources)
    pinned, rows = result_pin(results)
    from experiments.q5_replay import replay
    forbidden = AssertionError("first Q5 replay cannot generate, fit, forward or solve")
    with ExitStack() as stack:
        for target in ("highspy.Highs.run", "torch.nn.Module._call_impl",
                       "neumann1.lp_basis_headroom_v082.generate_q5_case",
                       "experiments.lp_frozen_support_expansion_v101.frozen_ranking",
                       "experiments.lp_frozen_support_expansion_v101.restore_frozen_quotient"):
            stack.enter_context(patch(target, side_effect=forbidden))
        derived = replay(sources, results)
    if derived != pinned:
        raise ValueError("Q5 independent replay changed first report")
    ev = evidence_module()
    failures, native_errors, max_rss = Counter(), Counter(), {}
    for row in rows:
        if row["kind"] != "observation":
            continue
        record = ev.unpack_case(results, row["payload"]["identity"])
        route = record["route"]
        max_rss[route] = max(max_rss.get(route, 0), record["peak_rss_kib"])
        if not record["accepted"]:
            failures[route] += 1
            execution = record["execution"]
            if execution is not None:
                for attempt in execution.get("attempts", []):
                    native_errors[attempt.get("error") or execution["status"]] += 1
    return {"status": "FIRST_RETAINED_BYTES_WITNESSES_AND_COSTS_REPLAY_PASS",
            "decision": DECISION, "observations": 1536,
            "failed_observations_by_route": dict(failures),
            "failed_native_attempt_errors": dict(native_errors), "peak_rss_kib_by_route": max_rss,
            "cell_statuses": dict(Counter(r["status"] for r in pinned["summary"]["cells"])),
            "eligible_slopes": len(pinned["summary"]["slopes"]),
            "new_generation": 0, "new_forward": 0, "new_solver_calls": 0,
            "cross_domain_pass": False, "global_q5_closed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--results", required=True)
    args = parser.parse_args()
    print(json.dumps(replay_first(args.sources, args.results), sort_keys=True))


if __name__ == "__main__":
    main()
