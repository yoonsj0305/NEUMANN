"""Constructed relational headroom; no model, hidden teacher plan, or user SQL."""
from __future__ import annotations

import hashlib
import json
import platform
import random
import sqlite3
import threading
from statistics import mean, median
from math import isfinite
from time import perf_counter, perf_counter_ns


ORDERS = (("a", "b", "c"), ("b", "a", "c"),
          ("b", "c", "a"), ("c", "b", "a"))
POLICIES = ("native", "grouped_counts") + tuple(f"order_{i}" for i in range(4))
REPEATS, ORDER_SEED, TIMEOUT_S = 3, 8091, 2.0
DUCKDB_VERSION = "1.5.6"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def specifications() -> tuple[dict, ...]:
    return tuple({"id": f"case_{i:02d}", "n": n, "shape": shape,
                  "threshold": threshold, "seed": 8001 + i}
                 for i, (n, shape, threshold) in enumerate(
                     (n, shape, t) for n in (2000, 8000)
                     for shape in ("uniform", "skew", "correlated") for t in (25, 75)))


def relations(spec: dict) -> dict:
    rng, n, shape = random.Random(spec["seed"]), spec["n"], spec["shape"]
    if n not in (2000, 8000) or shape not in ("uniform", "skew", "correlated"):
        raise ValueError("outside frozen generator family")
    def key():
        # Mild declared skew, not selected from measured timing results.
        return rng.randrange(128 if shape == "skew" and rng.random() < .15 else 512)
    def flagged():
        k = key()
        return (k, k % 100 if shape == "correlated" else rng.randrange(100))
    return {"a": [flagged() for _ in range(n)],
            "b": [(key(), key(), rng.randrange(1, 10)) for _ in range(n)],
            "c": [flagged() for _ in range(n)]}


def original_sql(threshold: int, order=ORDERS[0]) -> str:
    if type(threshold) is not int or threshold not in (25, 75) or order not in ORDERS:
        raise ValueError("only frozen typed query/permutation allowed")
    joined, parts = {order[0]}, [order[0]]
    for table in order[1:]:
        if table == "a": predicate = "a.k=b.k"
        elif table == "c": predicate = "b.j=c.j"
        elif "a" in joined: predicate = "a.k=b.k"
        else: predicate = "b.j=c.j"
        parts.append(f"JOIN {table} ON {predicate}")
        joined.add(table)
    return ("SELECT COUNT(*), COALESCE(SUM(b.w),0) FROM " + " ".join(parts)
            + f" WHERE a.flag<{threshold} AND c.flag<{threshold}")


def grouped_sql(threshold: int) -> str:
    original_sql(threshold)
    return f"""WITH aa AS (SELECT k,COUNT(*) n FROM a WHERE flag<{threshold} GROUP BY k),
    cc AS (SELECT j,COUNT(*) n FROM c WHERE flag<{threshold} GROUP BY j),
    bb AS (SELECT k,j,COUNT(*) n,SUM(w) w FROM b GROUP BY k,j)
    SELECT COALESCE(SUM(aa.n*bb.n*cc.n),0),COALESCE(SUM(aa.n*bb.w*cc.n),0)
    FROM aa JOIN bb ON aa.k=bb.k JOIN cc ON bb.j=cc.j"""


def build(rows):
    import duckdb  # Optional experiment dependency, absent from core imports.
    if duckdb.__version__ != DUCKDB_VERSION:
        raise ValueError("frozen engine version required")
    db = duckdb.connect(config={"threads": 1, "memory_limit": "512MB"})
    checker = sqlite3.connect(":memory:")
    schema = {"a": "k INTEGER,flag INTEGER", "b": "k INTEGER,j INTEGER,w INTEGER",
              "c": "j INTEGER,flag INTEGER"}
    try:
        for table in ("a", "b", "c"):
            create = f"CREATE TABLE {table}({schema[table]})"
            insert = f"INSERT INTO {table} VALUES ({','.join('?' for _ in rows[table][0])})"
            db.execute(create); checker.execute(create)
            db.executemany(insert, rows[table]); checker.executemany(insert, rows[table])
        for table, columns in (("a", "k,flag"), ("b", "k,j,w"), ("b", "j,k,w"),
                               ("c", "j,flag")):
            checker.execute(f"CREATE INDEX idx_{table}_{columns.replace(',', '_')} "
                            f"ON {table}({columns})")
        checker.commit(); checker.execute("ANALYZE"); db.execute("ANALYZE")
    except Exception:
        db.close(); checker.close()
        raise
    return db, checker


