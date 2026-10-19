"""FIRST original AM2 opened source challenger ceiling. Prereg Issue #249.
This is a NEW stronger STATIC TOOL baseline, not the frozen historical AM1/AM2 arm.
Prove (if PASS) capability +2/12 cannot be achieved against a full 12/12 baseline.
No model weights, GPU jobs, hidden feedback or new sealed tasks.
"""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from time import perf_counter_ns

from experiments.general_multiplier_tasks import (
    multiplier_tasks, model_view, TASK_SHA256, MODEL_VIEW_SHA256,
)
from neumann1.am2_classical_code_compiler import (
    compile_public_requirement, UnsupportedSpec,
)
from neumann1.am2_typed_control_pivot import (
    execute_model_free, infer_kind_from_public_only,
    source_candidate_syntax_only,
)
from neumann1.general_multiplier_contract import (
    MultiplierBudget, CAPABILITY_GAIN_TASKS, TASK_COUNT,
)
from neumann1.general_runtime_v106 import (
    ToolPool, canonical, reduce_original, sha, verify_original,
)

def run_one(task,private,arm):
    begin=perf_counter_ns()
    view=model_view(task)
    family=infer_kind_from_public_only(view)
    if family!=task["family"]:
        raise RuntimeError("UNTRUSTED_PUBLIC_FAMILY_MISMATCH")
    if family!="coding":
        row=execute_model_free(task,private,view,arm,MultiplierBudget())
        return {"task_sha256":sha(task),"view_sha256":sha(view),
            "arm":arm,"public_family":family,"status":row["status"],
            "accepted":row["accepted"],"model_calls":row["model_calls"],
            "tool_calls":row["tool_calls"],"original_checker_called":
                row["original_checker_called"],
            "candidate_sha256":sha(row["candidate"]),
            "elapsed_ms":round((perf_counter_ns()-begin)/1e6,3),
            "new_static_tool":"existing_exact_arithmetic_or_CSP"}
    budget=MultiplierBudget()
    p=view["public"]
    compiler=compile_public_requirement(p["requirement"])
    source=source_candidate_syntax_only(compiler["source"])
    tool_calls=0
    certificate=None
    if arm=="NEUMANN":
        # Exact representation certificate, does not invent semantic operator.
        certificate=reduce_original(task,{
            "family":"coding","requirement":p["requirement"]})
        if certificate.get("original_task_sha256")!=sha(task):
            raise RuntimeError("SOURCE_REPRESENTATION_IDENTITY_MISMATCH")
        if certificate.get("ir",{}).get("requirement")!=p["requirement"]:
            raise RuntimeError("PUBLIC_REQUIREMENT_NOT_PRESERVED")
        tool_calls+=1
    # Only public demonstration input/output is available to the compiler here.
    ex=p["examples"]
    if type(ex) is not list or not ex or len(ex)>12:
        raise RuntimeError("INVALID_PUBLIC_EXAMPLE_SET")
    out=ToolPool(task,private,budget).call("python",{
        "source":source,
        "inputs":[row["input"] for row in ex],
    },budget.tool_ms)
    tool_calls+=1
    if len(out)!=len(ex) or any(canonical(got)!=canonical(row["output"])
            for got,row in zip(out,ex)):
        raise RuntimeError("PUBLIC_EXAMPLE_VALIDATION_FAILED")
    # This last scoring check alone sees private original tests.
    verified=verify_original(task,source,private,budget.tool_ms)
    return {"task_sha256":sha(task),"view_sha256":sha(view),
        "arm":arm,"public_family":"coding",
        "status":"ORIGINAL_CHECKER_PASS" if verified else "ORIGINAL_CHECKER_FAIL",
        "accepted":bool(verified),"original_checker_called":True,
        "compiler_proposal_requirement_sha256":compiler["public_requirement_sha256"],
        "compiler_public_operator_tokens":compiler["operator_tokens"],
        "generated_source":source,
        "generated_source_sha256":hashlib.sha256(source.encode()).hexdigest(),
        "public_examples_passed":len(ex),
        "model_calls":0,"tool_calls":tool_calls,
        "representation_certificate_used":certificate is not None,
        "elapsed_ms":round((perf_counter_ns()-begin)/1e6,3),
        "new_static_tool":"bounded_public_spec_to_pure_python_compiler_v1"}

