"""Q3 open-code inventor: learned proposals, source counterexamples, safe execution.

Unlike the earlier fixed DSL / object ontologies, a generative policy proposes
a COMPLETE executable algorithm in a general Python language. New operators
are not added by hand when a new mathematical domain appears.

Neither the model nor its critic reads TARGET gold. A SOURCE-only validation
set can falsify the proposed program. Candidates are executed only inside
an explicitly isolated Docker container; no Docker means fail closed.

This architecture itself is not global autonomous invention proof. Model weights
must be trained/adapted separately using original SOURCE traces, and FIRST
external-origin heldouts must be measured with a strongest comparable baseline.
"""
from __future__ import annotations
import ast
from dataclasses import dataclass
import hashlib
import json
import re
import shutil
import subprocess
from time import perf_counter_ns
from .q3_prompt_contract import source_discovery_prompt

def source_same_value(actual, expected):
    """Original-source JSON equality, preserving bool/int output distinctions."""
    try:
        return json.dumps(
            actual,sort_keys=True,separators=(",",":"),
            ensure_ascii=True,allow_nan=False
        )==json.dumps(
            expected,sort_keys=True,separators=(",",":"),
            ensure_ascii=True,allow_nan=False)
    except (TypeError,ValueError,OverflowError):
        return False


OPS=(
    ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Return,ast.Assign,
    ast.AugAssign,ast.Expr,ast.If,ast.For,ast.While,ast.Break,ast.Continue,
    ast.Pass,ast.Name,ast.Load,ast.Store,ast.Constant,ast.List,ast.Tuple,
    ast.Dict,ast.Set,ast.ListComp,ast.DictComp,ast.SetComp,ast.GeneratorExp,
    ast.comprehension,ast.Subscript,ast.Slice,ast.Starred,ast.BinOp,
    ast.UnaryOp,ast.BoolOp,ast.Compare,ast.IfExp,ast.Attribute,ast.Call,
    ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,
    ast.USub,ast.UAdd,ast.Not,ast.And,ast.Or,ast.Eq,ast.NotEq,
    ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.In,ast.NotIn,
    ast.keyword,ast.Lambda,ast.BitAnd,ast.BitOr,ast.BitXor,
    ast.LShift,ast.RShift,ast.Is,ast.IsNot,
)
BUILTINS=("len","range","enumerate","zip","min","max","sum","abs",
          "int","str","bool","list","tuple","dict","set","sorted",
          "reversed","all","any","isinstance","float",
          "round","ord","chr","divmod","pow","map","filter")
METHODS=("append","extend","insert","reverse","sort","copy","count",
         "index","get","items","keys","values","pop",
         "lower","upper","strip","lstrip","rstrip","replace","split",
         "join","isalnum","isalpha","isdigit","isnumeric",
         "startswith","endswith","find","rfind")

class UnsafeProposal(ValueError):pass

_CODE_START=re.compile(r"^def\s+transform\s*\(\s*x\s*\)\s*:")

