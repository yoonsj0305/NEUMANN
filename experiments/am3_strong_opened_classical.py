"""AM3 OPENED evaluation diagnostic: stronger zero-model classical control.

NOT neural/NEUMANN capability. This posthoc human-designed semantic grammar
is intentionally tested against previously opened, author-constructed AM1 tasks.
It must NOT be described as a fresh heldout, preregistered baseline or general
NL understanding. It diagnoses whether the OPENED task set can discriminate
architecture-level intelligence from a simple classical parser.

Authority rules:
- Only model_view(task) is used to infer family and propose a program.
- Never inspect task id/family/private/hidden tests for selection or generation.
- Strongest comparator is allowed exactly the same public tools and checker as N.
- All accepted results use the ORIGINAL checker, not inferred output.
- Abstain on unknown, unparseable, ambiguous or malformed semantics.
"""
from __future__ import annotations
import ast
from dataclasses import dataclass
import json
import re
from time import perf_counter_ns
from experiments.general_multiplier_tasks import multiplier_tasks, model_view, TASK_SHA256
from neumann1.general_multiplier_contract import MultiplierBudget
from neumann1.general_runtime_v106 import ToolPool, canonical, verify_original, sha

SCHEMA = "neumann.am3.opened-strong-classical-ceiling.v1"
PHRASE = re.compile(
    r"^Return the (?P<aggregate>number|sum)"
    r"(?P<absolute> of absolute values)? of "
    r"(?P<distinct>distinct )?"
    r"(?P<qualifiers>(?:(?:negative|positive|nonzero|zero|even|odd) )*)"
    r"integers in items, a list of integers\.$"
)
QUALIFIERS = frozenset({"negative","positive","nonzero","zero","even","odd"})

@dataclass(frozen=True)
class TypedPlan:
    aggregate: str
    absolute: bool
    distinct: bool
    qualifiers: tuple[str,...]

def infer_family(view):
    if type(view) is not dict or set(view)!={"instruction","public"}:
        return None
    p=view["public"]
    if type(view["instruction"]) is not str or type(p) is not dict:
        return None
    hits=[]
    if type(p.get("expression")) is str and type(p.get("bindings")) is dict:
        hits.append("math_logic")
    if type(p.get("domains")) is dict and type(p.get("constraints")) is list:
        hits.append("constraint_planning")
    if type(p.get("requirement")) is str and type(p.get("examples")) is list:
        hits.append("coding")
    return hits[0] if len(hits)==1 else None

def parse_requirement(requirement):
    if type(requirement) is not str: return None
    m=PHRASE.fullmatch(requirement)
    if not m: return None
    agg=m.group("aggregate")
    absolute=bool(m.group("absolute"))
    distinct=bool(m.group("distinct"))
    qualifiers=tuple((m.group("qualifiers") or "").split())
    if not qualifiers or len(set(qualifiers))!=len(qualifiers) or not set(qualifiers)<=QUALIFIERS:
        return None
    q=set(qualifiers)
    if {"negative","positive"}<=q or {"even","odd"}<=q:
        return None
    if "zero" in q and ({"nonzero","positive","negative","odd"} & q):
        return None
    if "nonzero" in q and "zero" in q:
        return None
    if agg=="number" and absolute:
        # Count of absolute values is semantically underspecified here.
        return None
    return TypedPlan(agg,absolute,distinct,qualifiers)

def predicate(plan):
    q=set(plan.qualifiers)
    terms=[]
    if "negative" in q: terms.append("x < 0")
    if "positive" in q: terms.append("x > 0")
    if "nonzero" in q: terms.append("x != 0")
    if "zero" in q: terms.append("x == 0")
    if "even" in q: terms.append("x % 2 == 0")
    if "odd" in q: terms.append("x % 2 != 0")
    return " and ".join(terms) if terms else "True"

def compile_program(plan):
    if not isinstance(plan,TypedPlan):raise ValueError("TYPED_PLAN_REQUIRED")
    base="set(items)" if plan.distinct else "items"
    pred=predicate(plan)
    if plan.aggregate=="number":
        expression=f"len([x for x in {base} if {pred}])"
    elif plan.aggregate=="sum":
        term="abs(x)" if plan.absolute else "x"
        expression=f"sum({term} for x in {base} if {pred})"
    else:raise ValueError("UNSUPPORTED_AGGREGATE")
    source=f"def solve(items):\n    return {expression}"
    tree=ast.parse(source,mode="exec")
    if (len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef)
        or tree.body[0].name!="solve"):
        raise ValueError("COMPILER_CONTRACT_FAILURE")
    return source

