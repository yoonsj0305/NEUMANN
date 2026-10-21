"""Real 26-source no-gold proof broker. POSTHOC, not learned NEUMANN Q3.

Every original SMT-LIB source byte authenticated to previously frozen Git blob.
Code chooses source-based route, never filename or source :status or gold:
  * 3-cubes: mod9 complete unbounded UNSAT or exact CRT15561 bounded SAT
  * 2x2 positive pair: equal power sums source injectivity => UNSAT
  * 3x3 original full magic: exact AP theorem premises =>
    published Darmon-Merel conditional UNSAT (NOT self-contained theorem)
  * else UNKNOWN (never false SAT/UNSAT).
Original independent Z3 and cvc5 on all SAT positives and structure theorem
bridges. Strong classical specialist with SAME math can match broker exactly.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import z3
from research.evidence.g0_first_random_hash_12_20261021.first_original_twelve_same_cpu_unbounded_math_and_sat_vs_direct import hybrid_source
from research.evidence.q3_power_feature_20261021.first_ten_unchanged_power_magic_original_unbounded_unsat import (
    original_exact_geometry,independent_necessary_linear_certificate,
    original_positive,original_distinct
)
from research.evidence.q3_original_3x3_rank_20261021.exact_true_original_magic_power_rowspace_dual import (
    parse_true_source_linear_skeleton
)
from research.evidence.q3_published_3power_AP_20261021.five_original_source_to_Darmon_Merel_AP_theorem import (
    independent_entailment,EXTERNAL_LEMMA,EXTERNAL_CITATION
)
import subprocess,sys
def original_semantics_smt2(assertions):
    symbols={}
    stack=list(assertions)
    while stack:
        term=stack.pop()
        if term.num_args()==0 and term.decl().kind()==z3.Z3_OP_UNINTERPRETED:
            if term.sort().kind()!=z3.Z3_INT_SORT:
                raise RuntimeError("ORIGINAL_SOURCE_NONINTEGER_SYMBOL_UNEXPECTED")
            symbols[str(term)]=True
        else:
            stack.extend(term.children())
    lines=["(set-logic QF_NIA)"]
    lines.extend("(declare-fun "+name+" () Int)" for name in sorted(symbols))
    lines.extend("(assert "+a.sexpr()+")" for a in assertions)
    lines.extend(["(check-sat)","(exit)"])
    return "\n".join(lines)+"\n"

def status_run(engine,payload):
    start=time.perf_counter_ns()
    if engine=="z3":
        src="import z3,sys; p=z3.Solver();p.set(timeout=3000);p.from_string(sys.stdin.read());print(p.check())"
        cmd=[sys.executable,"-c",src]
    elif engine=="cvc5":
        cmd=["cvc5","--lang=smt2","--tlimit-per=3000","-"]
    else:raise ValueError("UNSUPPORTED_RAW_DIRECT_BACKEND")
    label="UNKNOWN";error=None
    try:
        proc=subprocess.run(cmd,input=payload,capture_output=True,text=True,timeout=4.5)
        vals=[q.strip().upper() for q in proc.stdout.splitlines()
              if q.strip().lower() in ("sat","unsat","unknown")]
        if proc.returncode==0 and vals:label=vals[0]
        elif proc.returncode!=0:error="NONZERO_EXIT_"+str(proc.returncode)+":"+proc.stderr[:180]
    except subprocess.TimeoutExpired:
        label="UNKNOWN_HARD_OS_CAP"
    except Exception as e:
        label="UNKNOWN_BACKEND_ERROR"
        error=type(e).__name__+":"+str(e)[:180]
    return {"engine":engine,"source_status":label,
            "whole_raw_source_backend_wall_ms":(time.perf_counter_ns()-start)/1e6,
            "hard_OS_cap_sec":4.5,"error":error}

from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import git_blob_sha1,sha256
from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import structural_source

UPSTREAM="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
CONTRACT_COMMIT="2da789feb5ea301b1b2ea9953e694639b0eea295"

def infer_without_filename(raw):
    start=time.perf_counter_ns()
    rec={"route":"UNKNOWN","status":"UNKNOWN","authority":"NONE",
         "learned_model_forwards":0,"source_gold_labels_input":False,
         "source_filename_routing":False,"external_theorem_premise_used":False}
    solver=z3.Solver();solver.from_string(raw.decode("utf-8"))
    actual_assertions=list(solver.assertions())
    rec["true_original_assertion_count"]=len(actual_assertions)

    # Test original syntactic ONE 3-cube equation. A failing parse is
    # a ROUTE MISFIT, never evidence the underlying source is unsolvable.
    try:
        structural_source(raw)
        syntactic_3cubes=True
    except (RuntimeError,ValueError,AssertionError,z3.Z3Exception,KeyError,TypeError):
        syntactic_3cubes=False

    if syntactic_3cubes:
        outcome=hybrid_source(raw,"original_source_only")
        rec["three_cube_exact_original_independent_evidence"]=outcome
        rec["route"]="ORIGINAL_3CUBES_MOD9_OR_CRT15561"
        if outcome["class"]=="SAT" and outcome["original_independent_Z3_cvc5_source_sat"]:
            rec["status"]="SAT"
            rec["authority"]="DUAL_ORIGINAL_RAW_SMT2_Z3_CVC5_GROUNDED"
        elif outcome["class"]=="UNSAT" and outcome["mod9_theorem_pass"]:
            rec["status"]="UNSAT"
            rec["authority"]="EXACT_SOURCE_ARITHMETIC_MOD9_FINITE_DUAL_THEOREM"
        else:
            rec["status"]="UNKNOWN"
        rec["all_attempted_proof_wall_ms"]=(time.perf_counter_ns()-start)/1e6
        return rec

    # A generic 2-term source equation algebraic shared-power-cancellation
    # only passes if all exact native original positivity/distinct guards exist.
    geometry=original_exact_geometry(actual_assertions)
    if geometry is not None:
        proof=independent_necessary_linear_certificate(geometry)
        rec["two_term_true_original_geometry"]=geometry
        rec["independent_native_QFLIA_Z3_cvc5"]=proof
        rec["route"]="ORIGINAL_POWER_INJECTIVITY_2TERM"
        if proof["both_independent_unbounded_necessary_condition_UNSAT"]:
            rec["status"]="UNSAT"
            rec["authority"]="ORIGINAL_SOURCE_EQUIVALENCE_AND_POSITIVE_POWER_MONOTONICITY"
        rec["all_attempted_proof_wall_ms"]=(time.perf_counter_ns()-start)/1e6
        return rec

    # General true 3x3 source program, NO use of original filename or
    # expected prior status. Exact native source AST and mathematical form.
    rec["route"]="ORIGINAL_GENERAL_MAGIC3_POWER_AP_CHECK"
    try:
        spec,rows=parse_true_source_linear_skeleton(solver)
        kvalues=spec["native_power_exponents"]
        rec["source_true_power_k"]=kvalues
        if len(kvalues)!=1 or int(kvalues[0])<3 or spec["matched_source_sum_ast_count"]!=8:
            rec["status"]="UNKNOWN"
            rec["route"]="ABSTAIN_NOT_FULL_MAGIC_OR_POWER_BELOW3"
        else:
            degree=int(kvalues[0])
            native_names=["x_0_1","x_1_1","x_2_1"]
            positive=[original_positive(actual_assertions,name) for name in native_names]
            distinct=[original_distinct(actual_assertions,a,b) for a,b in [
                ("x_0_1","x_1_1"),("x_0_1","x_2_1"),("x_1_1","x_2_1")]]
            guards=all(x is not None for x in positive+distinct)
            rec["original_native_all_necessary_guards_valid"]=guards
            if guards:
                proof=independent_entailment(rows,spec["columns"],degree)
                rec["native_true_original_source_to_AP_Z3_cvc5"]=proof
                if proof["full_original_sums_entail_three_power_AP_DUAL"]:
                    rec["status"]="UNSAT_CONDITIONAL_EXTERNAL_PUBLISHED_THEOREM"
                    rec["authority"]="SOURCE_PREMISES_DUAL_PROVED_EXTERNAL_NUMBER_THEORY_TRUST"
                    rec["external_theorem_premise_used"]=True
                    rec["external_number_theory_theorem"]=EXTERNAL_LEMMA
                    rec["external_published_reference"]=EXTERNAL_CITATION
    except (ValueError,RuntimeError,AssertionError,z3.Z3Exception,KeyError,TypeError) as e:
        rec["route"]="ABSTAIN_UNSUPPORTED_FULL_MAGIC_FORM"
        rec["structural_reason"]=type(e).__name__+":"+str(e)[:170]
    rec["all_attempted_proof_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return rec

def one_original(root,item,cohort):
    start=time.perf_counter_ns()
    out={"source":item["path"],"cohort":cohort,"original_expected_git_blob":item["sha1_git_blob"],
         "source_Git_blob_authenticated":False,"status":"ABSTAIN_NO_SOURCE"}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("UNMODIFIED_ORIGINAL_SOURCE_GIT_SHA_OR_BYTES_CHANGED")
        out["source_Git_blob_authenticated"]=True
        out["actual_original_SHA256"]=sha256(raw)
        route=infer_without_filename(raw)
        out["source_chosen_gold_free_math_dispatch"]=route
        out["verified_original_result"]=route["status"]
        out["external_theorem_off_ablation_result"]=(
            "UNKNOWN" if route["external_theorem_premise_used"] else route["status"])
        before=time.perf_counter_ns()
        # Matched raw generic Direct is exactly original AST, no answer hints.
        parser=z3.Solver();parser.from_string(raw.decode("utf-8"))
        native=original_semantics_smt2(list(parser.assertions()))
        out["matched_true_full_original_raw_direct"]={
            engine:status_run(engine,native) for engine in ("z3","cvc5")}
        out["original_direct_complete_source_and_OS_caps_ms"]=(time.perf_counter_ns()-before)/1e6
        rawstatuses=set(v["source_status"] for v in out["matched_true_full_original_raw_direct"].values())
        if "SAT" in rawstatuses and "UNSAT" in rawstatuses:
            out["status"]="FAIL_RAW_DIRECT_TWO_REAL_SOLVERS_CONTRADICT"
        elif route["status"] in ("UNSAT","UNSAT_CONDITIONAL_EXTERNAL_PUBLISHED_THEOREM") and "SAT" in rawstatuses:
            out["status"]="FAIL_REAL_ORIGINAL_GOLD_FREE_PROOF_CONTRADICTS_SAT"
        elif route["status"]=="SAT" and "UNSAT" in rawstatuses:
            out["status"]="FAIL_REAL_ORIGINAL_GOLD_FREE_PROOF_CONTRADICTS_UNSAT"
        else:
            out["status"]="VALID_TRUE_ORIGINAL_SOURCE_CHECK"
        out["raw_direct_union_original_solved"]=bool(rawstatuses &{"SAT","UNSAT"})
        out["gold_free_math_broker_certified"]=route["status"] in (
            "SAT","UNSAT","UNSAT_CONDITIONAL_EXTERNAL_PUBLISHED_THEOREM")
        out["gold_free_math_broker_solved_internal_only"]=route["status"] in ("SAT","UNSAT")
        out["gold_free_math_broker_added_over_RAW_GENERIC_direct"]=(
            out["gold_free_math_broker_certified"] and not out["raw_direct_union_original_solved"])
        out["ablation_external_theorem_off_loses_accepted_classification"]=route["external_theorem_premise_used"]
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_OR_PROOF_BROKER_EXCEPTION"
        out["error"]=type(e).__name__+":"+str(e)[:440]
    out["whole_actual_original_hybrid_plus_raw_direct_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("Q3_TRUE_SOURCE_BROKER_26",out["source"].split("/")[-1],
          "MATHEMATICAL",out.get("verified_original_result"),
          "RAW_DIRECT",[x["source_status"] for x in out.get("matched_true_full_original_raw_direct",{}).values()],
          "VALID",out["status"],"ERR",out.get("error"),flush=True)
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--manifest-four",type=Path,required=True)
    p.add_argument("--manifest-twelve",type=Path,required=True)
    p.add_argument("--manifest-ten",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    f=json.loads(a.manifest_four.read_text())
    t=json.loads(a.manifest_twelve.read_text())
    m=json.loads(a.manifest_ten.read_text())
    c=json.loads(a.contract.read_text())
    if c["schema"]!="neumann.q3.posthoc_integrated_no_oracle_math_theorem_broker_26.v1":
        raise RuntimeError("SOURCE_ORIGINAL_GOLD_FREE_BROKER_CONTRACT_CHANGED")
    if c["source_count"]!=26 or [len(f["targets"]),len(t["targets"]),
         len(m["five_original_2x2_targets"]),len(m["five_original_3x3_controls"])]!=[4,12,5,5]:
        raise RuntimeError("IMMUTABLE_TRUE_SOURCE_26_MATH_COHORT_CHANGED")
    tasks=[(q,"PREOPENED_PREVIOUS_PR349_THREE_CUBES") for q in f["targets"]]
    tasks += [(q,"PREOPENED_PREVIOUS_PR350_HASHED") for q in t["targets"]]
    tasks += [(q,"PREOPENED_PREVIOUS_PR354_MAGIC2") for q in m["five_original_2x2_targets"]]
    tasks += [(q,"PREOPENED_PREVIOUS_PR354_MAGIC3") for q in m["five_original_3x3_controls"]]
    if len({v["sha1_git_blob"] for v,_ in tasks})!=26:
        raise RuntimeError("TRUE_ORIGINAL_26_DUPLICATE_SOURCE_BLOB")
    rows=[one_original(a.root,q,split) for q,split in tasks]
    mathinternal=sum(q.get("gold_free_math_broker_solved_internal_only",False) for q in rows)
    literature=sum(q.get("ablation_external_theorem_off_loses_accepted_classification",False) for q in rows)
    raw=sum(q.get("raw_direct_union_original_solved",False) for q in rows)
    added=sum(q.get("gold_free_math_broker_added_over_RAW_GENERIC_direct",False) for q in rows)
    result={
       "schema":"neumann.q3.true_authentic_26_originals_three_classical_routes_published_theorem_ablation.v1",
       "posthoc_ALL_previous_source_bodies_opened":True,
       "preregistered_integration_contract_commit":CONTRACT_COMMIT,
       "true_original_26_source_count":len(rows),
       "actual_original_source_git_sha_authenticated_count":sum(q["source_Git_blob_authenticated"] for q in rows),
       "genuine_original_internal_machine_proved_sat_or_unsat":mathinternal,
       "genuine_original_EXTERNAL_PUBLISHED_THEOREM_conditional_unsat":literature,
       "integrated_original_classified_total_internal_plus_trusted_literature":mathinternal+literature,
       "exact_math_broker_NO_EXTERNAL_THEOREM_ablation_solved":mathinternal,
       "matched_raw_original_strong_generic_Z3_OR_cvc5_solved_count":raw,
       "extra_true_original_classification_vs_RAW_GENERIC_without_same_math_library":added,
       "accepted_comparator_equal_authority_specialist_can_copy_exact_same_algorithm":True,
       "learned_unique_structure_bonus_vs_equal_authority_classical":0,
       "no_neural_gradient_updates":True,
       "no_relabeling_original_first_unseen_cohorts_posthoc":True,
       "any_known_true_source_misclassification_or_authentication_failure":sum(q["status"]!="VALID_TRUE_ORIGINAL_SOURCE_CHECK" for q in rows),
       "external_published_number_theory_theorem_NOT_independently_formally_proved":True,
       "complete_original_checkers_all_OS_process_capped":True,
       "same_source_originals":rows,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN"
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("Q3_INTEGRATED_TRUE_ORIGINAL_26_AUTHENTIC",result["actual_original_source_git_sha_authenticated_count"],"/26")
    print("Q3_INTEGRATED_INTERNAL_INDEPENDENT_ORIGINAL_SOLVED",mathinternal)
    print("Q3_INTEGRATED_ADDITIONAL_CONDITIONAL_PUBLISHED_THEOREM_UNSAT",literature)
    print("Q3_INTEGRATED_TOTAL_CLASSIFIED",mathinternal+literature,"/26")
    print("Q3_INTEGRATED_MATCHED_GENERIC_RAW_DIRECT_SOLVED",raw,"/26")
    print("Q3_INTEGRATED_EXTRA_OVER_RAW_GENERIC_WITHOUT_MATH_LIBRARY",added)
    print("Q3_INTEGRATED_THM_OFF_ABLATION_LOSES",literature)
    print("Q3_INTEGRATED_EQUAL_AUTHORITY_SPECIALIST_NEUMANN_UNIQUE_ADVANTAGE",0)
    print("Q3_INTEGRATED_GLOBAL_Q3_Q4",result["global_Q3"],result["global_Q4"])
if __name__=="__main__":
    main()
