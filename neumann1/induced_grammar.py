"""Learn new reusable executable program grammar productions across I/O tasks.

Induce AST contexts and schematic operator slots from source-certified
programs. No dataset family labels enter solve(); heldout gold is never used
by library induction. This is a bounded classic program-library learner,
not a universal or frontier-level invention mechanism.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from time import perf_counter_ns
from collections import defaultdict

INVALID = object()
ATOMIC = ('abs','square','neg','inc','twice','lower','upper','strip','reverse',
          'sort','unique','length','sum','flatten','digits','join','first','last')
MAP_OPS = ('abs','square','neg','inc','twice','lower','upper')


def freeze(v):
    if isinstance(v, list): return tuple(freeze(x) for x in v)
    if isinstance(v, tuple): return tuple(freeze(x) for x in v)
    if isinstance(v, dict): return tuple(sorted((k,freeze(x)) for k,x in v.items()))
    return v


def atom(name,x):
    if name=='abs' and type(x) is int:return abs(x)
    if name=='square' and type(x) is int:return x*x
    if name=='neg' and type(x) is int:return -x
    if name=='inc' and type(x) is int:return x+1
    if name=='twice' and type(x) is int:return x*2
    if name=='lower' and isinstance(x,str):return x.lower()
    if name=='upper' and isinstance(x,str):return x.upper()
    if name=='strip' and isinstance(x,str):return x.strip()
    if name=='reverse' and isinstance(x,(tuple,str)):return x[::-1]
    if name=='sort' and isinstance(x,(tuple,str)):
        try:
            v=sorted(x)
            return ''.join(v) if isinstance(x,str) else tuple(v)
        except TypeError:return INVALID
    if name=='unique' and isinstance(x,(tuple,str)):
        try:
            v=tuple(dict.fromkeys(x))
            return ''.join(v) if isinstance(x,str) else v
        except TypeError:return INVALID
    if name=='length' and isinstance(x,(tuple,str)):return len(x)
    if name=='sum' and isinstance(x,tuple) and all(type(y) is int for y in x):return sum(x)
    if name=='flatten' and isinstance(x,tuple) and all(isinstance(y,tuple) for y in x):
        return tuple(z for y in x for z in y)
    if name=='digits' and type(x) is int and x>=0:return tuple(int(c) for c in str(x))
    if name=='join' and isinstance(x,tuple) and all(type(y) is str for y in x):return ''.join(x)
    if name=='first' and isinstance(x,(tuple,str)) and x:return x[0]
    if name=='last' and isinstance(x,(tuple,str)) and x:return x[-1]
    return INVALID


def eval_ast(ast,input_value):
    tag=ast[0]
    if tag=='input':return freeze(input_value)
    if tag=='call':
        value=eval_ast(ast[2],input_value)
        return INVALID if value is INVALID else atom(ast[1],value)
    if tag=='map':
        value=eval_ast(ast[2],input_value)
        if not isinstance(value,tuple):return INVALID
        result=tuple(atom(ast[1],x) for x in value)
        return INVALID if any(x is INVALID for x in result) else result
    raise ValueError('unknown AST; arbitrary Python evaluation forbidden')


def cost(ast):
    return 0 if ast[0]=='input' else 1+cost(ast[2])


def contexts(ast):
    nodes=[]
    while ast[0]!='input':
        nodes.append((ast[0],ast[1]))
        ast=ast[2]
    out=[]
    for start in range(len(nodes)):
        for end in range(start+2,len(nodes)+1):
            x=('hole','ARG')
            for tag,fn in reversed(nodes[start:end]):x=(tag,fn,x)
            out.append(x)
    return out


def antiunify(a,b):
    if a==b:return a
    if a[0]=='hole' or b[0]=='hole':
        return ('hole','ARG') if a==b else None
    if a[0]!=b[0] or a[0] not in ('call','map'):return None
    inner=antiunify(a[2],b[2])
    if inner is None:return None
    if a[1]==b[1]:fn=a[1]
    elif a[0]=='map':fn=('fn_hole','MAP')
    else:fn=('fn_hole','CALL')
    return (a[0],fn,inner)


def fixed_nodes(ast):
    return 0 if ast[0]=='hole' else int(type(ast[1]) is str)+fixed_nodes(ast[2])


def slot_count(ast):
    return 0 if ast[0]=='hole' else int(type(ast[1]) is tuple)+slot_count(ast[2])


def expand(pattern,expr):
    if pattern[0]=='hole':
        yield expr
        return
    tag,fn,inner=pattern
    opts=[fn] if type(fn) is str else MAP_OPS if tag=='map' else ATOMIC
    for op in opts:
        for child in expand(inner,expr):
            yield (tag,op,child)


def _template_cost(ast):
    return 0 if ast[0]=='hole' else 1+_template_cost(ast[2])


@dataclass(frozen=True)
class Production:
    template:tuple
    source_tasks:tuple[str,...]
    observed_operator_count:int

    @property
    def name(self):
        return 'G:'+repr(self.template)

    def instantiate(self,expr):
        return expand(self.template,expr)


@dataclass(frozen=True)
class Synthesis:
    expression:tuple|None
    checked:int
    elapsed_ms:float
    used_invented_production:bool
    solved:bool


class GrammarInventor:
    def __init__(self,max_cost=4,max_candidates=100000):
        self.max_cost=max_cost
        self.max_candidates=max_candidates
        self.source_solutions={}
        self.productions=[]

    def invent_from_source(self,task_id,examples,*,verification_pairs=None):
        if task_id in self.source_solutions:
            raise ValueError('duplicate source ID')
        result=self.solve(examples,learned=False)
        if result.solved and verification_pairs is not None:
            # Independent SOURCE-only counterexamples, never target data.
            if not verification_pairs or any(
                eval_ast(result.expression,x)!=freeze(y)
                for x,y in verification_pairs):
                return Synthesis(None,result.checked,result.elapsed_ms,False,False)
        if result.solved:
            self.source_solutions[task_id]=result.expression
            self._induce()
        return result

    def _induce(self):
        entries=[]
        for task,ast in self.source_solutions.items():
            for c in set(contexts(ast)):
                entries.append((task,c))
        support=defaultdict(set)
        for task,c in entries:
            support[c].add(task)
        for (ta,a),(tb,b) in combinations(entries,2):
            if ta==tb:continue
            g=antiunify(a,b)
            if g is not None and fixed_nodes(g)>=1 and slot_count(g)<=1:
                support[g].update((ta,tb))
        productions=[]
        for template,tasks in support.items():
            if len(tasks)<2:continue
            opcount=_template_cost(template)
            if opcount>=2:
                productions.append(Production(template,tuple(sorted(tasks)),opcount))
        productions.sort(key=lambda p:(-fixed_nodes(p.template),slot_count(p.template),
                                       -p.observed_operator_count,repr(p.template)))
        self.productions=productions[:64]

    def solve(self,examples,*,learned=True):
        start=perf_counter_ns()
        if not examples:raise ValueError('nonempty demonstrations required')
        examples=[(freeze(x),freeze(y)) for x,y in examples]
        xs=tuple(x for x,y in examples)
        ys=tuple(y for x,y in examples)
        seen={}
        checked=0

        def check(ast,used):
            nonlocal checked
            if cost(ast)>self.max_cost:return None
            outputs=tuple(eval_ast(ast,x) for x in xs)
            if any(o is INVALID for o in outputs):return None
            if outputs in seen:return None
            seen[outputs]=ast
            checked+=1
            if outputs==ys:
                return Synthesis(ast,checked,(perf_counter_ns()-start)/1e6,used,True)
            return None

        base=('input',)
        r=check(base,False)
        if r:return r
        by_depth={0:[base]}
        for depth in range(1,self.max_cost+1):
            next_level=[]
            if learned:
                for p in self.productions:
                    for child in by_depth.get(depth-p.observed_operator_count,[]):
                        for ast in p.instantiate(child):
                            if cost(ast)!=depth:continue
                            r=check(ast,True)
                            if r:return r
                            if seen.get(tuple(eval_ast(ast,x) for x in xs))==ast:
                                next_level.append(ast)
                            if checked>=self.max_candidates:
                                return Synthesis(None,checked,(perf_counter_ns()-start)/1e6,False,False)
            for child in by_depth.get(depth-1,[]):
                for name in ATOMIC:
                    ast=('call',name,child)
                    r=check(ast,False)
                    if r:return r
                    if seen.get(tuple(eval_ast(ast,x) for x in xs))==ast:
                        next_level.append(ast)
                for name in MAP_OPS:
                    ast=('map',name,child)
                    r=check(ast,False)
                    if r:return r
                    if seen.get(tuple(eval_ast(ast,x) for x in xs))==ast:
                        next_level.append(ast)
                if checked>=self.max_candidates:
                    return Synthesis(None,checked,(perf_counter_ns()-start)/1e6,False,False)
            by_depth[depth]=next_level
        return Synthesis(None,checked,(perf_counter_ns()-start)/1e6,False,False)
