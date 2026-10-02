"""Standard-library-only, first-attempt Q5 evidence primitives.

No fitting, LP generation, inference, solver execution or benchmark occurs on
import. Files are immutable; a reserved attempt cannot be silently resumed.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import os
import random
from pathlib import Path

from . import q5_scaling_contract as contract

RUNTIME = {"python": [3, 12], "numpy": "2.3.5", "scipy": "1.17.0",
           "scikit_learn": "1.9.1", "torch": "2.14.0+cpu",
           "highspy": "1.15.1", "threadpoolctl": "3.7.0"}
ROUTES = ("DIRECT", "ORACLE", "EXPAND4_s100001", "EXPAND4_s100002")
MAX_CASE_BYTES = 32 * 1024 * 1024
ZERO_HASH = "0" * 64


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def head_sha(value):
    if type(value) is not str or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("a pinned lowercase commit SHA is required")
    return value


def finite_ms(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("finite nonnegative cost required")
    return float(value)


def safe_name(name):
    if type(name) is not str or not name or name in (".", "..") or Path(name).name != name or "\\" in name:
        raise ValueError("unsafe evidence filename")
    return name


def exclusive_bytes(path, data):
    path = Path(path)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    exclusive_bytes(path, canonical(value) + b"\n")


class Attempt:
    """Reserve BEFORE imports/preflight/generation/timing; preserve every event.

    Creating the directory is atomic. A failed/partial attempt remains a stop
    condition, not permission to delete it or pick a new output path and rerun.
    """
    def __init__(self, path, stage, frozen_head):
        self.path = Path(path)
        head_sha(frozen_head)
        self.path.mkdir(parents=False, exist_ok=False)
        write_json(self.path / "reservation.json", {
            "schema": "neumann.q5-attempt.v1", "stage": stage,
            "frozen_head": frozen_head, "rerun": False,
        })
        self.stream = (self.path / "events.jsonl").open("xb")
        self.index = 0
        self.previous = ZERO_HASH

    def append(self, kind, payload):
        core = {"index": self.index, "previous": self.previous,
                "kind": kind, "payload": payload}
        row = {**core, "sha256": digest(canonical(core))}
        self.stream.write(canonical(row) + b"\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.previous = row["sha256"]
        self.index += 1
        return row

    def finish(self, status, **details):
        self.append("terminal", {"status": status, **details})
        self.stream.close()
        write_json(self.path / "terminal.json", {
            "status": status, "events": self.index, "last_sha256": self.previous, **details,
        })


def read_events(path):
    path = Path(path)
    previous, rows = ZERO_HASH, []
    with (path / "events.jsonl").open("rb") as stream:
        for index, line in enumerate(stream):
            row = json.loads(line)
            core = {k: row[k] for k in ("index", "previous", "kind", "payload")}
            if (set(row) != {*core, "sha256"} or row["index"] != index
                    or row["previous"] != previous or digest(canonical(core)) != row["sha256"]):
                raise ValueError("Q5 event chain drift")
            previous = row["sha256"]
            rows.append(row)
    terminal = json.loads((path / "terminal.json").read_text())
    if (not rows or rows[-1]["kind"] != "terminal"
            or terminal["events"] != len(rows) or terminal["last_sha256"] != previous
            or terminal["status"] != rows[-1]["payload"]["status"]):
        raise ValueError("Q5 missing/truncated terminal receipt")
    return rows, terminal


def pack_case(directory, name, value):
    raw = canonical(value)
    if len(raw) > MAX_CASE_BYTES:
        raise ValueError("Q5 per-case archive limit exceeded")
    name = safe_name(name)
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    exclusive_bytes(Path(directory) / name, packed)
    return {"file": name, "gzip_bytes": len(packed), "gzip_sha256": digest(packed),
            "json_bytes": len(raw), "json_sha256": digest(raw)}


def unpack_case(directory, identity):
    name = safe_name(identity["file"])
    limit = identity["json_bytes"]
    if type(limit) is not int or not 0 < limit <= MAX_CASE_BYTES:
        raise ValueError("Q5 invalid decoded size")
    size = identity["gzip_bytes"]
    if type(size) is not int or not 0 < size <= MAX_CASE_BYTES:
        raise ValueError("Q5 invalid compressed size")
    path = Path(directory) / name
    if path.stat().st_size != size:
        raise ValueError("Q5 compressed size drift")
    packed = path.read_bytes()
    if digest(packed) != identity["gzip_sha256"]:
        raise ValueError("Q5 compressed hash drift")
    # Bound expansion BEFORE allocation, not after gzip.decompress.
    with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
        raw = stream.read(limit + 1)
    if len(raw) != limit or digest(raw) != identity["json_sha256"]:
        raise ValueError("Q5 decoded identity drift")
    return json.loads(raw)


def schedule():
    rng = random.Random(contract.protocol()["order_seed"])
    rows = []
    for repeat in (-1, 0, 1, 2):
        block = [(s["id"], route, repeat) for s in contract.planned_views() for route in ROUTES]
        rng.shuffle(block)
        rows.extend(block)
    return rows


def summarize(records, cold, training):
    """Requires independent source/witness/attempt validation by replay first."""
    from statistics import median
    expected = schedule()
    if [(r["case_id"], r["route"], r["repeat"]) for r in records] != expected:
        raise ValueError("Q5 first observation order/coverage drift")
    if set(cold) != set(ROUTES):
        raise ValueError("Q5 cold-start route coverage drift")
    med = {}
    for source in contract.planned_views():
        for route in ROUTES:
            rows = [r for r in records if r["case_id"] == source["id"] and r["route"] == route]
            timed = [r for r in rows if r["repeat"] >= 0]
            setup = 0.0
            if route.startswith("EXPAND4"):
                t = training[route.rsplit("s", 1)[1]]
                setup = finite_ms(t["fit_ms"]) + finite_ms(t["feature_setup_ms"])
            startup = finite_ms(cold[route]["cold_start_ms"]) if route != "ORACLE" else 0.0
            costs = [contract.charged_cost(proposal_ms=r["proposal_ms"], post_ms=r["post_ms"],
                     fit_setup_ms=setup, cold_start_ms=startup) for r in timed]
            complete = median(c["complete_ms"] for c in costs)
            discovery = median(c["discovery_ms"] for c in costs)
            # Gates must equal median COMPLETE cost, not a cheaper sum of
            # independently chosen stage medians. Retain actual post median too.
            med[source["id"], route] = {
                "complete_ms": complete, "discovery_ms": discovery,
                "effective_post_ms": complete - discovery,
                "observed_post_median_ms": median(r["post_ms"] for r in timed),
                "cold_q1_ms": startup + setup + median(r["total_ms"] for r in timed),
                "capable": all(r["accepted"] for r in rows),
                "accounted": all(r["accounted"] for r in rows),
            }
    cells, slopes = {}, {}
    views = contract.planned_views()
    for seed in contract.SEEDS:
        route = f"EXPAND4_s{seed}"
        for m in contract.ROWS:
            for width in contract.WIDTHS:
                for surface in (False, True):
                    selected = [s for s in views if (s["rows"], s["width_factor"], s["surface"]) == (m, width, surface)]
                    def total(r, field):
                        return sum(med[s["id"], r][field] for s in selected)
                    def all_flag(r, field):
                        return all(med[s["id"], r][field] for s in selected)
                    cells[seed, m, width, surface] = contract.cell_gate(
                        direct_ms=total("DIRECT", "complete_ms"),
                        oracle_ms=total("ORACLE", "complete_ms"),
                        discovery_ms=total(route, "discovery_ms"),
                        post_ms=total(route, "effective_post_ms"),
                        direct_verified=all_flag("DIRECT", "capable"),
                        oracle_verified=all_flag("ORACLE", "capable"),
                        candidate_verified=all_flag(route, "capable"),
                        all_attempt_costs_charged=all(all_flag(r, "accounted") for r in ("DIRECT", "ORACLE", route)),
                        width_factor=width)
        for width in (16, 32):
            for surface in (False, True):
                selected = [s for s in views if s["width_factor"] == width and s["surface"] == surface]
                if all(med[s["id"], r][flag] for s in selected for r in ("DIRECT", route)
                       for flag in ("capable", "accounted")):
                    pairs = {m: [(med[s["id"], "DIRECT"]["complete_ms"], med[s["id"], route]["complete_ms"])
                                 for s in selected if s["rows"] == m] for m in contract.ROWS}
                    slopes[seed, width, surface] = contract.slope_evidence(pairs)
    summary = contract.summarize_scaling(cells, slopes)
    return {**summary, "cells": [{"seed": k[0], "rows": k[1], "width_factor": k[2], "surface": k[3], **v}
                                  for k, v in sorted(cells.items())],
            "slopes": [{"seed": k[0], "width_factor": k[1], "surface": k[2], **v} for k, v in sorted(slopes.items())],
            "case_costs": [{"case_id": k[0], "route": k[1], **v} for k, v in sorted(med.items())],
            "failures_including_warmup": sum(not r["accepted"] for r in records),
            "observations": len(records), "evidence_scope": "constructed_LP_only"}
