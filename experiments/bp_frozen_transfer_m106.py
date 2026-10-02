"""First frozen EXPAND4 transfer to new constructed basis-pursuit LPs.

No oracle labels, no fitting, no new checkpoint. Serial isolated workers.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
from time import perf_counter_ns

from experiments.q5_register import evidence_module, parent_authority, preflight
from experiments.q5_evaluate import Worker as ReceiptWorker
from experiments.q5_transfer_admission import decode_source, query as direct_query

ROUTES = ("NATIVE", "IPM", "EXPAND4_s100001", "EXPAND4_s100002")


def ms(start): return (perf_counter_ns() - start) / 1e6


def specs():
    return [{"id": "m106_bp_k%d_r%d" % (k, r), "family": "basis_pursuit", "level": k,
             "rows": 2*k, "cols": 32*k, "seed": 106300 + 4*i + r}
            for i,k in enumerate((8,16,32,64)) for r in range(4)]


def protocol():
    return {"schema": "neumann.bp-frozen-transfer.m106.v1", "specs": specs(),
            "routes": list(ROUTES), "model_seeds": [100001,100002], "budget_s": 5.,
            "warmups": 1, "timed_repeats": 3, "observations": 256,
            "amortization_queries": 10000, "new_fitting": False, "oracle_access": False,
            "same_lp_backend": True, "global_questions_closed": []}


def schedule():
    warm = [(s["id"],r,"warmup",0) for s in specs() for r in ROUTES]
    timed = [(s["id"],r,"timed",i) for i in range(3) for s in specs() for r in ROUTES]
    rng = random.Random(106300); rng.shuffle(warm); rng.shuffle(timed)
    return warm + timed


def generate(spec):
    if spec not in specs(): raise ValueError("unregistered M106 source")
    import numpy as np
    rng = np.random.default_rng(spec["seed"])
    X = rng.normal(size=(spec["rows"],spec["cols"]//2))
    X /= np.linalg.norm(X,axis=0)
    beta = np.zeros(spec["cols"]//2)
    positions = rng.choice(len(beta), max(2,spec["rows"]//8), replace=False)
    beta[positions] = rng.normal(size=len(positions))
    return {"A":np.concatenate((X,-X),axis=1), "b":X@beta, "c":np.ones(spec["cols"])}


def query(directory, entry, route, models):
    if route in ("NATIVE", "IPM"):
        result = direct_query(directory, entry, route)
        result["ranking"] = None
        return result
    ev = evidence_module(); start = perf_counter_ns()
    execution = witness = error = ranking = None; proposal_ms = 0.
    try:
        source = ev.unpack_case(directory, entry["identity"])
        if set(source) != {"metadata", "arrays", "input_sha256"}:
            raise ValueError("privileged label fields forbidden")
        raw = decode_source(source,entry["metadata"])
        from experiments.lp_frozen_support_expansion_v101 import frozen_ranking, expand4_checked
        ranking, proposal_ms = frozen_ranking(raw,models[int(route.split("s")[-1])])
        left = 5 - ms(start)/1000
        if left <= 0: raise TimeoutError("discovery exhausted complete budget")
        execution = expand4_checked(raw,ranking,left)
        witness = execution["witness"]
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    total = ms(start)
    return {"accepted":bool(error is None and execution and execution["accepted"] and total<=5000),
            "execution":execution, "witness":witness, "error":error, "ranking":ranking,
            "total_ms":total, "worker_total_ms":total, "proposal_ms":proposal_ms,
            "post_ms":total-proposal_ms, "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def worker(directory, route):
    if route not in ROUTES: raise ValueError("unregistered worker")
    import numpy, scipy.linalg, scipy.optimize
    from neumann1 import lp_native_warm_start_v086
    from threadpoolctl import threadpool_limits
    with threadpool_limits(1):
        env = preflight(); models = {}; training = {}
        if route.startswith("EXPAND4"):
            from experiments.lp_frozen_support_expansion_v101 import restore_frozen_quotient
            models, training = restore_frozen_quotient()
        manifest = json.loads((Path(directory)/"sources.json").read_text())
        if manifest["protocol"] != protocol(): raise ValueError("worker source contract drift")
        entries = {e["metadata"]["id"]:e for e in manifest["cases"]}
        print(json.dumps({"ready":True,"route":route,"environment":env,"training":training}),flush=True)
        for line in sys.stdin:
            request = json.loads(line)
            if request == {"stop":True}: return
            print(json.dumps(query(directory,entries[request["case_id"]],route,models),allow_nan=False),flush=True)


class Worker(ReceiptWorker):
    def __init__(self,directory,route,authority_ms):
        self.stderr = (Path(directory)/(route+".stderr.log")).open("xb")
        began = perf_counter_ns()
        self.process = subprocess.Popen([sys.executable,"-m","experiments.bp_frozen_transfer_m106",
            "--worker",route,"--directory",str(directory)],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=self.stderr,text=True,bufsize=1)
        try: self.ready = self.receive(timeout_s=60)
        except BaseException: self.close(); raise
        if self.ready.get("ready") is not True or self.ready["route"] != route:
            self.close(); raise ValueError("worker readiness drift")
        self.cold_ms = ms(began) + (authority_ms if route.startswith("EXPAND4") else 0.)


def validate(directory, manifest, records):
    from experiments.q5_replay import certificate, native_checked, expansion_checked, check_cost
    ev = evidence_module()
    if manifest["protocol"] != protocol() or [e["metadata"] for e in manifest["cases"]] != specs():
        raise ValueError("source coverage/contract drift")
    if len(records) != 256 or [(r["case_id"],r["route"],r["phase"],r["repeat"]) for r in records] != schedule():
        raise ValueError("ordered observations missing or replaced")
    for entry in manifest["cases"]:
        source = ev.unpack_case(directory,entry["identity"])
        if set(source) != {"metadata","arrays","input_sha256"}: raise ValueError("oracle leakage")
        raw = decode_source(source,entry["metadata"])
        for r in (r for r in records if r["case_id"] == entry["metadata"]["id"]):
            for key in ("total_ms","worker_total_ms","proposal_ms","post_ms","transport_and_receipt_ms"):
                ev.finite_ms(r[key])
            check_cost(r["total_ms"],r["worker_total_ms"])
            if not math.isclose(r["total_ms"],r["worker_total_ms"]+r["transport_and_receipt_ms"],rel_tol=1e-12):
                raise ValueError("transport discarded")
            if not math.isclose(r["total_ms"],r["proposal_ms"]+r["post_ms"],rel_tol=1e-12):
                raise ValueError("discovery cost discarded")
            ex = r["execution"]; accepted = False
            if ex is not None:
                check_cost(r["worker_total_ms"]-r["proposal_ms"],ex["total_ms"])
                if r["route"] == "NATIVE":
                    if r["ranking"] is not None or r["proposal_ms"] != 0: raise ValueError("Direct proposer")
                    native_checked(raw,ex); expected = ex["attempts"][-1]["witness"]
                elif r["route"] == "IPM":
                    if (r["ranking"] is not None or r["proposal_ms"] != 0 or ex["method"] != "highs-ipm"
                        or ex["linprog_calls"] != 1 or not 0<ex["budget_s"]<=5): raise ValueError("IPM rights")
                    if ex["accepted"] != certificate(raw,ex["witness"],ex["certificate"]): raise ValueError("IPM acceptance")
                    check_cost(ex["total_ms"],ex["solve_ms"]+ex["verify_ms"]); expected = ex["witness"]
                else:
                    expansion_checked(raw,ex,r["ranking"],5000-r["proposal_ms"])
                    expected = ex["witness"]
                if expected != r["witness"]: raise ValueError("witness substitution")
                accepted = bool(r["error"] is None and ex["accepted"] and certificate(raw,r["witness"],None) and r["total_ms"]<=5000)
            if type(r["accepted"]) is not bool or r["accepted"] != accepted:
                raise ValueError("original-task acceptance drift")
    return records


def summarize(records, cold, training):
    if len(records) != 256: raise ValueError("partial observation set")
    cells = []
    for spec in specs():
        costs = {}
        for route in ROUTES:
            rows = [r for r in records if r["case_id"]==spec["id"] and r["route"]==route]
            timed = [r["total_ms"] for r in rows if r["phase"]=="timed"]
            if len(rows)!=4 or len(timed)!=3: raise ValueError("route coverage")
            invest = 0.
            if route.startswith("EXPAND4"):
                row = training[str(int(route.split("s")[-1]))]
                invest = row["feature_setup_ms"] + row["fit_ms"]
            costs[route] = {"capability":all(r["accepted"] for r in rows),
                            "p50_ms":statistics.median(timed),
                            "amortized_ms":statistics.median(timed)+(cold[route]+invest)/10000,
                            "cold_q1_ms":statistics.median(timed)+cold[route]+invest}
        direct = min(costs[r]["amortized_ms"] for r in ("NATIVE","IPM"))
        ratios = {r:(costs[r]["amortized_ms"]/direct if all(c["capability"] for c in costs.values()) else None)
                  for r in ROUTES[2:]}
        cells.append({"id":spec["id"],"level":spec["level"],"costs":costs,"ratios":ratios})
    decisions = {}
    for route in ROUTES[2:]:
        passed = True
        for level in (8,16,32,64):
            values = [c["ratios"][route] for c in cells if c["level"]==level]
            passed = passed and all(v is not None for v in values)
            if all(v is not None for v in values):
                passed = passed and statistics.median(values) <= (1.2 if level==8 else .8)
                if level != 8: passed = passed and sum(v<=.8 for v in values)>=3
        decisions[route] = "BOUNDED_TRANSFER_PASS" if passed else "STOP_FROZEN_TRANSFER_NO_REFIT"
    return {"cells":cells,"decisions":decisions,"joint_pass":all(v=="BOUNDED_TRANSFER_PASS" for v in decisions.values()),
            "global_questions_closed":[],"computational_cross_domain":False,"natural_problem_transfer":False,
            "direct_envelope":"best per-source NATIVE/IPM; optimistic diagnostic, not deployed router"}


def execute(directory, head):
    ev = evidence_module(); attempt = ev.Attempt(directory,"m106_bp_transfer_first",head)
    workers,records,entries,cold = {},[],[],{}
    try:
        from threadpoolctl import threadpool_limits
        from neumann1 import lp_portfolio_v084 as storage
        with threadpool_limits(1):
            env = preflight(); authority_start = perf_counter_ns()
            authority,training = parent_authority(); authority_ms = ms(authority_start)
            attempt.append("preflight",{"environment":env,"protocol":protocol(),"training":training})
            for spec in specs():
                raw = generate(spec)
                source = {"metadata":spec,"arrays":{k:storage.encode_array(v) for k,v in raw.items()},
                          "input_sha256":storage.input_digest(raw)}
                identity = ev.pack_case(directory,spec["id"]+".json.gz",source)
                entry = {"metadata":spec,"identity":identity}; entries.append(entry); attempt.append("source",entry)
            manifest = {"protocol":protocol(),"frozen_head":head,"cases":entries,"environment":env,
                        "training_identity":training,"authority_gzip_sha256":authority["gzip_sha256"]}
            ev.write_json(Path(directory)/"sources.json",manifest)
            attempt.append("sources_frozen",{"manifest_sha256":ev.digest(ev.canonical(manifest))})
        for route in ROUTES:
            workers[route] = Worker(directory,route,authority_ms)
            cold[route] = workers[route].cold_ms
            if route.startswith("EXPAND4") and workers[route].ready["training"] != {str(k):v for k,v in training.items()}:
                raise ValueError("frozen training identity drift")
            attempt.append("cold",{"route":route,"cold_ms":cold[route],"ready":workers[route].ready})
        attempt.append("timing_window_start",{"serial":True,"order":schedule()})
        for case_id,route,phase,repeat in schedule():
            attempt.append("observation_start",{"case_id":case_id,"route":route,"phase":phase,"repeat":repeat})
            r = workers[route].observe(case_id)
            r.update({"case_id":case_id,"route":route,"phase":phase,"repeat":repeat})
            records.append(r); attempt.append("observation",r)
        for w in workers.values(): w.close()
        attempt.append("timing_window_end",{"observations":len(records)})
        with threadpool_limits(1): validate(directory,manifest,records)
        summary = summarize(records,cold,{str(k):v for k,v in training.items()})
        report = {"protocol":protocol(),"summary":summary,"cold_ms":cold,"frozen_head":head,
                  "training_identity":training,"records":records,"sources_sha256":ev.digest(ev.canonical(manifest)),
                  "new_fitting":False,"oracle_access":False}
        ev.write_json(Path(directory)/"report.json",report)
        ev.write_json(Path(directory)/"summary.json",summary)
        attempt.finish("completed",observations=len(records),report_sha256=ev.digest(ev.canonical(report)))
        print(json.dumps(summary))
        return report
    except BaseException as exc:
        for w in workers.values(): w.close()
        attempt.finish("failed_no_replacement",source_views=len(entries),observations=len(records),error=type(exc).__name__+": "+str(exc))
        raise


def replay(directory):
    """Replay retained bytes and original certificates; no generator/model/solver."""
    ev = evidence_module(); directory = Path(directory)
    events, terminal = ev.read_events(directory)
    report = json.loads((directory/"report.json").read_text())
    manifest = json.loads((directory/"sources.json").read_text())
    if (terminal["status"] != "completed" or terminal["observations"] != 256
        or report["protocol"] != protocol() or report["new_fitting"] is not False
        or report["oracle_access"] is not False
        or terminal["report_sha256"] != ev.digest(ev.canonical(report))
        or report["sources_sha256"] != ev.digest(ev.canonical(manifest))):
        raise ValueError("retained first transfer authority drift")
    _,training = parent_authority()
    if report["training_identity"] != {str(k):v for k,v in training.items()}:
        raise ValueError("checkpoint authority drift")
    observed = [e["payload"] for e in events if e["kind"] == "observation"]
    if observed != report["records"]: raise ValueError("event/report replacement")
    from threadpoolctl import threadpool_limits
    with threadpool_limits(1):
        validate(directory,manifest,observed)
    summary = summarize(observed,report["cold_ms"],report["training_identity"])
    if summary != report["summary"] or summary != json.loads((directory/"summary.json").read_text()):
        raise ValueError("summary replacement")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--directory",required=True)
    parser.add_argument("--worker",choices=ROUTES); parser.add_argument("--frozen-head")
    parser.add_argument("--replay",action="store_true")
    args = parser.parse_args()
    if args.replay: print(json.dumps(replay(args.directory)))
    elif args.worker: worker(args.directory,args.worker)
    else:
        if not args.frozen_head: parser.error("--frozen-head required")
        execute(args.directory,args.frozen_head)
