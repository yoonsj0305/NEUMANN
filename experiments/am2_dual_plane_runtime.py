"""AM2: separate low-entropy control from high-entropy generation.

Engineering-only until real frozen model inference on accelerator; fixture
outputs are never evidence of autonomous intelligence or AM2 improvement.
No amendment to immutable AM1 results.
"""
from __future__ import annotations
import ast
import json
from time import perf_counter_ns
from neumann1.general_runtime_v106 import ToolPool, reduce_original, verify_original, canonical, sha
from neumann1.general_multiplier_contract import MultiplierBudget
from experiments.general_multiplier_tasks import model_view
from experiments.am2_opened_control_dominance import visible_family

SCHEMA="neumann.am2.dual-plane-runtime.v1"
ARMS=("DIRECT","TOOL","NEUMANN")
MAX_SOURCE_CHARS=2048

def plain_final(raw):
    if type(raw) is not str or len(raw)>MAX_SOURCE_CHARS+256:
        raise ValueError("ABSTAIN_MISSING_OR_UNBOUNDED_FINAL")
    if "<|channel>thought" in raw or "<channel|>thought" in raw:
        raise ValueError("ABSTAIN_THOUGHT_CHANNEL_IN_CONTROL_OUTPUT")
    text=raw.strip()
    if "<|channel>final" in text:
        text=text.rsplit("<|channel>final",1)[-1].strip()
    for token in ("<turn|>","<eos>","<|end|>","<|im_end|>"):
        text=text.replace(token,"")
    return text.strip()

def parse_source(raw):
    text=plain_final(raw)
    if text.startswith(chr(96)) or len(text)>MAX_SOURCE_CHARS or not text.startswith("def solve(items):"):
        raise ValueError("ABSTAIN_UNSAFE_OR_NONPROGRAM_FINAL")
    try:
        module=ast.parse(text,mode="exec")
    except SyntaxError as exc:
        raise ValueError("ABSTAIN_UNPARSEABLE_PROGRAM") from exc
    if len(module.body)!=1 or not isinstance(module.body[0],ast.FunctionDef):
        raise ValueError("ABSTAIN_TOPLEVEL_NONFUNCTION")
    fn=module.body[0]
    if (fn.name!="solve" or fn.decorator_list or fn.args.posonlyargs or
        len(fn.args.args)!=1 or fn.args.args[0].arg!="items" or
        fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg or fn.args.defaults):
        raise ValueError("ABSTAIN_UNSUPPORTED_ENTRYPOINT")
    if any(isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,
                         ast.AsyncFunctionDef,ast.Await)) for n in ast.walk(module)):
        raise ValueError("ABSTAIN_UNTRUSTED_LANGUAGE")
    return text

def coding_prompt(view):
    public=view["public"]
    if visible_family(view)!="coding":
        raise ValueError("CODING_PROMPT_INELIGIBLE")
    examples=public.get("examples",[])
    if type(examples) is not list:
        raise ValueError("MALFORMED_PUBLIC_EXAMPLES")
    return [
        {"role":"system","content":(
            "Write only executable Python source defining def solve(items):. "
            "No Markdown, no explanations, no imports, no attributes, no eval, "
            "no files or network. Use only safe pure Python list/integer operations."
        )},
        {"role":"user","content":canonical({
            "requirement":public["requirement"],
            "examples":examples,
            "signature":"solve(items)"
        })}
    ]

def final_prompt(view,kind):
    if kind=="coding": return coding_prompt(view)
    if kind=="math_logic":
        ask="Return only the exact rational number, as integer or p/q. No prose."
    else:
        ask="Return only a JSON object mapping each declared variable to an integer, no prose."
    return [{"role":"system","content":ask},{"role":"user","content":canonical(view)}]

def parse_direct(raw,kind):
    x=plain_final(raw)
    if kind=="coding":return parse_source(x)
    if kind=="math_logic":
        if not x or len(x)>96 or any(c not in "-+0123456789/" for c in x):
            raise ValueError("ABSTAIN_INVALID_RATIONAL_FINAL")
        return x
    if len(x)>2048:raise ValueError("ABSTAIN_LONG_ASSIGNMENT")
    v=json.loads(x)
    if type(v) is not dict or any(type(k) is not str or type(z) is not int for k,z in v.items()):
        raise ValueError("ABSTAIN_INVALID_ASSIGNMENT")
    return v

