"""Q3: invent the state-transition T from SOURCE I/O, then reuse a learned
higher-order solver-generator on it. One typed SyGuS search for 3 domains.

Not a new mathematical primitive: integer/set/string instruction atoms and
types are human-supplied. The COMPLETE transition expression is NOT supplied.
Independent SOURCE verification is mandatory. No original test gold enters.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from time import perf_counter_ns


def _kind(x):
    if type(x) is int:return "int"
    if type(x) is str:return "str"
    if type(x) is frozenset:return "set"
    raise TypeError("unsupported typed SOURCE representation")


def _set_min(s):
    return min(s) if s else 0


def _primitive_ops():
    return (
        ("add",("int","int"),"int",lambda a,b:a+b),
        ("sub",("int","int"),"int",lambda a,b:a-b),
        ("max",("int","int"),"int",max),
        ("min",("int","int"),"int",min),
        ("min_element",("set",),"int",_set_min),
        ("singleton",("int",),"set",lambda x:frozenset((x,))),
        ("difference",("set","set"),"set",lambda a,b:a-b),
        ("union",("set","set"),"set",lambda a,b:a|b),
        ("intersection",("set","set"),"set",lambda a,b:a&b),
        ("replace",("str","str","str"),"str",
         lambda s,a,b:s.replace(a,b)),
    )


OPS={name:(ins,out,fn) for name,ins,out,fn in _primitive_ops()}


@dataclass(frozen=True)
class Expression:
    ast:tuple
    type:str
    nodes:int
    source_signature:tuple


def evaluate_ast(ast,source):
    if ast[0]=="input":return source
    if ast[0]=="constant":return ast[1]
    _,_,function=OPS[ast[0]]
    return function(*(evaluate_ast(x,source) for x in ast[1:]))


@dataclass(frozen=True)
class InventedTransition:
    ast:tuple
    input_type:str
    ast_nodes:int
    training_examples:int
    source_verifiers:int
    enumerated_expressions:int
    discovery_ms:float

    def __call__(self,raw):
        if _kind(raw)!=self.input_type:
            raise TypeError("new transition input type mismatch")
        return evaluate_ast(self.ast,raw)


class TypedTransitionInventor:
    """Source-induced operator AST from a typed, compositional instruction set.

    New formula creation is one bottom-up enumerator; the data type only
    restricts admissible primitives. No handcoded solver for each family.
    """

    def __init__(self, *, max_nodes=6,
                 max_expressions=80000,max_source_ms=2500):
        if (type(max_nodes) is not int or not 1<=max_nodes<=12
                or type(max_expressions) is not int
                or not 5<=max_expressions<=1000000
                or not 1<=max_source_ms<=120000):
            raise ValueError("finite typed expression search budget")
        self.max_nodes=max_nodes
        self.max_expressions=max_expressions
        self.max_source_ms=max_source_ms

    def invent(self,source_pairs,*,independent_source_checks):
        started=perf_counter_ns()
        train=tuple(source_pairs)
        verified=tuple(independent_source_checks)
        if len(train)<3 or len(verified)<2:
            raise ValueError("3 SOURCE examples and 2 SOURCE verifiers required")
        kind=_kind(train[0][0])
        if any(_kind(x)!=kind or _kind(y)!=kind
               for x,y in train+verified):
            raise ValueError("homogeneous source/target STATE types required")
        if {x for x,y in train}&{x for x,y in verified}:
            raise ValueError("SOURCE verifier overlaps synthesis examples")
        xvalues=tuple(x for x,y in train)
        expected=tuple(y for x,y in train)
        pool={}
        signatures={}
        n_candidates=0

        def register(ast,out_type,nodes,values):
            nonlocal n_candidates
            pytype={"int":int,"str":str,"set":frozenset}[out_type]
            if any(type(v) is not pytype for v in values):
                return
            key=(out_type,values)
            # Retain several observationally equal expressions because
            # an independent source verifier can distinguish them.
            if signatures.get(key,0)>=5:return
            signatures[key]=signatures.get(key,0)+1
            pool.setdefault(nodes,[]).append(
                Expression(ast,out_type,nodes,values))
            n_candidates+=1

        terminals=[(kind,("input",),xvalues)]
        if kind=="int":
            terminals.extend(
                ("int",("constant",n),tuple(n for _ in xvalues))
                for n in (0,1,2))
        elif kind=="set":
            terminals.extend((
                ("set",("constant",frozenset()),
                 tuple(frozenset() for _ in xvalues)),
                ("int",("constant",0),
                 tuple(0 for _ in xvalues)),
            ))
        else:
            alphabet=sorted({c for x in xvalues for c in x})
            literals={""}
            for c in alphabet:
                literals.add(c)
                literals.add(c*2)
            terminals.extend(
                ("str",("constant",s),tuple(s for _ in xvalues))
                for s in sorted(literals,key=lambda x:(len(x),x)))
        for out_type,ast,signature in terminals:
            register(ast,out_type,1,signature)

        for nodes in range(1,self.max_nodes+1):
            for item in pool.get(nodes,()):
                if (item.type==kind and
                        item.source_signature==expected and
                        all(evaluate_ast(item.ast,x)==y
                            for x,y in verified)):
                    return InventedTransition(
                        item.ast,kind,nodes,len(train),len(verified),
                        n_candidates,(perf_counter_ns()-started)/1e6)
            if nodes==self.max_nodes:break
            if n_candidates>=self.max_expressions or (
                    perf_counter_ns()-started)/1e6>self.max_source_ms:
                break
            next_size=nodes+1
            for name,required_types,out_type,fn in _primitive_ops():
                for split in product(range(1,next_size),
                                     repeat=len(required_types)):
                    if sum(split)!=next_size-1:continue
                    alternatives=tuple(
                        tuple(expr for expr in pool.get(n,())
                              if expr.type==desired)
                        for n,desired in zip(split,required_types))
                    if any(not p for p in alternatives):
                        continue
                    for terms in product(*alternatives):
                        if n_candidates>=self.max_expressions or (
                            perf_counter_ns()-started)/1e6>self.max_source_ms:
                            break
                        try:
                            outputs=tuple(
                                fn(*(term.source_signature[i]
                                     for term in terms))
                                for i in range(len(xvalues)))
                        except (ValueError,TypeError,IndexError,
                                ZeroDivisionError,OverflowError):
                            continue
                        register((name,)+tuple(t.ast for t in terms),
                                 out_type,next_size,outputs)
        raise ValueError(
            "ABSTAIN: no independently SOURCE-verified executable transition")
