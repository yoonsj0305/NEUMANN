"""Matched end-to-end classical *source-only inference function* of Q3+Q4,
on new original CellARC train lines 6001-7000. Exact source-only prediction
receipts archived BEFORE independent original target labels are retrieved.
"""
import argparse,collections,hashlib,json,pathlib,statistics,sys,time
BASE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(BASE.parent/'q3_cellarc2000_20261022'),str(BASE.parent/'q4_debruijn_source_index_20261022')]
import debruijn_structural_model as old
import debruijn_source_phase as phase
from indexed_cycle import infer_indexed

def fast_guard(task):
    previous=phase.infer
    phase.infer=infer_indexed
    try:return phase.source_only_policy_comparison(task)
    finally:phase.infer=previous

def score_all(task,policy):
    if policy=="raw":return old.infer(task)
    if policy=="guard_slow":return phase.source_only_policy_comparison(task)
    if policy=="guard_indexed":return fast_guard(task)
    raise ValueError(policy)

NAMES=("raw","guard_slow","guard_indexed")
def batch(tasks,policy):
    t0=time.perf_counter_ns();cpu0=time.process_time_ns()
    vals=[score_all(t,policy) for t in tasks]
    return vals,{"wall_ns":time.perf_counter_ns()-t0,"process_cpu_ns":time.process_time_ns()-cpu0}

def exact_before_truth(tasks):
    assert len(tasks)==1000
    # One correctness smoke before timed passes, so early import/code failure does not skew.
    base=old.infer(tasks[0]);a=phase.source_only_policy_comparison(tasks[0]);b=fast_guard(tasks[0])
    assert a==b and base==a["variants"]["baseline"]
    timings={p:[] for p in NAMES}
    locked=None;hashes=[]
    for loop in range(5):
        order=NAMES if loop%2==0 else tuple(reversed(NAMES))
        produced={}
        for policy in order:
            out,cost=batch(tasks,policy)
            produced[policy]=out
            timings[policy].append(cost)
        for i in range(1000):
            assert produced["guard_slow"][i]==produced["guard_indexed"][i],(loop,tasks[i]["id"])
            assert produced["raw"][i]==produced["guard_slow"][i]["variants"]["baseline"],(loop,tasks[i]["id"])
        if locked is None:
            locked={tasks[i]["id"]:{
                  "old":produced["raw"][i],
                  "guarded":produced["guard_indexed"][i]["variants"]["source_all_three"],
                  "other_source_diagnostics":produced["guard_indexed"][i]["source_phase_audit"],
                  "query_canonical":produced["guard_indexed"][i]["query_canonical_subword"]}
                   for i in range(1000)}
        checksum=hashlib.sha256(json.dumps(produced["guard_indexed"],sort_keys=True,separators=(",",":")).encode()).hexdigest()
        hashes.append(checksum)
        print("Q34_IDENTICAL_ALL1000",loop,checksum,"baseline_ns",timings["raw"][-1]["wall_ns"],
            "guard_slow_ns",timings["guard_slow"][-1]["wall_ns"],
            "guard_indexed_ns",timings["guard_indexed"][-1]["wall_ns"],flush=True)
    assert len(set(hashes))==1
    getmedian=lambda policy,key:statistics.median([v[key] for v in timings[policy]])/1e9
    result={"schema":"NEUMANN_Q34_SEVENTH_SOURCE_ONLY_INTEGRATED.v1",
        "n":1000,"outputs_targets_read":False,"true_generator_metadata_read":False,
        "unchanged_frozen_original_git_blob":"fb12bc217178f7f3e89f0865987078e5dc367074",
        "same_guard_indexed_vs_nonindexed_semantics_for_every_original":True,
        "all_5_prediction_hashes_identical":True,
        "timings":timings,
        "median_source_pipeline_wall_s":{p:getmedian(p,"wall_ns") for p in NAMES},
        "median_source_pipeline_cpu_s":{p:getmedian(p,"process_cpu_ns") for p in NAMES},
        "source_guard_indexed_vs_guard_slow_speedup":getmedian("guard_slow","wall_ns")/getmedian("guard_indexed","wall_ns"),
        "source_guard_indexed_vs_raw_speedup":getmedian("raw","wall_ns")/getmedian("guard_indexed","wall_ns"),
        "neural_model_trained":False,"not_full_neumann_end_to_end_10x":True,
        "rows":locked}
    print("INTEGRATED_Q3Q4_SOURCE_ONLY_METRICS",json.dumps({
        "speedup_guarded":result["source_guard_indexed_vs_guard_slow_speedup"],
        "speedup_raw":result["source_guard_indexed_vs_raw_speedup"],
        "seconds":result["median_source_pipeline_wall_s"]},sort_keys=True),flush=True)
    return result

def grade(original_path,sealed_path):
    archive=pathlib.Path(sealed_path);pre=json.loads(archive.read_text())
    assert pre["n"]==1000 and not pre["outputs_targets_read"] and not pre["true_generator_metadata_read"]
    ct=collections.Counter();rows={}
    for line in pathlib.Path(original_path).read_text().splitlines():
        d=json.loads(line);z=pre["rows"][d["id"]]
        truth=d["solution"]
        old_pred=z["old"].get("prediction")
        good_pred=z["guarded"].get("prediction")
        old_correct=old_pred is not None and old_pred==truth
        new_correct=good_pred is not None and good_pred==truth
        ct["n"]+=1
        ct["old_attempted"]+=int(old_pred is not None)
        ct["old_correct"]+=int(old_correct)
        ct["old_wrong"]+=int(old_pred is not None and not old_correct)
        ct["guarded_attempted"]+=int(good_pred is not None)
        ct["guarded_correct"]+=int(new_correct)
        ct["guarded_wrong"]+=int(good_pred is not None and not new_correct)
        ct["discarded_true"]+=int(old_correct and good_pred is None)
        ct["discarded_false"]+=int(old_pred is not None and not old_correct and good_pred is None)
        rows[d["id"]]={"baseline_correct":old_correct,"guarded_correct":new_correct}
    assert ct["n"]==len(rows)==1000
    print("INDEPENDENT_SEVENTH_Q34_ACTUAL_ORIGINAL_SCORE",json.dumps(dict(ct),sort_keys=True),flush=True)
    return {"schema":"NEUMANN_Q34_SEVENTH_ORIGINAL1000_INDEPENDENT_EXACT_GRADE.v1",
        "n":1000,"count":dict(ct),"rows":rows,
        "frozen_source_only_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
        "model_code_unchanged_during_run":True,
        "global_Q3_neural_discovery":"OPEN","global_Q4_total_compute_10x":"OPEN"}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--mode",choices=["infer","grade"],required=True)
    a.add_argument("--input",required=True);a.add_argument("--sealed");a.add_argument("--out",required=True)
    p=a.parse_args()
    if p.mode=="infer":
        tasks=[json.loads(line) for line in pathlib.Path(p.input).read_text().splitlines()]
        assert len({t["id"] for t in tasks})==len(tasks)==1000
        assert all("solution" not in t and "meta" not in t and "program" not in t for t in tasks)
        result=exact_before_truth(tasks)
    else:result=grade(p.input,p.sealed)
    out=pathlib.Path(p.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    print("INTEGRATED_Q34_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