def validate_code(text):
    """Only simple non-reflective transform(x) accepted; not a sandbox."""
    if not isinstance(text,str) or len(text)>6000 or not text.strip():
        raise UnsafeProposal("empty or oversized proposal")
    code=text.strip()
    fence=chr(96)*3
    if code.startswith(fence):
        lines=code.splitlines()
        if len(lines)<3 or lines[-1].strip()!=fence:
            raise UnsafeProposal("invalid model code fence")
        code="\n".join(lines[1:-1])
    elif not code.startswith("def transform"):
        # If the model adds a plain-language preamble, extract ONLY its
        # unique transform function. This is never arbitrary exec: the
        # extracted code is still AST-validated and sandboxed.
        lines=code.splitlines()
        starts=[i for i,line in enumerate(lines)
                if _CODE_START.match(line)]
        if len(starts)!=1:
            raise UnsafeProposal("a single def transform(x) is required")
        a=starts[0]
        b=len(lines)
        for j in range(a+1,len(lines)):
            if (lines[j].strip() and not lines[j].startswith((" ","\t","#"))):
                b=j
                break
        # Explanatory natural-language text may be discarded, but actual
        # top-level executable Python may NEVER be silently removed.
        # This prevents stripping malicious "import os" or "raise ..."
        # before/after an otherwise benign transform function.
        for extra in ("\n".join(lines[:a]),"\n".join(lines[b:])):
            if not extra.strip():
                continue
            try:
                external=ast.parse(extra)
            except SyntaxError:
                continue  # non-code model commentary only
            if external.body:
                raise UnsafeProposal("unexpected executable source outside transform")
        code="\n".join(lines[a:b]).strip()
    try:
        tree=ast.parse(code)
    except SyntaxError as exc:
        raise UnsafeProposal("source syntax invalid") from exc
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef):
        raise UnsafeProposal("single transform function only")
    fn=tree.body[0]
    if (fn.name!="transform" or fn.decorator_list or fn.returns is not None
            or len(fn.args.args)!=1 or fn.args.args[0].arg!="x"
            or fn.args.defaults or fn.args.kwonlyargs
            or fn.args.vararg or fn.args.kwarg):
        raise UnsafeProposal("transform(x) signature only")
    helpers={
        n.name for n in ast.walk(fn)
        if isinstance(n,ast.FunctionDef) and n is not fn
    }
    if any(x.startswith("_") or "__" in x for x in helpers):
        raise UnsafeProposal("reserved helper function name")
    for n in ast.walk(tree):
        if not isinstance(n,OPS):
            raise UnsafeProposal("forbidden syntax: "+type(n).__name__)
        if isinstance(n,ast.FunctionDef) and n is not fn and (
                n.decorator_list or n.returns is not None or
                n.args.defaults or n.args.kw_defaults or
                n.args.vararg or n.args.kwarg or
                any(a.annotation is not None for a in n.args.args)):
            raise UnsafeProposal("non-pure helper function signature")
        if isinstance(n,ast.Name) and (
                (n.id.startswith("_") and n.id!="_") or "__" in n.id):
            raise UnsafeProposal("reflection/private names forbidden")
        if isinstance(n,ast.Attribute) and n.attr not in METHODS:
            raise UnsafeProposal("method/reflection forbidden")
        if isinstance(n,ast.Call):
            if isinstance(n.func,ast.Name):
                if n.func.id not in BUILTINS and n.func.id not in helpers:
                    raise UnsafeProposal("unknown builtin or helper")
            elif isinstance(n.func,ast.Attribute):
                if n.func.attr not in METHODS:
                    raise UnsafeProposal("unknown container method")
            else:
                raise UnsafeProposal("callable expression forbidden")
            if any(k.arg is None or k.arg.startswith("_")
                   for k in n.keywords):
                raise UnsafeProposal("dynamic/private keywords forbidden")
        if isinstance(n,ast.comprehension) and n.is_async:
            raise UnsafeProposal("async forbidden")
        if isinstance(n,ast.Constant):
            v=n.value
            if (type(v) not in (int,float,bool,str,type(None))
                    or (type(v) is str and len(v)>1000)
                    or (type(v) in (int,float) and abs(v)>1000000)):
                raise UnsafeProposal("unbounded constant")
    if not any(isinstance(n,ast.Return) for n in ast.walk(fn)):
        raise UnsafeProposal("source return required")
    return code

WORKER=r"""
import builtins,json,sys
payload=json.loads(sys.stdin.read())
good={name:getattr(builtins,name) for name in (
 'len','range','enumerate','zip','min','max','sum','abs','int','str',
 'bool','list','tuple','dict','set','sorted','reversed','all','any',
 'isinstance','float','round','ord','chr','divmod','pow','map','filter')}
namespace={'__builtins__':good}
try:
 exec(compile(payload['code'],'<generated>','exec'),namespace,namespace)
 outputs=[]
 errors=[]
 for x in payload['inputs']:
  try:
   result=namespace['transform'](x)
   json.dumps(result)
   outputs.append(result)
   errors.append(None)
  except Exception as error:
   frame=error.__traceback__
   while frame is not None and frame.tb_next is not None:
    frame=frame.tb_next
   lineno=frame.tb_lineno if frame is not None else 0
   outputs.append(None)
   errors.append({
     'type':type(error).__name__[:80],
     'message':str(error)[:160],
     'line':lineno
   })
 print(json.dumps({'ok':True,'outputs':outputs,'errors':errors},
                  separators=(',',':')))
except Exception:
 print(json.dumps({'ok':False,'outputs':[],'errors':[]},
                  separators=(',',':')))
"""

@dataclass(frozen=True)
class Execution:
    status:str
    outputs:tuple
    wall_ms:float
    errors:tuple=()

