"""Q5 retained evidence replay: no models, fitting, solvers or new timing.

Structural accounting checks precede any cost/slope analysis. Replay cannot
prove absence of external contention; the frozen isolated workflow is part of
the provenance boundary. A missing/partial first receipt is not a new run.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from experiments.q5_register import evidence_module, load_registered, parent_authority, validate_source


def equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is float:
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    if isinstance(a, dict):
        return set(a) == set(b) and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def check_cost(outer, inner):
    ev = evidence_module()
    if ev.finite_ms(outer) + 1e-9 < ev.finite_ms(inner):
        raise ValueError("Q5 discarded/uncharged attempt cost")


def certificate(raw, witness, retained):
    from neumann1.lp_certificate_v081 import verify_standard_form_certificate
    if witness is None:
        if retained is not None:
            raise ValueError("Q5 certificate without witness")
        return False
    derived = verify_standard_form_certificate(**raw, **witness)
    if retained is not None:
        # Retained bytes pin ALL original numeric diagnostics. Independently
        # re-establish semantic acceptance, dimensions and default tolerance;
        # do not require roundoff-sensitive BLAS residuals to be byte-identical.
        fields = ("schema", "accepted", "numerical_finite", "rows", "cols", "nnz",
                  "atol", "rtol", "complementarity_diagnostic_only")
        if any(retained.get(k) != derived[k] for k in fields):
            raise ValueError("Q5 retained original certificate drift")
    return bool(derived["accepted"])


def native_checked(raw, result):
    ev = evidence_module()
    if type(result["accepted"]) is not bool or result["head_kind"] != "COLD" or result["fallback_used"] is not False:
        raise ValueError("Q5 Direct native authority drift")
    if len(result["attempts"]) != 1:
        raise ValueError("Q5 native attempt coverage drift")
    attempt = result["attempts"][0]
    if attempt["warm_start"] is not False or attempt["basis"] is not None:
        raise ValueError("Q5 unauthorized oracle/warm-start basis")
    stages = attempt["stages"]
    if any(s["stage"] not in ("model_setup", "native_solve", "original_verification") for s in stages):
        raise ValueError("Q5 undeclared native stage")
    names = [s["stage"] for s in stages]
    if names not in (["model_setup"], ["model_setup", "native_solve"],
                     ["model_setup", "native_solve", "original_verification"]):
        raise ValueError("Q5 missing/reordered native stages")
    check_cost(result["total_ms"], sum(ev.finite_ms(s["ms"]) for s in stages))
    ledger = attempt["ledger"]
    if (set(ledger) != {"native_run_calls", "set_basis_calls", "certificate_calls"}
            or any(type(v) is not int or v not in (0, 1) for v in ledger.values())
            or ledger["set_basis_calls"] != 0
            or ledger["certificate_calls"] != names.count("original_verification")
            or ledger["native_run_calls"] > names.count("native_solve")
            or (attempt["witness"] is not None and ledger["native_run_calls"] != 1)
            or result["ledger"] != ledger):
        raise ValueError("Q5 native execution ledger drift")
    verified = certificate(raw, attempt["witness"], attempt["certificate"])
    accepted = bool(attempt["error"] is None and attempt["certificate"] is not None and verified)
    if type(attempt["accepted"]) is not bool or attempt["accepted"] != accepted:
        raise ValueError("Q5 native witness acceptance drift")
    budget_ms = ev.finite_ms(result["budget_s"]) * 1000
    if (not 0 < budget_ms <= ev.contract.protocol()["budget_s"] * 1000
            or result["accepted"] != (accepted and result["total_ms"] <= budget_ms)):
        raise ValueError("Q5 native deadline acceptance drift")
    exceeded = result["total_ms"] > budget_ms
    status = "VERIFIED" if result["accepted"] else ("BUDGET_EXCEEDED" if exceeded else "REJECTED")
    if result["status"] != status:
        raise ValueError("Q5 native status drift")


def restricted_checked(raw, result, expected_indices):
    if result["indices"] != expected_indices:
        raise ValueError("Q5 restricted support identity drift")
    small = {"A": raw["A"][:, expected_indices], "b": raw["b"], "c": raw["c"][expected_indices]}
    native_checked(small, result["native"])
    check_cost(result["total_ms"], result["native"]["total_ms"])
    verified = certificate(raw, result["witness"], result["original_certificate"])
    if result["witness"] is not None:
        native_witness = result["native"]["attempts"][-1]["witness"]
        if native_witness is None or result["witness"]["y"] != native_witness["y"]:
            raise ValueError("Q5 dual witness reconstruction drift")
        x = [0.0] * len(raw["c"])
        for i, v in zip(expected_indices, native_witness["x"]):
            x[i] = v
        if result["witness"]["x"] != x:
            raise ValueError("Q5 primal witness reconstruction drift")
    budget_ms = result["native"]["budget_s"] * 1000
    accepted = bool(result["native"]["accepted"] and result["original_certificate"] is not None
                    and verified and result["total_ms"] <= budget_ms)
    if type(result["accepted"]) is not bool or result["accepted"] != accepted:
        raise ValueError("Q5 restricted deadline/certificate acceptance drift")


def expansion_checked(raw, execution, ranking, budget_ms=5000.0):
    m, n = raw["A"].shape
    if (type(ranking) is not list or len(ranking) != n or set(ranking) != set(range(n))
            or any(type(i) is not int for i in ranking)):
        raise ValueError("Q5 ranking is not a permutation")
    attempts = execution["attempts"]
    if not 1 <= len(attempts) <= 2:
        raise ValueError("Q5 support retry coverage drift")
    winner = None
    spent = 0.0
    for i, attempt in enumerate(attempts):
        factor = (2, 4)[i]
        size = min(n, factor * m)
        if attempt["support_factor"] != factor or attempt["support_size"] != size or winner is not None:
            raise ValueError("Q5 support expansion without verifier rejection")
        result = attempt["result"]
        restricted_checked(raw, result, ranking[:size])
        check_cost(budget_ms, spent + result["native"]["budget_s"] * 1000)
        spent += result["total_ms"]
        if result["accepted"]:
            winner = result["witness"]
    fallback = execution["fallback"]
    if fallback is not None:
        if winner is not None:
            raise ValueError("Q5 Direct fallback after accepted support")
        native_checked(raw, fallback)
        check_cost(budget_ms, spent + fallback["budget_s"] * 1000)
        if fallback["accepted"]:
            winner = fallback["attempts"][-1]["witness"]
    check_cost(execution["total_ms"], sum(a["result"]["total_ms"] for a in attempts)
               + (fallback["total_ms"] if fallback else 0))
    if (execution["witness"] != winner or execution["fallback_used"] is not (fallback is not None)
            or execution["subset_accepted"] is not any(a["result"]["accepted"] for a in attempts)
            or execution["expanded"] is not (len(attempts) == 2)
            or execution["expanded_accepted"] is not bool(len(attempts) == 2 and attempts[1]["result"]["accepted"])
            or type(execution["accepted"]) is not bool
            or execution["accepted"] != bool(winner is not None and execution["total_ms"] <= budget_ms)):
        raise ValueError("Q5 expansion retained decision drift")


def validate_record(raw, entry, record):
    ev = evidence_module()
    if type(record["accepted"]) is not bool:
        raise ValueError("Q5 acceptance type drift")
    for key in ("total_ms", "worker_total_ms", "proposal_ms", "post_ms", "transport_and_receipt_ms"):
        ev.finite_ms(record[key])
    if not math.isclose(record["total_ms"], record["proposal_ms"] + record["post_ms"], rel_tol=1e-12, abs_tol=1e-9):
        raise ValueError("Q5 complete stage accounting drift")
    if not math.isclose(record["total_ms"], record["worker_total_ms"] + record["transport_and_receipt_ms"], rel_tol=1e-12, abs_tol=1e-9):
        raise ValueError("Q5 external receipt accounting drift")
    check_cost(record["worker_total_ms"], record["proposal_ms"])
    if type(record["peak_rss_kib"]) is not int or record["peak_rss_kib"] <= 0:
        raise ValueError("Q5 missing descriptive RSS")
    route = record["route"]
    execution = record["execution"]
    if execution is not None:
        check_cost(record["worker_total_ms"] - record["proposal_ms"], execution["total_ms"])
        if route == "DIRECT":
            if record["proposal_ms"] != 0 or record["ranking"] is not None:
                raise ValueError("Q5 Direct receives no proposer")
            native_checked(raw, execution)
            expected_witness = execution["attempts"][-1]["witness"]
        elif route == "ORACLE":
            if record["proposal_ms"] != 0 or record["ranking"] is not None:
                raise ValueError("Q5 Oracle discovery is free diagnostic only")
            restricted_checked(raw, execution, entry["label"]["indices"])
            expected_witness = execution["witness"]
        else:
            expansion_checked(raw, execution, record["ranking"],
                              ev.contract.protocol()["budget_s"] * 1000 - record["proposal_ms"])
            expected_witness = execution["witness"]
        if record["witness"] != expected_witness:
            raise ValueError("Q5 record witness/attempt drift")
    elif record["witness"] is not None:
        raise ValueError("Q5 witness without execution")
    if record["accepted"] and not certificate(raw, record["witness"], None):
        raise ValueError("Q5 accepted original witness rejected")
    accepted = bool(record["error"] is None and execution and execution["accepted"]
                    and record["worker_total_ms"] <= ev.contract.protocol()["budget_s"] * 1000
                    and record["total_ms"] <= ev.contract.protocol()["budget_s"] * 1000)
    if record["accepted"] != accepted:
        raise ValueError("Q5 external complete deadline acceptance drift")
    return {**record, "accounted": True}


def validate_records(source_directory, records):
    ev = evidence_module()
    if [(r["case_id"], r["route"], r["repeat"]) for r in records] != ev.schedule():
        raise ValueError("Q5 observation schedule/coverage drift")
    manifest = load_registered(source_directory)
    validated = []
    # Only one decoded case in memory at once; no gigantic monolithic archive.
    for entry in manifest["cases"]:
        source = ev.unpack_case(source_directory, entry["identity"])
        raw = validate_source(source, entry["metadata"])
        for record in records:
            if record["case_id"] == source["id"]:
                validated.append(validate_record(raw, source, record))
    lookup = {(r["case_id"], r["route"], r["repeat"]): r for r in validated}
    return [lookup[key] for key in ev.schedule()]


def replay(source_directory, result_directory):
    ev = evidence_module()
    result_directory = Path(result_directory)
    rows, terminal = ev.read_events(result_directory)
    if terminal["status"] != "completed":
        raise ValueError("Q5 incomplete first attempt; no scientific verdict")
    report = json.loads((result_directory / "report.json").read_text())
    if (report["schema"] != "neumann.q5-evaluation.v1" or report["rerun"] is not False
            or report["contract"] != ev.contract.protocol() or report["cross_domain_pass"] is not False
            or report["global_q5_closed"] is not False or report["transport_receipts_charged"] is not True
            or terminal["report_sha256"] != ev.digest(ev.canonical(report))):
        raise ValueError("Q5 report receipt/contract drift")
    if (report["environment"]["runtime"] != ev.RUNTIME
            or report["environment"]["openblas_coretype"] != "HASWELL"
            or not report["environment"]["threadpools"]
            or any(p["num_threads"] != 1 for p in report["environment"]["threadpools"])):
        raise ValueError("Q5 report runtime/thread drift")
    reservation = json.loads((result_directory / "reservation.json").read_text())
    if reservation != {"schema": "neumann.q5-attempt.v1", "stage": "first_evaluation",
                        "frozen_head": ev.head_sha(report["frozen_head"]), "rerun": False}:
        raise ValueError("Q5 first execution reservation drift")
    if ev.digest((Path(source_directory) / "manifest.json").read_bytes()) != report["source_manifest_sha256"]:
        raise ValueError("Q5 retained registered manifest identity drift")
    _, training = parent_authority()
    if report["training_identity"] != {str(k): v for k, v in training.items()}:
        raise ValueError("Q5 replay training authority drift")
    cold_rows = [r["payload"] for r in rows if r["kind"] == "cold_start"]
    if [r["route"] for r in cold_rows] != list(ev.ROUTES):
        raise ValueError("Q5 first cold start coverage drift")
    for row in cold_rows:
        route = row["route"]
        if {k: v for k, v in row.items() if k != "route"} != report["cold"][route]:
            raise ValueError("Q5 cold start ledger drift")
        if (row["first_observation"] is not True
                or row["ready"]["environment"]["hardware"] != report["environment"]["hardware"]
                or row["ready"]["environment"]["runtime"] != ev.RUNTIME):
            raise ValueError("Q5 cold first/runtime/hardware drift")
        for key in ("cold_start_ms", "external_launch_ready_ms", "shared_authority_preflight_ms"):
            ev.finite_ms(row[key])
        if (not row["ready"]["environment"]["threadpools"]
                or any(p["num_threads"] != 1 for p in row["ready"]["environment"]["threadpools"])):
            raise ValueError("Q5 cold thread drift")
        if not math.isclose(row["cold_start_ms"], row["external_launch_ready_ms"] + row["shared_authority_preflight_ms"], rel_tol=1e-12):
            raise ValueError("Q5 cold authority cost omitted")
    kinds = [r["kind"] for r in rows]
    if kinds.count("timing_window_start") != 1 or kinds.count("timing_window_end") != 1:
        raise ValueError("Q5 isolated timing window drift")
    start, end = kinds.index("timing_window_start"), kinds.index("timing_window_end")
    if rows[start]["payload"] != {"serial": True, "other_workflows_on_runner": False}:
        raise ValueError("Q5 isolated serial runner declaration drift")
    if kinds[start+1:end] != ([kind for _ in ev.ROUTES for kind in ("cold_start_begin", "cold_start")]
                            + [kind for _ in ev.schedule() for kind in ("query_start", "observation")]):
        raise ValueError("Q5 serial timing ledger drift")
    starts = [r["payload"] for r in rows if r["kind"] == "query_start"]
    if [(r["case_id"], r["route"], r["repeat"]) for r in starts] != ev.schedule():
        raise ValueError("Q5 incomplete query receipts")
    records = []
    for row in rows:
        if row["kind"] == "observation":
            receipt = row["payload"]
            record = ev.unpack_case(result_directory, receipt["identity"])
            if any(record[k] != receipt[k] for k in ("case_id", "route", "repeat")):
                raise ValueError("Q5 per-observation receipt identity drift")
            records.append(record)
    validated = validate_records(source_directory, records)
    derived = ev.summarize(validated, report["cold"], report["training_identity"])
    if (not equal(derived, report["summary"]) or terminal["decision"] != derived["decision"]
            or terminal["observations"] != len(records)):
        raise ValueError("Q5 replay summary/decision drift")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True)
    parser.add_argument("--results", required=True)
    args = parser.parse_args()
    print(json.dumps(replay(args.sources, args.results)["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
