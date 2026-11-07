"""Q3 post-first causal root-cause correction: typed constructor-hole binding.

Prior source grammar contains a hole in the output of (str.indexof ...),
whose type is Int, but v1 bound it to String-producing ASTs. Here generic
contextual type inference supplies grammatical Int/String/Bool AST values.
No target task names or target solutions are used inside this binder.
Human implemented: typing rules, candidate enumerator, prior anti-unifier.
"""
from __future__ import annotations
import itertools,time
import typed_cross_domain_meta_engine as core
import typed_domain_interface_postfirst as typed

CHILD_TYPES={
    "substr":("String","Int","Int"),
    "at":("String","Int"),
    "index":("String","String","Int"),
    "len":("String",),
    "cat":("String","String"),
    "replace":("String","String","String"),
    "plus":("Int","Int"),
    "minus":("Int","Int"),
    "contains":("String","String"),
    "prefix":("String","String"),
    "suffix":("String","String"),
    "ite":("Bool","String","String"),
    "arg":("ArgIndex",),
    "lit":("StringLiteral",),
    "num":("IntLiteral",)
}

def holes_with_types(node,expected,types):
    if isinstance(node,dict) and set(node)=={"hole"}:
        i=node["hole"]
        if i in types and types[i]!=expected:raise ValueError("CONTRADICTORY_HOLE_TYPES")
        types[i]=expected;return
    if isinstance(node,list) and node:
        op=node[0]
        if op not in CHILD_TYPES or len(node)-1!=len(CHILD_TYPES[op]):
            raise ValueError("BAD_TEMPLATE_OPERATOR")
        for child,kind in zip(node[1:],CHILD_TYPES[op]):
            holes_with_types(child,kind,types)

def scalar_grammar(task):
    if task["output"] not in ("String","Int","Bool"):
        raise ValueError("UNSUPPORTED_OUTPUT")
    args=[["arg",i] for i in range(task["nargs"])]
    ops=set(task["ops"]);literals=[["lit",s] for s in task["constants"]]
    ints=[["num",k] for k in task["numbers"]]
    generated=list(ints)
    if "str.len" in ops:
        generated.extend(["len",a] for a in args)
    for a in args:
        if "str.indexof" in ops:
            for l in literals:
                if not l[1] or len(l[1])>5:continue
                term=["index",a,l,["num",0]]
                generated.append(term)
                if "+" in ops:generated.append(["plus",term,["num",1]])
                if "-" in ops:generated.append(["minus",term,["num",1]])
    unique={};out=[]
    for node in generated:
        digest=core.canonical(node)
        if digest not in unique:
            unique[digest]=True
            if core.grammar_compatible(node,task):out.append(node)
    return out

def choices_for(kind,task,subtrees):
    if kind=="ArgIndex":return list(range(task["nargs"]))
    if kind=="StringLiteral":return task["constants"]
    if kind=="IntLiteral":return task["numbers"]
    if kind=="Int":return subtrees
    if kind=="String":return core.candidate_library(task,limit=150)[:80]
    if kind=="Bool":return list(core.predicates(task))[:80]
    raise ValueError("UNEXPECTED_HOLE_TYPE")

def learned_candidates(templates,task,limit=3000):
    ints=scalar_grammar(task)
    emitted=set();n=0
    for p in templates:
        if p.get("holes",0)>3:continue
        types={}
        try:holes_with_types(p["template"],"String",types)
        except ValueError:continue
        if any(i not in types for i in range(p["holes"])):continue
        pools=[choices_for(types[i],task,ints) for i in range(p["holes"])]
        if any(not pool for pool in pools):continue
        for values in itertools.product(*pools):
            bound={i:v for i,v in enumerate(values)}
            node=core.substitute(p["template"],bound)
            if not core.grammar_compatible(node,task):continue
            k=core.canonical(node)
            if k in emitted:continue
            emitted.add(k);n+=1;yield node
            if n>=limit:return

def memory_search(templates,task,train,budget=500):
    if task["output"]!="String":
        return {"status":"ABSTAIN_SOURCE_TYPE","ast":None,"checks":0,"wall_ms":0.0}
    start=time.perf_counter_ns();n=0
    for p in learned_candidates(templates,task,limit=budget):
        n+=1
        if typed.score_any(p,train)["exact"]:
            return {"status":"SOURCE_LEARNED_TYPED_CONSTRUCTOR","ast":p,
                    "checks":n,"wall_ms":(time.perf_counter_ns()-start)/1e6}
    return {"status":"ABSTAIN_NO_SOURCE_TEMPLATE_MATCH","ast":None,
            "checks":n,"wall_ms":(time.perf_counter_ns()-start)/1e6}