def observe(db, checker, spec, policy):
    start, stages, answer, reference, error = perf_counter_ns(), {}, None, None, None
    sql, reference_sql = None, original_sql(spec["threshold"])
    try:
        begin = perf_counter_ns()
        forced = policy.startswith("order_")
        if policy == "native": sql = reference_sql
        elif policy == "grouped_counts": sql = grouped_sql(spec["threshold"])
        elif policy in POLICIES: sql = original_sql(spec["threshold"], ORDERS[int(policy[-1])])
        else: raise ValueError("undeclared policy")
        stages["compile_ms"] = (perf_counter_ns() - begin) / 1e6
        begin = perf_counter_ns()
        timer = threading.Timer(TIMEOUT_S, db.interrupt)
        timer.daemon = True
        timer.start()
        try:
            db.execute("SET disabled_optimizers = 'join_order,build_side_probe_side'"
                       if forced else "SET disabled_optimizers = ''")
            answer = tuple(int(x) for x in db.execute(sql).fetchone())
        finally:
            timer.cancel(); timer.join()
            db.execute("SET disabled_optimizers = ''")
            stages["engine_control_execute_ms"] = (perf_counter_ns() - begin) / 1e6
        begin = perf_counter_ns()
        deadline = perf_counter() + TIMEOUT_S
        checker.set_progress_handler(lambda: int(perf_counter() >= deadline), 1000)
        try:
            reference = tuple(int(x) for x in checker.execute(reference_sql).fetchone())
        finally:
            checker.set_progress_handler(None, 0)
            stages["independent_original_check_ms"] = (perf_counter_ns() - begin) / 1e6
        if answer != reference: raise ValueError("exact original-query answer mismatch")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {"case_id": spec["id"], "policy": policy, "sql": sql,
            "reference_sql": reference_sql, "answer": answer, "reference": reference,
            "accepted_exact": error is None and answer is not None and answer == reference,
            "error": error, **stages, "total_ms": (perf_counter_ns() - start) / 1e6}


def summarize(records):
    expected = {(s["id"], p, i) for s in specifications()
                for p in POLICIES for i in range(REPEATS)}
    seen = set()
    for r in records:
        identity = (r["case_id"], r["policy"], r["repeat"])
        if type(r["repeat"]) is not int or identity not in expected or identity in seen:
            raise ValueError("observation coverage/identity error")
        seen.add(identity)
    if seen != expected: raise ValueError("all 216 timed observations required")
    if not all(r["accepted_exact"] for r in records):
        return {"decision": "CAPABILITY_UNREACHED", "observations": len(records),
                "accepted_exact": sum(r["accepted_exact"] for r in records),
                "speed_ratio": None, "q3": "OPEN", "q4": "OPEN"}
    cells = []
    for spec in specifications():
        values = {p: median(r["total_ms"] for r in records
                            if r["case_id"] == spec["id"] and r["policy"] == p)
                  for p in POLICIES}
        cells.append({"case_id": spec["id"], "total_medians_ms": values,
                      "nondeployable_oracle_ms": min(values.values()),
                      "median_check_ms": median(r["independent_original_check_ms"]
                                                for r in records if r["case_id"] == spec["id"])})
    fixed_means = {p: mean(c["total_medians_ms"][p] for c in cells)
                   for p in ("native", "grouped_counts")}
    strongest = min(fixed_means, key=fixed_means.get)
    ratio = mean(c["nondeployable_oracle_ms"] for c in cells) / fixed_means[strongest]
    wins = sum(c["nondeployable_oracle_ms"] <= .8 * c["total_medians_ms"][strongest]
               for c in cells)
    admit = ratio <= .8 and wins >= 4
    return {"decision": "HEADROOM_REQUIRES_MATURE_BASELINE_COMPARISON" if admit
            else "REJECT_BOUNDED_RELATIONAL_PLANNER_TRAINING", "observations": len(records),
            "accepted_exact": len(records), "strongest_fixed_direct": strongest,
            "fixed_mean_of_case_medians_ms": fixed_means,
            "nondeployable_zero_model_oracle_ratio": ratio, "twenty_percent_win_cases": wins,
            "cells": cells, "q3": "OPEN", "q4": "OPEN"}


