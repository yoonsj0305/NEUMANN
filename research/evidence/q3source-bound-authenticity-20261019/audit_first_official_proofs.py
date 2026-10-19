"""Read-only authenticity audit of already-frozen official 2017/18 Q3 first result.

NO new source selection, tuning, experiment promotion, model, GPU or paid API.
Old three-UNSAT replay is forgeable. Audit requires original SyGuS source-bound
reconstruction from PR #246's stricter source verifier. Issue #263 prereg.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

FIRST_RAW_JSON_SHA256="090e63f7839df2cd43e7db4132928dc00c098987b71904f052b3366b84cc3fbd"
FROZEN_EXTERNAL_COMMIT="13c8deb68a873635879c9a69bc78caebd340f646"
FROZEN_FIRST_RUN=39210016907
FROZEN_FIRST_ARTIFACT=12167690489
STAT_3VC="ORIGINAL_SOURCE_THREE_VC_CERTIFIED"
FROZEN_COUNTS={
    "ORIGINAL_SOURCE_THREE_VC_CERTIFIED":8,
    "ORIGINAL_SOURCE_ONLY_SPACER_UNSAT":2,
    "ABSTAIN":2,
}
FORGED_SCRIPT="(set-logic QF_LIA)\n(assert false)\n(check-sat)\n"

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def load_strict(root:Path):
    p=root/"experiments"/"q3_source_prove.py"
    spec=importlib.util.spec_from_file_location("q3_strict_source_bound_immutable",p)
    if spec is None or spec.loader is None:
        raise RuntimeError("STRICT_SOURCE_BINDING_VERIFIER_UNAVAILABLE")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not callable(getattr(mod,"replay_original_source_bound",None)):
        raise RuntimeError("SOURCE_BOUND_API_NOT_PRESENT")
    return mod

def run(first_path:Path,external_root:Path,strict_root:Path):
    raw=first_path.read_bytes()
    if digest(raw)!=FIRST_RAW_JSON_SHA256:
        raise RuntimeError("FIRST_ARCHIVED_JSON_BYTE_SHA_MISMATCH")
    first=json.loads(raw)
    if first["external_git_commit"]!=FROZEN_EXTERNAL_COMMIT:
        raise RuntimeError("WRONG_ORIGINAL_SOURCE_UPSTREAM")
    cases=first["cases"]
    names=first["selected"]
    if len(cases)!=12 or len(names)!=12 or names!=[x["source_path"] for x in cases]:
        raise RuntimeError("FIRST_FROZEN_SOURCE_SELECTION_INVALID")
    if first["counts"]!=FROZEN_COUNTS:
        raise RuntimeError("FIRST_FROZEN_RESULT_COUNTS_UNEXPECTED")
    strict=load_strict(strict_root)
    audit=[]
    for prior in cases:
        source=external_root/prior["source_path"]
        if source.is_symlink() or not source.is_file():
            raise RuntimeError("ARCHIVED_ORIGINAL_FILE_MISSING")
        actual_sha=digest(source.read_bytes())
        if prior["raw_source_sha256"]!=actual_sha:
            raise RuntimeError("FIRST_ORIGINAL_SOURCE_BYTE_IDENTITY_MISMATCH")
        current=strict.prove_source(source)
        same=(current["status"]==prior["status"]
           and current.get("selected_route")==prior["route"]
           and current["source_sha256"]==actual_sha)
        row={
            "path":prior["source_path"],"source_sha256":actual_sha,
            "frozen_first_status":prior["status"],
            "strict_recomputed_status":current["status"],
            "same_first_source_route_and_status":same,
            "first_explicit_original_cvc5_verified":prior["independent_cvc5_valid"],
            "source_bound":None,"forged_false3_legacy_accepts":None,
            "forged_false3_source_bound_rejects":None,
            "mutated_source_sha_rejects":None,
            "mutated_invariant_rejects":None,
            "proof_is_nonpost":prior["route"] in (
                "OCTAGON_HOUDINI","BRANCH_AFFINE_NULLSPACE"),
        }
        if current["status"]==STAT_3VC and same:
            # Original receipt is re-derived EXACTLY from frozen original source.
            row["source_bound"]=strict.replay_original_source_bound(source,current)
            row["original_3vc_replay"]=strict.replay_exported_queries(current)
            if not prior["independent_cvc5_valid"]:
                row["source_bound"]=False
            forged=copy.deepcopy(current)
            for entry in forged["original_bad_condition_smt2"].values():
                entry["query"]=FORGED_SCRIPT
                entry["sha256"]=digest(FORGED_SCRIPT.encode())
                entry["expected"]="unsat"
            # The old "all three UNSAT" method can be fooled with forged
            # true-independent (assert false) scripts + matching SHA.
            row["forged_false3_legacy_accepts"]=strict.replay_exported_queries(forged)
            row["forged_false3_source_bound_rejects"]=(
                not strict.replay_original_source_bound(source,forged))
            corrupt_src=copy.deepcopy(current)
            corrupt_src["source_sha256"]="0"*64
            row["mutated_source_sha_rejects"]=(
                not strict.replay_original_source_bound(source,corrupt_src))
            corrupt_inv=copy.deepcopy(current)
            corrupt_inv["invariant_sexpr"]="(not "+corrupt_inv["invariant_sexpr"]+")"
            row["mutated_invariant_rejects"]=(
                not strict.replay_original_source_bound(source,corrupt_inv))
        audit.append(row)
        print("Q3_REAL_ORIGINAL_SOURCE_BOUND_AUDIT",row["path"],
              row["frozen_first_status"],"first_result_agrees",same,
              "bound",row["source_bound"],
              "forged_query_rejected",row["forged_false3_source_bound_rejects"])
    explicit=[x for x in audit if x["frozen_first_status"]==STAT_3VC]
    conditions={
        "twelve_first_selected_sources_unchanged":len(audit)==12 and all(
            x["same_first_source_route_and_status"] for x in audit),
        "eight_explicit_original_source_proofs_rebound":len(explicit)==8 and
            all(x["source_bound"] is True and x["original_3vc_replay"] is True
                for x in explicit),
        "first_independent_cvc5_3vc_results_still_recorded":all(
            x["first_explicit_original_cvc5_verified"] is True for x in explicit),
        "legacy_three_unsat_queries_spoofable":all(
            x["forged_false3_legacy_accepts"] is True for x in explicit),
        "strict_rejects_forged_three_unsat_queries":all(
            x["forged_false3_source_bound_rejects"] is True for x in explicit),
        "strict_rejects_modified_source_identity":all(
            x["mutated_source_sha_rejects"] is True for x in explicit),
        "strict_rejects_forged_invariant_representation":all(
            x["mutated_invariant_rejects"] is True for x in explicit),
        "nonpost_original_proof_still_one":sum(
            x["proof_is_nonpost"] for x in explicit)==1,
        "spacer_only_not_called_explicit_inductive":sum(
            x["frozen_first_status"]=="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT"
            and x["source_bound"] is None for x in audit)==2,
        "two_actual_abstentions_preserved":sum(
            x["frozen_first_status"]=="ABSTAIN"
            and x["source_bound"] is None for x in audit)==2,
    }
    return {
        "schema":"neumann.q3-official-original-source-bound-read-only-audit.v1",
        "audit_issue":263,"first_github_actions_run":FROZEN_FIRST_RUN,
        "first_artifact":FROZEN_FIRST_ARTIFACT,
        "original_first_receipt_sha256":FIRST_RAW_JSON_SHA256,
        "official_upstream_commit":FROZEN_EXTERNAL_COMMIT,
        "previous_12_scientific_results_unchanged":True,
        "scoped_audit_pass":all(conditions.values()),
        "checks":conditions,"cases":audit,
        "source_proposer_retrained":False,
        "no_new_task_originals":True,"model_calls":0,"gpu_calls":0,
        "independent_neural_structure_novelty":"NOT_PROVEN",
        "cross_origin_generalization":"NOT_PROVEN",
        "complete_economics":"NOT_EVALUATED",
        "global_Q1_Q7":"OPEN",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-first-receipt",type=Path,required=True)
    p.add_argument("--external-official-root",type=Path,required=True)
    p.add_argument("--strict-prover-checkout",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=run(args.original_first_receipt,args.external_official_root,
        args.strict_prover_checkout)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("SOURCE_BOUND_AUDIT_CHECKS",json.dumps(report["checks"],sort_keys=True))
    print("SOURCE_BOUND_AUDIT_VERDICT",report["scoped_audit_pass"])
    print("GLOBAL_Q1_Q7",report["global_Q1_Q7"])
if __name__=="__main__":
    main()
