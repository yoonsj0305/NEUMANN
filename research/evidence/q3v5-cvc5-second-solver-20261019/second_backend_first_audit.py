"""Independent CVC5 replay of 6 previously Z3-proven actual Q3V5 originals.
A second solver checks unchanged original proof VCs, not learned Q3 or fresh transfer.
Frozen science prereg: PR #241 comment #6257415686.
"""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
import z3
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3v4-proof-portfolio-20261019"))
sys.path.insert(0,str(HERE.parent/"q3v3-octagon-houdini-20261019"))
sys.path.insert(0,str(HERE.parent/"q3v-branch-common-nullspace-20261019"))
from first_integrated_original_portfolio import prove_one,source_proof,EXPECTED,PROVEN
from first_octagon_original import houdini
from first_original_branch_nullspace import (
    sexprs,extract_mixed_original,native_original_relations,check_parity,
    all_exact_branch_updates,common_kernels,actual_relation,prove_candidate_relation,
    blobhash,LICENSE_GIT_BLOB
)

# THESE SIX are post-FIRST Q3V5 SUCCESS cases, verified only. No new selection.
SOURCES={
 "benchmarks/LIA/2013.OOPSLA_Hola/hola.05.sl":("5afb6ea131e2c3bfcd8a8600fbad9f8c7e52fa6a","OCTAGON_HOUDINI"),
 "benchmarks/LIA/2013.OOPSLA_Hola/hola.07.sl":("8fbb75d1ea026429603679cd873fd4ab611c3949","BRANCH_AFFINE_NULLSPACE"),
 "benchmarks/LIA/2015.FMCAD_Acceleration/bk-nat.sl":("bef2c3c75be2d13117092fed4ee58104666d2ea3","POST_ONLY"),
 "benchmarks/LIA/2015.FMCAD_Acceleration/bkley.sl":("9b51471e8c5f403dcb796103c57af83eb6366e52","POST_ONLY"),
 "benchmarks/LIA/2015.FMCAD_Acceleration/cars.sl":("9ef1462529d504940de4856f7d27fcfdb3e20af8","POST_ONLY"),
 "benchmarks/LIA/2015.FMCAD_Acceleration/ex1.sl":("54c71ba46caf7a7e09d51c3c459d975102f058e9","POST_ONLY"),
}

def pick_invariant(src,native,winner):
    if winner=="POST_ONLY":
        return native["post"]
    if winner=="OCTAGON_HOUDINI":
        I,_,_,_=houdini(native["pre"],native["trans"],src["now"],src["next"])
        return I
    if winner=="BRANCH_AFFINE_NULLSPACE":
        branches=all_exact_branch_updates(src)
        preds=[]
        for cand in common_kernels(branches,src):
            R=actual_relation(cand,src["now"])
            if prove_candidate_relation(src,native,R)["source_certified"]:
                preds.append(R)
        return z3.And(native["post"],*preds)
    raise ValueError("FROZEN_WINNER_NOT_RECOGNIZED")

def run_cvc5(expr,expect):
    s=z3.Solver()
    s.add(expr)
    smt2=s.to_smt2()
    start=time.perf_counter_ns()
    try:
        r=subprocess.run(["cvc5","--lang","smt2"],input=smt2,text=True,
           capture_output=True,timeout=15)
        tokens=[x.strip() for x in r.stdout.strip().splitlines() if x.strip()]
        result=tokens[-1] if tokens else "NO_OUTPUT"
        success=r.returncode==0 and tokens==[expect] and not r.stderr.strip()
        return {"expected":expect,"observed":result,"exit_code":r.returncode,
            "stdout_excerpt":r.stdout.strip()[:250],
            "stderr_excerpt":r.stderr.strip()[:250],
            "smt2_sha256":hashlib.sha256(smt2.encode()).hexdigest(),
            "smt2_length":len(smt2),
            "solver_wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
            "pass":success}
    except Exception as e:
        return {"expected":expect,"pass":False,
            "error":type(e).__name__+":"+str(e)[:140]}

