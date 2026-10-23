"""Blind optimum-designed 4 vs random 4/6/12 calibrations, strict real scores.

No hidden permutation, answer or metadata access during inference. Compare
both strict full-lookup and joint exact completion from previous frozen Q3
program without ANY modification. Independent grader authentic original author.
"""
import argparse,collections,hashlib,json,pathlib
from hidden_rule_inference import discover,source_pair_mapping
from source_then_official_grade import official_verifier

KINDS=("random4","random6","random12","designed4")
POLICIES=("lookup","joint")
UPSTREAM="7d86373fdb63fe1bd3592ddf71d923ceebc5acd9"

def infer(path):
    records={};counts=collections.Counter();costs=collections.Counter()
    for line in pathlib.Path(path).read_text().splitlines():
        d=json.loads(line)
        assert "answer" not in d and "metadata" not in d
        assert "permutation" not in d["task"]["rule"]
        assert d["id"] not in records
        mapping,error=source_pair_mapping(d["demos"])
        assert error is None
        if d["calibration"]=="designed4":
            assert len(d["demos"])==4 and len(mapping)==16
        outputs={}
        for name in POLICIES:
            guess=discover(d,policy=name)
            outputs[name]=guess
            costs[name]+=guess["cpu_s"]
            counts[d["calibration"]+":"+name+":"+guess["status"]]+=1
        certified=[tuple(out["prediction"]) for out in outputs.values() if out.get("prediction")]
        assert len(set(certified))<=1
        counts[d["calibration"]+":n"]+=1
        records[d["id"]]={"original_id":d["original_id"],
                          "calibration":d["calibration"],"observed_rule_entries":len(mapping),
                          "source_probes":d["n_source_probes"],"outcomes":outputs}
    assert len(records)==1200
    assert all(counts[k+":n"]==300 for k in KINDS)
    result={"schema":"NEUMANN_Q3_FOUR_OPTIMAL_VS_RANDOM_1200_SOURCE_ONLY.v1",
            "n_original":300,"n_episodes":1200,"no_original_rule_exposed":True,
            "no_original_query_answers_exposed":True,
            "model_code_is_previous_frozen_hidden_rule_inference":True,
            "candidate_rule_family_is_known":True,
            "counts":dict(counts),"source_inference_cpu_seconds":dict(costs),
            "rows":records}
    print("BLIND_4_DESIGNED_VS_RANDOM_SOURCE_COUNTS",json.dumps(dict(counts),sort_keys=True),flush=True)
    print("BLIND_4_DESIGNED_VS_RANDOM_SOURCE_CPU",json.dumps(dict(costs),sort_keys=True),flush=True)
    return result

def grade(sealed,source_file,original_file,expected_original_sha):
    seal=pathlib.Path(sealed);pre=json.loads(seal.read_text())
    assert pre["n_episodes"]==1200 and pre["no_original_rule_exposed"]
    raw=pathlib.Path(original_file).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==expected_original_sha
    tasks={x["id"]:x for x in (json.loads(s) for s in raw.splitlines())}
    assert len(tasks)==300
    demos={d["id"]:d for d in (json.loads(s) for s in pathlib.Path(source_file).read_text().splitlines())}
    assert len(demos)==1200
    verified,verifier_sha=official_verifier(UPSTREAM)
    count=collections.Counter();errors=[]
    by_budget={}
    for uid,receipt in pre["rows"].items():
        r=demos[uid];truth=tasks[receipt["original_id"]]
        assert r["calibration"]==receipt["calibration"]
        assert verified(truth,truth["answer"])
        mapping,error=source_pair_mapping(r["demos"])
        assert error is None and len(mapping)==receipt["observed_rule_entries"]
        true_rule=truth["rule"]["permutation"]
        assert all(true_rule[x]==value for x,value in mapping.items())
        k=r["calibration"]
        if k=="designed4":
            assert len(mapping)==16 and all(mapping[j]==true_rule[j] for j in range(16))
            count["true_unknown_original_rule_permutation_exact_identified"]+=1
        count[k+":total"]+=1
        count[k+":complete_rule"]+=int(len(mapping)==16)
        count[k+":partially_unknown_rule"]+=int(len(mapping)<16)
        count[k+":sum_observed_rule_entries"]+=len(mapping)
        for method,out in receipt["outcomes"].items():
            prediction=out.get("prediction")
            if prediction is None:continue
            correct=prediction==truth["answer"]["initial_state"] and bool(verified(truth,prediction))
            count[k+":"+method+":submitted"]+=1
            count[k+":"+method+":correct"]+=int(correct)
            count[k+":"+method+":wrong"]+=int(not correct)
            if not correct:errors.append(uid+":"+method)
    assert all(count[k+":total"]==300 for k in KINDS)
    assert count["true_unknown_original_rule_permutation_exact_identified"]==300
    result={"schema":"NEUMANN_Q3_ORIGINAL_AUTHOR_FOUR_PROBE_VS_RANDOM_GRADE.v1",
        "n_actual_original_tasks":300,"n_augmented_source_episodes":1200,
        "counts":dict(count),"incorrect_predictions":errors,
        "original_upstream_raw_sha256":hashlib.sha256(raw).hexdigest(),
        "sealed_source_predictions_sha256":hashlib.sha256(seal.read_bytes()).hexdigest(),
        "original_authentic_author_verifier_sha256":verifier_sha,
        "rule_family_pregiven_reversible_block_permutation":True,
        "source_full_state_probe_design_is_human_constructed":True,
        "optimal_4_probes_for_UNIVERSAL_full_permutation_IDENTIFICATION":True,
        "three_probes_leave_at_least_4_factorial_rule_permutations":True,
        "not_raw_author_original_hidden_rule_benchmark":True,
        "neural_only_novel_primitive_Q3":"OPEN","end_to_end_Q4_10x":"OPEN"}
    print("INDEPENDENT_ORIGINAL_AUTHOR_OPTIMAL_FOUR_VS_RANDOM_SCORE",
          json.dumps(dict(count),sort_keys=True),flush=True)
    print("INDEPENDENT_ORIGINAL_AUTHOR_OPTIMAL_FOUR_VS_RANDOM_WRONG",
          json.dumps(errors[:12]),flush=True)
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("infer","grade"),required=True)
    parser.add_argument("--source");parser.add_argument("--original")
    parser.add_argument("--sealed");parser.add_argument("--expected-original-sha")
    parser.add_argument("--out",required=True)
    a=parser.parse_args()
    result=infer(a.source) if a.mode=="infer" else grade(a.sealed,a.source,a.original,a.expected_original_sha)
    out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    print("NEUMANN_FOUR_PROBE_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
