"""Same-run original AutomataBench public_eval300 matched total CPU Q4 speed gate.

Frozen SAT source policy vs 4x4 complete 16-bit state enumeration. Comparison
makes NO first-blind generalization claim (public_eval already scored in PR514).
All output arrays and ABSTAIN semantics must agree across all 5 paired runs.
"""
import argparse,collections,hashlib,json,pathlib,statistics,time
from exact_16bit_filter import exhaustive_4x4
from reversible_ca_solver import solve,native_verify
from source_then_official_grade import official_verifier
METHODS=("z3_propagation","exact_16bit_filter")
def compare(masked):
    records=[json.loads(s) for s in pathlib.Path(masked).read_text().splitlines()]
    assert len(records)==300 and all("answer" not in r and "metadata" not in r for r in records)
    seen=set()
    for t in records:
        assert t["id"] not in seen;seen.add(t["id"])
    completed={};trials={name:[] for name in METHODS};records_out={}
    # Warmup both methods on 4 originals, not included in timing.
    for task in records[:4]:
        assert solve(task,policy="propagation")["prediction"]==exhaustive_4x4(task)["prediction"]
    for trial in range(5):
        per_method=collections.defaultdict(float)
        order=METHODS if trial%2==0 else tuple(reversed(METHODS))
        for method in order:
            t0=time.process_time()
            for task in records:
                if method=="z3_propagation":result=solve(task,policy="propagation")
                else:result=exhaustive_4x4(task)
                guess=result.get("prediction")
                assert guess is not None,(task["id"],method,result["status"])
                assert native_verify(task,guess)
                if trial==0:
                    records_out.setdefault(task["id"],{})[method]=guess
                else:
                    assert records_out[task["id"]][method]==guess,(task["id"],method,trial)
            per_method[method]=time.process_time()-t0
        for name in METHODS:trials[name].append(per_method[name])
        print("PAIRED_AUTOMATABENCH_300_CPU_TRIAL",trial,json.dumps(dict(per_method),sort_keys=True),flush=True)
    for uid,d in records_out.items():
        assert set(d)==set(METHODS)
        assert d["z3_propagation"]==d["exact_16bit_filter"],uid
    times={name:{"cpu_s_5":v,"median_cpu_s":statistics.median(v),
                 "min_cpu_s":min(v),"max_cpu_s":max(v)} for name,v in trials.items()}
    ratio=times["z3_propagation"]["median_cpu_s"]/times["exact_16bit_filter"]["median_cpu_s"]
    report={"schema":"NEUMANN_AUTOMATABENCH_Q4_EXACT_16BIT_SOURCE_MATCHED.v1",
      "n":len(records_out),"predictions_source_only":True,"answers_seen":False,
      "metadata_seen":False,"n_matched_original_predictions":len(records_out),
      "n_trials":5,"times":times,"source_cpu_speedup_ratio_exact_filter_over_sat":ratio,
      "all_five_predictions_deterministic_and_equal":True,
      "original_dataset_source":"neelsomani/automata-bench/public_eval",
      "public_eval_previously_evaluated":True,"not_frontier_or_global10x":True,
      "rows":records_out}
    print("PRE_GRADE_ORIGINAL_Q4_SOURCE_CPU_RESULT",json.dumps({"speedup":ratio,"times":times},sort_keys=True),flush=True)
    return report

def grade(sealed,original,original_sha):
    before=pathlib.Path(sealed);d=json.loads(before.read_text())
    assert d["n"]==300 and d["predictions_source_only"] and d["all_five_predictions_deterministic_and_equal"]
    true=pathlib.Path(original).read_bytes();assert hashlib.sha256(true).hexdigest()==original_sha
    verifier,verifier_sha=official_verifier("7d86373fdb63fe1bd3592ddf71d923ceebc5acd9")
    cnt=collections.Counter()
    for line in true.splitlines():
        t=json.loads(line);uid=t["id"];p=d["rows"][uid]
        assert verifier(t,t["answer"])
        cnt["n"]+=1
        for method in METHODS:
            output=p[method]
            right=bool(verifier(t,output)) and output==t["answer"]["initial_state"]
            cnt[method+"_correct"]+=int(right)
            cnt[method+"_wrong"]+=int(not right)
            cnt[t["difficulty"]+"_"+method+"_correct"]+=int(right)
    assert cnt["n"]==300
    assert cnt["z3_propagation_correct"]==cnt["exact_16bit_filter_correct"]==300
    result={"schema":"NEUMANN_AUTOMATABENCH_Q4_ORIGINAL_INDEPENDENT_EXACT_EQUIVALENCE.v1",
      "n":300,"counts":dict(cnt),"prior_cpu_source_receipt_sha256":hashlib.sha256(before.read_bytes()).hexdigest(),
      "original_raw_sha256":hashlib.sha256(true).hexdigest(),
      "official_verifier_sha256":verifier_sha,
      "paired_source_cpu_median_speedup":d["source_cpu_speedup_ratio_exact_filter_over_sat"],
      "five_same_worker_cpu_trials":d["times"],
      "already_scored_original_source_previously":True,
      "global_q4_full10x":"NOT_PROVED",
      "permitted_claim":"same-300 exact 16-bit specialized CA original source inference stage performance"}
    print("INDEPENDENT_ORIGINAL_AUTOMATA_Q4_ALL_EXACT",json.dumps(dict(cnt),sort_keys=True),flush=True)
    print("INDEPENDENT_ORIGINAL_AUTOMATA_Q4_SPEEDUP",result["paired_source_cpu_median_speedup"],flush=True)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=("infer","grade"),required=True)
    ap.add_argument("--masked");ap.add_argument("--sealed");ap.add_argument("--original")
    ap.add_argument("--original-sha");ap.add_argument("--out",required=True)
    a=ap.parse_args()
    result=compare(a.masked) if a.mode=="infer" else grade(a.sealed,a.original,a.original_sha)
    out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(result,separators=(",",":"),sort_keys=True)+"\n")
    print("NEUMANN_AUTOMATA_Q4_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
