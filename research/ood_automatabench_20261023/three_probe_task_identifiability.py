"""Goal-conditioned 3-of-4 interventions: exact target initial state despite
incomplete 16-entry latent CA permutation. Source task receives ONLY the FIRST
THREE designed 4x4 input/output probes (12 distinct block states); the fourth
probe is physically redacted and may be supplied only after decisions are
sealed. All 24 hidden permutation completions are exhaustively evaluated
using the PREVIOUS unchanged symbolic joint inference program.

Postgrade only, compare with verified complete four-probe receipts from prior
original experiments and calculate counterfactual average intervention budget
and actual per-task source CPU cost (third pass + fallback fourth pass).
Not proof of information-theoretic optimality for QUERY resolution, only for
unrestricted complete unknown rule identification.
"""
import argparse,collections,hashlib,json,pathlib,statistics
from hidden_rule_inference import discover,source_pair_mapping,candidate_rules
from source_then_official_grade import official_verifier
SPLITS=("public_dev","public_eval")
BEFORE={
 "public_dev":"7e6ca97ab0f3d678ed51ec766fee7959f193571040f50e5251f827b309cb93d6",
 "public_eval":"acbf9a49bc561f5a86203e615cd9378326a10707b086e7d5766b5c22defd2c3b"}
GRADED={
 "public_dev":"a3d65b46bc5196ea18e61e0a74bf652e2b53f1d630813afe3bf06bc631daa475",
 "public_eval":"e34a2f7e17458583d507943bd9917e7a0a0568292b5c1f575a5bd69ec4a2bbc2"}
ORIGINAL="7d86373fdb63fe1bd3592ddf71d923ceebc5acd9"

def make(original_sources,out):
    records=[]
    for split,path in zip(SPLITS,original_sources):
        rows=[json.loads(x) for x in pathlib.Path(path).read_text().splitlines()]
        tasks=[r for r in rows if r["calibration"]=="designed4"]
        assert len(tasks)==len({r["original_id"] for r in tasks})==300
        for r in tasks:
            task={**r,
                  "id":split+"::"+r["original_id"]+"::designed3",
                  "split":split,
                  "calibration":"designed3",
                  "n_source_probes":3,
                  "demos":r["demos"][:3]}
            mapping,error=source_pair_mapping(task["demos"])
            assert error is None and len(mapping)==12
            completions,missing=candidate_rules(mapping,4)
            assert missing==4 and len(completions)==24
            assert "permutation" not in json.dumps(task) and "answer" not in json.dumps(task)
            records.append(task)
    assert len(records)==600
    path=pathlib.Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text("".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in records))
    print("THREE_PROBE_RULE_UNIDENTIFIED_BY_EXACTLY_24_COMPLETIONS_600_SOURCE",hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)

def infer(source):
    rows={};count=collections.Counter();cost=collections.Counter()
    for line in pathlib.Path(source).read_text().splitlines():
        r=json.loads(line)
        assert "permutation" not in r["task"]["rule"] and len(r["demos"])==3
        ans=discover(r,policy="joint")
        assert r["id"] not in rows
        rows[r["id"]]={"original_id":r["original_id"],"split":r["split"],
                       "result":ans}
        count[r["split"]+":"+ans["status"]]+=1
        cost[r["split"]]+=ans["cpu_s"]
    assert len(rows)==600
    result={"schema":"NEUMANN_Q3_3_PROBES_VS_4_COMPLETE_RULE_SOURCE_ONLY.v1",
        "n":600,"test_targets_or_true_rules_seen":False,"source_4th_probe_available":False,
        "candidate_rule_completions_per_task":24,"counts":dict(count),
        "cpu_s_by_split":dict(cost),"rows":rows}
    print("SEALED_THREE_PROBE_SOURCE_RESULTS",json.dumps(dict(count),sort_keys=True),flush=True)
    print("SEALED_THREE_PROBE_CPU",json.dumps(dict(cost),sort_keys=True),flush=True)
    return result

