"""Alternate opened native experiment: SyGuS pre/trans/post to Z3 Spacer CHC.

Runs native fixedpoint safety queries only; never claims to synthesize/certify
an independent original SyGuS invariant. Receipt records cannot close Q1-Q7.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from experiments.external_sygus_native_g0_20261009 import sexp_parse, to_smt

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/experiments/external_sygus_spacer_chc_g0_20261009.preregister.json"
SOURCES = ROOT / "third_party/sygus_benchmarks"
DEST = ROOT / "research/development/external_sygus_spacer_chc_g0_20261009"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def chc_from_sygus(source: str) -> tuple[str, dict]:
    """Preserve pre/trans/post term trees byte-semantically, add CHC reachability."""
    forms = sexp_parse(source)
    synths = [x for x in forms if isinstance(x, list) and len(x) >= 3 and x[0] == "synth-inv"]
    if len(synths) != 1 or synths[0][1] != "inv-f":
        raise ValueError("requires exactly one synth-inv inv-f")
    inputs = synths[0][2]
    if not inputs or not all(isinstance(x, list) and len(x) == 2 and x[1] == "Int" for x in inputs):
        raise ValueError("only declared integer state vectors supported")
    cur = [v[0] for v in inputs]
    if len(cur) != len(set(cur)):
        raise ValueError("duplicate state name")
    nxt = [n + "!" for n in cur]
    decls = {x[1]: x for x in forms if isinstance(x, list) and len(x) == 5 and x[0] == "define-fun"}
    if set(decls) != {"pre-f", "trans-f", "post-f"}:
        raise ValueError("unexpected benchmark function definitions")
    if [x[1] for x in decls["pre-f"][2]] != ["Int"] * len(cur):
        raise ValueError("pre-f argument sort drift")
    if [x[1] for x in decls["post-f"][2]] != ["Int"] * len(cur):
        raise ValueError("post-f argument sort drift")
    if [x[1] for x in decls["trans-f"][2]] != ["Int"] * (2 * len(cur)):
        raise ValueError("trans-f argument sort drift")

    allvars = cur + nxt
    decl_var_text = "\n".join("(declare-var " + name + " Int)" for name in allvars)
    type_sig = " ".join("Int" for _ in cur)
    a = " ".join(cur)
    b = " ".join(nxt)
    original_defs = "\n".join(to_smt(decls[n]) for n in ("pre-f", "trans-f", "post-f"))
    program = (
        "(set-logic HORN)\n" + original_defs + "\n"
        "(declare-rel Reach (" + type_sig + "))\n"
        "(declare-rel Bad ())\n" + decl_var_text + "\n"
        "(rule (=> (pre-f " + a + ") (Reach " + a + ")))\n"
        "(rule (=> (and (Reach " + a + ") (trans-f " + a + " " + b + ")) (Reach " + b + ")))\n"
        "(rule (=> (and (Reach " + a + ") (not (post-f " + a + "))) Bad))\n"
        "(query Bad)\n"
    )
    return program, {"state_vars":len(cur), "functions_kept":sorted(decls)}


def child(task_path: str) -> None:
    import z3
    raw = (SOURCES / task_path).read_bytes()
    program, meta = chc_from_sygus(raw.decode())
    config = json.loads(CONTRACT.read_text())
    if task_path not in config["selected_sources"]:
        raise RuntimeError("unregistered source not allowed")
    if z3.get_version_string() != config["z3_version"]:
        raise RuntimeError("Z3 version drift")
    fp = z3.Fixedpoint()
    fp.set(engine="spacer", timeout=config["deadline_ms"])
    time0 = time.perf_counter_ns()
    queries = fp.parse_string(program)
    if len(queries) != 1:
        raise RuntimeError(f"expected one CHC query, got {len(queries)}")
    prep_ms = (time.perf_counter_ns() - time0) / 1e6
    query0 = time.perf_counter_ns()
    try:
        verdict = str(fp.query(queries[0]))
        reason = fp.reason_unknown() if verdict == "unknown" else None
    except Exception as e:
        verdict = "Z3_QUERY_ERROR"
        reason = f"{type(e).__name__}: {e}"[:500]
    query_ms = (time.perf_counter_ns() - query0) / 1e6
    try:
        answer = str(fp.get_answer()) if verdict in {"sat", "unsat"} else ""
    except Exception as e:
        answer = "GET_ANSWER_ERROR: " + repr(e)
    result = {
        "status": "SAFE_BY_SPACER_UNSAT" if verdict == "unsat" else (
            "BAD_REACHABLE_SAT" if verdict == "sat" else "UNKNOWN_OR_ERROR"),
        "query_result": verdict, "reason": reason,
        "query_ms": query_ms, "parse_and_prepare_ms": prep_ms,
        "source_sha256": sha(raw), "chc_sha256": sha(program.encode()),
        "answer_sha256": sha(answer.encode()), "answer_sample":answer[:2000],
        "meta":meta,
        "critical_scope": "Z3 native CHC safety query; UNSAT proof is solver-authoritative and not independently checked as SyGuS inv-f candidate"
    }
    print(json.dumps(result, sort_keys=True), flush=True)


def orchestrate() -> None:
    config = json.loads(CONTRACT.read_text())
    if config["schema"] != "neumann.external-sygus-spacer-chc-native-screen.v1":
        raise RuntimeError("contract schema drift")
    head = subprocess.check_output(["git", "-C", str(SOURCES), "rev-parse", "HEAD"], text=True).strip()
    if head != config["sygus_source_commit"]:
        raise RuntimeError("upstream commit mismatch")
    DEST.mkdir(parents=True, exist_ok=True)
    records = []
    for k in range(config["repeats"]):
        paths = list(config["selected_sources"])
        random.Random(config["shuffle_seed"] + k).shuffle(paths)
        for task in paths:
            started = time.perf_counter_ns()
            ret, out, err, timed_out = None, "", "", False
            try:
                p = subprocess.run(
                    [sys.executable, "-m", "experiments.external_sygus_spacer_chc_g0_20261009", "--child", task],
                    capture_output=True, text=True, timeout=config["outer_deadline_s"])
                ret, out, err = p.returncode, p.stdout, p.stderr
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                out = ((exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""))
                err = ((exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""))
            wall_ms = (time.perf_counter_ns() - started) / 1e6
            if timed_out:
                payload = {"status":"OUTER_TIMEOUT"}
            elif ret != 0:
                payload = {"status":"WORKER_ERROR", "error":err[:1000]}
            else:
                try:
                    payload = json.loads(out.strip().splitlines()[-1])
                except Exception as exc:
                    payload = {"status":"INVALID_WORKER_RECEIPT", "error":repr(exc)}
            receipt = {"source": task, "repeat": k,
                       "source_sha256":sha((SOURCES / task).read_bytes()),
                       "solver_and_worker_wall_ms":wall_ms,
                       "worker_exit_code":ret,"timeout":timed_out,
                       "result":payload,"stdout":out[:4000],"stderr":err[:1500]}
            records.append(receipt)
            print("SPACER_CASE="+json.dumps({
                "source":task,"repeat":k,"status":payload["status"],
                "full_wall_ms":round(wall_ms,1)}),flush=True)
    group=defaultdict(list)
    for r in records:
        group[r["source"]].append(r)
    summary = {
        "status":"COMPLETE_OPENED_SPACER_NATIVE_ONLY",
        "source_commit":head, "contract_sha256":sha(CONTRACT.read_bytes()),
        "task_count":len(config["selected_sources"]),
        "record_count":len(records),"repeat_count":config["repeats"],
        "outcomes":dict(Counter(r["result"]["status"] for r in records)),
        "case_medians":{key:{"median_worker_included_ms":median(x["solver_and_worker_wall_ms"] for x in entries),
                            "outcomes":dict(Counter(x["result"]["status"] for x in entries)),
                            "source_sha256":entries[0]["source_sha256"]}
                        for key,entries in group.items()},
        "scope":"Only Z3 Spacer CHC safety; not an independently certified synthesized invariant or NEUMANN performance",
        "learning":False, "formal_approval":False, "no_global_Q_close":True
    }
    (DEST / "first_receipts.json").write_text(json.dumps({"summary":summary,"records":records},indent=2,sort_keys=True)+"\n")
    (DEST / "summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("SPACER_FIRST_SUMMARY="+json.dumps(summary,sort_keys=True),flush=True)


if __name__ == "__main__":
    try:
        if len(sys.argv)==3 and sys.argv[1]=="--child":
            child(sys.argv[2])
        elif len(sys.argv)==1:
            orchestrate()
        else:
            raise SystemExit("Invalid invocation")
    except Exception as exc:
        if len(sys.argv)==1:
            DEST.mkdir(parents=True,exist_ok=True)
            (DEST / "fatal.txt").write_text(repr(exc)+"\n")
        raise
