"""Explicit first new-family headroom audit; no model fit or inference."""
from __future__ import annotations

import argparse
import json
import math
import resource
import subprocess
import sys
from pathlib import Path
from time import perf_counter_ns
from unittest.mock import patch

from experiments import q5_transfer_contract as contract
from experiments.q5_register import evidence_module, preflight
from experiments.q5_evaluate import Worker as ReceiptWorker


def ms(start):
    return (perf_counter_ns() - start) / 1e6


def assignment_matrix(k):
    import numpy as np
    A = np.zeros((2*k-1, k*k))
    for i in range(k):
        A[i, i*k:(i+1)*k] = 1
    for j in range(k-1):
        A[k+j, j::k] = 1
    return A


def generate(spec):
    if spec not in contract.specs():
        raise ValueError("unregistered source specification")
    import numpy as np
    rng = np.random.default_rng(spec["seed"])
    k, m, n = spec["level"], spec["rows"], spec["cols"]
    if spec["family"] == "assignment":
        return {"A": assignment_matrix(k), "b": np.ones(m),
                "c": rng.integers(1, 10008, n).astype(float)}
    X = rng.normal(size=(m, n//2))
    X /= np.linalg.norm(X, axis=0)
    beta = np.zeros(n//2)
    positions = rng.choice(n//2, max(2, m//8), replace=False)
    beta[positions] = rng.normal(size=len(positions))
    return {"A": np.concatenate((X, -X), axis=1), "b": X @ beta, "c": np.ones(n)}


def oracle_support(witness, rows):
    """Offline exact primal support; a degenerate optimum need not have m entries."""
    indices = [i for i, value in enumerate(witness["x"]) if value != 0]
    if not 0 < len(indices) <= rows:
        raise ValueError("native optimum support outside frozen bound")
    return indices


def oracle_checked(raw, indices, known_y, budget_s):
    """Optimistic admission ceiling: free exact support AND dual, not deployable."""
    import numpy as np
    from neumann1.lp_native_warm_start_v086 import solve_native_checked
    from neumann1.lp_certificate_v081 import verify_standard_form_certificate
    start = perf_counter_ns()
    if (type(indices) is not list or len(indices) != len(set(indices))
            or not 0 < len(indices) <= raw["A"].shape[0]
            or any(type(i) is not int or not 0 <= i < raw["A"].shape[1] for i in indices)):
        raise ValueError("invalid exact oracle support")
    native = solve_native_checked(raw["A"][:,indices],raw["b"],raw["c"][indices],
                                  cold_fallback=False,budget_s=budget_s)
    witness = certificate = None
    if native["accepted"]:
        x=np.zeros(raw["A"].shape[1]);x[indices]=native["attempts"][-1]["witness"]["x"]
        witness={"x":x.tolist(),"y":list(known_y)}
    solve_ms=ms(start);check=perf_counter_ns()
    if witness is not None:
        certificate=verify_standard_form_certificate(**raw,**witness)
    verify_ms=ms(check);total=ms(start)
    return {"method":"free_exact_support_and_dual_ceiling","indices":indices,"native":native,
        "accepted":bool(native["accepted"] and certificate and certificate["accepted"] and total<=budget_s*1000),
        "witness":witness,"certificate":certificate,"solve_ms":solve_ms,"verify_ms":verify_ms,
        "total_ms":total,"budget_s":budget_s,"error":None}


def decode_source(source, spec):
    from neumann1 import lp_portfolio_v084 as storage
    shapes={"A":(spec["rows"],spec["cols"]),"b":(spec["rows"],),"c":(spec["cols"],)}
    raw = {k: storage.decode_array(v,shapes[k]) for k, v in source["arrays"].items()}
    if (source["metadata"] != spec or set(raw) != {"A", "b", "c"}
            or raw["A"].shape != (spec["rows"], spec["cols"])
            or storage.input_digest(raw) != source["input_sha256"]):
        raise ValueError("new-family original input identity drift")
    return raw


def assignment_checked(raw):
    """Specialized Direct receives only the same original A,b,c, never labels."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from neumann1.lp_certificate_v081 import verify_standard_form_certificate
    start = perf_counter_ns()
    k = math.isqrt(raw["A"].shape[1])
    if (k*k != raw["A"].shape[1] or raw["A"].shape[0] != 2*k-1
            or not np.array_equal(raw["A"], assignment_matrix(k))
            or not np.array_equal(raw["b"], np.ones(2*k-1))):
        raise ValueError("specialized Direct rejected assignment grammar")
    costs = raw["c"].reshape(k, k)
    rows, columns = linear_sum_assignment(costs)
    if not np.array_equal(rows, np.arange(k)):
        raise ValueError("assignment row coverage")
    weights = costs - costs[rows, columns][:, None]
    potential = np.zeros(k)
    stable = False
    # Difference constraints certify the optimizer's assignment independently.
    for _ in range(k):
        update = np.minimum(potential, np.min(weights + potential[columns][:, None], axis=0))
        if np.array_equal(update, potential):
            stable = True; break
        potential = update
    if not stable:
        raise ValueError("negative residual cycle or unstable matching certificate")
    potential -= potential[-1]
    u = costs[rows, columns] - potential[columns]
    x = np.zeros(k*k); x[rows*k + columns] = 1
    witness = {"x": x.tolist(), "y": np.concatenate((u, potential[:-1])).tolist()}
    solve_ms = ms(start)
    check = perf_counter_ns()
    certificate = verify_standard_form_certificate(**raw, **witness)
    return {"method": "scipy_assignment_plus_dual_difference_constraints", "witness": witness,
            "certificate": certificate, "accepted": bool(certificate["accepted"]),
            "solve_ms": solve_ms, "verify_ms": ms(check), "total_ms": ms(start),
            "error": None, "assignment_calls": 1}


def query(directory, entry, route):
    ev = evidence_module()
    start = perf_counter_ns()
    execution = witness = error = None
    try:
        source = ev.unpack_case(directory, entry["identity"])
        raw = decode_source(source, entry["metadata"])
        left = 5 - ms(start)/1000
        if left <= 0:
            raise TimeoutError("input decoding exhausted complete budget")
        if route == "NATIVE":
            from neumann1.lp_native_warm_start_v086 import solve_native_checked
            execution = solve_native_checked(**raw, cold_fallback=False, budget_s=left)
            witness = execution["attempts"][-1]["witness"]
        elif route == "ORACLE":
            execution = oracle_checked(raw,source["oracle"]["indices"],source["oracle"]["witness"]["y"],left)
            witness = execution["witness"]
        elif route == "ASSIGNMENT":
            execution = assignment_checked(raw); witness = execution["witness"]
        elif route == "IPM":
            from scipy.optimize import OptimizeWarning, linprog
            from neumann1.lp_certificate_v081 import verify_standard_form_certificate
            from warnings import catch_warnings, filterwarnings
            began = perf_counter_ns()
            with catch_warnings():
                filterwarnings("ignore", message="Unrecognized options detected:.*", category=OptimizeWarning)
                result = linprog(raw["c"], A_eq=raw["A"], b_eq=raw["b"], bounds=(0, None),
                    method="highs-ipm", options={"presolve": True, "threads": 1,
                        "parallel": False, "time_limit": left})
            solve_ms = ms(began); check = perf_counter_ns()
            witness = ({"x": result.x.tolist(), "y": result.eqlin.marginals.tolist()}
                       if result.success else None)
            cert = verify_standard_form_certificate(**raw, **witness) if witness else None
            execution = {"method": "highs-ipm", "accepted": bool(cert and cert["accepted"]),
                "witness": witness, "certificate": cert, "solver_status": int(result.status),
                "solve_ms": solve_ms, "verify_ms": ms(check), "total_ms": ms(began),
                "error": None, "linprog_calls": 1, "budget_s": left}
        else:
            raise ValueError("unregistered route")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    total = ms(start)
    return {"accepted": bool(error is None and execution and execution["accepted"] and total <= 5000),
        "execution": execution, "witness": witness, "error": error,
        "total_ms": total, "worker_total_ms": total, "proposal_ms": 0., "post_ms": total,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def worker(directory, route):
    from threadpoolctl import threadpool_limits
    if route not in {"NATIVE", "IPM", "ASSIGNMENT", "ORACLE"}:
        raise ValueError("unknown worker route")
    with threadpool_limits(1):
        env = preflight()
        manifest = json.loads((Path(directory)/"sources.json").read_text())
        entries = {e["metadata"]["id"]: e for e in manifest["cases"]}
        print(json.dumps({"ready": True, "route": route, "environment": env}), flush=True)
        for line in sys.stdin:
            request = json.loads(line)
            if request == {"stop": True}:
                return
            entry = entries[request["case_id"]]
            if route not in contract.routes(entry["metadata"]["family"]):
                raise ValueError("route/family authority drift")
            print(json.dumps(query(directory, entry, route), allow_nan=False), flush=True)


class Worker(ReceiptWorker):
    def __init__(self, directory, route):
        self.stderr = (Path(directory)/(route+".stderr.log")).open("xb")
        start = perf_counter_ns()
        self.process = subprocess.Popen([sys.executable, "-m", "experiments.q5_transfer_admission",
            "--worker", route, "--directory", str(directory)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=self.stderr, text=True, bufsize=1)
        try:
            self.ready = self.receive(timeout_s=60)
        except BaseException:
            self.close(); raise
        self.cold_ms = ms(start)
        if self.ready.get("ready") is not True or self.ready["route"] != route:
            self.close(); raise ValueError("worker readiness")


def validate_records(directory, manifest, records):
    ev = evidence_module()
    from experiments.q5_replay import certificate, check_cost, native_checked
    if [e["metadata"] for e in manifest["cases"]] != contract.specs():
        raise ValueError("source metadata coverage")
    entries = {e["metadata"]["id"]: e for e in manifest["cases"]}
    for case_id, entry in entries.items():
        source = ev.unpack_case(directory, entry["identity"])
        raw = decode_source(source, entry["metadata"])
        native_checked(raw,source["native_label"])
        label_witness=source["native_label"]["attempts"][-1]["witness"]
        if (source["native_label"]["accepted"] is not True
                or source["oracle"]["accepted"] is not True
                or source["oracle"]["indices"]!=oracle_support(label_witness,entry["metadata"]["rows"])
                or source["oracle"]["witness"]["y"]!=label_witness["y"]):
            raise ValueError("free exact oracle authority drift")
        if not certificate(raw, source["oracle"]["witness"], source["oracle"]["certificate"]):
            raise ValueError("registered oracle witness rejected")
        for record in (r for r in records if r["case_id"] == case_id):
            if record["route"] not in contract.routes(entry["metadata"]["family"]):
                raise ValueError("record/family drift")
            check_cost(record["total_ms"], record["worker_total_ms"])
            for key in ("proposal_ms","post_ms","transport_and_receipt_ms"):
                ev.finite_ms(record[key])
            if (record["proposal_ms"]!=0 or record["post_ms"]!=record["total_ms"]
                    or type(record["accepted"]) is not bool
                    or type(record["peak_rss_kib"]) is not int or record["peak_rss_kib"]<=0):
                raise ValueError("complete cost/proposal/RSS authority drift")
            if not math.isclose(record["total_ms"], record["worker_total_ms"]+record["transport_and_receipt_ms"], rel_tol=1e-12):
                raise ValueError("transport cost discarded")
            execution = record["execution"]
            verified = False
            if execution is not None:
                check_cost(record["worker_total_ms"], execution["total_ms"])
                if record["route"] == "NATIVE":
                    native_checked(raw, execution)
                else:
                    check_cost(execution["total_ms"], sum(execution[k] for k in ("solve_ms", "verify_ms") if execution[k] is not None))
                    if record["route"] == "ORACLE" and execution["indices"] != source["oracle"]["indices"]:
                        raise ValueError("oracle label substitution")
                    if record["route"] == "ORACLE":
                        import numpy as np
                        if (execution["method"]!="free_exact_support_and_dual_ceiling"
                                or not 0<execution["budget_s"]<=5
                                or execution["native"]["budget_s"]!=execution["budget_s"]):
                            raise ValueError("oracle execution rights drift")
                        indices=execution["indices"]
                        small={"A":raw["A"][:,indices],"b":raw["b"],"c":raw["c"][indices]}
                        native_checked(small,execution["native"])
                        check_cost(execution["solve_ms"],execution["native"]["total_ms"])
                        if execution["witness"] is not None:
                            x=np.zeros(raw["A"].shape[1]);x[indices]=execution["native"]["attempts"][-1]["witness"]["x"]
                            if (execution["witness"]["x"]!=x.tolist()
                                    or execution["witness"]["y"]!=source["oracle"]["witness"]["y"]):
                                raise ValueError("oracle reconstruction/dual drift")
                    if record["route"] == "IPM" and (execution["method"] != "highs-ipm" or execution["linprog_calls"] != 1 or not 0<execution["budget_s"]<=5):
                        raise ValueError("IPM rights drift")
                    if record["route"] == "ASSIGNMENT" and (execution["assignment_calls"] != 1 or execution["method"]!="scipy_assignment_plus_dual_difference_constraints"):
                        raise ValueError("assignment rights drift")
                inner_witness = (execution["attempts"][-1]["witness"] if record["route"] == "NATIVE" else execution["witness"])
                if inner_witness != record["witness"]:
                    raise ValueError("witness identity drift")
                retained = (execution["attempts"][-1]["certificate"] if record["route"] == "NATIVE"
                            else execution["certificate"])
                verified = certificate(raw, record["witness"], retained)
                expected=verified
                if record["route"]=="ORACLE":
                    expected=bool(verified and execution["native"]["accepted"] and execution["total_ms"]<=execution["budget_s"]*1000)
                if record["route"] != "NATIVE" and execution["accepted"] != expected:
                    raise ValueError("retained acceptance drift")
            accepted = bool(record["error"] is None and execution and execution["accepted"] and verified and record["total_ms"] <= 5000)
            if record["accepted"] != accepted:
                raise ValueError("complete capability drift")
            record["accounted"] = True
    return records


def run(directory, head):
    ev = evidence_module()
    attempt = ev.Attempt(directory, "v104_transfer_admission_first", head)
    workers, entries, records, cold = {}, [], [], {}
    began = perf_counter_ns()
    try:
        from threadpoolctl import threadpool_limits
        from neumann1 import lp_portfolio_v084 as storage
        from neumann1.lp_native_warm_start_v086 import solve_native_checked
        from experiments.q5_first_archive import source_pin, result_pin
        source_pin("docs/experiments/results/q5_first_sources")
        result_pin("docs/experiments/results/q5_first_evaluation")
        with threadpool_limits(1), patch("torch.nn.Module._call_impl", side_effect=AssertionError("no model admission")):
            env = preflight(); attempt.append("preflight", {"environment": env, "contract": contract.protocol()})
            for spec in contract.specs():
                raw = generate(spec)
                native = solve_native_checked(**raw, cold_fallback=False, budget_s=5.)
                label = None
                if native["accepted"]:
                    try:
                        witness=native["attempts"][-1]["witness"]
                        indices=oracle_support(witness,spec["rows"])
                        label=oracle_checked(raw,indices,witness["y"],5.)
                    except Exception as exc:
                        label = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}
                source = {"metadata": spec, "arrays": {k: storage.encode_array(v) for k,v in raw.items()},
                    "input_sha256": storage.input_digest(raw), "native_label": native, "oracle": label}
                identity = ev.pack_case(directory, spec["id"]+".json.gz", source)
                entry = {"metadata": spec, "identity": identity}; entries.append(entry)
                attempt.append("source", entry)
                if not native["accepted"] or not label or not label["accepted"]:
                    raise ValueError("first source label rejected; retain bytes, no reseed")
            manifest = {"schema": "neumann.v104-sources.v1", "frozen_head": head,
                "contract": contract.protocol(), "cases": entries, "environment": env,
                "model_access": False, "new_fitting": False, "rerun": False}
            ev.write_json(Path(directory)/"sources.json", manifest)
            attempt.append("sources_frozen", {"manifest_sha256": ev.digest(ev.canonical(manifest))})
        timing_start = perf_counter_ns(); attempt.append("timing_window_start", {"serial": True})
        for route in ("NATIVE", "IPM", "ASSIGNMENT", "ORACLE"):
            attempt.append("cold_start_begin", {"route": route})
            began_cold=perf_counter_ns()
            try:
                w=Worker(directory,route)
            except BaseException as exc:
                attempt.append("cold_start_failed",{"route":route,"elapsed_ms":ms(began_cold),"error":f"{type(exc).__name__}: {exc}"})
                raise
            workers[route] = w
            if w.ready["environment"]["hardware"] != env["hardware"]:
                raise ValueError("worker hardware drift")
            cold[route] = w.cold_ms
            attempt.append("cold_start", {"route": route, "cold_ms": w.cold_ms, "ready": w.ready})
        for index, (case_id, route, repeat) in enumerate(contract.schedule()):
            attempt.append("query_start", {"case_id": case_id, "route": route, "repeat": repeat})
            row = {"case_id": case_id, "route": route, "repeat": repeat, **workers[route].observe(case_id)}
            records.append(row)
            identity = ev.pack_case(directory, f"observation_{index:04d}.json.gz", row)
            attempt.append("observation", {"case_id": case_id, "route": route, "repeat": repeat, "identity": identity})
        for w in workers.values():
            w.close()
        workers.clear(); attempt.append("timing_window_end", {"wall_ms": ms(timing_start)})
        validated = validate_records(directory, manifest, records)
        summary = contract.summarize(validated, cold)
        report = {"schema": "neumann.v104-admission-result.v1", "frozen_head": head,
            "contract": contract.protocol(), "sources_sha256": ev.digest(ev.canonical(manifest)),
            "environment": env, "cold_ms": cold, "summary": summary, "rerun": False,
            "controller_wall_ms_including_research": ms(began)}
        ev.write_json(Path(directory)/"report.json", report)
        attempt.finish("completed", report_sha256=ev.digest(ev.canonical(report)), observations=len(records))
        return report
    except BaseException as exc:
        for w in workers.values():
            w.close()
        attempt.finish("failed_no_replacement", source_views=len(entries), observations=len(records), error=f"{type(exc).__name__}: {exc}")
        raise


def replay(directory):
    ev = evidence_module(); directory = Path(directory)
    events, terminal = ev.read_events(directory)
    report = json.loads((directory/"report.json").read_text())
    manifest = json.loads((directory/"sources.json").read_text())
    if (terminal["status"] != "completed" or terminal["observations"]!=448 or report["contract"] != contract.protocol()
            or manifest["contract"] != contract.protocol() or report["rerun"] is not False
            or report["sources_sha256"] != ev.digest(ev.canonical(manifest))
            or terminal["report_sha256"] != ev.digest(ev.canonical(report))):
        raise ValueError("first admission report contract/bytes drift")
    reservation=json.loads((directory/"reservation.json").read_text())
    if (manifest["frozen_head"]!=report["frozen_head"] or manifest["model_access"] is not False
            or manifest["rerun"] is not False or reservation!={"schema":"neumann.q5-attempt.v1",
                "stage":"v104_transfer_admission_first","frozen_head":report["frozen_head"],"rerun":False}
            or manifest["environment"]["runtime"]!=ev.RUNTIME):
        raise ValueError("first admission reservation/runtime drift")
    if [r["payload"] for r in events if r["kind"] == "source"] != manifest["cases"]:
        raise ValueError("source receipts changed")
    starts = [r["payload"] for r in events if r["kind"] == "query_start"]
    if [(r["case_id"],r["route"],r["repeat"]) for r in starts] != contract.schedule():
        raise ValueError("missing query receipts")
    kinds=[r["kind"] for r in events]
    if kinds.count("timing_window_start")!=1 or kinds.count("timing_window_end")!=1:
        raise ValueError("missing isolated timing window")
    a,b=kinds.index("timing_window_start"),kinds.index("timing_window_end")
    if kinds[a+1:b]!=([k for _ in range(4) for k in ("cold_start_begin","cold_start")]
                       +[k for _ in contract.schedule() for k in ("query_start","observation")]):
        raise ValueError("nonserial or missing timing ledger")
    cold_rows=[r["payload"] for r in events if r["kind"]=="cold_start"]
    if [r["route"] for r in cold_rows]!=["NATIVE","IPM","ASSIGNMENT","ORACLE"]:
        raise ValueError("cold first coverage")
    for row in cold_rows:
        env=row["ready"]["environment"]
        if (row["cold_ms"]!=report["cold_ms"][row["route"]]
                or env["hardware"]!=report["environment"]["hardware"] or env["runtime"]!=ev.RUNTIME
                or not env["threadpools"] or any(t["num_threads"]!=1 for t in env["threadpools"])):
            raise ValueError("cold startup/hardware/threads drift")
    records = []
    for event in events:
        if event["kind"] == "observation":
            pointer = event["payload"]; row = ev.unpack_case(directory, pointer["identity"])
            if any(row[k] != pointer[k] for k in ("case_id", "route", "repeat")):
                raise ValueError("observation identity")
            records.append(row)
    with patch("highspy.Highs.run", side_effect=AssertionError("no solve replay")), \
         patch("scipy.optimize.linprog", side_effect=AssertionError("no IPM replay")), \
         patch("scipy.optimize.linear_sum_assignment", side_effect=AssertionError("no assignment replay")), \
         patch("torch.nn.Module._call_impl", side_effect=AssertionError("no forward replay")), \
         patch(__name__+".generate", side_effect=AssertionError("no generation replay")):
        result = contract.summarize(validate_records(directory, manifest, records), report["cold_ms"])
    from experiments.q5_replay import equal
    if not equal(result, report["summary"]):
        raise ValueError("independent admission summary drift")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--directory", required=True)
    p.add_argument("--frozen-head")
    mode=p.add_mutually_exclusive_group()
    mode.add_argument("--worker")
    mode.add_argument("--replay", action="store_true")
    a = p.parse_args()
    if a.worker:
        worker(a.directory, a.worker)
    elif a.replay:
        print(json.dumps(replay(a.directory), sort_keys=True))
    else:
        report = run(a.directory, a.frozen_head)
        print(json.dumps({k:v for k,v in report["summary"].items() if k not in ("cases",)}, sort_keys=True))


if __name__ == "__main__":
    main()
