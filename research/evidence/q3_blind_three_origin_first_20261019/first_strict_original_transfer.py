"""FIRST blinded external source-transfer test of PREVIOUSLY FROZEN classical Q3 structure.

Issue #287 froze all exact Git tree paths/commit/blob IDs BEFORE any target
source body was fetched or inspected. Only import PRE-EXISTING algorithms:
  - full frozen source classic prover Q3V6
  - exact AST dead-state liveness from Issue #285
  - exact public Pre-tight signed relational constraints from Issue #281
  - actual public Trans counterexample-guided Houdini from Issue #281.
No learned model, no new grammar, no solution or filename routing.
Post is used for state-symbol relevance and appended only AFTER the source
R has frozen, not for selection of signed candidate cutpoints/CEGIS removals.
Final full native original Z3 and separate cvc5 original byte-SHA checker.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path
import z3

from experiments.q3_source_prove import (
    sexprs,extract_mixed_original,native_original_relations,
    check_parity,check_formula,source_proof,prove_source,
)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate
from research.evidence.q3_sum4vars_liveness_first_20261019.first_original_liveness import safe_used_states
from research.evidence.q3_cegar_pre_tight_facets_20261019.first_original_tight_facet import (
    pre_tight_source_atoms,exact_counterexample_pruning,
)

FROZEN=(
  ("loopinv","benchmarks/LIA/2005.ICALP_PolyRank/poly2.sl",
   "17448225fffad0cef48634b9d68f4f9193d616d8","POLYRANK_2005"),
  ("loopinv","benchmarks/LIA/2018.NeurIPS_Code2Inv/100.c.sl",
   "ec31090e13e75640447f234a7e2b58cfd09b1086","CODE2INV_2018"),
  ("sygus","comp/2018/Inv_Track/bk-nat.sl",
   "bfbbf92170c9799124211284fc6cdc9aea41fb31","SYGUS_2018"),
)
COMMITS={
 "loopinv":"6ac90265b11431c9477dfbd33e3e3380234c0499",
 "sygus":"13c8deb68a873635879c9a69bc78caebd340f646"
}
SCHEMA="neumann.q3.unseen-three-metadata-origin-source-transfer.v1"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def gitblob(b):
    return hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()

def actual_source_verifier(path,original_sha,formula):
    """Guard against formal-but-irrelevant or self-reported 'PASS'."""
    simple=z3.simplify(formula)
    equiv=z3.Solver()
    equiv.set(timeout=2500)
    equiv.add(z3.Xor(formula,simple))
    if equiv.check()!=z3.unsat:
        raise RuntimeError("ORIGINAL_TO_CVC5_FORMAT_NOT_PROVABLY_IDENTICAL")
    receipt=check_original_candidate(path,simple.sexpr(),
                       expected_source_sha256=original_sha)
    return {
      "status":receipt.get("status"),
      "accepted":receipt.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
      "source_sha256":original_sha,
      "native_original_three_vc":receipt.get("native_original_three_vc"),
      "cvc5_original_three_vc":receipt.get("cvc5_original_three_vc"),
      "candidate_original_sha256":sha(formula.sexpr().encode()),
      "canonical_smt2":simple.sexpr(),
      "XOR_original_canonical":"unsat",
    }

def evaluate_raw_and_goal(path,digest,src,native):
    start=time.perf_counter_ns()
    proj,projection=safe_used_states(src,native)
    atoms,all_bounds,extra=pre_tight_source_atoms(proj,native)
    summary=exact_counterexample_pruning(atoms,native)
    R=summary.pop("invariant")
    frozen_at=time.perf_counter_ns()
    raw=source_proof(R,native)
    candidate=z3.And(R,native["post"])  # after frozen source R
    full=source_proof(candidate,native)
    proof=actual_source_verifier(path,digest,candidate) if full["accepted"] else None
    negatives={}
    if proof and proof["accepted"]:
        for typ,value,expected_sha in (
            ("TRUE","true",digest),
            ("FALSE","false",digest),
            ("SMT_COMMAND","(assert false)",digest),
            ("SHA_MISMATCH",proof["canonical_smt2"],"0"*64),
        ):
            v=check_original_candidate(path,value,
                        expected_source_sha256=expected_sha)
            negatives[typ]=v["status"]!="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
    return {
       "status":"ORIGINAL_3VC_CVC5_CERTIFIED" if proof and proof["accepted"] else
                "NO_CERTIFIED_ORIGINAL_3VC",
       "projection":projection,
       "source_candidate_atom_count":len(atoms),
       "all_finite_exact_source_pre_bounds":len(all_bounds),
       "extra_source_tight_nonlegacy_facets":extra,
       "source_trans_removal_steps":summary["iterations"],
       "source_trans_removed_atoms":sum(x["removed_count"] for x in summary["removed"]),
       "retained_source_inequality_atoms":summary["kept"],
       "nontrivial_two_variable_survives":any(
            sum(c!=0 for c in a["coefficients"])==2 for a in summary["kept"]),
       "new_extra_pre_tight_two_var_survives":any(
            sum(c!=0 for c in a["coefficients"])==2
            and any(a["coefficients"]==b["coefficients"]
                    and a["threshold"]==b["threshold"] for b in extra)
                 for a in summary["kept"]),
       "source_only_relational_R_sha256":sha(R.sexpr().encode()),
       "source_only_R_original_native_three_vc":raw["vcs"],
       "source_only_R_inductive":raw["vcs"].get("initial")=="unsat" and
                                 raw["vcs"].get("consecution")=="unsat",
       "R_strictly_frozen_before_public_Post_conjunction":True,
       "source_R_optimization_wall_ms":round((frozen_at-start)/1e6,3),
       "strengthened_original_native_three_vc":full["vcs"],
       "strengthened_original_native_proved":full["accepted"],
       "unchanged_original_source_bound_cvc5_verifier":proof,
       "four_negative_controls_rejected":negatives,
       "full_new_route_wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
    }

def run_case(root,record):
    repo,rel,blob_id,origin=record
    f=root/repo/rel
    data=f.read_bytes()
    if gitblob(data)!=blob_id:
        raise RuntimeError("PREREGISTERED_UPSTREAM_FILE_BLOB_CHANGED:"+origin)
    digest=sha(data)
    wall=time.perf_counter_ns()
    row={
       "preregistered_collector":repo,
       "preregistered_collection_origin":origin,
       "official_git_commit":COMMITS[repo],
       "original_file":rel,
       "original_upstream_git_blob_sha1":blob_id,
       "original_data_sha256":digest,
       "source_file_bytes":len(data),
       "public_original_source_unseen_before_preregister":True,
       "actual_original_status":"ABSTAIN",
    }
    try:
        if len(data)>512*1024 or f.is_symlink():
            raise RuntimeError("ORIGINAL_SOURCE_BYTES_UNSAFE")
        sexp=sexprs(data)
        src=extract_mixed_original(sexp)
        native=native_original_relations(sexp,src)
        native.update({"now":src["now"],"next":src["next"]})
        parity=check_parity(src,native)
        row["original_semantics_native_custom_xor"]=parity
        if len(parity)!=3 or any(v!="unsat" for v in parity.values()):
            raise RuntimeError("SOURCE_NATIVE_CUSTOM_ORIGINAL_MISMATCH")
        row["original_pre_nonsynthetic"]=check_formula(native["pre"])=="sat"
        row["original_notpost_nonvacuous"]=check_formula(z3.Not(native["post"]))=="sat"
        if not row["original_pre_nonsynthetic"] or not row["original_notpost_nonvacuous"]:
            raise RuntimeError("VACUOUS_ORIGINAL_PRE_OR_NOTPOST")
        row["original_total_state_dimensions"]=len(src["now"])
        baseline_start=time.perf_counter_ns()
        baseline=prove_source(f)
        row["frozen_old_full_classic_portfolio"]={
            "status":baseline.get("status"),"selected_route":baseline.get("selected_route"),
            "reason":baseline.get("reason"),
            "explicit_inductive_original_3vc":
                baseline.get("status")=="ORIGINAL_SOURCE_THREE_VC_CERTIFIED",
            "safety_only_without_exportable_3vc":
                baseline.get("status")=="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT",
            "total_wall_ms":round((time.perf_counter_ns()-baseline_start)/1e6,3),
        }
        row["original_post_alone_native_three_vc"]=source_proof(native["post"],native)["vcs"]
        try:
            row["new_frozen_structure_path"]=evaluate_raw_and_goal(f,digest,src,native)
        except Exception as e:
            row["new_frozen_structure_path"]={
                "status":"ABSTAIN",
                "error_class":type(e).__name__,
                "error_summary":str(e)[:250]}
        new=row["new_frozen_structure_path"]
        new_ok=new.get("status")=="ORIGINAL_3VC_CVC5_CERTIFIED"
        base_ok=row["frozen_old_full_classic_portfolio"]["explicit_inductive_original_3vc"]
        post_ok=all(v=="unsat" for v in row["original_post_alone_native_three_vc"].values())
        row["verified_new_original_proof"]=new_ok
        row["distinct_original_inductive_3vc_vs_full_old_source_portfolio"]=bool(
             new_ok and not base_ok and not post_ok)
        row["actual_original_status"]="SOURCE_ORIGINAL_FULLY_CHECKED"
    except Exception as e:
        row["actual_original_status"]="ABSTAIN"
        row["fail_closed_cause"]=type(e).__name__+":"+str(e)[:250]
    row["entire_original_comparison_wall_ms"]=round(
        (time.perf_counter_ns()-wall)/1e6,3)
    return row

def first_registered_run(root):
    cases=[]
    for spec in FROZEN:
        row=run_case(root,spec)
        cases.append(row)
        print("Q3_FROZEN_THREE_ORIGIN_SOURCE",spec[-1],row["actual_original_status"],
             "old",row.get("frozen_old_full_classic_portfolio",{}).get("status"),
             "new",row.get("new_frozen_structure_path",{}).get("status"),
             "distinct",row.get("distinct_original_inductive_3vc_vs_full_old_source_portfolio",False))
    good=[r for r in cases if r.get("actual_original_status")=="SOURCE_ORIGINAL_FULLY_CHECKED"]
    winners=[r for r in good if r.get("verified_new_original_proof")]
    new_only=[r for r in winners if r.get(
        "distinct_original_inductive_3vc_vs_full_old_source_portfolio")]
    gates={
       "all_three_pre_registered_git_blob_and_unique_sha":len(cases)==3 and
           len({x["original_data_sha256"] for x in cases})==3 and
           len({x["preregistered_collection_origin"] for x in cases})==3,
       "all_three_independent_original_source_semantics_parity_and_noncacuity":
           len(good)==3 and all(
             len(x["original_semantics_native_custom_xor"])==3 and
             all(v=="unsat" for v in x["original_semantics_native_custom_xor"].values())
             and x["original_pre_nonsynthetic"] and x["original_notpost_nonvacuous"] for x in good),
       "at_least_one_real_source_Z3_and_separate_cvc5_3VC":len(winners)>=1,
       "one_distinct_original_3VC_not_exported_by_frozen_full_classic":len(new_only)>=1,
       "at_least_one_distinct_original_non_post_relation_retained":any(
             r["new_frozen_structure_path"].get("nontrivial_two_variable_survives")
             for r in new_only),
       "actual_trans_CEGIS_counterexample_pruning_on_distinct_source":any(
             r["new_frozen_structure_path"].get("source_trans_removed_atoms",0)>0 for r in new_only),
       "every_new_valid_candidate_has_independent_cvc5_3of3_unsat":all(
             r["new_frozen_structure_path"]["unchanged_original_source_bound_cvc5_verifier"] is not None
             and len(r["new_frozen_structure_path"]["unchanged_original_source_bound_cvc5_verifier"]["cvc5_original_three_vc"])==3
             and all(s["status"]=="unsat" and s["returncode"]==0 for s in
             r["new_frozen_structure_path"]["unchanged_original_source_bound_cvc5_verifier"]["cvc5_original_three_vc"].values())
             for r in winners),
       "every_positive_rejects_four_adversarial_false_source_controls":all(
             len(r["new_frozen_structure_path"]["four_negative_controls_rejected"])==4 and
             all(r["new_frozen_structure_path"]["four_negative_controls_rejected"].values())
             for r in winners),
       "all_new_candidates_frozen_before_Post_added":all(
             r["new_frozen_structure_path"].get("R_strictly_frozen_before_public_Post_conjunction")
             for r in winners),
    }
    return {
       "schema":SCHEMA,"preregistered_issue":287,
       "collection_names":["POLYRANK_2005","CODE2INV_2018","SYGUS_2018"],
       "two_repos_and_three_metadata_origins":True,
       "independent_original_human_authors_verified":False,
       "chosen_before_source_bodies_read":True,
       "original_file_receipts":cases,
       "genuinely_new_original_Z3_cvc5_proofs":len(winners),
       "new_original_explicit_certificate_gain_over_previous_full_classic":len(new_only),
       "frozen_first_gate_conditions":gates,
       "frozen_first_gate_pass":all(gates.values()),
       "structure_discovery_is_trained_neural":False,
       "complete_cost_energy_monetary_10x":"NOT_EVALUATED",
       "frozen_history_am1":"FAIL_UNCHANGED",
       "frozen_history_issue279":"FAIL_UNCHANGED",
       "frozen_history_issue283":"FAIL_UNCHANGED",
       "sealed_D3":"BLOCKED",
       "global_Q1_Q7":"OPEN",
       "frontier_model_calls":0,"native_GPU_model_forwards":0,"paid_API_calls":0,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    receipt=first_registered_run(a.source_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("Q3_THREE_ORIGINS_PROSPECTIVE_SCIENCE_GATE",receipt["frozen_first_gate_pass"])
    print("Q3_THREE_ORIGINS_FROZEN_CHECKS",json.dumps(receipt["frozen_first_gate_conditions"],sort_keys=True))
    print("Q3_DISTINCT_CERTIFICATES",receipt["new_original_explicit_certificate_gain_over_previous_full_classic"])
    print("Q1_Q7_GLOBAL",receipt["global_Q1_Q7"])
if __name__=="__main__":main()
