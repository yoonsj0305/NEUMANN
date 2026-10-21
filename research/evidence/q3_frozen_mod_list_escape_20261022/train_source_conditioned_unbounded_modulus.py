"""Q3 source-conditioned learned operator INSTANCE synthesis past frozen vocabulary.

PR441 *mathematically* certified all 19 listed moduli m in 2..20 fail
on held-out prime-step source k in 23,29,31,37 (76 native SAT proofs).
This experiment changes the OUTPUT REPRESENTATION from 19-way discrete
choice to an unbounded integer AST parameter, not the primitive 'mod'.

Train ONE scalar source-conditioned continuous composer from six
DEVELOPMENT raw source transition batches, without candidate modulus
labels. The objective uses an explicit **human-supplied periodic form and
a highest-period preference**; thus no autonomous operator/algorithm
invention is demonstrated. Freeze learned parameter before the 4 OOD
source tests. Integerize candidate and require full original Z3 + cvc5
Init/Consecution/Goal; reject untrained candidates and mutated sources.
Classical GCD is matched with the same raw source pairs and full authority.

Scope: controlled synthetic source family, previously known OOD steps.
Not external first-body blind or a frontier/computation superiority claim.
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
from pathlib import Path
import numpy as np
from research.evidence.q3_modular_operator_selection_20261022.learn_mod_operator_and_dual_prove import certified_source
TRAIN_K=(5,7,11,13,17,19)
HOLDOUT_K=(23,29,31,37)
PREVIOUS_OPTIONS=set(range(2,21))
def ms(t): return (time.perf_counter_ns()-t)/1e6
def source_pairs(k,seed,count=50):
    rng=np.random.default_rng(seed)
    start=rng.integers(-40,41,size=count)
    return np.column_stack([start,start+k]).astype(int)
def magnitude(src):
    diff=np.abs(src[:,1]-src[:,0])
    return float(np.median(diff))
def candidate(f,src):
    # This composition can emit integers OUTSIDE the finite 2..20 list,
    # but modulo is itself a previously provided primitive operator.
    return max(2,int(np.rint(f*magnitude(src))))
def self_supervised_fit(seed):
    rng=np.random.default_rng(seed)
    raw=[source_pairs(k,seed+53+i,20) for i,k in enumerate(TRAIN_K)]
    # Do not provide true modulus labels; only raw transitions and a
    # HUMAN CHOSEN periodic/conservation objective.
    theta=float(rng.normal(1.55,.13))
    before=1/(1+math.exp(-theta))
    initial_pre=[candidate(before,x) for x in raw]
    momentum=0.0;velocity=0.0
    t=time.perf_counter_ns()
    trace=[]
    for step in range(1,351):
        fraction=1/(1+math.exp(-theta))
        gradients=[]
        losses=[]
        for observations in raw:
            increments=(observations[:,1]-observations[:,0]).astype(float)
            scale=magnitude(observations)
            phase=2*math.pi*increments/(fraction*scale)
            losses.append(float(np.mean(1-np.cos(phase))))
            gradients.append(float(np.mean(-np.sin(phase)*phase/fraction)))
        # Preference for the largest source-consistent period is a
        # DESIGNER PRIOR. It is NOT evidence of generated new mathematics.
        dL_dfrac=float(np.mean(gradients))-.03
        grad=dL_dfrac*fraction*(1-fraction)
        momentum=.9*momentum+.1*grad
        velocity=.999*velocity+.001*grad*grad
        theta-=.1*(momentum/(1-.9**step))/(math.sqrt(velocity/(1-.999**step))+1e-8)
        if step in (1,100,200,350):
            trace.append(dict(iteration=step,coefficient_fraction=fraction,
                              mean_source_periodic_loss=float(np.mean(losses))))
    elapsed=ms(t)
    learned=1/(1+math.exp(-theta))
    return dict(actual_optimizer="scalar Adam 350 gradient updates",
                fit_source_originals=len(raw),
                fit_source_transition_pairs=sum(len(x) for x in raw),
                operator_target_labels_during_training=0,
                designer_periodic_objective_and_preference_injected=True,
                primitive_modulo_supplied=True,
                initialized_fraction=before,
                learned_fraction=learned,
                initialized_source_operator_candidates=initial_pre,
                learned_source_operator_candidates=[candidate(learned,x) for x in raw],
                weight_updates=350,
                training_wall_ms=elapsed,
                learning_trace=trace),learned,before
def gcd_same_observed_transitions(raw):
    t=time.perf_counter_ns(); g=0
    for current,following in raw:
        g=math.gcd(g,abs(int(following-current)))
    return g,ms(t)
def true_source_proof(k,m):
    evidence=certified_source(k,m)
    return evidence,bool(all(v["independent_dual_unsat"] for v in evidence))
def one(seed,k,fit,fraction,untrained):
    start=time.perf_counter_ns()
    observed=source_pairs(k,1000*k+seed,50)
    model=candidate(fraction,observed)
    knockout=candidate(untrained,observed)
    classical,classical_ms=gcd_same_observed_transitions(observed)
    neural_evidence,neural_pass=true_source_proof(k,model)
    classical_evidence,classical_pass=true_source_proof(k,classical)
    knockout_evidence,knockout_pass=true_source_proof(k,knockout)
    changed_evidence=certified_source(k,model,mutate=True)
    if not (neural_pass and classical_pass and
            not knockout_pass and changed_evidence[1]["independent_dual_sat"]):
        raise AssertionError("MODEL_GENERALIZATION_OR_ORIGINAL_DUAL_PROOF_FAILED")
    if model in PREVIOUS_OPTIONS or model!=k:
        raise AssertionError("NO_NEW_INSTANCE_OUTSIDE_FROZEN_OPERATOR_VOCAB")
    return dict(source_original_integer_step=k,
       original_Pre_AST="x = 1",
       original_Trans_AST=f"x_next = x + {k}",
       original_Post_AST=f"(x-1) mod {k} == 0",
       heldout_source_transition_pairs=len(observed),
       learned_candidate_AST=f"(x-1) mod {model} == 0",
       learned_candidate_parameter=model,
       learned_operator_is_OUTSIDE_frozen_2_20_candidate_list=True,
       independent_learned_full_original_Z3_cvc5_3VC=neural_evidence,
       learned_full_original_CERTIFIED=neural_pass,
       untrained_candidate_parameter=knockout,
       original_untrained_source_dual_3VC=knockout_evidence,
       untrained_full_original_CERTIFIED=knockout_pass,
       strong_classical_GCD=classical,
       strong_classical_gcd_ms=classical_ms,
       original_exact_classical_dual_3VC=classical_evidence,
       original_exact_classical_CERTIFIED=classical_pass,
       mutant_source_transition_k_plus_one_dual_SAT=changed_evidence,
       exact_invalid_source_mutant_REJECTED=changed_evidence[1]["independent_dual_sat"],
       whole_original_source_operator_generation_and_all_verification_wall_ms=ms(start))
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True)
    a=p.parse_args()
    records=[]
    for seed in range(20261022,20261026):
        fit,theta,untrained=self_supervised_fit(seed)
        for k in HOLDOUT_K:
            result=one(seed,k,fit,theta,untrained)
            records.append(dict(seed=seed,training_provenance=fit,**result))
            print("Q3_OOD_UNBOUNDED_OPERATOR_CONSTRUCTOR",seed,k,
                  "LEARNED",result["learned_candidate_parameter"],
                  "UNTRAINED",result["untrained_candidate_parameter"],
                  "CLASSICAL",result["strong_classical_GCD"],
                  "Z3_CVC5_SAFE",result["learned_full_original_CERTIFIED"],flush=True)
    report=dict(
      schema="neumann.q3.synthetic_source_meta_learned_modulus_constructor_frozen_list_ESCAPE.v1",
      study_level="CONTROLLED_SYNTHETIC_POSTHOC_OOD_NOT_EXTERNAL_FIRSTBLIND",
      experiment_train_k=list(TRAIN_K),
      frozen_previous_complete_model_operator_options=sorted(PREVIOUS_OPTIONS),
      previous_exhaustive_impossibility_PR_441_action_run=39625778248,
      source_training_heldout_step_parameters=list(HOLDOUT_K),
      training_examples_have_no_operator_labels=True,
      train_objective_hardcoded_PERIODICITY_and_max_period_bias=True,
      modulo_primitive_supplied_from_start=True,
      new_composed_operator_INSTANCE_OUTSIDE_finite_list=True,
      learned_OPERATOR_PRIMITIVE_CREATED=False,
      actual_model_weight_updates_per_seed=350,
      distinct_trained_models=4,
      heldout_test_count=len(records),
      new_out_of_dictionary_learned_native_complete_SAFE_count=sum(z["learned_full_original_CERTIFIED"] for z in records),
      untrained_model_native_complete_SAFE_count=sum(z["untrained_full_original_CERTIFIED"] for z in records),
      equivalent_strong_classical_exact_GCD_COMPLETE_SAFE_count=sum(z["original_exact_classical_CERTIFIED"] for z in records),
      mutated_original_source_Z3_cvc5_counterexamples=sum(z["exact_invalid_source_mutant_REJECTED"] for z in records),
      all_new_candidates_outside_the_19_preexisting_modulus_options=all(
        z["learned_operator_is_OUTSIDE_frozen_2_20_candidate_list"] for z in records),
      neural_training_wall_ms_sum=sum(z["training_provenance"]["training_wall_ms"]
                                       for z in records if z["source_original_integer_step"]==HOLDOUT_K[0]),
      source_matched_classical_candidate_extraction_ms_sum=sum(z["strong_classical_gcd_ms"] for z in records),
      no_controlled_10x_or_strong_classical_learned_superiority=True,
      original_source_semantics_exactly_checked_only_for_this_mathematical_family=True,
      global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
      all_original_source_trials=records)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for key in ("new_out_of_dictionary_learned_native_complete_SAFE_count",
                "untrained_model_native_complete_SAFE_count",
                "equivalent_strong_classical_exact_GCD_COMPLETE_SAFE_count",
                "mutated_original_source_Z3_cvc5_counterexamples",
                "neural_training_wall_ms_sum",
                "source_matched_classical_candidate_extraction_ms_sum"):
        print("Q3_GENUINE_FROZEN_LIST_ESCAPE",key,report[key],flush=True)
    print("Q3_GLOBAL_OPEN_STRONG_CLASSICAL_EQUAL",flush=True)
    assert report["new_out_of_dictionary_learned_native_complete_SAFE_count"]==len(records)==16
    assert report["untrained_model_native_complete_SAFE_count"]==0
    assert report["equivalent_strong_classical_exact_GCD_COMPLETE_SAFE_count"]==16
if __name__=="__main__":main()
