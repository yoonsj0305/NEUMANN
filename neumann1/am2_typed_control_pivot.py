"""AM2-CP0: typed public-shape dispatch; no learned capability experiment.
Preregistered before code: GitHub Issue #243.
"""
from __future__ import annotations
import ast
import json
from time import perf_counter_ns
from experiments.general_multiplier_tasks import model_view
from neumann1.general_multiplier_contract import MultiplierBudget
from neumann1.general_runtime_v106 import ToolPool, canonical, reduce_original, verify_original

PUBLIC_KEYS = {
    "math_logic": {"expression", "bindings"},
    "constraint_planning": {"domains", "constraints"},
    "coding": {"requirement"},
}
OPTIONAL = {
    "math_logic": {"background"},
    "constraint_planning": {"background"},
    "coding": {"background", "examples"},
}

class RejectControl(Exception):
    pass

def infer_kind_from_public_only(view):
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise RejectControl("PUBLIC_VIEW_SCHEMA_MISMATCH")
    if type(view["instruction"]) is not str or not view["instruction"]:
        raise RejectControl("MISSING_PUBLIC_INSTRUCTION")
    p = view["public"]
    if type(p) is not dict:
        raise RejectControl("PUBLIC_FIELDS_INVALID")
    matches = [family for family, required in PUBLIC_KEYS.items()
        if required <= set(p) <= required | OPTIONAL[family]]
    if len(matches) != 1:
        raise RejectControl("AMBIGUOUS_OR_UNKNOWN_PUBLIC_FORM")
    family=matches[0]
    if family == "math_logic" and (type(p["expression"]) is not str
        or type(p["bindings"]) is not dict):
        raise RejectControl("ILL_TYPED_MATH")
    if family == "constraint_planning" and (type(p["domains"]) is not dict
        or type(p["constraints"]) is not list):
        raise RejectControl("ILL_TYPED_CSP")
    if family == "coding" and type(p["requirement"]) is not str:
        raise RejectControl("ILL_TYPED_CODE")
    return family

def source_candidate_syntax_only(raw):
    """Validate model-produced code shape ONLY, not its semantics or correctness."""
    if type(raw) is not str or len(raw)>4096:
        raise RejectControl("BAD_MODEL_CODE_PAYLOAD")
    src=raw.strip()
    fence=chr(96)*3
    if src.startswith(fence+"python\n") and src.endswith(fence):
        src=src[len(fence+"python\n"):-len(fence)].strip()
    try:
        tree=ast.parse(src)
    except (SyntaxError, ValueError) as exc:
        raise RejectControl("INVALID_CODE_SYNTAX") from exc
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef):
        raise RejectControl("NOT_SINGLE_SOLVE_FUNCTION")
    fn=tree.body[0]
    if (fn.name!="solve" or fn.decorator_list or fn.args.posonlyargs
        or fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg
        or fn.args.defaults or fn.args.kw_defaults
        or [a.arg for a in fn.args.args]!=["items"]):
        raise RejectControl("INVALID_SOLVE_SIGNATURE")
    forbidden=(ast.Import,ast.ImportFrom,ast.Attribute,ast.Global,
        ast.Nonlocal,ast.AsyncFunctionDef,ast.Lambda,ast.ClassDef,
        ast.With,ast.AsyncWith,ast.Try,ast.Raise)
    if any(isinstance(node,forbidden) for node in ast.walk(tree)):
        raise RejectControl("FORBIDDEN_PYTHON_FORM")
    return src

def execute_model_free(task,private,view,arm,budget=None):
    """Matched TOOL/NEUMANN deterministic executor with independent original check.
    Code tasks must abstain pending ACTUAL frozen model. No hidden answer injection.
    """
    if arm not in ("TOOL","NEUMANN"):
        raise RejectControl("ARM_NOT_IN_CP0")
    if canonical(view)!=canonical(model_view(task)):
        raise RejectControl("PRIVATE_TASK_VIEW_OR_ORIGINAL_MISMATCH")
    family=infer_kind_from_public_only(view)
    if task["family"]!=family:
        raise RejectControl("PUBLIC_SCHEMA_DIFFERS_FROM_ORIGINAL")
    p=view["public"]
    started=perf_counter_ns()
    r={"arm":arm,"public_schema":family,"accepted":False,
       "model_calls":0,"model_output_tokens":0,"tool_calls":0,
       "original_checker_called":False,"candidate":None,
       "certificate":None,"status":"UNDETERMINED"}
    if family=="coding":
        r["status"]="NEEDS_ACTUAL_FROZEN_MODEL"
        r["complete_ms"]=(perf_counter_ns()-started)/1e6
        return r
    budget=budget or MultiplierBudget()
    pool=ToolPool(task,private,budget)
    src=p
    if arm=="NEUMANN":
        claimed=({"family":family,"expression":p["expression"]}
            if family=="math_logic" else
            {"family":family,"domains":p["domains"],"constraints":p["constraints"]})
        cert=reduce_original(task,claimed)
        if not cert.get("original_task_sha256") or cert.get("ir",{}).get("family")!=family:
            raise RejectControl("CERTIFICATE_IDENTITY_MISMATCH")
        r["certificate"]={"scope":cert["certificate_scope"],
            "original_task_sha256":cert["original_task_sha256"],
            "source_field_names":sorted(PUBLIC_KEYS[family])}
        r["tool_calls"]+=1
        src=cert["ir"]
    if family=="math_logic":
        answer=pool.call("arithmetic",{
            "expression":src["expression"],"bindings":src["bindings"]},budget.tool_ms)
        r["executor"]="arithmetic"
    else:
        out=pool.call("csp",{
            "spec":{"domains":src["domains"],"constraints":src["constraints"]},
            "strategy":"mrv"},budget.tool_ms)
        answer=out["assignment"]
        r["executor"]="csp"
    r["tool_calls"]+=1
    r["candidate"]=answer
    r["original_checker_called"]=True
    r["accepted"]=bool(verify_original(task,answer,private,budget.tool_ms))
    r["status"]="ORIGINAL_CHECKER_PASS" if r["accepted"] else "ORIGINAL_CHECKER_FAIL"
    r["complete_ms"]=(perf_counter_ns()-started)/1e6
    return r
