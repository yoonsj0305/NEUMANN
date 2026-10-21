"""Q3 causal source-counterexample refinement on PR442 official trained proposals.

Prior PR444: learned median-based candidate fails genuinely mixed source
transitions, while identical no-gradient source-conditioned candidate does
the same. Here transform independent ORIGINAL source verification into an
*active counterexample interface*: SAT exposes a violated concrete transition,
then a CLASSICAL gcd refinement shrinks the proposed modulus. This is
known counterexample-guided abstraction refinement (CEGAR), NOT a novel
trained operator. Compare trained vs same-rights no-training counterfactual
and strongest exact source-aware GCD. Reject genuine UNSAFE sources with
independent dual SAT reachability witness. Every original source formula and
semantic conclusion verified independently in Z3 and pinned cvc5.

Synthetic source families only. No claim Q3 learned necessity, real-world
generalization, 10x, or newly invented mathematical primitive.
"""
from __future__ import annotations
import argparse,hashlib,json,math,statistics,subprocess,time
from pathlib import Path
import numpy as np
import z3
from research.evidence.q3_frozen_mod_list_escape_20261022.train_source_conditioned_unbounded_modulus import candidate
HISTORICAL_SHA="7f2f88a67215bceefd7866fc5c82e350308001e7d8f3581d29028e5f13103457"
FIXED_THETA=6.0
FIXED_FRACTION=1/(1+math.exp(-FIXED_THETA))
def ms(t):return (time.perf_counter_ns()-t)/1e6
def dual_query(q):
    t=time.perf_counter_ns()
    solver=z3.Solver();solver.set(timeout=3200);solver.add(q)
    answer=str(solver.check())
    if answer not in ("sat","unsat"):
        raise RuntimeError("SOURCE_EXACT_Z3_UNKNOWN")
    data=None
    if answer=="sat":
        model=solver.model()
        data=model
    result=subprocess.run(["cvc5","--lang","smt2","--tlimit=3200"],
                          input=solver.to_smt2(),text=True,capture_output=True,timeout=8)
    res=[p.strip() for p in result.stdout.splitlines() if p.strip() in ("sat","unsat","unknown")]
    second=res[-1] if res else "UNKNOWN"
    if second!=answer:
        raise RuntimeError("ORIGINAL_INDEPENDENT_SOURCE_Z3_CVC5_DISAGREE_"+answer+"_"+second)
    return {"Z3":answer,"cvc5":second,"dual_verified":True,"wall_ms":ms(t)},data
def source(k,b,unsafe=False):
    x,xp=z3.Ints("source_state source_state_next")
    d=(k+1) if unsafe else k
    pre=(x==1)
    trans=z3.Or(xp==x+d,xp==x+b*k)
    post=(x-1)%k==0
    return x,xp,pre,trans,post
def queries(k,b,m,unsafe=False):
    x,xp,pre,trans,post=source(k,b,unsafe)
    inv=(x-1)%m==0
    invn=(xp-1)%m==0
    return [(z3.And(pre,z3.Not(inv)),"init"),
            (z3.And(inv,trans,z3.Not(invn)),"consecution"),
            (z3.And(inv,z3.Not(post)),"goal")]
def full_proof(k,b,m,unsafe=False):
    receipts=[];step_witness=None
    for q,name in queries(k,b,m,unsafe):
        receipt,model=dual_query(q)
        receipt["VC"]=name
        if name=="consecution" and model is not None:
            x,xp,_,tr,_=source(k,b,unsafe)
            current=model.eval(x,model_completion=True).as_long()
            following=model.eval(xp,model_completion=True).as_long()
            delta=following-current
            if delta not in ((k+1) if unsafe else k,b*k):
                raise RuntimeError("FAKE_SOURCE_CONSECUTION_COUNTEREXAMPLE")
            step_witness={"original_state":current,"original_next":following,
                          "real_original_transition_increment":delta,
                          "candidate_invariant_true_before":(current-1)%m==0,
                          "candidate_invariant_false_after":(following-1)%m!=0}
            if not(step_witness["candidate_invariant_true_before"] and
                   step_witness["candidate_invariant_false_after"]):
                raise RuntimeError("SMT_WITNESS_DOES_NOT_VIOLATE_REAL_INVARIANT")
        receipts.append(receipt)
    return receipts,step_witness