class IsolatedPython:
    def __init__(self,*,image="python:3.11-alpine",max_seconds=5):
        if not 1<=max_seconds<=30:raise ValueError("time cap required")
        self.image=image
        self.max_seconds=max_seconds

    def evaluate(self,code,inputs):
        start=perf_counter_ns()
        try:
            source=validate_code(code)
        except UnsafeProposal:
            return Execution("ABSTAIN_UNSAFE_SYNTAX",(),0)
        if shutil.which("docker") is None:
            return Execution("ABSTAIN_NO_SANDBOX",(),0)
        if not 1<=len(inputs)<=64:
            return Execution("ABSTAIN_INPUT_SIZE",(),0)
        payload=json.dumps({"code":source,"inputs":inputs},
                           separators=(",",":"),ensure_ascii=True)
        if len(payload)>200000:
            return Execution("ABSTAIN_INPUT_SIZE",(),0)
        command=["docker","run","--rm","-i","--network=none","--read-only",
                 "--cap-drop=ALL","--security-opt=no-new-privileges",
                 "--pids-limit=32","--memory=192m","--memory-swap=192m",
                 "--cpus=1","--user=65534:65534",
                 "--tmpfs=/tmp:rw,noexec,nosuid,size=16m",
                 self.image,"python","-I","-S","-c",WORKER]
        try:
            p=subprocess.run(command,input=payload,text=True,
                             capture_output=True,check=False,
                             timeout=self.max_seconds)
        except (OSError,subprocess.TimeoutExpired):
            return Execution("ABSTAIN_TIMEOUT_OR_SANDBOX",(),
                             (perf_counter_ns()-start)/1e6)
        if p.returncode!=0 or len(p.stdout)>200000:
            return Execution("ABSTAIN_SANDBOX_EXIT",(),
                             (perf_counter_ns()-start)/1e6)
        try:
            answer=json.loads(p.stdout.strip())
        except (TypeError,ValueError):
            return Execution("ABSTAIN_PROTOCOL",(),
                             (perf_counter_ns()-start)/1e6)
        if (answer.get("ok") is not True or
                not isinstance(answer.get("outputs"),list) or
                len(answer["outputs"])!=len(inputs) or
                not isinstance(answer.get("errors"),list) or
                len(answer["errors"])!=len(inputs)):
            return Execution("ABSTAIN_RUNTIME_ERROR",(),
                             (perf_counter_ns()-start)/1e6)
        errs=tuple(answer["errors"])
        if any(x is not None and (
                not isinstance(x,dict) or
                type(x.get("type")) is not str or
                type(x.get("message")) is not str or
                type(x.get("line")) is not int)
               for x in errs):
            return Execution("ABSTAIN_PROTOCOL",(),
                             (perf_counter_ns()-start)/1e6)
        return Execution(
            "EXECUTED_WITH_ERRORS" if any(x is not None for x in errs)
            else "EXECUTED",
            tuple(answer["outputs"]),
            (perf_counter_ns()-start)/1e6,errs)


@dataclass(frozen=True)
class Attempt:
    sha256:str
    source_correct:int
    source_total:int
    status:str
    iteration:int
    program:str|None=None

@dataclass(frozen=True)
class Discovery:
    status:str
    program:str|None
    frozen_sha256:str|None
    attempts:tuple[Attempt,...]
    independent_source_checks:int
    verified:bool

    def apply(self,x,runner):
        if not self.verified or self.program is None:
            raise UnsafeProposal("unverified source program")
        outcome=runner.evaluate(self.program,[x])
        if outcome.status!="EXECUTED":
            raise UnsafeProposal("program failed isolated execution")
        return outcome.outputs[0]


