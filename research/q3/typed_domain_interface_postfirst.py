"""Q3 typed domain generalization, post-FIRST development of type interface.

Reuses the EXACT pre-existing generic AST anti-unifier, source proof ledger,
and observable executor from typed_cross_domain_meta_engine. Extends the
human-written frontend to Bool and Int outputs; this is NOT invented by AI.
No task-specific rule names or IDs are used for synthesis.
"""
from __future__ import annotations
import time
import typed_cross_domain_meta_engine as old

def decode_any(raw):
    forms=old.parse(raw)
    synth=[x for x in forms if isinstance(x,list) and x and x[0]=="synth-fun"]
    if len(synth)!=1 or len(synth[0])<5:raise ValueError("UNSUPPORTED_SYNTH_COUNT")
    fun=synth[0];name=fun[1];params=fun[2]
    if (not isinstance(params,list) or not params or len(params)>6 or
        not all(isinstance(a,list) and len(a)==2 and a[1]=="String" for a in params)):
        raise ValueError("UNSUPPORTED_INPUT_TYPE")
    target=fun[3]
    if target not in ("String","Int","Bool"):raise ValueError("UNSUPPORTED_OUTPUT_TYPE")
    words=list(old.walk(fun[4:]))
    literals=sorted({x[1] for x in words if isinstance(x,tuple) and x[0]=="Q"},key=lambda q:(len(q),q))
    ops={x for x in words if isinstance(x,str)}
    nums=sorted({int(x) for x in ops if x.lstrip("-").isdigit() and abs(int(x))<=10})
    if 0 not in nums:nums=[0]+nums
    records=[]
    def out_value(x):
        if target=="String":
            if isinstance(x,tuple) and x[0]=="Q":return x[1]
        elif target=="Bool":
            if x=="true":return True
            if x=="false":return False
        elif target=="Int":
            if isinstance(x,str) and x.lstrip("-").isdigit():return int(x)
        raise ValueError("COMPLEX_REFERENCE_EXPRESSION")
    for row in forms:
        if not isinstance(row,list) or len(row)<2 or row[0]!="constraint":continue
        e=row[1]
        if not isinstance(e,list) or len(e)!=3 or e[0]!="=":continue
        lhs,rhs=e[1],e[2]
        if not (isinstance(lhs,list) and lhs and lhs[0]==name):
            if isinstance(rhs,list) and rhs and rhs[0]==name:
                lhs,rhs=rhs,lhs
            else:continue
        if len(lhs)!=len(params)+1 or not all(isinstance(x,tuple) and x[0]=="Q" for x in lhs[1:]):
            continue
        try:output=out_value(rhs)
        except ValueError:continue
        records.append((tuple(x[1] for x in lhs[1:]),output))
    dedup={};conflicts=[]
    for ins,out in records:
        if ins in dedup and dedup[ins]!=out:conflicts.append(ins)
        dedup[ins]=out
    if conflicts:raise ValueError("CONTRADICTORY_EXAMPLES")
    if not dedup:raise ValueError("NO_LITERAL_CONSTRAINTS")
    return {"nargs":len(params),"output":target,"ops":sorted(ops),
            "constants":literals,"numbers":nums,
            "examples":list(dedup.items()),"source_constraints":len(records)}

def candidate_typed(task):
    tag=task["output"];ops=set(task["ops"])
    args=[["arg",i] for i in range(task["nargs"])]
    const=[["lit",c] for c in task["constants"] if len(c)<=6]
    base=[]
    if tag=="String":return old.candidate_library(task,limit=3500)
    if tag=="Bool":
        if "true" in ops:base.append(["bool",True])
        if "false" in ops:base.append(["bool",False])
        for a in args:
            for v in const:
                if "str.contains" in ops:base.append(["contains",a,v])
                if "str.prefixof" in ops:base.append(["prefix",a,v])
                if "str.suffixof" in ops:base.append(["suffix",a,v])
                if "=" in ops:base.append(["str_eq",a,v])
            if "=" in ops and "str.len" in ops:
                for n in task["numbers"]:
                    base.append(["int_eq",["len",a],["num",n]])
    elif tag=="Int":
        for a in args:
            if "str.len" in ops:base.append(["len",a])
            if "str.indexof" in ops:
                for v in const:
                    if v[1]:base.append(["index",a,v,["num",0]])
        base += [["num",n] for n in task["numbers"]]
        if "str.len" in ops and "+" in ops:
            for a in args:
                for n in task["numbers"]:
                    base.append(["plus",["len",a],["num",n]])
        if "str.len" in ops and "-" in ops:
            for a in args:
                for n in task["numbers"]:
                    base.append(["minus",["len",a],["num",n]])
    seen=set();result=[]
    for p in base:
        k=old.canonical(p)
        if k in seen:continue
        seen.add(k);result.append(p)
    return result

