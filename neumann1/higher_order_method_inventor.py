"""Q3: source-learned algorithm-generator that rewrites its own control AST.

The control grammar is composed from VM primitives, not domain solutions.
A frozen learned method accepts a *new* classical transition T and compiles
a solver. It is guaranteed only if T converges to a fixed point in budget.
"""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter_ns


@dataclass(frozen=True)
class ControlProgram:
    ast: tuple
    max_steps: int = 256

    def compile(self, transition, *, known_classical=None,
                independent_source_checks=()):
        if known_classical is not None:
            checks=tuple(independent_source_checks)
            if not checks or any(known_classical(x)!=y for x,y in checks):
                raise ValueError("classical candidate lacks source verification")
            return CompiledMethod(("classical_first",),known_classical,0)
        if not callable(transition):
            raise TypeError("typed transition required")
        return CompiledMethod(self.ast,transition,self.max_steps)


@dataclass(frozen=True)
class Execution:
    status: str
    value: object
    transition_calls: int


@dataclass(frozen=True)
class CompiledMethod:
    ast: tuple
    transition: object
    max_steps: int

    def run(self, initial):
        if self.ast[0]=="classical_first":
            return Execution("CLASSICAL",self.transition(initial),0)
        current=initial
        tag=self.ast[0]
        calls=0
        if tag=="sequence":
            if self.ast[2]!=("apply","transition"):
                raise ValueError("ill-typed VM action")
            for _ in range(self.ast[1]):
                current=self.transition(current)
                calls+=1
            return Execution("HALT_UNROLL",current,calls)
        if tag!="while" or self.ast[2]!=("apply","transition"):
            raise ValueError("invalid generated method AST")
        condition=self.ast[1]

        def read(expr,c,n):
            if expr[0]=="read" and expr[1] in ("current","next"):
                return c if expr[1]=="current" else n
            if expr[0]=="project":
                val=read(expr[2],c,n)
                if expr[1]=="length":return len(val)
                if expr[1]=="head":return val[0]
            raise ValueError("unknown typed source projection")

        def evaluate(expr,c,n):
            if expr[0]=="not":return not evaluate(expr[1],c,n)
            if expr[0]=="equal":
                return read(expr[1],c,n)==read(expr[2],c,n)
            raise ValueError("unknown typed control guard")

        full_state_guard=(
            "not",("equal",("read","current"),("read","next")))
        for _ in range(self.max_steps):
            nxt=self.transition(current)
            calls+=1
            if not evaluate(condition,current,nxt):
                status=("HALT_CERTIFIED_FIXED_POINT"
                        if condition==full_state_guard else
                        "HALT_PREDICATE")
                return Execution(status,nxt,calls)
            current=nxt
        return Execution("ABSTAIN_BUDGET",None,calls)


@dataclass(frozen=True)
class SourceCase:
    transition: object
    initial: object
    expected: object
    group: str = "audit_only"


@dataclass(frozen=True)
class MetaRecord:
    program: ControlProgram
    passed: int
    failed: int
    transition_calls: int


@dataclass(frozen=True)
class InventedMethod:
    program: ControlProgram
    meta_records: tuple[MetaRecord,...]
    source_cases: int
    prior_ast: tuple|None
    counterexamples: int
    elapsed_ms: float


class HigherOrderMethodInventor:
    """Construct new algorithm generators through compositional VM search.

    The VM has read/project/equal/not/apply/sequence/while instructions.
    It is NOT supplied the complete method "repeat until state unchanged".
    The learner selects a newly assembled AST from SOURCE I/O and may
    revise it when later SOURCE counterexamples falsify it.
    """

    def __init__(self, *, max_unroll=3,max_steps=256):
        if not (type(max_unroll) is int and 1<=max_unroll<=32
                and type(max_steps) is int and 2<=max_steps<=10000):
            raise ValueError("finite typed search budget required")
        self.max_unroll=max_unroll
        self.max_steps=max_steps

    def grammar(self):
        action=("apply","transition")
        for n in range(1,self.max_unroll+1):
            yield ControlProgram(("sequence",n,action),self.max_steps)
        terminals=(("read","current"),("read","next"))
        projections=terminals+tuple(
            ("project",field,t)
            for field in ("length","head")
            for t in terminals)
        for a in projections:
            for b in projections:
                predicate=("equal",a,b)
                for guard in (predicate,("not",predicate)):
                    yield ControlProgram(("while",guard,action),
                                         self.max_steps)

    def discover(self,source_cases, *, old=None):
        start=perf_counter_ns()
        sources=tuple(source_cases)
        if len(sources)<4:
            raise ValueError("at least four independent source cases required")
        records=[]
        for candidate in self.grammar():
            passed=failed=calls=0
            for src in sources:
                try:
                    result=candidate.compile(src.transition).run(src.initial)
                    right=(result.value==src.expected and
                           result.status!="ABSTAIN_BUDGET")
                    calls+=result.transition_calls
                    passed+=int(right)
                    failed+=int(not right)
                except (TypeError,ValueError,IndexError):
                    failed+=1
            records.append(MetaRecord(candidate,passed,failed,calls))

        def information_cost(program):
            # Prefer a smaller information projection under equal source
            # correctness/calls, not a claim about measured CPU runtime.
            s=repr(program.ast)
            if "'project', 'head'" in s:return 0
            if "'project', 'length'" in s:return 1
            return 2 if program.ast[0]=="while" else 0

        winner=min(records,key=lambda r:(
            -r.passed,r.failed,r.transition_calls,
            information_cost(r.program),
            len(repr(r.program.ast)),repr(r.program.ast)))
        if winner.passed!=len(sources):
            raise ValueError("no source-complete invented control program")
        falsified=0
        if old is not None:
            for src in sources:
                try:
                    output=old.program.compile(src.transition).run(src.initial)
                    falsified+=int(output.value!=src.expected)
                except (TypeError,ValueError,IndexError):
                    falsified+=1
            if not falsified or winner.program.ast==old.program.ast:
                raise ValueError("no actual method-level counterexample repair")
        return InventedMethod(
            winner.program,tuple(records),len(sources),
            None if old is None else old.program.ast,falsified,
            (perf_counter_ns()-start)/1e6)


def conditional_proof():
    return (
        "Let T be deterministic. If T^m(x)=T^(m+1)(x) for some m "
        "with m+1<=B, then the compiled while-state-changed method with "
        "budget B returns T^m(x). Proof: induction over executed transitions "
        "gives x_t=T^t(x); a reached fixed point stays fixed under T. "
        "Existence of such m and task-semantic correctness are NOT guaranteed."
    )
