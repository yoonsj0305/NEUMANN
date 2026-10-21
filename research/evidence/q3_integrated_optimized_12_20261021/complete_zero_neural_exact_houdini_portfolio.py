"""Q3 PROOF-FIRST minimal-computation pipeline on twelve exact original programs.

Actual source-independent native original sources, SHA-frozen before PR412.
Scientific question: can we DELETE unnecessary learning and still produce
independently certified complete source safety while charging all relevant
model-free work? Fail closed for unsupported, unsafe and solver unknown.

Priority: (0) Post tautology -> I=True dual Z3+cvc5 3VC;
(1) exactly certified minimal source-state projection then bounded no-fit OR;
(2) source-generic classical affine Houdini conjunction; (3) native original
cvc5 SyGuS; (4) native Z3 SPACER/PDR.
NO FITTED MODEL CALLS; this is strongest honest classical comparator, not Q3 ML.
The minimum feature calculation establishes 0/1-step information necessity,
not inductive global-safety sufficiency.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sexprs,compile_typed_original,compile_independent_native
)
from research.evidence.q3_original12_state_information_profile_20261021.dual_verified_minimum_feature_distribution import once as min_information
from research.evidence.q3_original12_sourcegeneric_houdini_20261021.auto_affine_houdini_actual_original12 import houdini
from research.evidence.q3_guarded_tree_83_20261021.actual_trained_tree_SMT_disjunction import (
    dataset,find_no_fit
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    dual,verified_3vc,original_syguS,native_pdr,DUAL_S
)
def ms(t):return (time.perf_counter_ns()-t)/1e6
def case(root,item):
    start=time.perf_counter_ns()
    out={"source":item["path"],"original_git_blob":item["git_blob"],
         "status":"ABSTAIN","certified_SAFE":False,
         "neural_forward_count":0,"machine_learning_fit_count":0,"routes":[]}
    try:
        raw=(root/item["path"]).read_bytes()
        if blob(raw)!=item["git_blob"] or len(raw)!=item["bytes"]:
            raise RuntimeError("ORIGINAL_SOURCE_SHA_REGISTRATION_CHANGED")
        src=compile_typed_original(sexprs(raw))
        native=compile_independent_native(sexprs(raw),src)
        parity={name:dual(z3.Xor(src[name],native[name]),"unsat",DUAL_S)
                for name in ("pre","trans","post")}
        out["source_original_PreTransPost_independent_parity"]=parity
        if not all(check.get("dual_pass") for check in parity.values()):
            raise RuntimeError("SOURCE_ORIGINAL_INDEPENDENT_AST_MISMATCH")
        t=time.perf_counter_ns()
        direct=dual(z3.Not(native["post"]),"unsat",DUAL_S)
        out["original_Post_tautology_independent_probe"]=direct
        out["routes"].append({"route":"original_Post_tautology_preflight","wall_ms":ms(t),
                              "dual_certified":bool(direct.get("dual_pass"))})
        if direct.get("dual_pass"):
            pass_true,cert=verified_3vc(src,native,z3.BoolVal(True))
            out["certified_trivial_True_original_3VC"]=cert
            if not pass_true:raise RuntimeError("POST_TAUTOLOGY_BUT_TRUE_3VC_NOT_CERTIFIED")
            out["status"]="PASS_ORIGINAL_FULL_3VC_DELETED_ALL_LEARNING_AND_SEARCH"
            out["winner"]="tautology_delete"
            out["certified_SAFE"]=True
            return out
        t=time.perf_counter_ns()
        information=min_information(root,item)
        out["minimum_source_information_original_dual_evidence"]=information
        out["routes"].append({"route":"exact_minimal_information_check","wall_ms":ms(t),
                              "status":information["status"]})
        if information["status"]=="ORIGINAL_UNSAFE_WITH_ZERO_ONE_STEP_WITNESS":
            out["status"]="ORIGINAL_UNSAFE_DUAL_SAT_NOT_POSSIBLE_SAFE"
            out["original_UNSAFE_witness"]=information["real_native_UNSAFE_Z3_cvc5"]
            return out
        if information["status"]=="MINIMUM_ORIGINAL_SOURCE_INFO_PROVED_BY_BOTH_SOLVERS":
            features=information["one_minimal_original_feature_indices"]
            if 1<=len(features)<=2:
                order=list(features)
                for i in range(len(src["now"])):
                    if len(order)>=2:break
                    if i not in order:order.append(i)
                view=dict(src)
                swap=order+[i for i in range(len(src["now"])) if i not in order]
                view["now"]=[src["now"][i] for i in swap]
                view["next"]=[src["next"][i] for i in swap]
                out["proof_derived_minimum_feature_indices"]=list(features)
                out["proof_derived_no_fit_two_slot_indices"]=list(order)
                t=time.perf_counter_ns()
                try:
                    pos,neg=dataset(view,native)
                    out["original_native_NonML_data_sizes"]={
                        "positive":len(pos),"negative":len(neg)}
                    exact_inv,info=find_no_fit(view,native,pos,neg)
                    out["original_exact_nofit_boolean_OR_search"]=info
                    if exact_inv is not None:
                        result,cert=verified_3vc(src,native,exact_inv)
                        out["original_dual_3VC_nofit_OR"]=cert
                        out["exact_no_fit_typed_invariant_AST"]=exact_inv.sexpr()
                        if result:
                            out["certified_SAFE"]=True
                            out["winner"]="exact_no_fit_OR_with_min_info"
                            out["status"]="PASS_ORIGINAL_FULL_3VC_CLASSICAL_NOFIT_OR"
                except Exception as e:
                    out["exact_no_fit_OR_error"]=type(e).__name__+":"+str(e)[:320]
                finally:
                    out["routes"].append({"route":"certified_min_input_exact_nofit_OR",
                                          "wall_ms":ms(t),
                                          "certified":out["certified_SAFE"]})
                if out["certified_SAFE"]:return out
        # Known source-generic CLASSICAL Houdini affine conjunction route.
        # Authentically inductive original candidate is NOT trusted without
        # a separate full native source Z3+cvc5 Init/Trans/Goal verification.
        t=time.perf_counter_ns()
        try:
            invariant,hinfo=houdini(src,native)
            out["source_generic_affine_Houdini_search"]=hinfo
            if invariant is not None:
                complete,checks=verified_3vc(src,native,invariant)
                out["original_dual_3VC_Houdini_conjunction"]=checks
                out["Houdini_final_typed_original_AST"]=invariant.sexpr()
                if complete:
                    out["status"]="PASS_ORIGINAL_FULL_3VC_GENERIC_HOUDINI"
                    out["certified_SAFE"]=True
                    out["winner"]="generic_affine_Houdini"
        except Exception as e:
            out["source_generic_Houdini_error"]=type(e).__name__+":"+str(e)[:320]
        finally:
            out["routes"].append({"route":"source_generic_affine_Houdini",
                                  "wall_ms":ms(t),"certified":out["certified_SAFE"]})
        if out["certified_SAFE"]:return out
        # Separate independently verified complete unchanged original source route.
        t=time.perf_counter_ns()
        sygus=original_syguS(raw,src,native,2.0)
        out["strong_original_cvc5_SyGuS_native_source"]=sygus
        out["routes"].append({"route":"original_cvc5_SyGuS_2s",
                              "wall_ms":ms(t),"certified":sygus.get("certified",False)})
        if sygus.get("certified"):
            out["status"]="PASS_ORIGINAL_FULL_3VC_CVC5_SYGUS"
            out["certified_SAFE"]=True;out["winner"]="original_cvc5_SyGuS"
            return out
        t=time.perf_counter_ns()
        pdr=native_pdr(src,native)
        out["strong_original_Z3_SPACER_native_source"]=pdr
        out["routes"].append({"route":"original_Z3_SPACER",
                              "wall_ms":ms(t),"certified":pdr.get("certified",False)})
        if pdr.get("certified"):
            out["status"]="PASS_ORIGINAL_FULL_3VC_Z3_SPACER"
            out["certified_SAFE"]=True;out["winner"]="original_Z3_SPACER"
            return out
        out["status"]="UNKNOWN_ABSTAIN_ALL_ORIGINAL_SAFETY_ROUTES"
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_OR_CERTIFICATE"
        out["exception"]=type(e).__name__+":"+str(e)[:340]
    finally:
        out["total_original_source_parse_minimum_search_proof_wall_ms"]=ms(start)
        print("PROOF_FIRST_REAL_ORIGINAL",out["source"].rsplit("/",1)[-1],
              out["status"],"WINNER",out.get("winner"),"WALL_MS",round(out["total_original_source_parse_minimum_search_proof_wall_ms"],3),
              "ERROR",out.get("exception"),flush=True)
    return out
def main():
    ap=argparse.ArgumentParser()
    for k in ("root","freeze","out"):ap.add_argument("--"+k,required=True)
    a=ap.parse_args()
    frozen=json.loads(Path(a.freeze).read_text())
    assert frozen["schema"]=="neumann.q3.train_BOOLEAN_DNF_first12_unopened_xujie_SHA.v1"
    cases=frozen["cases"]
    assert len(cases)==12 and len({r["git_blob"] for r in cases})==12
    rows=[case(Path(a.root),item) for item in cases]
    wins={k:sum(x.get("winner")==k for x in rows) for k in (
        "tautology_delete","exact_no_fit_OR_with_min_info","generic_affine_Houdini","original_cvc5_SyGuS",
        "original_Z3_SPACER")}
    succeeded=sum(x["certified_SAFE"] for x in rows)
    result={
       "schema":"neumann.q3.proof_first_integrated_original12_zero_neural_exact_OR_Houdini_SyGuS_PDR.v2",
       "originals_frozen_by_previous_prebody_SHA":True,
       "study_is_posthoc_originals_already_opened_in_PR412":True,
       "source_original_count":12,
       "fully_certified_original_safe_independent_Z3_cvc5":succeeded,
       "winner_breakdown":wins,
       "original_UNSAFE_witness_count":sum(x["status"]=="ORIGINAL_UNSAFE_DUAL_SAT_NOT_POSSIBLE_SAFE" for x in rows),
       "genuine_unknown_or_abstained_count":12-succeeded-sum(
           x["status"]=="ORIGINAL_UNSAFE_DUAL_SAT_NOT_POSSIBLE_SAFE" for x in rows),
       "neural_forwards":0,"fitted_ML_models":0,
       "mean_total_source_wall_ms":sum(x["total_original_source_parse_minimum_search_proof_wall_ms"] for x in rows)/12,
       "median_total_source_wall_ms":sorted(x["total_original_source_parse_minimum_search_proof_wall_ms"] for x in rows)[5:7],
       "whole_source_total_observed_wall_ms":sum(x["total_original_source_parse_minimum_search_proof_wall_ms"] for x in rows),
       "exact_minimum_input_is_not_proof_of_global_safety":True,
       "only_original_independent_Z3_cvc5_FULL_3VC_counted":True,
       "frontier_and_10x_unproven":True,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
       "per_original":rows}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for k in ("fully_certified_original_safe_independent_Z3_cvc5",
              "winner_breakdown","genuine_unknown_or_abstained_count",
              "whole_source_total_observed_wall_ms"):
        print("Q3_PROOF_FIRST_CLASSICAL_PORTFOLIO",k,result[k])
    print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