def solve_opened(task,private,view,budget=None):
    budget=budget or MultiplierBudget()
    started=perf_counter_ns()
    record={
      "schema":SCHEMA,"task_view_sha256":sha(view),
      "model_calls":0,"input_tokens":0,"output_tokens":0,
      "tool_calls":0,"checker_calls":0,"accepted":False,
      "candidate":None,"typed_plan":None,"reason":None,
      "energy_j":None,"gpu_memory_bytes":None,
      "complete_ms":None
    }
    def finish():
        record["complete_ms"]=(perf_counter_ns()-started)/1e6
        if record["complete_ms"]>budget.wall_ms:
            record["accepted"]=False
            record["reason"]="QUERY_WALL_EXCEEDED"
        return record
    if canonical(view)!=canonical(model_view(task)):
        record["reason"]="ORIGINAL_VIEW_MISMATCH"
        return finish()
    family=infer_family(view)
    if family is None:
        record["reason"]="AMBIGUOUS_OR_UNKNOWN_SCHEMA"
        return finish()
    pool=ToolPool(task,private,budget)
    public=view["public"]
    try:
        if family=="math_logic":
            candidate=pool.call("arithmetic",{
                "expression":public["expression"],"bindings":public["bindings"]},budget.tool_ms)
            record["tool_calls"]+=1
        elif family=="constraint_planning":
            result=pool.call("csp",{
                "spec":{"domains":public["domains"],"constraints":public["constraints"]},
                "strategy":"mrv"},budget.tool_ms)
            record["tool_calls"]+=1
            candidate=result["assignment"]
        else:
            plan=parse_requirement(public["requirement"])
            if plan is None:
                record["reason"]="UNSUPPORTED_NATURAL_LANGUAGE_SEMANTICS"
                return finish()
            candidate=compile_program(plan)
            record["typed_plan"]={
                "aggregate":plan.aggregate,"absolute":plan.absolute,
                "distinct":plan.distinct,"qualifiers":plan.qualifiers}
            # Public-only example replay, before checking hidden original tests.
            examples=public["examples"]
            if not examples:
                record["reason"]="NO_PUBLIC_BEHAVIORAL_EVIDENCE"
                return finish()
            outputs=pool.call("python",{
                "source":candidate,"inputs":[e["input"] for e in examples]},budget.tool_ms)
            record["tool_calls"]+=1
            if (len(outputs)!=len(examples) or any(
                canonical(value)!=canonical(ex["output"])
                for value,ex in zip(outputs,examples))):
                record["reason"]="PUBLIC_EXAMPLE_MISMATCH"
                return finish()
        record["candidate"]=candidate
        record["checker_calls"]+=1
        record["accepted"]=bool(verify_original(task,candidate,private,budget.tool_ms))
        if not record["accepted"]:
            record["reason"]="ORIGINAL_CHECKER_REJECTED"
    except Exception as exc:
        record["reason"]=type(exc).__name__+": "+str(exc)
    return finish()

def run_opened():
    entries=[]
    for task,private in multiplier_tasks():
        view=model_view(task)
        receipt=solve_opened(task,private,view)
        entries.append({"id":task["id"],"original_family":task["family"],**receipt})
    rows={f:{"cases":sum(x["original_family"]==f for x in entries),
             "accepted":sum(x["accepted"] for x in entries if x["original_family"]==f)}
          for f in ("math_logic","coding","constraint_planning")}
    accepted=sum(x["accepted"] for x in entries)
    return {
      "schema":SCHEMA,"scope":"POSTHOC_OPENED_AUTHOR_CONSTRUCTED_ONLY",
      "task_sha256":TASK_SHA256,"model_call_count":0,
      "test_hidden_from_proposal":True,"human_written_parser":True,
      "preregistered_before_tasks":False,"new_generalization_evidence":False,
      "run_count":len(entries),"accepted":accepted,"family_results":rows,
      "decision":"CURRENT_AM1_12_TASKS_NON_DISCRIMINATIVE_IF_12_OF_12" if accepted==12 else "OPENED_BASELINE_GAP_REMAINS",
      "global_q1_to_q7":"OPEN","resource":{
        "cost_comparison_valid":False,"energy_j":"UNKNOWN","gpu_memory_bytes":"UNKNOWN",
        "complete_cpu_wall_ms":sum(x["complete_ms"] for x in entries)},
      "rows":entries
    }

if __name__=="__main__":
    print(json.dumps(run_opened(),indent=2,sort_keys=True))
