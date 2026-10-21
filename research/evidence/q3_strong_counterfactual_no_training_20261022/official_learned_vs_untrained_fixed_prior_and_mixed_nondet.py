"""NEUMANN Q3: counterfactual causal necessity test of an archived learned AST constructor.

Original official PR442 learned 16 source cases were held-out synthetic x'=x+k,
k∈{23,29,31,37}. The "model" constructs m=round(f*median(|x'-x|)).
Its input scaler ALREADY has k. We test source-independent UNTRAINED
theta=6 (sigmoid(theta)~=0.9975), and the no-model f=1 against identical
source pairs. All proposals get fresh genuine original Z3+cvc5 3VC.

Then deliberately change the original transition FAMILY to nondeterministic
x'∈{x+k,x+2k}, original Pre x=1, original Post (x-1) mod k=0.
50 genuinely valid transition observations with 25 of EACH source step.
The learned / untrained normalized-median proposals no longer remain
inductive, while exact classical GCD does. Independent Z3+cvc5 original
SAT/UNSAT witnesses enforce all verdicts.

Important: This is a POSTHOC scientific knockout on controlled synthetic
sources, not a new first-source-body-blind real program. No model weight
updates occur here. Does not alter historical PR442/443 evidence.
"""
from __future__ import annotations
import argparse, hashlib, json, math, statistics, time
from pathlib import Path
import numpy as np
import z3
from research.evidence.q3_frozen_mod_list_escape_20261022.train_source_conditioned_unbounded_modulus import (
    candidate, source_pairs, gcd_same_observed_transitions
)
from research.evidence.q3_modular_operator_selection_20261022.learn_mod_operator_and_dual_prove import certified_source
OLD_SHA="7f2f88a67215bceefd7866fc5c82e350308001e7d8f3581d29028e5f13103457"
THETA=6.0
FROZEN_NO_FIT_FRACTION=1.0/(1.0+math.exp(-THETA))
def ms(t):return (time.perf_counter_ns()-t)/1e6
def assert_true(v,msg):
    if not v:raise AssertionError(msg)
def check(k,m,heterogeneous=False):
    if not heterogeneous:
        return certified_source(k,m)
    x,xp=z3.Ints("heterogeneous_source_x heterogeneous_source_x_next")
    inv=(x-1)%m==0
    next_inv=(xp-1)%m==0
    conditions=(
        z3.And(x==1,z3.Not(inv)),
        z3.And(inv,z3.Or(xp==x+k,xp==x+2*k),z3.Not(next_inv)),
        z3.And(inv,z3.Not((x-1)%k==0)))
    import subprocess
    receipts=[]
    for name,phi in zip(("init","consecution","goal"),conditions):
        sl=z3.Solver();sl.set(timeout=3000);sl.add(phi)
        z3_answer=str(sl.check())
        try:
            p=subprocess.run(["cvc5","--lang","smt2","--tlimit=3000"],
                input=sl.to_smt2(),text=True,capture_output=True,timeout=6)
            outputs=[s.strip() for s in p.stdout.splitlines()
                     if s.strip() in ("sat","unsat","unknown")]
            cvc5_answer=outputs[-1] if outputs else "ERROR_OR_UNKNOWN"
        except Exception as e:cvc5_answer="EXCEPTION:"+str(e)[:130]
        receipts.append(dict(name=name,Z3=z3_answer,cvc5=cvc5_answer,
            independent_dual_unsat=(z3_answer==cvc5_answer=="unsat"),
            independent_dual_sat=(z3_answer==cvc5_answer=="sat")))
    return receipts
def safe(p):
    return len(p)==3 and all(x["independent_dual_unsat"] for x in p)
def bad_step(p):
    return len(p)==3 and p[0]["independent_dual_unsat"] and p[1]["independent_dual_sat"]
