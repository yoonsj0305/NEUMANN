"""Postgrade, independently audit CPU source inference cost against random calibration.

This script NEVER calls either inference model, and receives only SHA-frozen
source-only prediction records and already graded original author score
artifacts from two independent GitHub Action runs. It reports sample *and*
solver CPU budgets separately. Model inference CPU excludes producing/
conducting the calibration probes or collecting outcomes.
"""
import argparse,collections,hashlib,json,pathlib,statistics
PRE={
 "public_dev":"7e6ca97ab0f3d678ed51ec766fee7959f193571040f50e5251f827b309cb93d6",
 "public_eval":"acbf9a49bc561f5a86203e615cd9378326a10707b086e7d5766b5c22defd2c3b"
}
SCORED={
 "public_dev":"a3d65b46bc5196ea18e61e0a74bf652e2b53f1d630813afe3bf06bc631daa475",
 "public_eval":"e34a2f7e17458583d507943bd9917e7a0a0568292b5c1f575a5bd69ec4a2bbc2"
}
KINDS=("random4","random6","random12","designed4")
def inspect(split,pregrade,graded):
    p=pathlib.Path(pregrade);g=pathlib.Path(graded)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==PRE[split],split
    assert hashlib.sha256(g.read_bytes()).hexdigest()==SCORED[split],split
    source=json.loads(p.read_text());score=json.loads(g.read_text())
    assert source["n_episodes"]==1200 and score["n_augmented_source_episodes"]==1200
    rates={};per_task=collections.defaultdict(dict)
    for kind in KINDS:
        subset=[r for r in source["rows"].values() if r["calibration"]==kind]
        assert len(subset)==300
        elapsed=[float(r["outcomes"]["joint"]["cpu_s"]) for r in subset]
        assert all(v>=0 for v in elapsed)
        c=score["counts"]
        assert c[kind+":total"]==300 and c[kind+":joint:wrong"]==0
        right=c[kind+":joint:correct"]
        rates[kind]={"n_original_tasks":300,
            "source_full_state_transition_probe_count_per_task":4 if kind in ("random4","designed4") else (6 if kind=="random6" else 12),
            "exact_answers":right,
            "full_rule_exact":c[kind+":complete_rule"],
            "total_source_only_solver_cpu_s":sum(elapsed),
            "median_source_cpu_ms":statistics.median(elapsed)*1000,
            "source_cpu_seconds_per_correct":sum(elapsed)/right if right else None,
            "correct_tasks_per_cpu_second":right/sum(elapsed) if sum(elapsed)>0 else None}
        for r in subset:per_task[r["original_id"]][kind]=float(r["outcomes"]["joint"]["cpu_s"])
    assert len(per_task)==300 and all(set(v)==set(KINDS) for v in per_task.values())
    ratios={}
    for kind in ("random4","random6","random12"):
        base=rates[kind];opt=rates["designed4"]
        ratios["designed4_over_"+kind]={
            "exact_answer_count_advantage":opt["exact_answers"]-base["exact_answers"],
            "complete_rule_count_advantage":opt["full_rule_exact"]-base["full_rule_exact"],
            "correct_per_source_cpu_second_ratio":
                opt["correct_tasks_per_cpu_second"]/base["correct_tasks_per_cpu_second"]
                if base["correct_tasks_per_cpu_second"] else None,
            "total_source_cpu_time_speedup":base["total_source_only_solver_cpu_s"]/opt["total_source_only_solver_cpu_s"],
            "paired_median_cpu_speedup":statistics.median(
                per_task[uid][kind]/per_task[uid]["designed4"]
                for uid in per_task if per_task[uid]["designed4"]>0)
            }
    print("POSTGRADE_SPLIT_CALIBRATION_SOURCE_CPU",split,json.dumps(rates,sort_keys=True),flush=True)
    print("POSTGRADE_SPLIT_DESIGNED4_SAVINGS",split,json.dumps(ratios,sort_keys=True),flush=True)
    return {"kinds":rates,"ratios":ratios,"source_only_receipt_sha256":PRE[split],
        "independent_authentic_author_scored_sha256":SCORED[split]}
def main():
    ap=argparse.ArgumentParser()
    for split in ("public_dev","public_eval"):
        ap.add_argument("--"+split+"-pregrade",required=True)
        ap.add_argument("--"+split+"-scored",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    records={split:inspect(split,getattr(a,split+"_pregrade"),getattr(a,split+"_scored"))
        for split in ("public_dev","public_eval")}
    total={}
    for kind in KINDS:
        l=[records[split]["kinds"][kind] for split in records]
        exact=sum(z["exact_answers"] for z in l);cpu=sum(z["total_source_only_solver_cpu_s"] for z in l)
        total[kind]={"n_distinct_original":600,"exact_answers":exact,
            "full_rule_identifications":sum(z["full_rule_exact"] for z in l),
            "total_source_only_solver_cpu_s":cpu,
            "exact_correct_tasks_per_source_cpu_second":exact/cpu if cpu>0 else None}
    opt=total["designed4"];other=total["random12"]
    report={"schema":"NEUMANN_Q3Q4_OPTIMAL_EXPERIMENT_DESIGN_REAL_ORIGINAL_POSTGRADE_CPU.v1",
        "splits":records,"combined":total,
        "combined_designed4_vs_random12_exact_count_delta":opt["exact_answers"]-other["exact_answers"],
        "combined_designed4_vs_random12_full_rule_count_delta":
            opt["full_rule_identifications"]-other["full_rule_identifications"],
        "combined_designed4_vs_random12_correct_per_source_cpu_second_ratio":
            opt["exact_correct_tasks_per_source_cpu_second"]/other["exact_correct_tasks_per_source_cpu_second"],
        "source_observation_count_reduction_factor_random12_to_optimal4":3,
        "includes_calibration_oracle_generation_or_experiment_execution_cost":False,
        "full_AI_system_10x":"NOT_PROVED","neural_novelty":"NOT_PROVED",
        "original_sources_previously_published":True}
    p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,sort_keys=True,separators=(",",":"))+"\n")
    print("POSTGRADE_TWO_SPLIT_600_REAL_ORIGINAL_COMBINED_CPU",json.dumps(total,sort_keys=True),flush=True)
    print("POSTGRADE_TWO_SPLIT_600_CPU_SAVINGS_RATIO",report["combined_designed4_vs_random12_correct_per_source_cpu_second_ratio"],flush=True)
    print("POSTGRADE_600_ORIGINAL_CALIBRATION_RECEIPT_SHA256",hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
