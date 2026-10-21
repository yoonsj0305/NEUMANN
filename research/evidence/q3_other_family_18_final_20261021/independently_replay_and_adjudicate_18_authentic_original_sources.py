"""Single CI rerun of FOUR independent authentic original-source programs.

Immutable first original strong Z3/cvc5/NRA ceiling versus after-first-look:
  Strassen linear,h ard SAT + 1971 Winograd published theorem conditional
  cut-out-2 all-real universally quantified UNSAT by source countermodel
  cut-out-1 all-real existential SAT by exact 39/39 rational witness.

Only original FULL native SMT-LIB source may count; all source SHA bound
to original first-before-body Git-metadata manifest. Every solved/failed
original retained; no accidental promotion of classical knowledge to
learned Q3 or full cost 10x.
"""
from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path

UPSTREAM="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
FROZEN_FIRST_18="5412a4fb16c96694ab2bf629c34f6e41737f7a7f"
INTEGRATION_BEFORE_RUN="9764a50fddb2ddf75fdfe98afa1205f952db6233"

RUNNERS=[
("EXPERT_DIRECT","research/evidence/q3_fresh_real_nra_20261021/first_18_new_originals_same_cpu_strong_classical_expert_screen.py"),
("STRASSEN_SOURCE_TENSOR","research/evidence/q3_strassen_exact_tensor_20261021/actual_original_strassen_tensor_exact_source_checker.py"),
("CIRCLE2_QUANTIFIED_COUNTERMODEL","research/evidence/q3_circles_forall_20261021/genuine_circle2_source_forall_counterexample_dual.py"),
("CIRCLE1_EXACT_RATIONAL_SAT","research/evidence/q3_circles_sat_witness_20261021/original_circle1_39conjuncts_exact_rational_z3_cvc5.py"),
]
TENSOR_CONTRACT="research/evidence/q3_strassen_exact_tensor_20261021/POST_FIRST_OPEN_STRASSEN_SOURCE_EXACT_TENSOR_AND_EXTERNAL_RANK7_CONTRACT.json"
CIRCLE2_CONTRACT="research/evidence/q3_circles_forall_20261021/POSTHOC_ORIGINAL_CIRCLE2_EXACT_COUNTERMODEL_CONTRACT.json"
CIRCLE1_CONTRACT="research/evidence/q3_circles_sat_witness_20261021/BEFORE_DUAL_SAT_CHECK_REAL_ORIGINAL_CIRCLE1_WITNESS.json"
STRASSEN_NAMES=("strassen-linear.smt2","strassen-hard.smt2","strassen-impossible.smt2")

def run_script(name,script,root,source_manifest,outs):
    output=outs/(name.lower()+".json")
    cmd=[sys.executable,script,"--root",str(root),"--freeze",str(source_manifest)]
    if name=="STRASSEN_SOURCE_TENSOR":cmd+=["--contract",TENSOR_CONTRACT]
    if name=="CIRCLE2_QUANTIFIED_COUNTERMODEL":cmd+=["--contract",CIRCLE2_CONTRACT]
    if name=="CIRCLE1_EXACT_RATIONAL_SAT":cmd+=["--contract",CIRCLE1_CONTRACT]
    cmd+=["--out",str(output)]
    start=time.perf_counter_ns()
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=720)
    wall=(time.perf_counter_ns()-start)/1e6
    (outs/(name.lower()+".log")).write_text(p.stdout+"\nSTDERR:\n"+p.stderr)
    print("Q3_REAL18_INTEGRATION_STAGE",name,"EXIT",p.returncode,
          "ELAPSED_MS",round(wall,3),flush=True)
    if p.returncode!=0 or not output.exists():
        raise RuntimeError("INDEPENDENT_ORIGINAL_SOURCE_PROOF_STAGE_FAILED_"+name+":"+
                           p.stderr[-1200:])
    return json.loads(output.read_text()),wall

def full_truth_for_solver_receipts(row):
    answers={x["status"] for x in row["source_solver_execution_receipts"]}
    if "SAT" in answers and "UNSAT" in answers:
        raise RuntimeError("ORIGINAL_SOURCE_DIRECT_SOLVER_CONTRADICTION")
    allowed=answers &{"SAT","UNSAT"}
    return next(iter(allowed)) if allowed else "UNKNOWN"

