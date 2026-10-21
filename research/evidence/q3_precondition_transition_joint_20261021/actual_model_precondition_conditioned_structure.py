"""PRE-BODY frozen eight genuine external SyGuS source originals in 2 corpora.

Actual gradient-fitted degree-1..3 candidate source inductive equations, same
numeric and polynomial construction as prior synthetic PR430, but source
states/transitions are sampled from original native SMT (no known solution).
Equal source sample/grammar EXACT rational linear classical, native cvc5 SyGuS
and native Z3 Spacer are stronger controls. Every unsupported, unsafe, timeout,
no-conjecture stays in original 8 denominator. No new primitive created.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math,time
from pathlib import Path
import numpy as np
import sympy as sp
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sexprs,compile_typed_original,compile_independent_native,dual
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    original_syguS,native_pdr,verified_3vc,DUAL_S
)
from research.evidence.q3_raw_transition_nonlinear_20261021.learned_original_source_nonlinear_AST import fit
LOCK="e00e96733735e9d2ff5198359e3d76801b1eed1b"
REV="13c8deb68a873635879c9a69bc78caebd340f646"
def ms(t):return (time.perf_counter_ns()-t)/1e6
def quick(formula):
    s=z3.Solver();s.set(timeout=1800);s.add(formula)
    r=s.check()
    return str(r)
def three_z3(src,native,candidate):
    nxt=z3.substitute(candidate,*zip(src["now"],src["next"]))
    parts=(z3.And(native["pre"],z3.Not(candidate)),
           z3.And(candidate,native["trans"],z3.Not(nxt)),
           z3.And(candidate,z3.Not(native["post"])))
    return tuple(quick(p) for p in parts)
def original_samples(src,native,limit=72):
    z=src["now"]+src["next"]
    s=z3.Solver();s.set(timeout=2200);s.add(native["trans"])
    records=[];seen=set()
    # Fixed source-independent probes, without inspecting target program content
    for i in range(0,limit*4):
        if len(records)>=limit:break
        r=s.check()
        if r!=z3.sat:break
        model=s.model()
        try:sample=tuple(model.eval(v,model_completion=True).as_long() for v in z)
        except Exception:raise RuntimeError("NON_INT_TRANSITION_STATE")
        if sample not in seen:
            seen.add(sample);records.append(sample)
        s.add(z3.Or(*[v!=int(x) for v,x in zip(z,sample)]))
        if i%7==0 and len(records)>10:
            # Incremental exact solver may keep choosing irrelevant large cases.
            # No source-specific behavior or label is allowed.
            pass
    ps=z3.Solver();ps.set(timeout=2200);ps.add(native["pre"])
    if ps.check()!=z3.sat:raise RuntimeError("ORIGINAL_PRE_NOT_SAT_OR_SOLVER_UNKNOWN")
    m=ps.model()
    initial=tuple(m.eval(v,model_completion=True).as_long() for v in src["now"])
    # Positive original Pre samples are constraint-derived; no invariant
    # answers or source-variable-specific formulae are provided.
    pres={initial}
    for i in range(min(len(src["now"]),5)):
        for target in (-4,-2,-1,0,1,2,4):
            ps2=z3.Solver();ps2.set(timeout=1000)
            ps2.add(native["pre"],src["now"][i]==target)
            if ps2.check()!=z3.sat:continue
            m2=ps2.model()
            try:
                pres.add(tuple(m2.eval(v,model_completion=True).as_long()
                              for v in src["now"]))
            except Exception:continue
    return records,initial,sorted(pres)
def operator_basis(n,anchor,degree):
    others=[i for i in range(min(n,5)) if i!=anchor]
    out=[]
    for total in range(1,degree+1):
        for powers in itertools.product(range(total+1),repeat=len(others)):
            if sum(powers)!=total:continue
            if total>2 and sum(bool(v) for v in powers)>1:continue
            out.append(tuple((others[j],a) for j,a in enumerate(powers) if a>0))
    return out
def numeric_poly(row,monomial):
    p=1
    for i,power in monomial:p*=int(row[i])**power
    return p
def term_z3(vars,mono):
    t=z3.IntVal(1)
    for i,power in mono:
        for _ in range(power):t=t*vars[i]
    return t
def candidate_ast(vars,anchor,basis,coeffs,constant):
    return z3.Sum(*[int(c)*term_z3(vars,b) for c,b in zip(coeffs,basis)]
                  +[vars[anchor],z3.IntVal(-int(constant))])
def same_math_classical(A,b):
    start=time.perf_counter_ns()
    mat=sp.Matrix(np.rint(A).astype(int).tolist());vec=sp.Matrix(np.rint(b).astype(int).tolist())
    sol=sp.linsolve(list(mat*sp.Matrix(sp.symbols("w:"+str(A.shape[1])))-vec),
                    sp.symbols("w:"+str(A.shape[1])))
    if not sol:return None,ms(start)
    vv=list(next(iter(sol)))
    free=set().union(*(x.free_symbols for x in vv))
    vv=[t.subs({x:0 for x in free}) for t in vv]
    if any(x.q!=1 for x in vv):return None,ms(start)
    return [int(x) for x in vv],ms(start)
def evaluate_candidate(src,native,anchor,basis,coeff,initial):
    start=time.perf_counter_ns()
    h=candidate_ast(src["now"],anchor,basis,coeff,0)
    # Complete original Pre must agree with this initial value; only one
    # sampled initial anchor constant is proposed, never assumed proven.
    const=z3.simplify(z3.substitute(h,*[(s,z3.IntVal(v)) for s,v in zip(src["now"],initial)]))
    if not z3.is_int_value(const):raise RuntimeError("NONCONSTANT_COMPILER")
    inv=z3.simplify(h==const)
    cheap=three_z3(src,native,inv)
    out={"original_typed_compiled_AST":inv.sexpr(),
         "initial_sample_constant":const.as_long(),
         "original_all_3_VCs_Z3_probe":list(cheap),
         "exactly_full_source_3VC_proved":False,
         "exact_source_inductive_lemma_only":False,
         "full_source_verification_ms":ms(start)}
    if cheap==("unsat","unsat","unsat"):
        ok,cert=verified_3vc(src,native,inv)
        out["full_original_independent_Z3_cvc5_3VC"]=cert
        out["exactly_full_source_3VC_proved"]=bool(ok)
    elif cheap[0]=="unsat" and cheap[1]=="unsat":
        # Need not call independent verifier of original goal; certify
        # initiation/consecution only to measure genuine latent structure.
        initials=z3.And(native["pre"],z3.Not(inv))
        next=z3.substitute(inv,*zip(src["now"],src["next"]))
        consec=z3.And(inv,native["trans"],z3.Not(next))
        cert={"init":dual(initials,"unsat",DUAL_S),
              "consecution":dual(consec,"unsat",DUAL_S)}
        out["inductive_source_lemma_independent_dual"]=cert
        out["exact_source_inductive_lemma_only"]=all(q["dual_pass"] for q in cert.values())
    out["full_source_verification_ms"]=ms(start)
    return out
def one(root,item,seed):
    start=time.perf_counter_ns()
    record={"source":item["path"],"original_git_blob":item["git_blob"],
            "status":"ABSTAIN","learned_whole_program_safe":False,
            "classical_same_grammar_whole_program_safe":False}
    try:
        raw=(root/item["path"]).read_bytes()
        if blob(raw)!=item["git_blob"] or len(raw)!=item["bytes"]:
            raise RuntimeError("ORIGINAL_PREBODY_GIT_SHA_MISMATCH")
        forms=sexprs(raw)
        # Declare-primed-var is a SyGuS declaration, not a constraint;
        # exact names/types audited, independent SMT parser sees the
        # authentic original define-fun bodies unchanged.
        primed=[a for a in forms if isinstance(a,list) and a and a[0]=="declare-primed-var"]
        filtered=[a for a in forms if not (isinstance(a,list) and a and a[0]=="declare-primed-var")]
        src=compile_typed_original(filtered)
        if any(len(q)!=3 or q[2] not in ("Int","Bool") for q in primed):
            raise RuntimeError("MALFORMED_ORIGINAL_PRIMED_VAR")
        native=compile_independent_native(filtered,src)
        parity={k:dual(z3.Xor(src[k],native[k]),"unsat",DUAL_S) for k in ("pre","trans","post")}
        if not all(a["dual_pass"] for a in parity.values()):
            raise RuntimeError("NATIVE_SOURCE_PARITY_NOT_CERTIFIED")
        record["original_source_native_parity"]=parity
        unsafe=dual(z3.And(native["pre"],z3.Not(native["post"])),"sat",DUAL_S)
        if unsafe["dual_pass"]:
            record["status"]="UNSAFE_ORIGINAL_ZERO_STEP_PROVED";record["original_unsafe"]=unsafe
            return record
        if any(v.sort().kind()!=z3.Z3_INT_SORT for v in src["now"]) or len(src["now"])>8:
            raise RuntimeError("UNSUPPORTED_ORIGINAL_SOURCE_STATE_INTERFACE")
        vals,init,pres=original_samples(src,native)
        if len(vals)<16:raise RuntimeError("INSUFFICIENT_ORIGINAL_TRANSITION_SAMPLES")
        record["real_original_transition_sample_count"]=len(vals)
        record["original_initial_model_values"]=init
        record["native_original_pre_model_count"]=len(pres)
        n=len(src["now"]);X=np.array([v[:n] for v in vals],dtype=object)
        Y=np.array([v[n:] for v in vals],dtype=object)
        source_models=[]
        # Deterministic frozen anchor/degree budget per source.
        for anchor in range(min(n,3)):
            for deg in (1,2,3):
                B=operator_basis(n,anchor,deg)
                if not B or len(B)>20:continue
                D=np.asarray([[numeric_poly(ys,b)-numeric_poly(xs,b) for b in B]
                              for xs,ys in zip(X,Y)],dtype=np.float64)
                dy=np.asarray([int(ys[anchor])-int(xs[anchor])
                               for xs,ys in zip(X,Y)],dtype=np.float64)
                D_pre=np.asarray([[numeric_poly(state,mono)-numeric_poly(init,mono)
                                     for mono in B] for state in pres],dtype=np.float64)
                dy_pre=np.asarray([int(state[anchor])-int(init[anchor])
                                    for state in pres],dtype=np.float64)
                A=np.vstack([D,D_pre])
                b=np.concatenate([dy,dy_pre])
                if max(np.max(np.abs(A)),np.max(np.abs(b)))>1e9:continue
                st=time.perf_counter_ns()
                pars,fittime,error=fit(np.column_stack([A,b]),seed+anchor*17+deg)
                integer=np.rint(pars[:-1]).astype(int)
                convert=(np.max(np.abs(pars[:-1]-integer))<0.075
                         and np.max(np.abs(integer))<=20)
                learned=None
                if convert:
                    learned=evaluate_candidate(src,native,anchor,B,integer,init)
                exact,exacttime=same_math_classical(A,-b)
                classical=None
                if exact is not None:
                    classical=evaluate_candidate(src,native,anchor,B,exact,init)
                # Real intervention: remove ORIGINAL Pre equations and
                # rerun the *same* model fit to test identifiability.
                ablation_params,ablation_ms,ablation_residual=fit(
                    np.column_stack([D,dy]),seed+anchor*17+deg)
                ablation_integer=np.rint(ablation_params[:-1]).astype(int)
                ablation_ready=(np.max(np.abs(ablation_params[:-1]-ablation_integer))<0.075
                                and np.max(np.abs(ablation_integer))<=20)
                ablation=None
                if ablation_ready:
                    ablation=evaluate_candidate(src,native,anchor,B,ablation_integer,init)
                row={"anchor_index":anchor,"max_basis_degree":deg,
                     "real_source_transition_matrix_rank":int(np.linalg.matrix_rank(D)),
                     "real_source_Pre_plus_Trans_matrix_rank":int(np.linalg.matrix_rank(A)),
                     "transition_only_model_ablation":ablation,
                     "transition_only_model_ablation_fit_ms":ablation_ms,
                     "transition_only_numeric_residual":ablation_residual,
                     "basis_monomials":[list(map(list,m)) for m in B],
                     "fitted_gradient_wall_ms":fittime,
                     "fitted_numeric_residual":error,
                     "rounded_learned_coefficient_ready":convert,
                     "learned_candidate_original_proof":learned,
                     "classical_exact_original_proof":classical,
                     "classical_exact_synthesis_wall_ms":exacttime}
                source_models.append(row)
                if learned and learned["exactly_full_source_3VC_proved"]:
                    record["learned_whole_program_safe"]=True
                if classical and classical["exactly_full_source_3VC_proved"]:
                    record["classical_same_grammar_whole_program_safe"]=True
        record["source_generic_gradient_and_exact_classical_candidates"]=source_models
        record["transition_only_ablation_original_safe"]=any(
            bool(x["transition_only_model_ablation"] and
                 x["transition_only_model_ablation"]["exactly_full_source_3VC_proved"])
            for x in source_models)
        record["learned_source_inductive_lemma_count"]=sum(bool(x["learned_candidate_original_proof"] and x["learned_candidate_original_proof"]["exact_source_inductive_lemma_only"]) for x in source_models)
        record["exact_classical_source_inductive_lemma_count"]=sum(bool(x["classical_exact_original_proof"] and x["classical_exact_original_proof"]["exact_source_inductive_lemma_only"]) for x in source_models)
        # Strong original solution controls, both with original source and full native proof.
        record["original_cvc5_SyGuS_2s"]=original_syguS(raw,src,native,2.0)
        record["original_Z3_SPACER"]=native_pdr(src,native)
        record["status"]="EXECUTED_REAL_EXTERNAL_ORIGINAL_ALL_METHODS"
    except Exception as e:
        record["status"]="ABSTAIN_UNSUPPORTED_ORIGINAL_OR_PROVER"
        record["error"]=type(e).__name__+":"+str(e)[:390]
    finally:
        record["all_original_source_work_wall_ms"]=ms(start)
        print("Q3_REAL_CROSS_CORPUS_FIRSTBODY",item["path"],record["status"],
              "LEARNED_SAFE",record["learned_whole_program_safe"],
              "EXACT_SAFE",record["classical_same_grammar_whole_program_safe"],
              "SYGUS",record.get("original_cvc5_SyGuS_2s",{}).get("certified"),
              "SPACER",record.get("original_Z3_SPACER",{}).get("certified"),
              "ERROR",record.get("error"),flush=True)
    return record
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    f=json.loads(Path(a.freeze).read_text())
    assert f["schema"]=="neumann.q3.external_real_8_PREBODY_SHA_V1"
    assert f["upstream"].split("@")[-1]==REV
    assert f["original_source_bodies_opened_before_commit"] is False
    q=f["cases"];assert len(q)==8 and len({v["git_blob"] for v in q})==8
    for e in q:
        raw=(Path(a.root)/e["path"]).read_bytes()
        assert len(raw)==e["bytes"] and blob(raw)==e["git_blob"]
    rows=[one(Path(a.root),x,20261021+i) for i,x in enumerate(q)]
    audit={
        "schema":"neumann.q3.posthoc_original8_Pre_plus_Trans_numeric_structure_ablated_v1",
        "prebody_meta_SHA_lock_commit":LOCK,
        "exact_original_sources_sha_verified":8,
        "different_original_subcorpora_but_authors_independence_not_proven":2,
        "posthoc_already_opened_originals_no_first_blind_claim":True,
        "actual_numeric_gradient_model_invoked_sources":sum(x["status"]=="EXECUTED_REAL_EXTERNAL_ORIGINAL_ALL_METHODS" for x in rows),
        "actual_numeric_gradient_full_original_dual_3VC_SAFE":sum(x["learned_whole_program_safe"] for x in rows),
        "transition_only_model_ablation_full_original_SAFE":sum(x.get("transition_only_ablation_original_safe",False) for x in rows),
        "originals_with_Pre_plus_Trans_gradient_success_and_trans_only_failure":
            sum(x["learned_whole_program_safe"] and not x.get("transition_only_ablation_original_safe",False) for x in rows),
        "same_basis_exact_rational_full_original_dual_3VC_SAFE":sum(x["classical_same_grammar_whole_program_safe"] for x in rows),
        "native_full_source_cvc5_SyGuS_SAFE":sum(x.get("original_cvc5_SyGuS_2s",{}).get("certified",False) for x in rows),
        "native_full_source_Z3_SPACER_SAFE":sum(x.get("original_Z3_SPACER",{}).get("certified",False) for x in rows),
        "unsupported_or_abstain":sum(x["status"]!="EXECUTED_REAL_EXTERNAL_ORIGINAL_ALL_METHODS" for x in rows),
        "source_initial_unsafe_verified":sum(x["status"]=="UNSAFE_ORIGINAL_ZERO_STEP_PROVED" for x in rows),
        "new_operator_primitive_not_autonomously_invented":True,
        "same_math_classical_has_equal_grammar_and_source_samples":True,
        "learned_weight_retraining_each_source_not_meta_transfer":True,
        "full_original_inductive_proof_always_requires_Z3_AND_cvc5":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "all_cases":rows}
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(audit,indent=2,sort_keys=True,default=lambda q:bool(q) if isinstance(q,np.bool_) else int(q) if isinstance(q,np.integer) else float(q) if isinstance(q,np.floating) else str(q))+"\n")
    for k in ("actual_numeric_gradient_model_invoked_sources","actual_numeric_gradient_full_original_dual_3VC_SAFE",
              "transition_only_model_ablation_full_original_SAFE",
              "originals_with_Pre_plus_Trans_gradient_success_and_trans_only_failure",
              "same_basis_exact_rational_full_original_dual_3VC_SAFE",
              "native_full_source_cvc5_SyGuS_SAFE","native_full_source_Z3_SPACER_SAFE",
              "unsupported_or_abstain"):
        print("Q3_EXTERNAL_REAL_ORIGINAL_CORPORA_BLIND",k,audit[k],flush=True)
    print("GLOBAL_Q3_Q4_Q6_OPEN",flush=True)
if __name__=="__main__":main()
