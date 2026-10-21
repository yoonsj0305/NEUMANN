"""Posthoc, FULL original-source proof search on the sole source unsolved in
PR421's automatic exact proof-first classical portfolio: Code2Inv 1.c.sl.

No manually supplied invariant, golden solution, source variable names, or
nonlinear hand-derived coefficients. A fixed 2-slot grammar enumerates all
unary/bivariate small integer linear inequalities with ±1 coefficients
and constants -1,0,1,2; ORIGINAL native Pre+Trans inductive Houdini
deletes unsafe constraints. Independently Z3+cvc5 certify Init/Consecution/
Goal 3VC of the survivors. This is CLASSICAL structural discovery, not ML.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,time
from pathlib import Path
import z3
from research.evidence.q3_trained_affine_from_native_samples_20261021.actual_selfsupervised_candidate_miner import houdini
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare,verified_3vc
CASE="lib/Inv_Track/xujie_code2inv/1.c.sl"
ORIGINAL_SHA="859bae24a9f26044a40a3c97f1d2e5fc08504f06"
def elapsed(t):return (time.perf_counter_ns()-t)/1e6
def build(src):
    start=time.perf_counter_ns()
    # Same source-agnostic "two visible primary variables" interface used
    # by frozen PR411 Boolean DNF and all prior 12 tests.
    x,y=src["now"][:2]
    candidate={}
    for a,b in itertools.product((-1,0,1),repeat=2):
        if a==b==0:continue
        expr=a*x+b*y
        for const in (-1,0,1,2):
            for atom in (expr>=const,expr<=const):
                candidate[atom.sexpr()]=(atom,{"NO_FIT_EXACT_CONJUNCTIVE_GRAMMAR"})
    return list(candidate.values()),{"all_grammar_candidate_count":len(candidate),
                                    "fixed_coefficients":[-1,0,1],
                                    "fixed_bounds":[-1,0,1,2],
                                    "candidate_generation_ms":elapsed(start)}
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args();f=json.loads(Path(a.freeze).read_text())
    q=next(t for t in f["cases"] if t["path"]==CASE)
    if q["git_blob"]!=ORIGINAL_SHA:raise RuntimeError("GENUINE_SOURCE_GIT_SHA_CHANGED")
    t=time.perf_counter_ns()
    _,src,native,parity=prepare(Path(a.root),q)
    candidates,grammar=build(src)
    result=houdini(src,native,candidates)
    raw=[x["smt"] for x in result["retained_candidate_formulas"]]
    report={
        "schema":"neumann.q3.original1_posthoc_source_generic_small_inequality_grammar_Houdini_full3VC.v1",
        "original_code2inv_git_blob":ORIGINAL_SHA,
        "human_manual_invariant_injected":False,
        "same_real_original_source_pre_trans_post_native_parity":parity,
        "fixed_two_observable_state_slots_grammar":grammar,
        "actual_generic_houdini_full_original_dual_solver_result":result,
        "full_original_native_three_VC_SAFE_proved":result["fully_verified_complete_original_3VC"],
        "actual_retained_typed_original_inequalities":raw,
        "retained_original_source_AST_SHA256":result["retained_source_ast_sha256"],
        "source_generic_not_program_filename_coefficients":True,
        "explicitly_posthoc_source_previously_opened":True,
        "not_trained_or_neural":True,
        "not_first_source_blind_or_10x_claim":True,
        "elapsed_source_preflight_generation_houdini_and_independent_proof_ms":elapsed(t),
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"}
    Path(a.out).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("FINAL_ORIGINAL_SOURCE1_CLASSICAL_CONJUNCTIVE_SAFE",report["full_original_native_three_VC_SAFE_proved"],flush=True)
    print("SOURCE1_EXACT_CANDIDATE_GRAMMAR",grammar["all_grammar_candidate_count"],flush=True)
    print("SOURCE1_RETAINED_CONJUNCTION",len(raw),flush=True)
    for z in raw[:18]:print("SOURCE1_ORIGINAL_RETAINED_INVARIANT",z[:200],flush=True)
    print("GLOBAL_Q3_OPEN",flush=True)
if __name__=="__main__":main()
