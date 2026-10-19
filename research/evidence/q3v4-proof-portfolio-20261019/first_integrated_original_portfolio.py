"""Q3V4: ONE coherent source-correct classical proof portfolio, opened DEV only.
Preregistration: Q3V3 PR #239 issue comment #6257230593, before implementation.
No learned structure, no unseen Q6, no frontier-parity or 10x cost claims.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3v3-octagon-houdini-20261019"))
sys.path.insert(0,str(HERE.parent/"q3v-branch-common-nullspace-20261019"))
from first_octagon_original import houdini,synthetic,Abstain
from first_original_branch_nullspace import (
 all_exact_branch_updates,common_kernels,actual_relation,prove_candidate_relation,
 check_parity,check_cover,check_formula,independent_native_bad_query,
 extract_mixed_original,native_original_relations,sexprs,sample,blobhash,
 LICENSE_GIT_BLOB,REV,PROVEN
)
EXPECTED={"initial":"unsat","consecution":"unsat","post":"unsat"}

def source_proof(theorem,original):
    result=check_cover(theorem,original)
    checks={k:result.get(k) for k in EXPECTED}
    accepted=result["status"]==PROVEN and checks==EXPECTED
    return {"status":result["status"],"vcs":checks,"accepted":accepted}

def prove_one(path,root,index):
    raw=path.read_bytes()
    receipt={"source_path":path.relative_to(root).as_posix(),
             "original_source_git_blob":blobhash(raw),
             "status":"UNDETERMINED",
             "proofs_attempted":[]}
    t0=time.perf_counter_ns()
    try:
        forms=sexprs(raw)
        src=extract_mixed_original(forms)
        native=native_original_relations(forms,src)
        native.update({"now":src["now"],"next":src["next"]})
        parity=check_parity(src,native)
        receipt["source_semantics_native_xor_parity"]=parity
        if len(parity)!=3 or any(x!="unsat" for x in parity.values()):
            raise Abstain("SOURCE_NATIVE_XOR_PARITY_FAILED")
        if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
            raise Abstain("ORIGINAL_GOAL_VACUOUS_OR_UNKNOWN")
        receipt["status"]="PRECHECK_PASS"
        def baseline():
            try:
                b=independent_native_bad_query(native,src["now"],src["next"])
                receipt["strong_SPACER_raw_original_bad_exit"]=b["status"]
                receipt["strong_SPACER_solver_wall_ms"]=b["native_solver_wall_ms"]
            except Exception as e:
                receipt["strong_SPACER_raw_original_bad_exit"]="ERROR"
                receipt["strong_SPACER_error"]=type(e).__name__+":"+str(e)[:90]
        if index % 2==0:baseline()
        tproof=time.perf_counter_ns()
        post=source_proof(native["post"],native)
        receipt["proofs_attempted"].append({"arm":"POST_ONLY",**post})
        winner=None
        if post["accepted"]:
            winner="POST_ONLY"
        if winner is None:
            t=time.perf_counter_ns()
            try:
                if src["num_bool"]!=0:raise Abstain("BOOL_STATE_UNSUPPORTED")
                I,pool,n0,q=houdini(native["pre"],native["trans"],src["now"],src["next"])
                rec=source_proof(I,native)
                receipt["proofs_attempted"].append({
                    "arm":"OCTAGON_HOUDINI",**rec,"grammar_size":n0,
                    "surviving_atoms":len(pool),"queries":q,
                    "elapsed_ms":round((time.perf_counter_ns()-t)/1e6,3)})
                if rec["accepted"]:winner="OCTAGON_HOUDINI"
            except Exception as e:
                receipt["proofs_attempted"].append({
                    "arm":"OCTAGON_HOUDINI","status":"ABSTAIN",
                    "reason":type(e).__name__+":"+str(e)[:110]})
        if winner is None:
            t=time.perf_counter_ns()
            try:
                branches=all_exact_branch_updates(src)
                candidates=common_kernels(branches,src)
                certified=[]
                for candidate in candidates:
                    pred=actual_relation(candidate,src["now"])
                    proof=prove_candidate_relation(src,native,pred)
                    if proof["source_certified"]:certified.append(pred)
                rec=source_proof(z3.And(native["post"],*certified),native)
                receipt["proofs_attempted"].append({
                    "arm":"BRANCH_AFFINE_NULLSPACE",**rec,
                    "branches":len(branches),"candidates":len(candidates),
                    "certified_relations":len(certified),
                    "elapsed_ms":round((time.perf_counter_ns()-t)/1e6,3)})
                if rec["accepted"]:winner="BRANCH_AFFINE_NULLSPACE"
            except Exception as e:
                receipt["proofs_attempted"].append({
                    "arm":"BRANCH_AFFINE_NULLSPACE","status":"ABSTAIN",
                    "reason":type(e).__name__+":"+str(e)[:110]})
        receipt["proof_wall_ms"]=round((time.perf_counter_ns()-tproof)/1e6,3)
        receipt["selected_arm"]=winner if winner else "NO_PROOF"
        receipt["status"]="ORIGINAL_THREE_VC_CERTIFIED" if winner else "NO_ORIGINAL_THREE_VC_CERTIFICATE"
        if index%2:baseline()
    except Exception as e:
        receipt["status"]="SOURCE_OR_VALIDATOR_ABSTAIN"
        receipt["error"]=type(e).__name__+":"+str(e)[:200]
    receipt["case_end_to_end_wall_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
    return receipt

def run(root):
    assert blobhash((root/"LICENSE.md").read_bytes())==LICENSE_GIT_BLOB
    controls=synthetic()
    cases=[prove_one(p,root,i) for i,p in enumerate(sample(root))]
    assert len(cases)==10 and len({r["original_source_git_blob"] for r in cases})==10
    counts={arm:sum(r.get("selected_arm")==arm for r in cases)
        for arm in ["POST_ONLY","OCTAGON_HOUDINI","BRANCH_AFFINE_NULLSPACE","NO_PROOF"]}
    cert=sum(r["status"]=="ORIGINAL_THREE_VC_CERTIFIED" for r in cases)
    stats={"source_originals":10,
           "all_original_three_vc_certified":cert,
           "selected_arms":counts,
           "source_only_spacer_unsat_reports":sum(
               r.get("strong_SPACER_raw_original_bad_exit")=="unsat" for r in cases),
           "source_only_spacer_unanswered":sum(
               r.get("strong_SPACER_raw_original_bad_exit")!="unsat" for r in cases),
           "sum_proof_wall_ms":round(sum(r.get("proof_wall_ms",0) for r in cases),3),
           "sum_case_end_to_end_wall_ms":round(sum(r.get("case_end_to_end_wall_ms",0) for r in cases),3)}
    allvcs=all(r["status"]=="ORIGINAL_THREE_VC_CERTIFIED" and any(
            p.get("arm")==r.get("selected_arm") and p.get("vcs")==EXPECTED
            for p in r["proofs_attempted"]) for r in cases)
    return {"name":"Q3V4_OPENED_ORIGINALS_REVERIFIED_CLASSICAL_PORTFOLIO",
            "source_revision":REV,
            "controls":controls,
            "summary":stats,
            "cases":cases,
            "first_science_gate_pass":bool(allvcs and cert==10 and
                controls["synthetic_unsafe_mutants"]=="REJECTED_2_OF_2"),
            "source_family_blind":False,
            "new_learned_mathematical_operator":False,
            "training_calls":0,
            "frontier_comparison_run":False,
            "tenfold_cost_advantage_claimed":False,
            "global_Q1_Q7":"OPEN"}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=run(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("Q3V4_FROZEN_FIRST_SUMMARY",json.dumps(r["summary"],sort_keys=True))
    print("Q3V4_FIRST_CASES",[(x["source_path"],x["status"],x.get("selected_arm"),
        x.get("strong_SPACER_raw_original_bad_exit"),x.get("case_end_to_end_wall_ms"),
        x.get("error")) for x in r["cases"]])
    print("Q3V4_FIRST_GLOBAL_Q1_Q7",r["global_Q1_Q7"])
    print("Q3V4_FIRST_GATE",r["first_science_gate_pass"])
