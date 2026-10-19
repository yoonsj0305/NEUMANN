"""Q3V6 first bounded original-source lazy specialist gate.
DEV-only original evidence. Classical only. Preregistered before implementation:
PR #241 comment #6257659293. No new G1 or Q7 claim.
"""
from __future__ import annotations
import argparse, collections, json, sys, time
from pathlib import Path
import z3
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3v4-proof-portfolio-20261019"))
from first_integrated_original_portfolio import (
 source_proof,check_parity,check_cover,check_formula,
 independent_native_bad_query,extract_mixed_original,native_original_relations,
 sexprs,blobhash,LICENSE_GIT_BLOB,REV,
 houdini,all_exact_branch_updates,common_kernels,actual_relation,
 prove_candidate_relation,synthetic,EXPECTED,PROVEN
)

FIXED_EIGHT=(
 "benchmarks/LIA/2013.OOPSLA_Hola/add.sl",
 "benchmarks/LIA/2013.OOPSLA_Hola/countud.sl",
 "benchmarks/LIA/2013.OOPSLA_Hola/hola.05.sl",
 "benchmarks/LIA/2013.OOPSLA_Hola/hola.07.sl",
 "benchmarks/LIA/2015.FMCAD_Acceleration/bk-nat.sl",
 "benchmarks/LIA/2015.FMCAD_Acceleration/bkley.sl",
 "benchmarks/LIA/2015.FMCAD_Acceleration/cars.sl",
 "benchmarks/LIA/2015.FMCAD_Acceleration/ex1.sl"
)

def measured_solve(src,native):
    start=time.perf_counter_ns()
    status={"selected":"NONE","attempts":[],"certificate_kind":"NONE",
            "original_three_vc":None,"fallback_spacer_status":"NOT_CALLED",
            "fallback_spacer_wall_ms":0.0}
    def elapsed(t):
        return round((time.perf_counter_ns()-t)/1e6,3)
    def check(arm,I,extra=None):
        t=time.perf_counter_ns()
        vc=source_proof(I,native)
        row={"arm":arm,"status":vc["status"],"vcs":vc["vcs"],
             "accepted":vc["accepted"],"wall_ms":elapsed(t)}
        if extra:row.update(extra)
        status["attempts"].append(row)
        if vc["accepted"]:
            status["selected"]=arm
            status["certificate_kind"]="NATIVE_SOURCE_EXACT_ORIGINAL_3VC"
            status["original_three_vc"]=vc["vcs"]
            return True
        return False
    if check("POST_ONLY",native["post"]):
        status["pre_fallback_structural_wall_ms"]=elapsed(start)
        status["full_hybrid_wall_ms"]=elapsed(start)
        return status
    t=time.perf_counter_ns()
    try:
        if src["num_bool"]:raise ValueError("OCTAGON_BOOL_UNSUPPORTED")
        inv,atoms,count,queries=houdini(
            native["pre"],native["trans"],src["now"],src["next"])
        ok=check("OCTAGON_HOUDINI",inv,
            {"candidate_count":count,"remaining_atoms":len(atoms),"cegis_queries":queries})
        if ok:
            status["pre_fallback_structural_wall_ms"]=elapsed(start)
            status["full_hybrid_wall_ms"]=elapsed(start)
            return status
    except Exception as e:
        status["attempts"].append({"arm":"OCTAGON_HOUDINI","status":"ABSTAIN",
            "reason":type(e).__name__+":"+str(e)[:120],"wall_ms":elapsed(t)})
    t=time.perf_counter_ns()
    try:
        branch=all_exact_branch_updates(src)
        certified=[]
        for c in common_kernels(branch,src):
            term=actual_relation(c,src["now"])
            if prove_candidate_relation(src,native,term)["source_certified"]:
                certified.append(term)
        ok=check("BRANCH_AFFINE_NULLSPACE",
            z3.And(native["post"],*certified),
            {"branch_count":len(branch),"certified_relation_count":len(certified)})
        if ok:
            status["pre_fallback_structural_wall_ms"]=elapsed(start)
            status["full_hybrid_wall_ms"]=elapsed(start)
            return status
    except Exception as e:
        status["attempts"].append({"arm":"BRANCH_AFFINE_NULLSPACE","status":"ABSTAIN",
            "reason":type(e).__name__+":"+str(e)[:120],"wall_ms":elapsed(t)})
    status["pre_fallback_structural_wall_ms"]=elapsed(start)
    t=time.perf_counter_ns()
    try:
        v=independent_native_bad_query(native,src["now"],src["next"])
        status["fallback_spacer_status"]=v["status"]
        status["fallback_spacer_wall_ms"]=v["native_solver_wall_ms"]
        status["attempts"].append({"arm":"FALLBACK_SOURCE_ONLY_SPACER",
            "solver_raw_status":v["status"],"wall_ms":elapsed(t)})
        if v["status"]=="unsat":
            status["selected"]="FALLBACK_SOURCE_ONLY_SPACER"
            status["certificate_kind"]="SOURCE_ONLY_Z3_SPACER_UNSAT"
    except Exception as e:
        status["fallback_spacer_status"]="EXCEPTION"
        status["attempts"].append({"arm":"FALLBACK_SOURCE_ONLY_SPACER",
            "status":"ABSTAIN","reason":type(e).__name__+":"+str(e)[:120],
            "wall_ms":elapsed(t)})
    status["full_hybrid_wall_ms"]=elapsed(start)
    return status

