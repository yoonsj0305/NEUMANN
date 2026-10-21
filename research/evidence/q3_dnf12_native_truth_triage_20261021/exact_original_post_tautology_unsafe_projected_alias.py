"""Posthoc cause audit of first-blind Boolean learner on 12 unchanged originals.

Directly parse each REAL original Pre/Trans/Post independently, even when
Post is a tautology and standard prepare() intentionally rejects nontriviality.
Only dual Z3+cvc5 source-universal results count:
 (1) NotPost UNSAT -> entire Post tautological, no learning needed;
 (2) Pre&NotPost SAT or Pre&Trans&NotPost(next) SAT -> genuine UNSAFE;
 (3) distinct original good one-step state and bad state with identical
     first-two-variable observation -> projected binary classification cannot
     separate them (a representational information barrier, NOT source UNSAFE).
All source identities exactly matched to preregistered original Git blob.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sexprs,compile_typed_original,compile_independent_native
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    dual,DUAL_S,verified_3vc
)
def evaluate(root,item):
    t=time.perf_counter_ns()
    row={"original_source":item["path"],"original_git_blob":item["git_blob"],
         "status":"ABSTAIN","genuine_original_full_safe_certificate":False}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or blob(raw)!=item["git_blob"]:
            raise RuntimeError("PREOPEN_ORIGINAL_GIT_BLOB_OR_BYTE_LENGTH_CHANGED")
        expr=sexprs(raw)
        src=compile_typed_original(expr)
        native=compile_independent_native(expr,src)
        parity={kind:dual(z3.Xor(src[kind],native[kind]),"unsat",DUAL_S)
                for kind in ("pre","trans","post")}
        if not all(v["dual_pass"] for v in parity.values()):
            raise RuntimeError("ORIGINAL_NATIVE_PRE_TRANS_POST_PARITY_FAILED")
        row["authentic_source_native_parity"]=parity
        now=list(src["now"]);nxt=list(src["next"])
        npost=z3.Not(native["post"])
        notpost=dual(npost,"unsat",DUAL_S)
        row["unconditional_Post_tautology_independent_provers"]=notpost
        if notpost["dual_pass"]:
            # I=True gives UNSAT for original initiation and consecution,
            # and goal is exactly globally tautological Post.
            proved,obligations=verified_3vc(src,native,z3.BoolVal(True))
            row["True_invariant_full_original_3VC"]=obligations
            row["genuine_original_full_safe_certificate"]=bool(proved)
            row["status"]=("SOURCE_POST_TAUTOLOGY_NO_MACHINE_LEARNING_NEEDED"
                           if proved else "ABSTAIN_TAUTOLOGY_CERT_MISMATCH")
            return row
        pre=dual(native["pre"],"sat",DUAL_S)
        row["original_Pre_nonempty_dual"]=pre
        if not pre["dual_pass"]:
            row["status"]="ABSTAIN_VACUOUS_OR_UNSUPPORTED_PRE"
            return row
        init=dual(z3.And(native["pre"],npost),"sat",DUAL_S)
        row["genuine_initial_UNSAFE_dual_witness"]=init
        if init["dual_pass"]:
            row["status"]="GENUINE_SOURCE_INIT_UNSAFE"
            return row
        postnext=z3.substitute(native["post"],*list(zip(now,nxt)))
        step=dual(z3.And(native["pre"],native["trans"],z3.Not(postnext)),"sat",DUAL_S)
        row["genuine_first_transition_UNSAFE_dual_witness"]=step
        if step["dual_pass"]:
            row["status"]="GENUINE_SOURCE_ONE_STEP_UNSAFE"
            return row
        if len(now)<2:
            row["status"]="NO_TWO_FEATURE_PROJECTION"
            return row
        # Distinct BAD witness variables; genuine full original NotPost
        # and projection-identical to a genuine GOOD one-step successor.
        bad=[z3.Const("original_bad_projection_"+str(i),q.sort()) for i,q in enumerate(now)]
        postbad=z3.substitute(native["post"],*list(zip(now,bad)))
        same=z3.And(nxt[0]==bad[0],nxt[1]==bad[1])
        aliasquery=z3.And(native["pre"],native["trans"],postnext,z3.Not(postbad),same)
        aliased=dual(aliasquery,"sat",DUAL_S)
        row["full_original_safe_one_step_vs_bad_projection_alias_dual"]=aliased
        row["projected_two_slot_learning_cannot_separate_full_source_example"]=bool(aliased["dual_pass"])
        row["status"]=("CERTIFIED_TWO_SLOT_PROJECTED_LABEL_ALIAS"
                        if aliased["dual_pass"] else "NO_SHORT_UNSAFE_OR_ALIAS_WITNESS_NOT_PROVEN_GLOBALLY_SAFE")
    except Exception as e:
        row["status"]="ABSTAIN_SOURCE_OR_NATIVE_DUAL_SOLVER"
        row["error"]=type(e).__name__+":"+str(e)[:460]
    finally:
        row["native_parse_and_dual_proof_wall_ms"]=(time.perf_counter_ns()-t)/1e6
        print("REAL_ORIGINAL_BOOLEAN_LEARNER_TRIAGE",
              row["original_source"].split("/")[-1],row["status"],
              "POST_TAUTOLOGY",row.get("unconditional_Post_tautology_independent_provers",{}).get("dual_pass"),
              "INIT_UNSAFE",row.get("genuine_initial_UNSAFE_dual_witness",{}).get("dual_pass"),
              "STEP_UNSAFE",row.get("genuine_first_transition_UNSAFE_dual_witness",{}).get("dual_pass"),
              "PROJECTION_ALIAS",row.get("projected_two_slot_learning_cannot_separate_full_source_example"),
              "ERROR",row.get("error"),flush=True)
    return row
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    manifest=json.loads(Path(a.freeze).read_text())
    assert manifest["schema"]=="neumann.q3.train_BOOLEAN_DNF_first12_unopened_xujie_SHA.v1"
    cohort=manifest["cases"]
    assert len(cohort)==12 and len({x["git_blob"] for x in cohort})==12
    rows=[evaluate(Path(a.root),r) for r in cohort]
    status=lambda s:sum(r["status"]==s for r in rows)
    out={"schema":"neumann.q3.12_true_originals_posthoc_exact_native_learning_necessity_and_projection.v1",
         "original_pre_source_Git_SHA_commit":"ba08ffcf1760ef556d6f4fd058f81ef656263642",
         "previous_first_blind_model_run":39595138809,
         "all_source_bodies_were_opened_before_this_posthoc_diagnostic":True,
         "original_sha_locked_count":len(rows),
         "unconditionally_true_original_Post_source_count":
            status("SOURCE_POST_TAUTOLOGY_NO_MACHINE_LEARNING_NEEDED"),
         "genuine_original_initial_UNSAFE":status("GENUINE_SOURCE_INIT_UNSAFE"),
         "genuine_original_one_transition_UNSAFE":status("GENUINE_SOURCE_ONE_STEP_UNSAFE"),
         "proved_two_feature_safe_vs_bad_projection_collisions":status("CERTIFIED_TWO_SLOT_PROJECTED_LABEL_ALIAS"),
         "not_proven_safe_or_bad_or_alias":status("NO_SHORT_UNSAFE_OR_ALIAS_WITNESS_NOT_PROVEN_GLOBALLY_SAFE"),
         "abstentions_and_other":sum(r["status"] not in (
            "SOURCE_POST_TAUTOLOGY_NO_MACHINE_LEARNING_NEEDED",
            "GENUINE_SOURCE_INIT_UNSAFE","GENUINE_SOURCE_ONE_STEP_UNSAFE",
            "CERTIFIED_TWO_SLOT_PROJECTED_LABEL_ALIAS",
            "NO_SHORT_UNSAFE_OR_ALIAS_WITNESS_NOT_PROVEN_GLOBALLY_SAFE") for r in rows),
         "not_original_Blind_learned_model_pass":True,
         "tautology_is_exact_deletion_of_unnecessary_learning":True,
         "no_bounded_UNSAT_claimed_complete_safe":True,
         "not_close_global_Q3_Q4_Q6":True,
         "all_authentic_original_cases":rows}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    for k in ("unconditionally_true_original_Post_source_count","genuine_original_initial_UNSAFE",
              "genuine_original_one_transition_UNSAFE",
              "proved_two_feature_safe_vs_bad_projection_collisions",
              "not_proven_safe_or_bad_or_alias","abstentions_and_other"):
        print("NEW_ORIGINAL_DNF_LEARNER_EXACT_NATIVE_TRIAGE",k,out[k],flush=True)
if __name__=="__main__":main()
