"""Paired source-only exact reverse-observability vs strong SAT on 2D 4x4,6x6,8x8.

Public AutomataBench 300 original eval tasks (already scored) AND separate
unselected synthetic 6x6/8x8 forward-generated source tasks (160), with TRUE
initial state stored in different CI artifact never available at inference.
All three paired source CPU rounds alternated in one runner; independent grader.
"""
import argparse,collections,hashlib,json,pathlib,statistics,time,urllib.request
from reverse_observability_router import adaptive_solve,reverse_step_vector
from reversible_ca_solver import solve,native_verify
from source_then_official_grade import official_verifier

METHODS=("strong_sat","structural_router")
PIN="7d86373fdb63fe1bd3592ddf71d923ceebc5acd9"

def run_once(tasks,method,earlier=None):
    predictions={}
    t0=time.process_time()
    for d in tasks:
        v=solve(d,policy="propagation") if method=="strong_sat" else adaptive_solve(d)
        prediction=v.get("prediction")
        if prediction is not None and not native_verify(d,prediction):
            raise AssertionError(f"invalid reconstruction: {d['id']} {method}")
        if earlier is not None:
            assert prediction==earlier[d["id"]][method]["prediction"],(d["id"],method)
        witnesses=v.get("witness_initial_states")
        if witnesses is not None:
            assert len(witnesses)==2 and witnesses[0]!=witnesses[1]
            assert prediction is None and v["status"].startswith("PROVEN_NONUNIQUE")
            for witness in witnesses:
                assert native_verify(d,witness),"unverified purported two-solution proof"
        predictions[d["id"]]={"prediction":prediction,"status":v["status"],
            "route":v.get("route","SAT"),"cpu_s":v["cpu_s"],
            "witness_initial_states":witnesses,
            "witness_proof_checksum":v.get("witness_identity_sha256")}
    return predictions,time.process_time()-t0

def infer(source_syn,source_official):
    samples={}
    for name,path,expected in (("synthetic",source_syn,160),("official",source_official,300)):
        data=[json.loads(s) for s in pathlib.Path(path).read_text().splitlines()]
        assert len(data)==expected and len({s["id"] for s in data})==expected
        assert all("answer" not in s and "metadata" not in s for s in data)
        samples[name]=data
    rows={name:{} for name in samples}
    times={}
    for name,tasks in samples.items():
        loops={m:[] for m in METHODS};counts=collections.Counter()
        for trial in range(3):
            ordering=METHODS if trial%2==0 else tuple(reversed(METHODS))
            for method in ordering:
                this,elapsed=run_once(tasks,method,rows[name] if trial else None)
                loops[method].append(elapsed)
                if trial==0:
                    for uid,result in this.items():rows[name].setdefault(uid,{})[method]=result
            print("ORIGINAL_OBSERVABILITY_PAIRED_CPU",name,trial,
                  json.dumps({m:loops[m][-1] for m in METHODS},sort_keys=True),flush=True)
        for uid,pair in rows[name].items():
            assert pair["structural_router"]["status"] is not None
            counterexample=pair["structural_router"].get("witness_initial_states")
            if counterexample:
                counts["constructive_two_exact_witnesses"]+=1
                assert pair["structural_router"]["prediction"] is None
            if pair["structural_router"]["prediction"] is None and not counterexample:
                counts["unknown_without_constructive_pair"]+=1
            old=pair["strong_sat"]["prediction"]
            new=pair["structural_router"]["prediction"]
            if old is not None and new is not None:
                assert old==new,(uid,"TWO_CERTIFIED_DIFFERENT_INITIAL_STATES")
            if old is None and new is not None:
                counts["router_only_certified"]+=1
                print("ROUTER_CERTIFIED_WHILE_STRONG_SAT_ABSTAINS",
                      uid,pair["strong_sat"]["status"],pair["structural_router"]["status"],flush=True)
            if old is not None and new is None:
                counts["sat_only_certified"]+=1
                print("SAT_CERTIFIED_WHILE_ROUTER_ABSTAINS",
                      uid,pair["strong_sat"]["status"],pair["structural_router"]["status"],flush=True)
            counts["tasks"]+=1
            counts["solved"]+=int(pair["strong_sat"]["prediction"] is not None)
            counts["unsolved"]+=int(pair["strong_sat"]["prediction"] is None)
            counts["route_"+pair["structural_router"]["route"]]+=1
        times[name]={"cpu_trials":loops,"median_cpu":{m:statistics.median(loops[m]) for m in METHODS},
                     "solver_speedup":statistics.median(loops["strong_sat"])/statistics.median(loops["structural_router"])}
        print("SOURCE_ONLY_REVERSE_STRUCTURAL_ROUTER",name,json.dumps(dict(counts),sort_keys=True),flush=True)
        print("SOURCE_ONLY_REVERSE_PAIRED_CPU_AGG",name,json.dumps(times[name],sort_keys=True),flush=True)
    return {"schema":"NEUMANN_Q3Q4_MULTISIZE_REVERSE_OBSERVABILITY_SOURCE_ONLY.v1",
       "original_public_eval_previously_used_for_Q4":True,
       "generated_6x6_8x8_not_external_benchmark_problems":True,
       "query_truth_not_seen":True,"generation_truth_not_seen":True,
       "original_author_rules_given":True,"n_synthetic":160,"n_external":300,
       "paired_trials":3,"comparisons":times,"rows":rows}

