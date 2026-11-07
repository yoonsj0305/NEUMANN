"""Q3 typed, I/O-driven hypothesis construction, not untyped brute force.

Universal *human-written* cores:
  - typed scalar algebra; sparse polynomial basis over numeric args
  - sequential filter via a learned symbol predicate
  - finite list fold over primitive algebra
All target data and generated per-problem ASTs are learned from TRAIN only.
No benchmark function identifiers, target names, custom per-task operators,
hidden reference implementation, or heldout values are read by the inventor.

This is a scoped operator-induction experiment. A universal autonomous
invention policy is not proven by any number of synthetic/CodeARC cases.
"""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
from itertools import combinations,product
from hashlib import sha256
import json
import math
import time

SCHEMA="neumann.q3.typed-semantic-delta-generated-operators.v1"

def pack(x):return json.dumps(x,sort_keys=True,default=str,separators=(",",":"))
def digest(x):return sha256(pack(x).encode()).hexdigest()[:18]
def is_num(x):return type(x) in (int,float)

def same(actual,goal):
    if type(goal) is bool:return type(actual) is bool and actual is goal
    if is_num(actual) and is_num(goal):
        return (math.isfinite(actual) and math.isfinite(goal) and
                math.isclose(actual,goal,rel_tol=1e-10,abs_tol=1e-9))
    return type(actual) is type(goal) and actual==goal

def as_fraction(v):
    if type(v) is int:return Fraction(v)
    if type(v) is float and math.isfinite(v):
        return Fraction(str(v)).limit_denominator(1_000_000)
    raise ValueError("not a finite number")

def solve_exact_basis(rows,targets):
    """Unique solution from some independent rows; validate on all source."""
    if not rows:return None
    n=len(rows[0]);matrix=[list(row)+[rhs] for row,rhs in zip(rows,targets)]
    piv=[];rank=0
    for col in range(n):
        index=next((i for i in range(rank,len(matrix)) if matrix[i][col]),None)
        if index is None:continue
        matrix[rank],matrix[index]=matrix[index],matrix[rank]
        v=matrix[rank][col]
        matrix[rank]=[x/v for x in matrix[rank]]
        for i in range(len(matrix)):
            if i!=rank:
                factor=matrix[i][col]
                matrix[i]=[a-factor*b for a,b in zip(matrix[i],matrix[rank])]
        piv.append(col);rank+=1
        if rank==n:break
    if rank!=n:return None
    return [matrix[piv.index(col)][-1] for col in range(n)]

def numeric_monomials(arity):
    if arity not in (1,2):return []
    degrees=[(0,)*arity]
    for deg in (1,2,3):
        degrees.extend(e for e in product(range(deg+1),repeat=arity)
                       if sum(e)==deg)
    return degrees

def fit_support(examples,support,limit_coeff=256,limit_den=64):
    try:
        source=[([as_fraction(v) for v in args],as_fraction(y))
                for args,y in examples]
        def features(args):return [
            math.prod(v**p for v,p in zip(args,expo)) for expo in support]
        features_all=[features(x) for x,y in source]
        coefficients=solve_exact_basis(features_all,[y for x,y in source])
        if coefficients is None or any(abs(c.numerator)>limit_coeff or
                        c.denominator>limit_den for c in coefficients):
            return None
        for (args,y),observed in zip(examples,features_all):
            v=sum(c*part for c,part in zip(coefficients,observed))
            if not same(float(v),y):return None
        return {"kind":"DerivedPolynomial","monomials":[list(e) for e in support],
                "coefficients":[[c.numerator,c.denominator] for c in coefficients],
                "arity":len(source[0][0]),
                "observed_output_type":"float" if
                    any(type(y) is float for args,y in examples) else "int"}
    except (ValueError,OverflowError,TypeError,ZeroDivisionError,MemoryError):
        return None

def synth_numeric(examples,preferred_supports=(),max_candidate=5000):
    if not examples:return None,0
    arity=len(examples[0][0])
    if arity not in (1,2):return None,0
    if not all(len(args)==arity and all(is_num(x) for x in args) and
               is_num(y) for args,y in examples):
        return None,0
    monomials=numeric_monomials(arity);tried=set();attempts=0
    for s in preferred_supports:
        ex=tuple(tuple(row) for row in s)
        if all(row in monomials for row in ex) and ex and ex not in tried:
            attempts+=1;tried.add(ex)
            p=fit_support(examples,ex)
            if p:return p,attempts
    for count in range(1,min(5,len(monomials),len(examples))+1):
        for s in combinations(monomials,count):
            if s in tried:continue
            tried.add(s);attempts+=1
            p=fit_support(examples,s)
            if p:return p,attempts
            if attempts>=max_candidate:return None,attempts
    return None,attempts

def synth_filter(examples):
    if not examples or any(len(args)!=1 or
           type(args[0]) not in (list,str,tuple) or
           type(args[0]) is not type(y) for args,y in examples):
        return None,0
    removed=set();retained=set()
    try:
        for args,y in examples:
            a=args[0];source=Counter(a);target=Counter(y)
            if any(n>source[x] for x,n in target.items()):
                return None,1
            for key,quantity in source.items():
                if target[key]==quantity:retained.add(key)
                elif target[key]==0:removed.add(key)
                else:return None,1
        if not removed or removed&retained or len(removed)>16:
            return None,1
        elements=sorted(removed,key=lambda x:repr(x))
        if any(type(x) not in (str,int,float,bool)
               for x in elements):return None,1
        p={"kind":"DerivedSequenceFilter","source_arg":0,
           "removed":elements,
           "predicate_ast":["lambda","item",["not",
                           ["member",["arg","item"],["set",elements]]]],
           "output_container":"str" if type(examples[0][1]) is str
                        else "tuple" if type(examples[0][1]) is tuple
                        else "list"}
        return (p,1) if all(same(execute(p,args),y)
                           for args,y in examples) else (None,1)
    except (TypeError,ValueError):
        return None,1

