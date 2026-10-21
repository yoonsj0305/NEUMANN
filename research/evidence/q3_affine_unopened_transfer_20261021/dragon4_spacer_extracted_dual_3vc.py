"""Extract Z3 SPACER inferred invariant for authentic DRAGON_4 and
independently verify unmodified original Pre, Trans, Post 3VC by Z3+cvc5.
No trust in the SPACER UNSAT verdict is needed for final dual 3VC admission.
ABSTAIN if candidate extraction incomplete or any original proof UNKNOWN.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import z3
from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    blob,sha,sexprs,compile_typed_original,compile_independent_native,dual,elapsed
)

SOURCE="lib/Inv_Track/andrew_lustre/DRAGON_4.lus.sl"
FROZEN_BLOB="455422332af42a42d5f9c61562e1912f13bc2946"

def from_spacer_answer(answer,reach,now):
    candidates=[]
    for part in answer.children() if z3.is_and(answer) else [answer]:
        if not z3.is_quantifier(part) or not part.is_forall():continue
        body=part.body()
        if not z3.is_eq(body):continue
        lhs,rhs=body.children()
        for appli,pred in ((lhs,rhs),(rhs,lhs)):
            if not z3.is_app(appli) or appli.decl().name()!=reach.name():
                continue
            if appli.num_args()!=len(now) or part.num_vars()!=len(now):
                continue
            inv=z3.substitute_vars(pred,*list(reversed(now)))
            if not z3.is_bool(inv):continue
            allfree=z3.z3util.get_vars(inv)
            if any(str(v) not in {str(x) for x in now} for v in allfree):
                continue
            candidates.append(inv)
    return candidates

def run(root):
    t=time.perf_counter_ns()
    rec={"original":SOURCE,"original_git_blob":FROZEN_BLOB,
         "status":"ABSTAIN", "original_full_native_dual_3VC":False}
    try:
        data=(root/SOURCE).read_bytes()
        if blob(data)!=FROZEN_BLOB:raise RuntimeError("FROZEN_SOURCE_SHA_CHANGED")
        rec["original_sha256"]=sha(data)
        parsed=compile_typed_original(sexprs(data))
        native=compile_independent_native(sexprs(data),parsed)
        rec["original_typed_native_semantic_parity"]={
            a:dual(z3.Xor(parsed[a],native[a]),"unsat",10)
            for a in ("pre","trans","post")
        }
        if not all(v["dual_pass"] for v in rec["original_typed_native_semantic_parity"].values()):
            raise RuntimeError("ORIGINAL_SEMANTIC_PARITY_NOT_PROVED")
        o={**parsed,**native}
        r=z3.Function("source_reach",*[x.sort() for x in o["now"]],z3.BoolSort())
        bad=z3.Function("source_bad",z3.BoolSort())
        vars_=z3.z3util.get_vars(z3.And(o["pre"],o["trans"],o["post"]))
        f=z3.Fixedpoint()
        f.set(engine="spacer",timeout=60000)
        f.register_relation(r,bad)
        f.declare_var(*vars_)
        f.rule(r(*o["now"]),o["pre"])
        f.rule(r(*o["next"]),z3.And(r(*o["now"]),o["trans"]))
        f.rule(bad(),z3.And(r(*o["now"]),z3.Not(o["post"])))
        q=f.query(bad())
        rec["PDR_result"]=str(q)
        if q!=z3.unsat:
            rec["status"]="ABSTAIN_PDR_NOT_UNSAT"
            if q==z3.unknown:rec["PDR_reason"]=f.get_reason_unknown()
            return rec
        answer=f.get_answer()
        rec["PDR_answer_sha256"]=sha(str(answer).encode())
        rec["PDR_answer_chars"]=len(str(answer))
        rec["PDR_answer_full"]=str(answer)
        candidates=from_spacer_answer(answer,r,o["now"])
        rec["extracted_candidate_count"]=len(candidates)
        trials=[]
        for cand in candidates:
            cand_next=z3.substitute(cand,*list(zip(o["now"],o["next"])))
            proof={
                "initial":dual(z3.And(o["pre"],z3.Not(cand)),"unsat",12),
                "consecution":dual(z3.And(cand,o["trans"],z3.Not(cand_next)),"unsat",12),
                "safety":dual(z3.And(cand,z3.Not(o["post"])),"unsat",12),
            }
            row={"candidate_sexpr":cand.sexpr(),"candidate_size":len(cand.sexpr()),
                 "source_full_dual_3VC":all(x["dual_pass"] for x in proof.values()),
                 "original_proof":proof}
            trials.append(row)
            if row["source_full_dual_3VC"]:
                rec["status"]="PASS_SPACER_EXTRACTED_INVARIANT_INDEPENDENT_FULL_ORIGINAL_DUAL_3VC"
                rec["original_full_native_dual_3VC"]=True
                break
        rec["candidate_trials"]=trials
        if not rec["original_full_native_dual_3VC"]:
            rec["status"]="ABSTAIN_SPACER_ONE_ENGINE_ONLY_NO_DUAL_3VC"
    except Exception as e:
        rec["status"]="ABSTAIN_CANDIDATE_EXTRACTION_OR_CHECK_ERROR"
        rec["error"]=type(e).__name__+":"+str(e)[:400]
    finally:
        rec["wall_ms"]=elapsed(t)
        print("DRAGON4_SPACER_TO_DUAL_3VC",rec["status"],
              "CANDIDATES",rec.get("extracted_candidate_count",0),
              "ERROR",rec.get("error"),flush=True)
    return rec

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    r=run(a.root)
    result={"schema":"neumann.q3.dragon4_extracted_real_spacer_independent_dual_3VC.v1",
      "previous_Z3_SPACER_one_engine_safety":True,
      "no_original_relaxation":True,"neural_training_or_forward":0,
      "Q3_global":"OPEN","Q4_full":"OPEN","original":r}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("FOURTH_SOURCE_ORIGINAL_INDEPENDENT_DUAL_3VC",r["original_full_native_dual_3VC"])
    print("GLOBAL_Q3",result["Q3_global"])
if __name__=="__main__":
    main()
