"""First run on twelve original source bodies frozen BEFORE first reading.

Authoritative source: unchanged SMT-LIB Git SHA and exact source parsed
equation. No labels, source filename routing or original answer leakage.

Two-stage classical dispatch: complete modulo-9 integer UNSAT theorem,
else CRT15561 exact bounded witness with actual original SMT2 Z3+cvc5 SAT.
Raw generic Z3/cvc5 direct each get 4sec SAME original source on CPU.
Strong mathematical specialist Direct can adopt the identical dispatch:
NOT a unique NEUMANN Q3 algorithm or global efficiency advantage.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import (
    SOURCE_COMMIT,structural_source,independent_original_grounded_certificate
)
from research.evidence.g0_fresh_four_unsat_20261021.first_original_four_complete_integer_unsat_mod9 import (
    abstract_QFLIA,original_direct,THREE_CUBE_SUM_RESIDUES
)
from research.evidence.g0_crt15561_20261021.exact_four_factor_originals_specialist_comparison import (
    exact_composite_buckets
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
    git_blob_sha1,sha256
)

FREEZE_COMMIT="4eda52b70950dce790fba2b7ac44bc4553feb555"
RADIUS=10000
DIRECT_BUDGET=4

def hybrid_source(raw,path):
    start=time.perf_counter_ns()
    rec={"source":path,"class":"UNKNOWN","mod9_theorem_pass":False,
         "original_independent_Z3_cvc5_source_sat":False,
         "no_neural_forward":True,"source_answer_oracle_provided":False,
         "status":"ABSTAIN"}
    try:
        n,names,parsed=structural_source(raw)
        rec["original_source_exact_integer_cube_equation_parsed"]=True
        rec["source_numeric_rhs"]=n
        rec["structural_source_names"]=names
        if n%9 not in THREE_CUBE_SUM_RESIDUES:
            t=time.perf_counter_ns()
            math=abstract_QFLIA(n)
            rec["finite_unbounded_mod9_independent_Z3_cvc5"]=math
            rec["mod9_theorem_pass"]=math["independent_dual_abstract_agrees_with_finite_math"]
            rec["structural_math_wall_ms"]=(time.perf_counter_ns()-t)/1e6
            if rec["mod9_theorem_pass"]:
                rec["class"]="UNSAT"
                rec["status"]="ORIGINAL_ALL_INTEGER_UNSAT_VIA_COMPLETE_MOD9_THEOREM"
            else:
                rec["status"]="ABSTAIN_INDEPENDENT_MATH_THEOREM_FAILED"
        else:
            t=time.perf_counter_ns()
            trial=exact_composite_buckets(n,RADIUS)
            rec["source_CRT15561_numeric_attempt"]=trial
            rec["structural_math_wall_ms"]=(time.perf_counter_ns()-t)/1e6
            guess=trial["actual_integer_witness"]
            if guess is None:
                rec["status"]="BOUNDED_R10000_NO_WITNESS_UNBOUNDED_UNKNOWN"
            else:
                cert=independent_original_grounded_certificate(
                    raw.decode("utf-8"),names,guess,parsed,"SAT")
                rec["unchanged_original_full_SMT2_dual_source_ground_check"]=cert
                rec["original_independent_Z3_cvc5_source_sat"]=cert["independent_dual_result"]
                if cert["independent_dual_result"]:
                    rec["class"]="SAT"
                    rec["status"]="TRUE_ORIGINAL_UNCHANGED_SMT2_GROUNDED_DUAL_SAT"
                else:
                    rec["status"]="ABSTAIN_UNVERIFIED_TRUE_ORIGINAL_GROUND"
    except Exception as e:
        rec["status"]="ABSTAIN_SOURCE_PARSER_OR_VERIFIER_EXCEPTION"
        rec["error"]=type(e).__name__+":"+str(e)[:360]
    rec["complete_original_source_parse_math_candidate_full_certificate_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return rec

def direct_source(raw,path):
    start=time.perf_counter_ns()
    try:
        target,names,parsed=structural_source(raw)
        direct=original_direct(raw,parsed,DIRECT_BUDGET)
        outcomes=[direct["full_unchanged_source_Z3"],direct["full_unchanged_source_cvc5"]]
        if "SAT" in outcomes and "UNSAT" in outcomes:
            status="CONTRADICTORY_GENUINE_SOLVERS"
        elif "SAT" in outcomes:status="SAT"
        elif "UNSAT" in outcomes:status="UNSAT"
        else:status="UNKNOWN"
        rec={"source":path,"class":status,
             "original_source_full_raw_unchanged_Z3_and_cvc5":direct}
    except Exception as e:
        rec={"source":path,"class":"ABSTAIN","error":type(e).__name__+":"+str(e)[:340]}
    rec["whole_full_original_direct_parse_and_raw_two_solver_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return rec

def evaluate(root,item):
    ts=time.perf_counter_ns()
    rec={"source":item["path"],"expected_frozen_source_git_blob":item["sha1_git_blob"],
         "original_authenticity_valid":False,
         "scientific_split":"FIRST_SOURCE_BODY_UNOPENED_GIT_SHA_SELECT_BUT_FILENAME_NUMERIC_HINT",
         "status":"UNKNOWN_OR_ABSTAIN"}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("FIRST_ORIGINAL_SOURCE_SHA_AND_BYTES_CHANGED")
        rec["true_original_source_sha256"]=sha256(raw)
        rec["original_authenticity_valid"]=True
        rec["NEUMANN_no_neural_classical_source_dispatch"]=hybrid_source(raw,item["path"])
        rec["raw_direct_two_solver_comparator"]=direct_source(raw,item["path"])
        h=rec["NEUMANN_no_neural_classical_source_dispatch"]
        d=rec["raw_direct_two_solver_comparator"]
        if d["class"]=="CONTRADICTORY_GENUINE_SOLVERS" or (
            h["class"]!="UNKNOWN" and d["class"] in ("SAT","UNSAT") and h["class"]!=d["class"]):
            rec["status"]="FAIL_CONTRADICTORY_TRUE_ORIGINAL_SOURCE_SOLUTIONS"
        elif h["class"] in ("SAT","UNSAT"):
            rec["status"]="STRUCTURAL_ORIGINAL_SOURCE_CERTIFIED"
        elif h["class"]=="UNKNOWN":
            rec["status"]="ORIGINAL_SOURCE_STRUCTURAL_UNKNOWN"
        else:
            rec["status"]="ABSTAIN_SOURCE_OR_VERIFIER_ERROR"
        rec["strong_direct_union_raw_solved"]=d["class"] in ("SAT","UNSAT")
        rec["source_structural_solved"]=h["class"] in ("SAT","UNSAT")
        rec["additional_original_solved_vs_raw_direct"]=(
            rec["source_structural_solved"] and not rec["strong_direct_union_raw_solved"])
        rec["same_confirmed_source_status"]=(
            h["class"]==d["class"] and h["class"] in ("SAT","UNSAT"))
        rec["paired_raw_direct_over_hybrid_time_if_both_source_solved"]=(
           d["whole_full_original_direct_parse_and_raw_two_solver_wall_ms"]/
           h["complete_original_source_parse_math_candidate_full_certificate_wall_ms"]
           if rec["same_confirmed_source_status"] else None)
    except Exception as e:
        rec["status"]="ABSTAIN_ORIGINAL_SOURCE_GIT_AUTHENTICATION_FAILURE"
        rec["error"]=type(e).__name__+":"+str(e)[:380]
    rec["whole_study_wall_ms"]=(time.perf_counter_ns()-ts)/1e6
    print("G0_FIRST_12_HASH_ORIGINAL",rec["source"],
          "N",rec.get("NEUMANN_no_neural_classical_source_dispatch",{}).get("source_numeric_rhs"),
          "HYBRID",rec.get("NEUMANN_no_neural_classical_source_dispatch",{}).get("class"),
          "RAW_DIRECT",rec.get("raw_direct_two_solver_comparator",{}).get("class"),
          "STATUS",rec["status"],
          "WALL",round(rec["whole_study_wall_ms"],2),
          "ERROR",rec.get("error"),flush=True)
    return rec

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    frozen=json.loads(args.freeze.read_text())
    if frozen["schema"]!="neumann.G0.first_hash_selected_twelve_math_capability_headroom.v1":
        raise RuntimeError("FIRST_HASH_SOURCE_CONTRACT_CHANGED")
    if frozen["upstream"].split("@")[-1]!=SOURCE_COMMIT or len(frozen["targets"])!=12:
        raise RuntimeError("TWELVE_FIRST_ORIGINAL_IDS_CHANGED")
    cases=[evaluate(args.root,item) for item in frozen["targets"]]
    integrity=sum(c["original_authenticity_valid"] for c in cases)
    structural_sat=sum(c.get("NEUMANN_no_neural_classical_source_dispatch",{}).get("class")=="SAT" for c in cases)
    structural_unsat=sum(c.get("NEUMANN_no_neural_classical_source_dispatch",{}).get("class")=="UNSAT" for c in cases)
    direct_sat=sum(c.get("raw_direct_two_solver_comparator",{}).get("class")=="SAT" for c in cases)
    direct_unsat=sum(c.get("raw_direct_two_solver_comparator",{}).get("class")=="UNSAT" for c in cases)
    conflict=sum(c["status"]=="FAIL_CONTRADICTORY_TRUE_ORIGINAL_SOURCE_SOLUTIONS" for c in cases)
    both=[c for c in cases if c.get("same_confirmed_source_status")]
    report={
       "schema":"neumann.g0.hashselected12_first_actual_original_zero_neural_structural_vs_raw_z3_cvc5.v1",
       "immutable_git_blob_cohort_before_first_content_read_commit":FREEZE_COMMIT,
       "all_12_original_cases_retained":len(cases)==12,
       "original_source_verified_Git_blobs":integrity,
       "first_source_body_unopened_at_freeze_but_number_in_filename":True,
       "eligible_selection_scanned_only_directory_first1000_entries_not_full_corpus":True,
       "source_structural_SAT_original_Z3_cvc5_ground_verified":structural_sat,
       "source_structural_UNSAT_original_exact_ast_mod9_independent_finite_proof":structural_unsat,
       "source_structural_resolved_total":structural_sat+structural_unsat,
       "raw_source_direct_Z3_or_cvc5_4sec_SAT":direct_sat,
       "raw_source_direct_Z3_or_cvc5_4sec_UNSAT":direct_unsat,
       "raw_source_direct_union_total":direct_sat+direct_unsat,
       "source_resolved_by_classical_structural_but_raw_direct_unknown":sum(c.get("additional_original_solved_vs_raw_direct",False) for c in cases),
       "independent_original_classification_conflicts":conflict,
       "both_arms_same_correct_full_source_disposition_count":len(both),
       "no_trained_model_or_learned_new_representation":True,
       "equal_authority_strong_direct_can_use_same_mod9_and_CRT15561":True,
       "historical_original_prior_SMT_COMP_submission_claims_not_imported_as_matched_runtime":True,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
       "first_source_SHA_selection_original_cases":cases
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("G0_FIRST_SHA_12_SOURCE_AUTHENTIC",integrity,"/12")
    print("G0_FIRST_SHA_12_STRUCTURAL_SOURCE_CERTIFIED",structural_sat,"SAT",structural_unsat,"UNSAT","TOTAL",structural_sat+structural_unsat)
    print("G0_FIRST_SHA_12_RAW_DIRECT",direct_sat,"SAT",direct_unsat,"UNSAT","TOTAL",direct_sat+direct_unsat)
    print("G0_FIRST_SHA_12_STRUCTURAL_EXTRA_OVER_RAW",report["source_resolved_by_classical_structural_but_raw_direct_unknown"])
    print("G0_FIRST_SHA_12_CONFLICTS",conflict)
    print("G0_FIRST_SHA_12_GLOBAL_Q3_Q4",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