def synth_scalar(examples):
    if not examples or any(len(args)!=len(examples[0][0])
                       for args,y in examples):return None,0
    arity=len(examples[0][0])
    if arity not in (1,2):return None,0
    opcodes=("identity","abs") if arity==1 else (
        "add","mul","sub","reverse_sub","eq","lt","reverse_lt")
    for idx,opcode in enumerate(opcodes,1):
        p={"kind":"DerivedScalarCore","op":opcode,"arity":arity}
        try:
            if all(same(execute(p,args),y) for args,y in examples):
                return p,idx
        except (TypeError,ValueError,OverflowError,ZeroDivisionError):
            continue
    return None,len(opcodes)

def synth_fold(examples):
    if not examples or any(len(args)!=1 or type(args[0]) not in (list,tuple)
         or not all(is_num(e) for e in args[0]) or not is_num(y)
         for args,y in examples):
        return None,0
    proposals=0
    # These are generated from generic binary primitive ASTs, not target
    # functions such as sum, product, extrema, weighted aggregation.
    for binary in ("add","mul","min","max"):
        for initial in (0,1):
            proposals+=1
            p={"kind":"DerivedFold","source_arg":0,
               "initial":initial,
               "step":["apply",binary,["state"],["item"]],
               "output_container":"number"}
            if all(same(execute(p,args),y) for args,y in examples):
                return p,proposals
    return None,proposals

def execute(p,args):
    try:
        kind=p["kind"]
        if kind=="DerivedPolynomial":
            if len(args)!=p["arity"] or not all(is_num(x) for x in args):
                return None
            v=sum(Fraction(*coeff)*math.prod(
                as_fraction(x)**power for x,power in zip(args,exp))
                for coeff,exp in zip(p["coefficients"],p["monomials"]))
            if abs(v)>1_000_000_000:return None
            if p["observed_output_type"]=="float":return float(v)
            return v.numerator if v.denominator==1 else float(v)
        if kind=="DerivedSequenceFilter":
            v=args[p["source_arg"]];delset=set(p["removed"])
            if type(v) is str:return "".join(x for x in v if x not in delset)
            if type(v) is list:return [x for x in v if x not in delset]
            if type(v) is tuple:return tuple(x for x in v if x not in delset)
            return None
        if kind=="DerivedScalarCore":
            op=p["op"]
            if op=="identity":return args[0]
            if op=="abs":return abs(args[0])
            if op=="add":return args[0]+args[1]
            if op=="mul":return args[0]*args[1]
            if op=="sub":return args[0]-args[1]
            if op=="reverse_sub":return args[1]-args[0]
            if op=="eq":return args[0]==args[1]
            if op=="lt":return args[0]<args[1]
            if op=="reverse_lt":return args[1]<args[0]
        if kind=="DerivedFold":
            items=args[p["source_arg"]]
            if type(items) not in (list,tuple):return None
            v=p["initial"];op=p["step"][1]
            for item in items:
                if op=="add":v+=item
                elif op=="mul":v*=item
                elif op=="min":v=min(v,item)
                elif op=="max":v=max(v,item)
                else:return None
                if abs(v)>1_000_000_000:return None
            return v
    except (ValueError,TypeError,ZeroDivisionError,OverflowError,
            KeyError,IndexError,RecursionError):
        return None
    return None

class TypeGuidedInventor:
    def __init__(self,enable_structure_memory=True):
        self.enable_structure_memory=enable_structure_memory
        self.verified_programs=[]
        self.learned_supports=[]
        self.history=[]

    def propose(self,examples,allow_new_representations=True):
        start=time.perf_counter_ns()
        total=0
        if not examples:return {"status":"ABSTAIN","program":None,"attempts":0}
        def good(p):
            return all(same(execute(p,args),y) for args,y in examples)
        if self.enable_structure_memory:
            for p in self.verified_programs:
                total+=1
                if good(p):
                    return {"status":"REUSED_VERIFIED_PROGRAM","program":p,
                            "attempts":total,"ms":round(
                                (time.perf_counter_ns()-start)/1e6,4)}
        creators=[synth_scalar,synth_fold]
        if allow_new_representations:
            creators.insert(1,synth_filter)
            creators.append(lambda e:synth_numeric(
                e,self.learned_supports if self.enable_structure_memory else ()))
        for creator in creators:
            p,n=creator(examples);total+=n
            if p is not None:
                status=("GENERATED_NEW_REPRESENTATION"
                    if p["kind"] in ("DerivedPolynomial","DerivedSequenceFilter")
                    else "GENERATED_EXISTING_CORE_COMPOSITION")
                return {"status":status,"program":p,"attempts":total,
                        "ms":round((time.perf_counter_ns()-start)/1e6,4)}
        return {"status":"ABSTAIN","program":None,
                "attempts":total,
                "ms":round((time.perf_counter_ns()-start)/1e6,4)}

    def retain_independently_verified(self,record):
        if not record.get("verified_test_exact"):
            return False
        p=record["program"]
        self.verified_programs.append(p)
        if p["kind"]=="DerivedPolynomial":
            ex=p["monomials"]
            if ex not in self.learned_supports:
                self.learned_supports.append(ex)
        self.history.append({"event":"verified_then_memorized",
                             "source_program_hash":digest(p),
                             "representation_family":p["kind"]})
        return True

    def export(self):
        return {"schema":SCHEMA,
                "verified_operator_count":len(self.verified_programs),
                "inferred_source_grammar_supports":self.learned_supports,
                "history":self.history,
                "verified_programs":self.verified_programs}
