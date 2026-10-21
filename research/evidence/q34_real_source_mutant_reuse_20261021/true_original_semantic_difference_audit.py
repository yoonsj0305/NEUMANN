"""POSTHOC original program-source semantic delta adversarial audit.

Same source Git frozen 8 real mutation cohort. SHA divergence ALONE cannot
demonstrate meaningful semantic changes. Compare actual typed/native source
original Pre,Trans,Post after aligning identical original-state symbols;
require both Z3 and independently pinned cvc5 SAT witness for XOR of
real original formulas. Syntactic delta != reachable-behavior delta.
Do NOT change or select previous first trial cases based on outcomes.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare
from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import dual,sha

REV="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE_KEYS=("pre","trans","post")

def check_one(root,item,base):
    t=time.perf_counter_ns()
    row={"source":item["path"],"group":item["group"],
         "first_frozen_original_git_blob":item["git_blob"],
         "same_Git_blob_as_base":item["git_blob"]==base["git_blob"],
         "verified_native_semantic_delta":False,
         "status":"ABSTAIN",
    }
    try:
        _,orig_p,orig_n,orig_proof=prepare(root,base)
        _,target_p,target_n,target_proof=prepare(root,item)
        row["original_true_source_SHA_and_native_dual_parity"]=True
        row["candidate_true_source_SHA_and_native_dual_parity"]=True
        row["state_typed_signature_identical"]=orig_p["states"]==target_p["states"]
        if not row["state_typed_signature_identical"]:
            row["status"]="SIGNATURE_DIFFERENT_SEMANTIC_XOR_COMPARISON_INELIGIBLE"
            return row
        substitutions=list(zip(orig_p["now"],target_p["now"]))+list(zip(orig_p["next"],target_p["next"]))
        delta={}
        for key in SOURCE_KEYS:
            lhs=z3.substitute(orig_n[key],*substitutions)
            rhs=target_n[key]
            result=dual(z3.Xor(lhs,rhs),"sat",10)
            delta[key]={"true_original_symbolic_formula_inequivalence_Z3_cvc5_SAT":result["dual_pass"],
                        "real_source_XOR_query_original_both_solver_results":result}
        row["source_semantic_delta_evidence"]=delta
        row["verified_native_semantic_delta"]=any(v["true_original_symbolic_formula_inequivalence_Z3_cvc5_SAT"] for v in delta.values())
        row["status"]="ORIGINAL_SEMANTIC_FORMULAS_DIFFER_INDEPENDENT_DUAL" if row["verified_native_semantic_delta"] else "NO_DUAL_PROVED_ORIGINAL_SEMANTIC_FORMULA_DIFFERENCE"
    except Exception as e:
        row["error"]=type(e).__name__+":"+str(e)[:340]
        row["status"]="ABSTAIN_ORIGINAL_SEMANTIC_AUDIT_ERROR"
    finally:
        row["source_semantic_delta_audit_wall_ms"]=(time.perf_counter_ns()-t)/1e6
        print("ORIGINAL_SOURCE_SEMANTIC_DIFF",row["source"],
              row["status"],
              "DIFF_KEYS",[
                k for k,v in row.get("source_semantic_delta_evidence",{}).items()
                if v["true_original_symbolic_formula_inequivalence_Z3_cvc5_SAT"]],
              "ERROR",row.get("error"),flush=True)
    return row

def source_same_positive(root,b):
    _,parsed,native,sourceauth=prepare(root,b)
    tests={k:dual(z3.Xor(native[k],native[k]),"unsat",10) for k in SOURCE_KEYS}
    return {"source":b["path"],"same_source_all_three_formula_XOR_UNSAT_in_Z3_cvc5":
            all(q["dual_pass"] for q in tests.values()),"dual":tests}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    opts=ap.parse_args()
    frozen=json.loads(opts.freeze.read_text())
    if frozen["upstream_commit"]!=REV or len(frozen["baseline_origins"])!=3 or len(frozen["mutants"])!=8:
        raise RuntimeError("SOURCE_PREVIOUSLY_FROZEN_GIT_BLOBS_CHANGED")
    group={x["group"]:x for x in frozen["baseline_origins"]}
    controls=[source_same_positive(opts.root,b) for b in frozen["baseline_origins"]]
    cases=[check_one(opts.root,item,group[item["group"]]) for item in frozen["mutants"]]
    report={
        "schema":"neumann.q34.real_original_mutant_posthoc_semantic_difference_2solver.v1",
        "original_source_first_mutation_performance_study_unchanged":True,
        "not_fresh_since_mutants_opened_in_first_trial":True,
        "all_eight_first_source_mutants_retained":len(cases)==8,
        "all_original_baseline_positive_equivalence_controls_dual_pass":all(x["same_source_all_three_formula_XOR_UNSAT_in_Z3_cvc5"] for x in controls),
        "number_true_original_source_semantic_formula_deltas_independently_proven":sum(x["verified_native_semantic_delta"] for x in cases),
        "number_source_mutants_sha_different_than_base":sum(not x["same_Git_blob_as_base"] for x in cases),
        "source_original_semantic_XOR_does_not_prove_reachability_or_behavior_difference":True,
        "no_learned_achievement":True,"global_Q3":"OPEN","global_Q4":"OPEN",
        "original_positive_equal_source_controls":controls,"real_source_variants":cases,
    }
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("REAL_ORIGINAL_SEMANTICALLY_DISTINGUISHED_MUTANTS",report["number_true_original_source_semantic_formula_deltas_independently_proven"],"/8")
    print("SOURCE_GIT_SHA_DISTINCT_MUTANTS",report["number_source_mutants_sha_different_than_base"],"/8")
    print("ORIGINAL_POSITIVE_SEMANTIC_EQUIVALENCE_CONTROLS",report["all_original_baseline_positive_equivalence_controls_dual_pass"])
if __name__=="__main__":
    main()
