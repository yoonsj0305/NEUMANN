"""First frozen comparison on never-graded original CellARC train lines 3001..4000."""
import argparse,collections,hashlib,json,pathlib,time
from debruijn_source_phase import source_only_policy_comparison
NAMES=("baseline","source_alphabet","source_alphabet_plus_phase","source_alphabet_plus_query","source_all_three")
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--mode",choices=["infer","grade"],required=True)
 p.add_argument("--source");p.add_argument("--sealed");p.add_argument("--out",required=True)
 args=p.parse_args();start=time.perf_counter()
 if args.mode=="infer":
    rows={};status=collections.Counter()
    for line in pathlib.Path(args.source).read_text().splitlines():
        d=json.loads(line)
        assert "solution" not in d and "meta" not in d and "program" not in d
        assert d["id"] not in rows
        z=source_only_policy_comparison(d);rows[d["id"]]=z
        for name in NAMES:status[name+":"+z["variants"][name]["status"]]+=1
        status["query_canonical"]+=int(z["query_canonical_subword"])
        phase=z["source_phase_audit"]
        if phase:status["phase:"+phase["reason"]]+=1
    assert len(rows)==1000
    result={"schema":"NEUMANN_FOURTH1000_FROZEN_PHASE_CONSISTENCY.v1",
        "n":1000,"solution_read":False,"oracle_meta_read":False,
        "source_git_sha":"76040e6aef0edc4982e53c13a85ef227378ed171",
        "fixed_existing_solver_blob":"fb12bc217178f7f3e89f0865987078e5dc367074",
        "comparators":list(NAMES),"source_counts":dict(status),
        "source_only_wall_s":time.perf_counter()-start,"rows":rows}
    print("FROZEN_FOURTH_SOURCE_ONLY",json.dumps(dict(status),sort_keys=True),flush=True)
 else:
    receipt=pathlib.Path(args.sealed);frozen=json.loads(receipt.read_text())
    assert frozen["n"]==1000 and not frozen["solution_read"] and not frozen["oracle_meta_read"]
    total=collections.Counter();by_id={}
    for line in pathlib.Path(args.source).read_text().splitlines():
        d=json.loads(line);entry=frozen["rows"][d["id"]]
        ans={}
        for name in NAMES:
            pred=entry["variants"][name].get("prediction")
            exact=(pred is not None and pred==d["solution"])
            total[name+"_attempted"]+=int(pred is not None)
            total[name+"_correct"]+=int(exact)
            total[name+"_wrong"]+=int(pred is not None and not exact)
            ans[name]={"attempted":pred is not None,"correct":exact}
            if name!="baseline" and entry["variants"]["baseline"].get("prediction") is not None and pred is None:
                total[name+"_discarded_base_wrong"]+=int(not ans["baseline"]["correct"])
                total[name+"_discarded_base_right"]+=int(ans["baseline"]["correct"])
        total["n"]+=1;by_id[d["id"]]=ans
    assert total["n"]==len(by_id)==1000
    result={"schema":"NEUMANN_FOURTH1000_INDEPENDENT_PHASE_ABLATION.v1","n":1000,
       "sealed_source_sha256":hashlib.sha256(receipt.read_bytes()).hexdigest(),
       "total":dict(total),"rows":by_id,"untouched_project_cohort_before_this_run":True,
       "not_true_world_pristine":True,"neural_new_primitive_not_proven":True,
       "global_10x_not_proven":True}
    print("INDEPENDENT_FOURTH_PHASE_ABLATION",json.dumps(dict(total),sort_keys=True),flush=True)
 out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
 print("FOURTH_PHASE_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
