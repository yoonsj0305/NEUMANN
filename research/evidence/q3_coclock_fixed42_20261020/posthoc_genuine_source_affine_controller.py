"""NEUMANN Q3 co-clock source-affine rescue of frozen 42-weight integrator.
Posthoc after the THIRD test source was opened. First 2/3 failure is immutable.
No weights changed, no training on originals, no source post in generation.
The same source-controller serves both learned and exact classical methods.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import sympy as sp
import z3
from research.evidence.q3_frozen_learned_antidiff_20261020.first_synthetic_trained_three_originals import (
 COHORT,train_frozen_operator,DEG_DELTA,DEG_F,SCALE,proof)
from research.evidence.q3_source_only_discrete_antidifference_20261020.first_three_source_exact_recurrence import (
 blob,sha,ms,atoms,derive_updates,integer_eq,zcheck,cvc)
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,check_formula)

FROZEN_WEIGHTS_SHA="563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78"
FIRST_CI="https://github.com/yoonsj0305/NEUMANN/actions/runs/39424234515"
FIRST_RAW_JSON_SHA="993e7ce6ce116bedce68efa66ada4a42ea1913629730ec1b914bdfc60316f513"
EXPECTED={"initial","consecution","post"}

def independent(name,claim):
    z,elapsed=zcheck(claim,secs=8)
    other=cvc(claim,secs=12) if z=="unsat" else {"status":"NOT_RUN"}
    good=z=="unsat" and other.get("status")=="unsat" and other.get("exit_code")==0
    return {"name":name,"native_Z3":z,"Z3_wall_ms":elapsed,
      "independent_cvc5":other,"independently_proved":good}

def frozen_affine_clock_controller(src,native):
    start=time.perf_counter_ns()
    updates,source_entailment_ms=derive_updates(src,native)
    now=src["now"];nxt=src["next"]
    names=[str(x) for x in now]
    symbolic={name:sp.Symbol(name,integer=True) for name in names}
    static=sorted([v for v in names if updates[v]==symbolic[v]])
    clocks=sorted([v for v in names if sp.expand(updates[v]-symbolic[v])==1])
    if not clocks:raise ValueError("NO_SOURCE_INCREMENTING_CLOCK")
    canonical=clocks[0]
    source_pre=z3.Solver();source_pre.set(timeout=8000);source_pre.add(native["pre"])
    if source_pre.check()!=z3.sat:raise ValueError("SOURCE_PRE_NOT_SAT")
    model=source_pre.model()
    rel=[]
    normalization={}
    candidate_atoms=[]
    for name in clocks[1:]:
        left=z3.Int(name)-z3.Int(canonical)
        initial_offset=int(model.eval(left,model_completion=True).as_long())
        rel_now=left==initial_offset
        pos_now={str(x):x for x in now}
        pos_next={str(x):y for x,y in zip(now,nxt)}
        rel_next=(
          pos_next[name]-pos_next[canonical]==initial_offset)
        premise=independent("ORIGINAL_PRE_CLOCK_OFFSET_"+name,
            z3.And(native["pre"],z3.Not(rel_now)))
        step=independent("ORIGINAL_TRANS_PRESERVE_CLOCK_OFFSET_"+name,
            z3.And(rel_now,native["trans"],z3.Not(rel_next)))
        wrong,wrong_time=zcheck(z3.And(native["pre"],left==initial_offset+1),secs=5)
        if not premise["independently_proved"] or not step["independently_proved"] or wrong!="unsat":
            raise ValueError("SOURCE_CO_CLOCK_OFFSET_NOT_VERIFIABLE:"+name)
        # Candidate invariant derived ONLY from actual original Pre and Trans.
        normalization[symbolic[name]]=symbolic[canonical]+sp.Integer(initial_offset)
        candidate_atoms.append(rel_now)
        rel.append({"co_clock":name,"canonical_clock":canonical,
          "source_pre_offset":initial_offset,
          "original_Pre_offset_obligation":premise,
          "original_Trans_preservation_obligation":step,
          "wrong_offset_plus_one_initial_Z3":wrong,
          "wrong_offset_plus_one_Z3_ms":wrong_time})
    return updates,{"clocks":clocks,"canonical_clock":canonical,
      "source_static_parameters":static,
      "co_clock_verified_relations":rel,
      "source_transition_extraction_Z3_ms":source_entailment_ms,
      "original_source_next_updates":{v:str(e) for v,e in updates.items()},
      "controller_wall_ms":ms(start)},symbolic,normalization,candidate_atoms

def generator_from_controller(src,native,weights,exact_classical,controller):
    start=time.perf_counter_ns()
    updates,meta,sym,offset_substitution,initial_atoms=controller
    t=sym[meta["canonical_clock"]]
    static={sym[name] for name in meta["source_static_parameters"]}
    clock_names=set(meta["clocks"])
    parts=list(initial_atoms)
    new=[];rejected=[]
    for var in [str(x) for x in src["now"]]:
        if var in clock_names or var in meta["source_static_parameters"]:continue
        delta=sp.expand(updates[var]-sym[var])
        reduced=sp.expand(delta.subs(offset_substitution,simultaneous=True))
        if reduced==0 or not reduced.free_symbols.issubset({t,*static}):continue
        try:poly=sp.Poly(reduced,t)
        except Exception:continue
        if poly.degree()<0 or poly.degree()>DEG_DELTA:continue
        if exact_classical:
            tau=sp.Symbol("_exact_sum_tau_",integer=True)
            F=sp.expand(sp.summation(reduced.subs(t,tau),(tau,0,t-1)))
            method="SYMPY_EXACT_SUM_SOURCE_ONLY"
        else:
            # KEY GATE: use only the frozen 42 trained parameters to propose F.
            vector=[sp.expand(poly.nth(d)) for d in range(DEG_DELTA+1)]
            columns=[sp.expand(sum(sp.Integer(int(weights[k,d]))*vector[k]
                     for k in range(DEG_DELTA+1))/SCALE)
                     for d in range(DEG_F+1)]
            F=sp.expand(sum(columns[d]*t**d for d in range(DEG_F+1)))
            method="FROZEN_TRAINED_42_WEIGHT_FIRST_PROPOSAL"
        residual=sp.expand(F.subs(t,t+1)-F-reduced)
        equation,display=integer_eq(sym[var]-F,list(sym.values()))
        pre_status,pre_ms=zcheck(z3.And(native["pre"],z3.Not(equation)),secs=5)
        entry={"accumulator":var,"canonical_clock":str(t),
          "source_unmodified_delta":str(delta),
          "source_pre_trans_proved_reduced_delta":str(reduced),
          "generated_primitive_polynomial":str(F),
          "exact_finite_difference_residual":str(residual),
          "original_pre_bad":pre_status,"precheck_ms":pre_ms,
          "integration_mechanism":method,**display}
        if residual==0 and pre_status=="unsat":
            parts.append(equation);new.append(entry)
        else:rejected.append(entry)
    for name in sorted(clock_names | set(meta["source_static_parameters"])):
        domain=z3.Int(name)>=0
        res,_=zcheck(z3.And(native["pre"],z3.Not(domain)),secs=5)
        if res=="unsat":
            parts.append(domain);new.append({"original_pre_positive_domain":str(domain)})
    for e in atoms(native["trans"]):
        if e.decl().kind()!=z3.Z3_OP_LT:continue
        lo,hi=e.children()
        if str(lo)!=meta["canonical_clock"]:continue
        if not(z3.is_int_value(hi) or str(hi) in meta["source_static_parameters"]):continue
        bound=lo<=hi
        res,_=zcheck(z3.And(native["pre"],z3.Not(bound)),secs=5)
        if res=="unsat":
            parts.append(bound);new.append({"original_trans_clock_bound":str(bound)})
    if not parts:raise RuntimeError("CO_CLOCK_NO_CANDIDATE")
    return z3.And(*parts),{"generated_source_only":new,
        "rejected_source_only":rejected,"candidate_atom_count":len(parts),
        "source_pre_trans_only_no_Post_until_frozen":True,
        "has_nontrivial_generated_polynomial":any("generated_primitive_polynomial" in q for q in new),
        "generation_wall_ms":ms(start),
        "method":"STRONG_CLASSICAL_EXACT" if exact_classical else "FROZEN_LEARNED_OPERATOR"}

def one(root,path,expected,weights):
    start=time.perf_counter_ns()
    row={"original_source":path,"expected_blob":expected,
      "learned_full_original_dual_3VC":False,"classical_full_original_dual_3VC":False}
    try:
        raw=(root/path).read_bytes()
        if blob(raw)!=expected:raise RuntimeError("FROZEN_SOURCE_BLOB_WRONG")
        row["original_sha256"]=sha(raw)
        forms=sexprs(raw);src=extract_mixed_original(forms)
        native=native_original_relations(forms,src)
        native.update({"now":src["now"],"next":src["next"]})
        parity=check_parity(src,native)
        row["original_pre_trans_post_native_custom_xor"]=parity
        if set(parity)!=EXPECTED or any(v!="unsat" for v in parity.values()):
            raise RuntimeError("ORIGINAL_SEMANTIC_PARITY_FAIL")
        if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
            raise RuntimeError("VACUOUS_SOURCE_ORIGINAL")
        controller=frozen_affine_clock_controller(src,native)
        row["affine_source_controller"]=controller[1]
        learned,learned_meta=generator_from_controller(src,native,weights,False,controller)
        classical,classical_meta=generator_from_controller(src,native,weights,True,controller)
        row["learned_source_generated"]=learned_meta
        row["classical_source_generated"]=classical_meta
        row["learned_invariant_SMT"]=learned.sexpr()
        row["classical_invariant_SMT"]=classical.sexpr()
        row["identical_candidate_invariant_text"]=learned.sexpr()==classical.sexpr()
        # Post first consulted to verify the previously frozen two candidates.
        row["learned_original_3VC"],row["learned_full_original_dual_3VC"]=proof(learned,src,native)
        row["classical_original_3VC"],row["classical_full_original_dual_3VC"]=proof(classical,src,native)
        row["status"]=("POSTHOC_LEARNED_TRANSFER_AND_STRONG_CLASSICAL_BOTH_PASS" if
         row["learned_full_original_dual_3VC"] and row["classical_full_original_dual_3VC"] else
         "PARTIAL_OR_NONINDUCTIVE_PROPOSAL_NO_FULL_PROOF")
    except Exception as exc:
        row["status"]="ABSTAIN_CODE_OR_UNSUPPORTED"
        row["error"]=type(exc).__name__+":"+str(exc)[:280]
    row["whole_case_wall_ms"]=ms(start)
    return row

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    full=time.perf_counter_ns()
    # NO changed model, no target training. Match raw CI weight digest exactly.
    weights,learned_training=train_frozen_operator()
    if learned_training["frozen_trained_weights_sha256"]!=FROZEN_WEIGHTS_SHA:
        raise RuntimeError("UNAUTHORIZED_CHANGE_TO_TRAINED_42_WEIGHT_MODEL")
    assert learned_training["heldout_64_full_integer_coefficient_predictions_exact"]==64
    print("FROZEN_MODEL_WEIGHT_IDENTITY_PASS",FROZEN_WEIGHTS_SHA,flush=True)
    rows=[one(args.root,rel,blob_sha,weights) for rel,blob_sha in COHORT]
    for row in rows:
        print("CO_CLOCK_ORIGINAL_CASE",row["original_source"],row["status"],
         "LEARNED",row["learned_full_original_dual_3VC"],
         "STRONG_CLASSIC",row["classical_full_original_dual_3VC"],
         "ERROR",row.get("error"),flush=True)
    report={
      "schema":"neumann.q3.source_affine_coclock.posthoc_frozen42.first.v1",
      "fixed_original_first_blind_run_id":39424234515,
      "fixed_original_first_blind_learned_pass_count":2,
      "fixed_original_first_blind_classical_pass_count":2,
      "fixed_original_first_blind_raw_JSON_SHA256":FIRST_RAW_JSON_SHA,
      "scientific_scope":"POSTHOC_AFTER_THIRD_SOURCE_OPENED; NOT_NEW_BLIND",
      "neural_model_weights_fixed_before_any_new_source_work":True,
      "frozen_original_weights_and_synthetic_data_unmodified":learned_training,
      "source_affine_controller_original_Pre_Trans_only":True,
      "source_case_count":len(rows),
      "learned_posthoc_dual_original_3VC_count":sum(q["learned_full_original_dual_3VC"] for q in rows),
      "strong_classical_posthoc_dual_original_3VC_count":sum(q["classical_full_original_dual_3VC"] for q in rows),
      "predefined_grammar_no_learned_new_mathematical_primitive":True,
      "same_input_exact_classical_available":True,
      "learned_superiority_over_strong_classical":False,
      "new_author_family_out_of_domain":False,
      "GPU_calls":0,"paid_API_calls":0,
      "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
      "entire_wall_including_repeated_training_ms":ms(full),
      "cases":rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("POSTHOC_FROZEN_MODEL_PLUS_COCLOCK_SOURCE_PASS",
      report["learned_posthoc_dual_original_3VC_count"],"/3",flush=True)
    print("MATCHED_STRONG_CLASSICAL_SOURCE_PASS",
      report["strong_classical_posthoc_dual_original_3VC_count"],"/3",flush=True)
    print("Q3_GLOBAL",report["global_Q3"],flush=True)

if __name__=="__main__":main()
