"""FGSR: exact ORIGINAL RustHorn certificate with 27 fresh Z3 contexts.
Delete Python process restarts, never delete proof obligations. Scoped engineering only.
"""
from __future__ import annotations
import argparse
import ctypes as C
from ctypes.util import find_library
import importlib.util
import json
import pathlib
import subprocess
import sys
from time import perf_counter_ns

HERE = pathlib.Path(__file__).resolve().parent
CORE35 = HERE.parent / "core35-20261016" / "core35.py"


def load_original_module():
    if not CORE35.is_file():
        raise FileNotFoundError(f"Missing pinned parent engine: {CORE35}")
    spec = importlib.util.spec_from_file_location("core35_original_engine", CORE35)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def z3_version():
    lib = C.CDLL(find_library("z3"))
    lib.Z3_get_full_version.restype = C.c_char_p
    return lib.Z3_get_full_version().decode()


def resident_child():
    # Each check allocates and destroys its own native Z3 context.
    original = load_original_module()
    payload = json.load(sys.stdin)
    results = []
    for source in payload["clauses"]:
        tick = perf_counter_ns()
        verdict = original.native_evaluate(source)
        results.append({"verdict": verdict, "wall_ms": (perf_counter_ns()-tick)/1e6})
        if verdict not in ("sat", "unsat"):
            break
    print(json.dumps({"results": results, "z3": z3_version()}))


def single_process_batch(clauses, max_wall_s):
    tick = perf_counter_ns()
    try:
        cp = subprocess.run(
            [sys.executable, str(pathlib.Path(__file__).resolve()), "--resident-child"],
            input=json.dumps({"clauses": clauses}), capture_output=True, text=True,
            timeout=max_wall_s)
        result = json.loads(cp.stdout) if cp.returncode == 0 else {}
        rows = result.get("results", [])
        if len(rows) != len(clauses) or any(r["verdict"] not in ("sat","unsat") for r in rows):
            raise ValueError("resident incomplete or UNKNOWN")
        return {"status": "COMPLETE", "rows": rows, "z3": result["z3"],
                "wall_ms": (perf_counter_ns()-tick)/1e6,
                "hard_batch_cap_s": max_wall_s}
    except (subprocess.TimeoutExpired, ValueError, KeyError, json.JSONDecodeError):
        return {"status": "ABSTAIN", "rows": [],
                "wall_ms": (perf_counter_ns()-tick)/1e6,
                "hard_batch_cap_s": max_wall_s}


def old_per_clause_processes(original, clauses, each_cap_s):
    tick = perf_counter_ns()
    rows = [original.one(text, each_cap_s) for text in clauses]
    return {"status": "COMPLETE" if all(r["verdict"] in ("sat","unsat") for r in rows)
            else "ABSTAIN", "rows": rows,
            "wall_ms": (perf_counter_ns()-tick)/1e6,
            "per_clause_hard_cap_s": each_cap_s}


def run(cache, fetch_upstream, with_slow_reference=True):
    original = load_original_module()
    source = {key:original.get_source(key, cache, fetch_upstream)
              for key in ("safe","unsafe")}
    clauses = {key:list(original.clauses(source[key])) for key in source}
    poisoned = original.WITNESS.replace(
        '(+ (SUM (~cur<%Tree> p)) (SIZE (~cur<%Tree> p)))',
        '(SUM (~cur<%Tree> p))')
    if poisoned == original.WITNESS:
        raise ValueError("poison witness failed to mutate")
    poison_rule = list(original.clauses(source["safe"], poisoned))[1]
    queries = clauses["safe"] + clauses["unsafe"] + [poison_rule]
    assert len(clauses["safe"]) == len(clauses["unsafe"]) == 13
    assert len(queries) == 27
    resident = single_process_batch(queries, max_wall_s=112)
    prior = old_per_clause_processes(original, queries, each_cap_s=4) if with_slow_reference else None

    def verdicts(x):
        return [r["verdict"] for r in x["rows"]]

    v = verdicts(resident)
    expected = (len(v)==27 and v[:13]==["unsat"]*13
                and v[13:26].count("unsat")==12
                and v[13:26].count("sat")==1 and v[-1]=="sat")
    equal = (prior is not None and prior["status"]=="COMPLETE"
             and verdicts(prior)==v)
    ratio = prior["wall_ms"]/resident["wall_ms"] if equal and expected else None
    status = "CERTIFIED_REPLAY_EQUAL" if equal and expected else (
        "RESIDENT_ONLY_CERTIFIED" if expected and prior is None else "ABSTAIN")
    return {
        "study": "FGSR original-certificate process-boundary deletion",
        "status": status, "date": "2026-10-17", "global_Q1_Q7": "OPEN",
        "external_original": "chc-comp/rust-horn", "revision": original.REV,
        "source_identities": {k:{"sha256":original.CASES[k][2],
                                "git_blob":original.CASES[k][1]} for k in source},
        "original_clause_counts": {k: len(x) for k,x in clauses.items()},
        "same_Z3_native_evaluate": True, "fresh_Z3_context_per_clause_in_both_arms": True,
        "run_order": ["resident","one_process_per_clause"],
        "verification_verdicts":{"safe":v[:13],"unsafe":v[13:26],"poison":v[-1:]},
        "all_rules_checked":expected, "resident":resident, "per_clause_subprocess":prior,
        "equal_original_verdicts":equal,
        "scoped_process_wall_ratio_old_over_resident":ratio,
        "complete_cost_exclusions":["human source analysis","handwritten certificate",
                                    "upstream installation","training","cold dependency setup"],
        "scientific_limits": "One already-opened RustHorn source pair, posthoc human witness; "
            "process isolation and timeout granularity differ. No model/neural, "
            "frontier, end-to-end, or global Q4 result."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--resident-child",action="store_true")
    parser.add_argument("--cache",type=pathlib.Path,default=HERE/"external-source-cache")
    parser.add_argument("--fetch-upstream",action="store_true")
    parser.add_argument("--resident-only",action="store_true")
    parser.add_argument("--output",type=pathlib.Path,default=HERE/"first_receipt.json")
    args=parser.parse_args()
    if args.resident_child:
        resident_child()
        return
    rec=run(args.cache,args.fetch_upstream,not args.resident_only)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(rec,indent=2)+"\n")
    print(json.dumps({k:v for k,v in rec.items()
          if k not in ("resident","per_clause_subprocess","verification_verdicts")},indent=2))
    if rec["status"] not in ("CERTIFIED_REPLAY_EQUAL","RESIDENT_ONLY_CERTIFIED"):
        raise SystemExit(2)


if __name__=="__main__":
    main()
