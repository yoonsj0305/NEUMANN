"""Q3 experimental invention of INTEGER-state vs FINITE-variant semantics.

The representation-kind search (finite quotient vs symbolic integer
recurrence) is HUMAN coded, but the task-specific DATA TYPES, arithmetic
transition programs and state transition tables are induced from I/O.

No target family is given to the inventor. Neither model is assumed
universally valid. Unknown, noncausal or oversized problems fail closed.
This is a scoped cross-representation capability, NOT proof of unrestricted
creative intelligence or neural-specific discovery.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from research.q3.autonomous_state_type_invention import (
    LearnedOperator,LearnedSubsequentialOperator,NotRepresentable,
    learn_from_complete_io,
)


def stable_hash(value):
    return sha256(json.dumps(value,sort_keys=True,
                 separators=(",",":")).encode()).hexdigest()[:16]


def evaluate_term(ast,previous,current):
    name=ast[0]
    if name=="prev":return previous
    if name=="cur":return current
    if name=="lit":return ast[1]
    a=evaluate_term(ast[1],previous,current)
    b=evaluate_term(ast[2],previous,current)
    if name=="add":v=a+b
    elif name=="sub":v=a-b
    elif name=="mul":v=a*b
    elif name=="eq":v=int(a==b)
    elif name=="lt":v=int(a<b)
    else:raise ValueError("UNSUPPORTED_SYMBOLIC_OPERATOR")
    if abs(v)>100000000:
        raise ValueError("ARITHMETIC_SAFETY_CAP")
    return v


def inferred_steps(examples,initial):
    relations={}
    for word,out in examples:
        if len(word)!=len(out):return None
        state=initial
        for sym,value in zip(word,out):
            if type(sym) is not int or type(value) is not int:
                return None
            key=(state,sym)
            if key in relations and relations[key]!=value:
                return None
            relations[key]=value
            state=value
    return [(state,symbol,value)
            for (state,symbol),value in sorted(relations.items())]


def symbolic_search(steps,depth=3,budget=10000):
    """Observationally-pruned generic expression enumeration over 2 variables."""
    atoms=[["prev"],["cur"]]+[["lit",c] for c in (-2,-1,0,1,2,3)]
    desired=tuple(y for p,x,y in steps)
    seen=set();levels=[[]];attempts=0
    def test(ast,level):
        nonlocal attempts
        attempts+=1
        try:signature=tuple(evaluate_term(ast,p,x)
                            for p,x,y in steps)
        except (ValueError,TypeError,RecursionError):
            return False
        if signature in seen:return False
        seen.add(signature)
        levels[level].append(ast)
        return signature==desired
    for atom in atoms:
        if test(atom,0):return atom,attempts
    for layer in range(1,depth+1):
        levels.append([])
        for prior in levels[layer-1]:
            for leaf in atoms:
                for opcode in ("add","sub","mul","eq","lt"):
                    for left,right in ((prior,leaf),(leaf,prior)):
                        term=[opcode,left,right]
                        if test(term,layer):return term,attempts
                        if attempts>=budget:return None,attempts
    return None,attempts


@dataclass(frozen=True)
class InventedIntegerState:
    initial:int
    update:list

    def ast(self):
        name="invented_integer_state_"+stable_hash(
            [self.initial,self.update])
        return ["DefineAlgebraicType",name,
                ["IntegerState","safe_runtime_abs_cap",100000000],
                ["DefineRecursiveOperator","step_"+name[-16:],
                 ["lambda",["state","input_symbol"],self.update],
                 ["GenericListRecursion","emit_updated_state_each_input"],
                 ["InitialState",self.initial]]]

    def apply(self,word):
        state=self.initial;result=[]
        for symbol in word:
            if type(symbol) is not int:return None
            try:state=evaluate_term(self.update,state,symbol)
            except (ValueError,TypeError,RecursionError):
                return None
            result.append(state)
        return result


def infer_integer_state(examples,depth=3):
    best=None
    for initial in (0,1,-1,2,-2,3):
        steps=inferred_steps(examples,initial)
        if not steps:continue
        program,trials=symbolic_search(steps,depth=depth)
        if program is None:continue
        candidate=InventedIntegerState(initial,program)
        if not all(candidate.apply(x)==list(y) for x,y in examples):
            continue
        score=(len(json.dumps(program)),abs(initial),
               json.dumps(program))
        if best is None or score<best[0]:
            best=(score,candidate,trials)
    return (best[1],best[2]) if best else (None,0)


def expression_nodes(node):
    if isinstance(node,list):
        return 1+sum(expression_nodes(x) for x in node)
    return 1


def invent_representation(examples):
    """Choose best discovered TYPE and TRANSITION together under explicit MDL.

    No domain-specific task names; no target formulas available. Each
    candidate must be TRAIN-exact and remains frozen on heldout input.
    Scores are simple human-chosen description lengths, NOT speed metrics.
    """
    candidates=[];trace=[]
    try:
        finite,attempts=learn_from_complete_io(examples)
        if all(finite.apply(x)==list(y) for x,y in examples):
            m=finite.internal
            cost=10*m.num_states+6*len(m.transitions)
            candidates.append((cost,"FiniteVariantState",finite))
            trace.append(["FiniteVariantState","TRAIN_EXACT",cost])
    except (NotRepresentable,ValueError,RuntimeError,TypeError) as e:
        trace.append(["FiniteVariantState",type(e).__name__,None])
    numeric,trials=infer_integer_state(examples)
    if numeric is not None:
        cost=10+expression_nodes(numeric.update)+2*abs(numeric.initial)
        candidates.append((cost,"SymbolicIntegerState",numeric))
        trace.append(["SymbolicIntegerState","TRAIN_EXACT",cost])
    else:trace.append(["SymbolicIntegerState","UNSUPPORTED",None])
    if not candidates:return None,trace
    cost,kind,program=min(candidates,key=lambda x:(x[0],x[1]))
    return (kind,program,cost),trace


class HeterogeneousLanguage:
    """Reusable language whose newly inferred TypeExpr forms are persistent."""
    SCHEMA="neumann.q3.self-invented-heterogeneous-representations.v1"

    def __init__(self,definitions=None,history=None):
        self.definitions=dict(definitions or {})
        self.history=list(history or [])

    @staticmethod
    def _encode(kind,program):
        if kind=="SymbolicIntegerState":
            return {"type":kind,"initial":program.initial,
                    "update":program.update,"ast":program.ast()}
        if kind=="FiniteVariantState":
            m=program.internal
            return {"type":kind,
                    "initial_emission":list(program.initial_emission),
                    "num_states":m.num_states,
                    "transitions":[[q,s,list(chunk),to] for q,s,chunk,to
                                   in m.transitions],
                    "ast":program.to_ast()}
        raise ValueError("UNKNOWN_GENERATED_DATA_TYPE")

    @staticmethod
    def _decode(data):
        kind=data["type"]
        if kind=="SymbolicIntegerState":
            p=InventedIntegerState(data["initial"],data["update"])
            program_ast=p.ast()
        elif kind=="FiniteVariantState":
            m=LearnedOperator(
                data["num_states"],
                tuple((q,s,tuple(chunk),to)
                      for q,s,chunk,to in data["transitions"]))
            p=LearnedSubsequentialOperator(
                tuple(data["initial_emission"]),m)
            program_ast=p.to_ast()
        else:raise ValueError("BAD_STORED_TYPE")
        if data["ast"]!=program_ast:
            raise ValueError("INVENTED_TYPE_TAMPER_DETECTED")
        return p

    def solve(self,examples):
        for name,record in sorted(self.definitions.items()):
            program=self._decode(record)
            if all(program.apply(x)==list(y) for x,y in examples):
                self.history.append({"mode":"reuse","symbol":name,
                                     "kind":record["type"]})
                return name,program,"reuse",record["type"]
        selected,trace=invent_representation(examples)
        if selected is None:
            self.history.append({"mode":"abstain","candidates":trace})
            return None,None,"abstain",None
        kind,program,cost=selected
        name=(program.ast() if kind=="SymbolicIntegerState"
              else program.to_ast())[1]
        self.definitions[name]=self._encode(kind,program)
        self.history.append({"mode":"invent","symbol":name,
                             "kind":kind,"MDL_cost":cost,
                             "checked_candidate_types":trace})
        return name,program,"invent",kind

    def dump(self):
        return {"schema":self.SCHEMA,"definitions":self.definitions,
                "history":self.history}

    @classmethod
    def load(cls,record):
        if record.get("schema")!=cls.SCHEMA:
            raise ValueError("BAD_LANGUAGE_FORMAT")
        obj=cls(record["definitions"],record["history"])
        for definition in obj.definitions.values():obj._decode(definition)
        return obj