def grade(three_sealed,three_source,truth_files,four_pregrades,four_scores):
    prefile=pathlib.Path(three_sealed);pre=json.loads(prefile.read_text())
    assert pre["n"]==600 and not pre["test_targets_or_true_rules_seen"] and not pre["source_4th_probe_available"]
    source=[json.loads(z) for z in pathlib.Path(three_source).read_text().splitlines()]
    assert len(source)==600
    orig={}
    prev={}
    grades={}
    for split,path,pr,gr in zip(SPLITS,truth_files,four_pregrades,four_scores):
        raw=[json.loads(z) for z in pathlib.Path(path).read_text().splitlines()]
        assert len(raw)==300
        orig[split]={r["id"]:r for r in raw}
        assert len(orig[split])==300
        p=pathlib.Path(pr);g=pathlib.Path(gr)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==BEFORE[split]
        assert hashlib.sha256(g.read_bytes()).hexdigest()==GRADED[split]
        prev[split]=json.loads(p.read_text())["rows"]
        grades[split]=json.loads(g.read_text())["counts"]
        assert grades[split]["designed4:joint:correct"]==300
        assert grades[split]["designed4:joint:wrong"]==0
    official,verifier_sha=official_verifier(ORIGINAL)
    counts=collections.Counter();cpu={}
    for split in SPLITS:
        cpu[split]={"three_probe_cpu_s":0.0,"fallback_four_probe_cpu_s":0.0,
                    "four_always_cpu_s":0.0}
    for record in source:
        split=record["split"];uid=record["original_id"]
        before=pre["rows"][record["id"]]["result"]
        true=orig[split][uid]
        assert official(true,true["answer"])
        source_map,error=source_pair_mapping(record["demos"])
        assert error is None and len(source_map)==12
        assert all(true["rule"]["permutation"][i]==y for i,y in source_map.items())
        four=prev[split][uid+"__designed4"]["outcomes"]["joint"]
        assert four["prediction"]==true["answer"]["initial_state"]
        cpu[split]["three_probe_cpu_s"]+=float(before["cpu_s"])
        cpu[split]["four_always_cpu_s"]+=float(four["cpu_s"])
        initial=before.get("prediction")
        if initial is not None:
            valid=initial==true["answer"]["initial_state"] and official(true,initial)
            counts[split+":three_exact_submitted"]+=int(valid)
            counts[split+":three_wrong"]+=int(not valid)
        else:
            counts[split+":needed_fourth_probe"]+=1
            cpu[split]["fallback_four_probe_cpu_s"]+=float(four["cpu_s"])
        counts[split+":n"]+=1
    assert all(counts[s+":n"]==300 for s in SPLITS)
    assert all(counts[s+":three_wrong"]==0 for s in SPLITS)
    combined_three=sum(counts[s+":three_exact_submitted"] for s in SPLITS)
    fallback=sum(counts[s+":needed_fourth_probe"] for s in SPLITS)
    assert combined_three+fallback==600
    stats={}
    for split in SPLITS:
        c=cpu[split]
        c["counterfactual_adaptive_three_then_four_source_cpu_s"]=c["three_probe_cpu_s"]+c["fallback_four_probe_cpu_s"]
        c["source_cpu_ratio_four_always_over_adaptive"]=(c["four_always_cpu_s"]/c["counterfactual_adaptive_three_then_four_source_cpu_s"])
        stats[split]=c
    total_probes=3*combined_three+4*fallback
    report={"schema":"NEUMANN_GOAL_CONDITIONED_THREE_PROBE_OR_FOUR_POSTGRADE.v1",
        "n":600,"counts":dict(counts),"source_inference_cpu":stats,
        "exact_original_author_three_probe_predictions":combined_three,
        "all_600_original_tasks_finish_correct_with_fourth_if_needed":True,
        "counterfactual_total_intervention_count":total_probes,
        "always_four_total_interventions":4*600,
        "counterfactual_mean_source_probes_per_original":total_probes/600,
        "mean_source_probe_reduction_fraction":(4*600-total_probes)/(4*600),
        "source_3_probes_are_original_four_first_three_only":True,
        "source_four_probe_fallback_previously_independently_scored":True,
        "this_is_counterfactual_adaptive_not_actual_online_probing":True,
        "source_prediction_sha256":hashlib.sha256(prefile.read_bytes()).hexdigest(),
        "author_original_verifier_sha256":verifier_sha,
        "global_neural_discovery":"OPEN","global10x":"OPEN"}
    print("INDEPENDENT_REAL_ORIGINAL_THREE_PROBE_VS_FULL_RULE_600",json.dumps(dict(counts),sort_keys=True),flush=True)
    print("THREE_VS_FOUR_GOAL_CONDITIONED_BUDGET",total_probes,report["counterfactual_mean_source_probes_per_original"],flush=True)
    print("THREE_VS_FOUR_ADAPTIVE_SOURCE_CPU",json.dumps(stats,sort_keys=True),flush=True)
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("prep","infer","grade"),required=True)
    ap.add_argument("--dev-source");ap.add_argument("--eval-source");ap.add_argument("--source")
    ap.add_argument("--sealed");ap.add_argument("--dev-truth");ap.add_argument("--eval-truth")
    ap.add_argument("--dev-four-pregrade");ap.add_argument("--eval-four-pregrade")
    ap.add_argument("--dev-four-scored");ap.add_argument("--eval-four-scored")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    if a.mode=="prep":
        make([a.dev_source,a.eval_source],a.out);return
    result=infer(a.source) if a.mode=="infer" else grade(
       a.sealed,a.source,[a.dev_truth,a.eval_truth],
       [a.dev_four_pregrade,a.eval_four_pregrade],
       [a.dev_four_scored,a.eval_four_scored])
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    print("Q3_THREE_VS_FOUR_SOURCE_ONLY_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
