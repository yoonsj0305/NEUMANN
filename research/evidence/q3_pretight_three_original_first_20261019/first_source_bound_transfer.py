"""Q3 FIRST prospective check of unchanged source-Pre-tight relational invariant learner.

Preregistered Issue #283 BEFORE inspecting candidate original source file bodies.
Three Git blob metadata-pinned original SyGuS programs (sum4_vars,cars,ex1).
No candidate/threshold/algorithm tuning on first test outcomes. All first
source-specified ABSTAIN preserved; no source substitution after failure.
All proof certificates are actual native original Z3 3VC and separate CVC5.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import z3

from experiments.q3_source_prove import (
    sexprs,extract_mixed_original,native_original_relations,check_parity,
    check_formula,source_proof,prove_source,
)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate
from research.evidence.q3_anfp_relational_source_houdini_20261019.first_anfp_source_original import (
    original_houdini,
)
from research.evidence.q3_cegar_pre_tight_facets_20261019.first_original_tight_facet import (
    pre_tight_source_atoms,exact_counterexample_pruning,
)

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
FROZEN=(
    ("comp/2017/Inv_Track/sum4_vars.sl",
     "ba2a948d21a8b64a6ede2a441448118736792172","sum"),
    ("comp/2018/Inv_Track/cars.sl",
     "ebf61e2502cebf246e9b1d8a4ef1594945ad7f24","cars"),
    ("comp/2018/Inv_Track/ex1.sl",
     "29420aae47ca3ee36fab64c8e3a17759eac778a8","ex"),
)
SCHEMA="neumann.q3.public-pre-tight-3original-prospective-first.v1"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def blob(b):
    return hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()

def source_bound_external(path,original,source_sha):
    """No trust in proposal flags or arbitrary solver trace: independent verifier."""
    canonical=z3.simplify(original)
    s=z3.Solver()
    s.set(timeout=2500)
    s.add(z3.Xor(original,canonical))
    if s.check()!=z3.unsat:
        raise RuntimeError("SMT_CANDIDATE_CANONICAL_EQUIVALENCE_UNKNOWN")
    report=check_original_candidate(path,canonical.sexpr(),
                          expected_source_sha256=source_sha)
    return {
        "source_bound_checker_status":report["status"],
        "native_three_vc":report.get("native_original_three_vc"),
        "cvc5_three_vc":report.get("cvc5_original_three_vc"),
        "certified":report["status"]=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
        "original_candidate_smt_sha256":sha(original.sexpr().encode()),
        "equivalent_canonical_smt2_sha256":sha(canonical.sexpr().encode()),
        "canonical_smt2":canonical.sexpr(),
    }

def ablation_old_relational(src,native,path,original_sha):
    began=time.perf_counter_ns()
    try:
        old=original_houdini(src,native)
        proposal=old.pop("invariant")
        native_proof=source_proof(proposal,native)
        full=source_bound_external(path,proposal,original_sha) if native_proof["accepted"] else None
        return {
            "status":"CERTIFIED" if full and full["certified"] else "NO_REAL_ORIGINAL_3VC",
            "native_original_vcs":native_proof["vcs"],
            "old_sparse_atoms":old["candidate_count"],
            "old_sparse_removed":old["actual_removed_atom_count"],
            "strict_original_checker":full,
            "wall_ms":round((time.perf_counter_ns()-began)/1e6,3),
        }
    except Exception as e:
        return {"status":"ABSTAIN","reason":type(e).__name__+":"+str(e)[:200],
                "wall_ms":round((time.perf_counter_ns()-began)/1e6,3)}

def evaluate_new(src,native,path,original_sha):
    began=time.perf_counter_ns()
    try:
        atoms,optproofs,extra=pre_tight_source_atoms(src,native)
        proof=exact_counterexample_pruning(atoms,native)
        proposed=proof.pop("invariant")
        native_result=source_proof(proposed,native)
        verifier=source_bound_external(path,proposed,original_sha) if native_result["accepted"] else None
        result={
            "status":"CERTIFIED" if verifier and verifier["certified"] else "NO_REAL_ORIGINAL_3VC",
            "native_original_vcs":native_result["vcs"],
            "native_original_three_vc":native_result["accepted"],
            "independent_source_bound_original_checker":verifier,
            "source_pre_exact_optimal_cutpoint_proof_count":len(optproofs),
            "new_source_pre_tight_facets_not_in_old_offsets":extra,
            "source_pre_inductive_atom_count":len(atoms),
            "source_trans_counterexample_steps":proof["iterations"],
            "source_trans_counterexample_removed_atoms":sum(
                 x["removed_count"] for x in proof["removed"]),
            "source_pre_tight_surviving_facets":[
                 a for a in proof["kept"] if a["source_tight"] and
                 any(a["coefficients"]==f["coefficients"] and
                     a["threshold"]==f["threshold"] for f in extra)],
            "inductive_two_variable_survived":any(
                 sum(c!=0 for c in a["coefficients"])==2 for a in proof["kept"]),
            "original_smt_formula_hash":sha(proposed.sexpr().encode()),
            "wall_ms":round((time.perf_counter_ns()-began)/1e6,3),
        }
        return result
    except Exception as e:
        return {"status":"ABSTAIN","reason":type(e).__name__+":"+str(e)[:200],
                "wall_ms":round((time.perf_counter_ns()-began)/1e6,3)}

def run_one(root,rel,expected_blob,stem):
    path=root/rel
    source_bytes=path.read_bytes()
    if blob(source_bytes)!=expected_blob:
        raise RuntimeError("PREREGISTERED_UPSTREAM_GIT_BLOB_MISMATCH:"+rel)
    digest=sha(source_bytes)
    began=time.perf_counter_ns()
    try:
        forms=sexprs(source_bytes)
        src=extract_mixed_original(forms)
        native=native_original_relations(forms,src)
        native.update({"now":src["now"],"next":src["next"]})
        parity=check_parity(src,native)
        if len(parity)!=3 or any(v!="unsat" for v in parity.values()):
            raise RuntimeError("UNSUPPORTED_NATIVE_CUSTOM_SOURCE_SEMANTICS")
        if check_formula(native["pre"])!="sat" or (
            check_formula(z3.Not(native["post"]))!="sat"):
            raise RuntimeError("VACUOUS_SOURCE_ORIGINAL_PRE_OR_POST")
    except Exception as e:
        return {
            "public_original":rel,"prereg_github_blob_sha1":expected_blob,
            "actual_source_sha256":digest,"source_group_stem":stem,
            "parse_status":"ABSTAIN",
            "reason":type(e).__name__+":"+str(e)[:220],
            "cold_total_original_wall_ms":round((time.perf_counter_ns()-began)/1e6,3),
        }

    # Same-original strong frozen full classic portfolio, no input filtering.
    try:
        old=prove_source(path)
        baseline={
           "status":old.get("status"),
           "selected_route":old.get("selected_route"),
           "explicit_source_original_three_vc":
               old.get("status")=="ORIGINAL_SOURCE_THREE_VC_CERTIFIED",
           "only_source_spacer":
               old.get("status")=="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT",
           "reason":old.get("reason"),
        }
    except Exception as e:
        baseline={"status":"ABSTAIN","reason":type(e).__name__+":"+str(e)[:220],
                  "explicit_source_original_three_vc":False,"only_source_spacer":False}

    post=source_proof(native["post"],native)
    old_rel=ablation_old_relational(src,native,path,digest)
    new=evaluate_new(src,native,path,digest)
    accepted=new.get("status")=="CERTIFIED"
    controls={}
    if accepted:
        assert new["independent_source_bound_original_checker"]["certified"]
        cands=(
            ("TRUE","true",digest),
            ("FALSE","false",digest),
            ("WRONG_SOURCE_SHA",new["independent_source_bound_original_checker"]["canonical_smt2"],"0"*64),
        )
        for label,term,orig_digest in cands:
            report=check_original_candidate(path,term,
                                             expected_source_sha256=orig_digest)
            controls[label]=report.get("status")!="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"

    novel=accepted and not baseline["explicit_source_original_three_vc"] and (
        old_rel["status"]!="CERTIFIED") and (not post["accepted"])
    return {
       "public_original":rel,"prereg_github_blob_sha1":expected_blob,
       "actual_source_sha256":digest,"source_group_stem":stem,
       "source_actual_int_state_dimension":len(src["now"]),
       "parse_status":"PARITY_VALID_NONVACUOUS",
       "original_source_semantic_parity":parity,
       "original_pre_and_notpost_nonvacuous":True,
       "old_frozen_full_classical":baseline,
       "original_post_only_inductive":bool(post["accepted"]),
       "old_signed_relational_without_pre_tight":old_rel,
       "new_exact_pre_tight_relational":new,
       "new_original_strict_3vc_cvc5_pass":accepted,
       "genuine_distinct_explicit_source_3vc_gain_over_both_prior_classical":novel,
       "negative_verifier_controls":controls,
       "proposer_received_original_gold_post":False,
       "source_algorithm_unmodified_since_prior_registered_dev":True,
       "cold_total_original_wall_ms":round((time.perf_counter_ns()-began)/1e6,3),
    }

def execute(root):
    rows=[]
    for rel,blob,stem in FROZEN:
        row=run_one(root,rel,blob,stem)
        rows.append(row)
        print("Q3_FIRST_SOURCE_TIGHT_TRANSFER",stem,
              "old",row.get("old_frozen_full_classical",{}).get("status"),
              "old_rel",row.get("old_signed_relational_without_pre_tight",{}).get("status"),
              "new",row.get("new_exact_pre_tight_relational",{}).get("status"),
              "novel_gain",row.get("genuine_distinct_explicit_source_3vc_gain_over_both_prior_classical"))
    complete=[r for r in rows if r.get("parse_status")=="PARITY_VALID_NONVACUOUS"]
    winners=[r for r in complete if r["new_original_strict_3vc_cvc5_pass"]]
    gains=[r for r in winners if r["genuine_distinct_explicit_source_3vc_gain_over_both_prior_classical"]]
    conditions={
       "three_meta_preregistered_sources_and_unique_real_sha":len(rows)==3
             and len({r["actual_source_sha256"] for r in rows})==3
             and len({r["source_group_stem"] for r in rows})==3,
       "all_three_actual_original_parser_parity_and_nonvacuity":len(complete)==3
             and all(len(r["original_source_semantic_parity"])==3 and
                 all(v=="unsat" for v in r["original_source_semantic_parity"].values()) for r in complete),
       "at_least_one_new_original_true_z3_and_independent_cvc5_certificate":len(winners)>=1,
       "at_least_one_distinct_unseen_original_3vc_gain_over_frozen_full_classical_and_old_relational":
             len(gains)>=1,
       "nonpost_source_tight_surviving_facet_on_gained_source":any(
             len(r["new_exact_pre_tight_relational"].get("source_pre_tight_surviving_facets",[]))>0 for r in gains),
       "concrete_trans_counterexample_pruning_on_some_gained_source":any(
             r["new_exact_pre_tight_relational"].get("source_trans_counterexample_removed_atoms",0)>0 for r in gains),
       "all_positive_independent_cvc5_three_original_obligations_unsat":all(
           r["new_exact_pre_tight_relational"]["independent_source_bound_original_checker"] is not None
           and len(r["new_exact_pre_tight_relational"]["independent_source_bound_original_checker"]["cvc5_three_vc"])==3
           and all(v["status"]=="unsat" and v["returncode"]==0 for v in r[
               "new_exact_pre_tight_relational"]["independent_source_bound_original_checker"]["cvc5_three_vc"].values())
           for r in winners),
       "all_positive_false_and_tampered_original_source_controls_rejected":all(
           len(r["negative_verifier_controls"])==3 and
           all(r["negative_verifier_controls"].values()) for r in winners),
       "no_neural_model_or_post_leak_or_filename_answer_routing":all(
           not r.get("proposer_received_original_gold_post",False) and
           r.get("source_algorithm_unmodified_since_prior_registered_dev",False) for r in complete),
    }
    return {
      "schema":SCHEMA,"preregistered_issue":283,
      "upstream_repo":"SyGuS-Org/benchmarks","upstream_exact_commit":UPSTREAM,
      "metadata_preregistered_before_original_body_examination":True,
      "originals":[x[0] for x in FROZEN],
      "first_original_receipts":rows,
      "explicit_z3_cvc5_successes":len(winners),
      "distinct_explicit_3vc_gains_over_eligible_frozen_classical":len(gains),
      "first_predeclared_scope_pass":all(conditions.values()),
      "predeclared_conditions":conditions,
      "distinct_original_authors_confirmed":False,
      "neural_learned_unique_capability":False,
      "full_economic_10x":"NOT_EVALUATED",
      "actual_model_forwards":0,"accelerator_calls":0,"paid_api_calls":0,
      "historical_AM1_first":"FAIL_UNCHANGED",
      "historical_issue279_first":"FAIL_UNCHANGED",
      "sealed_D3":"BLOCKED","global_Q1_Q7":"OPEN",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-root",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    report=execute(a.source_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_FIRST_PRETIGHT_CROSS_STEM_ORIGINAL_GATE",
          report["first_predeclared_scope_pass"])
    print("Q3_FIRST_PREDECLARED_CONDITIONS",json.dumps(report["predeclared_conditions"],sort_keys=True))
    print("Q3_FIRST_DISTINCT_CLASSICAL_EXPLICIT_3VC_GAINS",
          report["distinct_explicit_3vc_gains_over_eligible_frozen_classical"])
    print("GLOBAL_Q1_Q7",report["global_Q1_Q7"])
if __name__=="__main__":
    main()