def run_one(path,root):
    t0=time.perf_counter_ns()
    rec={"source":path.relative_to(root).as_posix(),
         "source_git_blob":blobhash(path.read_bytes()),
         "status":"UNDETERMINED"}
    try:
        form=sexprs(path.read_bytes())
        src=extract_mixed_original(form)
        native=native_original_relations(form,src)
        native.update({"now":src["now"],"next":src["next"]})
        parity=check_parity(src,native)
        rec["native_source_xor_3vc"]=parity
        if len(parity)!=3 or any(s!="unsat" for s in parity.values()):
            raise ValueError("ORIGINAL_PARSER_SEMANTIC_XOR_NOT_UNSAT")
        if check_formula(native["pre"])!="sat" or \
             check_formula(z3.Not(native["post"]))!="sat":
            raise ValueError("VACUOUS_ORIGINAL_SOURCE")
        parse_ms=round((time.perf_counter_ns()-t0)/1e6,3)
        rec["shared_source_parse_validation_wall_ms"]=parse_ms
        # Independent direct strong classical baseline is ALWAYS measured.
        t=time.perf_counter_ns()
        b=independent_native_bad_query(native,src["now"],src["next"])
        direct_ms=round((time.perf_counter_ns()-t)/1e6,3)
        rec["direct_spacer"]={"raw_status":b["status"],
            "solver_wall_ms":b["native_solver_wall_ms"],
            "wrapper_wall_ms":direct_ms,"usable_original_safe":b["status"]=="unsat"}
        # Exact classical structural proof first, independent of case basename.
        rec["lazy"]=measured_solve(src,native)
        rec["status"]="ACCEPTED_ORIGINAL_SAFE" if (
            rec["lazy"]["certificate_kind"]!="NONE") else "NO_CERTIFIED_SAFE_RESULT"
        rec["direct_parse_plus_solver_ms"]=round(parse_ms+direct_ms,3)
        rec["lazy_parse_plus_solver_ms"]=round(
            parse_ms+rec["lazy"]["full_hybrid_wall_ms"],3)
    except Exception as e:
        rec.update({"status":"ABSTAIN","error":
          type(e).__name__+":"+str(e)[:160]})
    rec["total_both_arms_sequential_wall_ms"]=round(
       (time.perf_counter_ns()-t0)/1e6,3)
    return rec

