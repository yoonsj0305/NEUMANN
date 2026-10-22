"""Task source only pregrade, and completely separate original official grading."""
from __future__ import annotations
import argparse,collections,hashlib,importlib.util,json,pathlib,statistics,time,urllib.request
from reversible_ca_solver import published_zero_fill,solve,native_verify

ORIGINAL_REPO="neelsomani/automata-bench"
PIN="7d86373fdb63fe1bd3592ddf71d923ceebc5acd9"
SOLVERS=("zero_fill","z3_plain","propagation_sat")

def cpu_agg(series):
    return {"n":len(series),"total_cpu_s":sum(series),
            "median_cpu_ms":round(statistics.median(series)*1000,4) if series else None}

def infer(source):
    records={};counters=collections.Counter();timecost=collections.defaultdict(list)
    for line in pathlib.Path(source).read_text().splitlines():
        row=json.loads(line)
        assert "answer" not in row and "metadata" not in row
        uid=row["id"];assert uid not in records
        baseline=published_zero_fill(row)
        counters["n"]+=1
        predictions={"zero_fill":{"status":"ORIGINAL_PUBLISHED_ZERO_FILL",
                                   "prediction":baseline,"cpu_s":0}}
        # Alternate order to reduce any fixed caching/frequency skew.
        order=["z3_plain","propagation_sat"] if counters["n"]%2 else ["propagation_sat","z3_plain"]
        for name in order:
            method="plain" if name=="z3_plain" else "propagation"
            value=solve(row,policy=method)
            predictions[name]=value;timecost[name].append(value["cpu_s"])
            counters[name+"_status_"+value["status"]]+=1
            if value.get("prediction") is not None:
                assert native_verify(row,value["prediction"]),(uid,name)
        p=predictions["z3_plain"].get("prediction")
        q=predictions["propagation_sat"].get("prediction")
        if p is not None and q is not None:assert p==q,uid
        records[uid]={"predictions":predictions,"difficulty":row.get("difficulty","unknown"),
                      "observations":len(row["observations"])}
        if counters["n"]%50==0:print("EXTERNAL_SOURCE_ONLY_PROGRESS",counters["n"],dict(counters),flush=True)
    assert len(records)==counters["n"]
    report={"schema":"NEUMANN_AUTOMATABENCH_2D_SOURCE_ONLY.v1",
        "n":len(records),"original_public_repo":ORIGINAL_REPO,"source_rev":PIN,
        "query_answers_seen":False,"dataset_metadata_seen":False,"neural_training_used":False,
        "original_public_zero_fill_baseline_included":True,
        "source_cpu_cost":{key:cpu_agg(vals) for key,vals in timecost.items()},
        "statuses":dict(counters),"rows":records}
    print("NEUMANN_AUTOMATABENCH_SOURCE_ONLY_MODEL_COUNTS",json.dumps(report["statuses"],sort_keys=True),flush=True)
    print("NEUMANN_AUTOMATABENCH_SOURCE_ONLY_CPU",json.dumps(report["source_cpu_cost"],sort_keys=True),flush=True)
    return report

def official_verifier(repo_sha):
    url=f"https://raw.githubusercontent.com/{ORIGINAL_REPO}/{repo_sha}/automata_bench/verifier.py"
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"NEUMANN-independent-official-verifier/1.0"}),timeout=120) as resp:raw=resp.read()
    module_name="official_automata_bench_verifier_pinned"
    import types
    module=types.ModuleType(module_name)
    exec(compile(raw,"original_official_verifier.py","exec"),module.__dict__)
    return module.verify_initial_state,hashlib.sha256(raw).hexdigest()

def grade(sealed,official_rows,original_sha_expected):
    raw=pathlib.Path(official_rows).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==original_sha_expected
    frozen=pathlib.Path(sealed);before=json.loads(frozen.read_text())
    assert not before["query_answers_seen"] and not before["dataset_metadata_seen"]
    official_verify,verifier_sha=official_verifier(PIN)
    counters=collections.Counter();details={}
    timings=before["source_cpu_cost"]
    for line in raw.splitlines():
        row=json.loads(line);uid=row["id"];guess=before["rows"][uid]
        assert "answer" in row
        assert bool(official_verify(row,row["answer"])),"original benchmark reference itself invalid"
        counters["n"]+=1;difficulty=row["difficulty"]
        for method in SOLVERS:
            prediction=guess["predictions"][method].get("prediction")
            attempted=prediction is not None
            # Both official simulation consistency and included unique reference match required.
            correct=attempted and bool(official_verify(row,prediction)) and prediction==row["answer"]["initial_state"]
            counters[method+"_attempts"]+=int(attempted)
            counters[method+"_correct"]+=int(correct)
            counters[method+"_wrong"]+=int(attempted and not correct)
            counters[difficulty+"_"+method+"_correct"]+=int(correct)
            counters[difficulty+"_"+method+"_n"]+=1
        details[uid]={"difficulty":difficulty,
                      "policy_correct":{m:guess["predictions"][m].get("prediction") == row["answer"]["initial_state"] for m in SOLVERS},
                      "observations":len(row["observations"])}
    assert counters["n"]==len(details)==before["n"]
    efficiency={}
    for name in ("z3_plain","propagation_sat"):
        elapsed=timings[name]["total_cpu_s"]
        efficiency[name]={"exact_tasks_per_source_cpu_s":counters[name+"_correct"]/elapsed if elapsed>0 else 0,
            "source_cpu_s":elapsed,"exact":counters[name+"_correct"]}
    if all(efficiency[x]["exact_tasks_per_source_cpu_s"]>0 for x in efficiency):
        efficiency["propagation_over_plain_cpu_efficiency_ratio"]=(
            efficiency["propagation_sat"]["exact_tasks_per_source_cpu_s"] /
            efficiency["z3_plain"]["exact_tasks_per_source_cpu_s"])
    print("INDEPENDENT_OFFICIAL_AUTOMATABENCH_SCORE",json.dumps(dict(counters),sort_keys=True),flush=True)
    print("INDEPENDENT_AUTOMATABENCH_CPU_EFFICIENCY",json.dumps(efficiency,sort_keys=True),flush=True)
    return {"schema":"NEUMANN_AUTOMATABENCH_ORIGINAL_OFFICIAL_INDEPENDENT_GRADE.v1",
        "n":before["n"],"n_orig":counters["n"],
        "official_original_file_sha256":hashlib.sha256(raw).hexdigest(),
        "official_original_verifier_sha256":verifier_sha,"source_before_grade_sha256":hashlib.sha256(frozen.read_bytes()).hexdigest(),
        "original_repo_commit":PIN,"counts":dict(counters),"cost":efficiency,
        "per_task":details,"different_author_benchmark":True,
        "solver_uses_published_known_rule":True,"inferred_new_CA_rule":False,
        "neural_only_invention":False,"frontier_parity":"NOT_PROVED","total_compute10x":"NOT_PROVED"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("infer","grade"),required=True)
    parser.add_argument("--source");parser.add_argument("--sealed");parser.add_argument("--original")
    parser.add_argument("--expected-raw-sha");parser.add_argument("--out",required=True)
    a=parser.parse_args()
    if a.mode=="infer":data=infer(a.source)
    else:data=grade(a.sealed,a.original,a.expected_raw_sha)
    path=pathlib.Path(a.out);path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(data,sort_keys=True,separators=(",",":"))+"\n")
    print("AUTOMATABENCH_ORIGINAL_RECEIPT_SHA256",hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
