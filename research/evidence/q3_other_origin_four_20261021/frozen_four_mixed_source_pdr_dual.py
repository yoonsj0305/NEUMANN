"""First pre-Git-blob frozen source four programs from two new directory families.
No training or source-tailoring. The exact source Post is checked by full
reachability SPACER and only promote to STRONG_3VC when *both independent*
original Z3+cvc5 prove genuine native initiation, step, safety of extracted AST.

Four first outcomes in fixed order; unsupported => ABSTAIN, source SAT =>
unverified reachability until separately ground replay. Do not fabricate PASS.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3

from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    blob,sha,sexprs,compile_typed_original,compile_independent_native,dual,elapsed
)
from research.evidence.q3_affine_unopened_transfer_20261021.dragon4_spacer_extracted_dual_3vc import from_spacer_answer

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
PDR_TIMEOUT_MS=30000
DUAL_TIMEOUT_S=8

def evaluate_source(root,entry):
    t=time.perf_counter_ns()
    rec={"source":entry["path"],"pre_registered_blob":entry["git_blob"],
         "origin_directory":entry["group"],"status":"ABSTAIN_NOT_TESTED",
         "source_independent_original_3VC":False,
         "learned_contribution":"NONE"}
    try:
        source=(root/entry["path"]).read_bytes()
        if len(source)!=entry["bytes"] or blob(source)!=entry["git_blob"]:
            raise RuntimeError("PRESOURCE_SOURCE_GIT_BLOB_OR_LENGTH_CHANGED")
        rec["real_original_bytes_sha256"]=sha(source)
        sex=sexprs(source)
        parsed=compile_typed_original(sex)
        native=compile_independent_native(sex,parsed)
        rec["source_typed_native_pre_trans_post_semantic_parity"]={
            k:dual(z3.Xor(parsed[k],native[k]),"unsat",DUAL_TIMEOUT_S)
            for k in ("pre","trans","post")}
        if not all(v["dual_pass"] for v in rec["source_typed_native_pre_trans_post_semantic_parity"].values()):
            rec["status"]="ABSTAIN_UNPROVED_ORIGINAL_SEMANTIC_PARITY"
            return rec
        source_orig={**parsed,**native}
        rec["original_pre_nonvacuity_dual"]=dual(source_orig["pre"],"sat",DUAL_TIMEOUT_S)
        if not rec["original_pre_nonvacuity_dual"]["dual_pass"]:
            rec["status"]="ABSTAIN_SOURCE_PRE_NOT_DUAL_SAT"
            return rec
        rec["published_Post_is_not_universal_dual"]=dual(z3.Not(source_orig["post"]),"sat",DUAL_TIMEOUT_S)
        if not rec["published_Post_is_not_universal_dual"]["dual_pass"]:
            rec["status"]="ABSTAIN_ORIGINAL_PUBLISHED_POST_UNINTERESTING_OR_UNKNOWN"
            return rec
        reach=z3.Function("fresh_source_reach",*[v.sort() for v in source_orig["now"]],z3.BoolSort())
        bad=z3.Function("fresh_source_bad",z3.BoolSort())
        all_vars=z3.z3util.get_vars(z3.And(source_orig["pre"],source_orig["trans"],source_orig["post"]))
        fp=z3.Fixedpoint()
        fp.set(engine="spacer",timeout=PDR_TIMEOUT_MS)
        fp.register_relation(reach,bad)
        fp.declare_var(*all_vars)
        fp.rule(reach(*source_orig["now"]),source_orig["pre"])
        fp.rule(reach(*source_orig["next"]),z3.And(reach(*source_orig["now"]),source_orig["trans"]))
        fp.rule(bad(),z3.And(reach(*source_orig["now"]),z3.Not(source_orig["post"])))
        outcome=fp.query(bad())
        rec["original_published_Post_PDR"]=str(outcome)
        if outcome!=z3.unsat:
            rec["status"]="ABSTAIN_SPACER_UNKNOWN_OR_UNVERIFIED_SAT"
            if outcome==z3.unknown:rec["solver_reason"]=fp.get_reason_unknown()
            return rec
        rec["Z3_SPACER_one_engine_published_safety_proved"]=True
        reply=fp.get_answer()
        rec["SPACER_raw_answer_sha256"]=sha(str(reply).encode())
        rec["SPACER_answer_len_chars"]=len(str(reply))
        hypotheses=from_spacer_answer(reply,reach,source_orig["now"])
        rec["real_PDR_invariant_candidate_count"]=len(hypotheses)
        receipts=[]
        for cand in hypotheses:
            candprime=z3.substitute(cand,*list(zip(source_orig["now"],source_orig["next"])))
            checks={
                "source_initial":dual(z3.And(source_orig["pre"],z3.Not(cand)),
                                      "unsat",DUAL_TIMEOUT_S),
                "source_step":dual(z3.And(cand,source_orig["trans"],z3.Not(candprime)),
                                   "unsat",DUAL_TIMEOUT_S),
                "source_published_Post":dual(z3.And(cand,z3.Not(source_orig["post"])),
                                            "unsat",DUAL_TIMEOUT_S),
            }
            good=all(q["dual_pass"] for q in checks.values())
            receipts.append({
                "candidate_original_SMT_AST_sha256":sha(cand.sexpr().encode()),
                "candidate_original_SMT_AST_chars":len(cand.sexpr()),
                "complete_original_3VC_independently_dual_proven":good,
                "original_native_Z3_and_cvc5":checks,
            })
            if good:
                rec["status"]="PASS_ORIGINAL_PUBLISHED_SAFETY_NATIVE_DUAL_3VC"
                rec["source_independent_original_3VC"]=True
                break
        rec["original_PDR_extracted_candidate_dual_receipts"]=receipts
        if not rec["source_independent_original_3VC"]:
            rec["status"]="ABSTAIN_PDR_ONE_ENGINE_ONLY_NOT_DUAL_CERTIFIED"
    except Exception as e:
        rec["status"]="ABSTAIN_SOURCE_PDR_OR_INVARIANT_EXCEPTION"
        rec["error"]=type(e).__name__+":"+str(e)[:310]
    finally:
        rec["wall_ms"]=elapsed(t)
        print("FROZEN_OTHER_ORIGIN_SOURCE",rec["source"],rec["status"],
              "DUAL3VC",rec["source_independent_original_3VC"],
              "ERROR",rec.get("error"),flush=True)
    return rec

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    metadata=json.loads(args.freeze.read_text())
    if metadata["upstream_commit"]!=UPSTREAM or len(metadata["targets"])!=4:
        raise RuntimeError("PREGISTERED_NEW_DIRECTORY_SOURCES_CHANGED")
    rows=[evaluate_source(args.root,t) for t in metadata["targets"]]
    output={
        "schema":"neumann.q3.first_unopened_four_other_directory_native_pdr.v1",
        "immutable_presource_metadata_commit":"c3878668196e92b2c16ed359716d88b3d4e8f7fe",
        "number_of_actual_original_source_authentications":sum(
          "real_original_bytes_sha256" in x for x in rows),
        "number_of_real_source_full_published_safety_dual_3VC":sum(
          x["source_independent_original_3VC"] for x in rows),
        "number_of_original_PDR_one_engine_unsat":sum(
          x.get("Z3_SPACER_one_engine_published_safety_proved",False) for x in rows),
        "four_rows_preserved":len(rows)==4,
        "new_neural_training_updates":0,"new_neural_forwards":0,"paid_API_calls":0,
        "neural_primitive_novelty":"NOT_DEMONSTRATED",
        "global_Q3":"OPEN","global_Q4":"OPEN",
        "results":rows,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
    print("NEW_DIR_TWO_FAMILY_ORIGINAL_DUAL_3VC",output["number_of_real_source_full_published_safety_dual_3VC"],"/4")
    print("NEW_DIR_PDR_UNSAT",output["number_of_original_PDR_one_engine_unsat"],"/4")
    print("GLOBAL_Q3",output["global_Q3"])
if __name__=="__main__":
    main()