def run(root):
    if blobhash((root/"LICENSE.md").read_bytes())!=LICENSE_GIT_BLOB:
        raise ValueError("SOURCE_LICENSE_MISMATCH")
    controls=synthetic()
    cases=[run_one(root/path,root) for path in FIXED_EIGHT]
    assert len(cases)==8 and len({c["source_git_blob"] for c in cases})==8
    counts=collections.Counter(c.get("lazy",{}).get("selected","NONE") for c in cases)
    accepted=sum(c["status"]=="ACCEPTED_ORIGINAL_SAFE" for c in cases)
    direct=sum(c.get("direct_spacer",{}).get("usable_original_safe",False) for c in cases)
    structural_ok=sum(c.get("lazy",{}).get("certificate_kind")=="NATIVE_SOURCE_EXACT_ORIGINAL_3VC" for c in cases)
    fallback=sum(c.get("lazy",{}).get("selected")=="FALLBACK_SOURCE_ONLY_SPACER" for c in cases)
    parse_accurate=all(len(c.get("native_source_xor_3vc",{}))==3 and
       all(v=="unsat" for v in c["native_source_xor_3vc"].values()) for c in cases)
    lazy_wall=sum(c.get("lazy_parse_plus_solver_ms",0) for c in cases)
    direct_wall=sum(c.get("direct_parse_plus_solver_ms",0) for c in cases)
    # Explicitly counterfactual: ALWAYS execute both approaches. Uses
    # actually measured direct-baseline wrapper wall on structural wins.
    avoided=sum(c["direct_spacer"]["wrapper_wall_ms"] for c in cases
             if c.get("lazy",{}).get("certificate_kind")=="NATIVE_SOURCE_EXACT_ORIGINAL_3VC")
    naive_estimated_lazy_plus_all_spacer=lazy_wall+avoided
    first_gate=(accepted==8 and direct<=7 and structural_ok>=6 and
        fallback>=1 and parse_accurate and
        controls["synthetic_unsafe_mutants"]=="REJECTED_2_OF_2" and
        avoided>0 and all(c["status"]=="ACCEPTED_ORIGINAL_SAFE" for c in cases))
    return {"study":"Q3V6_FIRST_CLASSICAL_PROOF_GATED_LAZY_FALLBACK_DEV",
       "source_git_revision":REV,"originals":8,
       "first_cases":cases,"synthetic_controls":controls,
       "first_summary":{"lazy_accepted_originals":accepted,
         "native_3vc_certified_originals":structural_ok,
         "source_only_spacer_fallback_originals":fallback,
         "direct_source_only_SPACER_accepted_originals":direct,
         "lazy_route_counts":dict(counts),
         "sum_lazy_parse_plus_full_execution_ms":round(lazy_wall,3),
         "sum_direct_spacer_parse_plus_execution_ms":round(direct_wall,3),
         "specialist_calls_eliminated":structural_ok,
         "separately_measured_baseline_solver_wall_eliminated_ms":round(avoided,3),
         "hypothetical_always_execute_specialist_all_in_ms":round(
            naive_estimated_lazy_plus_all_spacer,3),
         "counterfactual_avoided_wall_fraction":round(
           avoided/naive_estimated_lazy_plus_all_spacer,5)
             if naive_estimated_lazy_plus_all_spacer>0 else None,
         "first_gate_pass":first_gate},
       "source_family_blind":False,"neural_learning_or_inference_calls":0,
       "iso_capability_tenfold_claim":False,
       "global_Q1_Q7":"OPEN"}
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=run(args.root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Q3V6_FIRST_COUNTS",json.dumps(result["first_summary"],sort_keys=True))
    print("Q3V6_FIRST_CASES",[(c["source"],c["status"],c.get("lazy",{}).get("selected"),
           c.get("direct_spacer",{}).get("raw_status"),
           c.get("lazy_parse_plus_solver_ms")) for c in result["first_cases"]])
    print("Q3V6_FIRST_FROZEN_GATE",result["first_summary"]["first_gate_pass"])
