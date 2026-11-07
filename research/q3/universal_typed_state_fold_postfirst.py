"""Q3 post-first: one polymorphic, typed universal state fold.

This deletes a restrictive hypothesis from #715:
  output has to have the same container type as input.
Instead a SINGLE generic loop is typed by the output examples; its initial
state and update expression are synthesized from a generic tiny instruction
basis, not a hand-written task function or domain-specific solver.

This is a post-exposure DEVELOPMENT study: OpenAI HumanEval original 164
task IDs were already accessed in the #715 FIRST, so any new metrics here
are NOT independent FIRST. The typed VM and expression enumerator are
still HUMAN WRITTEN and do not satisfy unrestricted Q3 self-invention.
"""
from __future__ import annotations
from hashlib import sha256
import itertools,json,time,math
from research.q3.causal_learned_grammar_inventor import (
    decompose_examples,solve as old_solve,run_operator as old_run
)

def cprint(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)

def same(a,b):
    if type(b) is float and type(a) in (int,float):
        return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12)
    return type(a) is type(b) and a==b

def expression(ast,state,item):
    tag=ast[0]
    if tag=="s":return state
    if tag=="x":return item
    if tag=="lit":return ast[1]
    if tag=="len":
        v=expression(ast[1],state,item)
        if type(v) not in (list,tuple,str):raise ValueError("NOT_SEQUENCE")
        return len(v)
    if tag=="not":return not expression(ast[1],state,item)
    if tag=="if":
        return expression(ast[2] if expression(ast[1],state,item)
                          else ast[3],state,item)
    a=expression(ast[1],state,item)
    b=expression(ast[2],state,item)
    if tag=="eq":return type(a) is type(b) and a==b
    if tag=="lt":
        if type(a) not in (int,float) or type(b) not in (int,float):
            raise ValueError("NONNUMERIC_LT")
        return a<b
    if tag=="mod":
        if type(a) is not int or type(b) is not int or not b:
            raise ValueError("NONINTEGER_MOD")
        return a%b
    if tag in ("add","sub","mul","min","max"):
        if type(a) not in (int,float) or type(b) not in (int,float):
            raise ValueError("NUMERIC_REQUIRED")
        if tag=="add":return a+b
        if tag=="sub":return a-b
        if tag=="mul":return a*b
        if tag=="min":return min(a,b)
        if tag=="max":return max(a,b)
    if tag=="and":
        if type(a) is not bool or type(b) is not bool:
            raise ValueError("BOOLEAN_REQUIRED")
        return a and b
    if tag=="or":
        if type(a) is not bool or type(b) is not bool:
            raise ValueError("BOOLEAN_REQUIRED")
        return a or b
    if tag=="append":
        if type(a) is str and type(b) is str and len(b)==1:
            return a+b
        if type(a) is list:return a+[b]
        if type(a) is tuple:return a+(b,)
    raise ValueError("UNKNOWN_OR_UNTYPED_COMBINATOR")

def run(program,args):
    if program is None:return None
    try:
        if len(args)!=1:return None
        xs=args[0]
        if type(xs) not in (list,tuple,str) or len(xs)>1024:
            return None
        if program[0]!="fold_state":
            return None
        acc=program[1]
        update=program[2]
        for item in xs:
            acc=expression(update,acc,item)
            if type(acc) in (int,float) and not math.isfinite(acc):
                return None
            if type(acc) in (int,float) and abs(acc)>1e12:
                return None
            if type(acc) in (list,tuple,str) and len(acc)>1024:
                return None
            if type(acc) not in (str,list,tuple,int,float,bool):
                return None
        return acc
    except (ValueError,TypeError,KeyError,IndexError,RecursionError,
            OverflowError,ZeroDivisionError):
        return None

def seed_values(outputs):
    ty=type(outputs[0])
    if any(type(x) is not ty for x in outputs):return []
    if ty is int:return [0,1]
    if ty is float:return [0.0,1.0]
    if ty is bool:return [False,True]
    if ty in (list,tuple,str):return [ty()]
    return []

