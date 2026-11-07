"""Q3: synthesize relational REPRESENTATION and executable operator AST.

Unlike earlier unary-token filtering, a candidate representation is
(internal coordinate i, second coordinate J(i,n), relation between two
values, reduction over i). The coordinate mapping J is synthesized from
a generic typed affine integer expression language with NO predefined
mirror/reverse/palindrome operator or J=n-i-1 hardcoded in the inventor.

IMPORTANT:
* The programmer did provide generic indexed access, addition/subtraction,
  finite quantification and the universal IR interpreter.
* Original HumanEval/48 was inspected AFTER prior FIRST #715/#716, so all
  results on this original are POSTFIRST DEVELOPMENT, NOT new blind proof.
* Source-trained relation invention is not unrestricted Q3 creativity.
"""
from __future__ import annotations
from hashlib import sha256
import json,time

SCHEMA="neumann.q3.generic_pairwise_relation_constructor.v1"

def canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"))
def digest(x):return sha256(canon(x).encode()).hexdigest()[:16]
def sequence(x):return type(x) in (str,list,tuple)

def affine_value(expr,i,n):
    tag=expr[0]
    if tag=="i":return i
    if tag=="n":return n
    if tag=="c":return expr[1]
    if tag=="add":return affine_value(expr[1],i,n)+affine_value(expr[2],i,n)
    if tag=="sub":return affine_value(expr[1],i,n)-affine_value(expr[2],i,n)
    raise ValueError("NOT_AFFINE_BASE_EXPRESSION")

def coeffs(expr):
    """Exact affine coefficients, by structural induction on + and -."""
    if expr[0]=="i":return (1,0,0)
    if expr[0]=="n":return (0,1,0)
    if expr[0]=="c":return (0,0,expr[1])
    if expr[0] in ("add","sub"):
        a=coeffs(expr[1]);b=coeffs(expr[2])
        sign=1 if expr[0]=="add" else -1
        return tuple(x+sign*y for x,y in zip(a,b))
    raise ValueError("CANNOT_PROVE_NONAFFINE_EXPRESSION")

def generated_coordinates():
    """Small complete normalized affine grammar, no task-name priors.

    Prune expressions that are identical on independent generic length
    contexts n=1..16. This removes syntactic aliasing but keeps distinct
    position relations available for source-driven discovery.
    """
    base=[["i"],["n"],["c",-1],["c",0],["c",1],["c",2]]
    probe=[(i,n) for n in range(1,17) for i in range(n)]
    seen={};terms=[]
    def add(e):
        try:sig=tuple(affine_value(e,i,n) for i,n in probe)
        except (ValueError,OverflowError):return
        if sig not in seen:
            seen[sig]=e;terms.append(e)
    for x in base:add(x)
    for generation in range(2):
        saved=terms[:]
        for a in saved:
            for b in base:
                for op in ("add","sub"):
                    add([op,a,b]);add([op,b,a])
    return sorted(terms,key=lambda e:(len(canon(e)),canon(e)))

def run_new_representation(program,args):
    if program is None or len(args)!=1:return None
    seq=args[0]
    if not sequence(seq) or len(seq)>1024:return None
    if program.get("kind")!="DefineGeneratedCoordinateRelation":
        return None
    coordinate=program["representation_constructor"]["second_index"]
    reduction=program["relation"]["reduce"]
    comparator=program["relation"]["compare"]
    seen=[]
    try:
        for i in range(len(seq)):
            j=affine_value(coordinate,i,len(seq))
            if not isinstance(j,int) or not 0<=j<len(seq):
                return None
            v=seq[i]==seq[j]
            if comparator=="neq":v=not v
            elif comparator!="eq":return None
            seen.append(v)
        if reduction=="all":return all(seen)
        if reduction=="any":return any(seen)
        return None
    except (TypeError,ValueError,OverflowError,IndexError,KeyError):
        return None

def discover(examples,budget=1200):
    """One source TRAIN -> independently generated coordinate grammar AST."""
    started=time.perf_counter_ns()
    if len(examples)<4:return {
        "status":"ABSTAIN_INSUFFICIENT_SOURCE","attempts":0,"program":None}
    if any(len(args)!=1 or not sequence(args[0]) or
           type(y) is not bool for args,y in examples):
        return {"status":"ABSTAIN_TYPE","attempts":0,"program":None}
    if not ({y for args,y in examples}=={False,True}):
        return {"status":"ABSTAIN_NO_POSITIVE_NEGATIVE","attempts":0,
                "program":None}
    if len({len(args[0]) for args,y in examples})<2:
        return {"status":"ABSTAIN_UNDERSPECIFIED_LENGTH","attempts":0,
                "program":None}
    attempts=0
    for expr in generated_coordinates():
        for reduction in ("all","any"):
            for comp in ("eq","neq"):
                ast={
                    "kind":"DefineGeneratedCoordinateRelation",
                    "representation_constructor":{
                        "type":"IndexedPairwiseRelation",
                        "first_index":["i"],"second_index":expr,
                        "arity":2,"domain":"range(len(input))"},
                    "relation":{"compare":comp,"reduce":reduction},
                    "human_supplied_base_VM":True,
                }
                ast["operator_symbol"]="invented_relation_"+digest(ast)
                attempts+=1
                if all(run_new_representation(ast,args) is y
                       for args,y in examples):
                    return {
                        "status":"INVENTED_EXECUTABLE_RELATION",
                        "program":ast,"attempts":attempts,
                        "wall_ms":round(
                            (time.perf_counter_ns()-started)/1e6,5),
                        "coordinate_affine_coefficients":coeffs(expr),
                    }
                if attempts>=budget:
                    return {"status":"ABSTAIN_BUDGET","attempts":attempts,
                            "program":None,
                            "wall_ms":round(
                              (time.perf_counter_ns()-started)/1e6,5)}
    return {"status":"ABSTAIN_UNREPRESENTABLE","attempts":attempts,
            "program":None,
            "wall_ms":round((time.perf_counter_ns()-started)/1e6,5)}
