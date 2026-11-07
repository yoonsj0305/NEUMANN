"""Q3: invent typed predicate ASTs rather than memorizing deleted symbols.

This is a DEV-stage upgrade based on POST-FIRST failure analyses of MBPP
#412/#426/#451, so those three tasks are explicitly EXPOSED controls.

The *previously source-learned* higher-order fold constructor is frozen.
This module discovers a new boolean predicate expression for its branch by
solving per-token keep/drop constraints induced from TRAIN input/output I/O,
then lets the learned fold program execute it on unseen values.

Generic predicates (modulo, comparison, Unicode classes, literal set) are
HUMAN-AUTHORED universal primitive hypotheses. There is no hand-written
odd-number or whitespace-removal task function in the inventor.
No open-ended representational-constructor invention is claimed.
"""
from __future__ import annotations
from collections import Counter
import copy
from hashlib import sha256
import json
from math import isfinite

from research.q3.reflexive_constructor_from_experience import canonical,ident

def classify(examples):
    """Infer positive/negative token roles from I/O alignment, no target AST."""
    roles={}
    if not examples:return None
    for args,goal in examples:
        if len(args)!=1:return None
        source=args[0]
        if type(source) not in (str,list,tuple) or type(source) is not type(goal):
            return None
        if len(source)>1024 or len(goal)>1024:return None
        try:
            # An ordered SUBSEQUENCE is required, not a reorder/replacement.
            it=iter(source)
            if not all(any(x==y for x in it) for y in goal):return None
            a=Counter(source);b=Counter(goal)
        except TypeError:
            return None
        if any(n>a[sym] for sym,n in b.items()):
            return None
        for sym,count in a.items():
            if type(sym) not in (str,int,float,bool):return None
            if type(sym) is float and not isfinite(sym):return None
            if b[sym]==count:label=False
            elif b[sym]==0:label=True
            else:return None # mixed observations not a unary predicate
            if sym in roles and roles[sym] is not label:
                return None
            roles[sym]=label
    if not roles or not any(roles.values()):
        return None
    return roles

def pred_value(ast,item):
    kind=ast[0]
    if kind=="member":
        return item in ast[1]
    if kind=="mod_equals":
        return type(item) is int and ast[1]!=0 and item%ast[1]==ast[2]
    if kind=="less_than":
        return type(item) in (int,float) and item<ast[1]
    if kind=="greater_than":
        return type(item) in (int,float) and item>ast[1]
    if kind=="eq":
        return type(item) is type(ast[1]) and item==ast[1]
    if kind=="unicode_class":
        if type(item) is not str or len(item)!=1:return False
        rule=ast[1]
        if rule=="space":return item.isspace()
        if rule=="digit":return item.isdigit()
        if rule=="alpha":return item.isalpha()
        if rule=="upper":return item.isupper()
        if rule=="lower":return item.islower()
        if rule=="alnum":return item.isalnum()
        return False
    raise ValueError("UNKNOWN_BOOLEAN_EXPRESSION")

def proposals(roles):
    removed=sorted((a for a,b in roles.items() if b),key=lambda x:repr(x))
    candidates=[]
    for name in ("space","digit","alpha","upper","lower","alnum"):
        candidates.append((2.3,["unicode_class",name]))
    if all(type(x) is int for x in roles):
        for k in range(2,11):
            for rem in range(k):
                candidates.append((2.4+0.04*k,["mod_equals",k,rem]))
        vals=[v for v in roles]
        for v in sorted(set(vals+[-1,0,1,2])):
            candidates.append((3.3,["less_than",v]))
            candidates.append((3.3,["greater_than",v]))
    candidates.append((2.8+1.25*len(removed),["member",removed]))
    for v in removed:
        candidates.append((3.2,["eq",v]))
    return sorted(candidates,key=lambda q:(q[0],canonical(q[1])))

def infer_predicate(examples):
    roles=classify(examples)
    if roles is None:return None,0,[]
    attempts=0;trace=[]
    for mdl,expr in proposals(roles):
        attempts+=1
        try:
            good=all(pred_value(expr,item)==lab
                     for item,lab in roles.items())
        except (TypeError,ValueError):
            good=False
        trace.append({"candidate":expr,"MDL_estimate":round(mdl,3),
                      "classification_consistent":good})
        if good:
            return expr,attempts,trace
    return None,attempts,trace

def generate_fold_from_learned_constructor(frozen,examples):
    """Retain source-learned FOLD body, invent only its typed boolean branch."""
    if frozen.get("kind")!="DefineRepresentationConstructor":
        return None,0,[]
    source=frozen["constructor_program"]
    if source.get("hole_count")!=1:
        return None,0,[]
    tpl=source.get("template")
    if not (type(tpl) is list and tpl[0]=="fold"):
        return None,0,[]
    condition,tries,trace=infer_predicate(examples)
    if condition is None:return None,tries,trace
    ast=copy.deepcopy(tpl)
    # Generic AST rewrite against the previously LEARNED 'if' branch:
    # no target-specific primitive filter attached to the interpreter.
    if ast[3][0]!="if":
        return None,tries,trace
    ast[3][1]=["ApplyGeneratedBooleanExpression",condition,["item"]]
    program={
        "kind":"DefineGeneratedOperator",
        "source_constructor":frozen["symbol"],
        "operator_name":"invented_predicate_fold_"+ident(ast),
        "ast":ast,
        "predicate":condition,
        "learned_branch_type":"Bool",
        "container_polymorphism":["str","list","tuple"],
    }
    if not all(run_generated(program,args)==goal for args,goal in examples):
        return None,tries,trace
    return program,tries,trace

def run_generated(program,args):
    try:
        ast=program["ast"]
        if len(args)!=1 or ast[0]!="fold":return None
        seq=args[0]
        if type(seq) not in (str,list,tuple) or len(seq)>1024:return None
        step=ast[3]
        if (step[0]!="if" or step[1][0]!="ApplyGeneratedBooleanExpression"
                or step[1][2]!=["item"]):
            return None
        pred=step[1][1]
        result=type(seq)()
        for item in seq:
            if not pred_value(pred,item):
                if type(seq) is str:result=result+item
                elif type(seq) is tuple:result=result+(item,)
                else:result=result+[item]
            if len(result)>1024:return None
        return result
    except (TypeError,ValueError,IndexError,KeyError,OverflowError):
        return None