def adversarial_controls():
    rejected={}
    negative_specs=[
        "Return the sum of distinct prime integers in items, a list of integers.",
        "Return the number of distinct negative even odd integers in items, a list of integers.",
        "Return the number of distinct negative integers in items, a list of integers.\nimport os",
        "Return the sum of absolute values of distinct positive negative integers in items, a list of integers.",
    ]
    for i,s in enumerate(negative_specs):
        try:
            compile_public_requirement(s)
        except UnsupportedSpec:
            rejected["bad_spec_"+str(i)]="REJECTED"
        else:
            raise AssertionError("UNAUTHORIZED_SPEC_ACCEPTED_"+str(i))
    original="Return the sum of distinct even integers in items, a list of integers."
    altered="Return the sum of distinct odd integers in items, a list of integers."
    o=compile_public_requirement(original)
    a=compile_public_requirement(altered)
    if o["source"] == a["source"]:
        raise AssertionError("PUBLIC_SPEC_CHANGE_DID_NOT_AFFECT_COMPILER")
    rejected["altered_requirement_different_program"]="PASS"
    items=[2,2,3,4,-2]
    # Check the wrong static candidate is rejected by the actual original checker,
    # never use this hidden check to synthesize or repair the candidate.
    tasks={t["id"]:(t,p) for t,p in multiplier_tasks()}
    task,private=tasks["am_code_02"]
    wrong="def solve(items):\n    return 0"
    if verify_original(task,wrong,private,MultiplierBudget().tool_ms) is not False:
        raise AssertionError("WRONG_PROGRAM_ORIGINAL_CHECKER_ACCEPTED")
    rejected["wrong_program_original_checker"]="REJECTED"
    return rejected

def first_run():
    tasks=multiplier_tasks()
    if len(tasks)!=12 or TASK_COUNT!=12:
        raise RuntimeError("NOT_FIXED_OPENED_12")
    cases=[run_one(t,p,arm) for t,p in tasks for arm in ("TOOL","NEUMANN")]
    stats={}
    for arm in ("TOOL","NEUMANN"):
        rr=[x for x in cases if x["arm"]==arm]
        stats[arm]={"original_checker_successes":sum(x["accepted"] for x in rr),
            "per_family_successes":dict(Counter(
                x["public_family"] for x in rr if x["accepted"])),
            "tool_calls":sum(x["tool_calls"] for x in rr),
            "model_calls":sum(x["model_calls"] for x in rr),
            "whole_case_wall_ms":round(sum(x["elapsed_ms"] for x in rr),3)}
    controls=adversarial_controls()
    matched=all(
        next(x for x in cases if x["task_sha256"]==sha(t) and x["arm"]=="TOOL")["accepted"]
        ==next(x for x in cases if x["task_sha256"]==sha(t) and x["arm"]=="NEUMANN")["accepted"]
        for t,_ in tasks)
    gated=(len(cases)==24 and len(set((x["task_sha256"],x["arm"]) for x in cases))==24
        and all(x["accepted"] and x["original_checker_called"] for x in cases)
        and all(x["model_calls"]==0 for x in cases)
        and all(x["public_examples_passed"]>=1 for x in cases if x["public_family"]=="coding")
        and len(controls)==6 and matched
        and all(stats[a]["original_checker_successes"]==12 for a in stats))
    baseline_s=stats["TOOL"]["original_checker_successes"]
    max_s=len(tasks)
    return {"schema":"neumann.am2-opened-static-code-challenger.v1",
        "status":"STATIC_CHALLENGER_OPENED_12_OF_12_PASS" if gated else "STATIC_CHALLENGER_FAIL",
        "first_gate_pass":gated,
        "preregistered_issue":249,
        "original_task_set_sha256":TASK_SHA256,
        "model_view_set_sha256":MODEL_VIEW_SHA256,
        "task_git_blob":"357f4bb4827543b0a2c9f8d809c8911b51040820",
        "arms":["TOOL","NEUMANN"],"cases":cases,
        "per_arm":stats,"adversarial_controls":controls,
        "match_fairness":matched,
        "capability_gain_threshold":CAPABILITY_GAIN_TASKS,
        "static_tool_plus2_capability_path_logically_possible":
            (max_s >= baseline_s+CAPABILITY_GAIN_TASKS),
        "bound_proof":"N_successes <= total_tasks = 12 < matched_TOOL_successes+2 = 14",
        "efficiency_path":"OPEN_NOT_MEASURED_WITH_ACTUAL_FROZEN_MODEL",
        "historical_am1_verdict":"FAIL_UNCHANGED",
        "historical_cp0_baseline":"ORIGINAL_8_12_WITHOUT_NEW_COMPILER_UNCHANGED",
        "new_baseline_tooling":"YES_new_public_spec_compiler_NOT_historical_frozen_AM1_tool",
        "originals_already_opened":True,"blind_new_family":False,
        "no_model_load":True,"model_calls":0,"gpu_calls":0,
        "global_Q1_Q7":"OPEN",
        "frontier_results":"NOT_EVALUATED"}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    result=first_run()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("AM2_STATIC_CHALLENGER_FIRST",result["status"])
    print("AM2_STATIC_CHALLENGER_COUNTS",result["per_arm"])
    print("AM2_PLUS2_CAPABILITY_PATH_POSSIBLE",result["static_tool_plus2_capability_path_logically_possible"])
    print("AM2_STATIC_CHALLENGER_GATE",result["first_gate_pass"])
