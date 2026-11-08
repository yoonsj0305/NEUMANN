"""Q3: learn an EXECUTABLE RECURSIVE DISCOVERY METHOD, not a task answer.

The meta language is typed and bounded. A policy AST decides how to propose,
challenge, refute, and expand hypotheses; it operates on unrelated classical
backends through the same interface. A new policy is chosen from performance
on source-development tasks, then frozen before unseen evaluation.

This demonstrates conditional method-level invention, NOT unrestricted
invention of primitive mathematics or universally correct induction.
"""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter_ns


class InsufficientEvidence(ValueError):
    pass


@dataclass(frozen=True)
class Step:
    status: str
    hypothesis: object | None
    dimension: int
    cost: int


@dataclass(frozen=True)
class RecursiveMethod:
    transition: tuple[str,int]
    challenges: int
    max_complexity: int

    @property
    def ast(self):
        return (
            "repeat",
            ("try_source_model","complexity"),
            ("challenge_fresh_source",self.challenges),
            ("on_verified","return_executable"),
            ("on_refuted",("update_complexity",self.transition)),
            ("on_unidentifiable","abstain"),
            ("guard","max_complexity",self.max_complexity),
        )

    def next_complexity(self,k):
        kind,n=self.transition
        if kind=="increment":
            return k+n
        if kind=="multiply":
            return k*n
        raise InsufficientEvidence("unknown meta update operation")


@dataclass(frozen=True)
class Episode:
    status: str
    model: object | None
    source_queries: int
    trace: tuple
    elapsed_ms: float

    def apply(self,x):
        if self.model is None:
            raise InsufficientEvidence("no certified executable")
        return self.model(x)


class ObservedOracle:
    """Source-only query interface. Shared caches count unique source cost.

    The local cache contains only observations THIS candidate asked about,
    while shared_cache counts all unique source labels used in meta training.
    Excluded TARGET labels can never enter source hypothesis fitting.
    """
    def __init__(self,oracle,forbidden=(),shared_cache=None):
        if not callable(oracle):
            raise TypeError("source oracle required")
        self.oracle=oracle
        self.forbidden=frozenset(forbidden)
        self.cache={}
        self.shared_cache=shared_cache

    def ask(self,x):
        if x in self.forbidden:
            raise InsufficientEvidence("target gold source-probe attempt")
        if x not in self.cache:
            if self.shared_cache is not None and x in self.shared_cache:
                self.cache[x]=self.shared_cache[x]
            else:
                self.cache[x]=self.oracle(x)
                if self.shared_cache is not None:
                    self.shared_cache[x]=self.cache[x]
        return self.cache[x]


def execute(method,backend,*,start=1,
            known_classical=(),classical_probe_inputs=()):
    """Interpret an INVENTED procedure over any conforming source backend.

    The backend supplies attempt(complexity, challenges) -> Step, not a
    domain label. The interpreter has no access to target answer labels.
    """
    t0=perf_counter_ns()
    if not isinstance(method,RecursiveMethod):
        raise TypeError("compiled method required")
    if (type(start) is not int or start<1 or
            type(method.challenges) is not int or method.challenges<1 or
            type(method.max_complexity) is not int or
            method.max_complexity<start or method.max_complexity>64):
        raise ValueError("finite typed method budget")
    k=start
    seen=set()
    trace=[]

    def episode(status,model):
        return Episode(status,model,len(backend.source.cache),
                       tuple(trace),(perf_counter_ns()-t0)/1e6)

    if known_classical:
        probes=tuple(classical_probe_inputs)
        if not probes:
            raise ValueError("classical candidate needs source verifier")
        try:
            for classical in known_classical:
                if all(classical(x)==backend.source.ask(x) for x in probes):
                    trace.append(("CLASSICAL","SOURCE_VERIFIED"))
                    return episode("CLASSICAL_SOURCE_VERIFIED",classical)
        except InsufficientEvidence:
            return episode("ABSTAIN_SOURCE_LIMIT",None)

    while k<=method.max_complexity:
        if k in seen:
            return episode("ABSTAIN_LOOP",None)
        seen.add(k)
        try:
            result=backend.attempt(k,method.challenges)
        except InsufficientEvidence:
            return episode("ABSTAIN_SOURCE_LIMIT",None)
        trace.append((k,result.status))
        if result.status=="VERIFIED":
            if result.hypothesis is None:
                raise InsufficientEvidence("no verified executable")
            return episode("SOURCE_VERIFIED",result.hypothesis)
        if result.status=="UNIDENTIFIABLE":
            return episode("ABSTAIN_UNIDENTIFIABLE",None)
        if result.status!="REFUTED":
            raise InsufficientEvidence("unknown evidence state")
        nxt=method.next_complexity(k)
        if nxt<=k:
            raise InsufficientEvidence("learned recurrence must progress")
        k=nxt
    return episode("ABSTAIN_COMPLEXITY_LIMIT",None)


@dataclass(frozen=True)
class MetaCase:
    family: str  # Audit metadata ONLY, never an input to the policy
    backend_factory: object
    oracle: object
    heldout: tuple


@dataclass(frozen=True)
class LearnedMethod:
    method: RecursiveMethod
    correct_on_meta_training: int
    incorrect_on_meta_training: int
    total_source_queries: int
    training_cost_queries: int
    candidate_trace: tuple
    grade_label_cost: int
    meta_cpu_ms: float


class RecursiveMethodInventor:
    """Generate and choose conditional discovery ASTs from source feedback.

    The primitives and search grammar are human-designed; the concrete
    procedure AST, query budget and complexity transition are learned. A
    counterexample-bearing new meta task can revise the learned procedure.
    """
    def __init__(self,max_complexity=9,challenges=(4,8,16,32,64,96)):
        if (type(max_complexity) is not int or not 1<=max_complexity<=64
                or not challenges or any(type(k) is not int or
                                          not 1<=k<=1024 for k in challenges)):
            raise ValueError("bounded meta candidate budget")
        self.max_complexity=max_complexity
        self.challenges=tuple(challenges)

    def proposals(self):
        for kind,n in (("increment",1),("increment",2),("multiply",2)):
            for checks in self.challenges:
                yield RecursiveMethod((kind,n),checks,self.max_complexity)

    def learn(self,cases):
        start=perf_counter_ns()
        cases=tuple(cases)
        if not cases:
            raise ValueError("source-development tasks required")
        # Grade labels ARE exposed for META TRAINING, not withheld test.
        # Count them explicitly. All candidate hypotheses are forbidden
        # from probing these labels as SOURCE data.
        shared=[{} for _ in cases]
        grading=[tuple(case.oracle(x) for x in case.heldout)
                 for case in cases]
        scores=[]
        for candidate in self.proposals():
            correct=wrong=queries=0
            for i,case in enumerate(cases):
                source=ObservedOracle(case.oracle,case.heldout,shared[i])
                run=execute(candidate,case.backend_factory(source))
                queries+=run.source_queries
                if run.model is not None:
                    if all(run.apply(x)==y for x,y in
                           zip(case.heldout,grading[i])):
                        correct+=1
                    else:
                        wrong+=1
            scores.append((candidate,correct,wrong,queries))
        winner=min(scores,key=lambda r:(
            -r[1],r[2],r[3],len(str(r[0].ast))))
        return LearnedMethod(
            winner[0],winner[1],winner[2],winner[3],
            sum(len(cache) for cache in shared),tuple(scores),
            sum(len(c.heldout) for c in cases),
            (perf_counter_ns()-start)/1e6)