def mixed_pairs(k,seed):
    rng=np.random.default_rng(seed+19)
    x=rng.integers(-40,41,50)
    inc=np.array([k]*25+[2*k]*25,dtype=np.int64)
    rng.shuffle(inc)
    assert len(np.unique(inc))==2
    return np.column_stack([x,x+inc])
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--official",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    raw=Path(args.official).read_bytes()
    assert_true(hashlib.sha256(raw).hexdigest()==OLD_SHA,
                "OFFICIAL_PR442_SOURCE_TRAINING_RECEIPT_SHA_CHANGED")
    prior=json.loads(raw)
    assert_true(prior["schema"]=="neumann.q3.synthetic_source_meta_learned_modulus_constructor_frozen_list_ESCAPE.v1",
                "NOT_THE_ACTUAL_PR442_SOURCE_TRAINED_RUN")
    original_trials=prior["all_original_source_trials"]
    assert_true(len(original_trials)==16,"ORIGINAL_16_SOURCE_TRIALS_CHANGED")
    assert_true(len({(a["seed"],a["source_original_integer_step"]) for a in original_trials})==16,
                "NON_DISTINCT_ORIGINAL_SOURCE_TRIALS")
    cases=[]
    for old in original_trials:
        seed=int(old["seed"]);k=int(old["source_original_integer_step"])
        assert_true(k in (23,29,31,37),"ORIGINAL_OOD_CLASS_CHANGED")
        assert_true(old["learned_full_original_CERTIFIED"],"HISTORICAL_TRAINED_PROOF_NOT_PASS")
        f=float(old["training_provenance"]["learned_fraction"])
        assert_true(0<f<1,"NOT_A_TRAINED_SIGMOID_COEFFICIENT")
        pairs=source_pairs(k,1000*k+seed,50)
        t=time.perf_counter_ns()
        frozen_untrained=candidate(FROZEN_NO_FIT_FRACTION,pairs)
        no_model=candidate(1.0,pairs)
        trained=candidate(f,pairs)
        gcd_value,gcd_ms=gcd_same_observed_transitions(pairs)
        construct_ms=ms(t)
        assert_true(trained==old["learned_candidate_parameter"],
                    "HISTORICAL_TRAINED_ORIGINAL_SOURCE_REPLAY_MISMATCH")
        certificates={name:check(k,m) for name,m in (
            ("historical_frozen_learned",trained),
            ("untrained_theta6_same_architecture",frozen_untrained),
            ("constant_one_no_model",no_model),
            ("exact_gcd",gcd_value))}
        assert_true(all(safe(r) for r in certificates.values()),
                    "UNTRAINED_COUNTERFACTUAL_OR_GCD_ORIGINAL_NOT_PROVED")
        # New semantic transfer stress (NOT a new preregistered external family).
        observations=mixed_pairs(k,seed)
        deltas=observations[:,1]-observations[:,0]
        assert_true(int(np.sum(deltas==k))==int(np.sum(deltas==2*k))==25,
                    "MIXED_ORIGINAL_SOURCE_GENERATOR_CHANGED")
        t2=time.perf_counter_ns()
        m_trained=candidate(f,observations)
        m_fixed=candidate(FROZEN_NO_FIT_FRACTION,observations)
        m_nomodel=candidate(1.,observations)
        m_gcd,mgcd_ms=gcd_same_observed_transitions(observations)
        source_selection_ms=ms(t2)
        mixed_cert={name:check(k,m,True) for name,m in (
            ("historical_frozen_learned",m_trained),
            ("untrained_theta6_same_architecture",m_fixed),
            ("constant_one_no_model",m_nomodel),
            ("exact_gcd",m_gcd))}
        assert_true(bad_step(mixed_cert["historical_frozen_learned"]),
                    "MIXED_ORIGINAL_TRAINED_MODEL_DID_NOT_FAIL_AS_PREDICTED")
        assert_true(bad_step(mixed_cert["untrained_theta6_same_architecture"]),
                    "MIXED_FIXED_MODEL_DID_NOT_FAIL_AS_PREDICTED")
        assert_true(bad_step(mixed_cert["constant_one_no_model"]),
                    "MIXED_NO_MODEL_MEDIAN_DID_NOT_FAIL_AS_PREDICTED")
        assert_true(safe(mixed_cert["exact_gcd"]),
                    "MIXED_ORIGINAL_EXACT_GCD_DID_NOT_PROVE")
        row=dict(seed=seed,original_k=k,
            immutable_PR442_original_model_fraction=f,
            no_gradient_theta=THETA,
            no_gradient_fraction=FROZEN_NO_FIT_FRACTION,
            deterministic_original_source_operator_values=dict(
                trained=trained,untrained_theta6=frozen_untrained,
                constant_one=no_model,exact_gcd=gcd_value),
            deterministic_original_Z3_cvc5_3VC=certificates,
            deterministic_no_gradient_same_architecture_safe=True,
            mixed_source_original_AST=dict(Pre="x=1",
                Trans=f"x_next=x+{k} OR x_next=x+{2*k}",
                Post=f"(x-1) mod {k} == 0"),
            mixed_source_observations_each_branch=25,
            mixed_original_source_operator_values=dict(
                trained=m_trained,untrained_theta6=m_fixed,
                constant_one=m_nomodel,exact_gcd=m_gcd),
            mixed_original_Z3_cvc5_3VC=mixed_cert,
            mixed_trained_consecution_bad_dual_SAT=True,
            mixed_gcd_full_source_original_dual_SAFE=True,
            new_source_mixed_representations_not_seen_in_PR442_training=True,
            candidate_selection_wall_ms=construct_ms,
            mixed_candidate_selection_wall_ms=source_selection_ms,
            strong_GCD_mixed_extraction_ms=mgcd_ms)
        cases.append(row)
        print("Q3_CAUSAL_UNTRAINED_PRIOR",k,seed,
              "TRAINED",trained,"NO_FIT",frozen_untrained,
              "GCD",gcd_value,"DETERMINISTIC_SAFE",True,
              "MIXED_TRAINED",m_trained,"MIXED_GCD",m_gcd,
              "MIXED_TRAINED_UNSAFE",True,flush=True)
    report=dict(schema="neumann.q3_PR442_untrained_fixed_prior_and_mixed_semantics_independent_native_replay.v1",
        immutable_historical_PR442_raw_SHA256=OLD_SHA,
        original_archived_learned_model_trial_count=16,
        original_deterministic_source_learned_safe=16,
        original_deterministic_source_untrained_theta6_safe=16,
        original_deterministic_source_constant_one_no_model_safe=16,
        original_deterministic_source_exact_GCD_safe=16,
        semantic_shift_nondeterministic_source_originals=16,
        mixed_source_frozen_learned_failed_consecution_independent_SAT=16,
        mixed_source_untrained_theta6_failed_consecution_independent_SAT=16,
        mixed_source_constant_one_failed_consecution_independent_SAT=16,
        mixed_source_GCD_complete_original_SAFE_independent_3VC=16,
        old_historical_random_initialization_ablation_succeeded=0,
        causal_interpretation="An untrained fixed scale f=sigmoid(6) uses identical built-in source magnitude and proves all deterministic source goals. Therefore gradient training is not necessary for this controlled source family under this stronger no-training counterfactual. For heterogenous nondeterministic source steps, median-based proposer including the trained fraction fails independently; exact GCD retains original safety. This is POSTHOC not fresh real-source firstblind.",
        trained_learning_NOT_CAUSALLY_NECESSARY_under_fixed_prior_comparator=True,
        actual_new_mathematical_primitive_discovered=False,
        strongest_classical_exact_GCD_more_robust_in_shift=True,
        baseline_integrity_all_same_observations_and_full_native_authority=True,
        previous_PR442_training_cost_is_nonzero_and_not_needed=True,
        complete_end_to_end_frontier_10x_UNPROVEN=True,
        global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
        source_truth_ledger=cases)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for key in ("original_deterministic_source_untrained_theta6_safe",
                "original_deterministic_source_constant_one_no_model_safe",
                "mixed_source_frozen_learned_failed_consecution_independent_SAT",
                "mixed_source_GCD_complete_original_SAFE_independent_3VC"):
        print("Q3_STRONG_NO_TRAIN_CAUSAL_TEST",key,report[key],flush=True)
    print("GLOBAL_Q3_Q4_Q6_STILL_OPEN")
if __name__=="__main__":main()