def run_observation(task,private,view,arm,core=None,budget=None):
    if arm not in ARMS:raise ValueError("UNREGISTERED_ARM")
    budget=budget or MultiplierBudget()
    started=perf_counter_ns()
    trace={
      "schema":SCHEMA,"arm":arm,"task_id":task.get("id"),
      "model_view_sha256":sha(view),"original_task_sha256":sha(task),
      "model_calls":0,"tool_calls":0,"input_tokens":0,"output_tokens":0,
      "token_accounting_complete":True,
      "checker_calls":0,"representation_certified":False,"thinking_enabled":False,
      "events":[],"accepted":False,"answer":None,"error":None,
      "peak_accelerator_memory_bytes":0,
      "model_identity_sha256":sha(core.identity) if core is not None else None
    }
    def left():return budget.wall_ms-(perf_counter_ns()-started)/1e6
    def finish():
        trace["complete_ms"]=(perf_counter_ns()-started)/1e6
        if trace["complete_ms"]>budget.wall_ms:
            trace["accepted"]=False
            trace["error"]="QUERY_DEADLINE_EXCEEDED"
        return trace
    if canonical(view)!=canonical(model_view(task)):
        trace["error"]="ABSTAIN_MODEL_VIEW_ORIGINAL_MISMATCH"
        return finish()
    kind=visible_family(view)
    if kind is None:
        trace["error"]="ABSTAIN_UNKNOWN_SEMANTIC_SCHEMA"
        return finish()
    def model_generate(messages):
        if core is None:
            raise ValueError("ABSTAIN_NO_FROZEN_MODEL")
        identity=core.identity
        if identity.get("weights_frozen") is not True or identity.get("accelerator_class") is not True:
            raise ValueError("ABSTAIN_UNATTESTED_MODEL")
        prompt_tokens=core.count_tokens(messages,False)
        if type(prompt_tokens) is not int or prompt_tokens>=budget.context_tokens:
            raise ValueError("ABSTAIN_CONTEXT_BUDGET")
        if left()<=0:raise TimeoutError("QUERY_DEADLINE")
        allowance=min(budget.per_call_tokens,budget.output_tokens,budget.context_tokens-prompt_tokens)
        if allowance<1:raise ValueError("ABSTAIN_NO_OUTPUT_BUDGET")
        trace["model_calls"]+=1
        trace["token_accounting_complete"]=False
        rec=core.generate(messages,allowance,False,left())
        trace["events"].append({"kind":"model_call","receipt":rec})
        if sha(core.identity)!=trace["model_identity_sha256"]:
            raise ValueError("FROZEN_MODEL_IDENTITY_DRIFT")
        if rec.get("thinking_enabled") is not False:
            raise ValueError("THINKING_DISABLE_CONTRACT_VIOLATION")
        if rec.get("input_tokens")!=prompt_tokens or type(rec.get("output_tokens")) is not int:
            raise ValueError("TOKEN_ACCOUNTING_INCOMPLETE")
        if not 0<=rec["output_tokens"]<=allowance or rec.get("deadline_reached"):
            raise ValueError("GENERATION_BUDGET_OR_DEADLINE")
        trace["input_tokens"]+=prompt_tokens
        trace["output_tokens"]+=rec["output_tokens"]
        trace["token_accounting_complete"]=True
        trace["peak_accelerator_memory_bytes"]=max(
            trace["peak_accelerator_memory_bytes"],int(rec.get("peak_accelerator_memory_bytes",0)))
        return rec["raw"]
    try:
        if arm=="DIRECT":
            candidate=parse_direct(model_generate(final_prompt(view,kind)),kind)
        else:
            pool=ToolPool(task,private,budget)
            public=view["public"]
            if arm=="NEUMANN":
                proposed={"family":kind}
                if kind=="math_logic":proposed["expression"]=public["expression"]
                elif kind=="constraint_planning":
                    proposed.update(domains=public["domains"],constraints=public["constraints"])
                else:proposed["requirement"]=public["requirement"]
                cert=reduce_original(task,proposed)
                if cert.get("original_task_sha256")!=sha(task):
                    raise ValueError("ABSTAIN_CERTIFICATE_ORIGINAL_MISMATCH")
                trace["representation_certified"]=True
                trace["events"].append({"kind":"representation","sha256":sha(cert)})
                source=cert["ir"]
            else:source=public
            if kind=="math_logic":
                candidate=pool.call("arithmetic",{
                    "expression":source["expression"],"bindings":source["bindings"]},min(left(),budget.tool_ms))
                trace["tool_calls"]+=1
            elif kind=="constraint_planning":
                out=pool.call("csp",{
                    "spec":{"domains":source["domains"],"constraints":source["constraints"]},
                    "strategy":"mrv"},min(left(),budget.tool_ms))
                trace["tool_calls"]+=1
                candidate=out["assignment"]
            else:
                candidate=parse_source(model_generate(coding_prompt(view)))
                examples=public.get("examples",[])
                if examples:
                    before=perf_counter_ns()
                    results=pool.call("python",{
                        "source":candidate,"inputs":[ex["input"] for ex in examples]
                    },min(left(),budget.tool_ms))
                    trace["tool_calls"]+=1
                    if (len(results)!=len(examples) or
                        any(canonical(a)!=canonical(ex["output"]) for a,ex in zip(results,examples))):
                        raise ValueError("PUBLIC_EXAMPLE_REPLAY_FAILED")
                    trace["events"].append({"kind":"public_replay",
                         "ms":(perf_counter_ns()-before)/1e6,
                         "examples":len(examples)})
        trace["answer"]=candidate
        if left()<=0:raise TimeoutError("QUERY_DEADLINE")
        trace["checker_calls"]+=1
        trace["accepted"]=bool(verify_original(task,candidate,private,min(budget.tool_ms,left())))
        if not trace["accepted"]:
            trace["error"]="ORIGINAL_CHECKER_REJECTED"
    except Exception as exc:
        trace["accepted"]=False
        trace["error"]=type(exc).__name__+": "+str(exc)
    return finish()
