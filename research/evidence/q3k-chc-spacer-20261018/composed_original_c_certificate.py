"""Q3K-2: complete original C signed-safe reachability proof by composition.

Runs source-only Q3J polynomial Houdini base/step/no-overflow and independent
Q3K SPACER bad-exit proof on THE SAME UNCHANGED C program, with separate
verification obligations and controls. Any SAT/UNKNOWN or mismatch fails closed.
Not an AI learner; Q1-Q7 OPEN.
"""
from __future__ import annotations
import argparse,hashlib,io,json,sys,time,zipfile
from pathlib import Path
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3j-polynomial-20261018"))
from source_only_quadratic import (
    synthesize,SOURCE as ORIGINAL,EXPECTED_SHA as ORIGINAL_SHA,
    EXPECTED_BLOB as PINNED_BLOB
)
from first_source_only_direct_chc import model_semantics,source_fixedpoint,controls,bounded_reachability

UPSTREAM="91fe89245a0894ec8ad3741d85ae91ce3b552b2e"

def source_bytes(dataset):
    raw=dataset.read_bytes()
    ident=b"blob "+str(len(raw)).encode()+bytes([0])+raw
    if hashlib.sha1(ident).hexdigest()!=PINNED_BLOB:
        raise ValueError("SOURCE_ARCHIVE_PIN_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        original=z.read(ORIGINAL)
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("UNMODIFIED_ORIGINAL_IDENTITY_MISMATCH")
    return original

def run(dataset):
    original=source_bytes(dataset)
    code=original.decode("utf-8",errors="strict")
    t0=time.perf_counter_ns()
    comparison={
        "experiment":"Q3K2_CLASSICAL_COMPOSITION_FIXED_SOURCE",
        "exact_original_path":ORIGINAL,
        "exact_original_sha256":ORIGINAL_SHA,
        "pinned_original_corpus_git_blob":PINNED_BLOB,
        "pinned_upstream_commit":UPSTREAM,
        "original_C_unchanged":True,
        "original_published_invariant_read":False,
        "q3f_escrow_chc_target_source_read":False,
        "learned_model_calls":0,
        "human_target_invariant_inserted":False,
        "global_q1_q7":"OPEN",
        "first_original_q3j_stays_whole_source":"NOT_PROVEN",
        "first_original_q3k_stays_whole_source":"UNKNOWN",
    }
    validation=controls()
    comparison["three_independent_control_verdicts"]=validation
    comparison["three_controls_pass"]=all(row["pass"] for row in validation.values())
    if not comparison["three_controls_pass"]:
        comparison["status"]="BLOCKED_CONTROL_VERDICT"
        return comparison
    try:
        # One new fresh Q3J regeneration. It is legitimate to combine exactly
        # its init/step/no-overflow lemmas, not its SAT exit obligation.
        q3j=synthesize(code)
        comparison["source_only_polynomial_induction"]={
            "source_state_names":q3j["source_variables"],
            "original_checks":q3j["full_original"],
            "number_polynomial_candidates":q3j["polynomial_candidate_count"],
            "number_polynomial_facts_retained":q3j["final_quadratic_candidates"],
            "candidate_solver_queries":q3j["solver_queries"],
            "source_only_no_answer_labels":q3j["published_invariant_used"] is False
        }
        # Independently reconstruct the exact same original C semantics from
        # original text, not from Q3J candidate formulas.
        m,names,base,prestatus,arith=model_semantics(code)
        q3k=source_fixedpoint(m,names,base,arith,requested=("exit_safety",))
        direct=q3k["exit_safety"]
        comparison["source_only_direct_reachability"]={
            "source_state_names":list(names),
            "source_initialization_overflow":prestatus,
            "reachable_original_bad_exit":direct["bad_state_query"],
            "fixedpoint_exit_query_reason":direct["reason"],
            "fixedpoint_exit_query_ms":direct["wall_ms"],
            "fixedpoint_engine":"SPACER",
            "overflow_timeout_from_first_study_preserved":True
        }
        # Independent bounded reachability acts as a falsification control,
        # never as the global proof on its own.
        bmc=bounded_reachability(m,names,base,arith)
        comparison["bounded_trace_negative_check"]=bmc
        a=q3j["full_original"]
        exact_original_match=tuple(q3j["source_variables"])==tuple(names)
        comparison["cross_method_original_state_signature_equal"]=exact_original_match
        parts={
          "q3j_original_init_induction":a["init"]=="unsat" and a["inductive"]=="unsat",
          "q3j_all_original_step_signed_arithmetic":a["signed_overflow"]=="unsat",
          "q3k_original_prelude_signed_arithmetic":prestatus=="unsat",
          "q3k_original_reachable_unsafe_exit_absence":direct["bad_state_query"]=="unsat",
          "original_same_typed_state_signature":exact_original_match,
          "source_only_zero_hints":q3j["published_invariant_used"] is False,
          "q3j_safety_mutation_controls":a["false_goal"]=="sat" and a["empty_invariant"]=="sat",
          "three_control_programs_valid":comparison["three_controls_pass"],
          "no_bmc_actual_counterexample":bmc["classification"]!="ACTUAL_REACHABLE_BAD_EXIT_WITHIN_BOUND",
        }
        comparison["composition_lemma_contract"]=parts
        comparison["all_components_passing"]=all(parts.values())
        comparison["status"]=(
            "ONE_AUTHENTIC_ORIGINAL_C_SAFETY_PROVEN_BY_CLASSICAL_COMPOSITION"
            if all(parts.values()) else
            "NOT_PROVEN_SOURCE_COMPONENTS_DISAGREE_OR_INCOMPLETE"
        )
    except Exception as e:
        comparison["status"]="BLOCKED_VERIFIER_OR_ORIGINAL_UNSUPPORTED"
        comparison["error"]=f"{type(e).__name__}: {str(e)[:350]}"
    comparison["composition_total_wall_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
    comparison["scientific_boundary"]=(
        "Proof is restricted to Q3H original C single-integer-loop semantic subset "
        "with signed 32-bit obligations. Both methods classical and share Z3 backend; "
        "neural Q3/Q4/Q7 all remain OPEN."
    )
    return comparison

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=run(args.dataset)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3K2_COMPOSITION_ACTUAL_ORIGINAL",result["status"])
    print("Q3K2_CONDITIONS",result.get("composition_lemma_contract"))
    print("Q3K2_SPACER",result.get("source_only_direct_reachability"))
    print("Q3K2_CLASSICAL_INDUCTION",result.get("source_only_polynomial_induction"))
    print("Q1_Q7",result["global_q1_q7"])

if __name__=="__main__":main()
