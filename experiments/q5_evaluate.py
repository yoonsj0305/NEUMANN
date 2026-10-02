"""Explicit, serial, first-attempt Q5 whole-path evaluator.

Ordinary tests import this without launching processes or numerical execution.
CLI writes an atomic reservation before any imports/preflight/observations.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import select
import subprocess
import sys
from pathlib import Path
from time import perf_counter_ns

from experiments.q5_register import evidence_module, hardware, load_registered, parent_authority, preflight, validate_source


def elapsed_ms(start):
    return (perf_counter_ns() - start) / 1e6


def query(source_directory, entry, route, model=None):
    """Timer precedes disk read, decompression, digest and array decoding."""
    ev = evidence_module()
    start = perf_counter_ns()
    from neumann1.lp_native_warm_start_v086 import solve_native_checked
    from neumann1.lp_q34_support_v097 import restricted_original_checked
    proposal_ms = 0.0
    execution = ranking = witness = None
    error = None
    try:
        source = ev.unpack_case(source_directory, entry["identity"])
        raw = validate_source(source, entry["metadata"], oracle=False)
        left = ev.contract.protocol()["budget_s"] - elapsed_ms(start) / 1000.0
        if left <= 0:
            raise TimeoutError("input decoding exhausted complete budget")
        if route == "DIRECT":
            execution = solve_native_checked(**raw, cold_fallback=False, budget_s=left)
            witness = execution["attempts"][-1]["witness"] if execution["attempts"] else None
        elif route == "ORACLE":
            execution = restricted_original_checked(**raw, indices=source["label"]["indices"], budget_s=left)
            witness = execution["witness"]
        else:
            from experiments.lp_frozen_support_expansion_v101 import expand4_checked, frozen_ranking
            ranking, _ = frozen_ranking(raw, model)
            n = source["cols"]
            if (len(ranking) != n or set(ranking) != set(range(n))
                    or any(type(i) is not int for i in ranking)):
                raise ValueError("frozen ranking must be a full permutation")
            proposal_ms = elapsed_ms(start)  # includes ALL input read/decode/preprocessing
            left = ev.contract.protocol()["budget_s"] - proposal_ms / 1000.0
            if left > 0:
                execution = expand4_checked(raw, ranking, left)
                witness = execution["witness"]
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    total = elapsed_ms(start)
    if route.startswith("EXPAND4") and ranking is None:
        proposal_ms = total
    return {"accepted": bool(error is None and execution and execution["accepted"]
                             and total <= ev.contract.protocol()["budget_s"] * 1000),
            "proposal_ms": proposal_ms, "post_ms": total - proposal_ms,
            "total_ms": total, "worker_total_ms": total,
            "execution": execution, "ranking": ranking, "witness": witness,
            "error": error, "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def worker(source_directory, route):
    ev = evidence_module()
    if route not in ev.ROUTES:
        raise ValueError("unregistered Q5 route")
    from threadpoolctl import threadpool_limits
    # Legacy package/scientific imports are INSIDE externally timed launch.
    from neumann1 import lp_native_warm_start_v086  # noqa: F401
    model = None
    training = None
    with threadpool_limits(1):
        if route.startswith("EXPAND4"):
            import torch
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
            from experiments.lp_frozen_support_expansion_v101 import restore_frozen_quotient
            models, all_training = restore_frozen_quotient()
            seed = int(route.rsplit("s", 1)[1])
            model = models[seed]
            training = {str(k): v for k, v in all_training.items()}
            del models
        env = preflight()
        # Route-independent metadata preflight; complete parent replay is shared
        # and charged by the controller, not discarded as research overhead.
        authority_path = Path("docs/experiments/results/v102_first_evaluation.manifest.json")
        parent = json.loads(authority_path.read_text())
        manifest = load_registered(source_directory, verify=False)
        ev.contract.validate_authority(parent, training or manifest["training_identity"])
        entries = {e["metadata"]["id"]: e for e in manifest["cases"]}
        print(json.dumps({"ready": True, "route": route, "environment": env,
                          "training_identity": training,
                          "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)
        for line in sys.stdin:
            request = json.loads(line)
            if request == {"stop": True}:
                return
            entry = entries[request["case_id"]]
            record = query(source_directory, entry, route, model)
            print(json.dumps(record, allow_nan=False, separators=(",", ":")), flush=True)


class Worker:
    def __init__(self, directory, route, output, shared_authority_ms):
        self.stderr = (Path(output) / (route + ".stderr.log")).open("xb")
        started = perf_counter_ns()
        self.process = subprocess.Popen(
            [sys.executable, "-m", "experiments.q5_evaluate", "--worker", route, "--sources", str(directory)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
            text=True, bufsize=1)
        try:
            ready = self.receive(timeout_s=60.0)
        except BaseException:
            self.close()
            raise
        external = elapsed_ms(started)
        if ready.get("ready") is not True or ready.get("route") != route:
            self.close()
            raise RuntimeError("Q5 worker readiness drift")
        self.ready = ready
        self.cold = {"external_launch_ready_ms": external,
                     "shared_authority_preflight_ms": shared_authority_ms,
                     "cold_start_ms": external + shared_authority_ms,
                     "first_observation": True, "ready": ready}

    def receive(self, timeout_s):
        if not select.select([self.process.stdout], [], [], timeout_s)[0]:
            self.close()
            raise TimeoutError("Q5 worker receipt timeout; no replacement run")
        line = self.process.stdout.readline()
        if not line:
            self.close()
            raise RuntimeError("Q5 worker exited without complete receipt")
        return json.loads(line)

    def observe(self, case_id):
        start = perf_counter_ns()
        self.process.stdin.write(json.dumps({"case_id": case_id}, separators=(",", ":")) + "\n")
        self.process.stdin.flush()
        result = self.receive(timeout_s=60.0)
        total = elapsed_ms(start)
        # Charge request/response transport, including full failed-attempt ledger
        # serialization. This is a conservative retained-system cost, not FLOPs.
        result["transport_and_receipt_ms"] = total - result["worker_total_ms"]
        result["total_ms"] = total
        result["post_ms"] = total - result["proposal_ms"]
        result["accepted"] = bool(result["accepted"] and total <= evidence_module().contract.protocol()["budget_s"] * 1000)
        return result

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout, self.stderr):
            if not stream.closed:
                stream.close()


def evaluate(source_directory, output, frozen_head, expected_source_manifest_sha256):
    ev = evidence_module()
    attempt = ev.Attempt(output, "first_evaluation", frozen_head)
    workers, records, cold = {}, [], {}
    began = perf_counter_ns()
    try:
        manifest_path = Path(source_directory) / "manifest.json"
        # Required external pin: cannot swap the input archive under the executor.
        if ev.digest(manifest_path.read_bytes()) != expected_source_manifest_sha256:
            raise ValueError("Q5 registered manifest execution pin drift")
        authority_start = perf_counter_ns()
        parent, training = parent_authority()
        authority_ms = elapsed_ms(authority_start)
        from threadpoolctl import threadpool_limits
        with threadpool_limits(1):
            env = preflight()
            source_manifest = load_registered(source_directory)
        if (source_manifest["authority_gzip_sha256"] != parent["gzip_sha256"]
                or source_manifest["training_identity"] != {str(k): v for k, v in training.items()}):
            raise ValueError("Q5 source/parent training authority drift")
        attempt.append("preflight", {"environment": env, "source_manifest_sha256": expected_source_manifest_sha256,
                                    "authority_preflight_ms": authority_ms})
        # One runner; no source generation, replay, pytest or solver runs during
        # this window. Persistent workers are idle except the current request.
        timing_start = perf_counter_ns()
        attempt.append("timing_window_start", {"serial": True, "other_workflows_on_runner": False})
        for route in ev.ROUTES:
            attempt.append("cold_start_begin", {"route": route})
            cold_began = perf_counter_ns()
            try:
                instance = Worker(source_directory, route, output, authority_ms)
            except BaseException as exc:
                attempt.append("cold_start_failed", {"route": route, "elapsed_ms": elapsed_ms(cold_began),
                                                       "error": f"{type(exc).__name__}: {exc}"})
                raise
            workers[route] = instance
            if instance.ready["environment"]["hardware"] != env["hardware"]:
                raise RuntimeError("Q5 cross-route hardware drift")
            cold[route] = instance.cold
            attempt.append("cold_start", {"route": route, **instance.cold})
            if route.startswith("EXPAND4") and instance.ready["training_identity"] != {str(k): v for k, v in training.items()}:
                raise ValueError("Q5 restored training identity drift")
        for index, (case_id, route, repeat) in enumerate(ev.schedule()):
            attempt.append("query_start", {"case_id": case_id, "route": route, "repeat": repeat})
            record = {"case_id": case_id, "route": route, "repeat": repeat, **workers[route].observe(case_id)}
            records.append(record)
            identity = ev.pack_case(attempt.path, f"observation_{index:04d}.json.gz", record)
            attempt.append("observation", {"case_id": case_id, "route": route, "repeat": repeat, "identity": identity})
        for instance in workers.values():
            instance.close()
        workers.clear()
        attempt.append("timing_window_end", {"wall_ms": elapsed_ms(timing_start)})
        # Independent witness/ledger replay occurs AFTER every worker stops.
        from experiments.q5_replay import validate_records
        validated = validate_records(source_directory, records)
        summary = ev.summarize(validated, cold, {str(k): v for k, v in training.items()})
        report = {"schema": "neumann.q5-evaluation.v1", "frozen_head": frozen_head,
                  "source_manifest_sha256": expected_source_manifest_sha256,
                  "contract": ev.contract.protocol(), "environment": env,
                  "training_identity": {str(k): v for k, v in training.items()}, "cold": cold,
                  "summary": summary, "rerun": False,
                  "controller_wall_ms_including_research_replay": elapsed_ms(began),
                  "research_costs": "source labels retained in source cases; replay/retention wall disclosed separately",
                  "transport_receipts_charged": True, "cross_domain_pass": False, "global_q5_closed": False}
        ev.write_json(attempt.path / "report.json", report)
        attempt.finish("completed", report_sha256=ev.digest(ev.canonical(report)),
                       observations=len(records), decision=summary["decision"])
        return report
    except BaseException as exc:
        for instance in workers.values():
            instance.close()
        attempt.finish("evaluation_failed_no_replacement", observations=len(records),
                       error=f"{type(exc).__name__}: {exc}")
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=evidence_module().ROUTES)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--output")
    parser.add_argument("--frozen-head")
    parser.add_argument("--source-manifest-sha256")
    args = parser.parse_args()
    if args.worker:
        worker(args.sources, args.worker)
    else:
        if not args.output or not args.frozen_head or not args.source_manifest_sha256:
            parser.error("evaluation needs --output --frozen-head --source-manifest-sha256")
        report = evaluate(args.sources, args.output, args.frozen_head, args.source_manifest_sha256)
        print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