def source_truth(k,b,unsafe=False):
    x,xp,pre,trans,post=source(k,b,unsafe)
    violated=z3.And(pre,trans,z3.Not(z3.substitute(post,(x,xp))))
    proof,model=dual_query(violated)
    label="UNSAFE" if unsafe else "SAFE_NO_ONE_STEP_WITNESS"
    if (proof["Z3"]=="sat")!=unsafe:
        raise RuntimeError("ACTUAL_ORIGINAL_SOURCE_SAFETY_CONTRADICTION")
    witness=None
    if unsafe:
        cur=model.eval(x,model_completion=True).as_long()
        nex=model.eval(xp,model_completion=True).as_long()
        if cur!=1 or nex-cur!=k+1 or (nex-1)%k==0:
            raise RuntimeError("FALSE_REACHABLE_UNSAFE_SOURCE_WITNESS")
        witness={"initial":cur,"next":nex,"unsafe_step_delta":nex-cur}
    return {"original_source_verdict":label,"source_one_step_original_Z3_cvc5":proof,
            "genuine_reachable_original_unsafe_witness":witness}
def active_refine(k,b,initial,unsafe=False):
    t=time.perf_counter_ns()
    m=initial
    all_attempts=[]
    for iteration in range(7):
        if m<2:
            return {"status":"REJECT_NO_INDUCTIVE_MODULUS","attempts":all_attempts,
                    "candidate":m,"wall_ms":ms(t)}
        cert,witness=full_proof(k,b,m,unsafe)
        successful=all(z["Z3"]=="unsat" and z["cvc5"]=="unsat" for z in cert)
        entry={"candidate_modulus":m,"all_native_original_3VC":cert,
               "source_consecution_counterexample":witness,
               "whole_original_source_certified":successful}
        if successful:
            all_attempts.append(entry)
            return {"status":"CERTIFIED_ORIGINAL_FULL_3VC","candidate":m,
                    "attempts":all_attempts,
                    "verified_CEGAR_refinement_steps":iteration,
                    "wall_ms":ms(t)}
        if witness is None:
            all_attempts.append(entry)
            return {"status":"ABSTAIN_NO_REAL_CONSECUTION_REFINEMENT",
                    "candidate":m,"attempts":all_attempts,"wall_ms":ms(t)}
        refined=math.gcd(m,abs(witness["real_original_transition_increment"]))
        entry["certified_classical_gcd_refinement"]=refined
        if not(0<refined<m and refined<=m//2):
            raise RuntimeError("GCD_COUNTEREXAMPLE_REFINEMENT_NOT_STRICT_HALVING")
        all_attempts.append(entry)
        m=refined
    raise RuntimeError("SOURCE_COUNTEREXAMPLE_REFINEMENT_UNBOUNDED")
def observed_only(k,b,seed):
    rng=np.random.default_rng(seed)
    base=rng.integers(-55,56,size=50)
    pairs=np.column_stack([base,base+b*k]).astype(int)
    if set(pairs[:,1]-pairs[:,0])!={b*k}:
        raise RuntimeError("SOURCE_OBSERVATIONS_NOT_IDENTICAL")
    return pairs
def one(record,b,unsafe=False):
    t=time.perf_counter_ns()
    k=int(record["source_original_integer_step"])
    seed=int(record["seed"])
    fraction=float(record["training_provenance"]["learned_fraction"])
    pairs=observed_only(k,b,seed+37*k)
    learned=candidate(fraction,pairs)
    untrained=candidate(FIXED_FRACTION,pairs)
    no_fit=candidate(1.0,pairs)
    # Negative evidence matters: the learned REAL-valued coefficient may
    # round to b*k-1 when extrapolated to larger increments. Preserve raw
    # candidate, and use a SOURCE-OBSERVATION classical consistency gate
    # before admitting the integer proposal to the formal CEGAR loop.
    raw_candidates={"original_trained_model_prior":learned,
                    "untrained_same_architecture_prior":untrained,
                    "no_model_scale_statistic":no_fit}
    all_deltas=[abs(int(v-u)) for u,v in pairs]
    observed_only_gcd=math.gcd(*all_deltas)
    if observed_only_gcd!=b*k:
        raise RuntimeError("SOURCE_SAMPLES_MATCHED_CONSISTENCY_FAILED")
    preflight={}
    for name,raw_modulus in raw_candidates.items():
        consistent=(raw_modulus>=2 and all(d%raw_modulus==0 for d in all_deltas))
        admitted=raw_modulus if consistent else observed_only_gcd
        preflight[name]={"raw_unverified_model_output":raw_modulus,
                        "source_observation_consistent":consistent,
                        "classically_corrected_before_CEGAR":not consistent,
                        "actual_admitted_modulus":admitted,
                        "raw_candidate_changed_by_no_learning_calibration":raw_modulus!=admitted}
    actual=source_truth(k,b,unsafe)
    methods={}
    for name,row in preflight.items():
        methods[name]=active_refine(k,b,row["actual_admitted_modulus"],unsafe)
    # Strongest source-aware exact branch-GCD receives ENTIRE original
    # transition grammar, not just the observed branch.
    source_deltas=[(k+1) if unsafe else k,b*k]
    t2=time.perf_counter_ns()
    g=math.gcd(*source_deltas)
    exact_ms=ms(t2)
    control=active_refine(k,b,g,unsafe) if g>=2 else {
      "status":"REJECT_NO_INDUCTIVE_MODULUS","candidate":g,
      "attempts":[],"wall_ms":0.0}
    if not unsafe:
        if not all(z["status"]=="CERTIFIED_ORIGINAL_FULL_3VC" and z["candidate"]==k
                   for z in [*methods.values(),control]):
            raise RuntimeError("ACTUAL_SOURCE_SAFE_REPAIR_NOT_CERTIFIED_ALL_METHODS")
        if not all(z["verified_CEGAR_refinement_steps"]==1 for z in methods.values()):
            raise RuntimeError("NO_REAL_MODEL_OR_BASELINE_CONSECUTION_FEEDBACK")
    else:
        if actual["original_source_verdict"]!="UNSAFE":
            raise RuntimeError("UNSAFE_SOURCE_WRONGLY_DECLARED_SAFE")
        if any(z["status"]=="CERTIFIED_ORIGINAL_FULL_3VC" for z in [*methods.values(),control]):
            raise RuntimeError("FALSE_ORIGINAL_SOURCE_SAFE_ON_REACHABLE_UNSAFE")
    return {"original_step_k":k,"visible_step_multiple":b,
       "source_category":"REACHABLE_UNSAFE" if unsafe else "HIDDEN_SAFE_BRANCH",
       "original_Pre_AST":"x == 1",
       "original_Trans_AST":f"x_next = x + {(k+1) if unsafe else k} OR x_next = x + {b*k}",
       "original_Post_AST":f"(x-1) mod {k} == 0",
       "identical_transition_observation_count":len(pairs),
       "all_observations_contain_ONLY_large_step":True,
       "historical_trained_weight":fraction,
       "source_truth_independent_Z3_cvc5":actual,
       "same_observations_learned_and_fixed_and_no_model":True,
       "source_observation_only_integer_calibration":preflight,
       "observation_only_exact_GCD_before_original_source_consultation":observed_only_gcd,
       "candidate_prior_methods_and_independent_counterexample_proofs":methods,
       "source_native_two_branch_gcd":g,
       "source_native_GCD_source_extraction_ms":exact_ms,
       "source_native_exact_GCD_baseline_original_proof":control,
       "full_experiment_work_wall_ms":ms(t)}
def main():
    p=argparse.ArgumentParser()
    for key in ("official","out"):p.add_argument("--"+key,required=True)
    args=p.parse_args()
    data=Path(args.official).read_bytes()
    if hashlib.sha256(data).hexdigest()!=HISTORICAL_SHA:
        raise RuntimeError("IMMUTABLE_PRIOR_TRAINED_MODEL_SHA_DRIFT")
    past=json.loads(data)
    if past["schema"]!="neumann.q3.synthetic_source_meta_learned_modulus_constructor_frozen_list_ESCAPE.v1":
        raise RuntimeError("IMPORTED_SOURCE_ARCHIVE_WRONG")
    history=past["all_original_source_trials"]
    if len(history)!=16 or len({(x["seed"],x["source_original_integer_step"]) for x in history})!=16:
        raise RuntimeError("HISTORICAL_TRAINED_MODEL_ORIGINAL_IDENTITY_CHANGED")
    safe_rows=[one(z,b,False) for z in history for b in (2,3)]
    unsafe_rows=[one(z,2,True) for z in history]
    # Exactly the SAME observations are consistent with a SAFE hidden branch
    # and an UNSAFE hidden branch. No observation-only learner can decide
    # program safety before inspecting original source or requesting a proof.
    for case in unsafe_rows:
        match=next(p for p in safe_rows if p["original_step_k"]==case["original_step_k"] and
                   p["visible_step_multiple"]==case["visible_step_multiple"] and
                   p["historical_trained_weight"]==case["historical_trained_weight"])
        if (match["identical_transition_observation_count"]!=case["identical_transition_observation_count"]
            or match["source_truth_independent_Z3_cvc5"]["original_source_verdict"]==
                 case["source_truth_independent_Z3_cvc5"]["original_source_verdict"]):
            raise RuntimeError("OBSERVATION_ALIASING_IMPOSSIBILITY_NOT_GENUINE")
    r=dict(schema="neumann.q3.official_trained_operator_source_cex_active_repair_observation_aliasing.v1",
      actual_archived_training_source_SHA256=HISTORICAL_SHA,
      prototype_scope="POSTHOC CONTROLLED SYNTHETIC SOURCES NOT REAL EXTERNAL FIRSTBLIND",
      hidden_safe_originals=len(safe_rows),
      hidden_unsafe_originals=len(unsafe_rows),
      originally_frozen_learned_prior_requires_CEGAR=True,
      independently_proved_hidden_safe_learned_repair=sum(z["candidate_prior_methods_and_independent_counterexample_proofs"]["original_trained_model_prior"]["status"]=="CERTIFIED_ORIGINAL_FULL_3VC" for z in safe_rows),
      independently_proved_hidden_safe_same_architecture_no_training_repair=sum(z["candidate_prior_methods_and_independent_counterexample_proofs"]["untrained_same_architecture_prior"]["status"]=="CERTIFIED_ORIGINAL_FULL_3VC" for z in safe_rows),
      independently_proved_hidden_safe_NO_MODEL_scale_repair=sum(z["candidate_prior_methods_and_independent_counterexample_proofs"]["no_model_scale_statistic"]["status"]=="CERTIFIED_ORIGINAL_FULL_3VC" for z in safe_rows),
      independently_proved_hidden_safe_source_GCD=sum(z["source_native_exact_GCD_baseline_original_proof"]["status"]=="CERTIFIED_ORIGINAL_FULL_3VC" for z in safe_rows),
      independently_proved_reachable_original_unsafe=sum(z["source_truth_independent_Z3_cvc5"]["original_source_verdict"]=="UNSAFE" for z in unsafe_rows),
      false_certified_safe_on_reachable_unsafe=sum(z["candidate_prior_methods_and_independent_counterexample_proofs"]["original_trained_model_prior"]["status"]=="CERTIFIED_ORIGINAL_FULL_3VC" for z in unsafe_rows),
      observationally_indistinguishable_safe_vs_unsafe_source_pairs=len(unsafe_rows),
      additional_source_information_or_independent_verification_needed_to_distinguish_twins=True,
      raw_gradient_models_never_credited_for_classical_observation_calibration=True,
      original_model_integer_proposals_requiring_calibration=sum(
        q["source_observation_only_integer_calibration"]["original_trained_model_prior"]["classically_corrected_before_CEGAR"]
        for q in safe_rows),
      classical_gcd_strict_halving_max_feedback_queries_per_safe_original=1,
      classical_gcd_feedback_general_worst_case_log2_bound=True,
      full_origin_verified_source_and_proof_cost_ms=sum(z["full_experiment_work_wall_ms"] for z in safe_rows+unsafe_rows),
      all_these_methods_reuse_existing_modulo_primitive=True,
      feedback_update_is_CLASSICAL_not_learned=True,
      trained_model_not_causally_needed_under_identical_no_fit_counterfactual=True,
      full_frontier_model_10x_and_cross_domain_transfer_UNPROVEN=True,
      global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
      safe_original_full_certificate_ledger=safe_rows,
      unsafe_original_full_rejection_ledger=unsafe_rows)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    for key in ("independently_proved_hidden_safe_learned_repair",
                "independently_proved_hidden_safe_same_architecture_no_training_repair",
                "independently_proved_hidden_safe_source_GCD",
                "independently_proved_reachable_original_unsafe",
                "observationally_indistinguishable_safe_vs_unsafe_source_pairs",
                "false_certified_safe_on_reachable_unsafe"):
        print("Q3_VERIFIER_GUIDED_REPAIR_AND_OBSERVABILITY_LIMIT",key,r[key],flush=True)
    print("RESULTS_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
    print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
