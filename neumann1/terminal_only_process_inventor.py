"""Q3: invent an executable LATENT PROCESS using ENDPOINTS ONLY.

Prior work required (initial, successor) pairs to synthesize transition T.
Here no successor pairs, no intermediate ground truth and no target outputs
enter the discovery module. A previously source-learned higher-order control
program is combined with candidate typed expressions, then challenged using
INDEPENDENT SOURCE initial→terminal endpoints.

This discovers A process compatible with final effects. The actual hidden
transition T is generally NOT identifiable from endpoints, and the engine
must not claim causal recovery of the unique true trajectory.

All atom operations and the fixedpoint control code are classical/human
supplied, as openly required by the bounded-language scientific contract.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from time import perf_counter_ns

from .higher_order_method_inventor import ControlProgram
from .typed_transition_inventor import (
    _kind, _primitive_ops, evaluate_ast)


def _bounded_state(value):
    # A synthesized candidate must not amplify raw input into an
    # enormous state during its own multi-step execution. These are
    # RESOURCE bounds, not semantic assumptions about the true law.
    if type(value) is int:
        return abs(value)<=16_777_216
    if type(value) is str:
        return len(value)<=4096
    if type(value) is frozenset:
        return len(value)<=4096
    return False



@dataclass(frozen=True)
class ProcessExpr:
    ast: tuple
    out_type: str
    nodes: int
    source_values: tuple


@dataclass(frozen=True)
class InventedLatentProcess:
    transition_ast: tuple
    transition_type: str
    transition_nodes: int
    control_ast: tuple
    source_examples: int
    independent_checks: int
    candidate_expressions: int
    final_endpoint_checks: int
    max_observed_transition_calls: int
    discovery_ms: float

    @property
    def ast(self):
        return (
            "source_invented_process_from_terminal_only",
            ("latent_state_update", self.transition_ast),
            ("learned_control", self.control_ast),
        )

    def transition(self, x):
        if _kind(x)!=self.transition_type:
            raise TypeError("latent process state type mismatch")
        result=evaluate_ast(self.transition_ast,x)
        if _kind(result)!=self.transition_type or not _bounded_state(result):
            raise ValueError("generated process exceeds typed state bounds")
        return result

    def compile(self, *, max_steps=256):
        return ControlProgram(self.control_ast,max_steps).compile(
            self.transition)


class TerminalOnlyProcessInventor:
    def __init__(self, *, max_nodes=6, max_expressions=35000,
                 max_source_ms=12000, min_proven_steps=3):
        if not (type(max_nodes) is int and 1<=max_nodes<=9 and
                type(max_expressions) is int and 100<=max_expressions<=300000
                and 1<=max_source_ms<=120000 and
                type(min_proven_steps) is int and
                2<=min_proven_steps<=64):
            raise ValueError("finite evidence and hypothesis budgets required")
        self.max_nodes=max_nodes
        self.max_expressions=max_expressions
        self.max_source_ms=max_source_ms
        self.min_proven_steps=min_proven_steps

    def invent(self,source_endpoints,*,independent_terminal_checks,
               control:ControlProgram,known_classical=None):
        started=perf_counter_ns()
        pairs=tuple(source_endpoints)
        verified=tuple(independent_terminal_checks)
        if (len(pairs)<4 or len(verified)<3 or
                not isinstance(control,ControlProgram)):
            raise ValueError(
                ">=4 SOURCE endpoints, >=3 independent checks and "
                "source-learned control program required")
        state_type=_kind(pairs[0][0])
        if any(_kind(x)!=state_type or _kind(y)!=state_type
               for x,y in pairs+verified):
            raise ValueError("typed source endpoints required")
        train_inputs=tuple(x for x,y in pairs)
        if len(set(train_inputs))!=len(train_inputs) or (
                {x for x,y in pairs}&{x for x,y in verified}):
            raise ValueError("independent source endpoint split required")
        # Trusted classical algorithms are used only if independently
        # SOURCE-verified. This method's purpose is invention at a gap.
        if known_classical is not None and all(
                known_classical(x)==y for x,y in pairs+verified):
            return None

        inputs=tuple(x for x,y in pairs)
        goal=tuple(y for x,y in pairs)
        pool={}
        signature_counts={}
        seen=0
        checked=0
        deadline=started+int(self.max_source_ms*1e6)

        def insert(ast,typ,nodes,values):
            nonlocal seen
            pytype={"int":int,"str":str,"set":frozenset}[typ]
            if len(values)!=len(inputs) or any(
                    type(v) is not pytype or not _bounded_state(v)
                    for v in values):
                return
            key=(typ,values)
            if signature_counts.get(key,0)>=3:
                return
            signature_counts[key]=signature_counts.get(key,0)+1
            pool.setdefault(nodes,[]).append(ProcessExpr(
                ast,typ,nodes,values))
            seen+=1

        insert(("input",),state_type,1,inputs)
        if state_type=="int":
            constants=(0,1,2)
            for k in constants:
                insert(("constant",k),"int",1,
                       tuple(k for _ in inputs))
        elif state_type=="set":
            insert(("constant",frozenset()),"set",1,
                   tuple(frozenset() for _ in inputs))
            insert(("constant",0),"int",1,tuple(0 for _ in inputs))
        else:
            alphabet=sorted({letter for x in inputs for letter in x})
            literals={""}
            for ch in alphabet:
                literals.add(ch)
                literals.add(ch*2)
            for s in sorted(literals,key=lambda s:(len(s),s)):
                insert(("constant",s),"str",1,
                       tuple(s for _ in inputs))

        def is_input_dependent(ast):
            if ast[0]=="input":return True
            if ast[0]=="constant":return False
            return any(is_input_dependent(child) for child in ast[1:])

        def test_candidate(expr):
            nonlocal checked
            if not is_input_dependent(expr.ast):
                return None
            def latent(x):
                result=evaluate_ast(expr.ast,x)
                if _kind(result)!=state_type or not _bounded_state(result):
                    raise ValueError("candidate state over resource limit")
                return result
            compiled=control.compile(latent)
            max_steps=0
            for x,y in pairs:
                checked+=1
                try:
                    out=compiled.run(x)
                except (IndexError,TypeError,ValueError,
                        OverflowError,RecursionError):
                    return None
                if (out.status!="HALT_CERTIFIED_FIXED_POINT" or
                        out.value!=y):
                    return None
                max_steps=max(max_steps,out.transition_calls)
            # Prevent a vacuous one-step projection from being called
            # a newly invented multi-step PROCESS. This is an explicit
            # research constraint, not a true-transition certificate.
            if max_steps<self.min_proven_steps:
                return None
            for x,y in verified:
                checked+=1
                try:
                    out=compiled.run(x)
                except (IndexError,TypeError,ValueError,
                        OverflowError,RecursionError):
                    return None
                if (out.status!="HALT_CERTIFIED_FIXED_POINT" or
                        out.value!=y):
                    return None
            return InventedLatentProcess(
                expr.ast,state_type,expr.nodes,control.ast,
                len(pairs),len(verified),seen,checked,max_steps,
                (perf_counter_ns()-started)/1e6)

        for nodes in range(1,self.max_nodes+1):
            if perf_counter_ns()>deadline or seen>=self.max_expressions:
                break
            for expr in tuple(pool.get(nodes,())):
                if expr.out_type==state_type:
                    invented=test_candidate(expr)
                    if invented is not None:return invented
            if nodes==self.max_nodes:break
            size=nodes+1
            for name,operand_types,outtype,fn in _primitive_ops():
                arity=len(operand_types)
                for sizes in product(range(1,size),repeat=arity):
                    if sum(sizes)!=size-1:continue
                    options=tuple(
                        [expr for expr in pool.get(n,())
                         if expr.out_type==want]
                        for n,want in zip(sizes,operand_types))
                    if any(not part for part in options):continue
                    for terms in product(*options):
                        if seen>=self.max_expressions or perf_counter_ns()>deadline:
                            break
                        try:
                            result=tuple(fn(*(term.source_values[i]
                                              for term in terms))
                                         for i in range(len(inputs)))
                        except (TypeError,IndexError,ValueError,
                                OverflowError,ZeroDivisionError):
                            continue
                        if all(_bounded_state(v) for v in result):
                            insert((name,)+tuple(t.ast for t in terms),
                                   outtype,size,result)
        raise ValueError(
            "ABSTAIN: no independently SOURCE-verified latent "
            "multi-step process compatible with endpoint observations")
