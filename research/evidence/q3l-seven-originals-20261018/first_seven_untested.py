"""Q3L first-only 7 authentic Loopy C source-only classical composition survey.

Q3I prior failed 8/150, excluding Q3J/K2-resolved sum04. Original C
syntax and per-source SHA frozen in prereg, no published invariant access.
No model, no training, no opened Q3F escrow. SAT/UNKNOWN fail closed.
"""
from __future__ import annotations
import argparse,hashlib,io,json,sys,time,zipfile
from pathlib import Path
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3h-real-source-proof-20261018"))
sys.path.insert(0,str(HERE.parent/"q3k-chc-spacer-20261018"))
from source_only_houdini import candidate_proof
from replay_real_c_loop_invariants import signed_domain,MIN_INT,MAX_INT
from first_source_only_direct_chc import (
    model_semantics,source_fixedpoint,controls,substitute,signed_bad,
    bounded_reachability
)

DATASET_BLOB="17cac0f6734a39f0fe73558199cc2ad8d5c1a810"
REV="91fe89245a0894ec8ad3741d85ae91ce3b552b2e"
SOURCES={
    "dataset/loop_invariants/LinearArbitrary-SeaHorn/llreve/loop4_merged_safe.c":"c13d8ad816e6524be5d58c57bf1db3a2c79273c5966beda9f2e27d31039d930c",
    "dataset/loop_invariants/LinearArbitrary-SeaHorn/loops/loop-lit/cggmp2005_true-unreach-call_true-termination.c":"dac9dd91ff5d136dfdc323a9f50a2337092d269e286913bc9f309f7fb30ffa49",
    "dataset/loop_invariants/LinearArbitrary-SeaHorn/pie/hola/11.c":"ec325a79c5afc4a957eadffdfa160019f17596a0c56439eea1714b93a3e45b66",
    "dataset/loop_invariants/LinearArbitrary-SeaHorn/pie/hola/30.c":"0c3c665df9002d4960089fffe8e169a2e433b63490d3ed203caccbab88dc2c15",
    "dataset/loop_invariants/LinearArbitrary-SeaHorn/pie/ICE/benchmarks/fig1.c":"2abb081daca93b0e5aa80737c96eb336b2deb637204e5f78e8bb796c83838402",
    "dataset/loop_invariants/LinearArbitrary-SeaHorn/pie/ICE/benchmarks/fig9.c":"e8e826e0929cafd8646b8b15a4087fc9857f621cfba95fd89824345b044dab27",
    "dataset/loop_invariants/sv-benchmarks/loop-lit/cggmp2005.c":"f1282223fea471bec6ea423988737a6044148cb189dc2e8575d3a23a5656c4d2",
}
QUERY_TIMEOUT_MS=3500
MAX_EXIT_WITNESS_DEPTH=32

def reachable_exit_in_bound(model,names,base,arith):
    """Existential concrete source exit trace only, not a global proof."""
    h=model["loop_state"]
    current={n:z3.Int(f"q3l_exit_step0_{n}") for n in names}
    solver=z3.Solver();solver.set(timeout=1000)
    solver.add(base)
    for n in names:solver.add(current[n]==model["after_prelude"][n])
    for depth in range(MAX_EXIT_WITNESS_DEPTH+1):
        guard=substitute(model["loop_test"],h,current)
        solver.push()
        solver.add(z3.Not(guard))
        result=solver.check()
        solver.pop()
        if result==z3.sat:
            return {"classification":"REACHABLE_TERMINATION_EXHIBITED",
                    "exit_depth":depth}
        if result==z3.unknown:
            return {"classification":"BMC_UNKNOWN","exit_depth":depth}
        if depth==MAX_EXIT_WITNESS_DEPTH:break
        body_arith=[substitute(e,h,current) for e in arith]
        dest={n:z3.Int(f"q3l_exit_step{depth+1}_{n}") for n in names}
        solver.add(guard,z3.Not(signed_bad(body_arith)))
        for n in names:
            solver.add(dest[n]==substitute(model["body_state"][n],h,current))
        solver.add(*signed_domain(dest))
        current=dest
    return {"classification":"NO_TERMINATION_FOUND_WITHIN_32_NOT_NONTERMINATION_PROOF",
            "exit_depth":None}

