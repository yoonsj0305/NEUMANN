"""NEUMANN AM2 | Model-free structural headroom audit on already OPENED AM1 tasks.

This is a NEGATIVE CONTROL for capability attribution, not AM2 model evidence:
- Routing reads only instruction/public fields available to the model.
- Original task family/id and private gold are never used to choose a route.
- All accepted answers go through the unchanged independent original checker.
- Coding tasks ABSTAIN instead of fabricating hidden-program solutions.
- Shared arithmetic and CSP tools are available to both TOOL and NEUMANN.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from time import perf_counter_ns
from dataclasses import asdict
from experiments.general_multiplier_tasks import multiplier_tasks, model_view, TASK_SHA256, MODEL_VIEW_SHA256
from neumann1.general_runtime_v106 import ToolPool, reduce_original, verify_original, canonical, sha
from neumann1.general_multiplier_contract import MultiplierBudget

SCHEMA = "neumann.am2.opened-model-free-headroom.v1"
SUPPORTED = ("math_logic","constraint_planning","coding")

def visible_family(view):
    """No task ID, private answer, or hidden family is allowed in this function."""
    if type(view) is not dict or set(view) != {"instruction","public"}:
        return None
    p=view["public"]
    if type(view["instruction"]) is not str or type(p) is not dict:
        return None
    has_math = type(p.get("expression")) is str and type(p.get("bindings")) is dict
    has_csp = type(p.get("domains")) is dict and type(p.get("constraints")) is list
    has_code = type(p.get("requirement")) is str
    if sum((has_math,has_csp,has_code)) != 1:
        return None
    if has_math: return "math_logic"
    if has_csp: return "constraint_planning"
    return "coding"

def _solver(task,private,view,method,budget):
    start=perf_counter_ns()
    code=visible_family(view)
    trace={"method":method,"inferred_family":code,"model_calls":0,"tool_calls":0,
           "checker_calls":0,"error":None,"degraded":False,
           "representation_certified":False,"selected_public_fields":[]}
    def finish(accepted=False):
        trace["complete_ms"]=(perf_counter_ns()-start)/1e6
        trace["accepted"]=bool(accepted)
        return trace
    if code is None:
        trace["error"]="ABSTAIN_UNKNOWN_OR_AMBIGUOUS_VIEW"
        trace["degraded"]=True
        return finish()
    if code=="coding":
        trace["error"]="ABSTAIN_PROGRAM_SEMANTICS_NOT_IN_VISIBLE_SCHEMA"
        trace["degraded"]=True
        return finish()
    try:
        pool=ToolPool(task,private,budget)
        public=view["public"]
        if method=="NEUMANN":
            if code=="math_logic": proposed={"family":code,"expression":public["expression"]}
            else: proposed={"family":code,"domains":public["domains"],"constraints":public["constraints"]}
            # Certificate is checked against the original task by the immutable reducer.
            certificate=reduce_original(task,proposed)
            if certificate.get("original_task_sha256")!=sha(task):
                raise ValueError("CERTIFICATE_SOURCE_DRIFT")
            source=certificate["ir"]
            trace["representation_certified"]=True
            trace["selected_public_fields"]=sorted(("expression","bindings") if code=="math_logic" else ("domains","constraints"))
        else:
            source=public
        if code=="math_logic":
            value=pool.call("arithmetic",{"expression":source["expression"],"bindings":source["bindings"]},budget.tool_ms)
        else:
            output=pool.call("csp",{"spec":{"domains":source["domains"],"constraints":source["constraints"]},"strategy":"mrv"},budget.tool_ms)
            value=output["assignment"]
        trace["tool_calls"]+=1
        trace["checker_calls"]+=1
        accepted=verify_original(task,value,private,budget.tool_ms)
        return finish(accepted)
    except Exception as error:
        trace["error"]=type(error).__name__+": "+str(error)
        trace["degraded"]=True
        return finish()

def evaluate_opened():
    budget=MultiplierBudget()
    cases=[]
    for task,private in multiplier_tasks():
        view=model_view(task)
        # Canary: frozen hidden metadata never appears in the model view.
        assert "family" not in view and "id" not in view
        route=visible_family(view)
        assert route==task["family"],"OPENED_VISIBLE_TASK_SCHEMA_DRIFT"
        for method in ("TOOL","NEUMANN"):
            r=_solver(task,private,view,method,budget)
            cases.append({"task_id":task["id"],"arm":method,**r})
    totals={method:{
        "terminal":sum(x["arm"]==method for x in cases),
        "accepted":sum(x["accepted"] for x in cases if x["arm"]==method),
        "tool_calls":sum(x["tool_calls"] for x in cases if x["arm"]==method),
        "checker_calls":sum(x["checker_calls"] for x in cases if x["arm"]==method),
        "model_calls":0,
        "complete_ms":sum(x["complete_ms"] for x in cases if x["arm"]==method),
        "degraded_coding":sum(x["degraded"] and x["inferred_family"]=="coding" for x in cases if x["arm"]==method)
    } for method in ("TOOL","NEUMANN")}
    assert totals["TOOL"]["terminal"]==totals["NEUMANN"]["terminal"]==12
    assert totals["TOOL"]["accepted"]==totals["NEUMANN"]["accepted"]==8
    assert all(x["accepted"] for x in cases if x["inferred_family"]!="coding")
    assert all(not x["accepted"] for x in cases if x["inferred_family"]=="coding")
    assert all(x["model_calls"]==0 for x in cases)
    return {
        "schema":SCHEMA,
        "task_sha256":TASK_SHA256,
        "model_view_sha256":MODEL_VIEW_SHA256,
        "opened_only":True,
        "new_architecture_multiplier_executed":False,
        "actual_frozen_model_inference":False,
        "new_training":False,"sealed_opened":False,"frontier_calls":0,
        "result":"OPENED_8_OF_12_MODEL_FREE_MATCHED_TOOL_BASELINE",
        "interpretation":"8/12 math+CSP capability is already fully accessible to both matched TOOL and NEUMANN without LLM. This is not an AM2 PASS, new intelligence, causal architecture discovery, or full compute advantage.",
        "remaining_discrimination":"Coding 4/12 or genuine harder structural/semantic tasks must distinguish a future new architecture against the strongest matched baseline.",
        "resource_scope":"Python CPU process wall only; excludes model, accelerator, energy, monetary cost.",
        "totals":totals,"rows":cases,
    }

if __name__=="__main__":
    out=evaluate_opened()
    print(json.dumps(out,indent=2,sort_keys=True))