def run_audit():
    specs, rows, setups, warmups = specifications(), [], [], []
    for spec in specs:
        begin = perf_counter_ns()
        inputs = relations(spec)
        db, checker = build(inputs)
        setups.append({**spec, "setup_ms": (perf_counter_ns() - begin) / 1e6,
                       "table_sha256": {k: digest(v) for k, v in inputs.items()}})
        try:
            for policy in POLICIES:
                warmups.append(observe(db, checker, spec, policy))
            schedule = [(p, i) for p in POLICIES for i in range(REPEATS)]
            random.Random(ORDER_SEED + spec["seed"]).shuffle(schedule)
            for policy, repeat in schedule:
                rows.append({**observe(db, checker, spec, policy), "repeat": repeat})
        finally:
            db.close(); checker.close()
    summary = summarize(rows)
    if not all(w["accepted_exact"] for w in warmups):
        summary = {"decision": "CAPABILITY_UNREACHED", "warmup_failure": True,
                   "speed_ratio": None, "q3": "OPEN", "q4": "OPEN"}
    return {"experiment": "v0.0.80 constructed relational headroom", "summary": summary,
            "versions": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
                         "duckdb": DUCKDB_VERSION}, "platform": platform.platform(),
            "protocol": {"repeats": REPEATS, "order_seed": ORDER_SEED,
                         "timeout_s": TIMEOUT_S}, "setup": setups, "warmups": warmups,
            "rows": rows, "source": "Author-generated opened development data; no model training."}


def validate_archive(report: dict) -> None:
    """Post-audit archive completeness check; does not rerun the timed audit."""
    def milliseconds(value):
        return type(value) in (float, int) and isfinite(value) and value >= 0
    specs = specifications()
    expected = {(s["id"], p, i) for s in specs for p in POLICIES for i in range(REPEATS)}
    if report["protocol"] != {"repeats": REPEATS, "order_seed": ORDER_SEED,
                              "timeout_s": TIMEOUT_S}:
        raise ValueError("protocol drift")
    if report["versions"]["duckdb"] != DUCKDB_VERSION:
        raise ValueError("engine drift")
    seen, answers = set(), {}
    for r in report["rows"]:
        if type(r["repeat"]) is not int:
            raise ValueError("invalid repeat")
        key = (r["case_id"], r["policy"], r["repeat"])
        if key not in expected or key in seen:
            raise ValueError("duplicate or unexpected record")
        seen.add(key)
        if type(r["accepted_exact"]) is not bool:
            raise ValueError("invalid capability flag")
        if r["accepted_exact"] != (r["error"] is None and r["answer"] is not None
                                    and r["answer"] == r["reference"]):
            raise ValueError("contradictory verification result")
        if r["accepted_exact"]:
            if (len(r["answer"]) != 2 or any(type(x) is not int or x < 0 for x in r["answer"])
                    or answers.setdefault(r["case_id"], r["answer"]) != r["answer"]):
                raise ValueError("answer/domain drift")
        times = [r[k] for k in ("compile_ms", "engine_control_execute_ms",
                                "independent_original_check_ms") if k in r]
        if (not all(milliseconds(t) for t in times) or not milliseconds(r["total_ms"])
                or r["total_ms"] < sum(times)
                or (r["accepted_exact"] and len(times) != 3)):
            raise ValueError("missing or invalid charged cost")
    if seen != expected:
        raise ValueError("incomplete timed archive")
    warm_expected = {(s["id"], p) for s in specs for p in POLICIES}
    warm_ids = [(r["case_id"], r["policy"]) for r in report["warmups"]]
    if len(warm_ids) != len(warm_expected) or set(warm_ids) != warm_expected:
        raise ValueError("warmup coverage drift")
    setups = report["setup"]
    if len(setups) != len(specs) or {s["id"] for s in setups} != {s["id"] for s in specs}:
        raise ValueError("setup coverage drift")
    by_id = {s["id"]: s for s in specs}
    for setup in setups:
        spec = by_id[setup["id"]]
        if any(setup[k] != v for k, v in spec.items()) or not milliseconds(setup["setup_ms"]):
            raise ValueError("setup specification drift")
        if setup["table_sha256"] != {k: digest(v) for k, v in relations(spec).items()}:
            raise ValueError("source identity drift")
    expected_summary = summarize(report["rows"])
    if not all(w["accepted_exact"] for w in report["warmups"]):
        expected_summary = {"decision": "CAPABILITY_UNREACHED", "warmup_failure": True,
                            "speed_ratio": None, "q3": "OPEN", "q4": "OPEN"}
    if report["summary"] != expected_summary:
        raise ValueError("summary drift")