def grade(frozen,truth_syn,official_orig,sha_orig,synthetic_source):
    file=pathlib.Path(frozen);pre=json.loads(file.read_text())
    assert pre["query_truth_not_seen"] and pre["generation_truth_not_seen"]
    official_bytes=pathlib.Path(official_orig).read_bytes()
    assert hashlib.sha256(official_bytes).hexdigest()==sha_orig
    verify,official_code_sha=official_verifier(PIN)
    syn=[json.loads(s) for s in pathlib.Path(truth_syn).read_text().splitlines()]
    ext=[json.loads(s) for s in official_bytes.splitlines()]
    assert len(syn)==160 and len(ext)==300
    source=[json.loads(s) for s in pathlib.Path(synthetic_source).read_text().splitlines()]
    source_by_id={r["id"]:r for r in source}
    assert len(source_by_id)==160
    assert all("answer" not in t and "metadata" not in t for t in source_by_id.values())
    overall=collections.Counter();by_group=collections.defaultdict(collections.Counter)
    for d in syn:
        uid=d["id"];p=pre["rows"]["synthetic"][uid]
        kind=d["group"]+"_"+str(d["height"])+"x"+str(d["width"])
        witness=p["structural_router"].get("witness_initial_states")
        if witness is not None:
            assert len(witness)==2 and witness[0]!=witness[1],uid
            for alternative in witness:
                assert native_verify(source_by_id[uid],alternative),(uid,"INVALID_NONUNIQUE_WITNESS")
            assert p["structural_router"]["prediction"] is None
            overall["independently_verified_two_solution_certificates"]+=1
            by_group[kind]["verified_nonunique_proofs"]+=1
        elif p["structural_router"]["prediction"] is None:
            overall["source_unknown_no_two_witness_proof"]+=1
            by_group[kind]["unknown_without_witness"]+=1
        for m in METHODS:
            value=p[m]["prediction"]
            exact=value is not None and value==d["answer"]["initial_state"]
            overall["synthetic_"+m+"_attempted"]+=int(value is not None)
            overall["synthetic_"+m+"_correct"]+=int(exact)
            overall["synthetic_"+m+"_wrong"]+=int(value is not None and not exact)
            by_group[kind][m+"_attempted"]+=int(value is not None)
            by_group[kind][m+"_correct"]+=int(exact)
        overall["synthetic_n"]+=1;by_group[kind]["n"]+=1
    for d in ext:
        uid=d["id"];p=pre["rows"]["official"][uid]
        assert verify(d,d["answer"])
        for m in METHODS:
            value=p[m]["prediction"]
            exact=value is not None and verify(d,value) and value==d["answer"]["initial_state"]
            overall["external_"+m+"_attempted"]+=int(value is not None)
            overall["external_"+m+"_correct"]+=int(exact)
            overall["external_"+m+"_wrong"]+=int(value is not None and not exact)
        overall["external_n"]+=1
    assert overall["external_n"]==300 and overall["synthetic_n"]==160
    assert overall["external_strong_sat_correct"]==overall["external_structural_router_correct"]==300
    assert overall["synthetic_strong_sat_wrong"]==overall["synthetic_structural_router_wrong"]==0
    result={"schema":"NEUMANN_Q3Q4_MULTISIZE_REVERSE_OBSERVABILITY_INDEPENDENT_GRADE.v1",
       "counts":dict(overall),"by_group":{k:dict(v) for k,v in by_group.items()},
       "source_receipt_sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
       "original_author_truth_sha256":hashlib.sha256(official_bytes).hexdigest(),
       "original_author_verifier_sha256":official_code_sha,
       "paired_three_trials":pre["comparisons"],
       "n_original_external":300,"n_generated_stress":160,
       "original_public_eval_previously_exposed":True,
       "global_Q3_unknown_rule":"OPEN","global_Q4_total10x":"OPEN"}
    print("INDEPENDENT_VARIABLE_SIZE_CA_GRADE",json.dumps(dict(overall),sort_keys=True),flush=True)
    print("INDEPENDENT_VARIABLE_SIZE_BY_GROUP",json.dumps(result["by_group"],sort_keys=True),flush=True)
    print("INDEPENDENT_VARIABLE_SIZE_CPU",json.dumps(pre["comparisons"],sort_keys=True),flush=True)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("infer","grade"),required=True)
    p.add_argument("--synthetic");p.add_argument("--official");p.add_argument("--sealed")
    p.add_argument("--synthetic-truth");p.add_argument("--synthetic-source");p.add_argument("--official-truth")
    p.add_argument("--official-sha");p.add_argument("--out",required=True)
    a=p.parse_args()
    result=infer(a.synthetic,a.official) if a.mode=="infer" else grade(a.sealed,a.synthetic_truth,a.official_truth,a.official_sha,a.synthetic_source)
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,separators=(",",":"),sort_keys=True)+"\n")
    print("NEUMANN_MULTISIZE_REVERSE_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