def combined_audit(orig,tensor,circle2,circle1):
    assert orig["authenticated_native_original_source_sha_count"]==18
    assert tensor["source_original_all_three_authentic"]==3
    assert tensor["source_linear_complete_original_SAT_algebraic"]
    assert tensor["source_hard_complete_original_SAT_algebraic"]
    for row in tensor["original_three"][:2]:
        assert row["independent_genuine_original_Z3_cvc5_universal_witness"][
            "both_independent_Z3_cvc5_prove_ORIGINAL_FORALL_TRUE"]
        assert row["original_source_full_real_quantified_identity_coefficient_proof"][
            "all_actual_original_output_input_basis_coefficients_exact"]==64
    assert tensor["source_impossible_classification_external_rank7_theorem_only"]
    assert tensor["original_three"][2]["original_native_rank_six_external_theorem_premises"][
        "actual_original_seventh_weight_exactly_literal_zero"]
    assert circle2["actual_original_source_evidence"]["original_forall_actually_refuted"]
    assert circle2["actual_original_source_evidence"]["original_full_native_SMT2_dual_Z3_cvc5"][
        "both_Z3_and_cvc5_full_source_ground_counterexample_SAT"]
    assert circle1["original_full_true_SMT2_dual_Z3_cvc5_SAT"]
    assert circle1["original_exact_Fraction_true_all_39_native_inequalities"]
    assert circle1["evidence"]["negative_control_actual_original_SMT2"][
        "both_authentic_independent_UNSAT"]
    tensor_map={}
    for source in tensor["original_three"]:
        suffix=source["source_identity"]["source"].split("/")[-1]
        tensor_map[suffix]=source
    actual=[]
    for source in orig["all_exact_original_sources"]:
        name=source["path"].split("/")[-1]
        raw_state=full_truth_for_solver_receipts(source)
        state=raw_state
        origin="RAW_GENERIC_ACTUAL_ORIGINAL" if raw_state in ("SAT","UNSAT") else "UNKNOWN"
        trusted_external=False
        twin=None
        if name in tensor_map:
            witness=tensor_map[name]
            assert source["original_Git_blob_authenticated"]
            assert source["true_original_source_sha256"]==witness["source_identity"]["source_sha256"]
            if name in STRASSEN_NAMES[:2]:
                twin="SAT"
                if raw_state not in ("UNKNOWN","SAT"):
                    raise RuntimeError("STRASSEN_FULL_WITNESS_CONFLICTS_STRONG_DIRECT")
                if raw_state=="UNKNOWN":
                    state=twin;origin="AUTHENTIC_ORIGINAL_EXACT_TENSOR_DUAL_QUANTIFIER"
            elif name==STRASSEN_NAMES[2]:
                twin="UNSAT"
                trusted_external=True
                if raw_state not in ("UNKNOWN","UNSAT"):
                    raise RuntimeError("PUBLISHED_WINOGRAD_RANK6_BRIDGE_CONFLICTS_SOURCE")
                if raw_state=="UNKNOWN":
                    state="UNSAT_CONDITIONAL_WINOGRAD_1971_RANK7"
                    origin="REAL_ORIGINAL_NATIVE_SOURCE_BRIDGE_PLUS_EXTERNAL_THEOREM"
        elif name=="cut-out-2.smt2":
            witness=circle2["actual_original_source_evidence"]
            assert source["true_original_source_sha256"]==witness["real_source_SHA256"]
            twin="UNSAT"
            if raw_state not in ("UNKNOWN","UNSAT"):
                raise RuntimeError("CIRCLE_FORALL_COUNTEREXAMPLE_CONFLICTS_DIRECT")
            if raw_state=="UNKNOWN":
                state=twin;origin="TRUE_ORIGINAL_ALL_12_REAL_UNIVERSAL_COUNTERMODEL_Z3_CVC5"
        elif name=="cut-out-1.smt2":
            witness=circle1["evidence"]
            assert source["true_original_source_sha256"]==witness["original_source_SHA256"]
            twin="SAT"
            if raw_state not in ("UNKNOWN","SAT"):
                raise RuntimeError("CIRCLE_REAL_39_CLAUSE_WITNESS_CONFLICTS_DIRECT")
            if raw_state=="UNKNOWN":
                state=twin;origin="TRUE_ORIGINAL_EXACT_FRACTION_39_CONJUNCTS_Z3_CVC5"
        if state=="UNKNOWN":
            raise RuntimeError("UNRESOLVED_TRUE_ORIGINAL_REMAINED_"+name)
        actual.append({
            "source":source["path"],"registered_actual_SHA":source["registered_original_git_blob"],
            "source_SHA_authenticated":source["original_Git_blob_authenticated"],
            "direct_original_classical":raw_state,
            "admitted_true_original_disposition":state,
            "source_mathematical_proof_origin":origin,
            "trusted_external_math_theorem_required":trusted_external,
            "same_as_independent_late_mathematical_witness":twin,
        })
        print("Q3_REAL18_COMPLETE_ORIGINAL_PROOF",name,"ORIGINAL",state,
              "ORIGIN",origin,flush=True)
    direct=sum(q["direct_original_classical"]!="UNKNOWN" for q in actual)
    internal=sum(q["admitted_true_original_disposition"] in ("SAT","UNSAT") for q in actual)
    external=sum(q["trusted_external_math_theorem_required"] for q in actual)
    out={
      "schema":"neumann.q3.complete_18_genuine_original_three_problem_families_provenance_and_ablation.v1",
      "source_18_git_blobs_locked_pre_source_content_commit":FROZEN_FIRST_18,
      "integration_protocol_frozen_before_replay_commit":INTEGRATION_BEFORE_RUN,
      "original_first_source_run_historically_SHA_frozen_before_body_read_but_this_is_POSTHOC":True,
      "all_18_real_original_sources_authenticated":sum(q["source_SHA_authenticated"] for q in actual),
      "full_original_truth_evidence_18_of_18":len(actual),
      "real_originals_raw_strong_generic_Z3_cvc5_specialized_solved":direct,
      "extra_original_machine_or_exact_algebra_proved":internal-direct,
      "real_originals_internal_independent_math_or_solver_classified":internal,
      "real_originals_published_external_mathematical_lower_bound_CONDITIONAL":external,
      "every_original_classified_internal_or_external":internal+external,
      "all_external_theorem_cases_NOT_machine_proved_from_first_principles":True,
      "NOT_a_model_trained_or_learned_Q3_unique_result":True,
      "full_external_literature_search_and_human_numerical_tuning_cost_not_instrumented":True,
      "equal_rights_strongest_classical_expert_may_use_identical_math":True,
      "Q3_Q4_Q5_GLOBAL":"OPEN",
      "all_source_originals":actual
    }
    return out

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,required=True)
    a.add_argument("--freeze",type=Path,required=True)
    a.add_argument("--contract",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    p=a.parse_args()
    contract=json.loads(p.contract.read_text())
    if contract["schema"]!="neumann.q3.after_original_18_first_open_complete_provenance_union.v1":
        raise RuntimeError("INTEGRATED_SOURCE_PROVENANCE_CONTRACT_CHANGED")
    if contract["global_Q3"]!=contract["global_Q4"] or contract["global_Q3"]!="OPEN":
        raise RuntimeError("MISREPORTED_GLOBAL_Q3_CLOSURE")
    outs=Path("/tmp/NEUMANN_true_original18_integrated_replay")
    outs.mkdir(parents=True,exist_ok=True)
    results=[];costs={}
    for name,script in RUNNERS:
        data,cost=run_script(name,script,p.root,p.freeze,outs)
        results.append(data);costs[name]=cost
    record=combined_audit(*results)
    record["complete_all_four_source_replay_python_wall_ms"]=costs
    record["full_replay_no_dependency_install_wall_ms"]=sum(costs.values())
    p.out.parent.mkdir(parents=True,exist_ok=True)
    p.out.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("Q3_EIGHTEEN_GENUINE_ORIGINAL_GIT_AUTHENTIC",record["all_18_real_original_sources_authenticated"],"/18")
    print("Q3_EIGHTEEN_RAW_STRONG_DIRECT",record["real_originals_raw_strong_generic_Z3_cvc5_specialized_solved"],"/18")
    print("Q3_EIGHTEEN_ADDITIONAL_INTERNAL_CERTIFIED",record["extra_original_machine_or_exact_algebra_proved"])
    print("Q3_EIGHTEEN_EXTERNAL_PUBLISHED_MATH_CONDITIONAL",record["real_originals_published_external_mathematical_lower_bound_CONDITIONAL"])
    print("Q3_EIGHTEEN_TOTAL_CLASSIFIED",record["every_original_classified_internal_or_external"],"/18")
    print("Q3_EIGHTEEN_GLOBAL_Q3_Q4_Q5",record["Q3_Q4_Q5_GLOBAL"])
if __name__=="__main__":
    main()
