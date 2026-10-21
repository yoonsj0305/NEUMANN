"""Q3 out-of-vocabulary structural model falsification and fail-closed fallback.

Same trained candidate selector, source-native original SAT / UNSAT verifier and
same source data as parent PR438. OOD prime step k∈{23,29,31,37} is NOT in
fixed model vocabulary m in [2,20]. Every candidate must fail true original
Z3+cvc5 induction; exact source GCD fallback must prove it instead.
Scope synthetic adversarial HOLDOUT, not claim of independent author transfer.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from research.evidence.q3_modular_operator_selection_20261022.learn_mod_operator_and_dual_prove import (
    OPTIONS,learn,gcd,certified_source,ms)
OOD=(23,29,31,37)
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--out",required=True)
    args=parser.parse_args()
    rows=[]
    for k in OOD:
        for rep in range(4):
            seed=20261022+rep
            rng=np.random.default_rng(seed)
            raw=[(int(x),int(x+k)) for x in rng.integers(-40,41,size=50)]
            start=time.perf_counter_ns()
            pred=learn(raw,seed)
            ml_proof=certified_source(k,pred["candidate"])
            model_safe=all(z["independent_dual_unsat"] for z in ml_proof)
            model_rejected=ml_proof[1]["independent_dual_sat"]
            # Model admits ONLY after complete original dual proof;
            # upon veto, invoke independently full-authorized classical GCD.
            fallback,baseline_ms=gcd(raw)
            exact_proof=certified_source(k,fallback)
            fallback_safe=all(z["independent_dual_unsat"] for z in exact_proof)
            online_ms=ms(start)
            if not model_rejected or model_safe or not fallback_safe:
                raise AssertionError("FAIL_CLOSED_OOD_DUAL_CERTIFICATION_FAILED")
            rows.append(dict(original_program_AST={
                "Pre":"x=1","Trans":f"x_next=x+{k}","Post":f"(x-1) mod {k}=0"},
                in_supplied_categorical_operator_vocabulary=False,
                seed=seed,model_selected_m=pred["candidate"],
                source_original_model_independent_three_VC=ml_proof,
                wrong_model_independent_original_SAT_counterexample=model_rejected,
                unverified_model_never_authorized_SAFE=True,
                source_native_exact_classical_fallback_m=fallback,
                native_original_Z3_cvc5_complete_SAFE=exact_proof,
                exact_baseline_full_original_safe=fallback_safe,
                real_online_full_fallback_wall_ms=online_ms,
                model_fit_ms=pred["train_ms"],
                exact_GCD_ms=baseline_ms))
            print("Q3_OUTSIDE_GRAMMAR_FAIL_CLOSED",k,seed,
                  "BAD_MODEL_M",pred["candidate"],"COUNTEREXAMPLE",model_rejected,
                  "CLASSICAL_EXACT",fallback,"SAFE",fallback_safe,flush=True)
    report=dict(schema="neumann.q3.ood_fixed_primitive_vocabulary_failclosed_gcd.v1",
          source_class="synthetic original mathematical source, NO real external source",
          true_originals=[23,29,31,37],
          trained_model_allowed_operator_parameters=list(map(int,OPTIONS)),
          frozen_vocabulary_cannot_express_original_modulus=True,
          total_out_of_vocabulary_trials=len(rows),
          learned_full_original_SAFE_count=0,
          original_model_cvc5_Z3_counterexamples=sum(x["wrong_model_independent_original_SAT_counterexample"] for x in rows),
          classical_native_full_original_SAFE_count=sum(x["exact_baseline_full_original_safe"] for x in rows),
          online_controller_fail_closed_classical_recovery_count=sum(x["exact_baseline_full_original_safe"] and x["unverified_model_never_authorized_SAFE"] for x in rows),
          actual_full_fallback_wall_ms_sum=sum(x["real_online_full_fallback_wall_ms"] for x in rows),
          waste_model_fit_ms_sum=sum(x["model_fit_ms"] for x in rows),
          no_unsupported_operator_invention=True,
          result_is_negative_distribution_shift_evidence=True,
          not_a_Q3_learning_transfer_success=True,
          global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",evidence=rows)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("total_out_of_vocabulary_trials","original_model_cvc5_Z3_counterexamples",
              "classical_native_full_original_SAFE_count",
              "online_controller_fail_closed_classical_recovery_count",
              "actual_full_fallback_wall_ms_sum"):
        print("Q3_OOD_VOCABULARY_ADMISSION",k,report[k],flush=True)
    print("RAW_RECEIPT_SHA256",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
    assert report["original_model_cvc5_Z3_counterexamples"]==16
    assert report["classical_native_full_original_SAFE_count"]==16
if __name__=="__main__":main()
