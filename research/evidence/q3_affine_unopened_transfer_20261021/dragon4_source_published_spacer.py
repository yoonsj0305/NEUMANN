"""One bounded Z3 SPACER reachability proof of authentic original DRAGON_4 Post.
No k-induction assumptions; universal CHC over full native original state.
SPACER UNSAT counts only as source-scoped Z3 reachability proof unless
a separately verified inductive certificate is produced. Does not claim
Z3+cvc5 dual 3VC, learned-new-math, or global Q3.
"""
import argparse, hashlib, json, time
from pathlib import Path
import z3
from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    blob, sha, sexprs, compile_typed_original, compile_independent_native, dual, elapsed
)

SOURCE="lib/Inv_Track/andrew_lustre/DRAGON_4.lus.sl"
GIT_BLOB="455422332af42a42d5f9c61562e1912f13bc2946"
MAX_MS=60000

def check(root):
    st=time.perf_counter_ns()
    row={"source":SOURCE,"frozen_original_git_blob":GIT_BLOB,
         "status":"ABSTAIN_UNTESTED","dual_certificate_original_3VC":False,
         "global_Q3":"OPEN"}
    try:
        raw=(root/SOURCE).read_bytes()
        if blob(raw)!=GIT_BLOB:
            raise RuntimeError("FROZEN_ORIGINAL_GIT_BLOB_CHANGED")
        row["real_original_sha256"]=sha(raw)
        parsed=compile_typed_original(sexprs(raw))
        native=compile_independent_native(sexprs(raw),parsed)
        row["source_semantic_original_dual_parity"]={
            name:dual(z3.Xor(parsed[name],native[name]),"unsat",10)
            for name in ("pre","trans","post")
        }
        if not all(x["dual_pass"] for x in row["source_semantic_original_dual_parity"].values()):
            raise RuntimeError("ORIGINAL_PRE_TRANS_POST_PARITY_FAILED")
        orig={**parsed,**native}
        n=len(orig["now"])
        reach=z3.Function("source_reach",*[x.sort() for x in orig["now"]],z3.BoolSort())
        bad=z3.Function("source_bad",z3.BoolSort())
        vars_=z3.z3util.get_vars(z3.And(orig["pre"],orig["trans"],orig["post"]))
        fp=z3.Fixedpoint()
        fp.set(engine="spacer",timeout=MAX_MS)
        fp.register_relation(reach,bad)
        fp.declare_var(*vars_)
        fp.rule(reach(*orig["now"]),orig["pre"])
        fp.rule(reach(*orig["next"]),z3.And(reach(*orig["now"]),orig["trans"]))
        fp.rule(bad(),z3.And(reach(*orig["now"]),z3.Not(orig["post"])))
        row["full_original_state_count"]=n
        row["auxiliary_declared_free_variables"]=len(vars_)-2*n
        result=fp.query(bad())
        row["fixedpoint_query_result"]=str(result)
        if result==z3.unsat:
            row["status"]="ORIGINAL_SOURCE_FULL_PUBLISHED_SAFETY_SPACER_UNSAT"
            row["one_engine_safety_proved"]=True
            row["independent_dual_original_3VC_proved"]=False
            answer=str(fp.get_answer())
            row["SPACER_certificate_sexpr_sha256"]=sha(answer.encode())
            row["SPACER_certificate_size_chars"]=len(answer)
            row["SPACER_certificate_excerpt"]=answer[:1200]
        elif result==z3.sat:
            row["status"]="SPACER_REPORTED_BAD_REACHABLE_UNVALIDATED_TRACE"
            row["one_engine_safety_proved"]=False
        else:
            row["status"]="ABSTAIN_SPACER_UNKNOWN"
            row["one_engine_safety_proved"]=False
            row["reason"]=fp.get_reason_unknown()
    except Exception as e:
        row["status"]="ABSTAIN_SOURCE_OR_SPACER_EXCEPTION"
        row["error"]=type(e).__name__+":"+str(e)[:320]
    row["wall_ms"]=elapsed(st)
    print("DRAGON4_REAL_SOURCE_SPACER",row["status"],
          "PDR_RESULT",row.get("fixedpoint_query_result"),
          "ERROR",row.get("error"))
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    rec=check(a.root)
    out={
        "schema":"neumann.q3.dragon4_original_spacer_posthoc.v1",
        "after_k8_abstain":True,
        "no_paid_GPU_or_neural":True,
        "first_frozen_pre_body_git_identity":"8e6efc5b5a6f637ac6b92fbb459616e30ce97072",
        "global_Q3":"OPEN",
        "original":rec,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("DRAGON4_SOURCE_PUBLISHED_ONE_SOLVER_SAFETY_PROVED",
          rec.get("one_engine_safety_proved",False))
    print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":
    main()