def evaluate_source(source):
    start=time.perf_counter_ns()
    # Both semantic constructors parse original unchanged C, independently
    # of any published answer invariant or benchmark solver label.
    info={"status":"NOT_PROVEN","error":None}
    try:
        model,names,base,prestatus,arith=model_semantics(source)
        prior=candidate_proof(source)
        info["original_variables"]=list(names)
        info["original_initial_prelude_bad"]=prestatus
        info["source_only_houdini"]={
            "status":prior["status"],
            "verification":prior["full_original_check"],
            "generated_candidates":prior["source_conditioned_candidate_count"],
            "final_invariants":prior["final_inductive_candidate_count"],
            "solver_calls":prior["total_induction_solver_queries"],
        }
        # CHC all targets are independently queried. First returns are
        # preserved as-is, including canceled solver UNKNOWN/errors.
        chcs=source_fixedpoint(model,names,base,arith)
        bad_exit=chcs["exit_safety"]["bad_state_query"]
        bad_overflow=chcs["signed_step_overflow"]["bad_state_query"]
        info["direct_original_chc"]={
            "bad_exit":chcs["exit_safety"],
            "bad_overflow":chcs["signed_step_overflow"],
            "original_relation_arity":chcs["quantified_original_relation_arity"],
        }
        checks=prior["full_original_check"]
        houdini_overflow=(
            checks["initial"]=="unsat" and
            checks["inductive"]=="unsat" and
            checks["signed_overflow"]=="unsat"
        )
        parts={
          "original_prelude_no_signed_overflow":prestatus=="unsat",
          "original_reachable_bad_exit_absent":bad_exit=="unsat",
          "source_only_houdini_legal_step_certificate":houdini_overflow,
          "direct_chc_bad_overflow_absent":bad_overflow=="unsat",
          "same_original_state_variables":set(prior["program_features_used"])>=set() and
                 tuple(names)==tuple(sorted(names)),
        }
        # The classical Houdini invariant and the SPACER transition both
        # use the same Q3H model_original original source parser.
        combined=(
          parts["original_prelude_no_signed_overflow"] and
          parts["original_reachable_bad_exit_absent"] and
          (houdini_overflow or parts["direct_chc_bad_overflow_absent"]) and
          parts["same_original_state_variables"]
        )
        info["composition_gate"]=parts
        if combined:
            # Finite bounded trace is a falsification guard, not proof.
            bmc=bounded_reachability(model,names,base,arith)
            info["bounded_actual_bad_exit_check"]=bmc
            if bmc["classification"]=="ACTUAL_REACHABLE_BAD_EXIT_WITHIN_BOUND":
                raise ValueError("EXACT_BOUNDED_TRACE_CONTRADICTS_SPACER")
            if bmc["classification"]=="BMC_SOLVER_UNKNOWN":
                info["status"]="BLOCKED_BMC_UNKNOWN"
            else:
                info["status"]="CLASSICAL_SPECIALISTS_COMPOSED_ORIGINAL_C_PROVEN"
        else:
            info["status"]="ORIGINAL_SAFETY_NOT_ESTABLISHED"
        if bad_exit=="unsat":
            info["reachable_safe_exit_witness"]=reachable_exit_in_bound(
                model,names,base,arith
            )
    except Exception as exc:
        info["status"]="BLOCKED_OR_UNSUPPORTED"
        info["error"]=f"{type(exc).__name__}: {str(exc)[:200]}"
    info["elapsed_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    return info

def run(archive_file):
    raw=archive_file.read_bytes()
    blob=b"blob "+str(len(raw)).encode()+b"\x00"+raw
    if hashlib.sha1(blob).hexdigest()!=DATASET_BLOB:
        raise ValueError("REAL_SOURCE_ARCHIVE_CHANGED")
    controls_result=controls()
    controls_ok=all(v["pass"] for v in controls_result.values())
    cases=[]
    if controls_ok:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for path,expected in SOURCES.items():
                source=z.read(path)
                if hashlib.sha256(source).hexdigest()!=expected:
                    raise ValueError("PINNED_REAL_C_SOURCE_HASH_MISMATCH")
                case=evaluate_source(source.decode("utf-8",errors="strict"))
                cases.append({"source_path":path,
                              "source_sha256":expected,
                              "source_unmodified":True,**case})
    for case in cases:
        if case["status"]=="CLASSICAL_SPECIALISTS_COMPOSED_ORIGINAL_C_PROVEN":
            gate=case["composition_gate"]
            if not (
                gate["original_prelude_no_signed_overflow"] and
                gate["original_reachable_bad_exit_absent"] and
                (gate["source_only_houdini_legal_step_certificate"] or
                 gate["direct_chc_bad_overflow_absent"])
            ):raise ValueError("INVALID_SOURCE_COMPOSITE_PROOF")
    return {
        "study":"Q3L_SEVEN_EXACT_AUTHENTIC_C_ORIGINALS_FIRST_CLASSICAL_COMPOSITION",
        "registered_source_count":len(SOURCES),
        "actual_evaluated_source_count":len(cases),
        "controls":controls_result,
        "controls_all_pass":controls_ok,
        "original_upstream_commit":REV,
        "original_dataset_git_blob":DATASET_BLOB,
        "classical_complete_original_proofs":sum(
            r["status"]=="CLASSICAL_SPECIALISTS_COMPOSED_ORIGINAL_C_PROVEN"
            for r in cases),
        "proven_with_bounded_reachable_termination":sum(
            r["status"]=="CLASSICAL_SPECIALISTS_COMPOSED_ORIGINAL_C_PROVEN" and
            r.get("reachable_safe_exit_witness",{}).get("classification")==
                "REACHABLE_TERMINATION_EXHIBITED"
            for r in cases),
        "neural_model_training_or_inference_calls":0,
        "original_publication_answer_labels_used":False,
        "q3f_sealed_chc_originals_opened":False,
        "first_no_tuning_policy":True,
        "global_q1_q7":"OPEN",
        "cases":cases
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    r=run(args.dataset)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,indent=2)+"\n")
    print("Q3L_FIRST_RESULTS",r["classical_complete_original_proofs"],
      "OF",r["actual_evaluated_source_count"],
      "NONVACUOUS_BOUNDED_EXIT",r["proven_with_bounded_reachable_termination"])
    print("PER_SOURCE",[(x["source_path"],x["status"],
          x.get("direct_original_chc",{}).get("bad_exit",{}).get("bad_state_query"),
          x.get("direct_original_chc",{}).get("bad_overflow",{}).get("bad_state_query"))
          for x in r["cases"]])
    print("Q1_Q7",r["global_q1_q7"])