def execute(p,x):
    if not isinstance(p,list):raise ValueError("UNKNOWN_AST")
    if p[0]=="bool":return p[1]
    if p[0]=="str_eq":return old.ev(p[1],x)==old.ev(p[2],x)
    if p[0]=="int_eq":return old.ev(p[1],x)==old.ev(p[2],x)
    return old.ev(p,x)

def score_any(p,pairs):
    if p is None:return {"submitted":False,"exact":False,"hits":0,"total":len(pairs)}
    hits=0
    for a,y in pairs:
        try:
            v=execute(p,a)
            hits+=int(type(v)==type(y) and v==y)
        except (ValueError,TypeError,IndexError,KeyError,OverflowError):pass
    return {"submitted":True,"exact":hits==len(pairs),"hits":hits,"total":len(pairs)}

def search(task,train,allow_branch):
    start=time.perf_counter_ns()
    xs=[x for x,y in train];goal=tuple(y for x,y in train)
    forms=candidate_typed(task)
    observed={};pool=[]
    for p in forms:
        try:sig=tuple(execute(p,x) for x in xs)
        except (TypeError,ValueError,IndexError,OverflowError):continue
        if sig not in observed:
            observed[sig]=p;pool.append((p,sig))
    checks=len(pool)
    for p,sig in pool:
        if sig==goal:
            return {"ast":p,"status":"TYPED_BASE","checks":checks,
                    "wall_ms":(time.perf_counter_ns()-start)/1e6}
    if allow_branch and "ite" in task["ops"]:
        masks=[]
        for cond in old.predicates(task):
            try:v=tuple(bool(old.ev(cond,x)) for x in xs)
            except Exception:continue
            if v in masks:continue
            masks.append(v)
            yes=[i for i,b in enumerate(v) if b];no=[i for i,b in enumerate(v) if not b]
            if not yes or not no:continue
            a=[p for p,s in pool if all(s[i]==goal[i] for i in yes)]
            b=[p for p,s in pool if all(s[i]==goal[i] for i in no)]
            checks+=2*len(pool)
            if a and b:
                pa=min(a,key=lambda q:(old.size(q),old.canonical(q)))
                pb=min(b,key=lambda q:(old.size(q),old.canonical(q)))
                node=["ite",cond,pa,pb]
                if score_any(node,train)["exact"]:
                    return {"ast":node,"status":"TYPED_BRANCH",
                            "checks":checks,
                            "wall_ms":(time.perf_counter_ns()-start)/1e6}
    return {"ast":None,"status":"ABSTAIN","checks":checks,
            "wall_ms":(time.perf_counter_ns()-start)/1e6}

def memory_search_any(rules,task,train,budget=500):
    if task["output"]!="String":
        return {"ast":None,"status":"ABSTAIN_CROSS_TYPE_UNSUPPORTED",
                "checks":0,"wall_ms":0.0}
    start=time.perf_counter_ns();n=0
    for p in old.candidates_from_templates(rules,task,cap=budget):
        n+=1
        if score_any(p,train)["exact"]:
            return {"ast":p,"status":"LEARNED_TEMPLATE",
                    "checks":n,"wall_ms":(time.perf_counter_ns()-start)/1e6}
    return {"ast":None,"status":"ABSTAIN_TEMPLATE",
            "checks":n,"wall_ms":(time.perf_counter_ns()-start)/1e6}
