"""Model-free original P1 hash, accounting and diagnostic-verdict replay."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from neumann1.control_plane_v1 import ROUTES, digest, finite, public_view
from neumann1.control_plane_p1_contract import CRITERIA, PUBLIC_SHA256, TASK_IDS, P1Budget, evaluate, manifest, route_statistics, validate_identity


def replay(directory):
    directory = Path(directory)
    load = lambda name: json.loads((directory / name).read_bytes())
    terminal = load("terminal.json")
    retained = {p.name for p in directory.glob("*.json") if p.name != "terminal.json"}
    if retained != set(terminal["files"]) or "report.json" not in retained:
        raise ValueError("exact retained receipt coverage required")
    for name, expected in terminal["files"].items():
        if Path(name).name != name or hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError("retained first byte drift: " + name)
    report = load("report.json")
    if terminal.get("no_replacement") is not True or report["generated_calls"] != 0 or report["tool_calls"] != 0:
        raise ValueError("scientific execution boundary drift")
    if terminal["complete"] != (report["status"] == "COMPLETE") or terminal["decision"] != report["decision"]["verdict"]:
        raise ValueError("terminal/report completeness drift")
    if report["status"] != "COMPLETE":
        return {"integrity_valid": True, "complete": False, "decision": report["decision"],
                "next": "PRESERVE_FIRST_FAILURE_NO_AUTOMATIC_RERUN", "model_inference": False}
    data = load("manifest.json")
    if data["registration"]["contract"] != manifest():
        raise ValueError("registered contract drift")
    rows = data["public_rows"]
    if tuple(r["task_id"] for r in rows) != TASK_IDS or any(set(r) != {"task_id", "view"} for r in rows):
        raise ValueError("exact original opened task coverage required")
    if digest([public_view(r["view"]) for r in rows]) != PUBLIC_SHA256:
        raise ValueError("original public input drift")
    validate_identity(load("core.json"))
    scorer = load("scorer.json")
    validate_identity(scorer)
    records = [load("task_%02d.json" % i) for i in range(12)]
    totals = {k:0 for k in ("evaluated_tokens", "padded_tokens", "forward_calls", "score_rows", "scored_tokens")}
    for record, row in zip(records, data["public_rows"]):
        if record["task_id"] != row["task_id"] or record["view_sha256"] != digest(row["view"]):
            raise ValueError("public-task identity drift")
        if record["trace_sha256"] != digest(record["passes"]):
            raise ValueError("scoring trace drift")
        modes = record["passes"]
        if [p["mode"] for p in modes] != ["batch4", "unbatched1", "reverse_batch4"]:
            raise ValueError("three registered scoring modes required")
        for p in modes:
            if p["status"] != "COMPLETE" or p["generated_tokens"] != 0:
                raise ValueError("complete no-generation scoring required")
            labels = list(ROUTES) if p["mode"] != "reverse_batch4" else list(reversed(ROUTES))
            if p["labels"] != labels or set(p["scores"]) != set(ROUTES):
                raise ValueError("fixed candidate coverage drift")
            for value in p["scores"].values():
                if finite(value) > 0:
                    raise ValueError("log-likelihood score invalid")
            encoded = p["encoded_rows"]
            if len(encoded) != 4 or any(not r["prompt_ids"] or not r["label_ids"] for r in encoded):
                raise ValueError("exact nonempty candidate rows required")
            if any(len(r["prompt_ids"])+len(r["label_ids"]) > P1Budget().context_tokens
                   or len(r["label_ids"]) > P1Budget().label_tokens for r in encoded):
                raise ValueError("registered encoded context/label admission drift")
            size = p["batch_size"]
            expected_size = 1 if p["mode"] == "unbatched1" else 4
            if size != expected_size:
                raise ValueError("registered batch size drift")
            actual = {"evaluated_tokens":sum(len(r["prompt_ids"])+len(r["label_ids"]) for r in encoded),
                      "score_rows":4, "forward_calls":4 if size == 1 else 1,
                      "padded_tokens":sum(max(len(r["prompt_ids"])+len(r["label_ids"]) for r in encoded[i:i+size])
                                           *len(encoded[i:i+size]) for i in range(0,4,size))}
            if actual != p["actual"] or actual != p["planned"]:
                raise ValueError("forward/input/padding accounting drift")
            for key, value in actual.items():
                totals[key] += value
            label_count = sum(len(r["label_ids"]) for r in encoded)
            if p["scored_tokens"] != label_count:
                raise ValueError("scored token accounting drift")
            totals["scored_tokens"] += label_count
        vectors = [[p["scores"][r] for r in ROUTES] for p in modes]
        if record["canonical_scores"] != vectors[0] or record["statistics"] != route_statistics(vectors[0]):
            raise ValueError("route summary drift")
        deltas = [max(abs(a-b) for a,b in zip(vectors[0], vector)) for vector in vectors[1:]]
        if deltas != [record["max_batch_delta_nats"], record["max_order_delta_nats"]]:
            raise ValueError("numerical consistency accounting drift")
        stats = route_statistics(vectors[0])
        stable = stats["margin_nats"] <= CRITERIA["strict_winner_margin_nats"] or all(
            route_statistics(v)["winner"] == stats["winner"] for v in vectors[1:])
        if record["stable_large_margin_winner"] is not stable:
            raise ValueError("winner stability summary drift")
    if totals != report["ledger"] or any(totals[k] > getattr(P1Budget(),k) for k in totals if k != "scored_tokens"):
        raise ValueError("complete study aggregate/budget drift")
    decision = evaluate(records, report["core_audit"], report["generated_calls"], report["whole_study_ms"], report["accounting_complete"])
    if decision != report["decision"] or decision["verdict"] != terminal["decision"]:
        raise ValueError("diagnostic verdict drift")
    return {"integrity_valid": True, "complete": True, "decision": decision, "records":12,
            "scoring_rows":totals["score_rows"], "model_inference":False,
            "general_capability_gate":"NOT_EVALUATED", "decision3_admitted":False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    print(json.dumps(replay(args.directory), sort_keys=True))
