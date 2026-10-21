"""PRE-SOURCE-BODY first 12 SHA-ranked official SMT-LIB QF_NIA originals.

Uniform source-AST-powered classical structural policy, no per-source code:
- true complete integer UNSAT by original 3-cubes mod 9 abstraction with
  independent Z3+cvc5 proof if target residue impossible;
- otherwise exact CRT15561 ±10000 finite integer search, ONLY actual
  original SMT2 positive witnesses independently SAT Z3+cvc5 admitted;
- else UNKNOWN (never numeric miss=>unbounded UNSAT).
Same unchanged original direct Z3 and cvc5 4s control each. Existing number
theory tools available to Strong Direct, NO NEUMANN-specific learned novelty.
Filename metadata leaks actual RHS; selection used only git SHA sort.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import (
    SOURCE_COMMIT,structural_source,independent_original_grounded_certificate
)
from research.evidence.g0_crt15561_20261021.exact_four_factor_originals_specialist_comparison import (
    exact_composite_buckets
)
from research.evidence.g0_fresh_four_unsat_20261021.first_original_four_complete_integer_unsat_mod9 import (
    abstract_QFLIA,original_direct,THREE_CUBE_SUM_RESIDUES
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
    git_blob_sha1,sha256
)

FIRST_FREEZE="4eda52b70950dce790fba2b7ac44bc4553feb555"
RADIUS=10000

def one_original(root,item):
    begin=time.perf_counter_ns()
    case={"source":item["path"],"expected_original_sha1_git_blob":item["sha1_git_blob"],
          "status":"ABSTAIN","true_original_automated_hybrid_status":"UNKNOWN",
          "pure_structural_hybrid_no_neural_calls":True,
          "original_full_source_semantics_authenticated":False,
          "hybrid_correctly_verified":False}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("FROZEN_SHA_AUTHENTIC_SOURCE_CHANGED")
        case["original_source_SHA256"]=sha256(raw)
        n,names,orig=structural_source(raw)
        case["original_actual_RHS"]=n
        case["three_integer_source_symbols"]=names
        case["original_full_source_semantics_authenticated"]=True
        modular=abstract_QFLIA(n)
        case["independent_Z3_cvc5_source_abstract_mod9_theorem"]=modular
        if not modular["independent_dual_abstract_agrees_with_finite_math"]:
            case["status"]="ABSTAIN_UNVERIFIED_MOD9_STRUCTURAL_ABSTRACTION"
        elif n%9 not in THREE_CUBE_SUM_RESIDUES:
            case["true_original_automated_hybrid_status"]="UNSAT"
            case["hybrid_correctly_verified"]=True
            case["status"]="ORIGINAL_FULL_UNBOUNDED_UNSAT_BY_SOUND_SOURCE_MOD9_ABSTRACTION"
        else:
            search=exact_composite_buckets(n,RADIUS)
            case["bounded_structural_specialist"]=search
            triple=search["actual_integer_witness"]
            if triple:
                check=independent_original_grounded_certificate(
                    raw.decode("utf-8"),names,triple,orig,"SAT")
                case["independent_true_full_raw_source_z3_cvc5"]=check
                if check["independent_dual_result"]:
                    case["true_original_automated_hybrid_status"]="SAT"
                    case["hybrid_correctly_verified"]=True
                    case["status"]="ORIGINAL_FULL_SOURCE_SAT_INDEPENDENT_DUAL"
                else:
                    case["status"]="ABSTAIN_ORIGINAL_WITNESS_NOT_DUAL"
            else:
                case["status"]="UNKNOWN_NUMERIC_RADIUS10000_NOT_FULL_ORIGINAL_UNSAT"
        case["true_original_hybrid_complete_independent_proof_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
        direct=original_direct(raw,orig,4)
        case["unchanged_raw_original_direct_z3_cvc5"]=direct
        p,q=direct["full_unchanged_source_Z3"],direct["full_unchanged_source_cvc5"]
        case["direct_union_original_result"]=(
            "SAT" if p=="SAT" or q=="SAT" else
            "UNSAT" if p=="UNSAT" and q=="UNSAT" else "UNKNOWN")
        case["direct_original_source_cost_both_solving_ms"]=(
            direct["raw_z3_wall_ms"]+direct["raw_cvc5_wall_ms"])
        if case["hybrid_correctly_verified"] and case["direct_union_original_result"] not in (
            "UNKNOWN",case["true_original_automated_hybrid_status"]):
            case["status"]="FAIL_DISAGREE_WITH_DIRECT_ORIGINAL_SOURCE"
            case["hybrid_correctly_verified"]=False
        case["source_original_hybrid_vs_direct_capability"]="HYBRID_ONLY" if (
            case["hybrid_correctly_verified"] and case["direct_union_original_result"]=="UNKNOWN"
        ) else "DIRECT_ONLY" if (
            not case["hybrid_correctly_verified"] and case["direct_union_original_result"]!="UNKNOWN"
        ) else "BOTH" if (
            case["hybrid_correctly_verified"] and case["direct_union_original_result"]!="UNKNOWN"
        ) else "NEITHER"
    except Exception as e:
        case["status"]="ABSTAIN_SOURCE_ERROR"
        case["error"]=type(e).__name__+":"+str(e)[:380]
    case["full_experiment_hybrid_plus_direct_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
    print("G0_FIRST_HASHED_ORIGINAL",case["source"],"TRUE_RHS",case.get("original_actual_RHS"),
          "STRUCTURE",case["true_original_automated_hybrid_status"],
          "DIRECT",case.get("direct_union_original_result"),
          "CAPABILITY",case.get("source_original_hybrid_vs_direct_capability"),
          "STRUCTURAL_WALL",case.get("true_original_hybrid_complete_independent_proof_wall_ms"),
          "ERROR",case.get("error"),flush=True)
    return case

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    m=json.loads(args.freeze.read_text())
    if m["schema"]!="neumann.G0.first_hash_selected_twelve_math_capability_headroom.v1":
        raise RuntimeError("SELECTOR_CONTRACT_CHANGED")
    if not m["frozen_before_first_source_body_read"] or len(m["targets"])!=12:
        raise RuntimeError("MISSING_12_ORIGINAL_FROZEN_FIRST_SOURCE")
    if not len({i["sha1_git_blob"] for i in m["targets"]})==12:
        raise RuntimeError("DUPLICATE_ORIGINAL_SOURCE")
    if m["upstream"].split("@")[-1]!=SOURCE_COMMIT:
        raise RuntimeError("ORIGINAL_UPSTREAM_SOURCE_COMMIT_CHANGED")
    cases=[one_original(args.root,t) for t in m["targets"]]
    classes=("SAT","UNSAT","UNKNOWN")
    # FIRST IMMUTABLE execution #39537541152 exposed a reporting-only bug:
    # UNKNOWN was counted only when hybrid_correctly_verified==True, which is
    # correctly False for UNKNOWN, so first report printed UNKNOWN:0 although
    # all 12 individual source rows retained the true one UNKNOWN status.
    # Preserve the first run and correct ONLY aggregate accounting.
    hy={
       "SAT":sum(r["hybrid_correctly_verified"] and
                 r["true_original_automated_hybrid_status"]=="SAT" for r in cases),
       "UNSAT":sum(r["hybrid_correctly_verified"] and
                   r["true_original_automated_hybrid_status"]=="UNSAT" for r in cases),
    }
    hy["UNKNOWN"]=len(cases)-hy["SAT"]-hy["UNSAT"]
    assert sum(hy.values())==12
    direct={k:sum(r.get("direct_union_original_result","UNKNOWN")==k for r in cases) for k in classes}
    gain=sum(r.get("source_original_hybrid_vs_direct_capability")=="HYBRID_ONLY" for r in cases)
    extra=sum(r.get("source_original_hybrid_vs_direct_capability")=="DIRECT_ONLY" for r in cases)
    report={
      "schema":"neumann.g0.first_source_sha_selected_12_true_originals_structural_vs_generic_direct.v1",
      "frozen_selected_prior_to_first_source_body_commit":FIRST_FREEZE,
      "immutable_first_run_actions_id":39537541152,
      "immutable_first_run_head_sha":"d83c609888af80a5a5515430264730458fa84a38",
      "aggregation_correction_after_first_run_only":True,
      "source_level_historical_first_results_retained":True,
      "all_12_original_true_source_rows_kept":len(cases)==12,
      "source_file_names_leak_numeric_rhs_selection_did_NOT_use_rhs":True,
      "same_original_STC_math_family_not_cross_family":True,
      "source_verified_exact_AST_parity_count":sum(r["original_full_source_semantics_authenticated"] for r in cases),
      "no_trained_neural_model_calls":True,
      "hybrid_true_original_disposition_counts":hy,
      "direct_generic_4sec_each_union_disposition_counts":direct,
      "hybrid_ONLY_true_original_SAT_or_complete_UNSAT":gain,
      "raw_direct_ONLY_true_original_SAT_or_UNSAT":extra,
      "non_source_specific_fixed_mathematical_abstraction_and_specialist_search":True,
      "no_new_mathematical_invention_or_strongest_equal_auth_direct_gap":True,
      "do_not_claim_global_Q3_or_Q4":"OPEN",
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "cases":cases
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("G0_SHA_SELECTED_FIRST_12_SOURCE_PARITY",report["source_verified_exact_AST_parity_count"],"/12")
    print("G0_SHA_SELECTED_STRUCTURAL_TRUE_ORIGINAL_RESULT_COUNTS",hy)
    print("G0_SHA_SELECTED_RAW_GENERIC_DIRECT_4SEC_RESULT_COUNTS",direct)
    print("G0_SHA_SELECTED_HYBRID_ONLY_VERIFIED_CAPABILITY",gain,"/12")
    print("G0_SHA_SELECTED_DIRECT_ONLY_VERIFIED_CAPABILITY",extra,"/12")
    print("G0_GLOBAL_Q3_Q4",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