class GenerativeProgramInventor:
    """Model-policy -> new Python algorithm -> source refutation -> revision."""

    def __init__(self,policy,runner,*,max_proposals=8,
                 rich_runtime_feedback=True,
                 reveal_independent_counterexample=True):
        if not 1<=max_proposals<=64:raise ValueError("finite source budget")
        self.policy=policy
        self.runner=runner
        self.max_proposals=max_proposals
        self.rich_runtime_feedback=bool(rich_runtime_feedback)
        self.reveal_independent_counterexample=bool(
            reveal_independent_counterexample)

    def discover(self,source_pairs,*,independent_source_checks,
                 method_context=""):
        train=tuple(source_pairs)
        checks=tuple(independent_source_checks)
        if not train or not checks or len(train)>32 or len(checks)>32:
            raise ValueError("source pairs and independent verifier required")
        # "Independent SOURCE" must mean new input information, not
        # the same observed label checked a second time.
        train_inputs={json.dumps(x,sort_keys=True,separators=(",",":"))
                      for x,y in train}
        check_inputs=[json.dumps(x,sort_keys=True,separators=(",",":"))
                      for x,y in checks]
        if len(check_inputs)!=len(set(check_inputs)) or (
                train_inputs & set(check_inputs)):
            raise ValueError("SOURCE verifier must be disjoint from training")
        prompt=source_discovery_prompt(train,method_context=method_context)
        seen=set()
        receipts=[]
        for step in range(self.max_proposals):
            raw=None
            try:
                raw=self.policy.propose(prompt)
                code=validate_code(raw)
            except (UnsafeProposal,ValueError,TypeError) as exc:
                # The previous policy threw away 9/27 original candidate
                # proposals as REJECTED but supplied zero preflight detail.
                # This is source-independent compiler feedback, never
                # information about a withheld target answer.
                raw_hash=(hashlib.sha256(raw.encode()).hexdigest()
                          if isinstance(raw,str) else "")
                receipts.append(Attempt(
                    raw_hash,0,len(train),"REJECTED",step,
                    raw[:3000] if isinstance(raw,str) else None))
                prompt+=(
                    "\nYour proposed code failed the deterministic Python "
                    "preflight. Fix the code while preserving its hypothesized "
                    "algorithm. Error: "+type(exc).__name__+": "+
                    str(exc)[:220]+"\n")
                continue
            sha=hashlib.sha256(code.encode()).hexdigest()
            if sha in seen:
                prompt+="\nYou repeated a disproven proposal. Invent new code."
                continue
            seen.add(sha)
            result=self.runner.evaluate(code,[x for x,y in train])
            source_executed=result.status in (
                "EXECUTED","EXECUTED_WITH_ERRORS")
            correct=sum(
                source_executed and error is None and source_same_value(got,y)
                for got,error,(_,y) in zip(
                    result.outputs,result.errors,train))
            if not self.rich_runtime_feedback and result.status=="EXECUTED_WITH_ERRORS":
                correct=0  # historical opaque runtime-error feedback ablation
            receipts.append(Attempt(sha,correct,len(train),result.status,step,code))
            if correct==len(train):
                final=self.runner.evaluate(code,[x for x,y in checks])
                if final.status=="EXECUTED" and all(
                        source_same_value(got,y) for got,(_,y) in zip(final.outputs,checks)):
                    return Discovery("SOURCE_VERIFIED_OPEN_PROGRAM",code,sha,
                                     tuple(receipts),len(checks),True)
                # A failed disjoint SOURCE verifier is a SOURCE label, not
                # any hidden TARGET answer. Previously, this true new
                # observation was discarded and the model was told only
                # "refuted". Give an explicit causal witness to the next
                # synthesis attempt. The ablation can retain the old opaque
                # feedback, while both arms see identical first proposals.
                if self.reveal_independent_counterexample and (
                        final.status in ("EXECUTED","EXECUTED_WITH_ERRORS")):
                    witness=[]
                    for got,error,(x,y) in zip(
                            final.outputs,final.errors,checks):
                        if error is not None or not source_same_value(got,y):
                            witness.append({
                                "source_input":x,
                                "source_expected":y,
                                "previous_observed":got,
                                "runtime_error":error})
                    prompt+=(
                        "\nYour proposed algorithm passed the first SOURCE "
                        "examples but FAILED on NEW SOURCE observations. "
                        "Identify the missing invariant and revise the "
                        "algorithm. New SOURCE counterexamples:\n"+
                        json.dumps(witness[:3],ensure_ascii=True)[:3500])
                else:
                    prompt+=(
                        "\nAn independent SOURCE verifier refuted your "
                        "program. Propose a different general algorithm.")
            else:
                errors=[]
                if source_executed and self.rich_runtime_feedback:
                    for got,error,(x,y) in zip(
                            result.outputs,result.errors,train):
                        if error is not None:
                            errors.append({
                                "input":x,"expected":y,
                                "runtime_failure":error})
                        elif not source_same_value(got,y):
                            errors.append({
                                "input":x,"expected":y,"got":got})
                else:
                    errors=["ABSTAIN_RUNTIME_ERROR" if source_executed
                            else result.status]
                prompt+=(
                    "\nYour last source program was falsified. "
                    "Fix the causal rule, not individual examples. Errors:\n"+
                    json.dumps(errors[:3],ensure_ascii=True)[:3500])
        return Discovery("ABSTAIN_NO_SOURCE_PROGRAM",None,None,
                         tuple(receipts),len(checks),False)


def source_training_example(source,discovery):
    """Certified original SOURCE episodes only. Never target gold."""
    if not discovery.verified:raise UnsafeProposal("source certificate absent")
    return {
        "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
        "pairs":list(source),"program":discovery.program,
        "sha256":discovery.frozen_sha256,
        "independent_checks":discovery.independent_source_checks,
        "provenance":"ORIGINAL_SOURCE_ONLY"}
