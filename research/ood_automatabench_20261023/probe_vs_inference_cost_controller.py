"""Q4 minimal *total source effort* under a priced observation oracle.

Two full-information sound solution policies were already independently
graded exact on 600 original tasks:
  ALWAYS4   -> four designed probes followed by direct complete-rule inverse.
  EARLY3    -> three designed probes, 24-rule expensive joint proof; if UNKNOWN
               conduct the fourth probe and rerun complete inverse.

Total objective = source model CPU seconds + lambda * number of one-step
full-grid observational interventions. Lambda in CPU-equivalent seconds per
probe is hypothetical price, not a measured real physical lab duration.
Freeze policy threshold from dev300 only, test on dev-disjoint eval300, show
counterexample near threshold and cautious UNKNOWN region.
"""
import argparse,hashlib,json,pathlib
EARLY_SHA="8daaa27f92314a399b91be8e453aa5bcb2356b06f1bb4d22e5761786524c7c5a"
AUDIT_SHA="807ef1c34b1fb8d22df277ee028894300806f232bd90d428a675c7ba297d14b1"
SPLITS=("public_dev","public_eval")
PRICES=(0.001,0.010,0.030,0.031,0.050,0.100,1.000)
LOW_BAND=0.030
HIGH_BAND=0.032

def profile(f,kind):
    m=f["source_inference_cpu"][kind]
    total=300
    recovered=f["counts"][kind+":three_exact_submitted"]
    followup=f["counts"][kind+":needed_fourth_probe"]
    assert recovered+followup==total
    return {
        "direct_cpu_s":m["four_always_cpu_s"],
        "adaptive_cpu_s":m["counterfactual_adaptive_three_then_four_source_cpu_s"],
        "direct_probes":1200,
        "adaptive_probes":3*recovered+4*followup,
        "adaptive_saved_probes":recovered,
        "n_exact_with_rule_hidden":300,
        "threshold_s_per_probe":(m["counterfactual_adaptive_three_then_four_source_cpu_s"]-
                                  m["four_always_cpu_s"])/recovered,
        "fully_scored":True}

def choose(policy,p):
    if p>policy:return "EARLY3_THEN4"
    if p<policy:return "ALWAYS4"
    return "EQUAL"

def total(profile,method,p):
    return profile["direct_cpu_s"]+profile["direct_probes"]*p if method=="ALWAYS4" else (
           profile["adaptive_cpu_s"]+profile["adaptive_probes"]*p)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--three-proof",required=True)
    ap.add_argument("--source-cost",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    p=pathlib.Path(a.three_proof);q=pathlib.Path(a.source_cost)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==EARLY_SHA
    assert hashlib.sha256(q.read_bytes()).hexdigest()==AUDIT_SHA
    early=json.loads(p.read_text());cost=json.loads(q.read_text())
    assert early["n"]==600 and early["all_600_original_tasks_finish_correct_with_fourth_if_needed"]
    assert early["exact_original_author_three_probe_predictions"]==320
    assert cost["combined"]["designed4"]["exact_answers"]==600
    profiles={s:profile(early,s) for s in SPLITS}
    for s in SPLITS:
        assert abs(profiles[s]["direct_cpu_s"] -
          cost["splits"][s]["kinds"]["designed4"]["total_source_only_solver_cpu_s"])<1e-8
    threshold=profiles["public_dev"]["threshold_s_per_probe"]
    assert 0.030<threshold<0.032,"registered uncertainty guard"
    outcomes=[]
    for price in PRICES:
        test=profiles["public_eval"]
        expected=choose(threshold,price)
        direct=total(test,"ALWAYS4",price)
        adaptive=total(test,"EARLY3_THEN4",price)
        oracle="ALWAYS4" if direct<adaptive else "EARLY3_THEN4"
        chosen=total(test,expected,price)
        # A tolerance band forces an honest UNKNOWN in regimes where
        # dataset-to-dataset threshold can switch the preferred route.
        conservative="UNKNOWN_NEAR_TRADEOFF" if LOW_BAND<=price<=HIGH_BAND else expected
        if conservative=="UNKNOWN_NEAR_TRADEOFF":claimed_regret=None
        else:claimed_regret=chosen-min(direct,adaptive)
        outcomes.append({"price_seconds_per_full_grid_probe":price,
            "selected_by_dev_only":expected,
            "conservative_verified_decision":conservative,
            "eval_total_cost_selected":chosen,
            "eval_total_cost_direct":direct,
            "eval_total_cost_three_then_four":adaptive,
            "eval_actual_optimal_of_two":oracle,
            "eval_selected_regret":chosen-min(direct,adaptive),
            "eval_conservative_admitted_regret":claimed_regret})
    assert all(z["eval_conservative_admitted_regret"]<1e-8 for z in outcomes
               if z["conservative_verified_decision"]!="UNKNOWN_NEAR_TRADEOFF")
    assert any(z["selected_by_dev_only"]!=z["eval_actual_optimal_of_two"]
               for z in outcomes),"failure zone deliberately retained"
    result={"schema":"NEUMANN_Q4_COST_AWARE_TWO_EXACT_PROBE_POLICIES_TEST.v1",
        "source_receipts_sha256":{"three_proof":EARLY_SHA,"four_source_audit":AUDIT_SHA},
        "development_only_break_even_seconds_per_probe":threshold,
        "evaluation_realized_break_even_seconds_per_probe":profiles["public_eval"]["threshold_s_per_probe"],
        "development":profiles["public_dev"],
        "disjoint_evaluation":profiles["public_eval"],
        "uncertain_probe_cost_zone_seconds":(LOW_BAND,HIGH_BAND),
        "priced_probe_scenarios":outcomes,
        "current_probes_are_controlled_source_observations_not_free_data":True,
        "probe_prices_are_hypothetical_not_physically_measured":True,
        "adaptive_stopping_measured_as_counterfactual_from_sealed_previous_proofs":True,
        "no_new_actual_deployment_or_neural_learning":True,
        "Q4_global_all_cost_10x":"OPEN"}
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    print("ORIGINAL_600_COST_AWARE_DEV_THRESHOLD_S",threshold,flush=True)
    print("ORIGINAL_600_COST_AWARE_EVAL_THRESHOLD_S",profiles["public_eval"]["threshold_s_per_probe"],flush=True)
    for r in outcomes:
        print("ORIGINAL_600_ORACLE_COST_TRADEOFF",json.dumps(r,sort_keys=True),flush=True)
    print("ORIGINAL_600_COST_AWARE_Q4_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
