"""One source-bound proof replay RED-TEAM for old Q3 historical receipt.

Preregistered under Issue #245 BEFORE code/CI.
This is Q2 verifier integrity, not a new Q3 learning or benchmark experiment.
Only two ALREADY OPENED pinned real LoopInvGen source files are used.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from experiments.q3_source_prove import (
    prove_source,replay_exported_queries,replay_original_source_bound,
)

ALREADY_OPENED = (
    "benchmarks/LIA/2013.OOPSLA_Hola/hola.05.sl",
    "benchmarks/LIA/2015.FMCAD_Acceleration/bk-nat.sl",
)
CHECKS = ("initial","consecution","post")


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def run(root):
    if len(ALREADY_OPENED)!=2:
        raise AssertionError("NOT_EXACT_TWO_PRE_REGISTERED_REAL_SOURCES")
    paths=[root/name for name in ALREADY_OPENED]
    r=[prove_source(p) for p in paths]
    if any(x["status"]!="ORIGINAL_SOURCE_THREE_VC_CERTIFIED" for x in r):
        raise AssertionError("REAL_SOURCE_PROOF_NOT_CERTIFIED")
    if r[0]["selected_route"] not in ("OCTAGON_HOUDINI","BRANCH_AFFINE_NULLSPACE"):
        raise AssertionError("FIRST_HOLA_MUST_BE_STRUCTURAL_NON_POST")
    if r[1]["selected_route"]!="POST_ONLY":
        raise AssertionError("SECOND_ACCELERATION_MUST_BE_POST_ONLY")
    good=[replay_original_source_bound(p,x) for p,x in zip(paths,r)]
    if good!=[True,True]:
        raise AssertionError("GENUINE_SOURCE_BOUND_REPLAY_FAILED")

    poisoned=copy.deepcopy(r[0])
    # Both content and SHA can be changed by an adversarial receipt writer.
    # All three queries are trivially UNSAT, irrespective of the actual source.
    trivial="(set-logic QF_LIA)\n(assert false)\n(check-sat)\n"
    for key in CHECKS:
        poisoned["original_bad_condition_smt2"][key]={
            "query":trivial,"sha256":_sha(trivial),"expected":"unsat"}
    legacy_forgery_accepted=replay_exported_queries(poisoned)
    fixed_forgery_rejected=not replay_original_source_bound(paths[0],poisoned)

    modified_inv=copy.deepcopy(r[0])
    modified_inv["invariant_sexpr"]="false"
    modified_inv["invariant_sha256"]=_sha("false")
    wrong_invariant_rejected=not replay_original_source_bound(paths[0],modified_inv)

    missing_vc=copy.deepcopy(r[0])
    del missing_vc["original_bad_condition_smt2"]["post"]
    missing_vc_rejected=not replay_original_source_bound(paths[0],missing_vc)

    changed_status=copy.deepcopy(r[0])
    changed_status["status"]="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT"
    spacer_promotion_rejected=not replay_original_source_bound(paths[0],changed_status)

    # A completely true certificate for a different real source is NOT portable.
    cross_source_rejected=not replay_original_source_bound(paths[1],r[0])

    with TemporaryDirectory() as d:
        changed=Path(d)/"tampered.sl"
        changed.write_bytes(paths[0].read_bytes()+b"\n; deliberate changed original bytes\n")
        changed_original_rejected=not replay_original_source_bound(changed,r[0])

    checks={
        "legacy_unbound_replay_accepts_three_trivial_unsat_queries":
            legacy_forgery_accepted,
        "new_bound_replay_rejects_three_trivial_unsat_queries":
            fixed_forgery_rejected,
        "new_bound_replay_rejects_changed_invariant_even_rehashed":
            wrong_invariant_rejected,
        "new_bound_replay_rejects_missing_original_vc":
            missing_vc_rejected,
        "new_bound_replay_rejects_spacer_as_inductive_certificate":
            spacer_promotion_rejected,
        "new_bound_replay_rejects_different_real_original_source":
            cross_source_rejected,
        "new_bound_replay_rejects_changed_original_source_bytes":
            changed_original_rejected,
    }
    passed=good==[True,True] and all(checks.values())
    return {
       "schema":"neumann.q2.original-source-bound-proof-redteam.v1",
       "scope":"OFFLINE_Q2_PROOF_INTEGRITY_NOT_MODEL_CAPABILITY",
       "preregistration_issue":245,"preregistered_real_originals":list(ALREADY_OPENED),
       "pinned_input_revision":"6ac90265b11431c9477dfbd33e3e3380234c0499",
       "sources":[{"path":name,"source_sha256":row["source_sha256"],
            "selected_route":row["selected_route"],"status":row["status"],
            "original_three_vc":row["original_three_vc"],
            "strict_original_bound_replay":is_good}
            for name,row,is_good in zip(ALREADY_OPENED,r,good)],
       "legacy_unbound_vulnerability_reproduced":legacy_forgery_accepted,
       "hardened_boundary_negative_controls":checks,
       "strict_replay_good_sources_passed":sum(good),
       "first_gate_pass":passed,
       "new_sealed_sources_opened":0,"new_model_inferences":0,
       "learned_new_semantic_operator":False,
       "historical_prove_source_success_preserved":True,
       "original_am1_decision2":"FAIL_UNCHANGED",
       "Q3_scoped_classical":"PRESERVED",
       "global_Q1_Q7":"OPEN",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=run(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Q2_LEGACY_UNBOUND_FORGED_UNSAT_ACCEPTED",result["legacy_unbound_vulnerability_reproduced"])
    print("Q2_STRICT_ORIGINAL_SOURCE_REPLAY",result["strict_replay_good_sources_passed"])
    print("Q2_MUTATION_CONTROLS",result["hardened_boundary_negative_controls"])
    print("Q2_FIRST_REDTEAM_GATE",result["first_gate_pass"])
if __name__=="__main__":
    main()
