"""Source-native published Post proof on FIREFLY_1 and DRAGON_2 via SPACER
candidate extraction and original Z3+cvc5 independent 3VC. Posthoc classical.
Both original source Git blobs immutable from pre-source PR321; preserve first
learned XOR4 0/2, do not claim new source blind or neural contribution.
"""
import argparse,json,time
from pathlib import Path
import z3

from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    ORIGINS,UPSTREAM,blob,sha,sexprs,compile_typed_original,compile_independent_native,dual,elapsed
)
from research.evidence.q3_affine_unopened_transfer_20261021.dragon4_spacer_extracted_dual_3vc import from_spacer_answer

def case(root,path,source_sha):
    start=time.perf_counter_ns()
    out={"source":path,"git_blob":source_sha,"status":"ABSTAIN",
         "actual_source_original_dual_3VC":False}
    try:
        raw=(root/path).read_bytes()
        if blob(raw)!=source_sha:raise RuntimeError("PRESOURCE_PINNED_ORIGINAL_CHANGED")
        out["original_source_sha256"]=sha(raw)
        parsed=compile_typed_original(sexprs(raw))
        native=compile_independent_native(sexprs(raw),parsed)
        out["native_custom_source_semantic_dual"]={
            k:dual(z3.Xor(parsed[k],native[k]),"unsat",10)
            for k in ("pre","trans","post")
        }
        if not all(p["dual_pass"] for p in out["native_custom_source_semantic_dual"].values()):
            raise RuntimeError("ORIGINAL_SOURCE_SEMANTICS_NOT_DUAL")
        o={**parsed,**native}
        name=path.split("/")[-1].split(".")[0]
        Reach=z3.Function("q3_two_source_reach_"+name,
            *[v.sort() for v in o["now"]],z3.BoolSort())
        Bad=z3.Function("q3_two_source_bad_"+name,z3.BoolSort())
        free=z3.z3util.get_vars(z3.And(o["pre"],o["trans"],o["post"]))
        fp=z3.Fixedpoint()
        fp.set(engine="spacer",timeout=60000)
        fp.register_relation(Reach,Bad)
        fp.declare_var(*free)
        fp.rule(Reach(*o["now"]),o["pre"])
        fp.rule(Reach(*o["next"]),z3.And(Reach(*o["now"]),o["trans"]))
        fp.rule(Bad(),z3.And(Reach(*o["now"]),z3.Not(o["post"])))
        checked=fp.query(Bad())
        out["native_full_source_published_post_SPACER"]=str(checked)
        if checked!=z3.unsat:
            out["status"]="ABSTAIN_SPACER_NOT_PROVEN"
            if checked==z3.unknown:out["reason"]=fp.get_reason_unknown()
            return out
        answer=fp.get_answer()
        out["SPACER_answer_sha256"]=sha(str(answer).encode())
        candidates=from_spacer_answer(answer,Reach,o["now"])
        out["candidate_count"]=len(candidates)
        checked_candidates=[]
        for cand in candidates:
            nxt=z3.substitute(cand,*list(zip(o["now"],o["next"])))
            proof={
                "initial":dual(z3.And(o["pre"],z3.Not(cand)),"unsat",12),
                "consecution":dual(z3.And(cand,o["trans"],z3.Not(nxt)),"unsat",12),
                "published_post":dual(z3.And(cand,z3.Not(o["post"])),"unsat",12),
            }
            verified=all(v["dual_pass"] for v in proof.values())
            checked_candidates.append({
                "verified_source_original_full_3VC":verified,
                "source_candidate_SMT":cand.sexpr(),
                "native_independent_3VC":proof,
            })
            if verified:break
        out["checked_candidates"]=checked_candidates
        out["actual_source_original_dual_3VC"]=any(
            q["verified_source_original_full_3VC"] for q in checked_candidates)
        out["status"]="PASS_ORIGINAL_FULL_SOURCE_DUAL_3VC" if out["actual_source_original_dual_3VC"] else "ABSTAIN_CANNOT_CERTIFY_SPACER_CANDIDATE"
    except Exception as ex:
        out["status"]="ABSTAIN_EXCEPTION"
        out["error"]=type(ex).__name__+":"+str(ex)[:400]
    finally:
        out["wall_ms"]=elapsed(start)
        print("POSTHOC_TWO_OLDER_PUBLISHED_SOURCE_3VC",path,out["status"],
              "ERROR",out.get("error"),flush=True)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    results=[case(a.root,path,digest) for path,digest in ORIGINS]
    assert len(results)==2
    res={"schema":"neumann.q3.two_original_source_published_post_pdr_to_dual_3VC.v1",
      "previous_first_unopened_learned_XOR4_zero_of_two_immutable":True,
      "upstream_source_revision":UPSTREAM,
      "posthoc_source_read":"YES",
      "original_full_safety_dual_3VC":sum(r["actual_source_original_dual_3VC"] for r in results),
      "rows":results,
      "model_train_updates":0,"neural_forwards":0,"GPU":0,"paid_API":0,
      "global_Q3":"OPEN","global_Q4":"OPEN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(res,sort_keys=True,indent=2)+"\n")
    print("OLD_TWO_ORIGINAL_FULL_PUBLISHED_3VC_PASS",res["original_full_safety_dual_3VC"],"/2")
    print("GLOBAL_Q3",res["global_Q3"])
if __name__=="__main__":
    main()
