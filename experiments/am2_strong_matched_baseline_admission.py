"""AM2 Strong Matched Baseline Admission: preserve an existing 12/12 ceiling.

This is a replay of the *previously opened and solved* October 19 public
development set, NOT new model intelligence, novel generalization, or a change
to the historical AM1 three-arm test. The existing human-authored compiler is
imported as a byte-identical source Git blob; both TOOL and NEUMANN receive
the same expanded tool catalogue.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from time import perf_counter_ns
from neumann1.am2_classical_code_compiler import compile_public_requirement, UnsupportedSpec
from neumann1.general_multiplier_contract import MultiplierBudget, CAPABILITY_GAIN_TASKS
from neumann1.general_runtime_v106 import ToolPool, canonical, sha, reduce_original, verify_original
from experiments.general_multiplier_tasks import (
    multiplier_tasks, model_view, TASK_SHA256, MODEL_VIEW_SHA256,
)
from experiments.am2_opened_control_dominance import visible_family

SCHEMA="neumann.am2.strong-matched-baseline-admission.v1"
REFERENCE_COMPILER_GIT_BLOB="8440a8dc13fa8084fd48407462deb7ef41c5e715"

def git_blob_sha(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def check_compiler_identity():
    import neumann1.am2_classical_code_compiler as c
    return git_blob_sha(c.__file__)==REFERENCE_COMPILER_GIT_BLOB

def strong_one(task, private, arm):
    if arm not in ("TOOL","NEUMANN"):
        raise ValueError("ONLY_STRONG_MATCHED_TOOL_AND_N")
    view=model_view(task)
    kind=visible_family(view)
    if kind!=task["family"]:
        raise ValueError("MODEL_VISIBLE_FAMILY_MISMATCH")
    if canonical(view)!=canonical(model_view(task)):
        raise ValueError("MODEL_VIEW_ORIGINAL_MISMATCH")
    budget=MultiplierBudget()
    start=perf_counter_ns()
    tool_calls=checker_calls=0
    source=view["public"]
    represented=False
    if arm=="NEUMANN":
        proposed={"family":kind}
        if kind=="math_logic":
            proposed["expression"]=source["expression"]
        elif kind=="constraint_planning":
            proposed.update(domains=source["domains"],constraints=source["constraints"])
        else:
            proposed["requirement"]=source["requirement"]
        cert=reduce_original(task,proposed)
        if cert.get("original_task_sha256")!=sha(task):
            raise ValueError("REDUCER_ORIGINAL_IDENTITY_MISMATCH")
        represented=True
        source=cert["ir"]
        tool_calls+=1 # accounting for certificate, no free work.
    pool=ToolPool(task,private,budget)
    public_example_count=0
    if kind=="math_logic":
        candidate=pool.call("arithmetic",{
            "expression":source["expression"],"bindings":source["bindings"]
        },budget.tool_ms)
        tool_calls+=1
    elif kind=="constraint_planning":
        solved=pool.call("csp",{
            "spec":{"domains":source["domains"],"constraints":source["constraints"]},
            "strategy":"mrv"
        },budget.tool_ms)
        tool_calls+=1
        candidate=solved["assignment"]
    else:
        # Compiler sees only PUBLIC requirement and never source ID, labels,
        # hidden tests, TASK family, or expected outputs.
        compiled=compile_public_requirement(source["requirement"])
        candidate=compiled["source"]
        examples=view["public"].get("examples",[])
        if not examples or len(examples)>12:raise ValueError("PUBLIC_EXAMPLES_MISSING")
        actual=pool.call("python",{
            "source":candidate,"inputs":[x["input"] for x in examples]
        },budget.tool_ms)
        tool_calls+=1
        public_example_count=len(examples)
        if len(actual)!=len(examples) or any(canonical(v)!=canonical(e["output"])
                for v,e in zip(actual,examples)):
            raise ValueError("COMPILER_PUBLIC_REPLAY_FAIL")
    checker_calls+=1
    accepted=verify_original(task,candidate,private,budget.tool_ms)
    wall_ms=(perf_counter_ns()-start)/1e6
    return {
        "arm":arm,"task_id":task["id"],"kind":kind,
        "accepted":bool(accepted),"model_calls":0,
        "tool_calls":tool_calls,"checker_calls":checker_calls,
        "representation_certified":represented,
        "candidate_sha256":sha(candidate),
        "original_task_sha256":sha(task),
        "original_view_sha256":sha(view),
        "public_example_count":public_example_count,
        "wall_ms":wall_ms,"energy_j":None,"money_usd":None,"gpu_vram_bytes":None
    }

def evaluate():
    if not check_compiler_identity():raise ValueError("STRONG_BASELINE_SOURCE_BLOB_CHANGED")
    cases=[]
    for task,private in multiplier_tasks():
        for arm in ("TOOL","NEUMANN"):
            cases.append(strong_one(task,private,arm))
    stats={}
    for arm in ("TOOL","NEUMANN"):
        rows=[r for r in cases if r["arm"]==arm]
        stats[arm]={
            "original_solved":sum(x["accepted"] for x in rows),
            "terminal":len(rows),
            "model_calls":sum(x["model_calls"] for x in rows),
            "tool_calls":sum(x["tool_calls"] for x in rows),
            "checker_calls":sum(x["checker_calls"] for x in rows),
            "wall_ms":sum(x["wall_ms"] for x in rows),
            "by_family":{family:sum(r["accepted"] and r["kind"]==family for r in rows)
                         for family in ("math_logic","constraint_planning","coding")}
        }
    assert len(cases)==24
    assert all(stats[a]["original_solved"]==12 for a in stats)
    assert all(stats[a]["model_calls"]==0 for a in stats)
    assert all(stats[a]["checker_calls"]==12 for a in stats)
    n=len(multiplier_tasks())
    b=stats["TOOL"]["original_solved"]
    cannot_gain=n<b+CAPABILITY_GAIN_TASKS
    assert cannot_gain
    return {
        "schema":SCHEMA,
        "scope":"Already-opened author-constructed AM1 development set; expanded classical toolbox",
        "source_provenance": "2026-10-19 archived AM2 stronger classical compiler, Git blob identical",
        "source_git_blob":REFERENCE_COMPILER_GIT_BLOB,
        "task_sha256":TASK_SHA256,
        "model_view_sha256":MODEL_VIEW_SHA256,
        "result":"STRONG_MATCHED_BASELINE_12_OF_12_AND_CAPABILITY_GATE_SATURATED",
        "stronger_tool_catalogue_added":True,
        "historical_am1_first_unchanged":True,
        "historical_am2_8_12_unchanged":True,
        "new_neural_capability_evidence":False,
        "global_Q1_Q7":"OPEN",
        "decision":"STOP adding models for +2 accuracy on these already-opened 12 tasks; retain separate unmeasured efficiency path",
        "max_extra_accuracy_with_this_toolbox":max(0,n-b),
        "plus_two_accuracy_gate_possible":not cannot_gain,
        "efficiency_gate":"NOT_EVALUATED",
        "statistics":stats,
        "rows":cases,
    }

if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2,sort_keys=True))
