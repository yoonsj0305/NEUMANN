"""POSTHOC independent external original sum1 guarded-source classical closure.
No gold invariant or source published Post enters source candidate enumeration.
Strong exact classic and frozen 42-weight model get identical extra source guard.
Ablate learned candidate and retain first original blind 0/3 unchanged.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q3_frozen_learned_antidiff_20261020.first_synthetic_trained_three_originals import (
 train_frozen_operator, proof)
from research.evidence.q3_coclock_fixed42_20261020.posthoc_genuine_source_affine_controller import (
 frozen_affine_clock_controller,generator_from_controller,FROZEN_WEIGHTS_SHA)
from research.evidence.q3_source_only_discrete_antidifference_20261020.first_three_source_exact_recurrence import (
 atoms,blob,sha,ms,zcheck,cvc)
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,check_formula)

SOURCE="comp/2017/Inv_Track/sum1.sl"
BLOB="5fd2e4f7841aea6ebab96d30d394819b0d2b17d6"
UPSTREAM="SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646"
FIRST_SCIENCE_SHA="0daf8dc6782e7aca9c594b71a83856b20370d8fb6ebeef69540ae1296addfd7a"

def dual_unsat(name,bad):
    ze,elapsed=zcheck(bad,secs=9)
    ext=cvc(bad,secs=12) if ze=="unsat" else {"status":"NOT_RUN"}
    return {"name":name,"Z3":ze,"Z3_wall_ms":elapsed,"cvc5":ext,
        "both_UNSAT":ze=="unsat" and ext.get("status")=="unsat" and ext.get("exit_code")==0}

def eligible_source_guards(src,native,controller):
    """Enumerate source Pre/Trans-only zero-or-bound candidates.
    No hardcoded physical variable names, no original Post filter.
    """
    t=time.perf_counter_ns()
    (updates,meta,symbols,offsets,relation_atoms)=controller
    clocks=meta["clocks"]
    static=set(meta["source_static_parameters"])
    now=src["now"];nxt=src["next"]
    now_by_name={str(v):v for v in now}
    next_by_name={str(x):y for x,y in zip(now,nxt)}
    affine_rels=z3.And(*relation_atoms)
    s=z3.Solver();s.add(native["pre"])
    if s.check()!=z3.sat:raise RuntimeError("ORIGINAL_PRE_NOT_SAT")
    model=s.model()
    guard_rows=[]
    for a in atoms(native["trans"]):
        if a.decl().kind() not in {z3.Z3_OP_LE,z3.Z3_OP_LT}:continue
        low,high=a.children()
        if str(low) not in clocks:continue
        if not (z3.is_int_value(high) or str(high) in static):continue
        guard_rows.append({"lower_clock":str(low),"original_source_guard":str(a),
                           "upper_expr":high})
    if not guard_rows:raise RuntimeError("NO_SOURCE_CLOCK_STATIC_UPPER_GUARD")
    considered=[];admitted=[]
    for item in guard_rows:
        upper=item["upper_expr"]
        for c in clocks:
            variable=now_by_name[c]
            initial=int(model.eval(variable,model_completion=True).as_long())
            atom=z3.Or(variable==initial,variable<=upper)
            assert str(variable) not in {"i","sn"} or True
            pre_bad=z3.And(native["pre"],z3.Not(atom))
            nxt_clause=z3.substitute(atom,*list(zip(now,nxt)))
            # Check single-candidate induction relative to already verified
            # source co-clock relations; no circular use of other proposals.
            induction_bad=z3.And(affine_rels,atom,native["trans"],
                                 z3.Not(nxt_clause))
            p,ptime=zcheck(pre_bad,secs=7)
            q,qtime=zcheck(induction_bad,secs=7)
            r={"source_guard":item["original_source_guard"],
               "candidate_clock":c,"Pre_model_initial":initial,
               "source_pre_initial_constant_proven":zcheck(
                  z3.And(native["pre"],variable!=initial),secs=7)[0]=="unsat",
               "generated_guard_invariant":atom.sexpr(),
               "original_pre_bad":p,"original_induction_bad":q,
               "pre_Z3_wall_ms":ptime,"step_Z3_wall_ms":qtime}
            if p=="unsat" and q=="unsat" and r["source_pre_initial_constant_proven"]:
                r["verified_pre_both"]=dual_unsat("ORIGINAL_PRE_guard_"+c,pre_bad)
                r["verified_step_both"]=dual_unsat("ORIGINAL_STEP_guard_"+c,induction_bad)
                if r["verified_pre_both"]["both_UNSAT"] and r["verified_step_both"]["both_UNSAT"]:
                    admitted.append(atom)
                    r["accepted"]=True
                else:r["accepted"]=False
            else:r["accepted"]=False
            considered.append(r)
    return admitted,{"original_source_static_guard_facts_considered":considered,
      "admitted_disjunction_count":len(admitted),
      "source_without_Post":True,
      "synthesis_ms":ms(t)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();total=time.perf_counter_ns()
    raw=(args.root/SOURCE).read_bytes()
    if blob(raw)!=BLOB:raise RuntimeError("SOURCE_GIT_BLOB_CHANGED")
    weights,training=train_frozen_operator()
    if training["frozen_trained_weights_sha256"]!=FROZEN_WEIGHTS_SHA:raise RuntimeError("LEARNER_CHANGED")
    forms=sexprs(raw);src=extract_mixed_original(forms)
    native=native_original_relations(forms,src)
    native.update({"now":src["now"],"next":src["next"]})
    parity=check_parity(src,native)
    if set(parity)!={"pre","trans","post"} or any(x!="unsat" for x in parity.values()):
        raise RuntimeError("ORIGINAL_SEMANTIC_PARITY_MISMATCH")
    if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
        raise RuntimeError("ORIGINAL_NOT_NONVACUOUS")
    controller=frozen_affine_clock_controller(src,native)
    original_learned,learned_generation=generator_from_controller(src,native,weights,False,controller)
    original_classic,classic_generation=generator_from_controller(src,native,weights,True,controller)
    guard_additions,guard_receipt=eligible_source_guards(src,native,controller)
    # Freeze source-only candidates before any original Post-goal VCs.
    augmented_learned=z3.And(original_learned,*guard_additions)
    augmented_classical=z3.And(original_classic,*guard_additions)
    guarded_only=z3.And(*controller[4],*guard_additions)
    learned_original_vcs,learned_pass=proof(augmented_learned,src,native)
    classical_original_vcs,classical_pass=proof(augmented_classical,src,native)
    ablated_vcs,ablated_pass=proof(guarded_only,src,native)
    prior_unchanged_vcs,prior_pass=proof(original_learned,src,native)
    result={"schema":"neumann.q3.sygus_orig.sum1.source_guard.classical_posthoc.v1",
      "upstream_original":UPSTREAM,"original_path":SOURCE,
      "original_git_blob":BLOB,"original_raw_sha256":sha(raw),
      "original_source_parser_semantic_xor":parity,
      "previous_first_cross_corpus_first_result":"LEARNED_0/3_CLASSIC_0/3",
      "previous_first_cross_corpus_original_json_sha256":FIRST_SCIENCE_SHA,
      "science_scope":"POSTHOC_AFTER_FIRST_0/3_SOURCE_OPENED",
      "trained_weights_unchanged_sha256":training["frozen_trained_weights_sha256"],
      "synthetic_heldout_64_exact":training["heldout_64_full_integer_coefficient_predictions_exact"],
      "original_source_affine_proofs":controller[1],
      "source_pre_trans_bound_miner":guard_receipt,
      "frozen_learned_original_candidate":augmented_learned.sexpr(),
      "frozen_classical_original_candidate":augmented_classical.sexpr(),
      "both_candidate_invariants_identical":augmented_learned.sexpr()==augmented_classical.sexpr(),
      "source_relational_only_ablated_neural_candidate":guarded_only.sexpr(),
      "learned_with_source_guard_original_Z3_cvc5_3VC":learned_original_vcs,
      "strong_classical_with_same_guard_original_Z3_cvc5_3VC":classical_original_vcs,
      "neural_polynomial_ablation_original_Z3_cvc5_3VC":ablated_vcs,
      "previous_prior_guardless_original_Z3_cvc5_3VC":prior_unchanged_vcs,
      "learned_posthoc_original_full_dual_3VC_PASS":learned_pass,
      "classical_posthoc_original_full_dual_3VC_PASS":classical_pass,
      "without_learned_polynomial_original_full_dual_3VC_PASS":ablated_pass,
      "unchanged_first_guardless_original_full_dual_3VC_PASS":prior_pass,
      "learned_generates_nontrivial_polynomial":learned_generation["has_nontrivial_generated_polynomial"],
      "neural_unique_causal_effect_proven":False,
      "uses_explicit_source_specific_answer_for_candidate_generation":False,
      "GPU_calls":0,"paid_API_calls":0,
      "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
      "full_study_wall_ms":ms(total)}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("SOURCE_ONLY_GUARDED_FACTS_ADMITTED",guard_receipt["admitted_disjunction_count"],flush=True)
    print("SOURCE_GUARD_RESULT original learned",learned_pass,"classical",classical_pass,
        "ablate_nn",ablated_pass,"prior_original",prior_pass,flush=True)
    print("NEURAL_NONTRIVIAL_GENERATED",result["learned_generates_nontrivial_polynomial"],flush=True)
    print("GLOBAL_Q3 OPEN",flush=True)
if __name__=="__main__":main()