def process(root):
    if blobhash((root/"LICENSE.md").read_bytes())!=LICENSE_GIT_BLOB:
        raise RuntimeError("SOURCE_LICENSE_MISMATCH")
    try:version=subprocess.check_output(["cvc5","--version"],text=True,timeout=5).strip()
    except Exception as e:
        return {"status":"INFRASTRUCTURE_BLOCKED_CVC5_BINARY",
          "reason":str(e)[:200],"cases":[],"global_Q1_Q7":"OPEN"}
    cases=[]
    for idx,(path,(expected_blob,expected_arm)) in enumerate(SOURCES.items()):
        file=root/path
        raw=file.read_bytes()
        result={"source":path,"source_git_blob":blobhash(raw),"checks":[],
                "status":"PRECHECK_PENDING"}
        try:
            if result["source_git_blob"]!=expected_blob:raise RuntimeError("IMMUTABLE_SOURCE_MISMATCH")
            replay=prove_one(file,root,idx)
            if replay["status"]!="ORIGINAL_THREE_VC_CERTIFIED":
                raise RuntimeError("FROZEN_ORIGINAL_3VC_NOT_REPRODUCED")
            if replay["selected_arm"]!=expected_arm:raise RuntimeError("FROZEN_SELECTED_ROUTE_CHANGED")
            forms=sexprs(raw)
            src=extract_mixed_original(forms)
            native=native_original_relations(forms,src)
            native.update({"now":src["now"],"next":src["next"]})
            native_parity=check_parity(src,native)
            if len(native_parity)!=3 or any(s!="unsat" for s in native_parity.values()):
                raise RuntimeError("ORIGINAL_NATIVE_SEMANTIC_PARITY_FAIL")
            I=pick_invariant(src,native,expected_arm)
            z3original=source_proof(I,native)
            if z3original["vcs"]!=EXPECTED or not z3original["accepted"]:
                raise RuntimeError("FIRST_Z3_ORIGINAL_VC_CANNOT_REPRODUCE")
            Ip=z3.substitute(I,*[(v,vp) for v,vp in zip(src["now"],src["next"])])
            bads={
               "initial":z3.And(native["pre"],z3.Not(I)),
               "consecution":z3.And(I,native["trans"],z3.Not(Ip)),
               "post":z3.And(I,z3.Not(native["post"]))
            }
            result["selected_arm"]=replay["selected_arm"]
            result["replayed_native_z3_three_vcs"]=z3original["vcs"]
            for step in ["initial","consecution","post"]:
                r=run_cvc5(bads[step],"unsat")
                result["checks"].append({"vc":step,**r})
            if idx<2:
                result["checks"].append({"vc":"negative_overstrengthened_false",
                    **run_cvc5(z3.And(native["pre"],z3.Not(z3.And(I,z3.BoolVal(False)))),"sat")})
            result["status"]="CVC5_ORIGINAL_VCS_CONFIRMED" if all(
                  c["pass"] for c in result["checks"]) else "CVC5_FAILED_OR_UNKNOWN"
        except Exception as exc:
            result["status"]="ABSTAIN_ORIGINAL_REPLAY"
            result["reason"]=type(exc).__name__+":"+str(exc)[:180]
        cases.append(result)
    all_18=sum(c["pass"] and c["expected"]=="unsat"
        for r in cases for c in r["checks"])
    negative=sum(c["pass"] and c["expected"]=="sat"
        for r in cases for c in r["checks"])
    full=all_18==18 and negative==2 and all(
         c["status"]=="CVC5_ORIGINAL_VCS_CONFIRMED" for c in cases)
    return {"study":"Q3V5_EXTERNAL_CVC5_NATIVE_ORIGINAL_CERTIFICATE_SECOND_SOLVER",
       "status":"CVC5_SECOND_SOLVER_SCOPED_PASS" if full else "CVC5_SECOND_SOLVER_FAIL",
       "cvc5_version":version,"original_safety_vcs_independently_unsat":all_18,
       "negative_controls_sat":negative,"cases":cases,"gate_pass":full,
       "prior_two_origin_prospective_gate":"FIRST_FROZEN_TRANSFER_FAIL_UNCHANGED",
       "learning_calls":0,"source_family_blind":False,
       "neumann_frontier_parity":False,"global_Q1_Q7":"OPEN"}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    r=process(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("Q3V5_CVC5_SECOND_SOLVER_STATUS",r["status"])
    print("Q3V5_CVC5_VCS",r.get("original_safety_vcs_independently_unsat"))
    print("Q3V5_CVC5_NEGATIVES",r.get("negative_controls_sat"))
    print("Q3V5_CVC5_CASES",[(c["source"],c["status"],[(q["vc"],q.get("observed"),q.get("pass")) for q in c["checks"]]) for c in r.get("cases",[])])
if __name__=="__main__":main()