def expressions_for(source_type,output_type,seen_tokens):
    s=["s"];x=["x"];zero=["lit",0];one=["lit",1]
    nums=[x,zero,one,["len",x]]
    if output_type in (int,float):
        # A typed tree grammar of general arithmetic operations, NOT named
        # sum/product/count/etc. The operation order is a fixed MDL prior.
        for lhs,rhs in [
            (s,x),(s,one),(s,zero),(x,s),
            (s,["len",x])]:
            for op in ("add","mul","sub","min","max"):
                yield [op,lhs,rhs]
        # 2-level conditional state updates, parametrized by observed
        # scalar token roles, not task labels. This is an expression AST.
        observed=[v for v in seen_tokens if type(v) in (int,float,str,bool)]
        for sym in observed[:12]:
            pred=["eq",x,["lit",sym]]
            for op in ("add","mul"):
                updated=[op,s,one]
                yield ["if",pred,updated,s]
                yield ["if",pred,s,updated]
        if source_type in (list,tuple,str):
            for cutoff in (0,1,2):
                cond=["lt",x,["lit",cutoff]]
                yield ["if",cond,["add",s,one],s]
                yield ["if",cond,s,["add",s,one]]
            for k in (2,3,4,5):
                for residue in range(k):
                    pred=["eq",["mod",x,["lit",k]],
                          ["lit",residue]]
                    yield ["if",pred,["add",s,one],s]
    if output_type is bool:
        for sym in seen_tokens[:16]:
            p=["eq",x,["lit",sym]]
            for op in ("and","or"):
                yield [op,s,p]
                yield [op,s,["not",p]]
        for threshold in (-1,0,1,2):
            p=["lt",x,["lit",threshold]]
            yield ["or",s,p]
            yield ["and",s,p]
    if output_type in (list,tuple,str):
        yield ["append",s,x]
        for sym in seen_tokens[:12]:
            p=["eq",x,["lit",sym]]
            yield ["if",p,s,["append",s,x]]
            yield ["if",p,["append",s,x],s]
        for k in (2,3):
            for residue in range(k):
                p=["eq",["mod",x,["lit",k]],["lit",residue]]
                yield ["if",p,s,["append",s,x]]
                yield ["if",p,["append",s,x],s]

def synthesis(examples,budget=5000):
    t0=time.perf_counter_ns()
    if len(examples)<2:
        return {"program":None,"attempts":0,"status":"ABSTAIN"}
    if any(len(args)!=1 or type(args[0]) not in (list,tuple,str)
           for args,y in examples):
        return {"program":None,"attempts":0,"status":"ABSTAIN_INPUT"}
    out_type=type(examples[0][1])
    seeds=seed_values([y for args,y in examples])
    if not seeds:return {"program":None,"attempts":0,"status":"ABSTAIN_OUTPUT"}
    # Generic structure probes select types/available literal atoms.
    tokens=[]
    for args,y in examples:
        if len(args[0])>1024:return {"program":None,"attempts":0,
                                      "status":"ABSTAIN_SIZE"}
        for tok in args[0]:
            if type(tok) in (int,float,str,bool) and tok not in tokens:
                tokens.append(tok)
    checked=0;hashes=set()
    for update in expressions_for(type(examples[0][0]),out_type,tokens):
        for seed in seeds:
            p=["fold_state",seed,update]
            key=cprint(p)
            if key in hashes:continue
            hashes.add(key)
            checked+=1
            if all(same(run(p,args),goal) for args,goal in examples):
                return {"program":p,"attempts":checked,
                        "status":"GENERATED_GENERIC_FOLD_AST",
                        "wall_ms":round((time.perf_counter_ns()-t0)/1e6,5)}
            if checked>=budget:
                return {"program":None,"attempts":checked,
                        "status":"ABSTAIN_BUDGET",
                        "wall_ms":round((time.perf_counter_ns()-t0)/1e6,5)}
    return {"program":None,"attempts":checked,
            "status":"ABSTAIN_REPRESENTATION",
            "wall_ms":round((time.perf_counter_ns()-t0)/1e6,5)}
