"""RC39 classical active state-structure induction from SOURCE word I/O only.

Learner knows input alphabet and visible output alphabet, NOT target state
count, transition graph, family labels, or hidden implementation. It builds a
Mealy machine by observable residual-output signatures and counterexamples.

All proof/equivalence rights are explicitly counted. The exact oracle is a
strong external resource, NOT an autonomous neural discovery achievement.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from time import process_time_ns
from typing import Any

class UnknownStateStructure(RuntimeError):
    pass

@dataclass(frozen=True)
class MealyProgram:
    alphabet: tuple[str,...]
    outputs: tuple[str,...]
    transitions: tuple[tuple[int,...],...]
    emissions: tuple[tuple[str,...],...]
    initial: int=0

    def run(self, word: str) -> str:
        state=self.initial
        out=[]
        for char in word:
            try: k=self.alphabet.index(char)
            except ValueError: raise UnknownStateStructure("unknown symbol")
            out.append(self.emissions[state][k])
            state=self.transitions[state][k]
        return "".join(out)

    def to_source(self) -> dict[str,Any]:
        return {"schema":"neumann.rc39.mealy-ast.v1","alphabet":list(self.alphabet),
                "outputs":list(self.outputs),"initial":self.initial,
                "states":len(self.transitions),
                "transitions":[list(r) for r in self.transitions],
                "emissions":[list(r) for r in self.emissions]}

    @staticmethod
    def from_source(src: dict[str,Any]) -> "MealyProgram":
        if not isinstance(src,dict) or set(src)!={"schema","alphabet","outputs","initial","states","transitions","emissions"}:
            raise UnknownStateStructure("bad AST keys")
        if src["schema"]!="neumann.rc39.mealy-ast.v1":raise UnknownStateStructure("invalid schema")
        alphabet=tuple(src["alphabet"])
        outputs=tuple(src["outputs"])
        n=src["states"]
        if (not isinstance(n,int) or type(n) is bool or not 1<=n<=16 or
            not isinstance(src["initial"],int) or not 0<=src["initial"]<n or
            len(alphabet) not in range(1,9) or len(set(alphabet))!=len(alphabet) or
            any(not isinstance(x,str) or len(x)!=1 for x in alphabet) or
            len(outputs) not in range(1,9) or len(set(outputs))!=len(outputs) or
            any(not isinstance(x,str) or len(x)!=1 for x in outputs)):
            raise UnknownStateStructure("invalid dimensions")
        trans=src["transitions"];emits=src["emissions"]
        if not isinstance(trans,list) or not isinstance(emits,list) or len(trans)!=n or len(emits)!=n:
            raise UnknownStateStructure("invalid table size")
        for t,e in zip(trans,emits):
            if (not isinstance(t,list) or not isinstance(e,list) or
                len(t)!=len(alphabet) or len(e)!=len(alphabet) or
                any(type(x)!=int or not 0<=x<n for x in t) or
                any(x not in outputs for x in e)):
                raise UnknownStateStructure("bad transition/output")
        return MealyProgram(alphabet,outputs,tuple(tuple(row) for row in trans),
                            tuple(tuple(row) for row in emits),src["initial"])

@dataclass
class InductionReceipt:
    source: dict[str,Any]|None
    status: str
    counterexamples: list[str]
    membership_calls: int
    membership_symbols: int
    equivalence_calls: int
    hypothesis_states: int|None
    process_cpu_ms: float
    source_observations: int
    provenance: str="classical-active-lstar-known-general-metalanguage"

class ActiveMealyLearner:
    """L* observation-table/CEGIS learner. Oracles are injected, never imported."""
    def __init__(self, alphabet: str, outputs: str, *, max_states=8,
                 max_membership=20000, max_equivalence=200):
        if len(alphabet)!=len(set(alphabet)) or not alphabet or not outputs:
            raise ValueError("invalid source alphabet")
        self.alpha=tuple(alphabet);self.outputs=tuple(outputs)
        self.max_states=max_states
        self.max_membership=max_membership
        self.max_equivalence=max_equivalence

    def learn(self, membership, equivalence)->InductionReceipt:
        start=process_time_ns()
        cache:dict[str,str]={}
        count=0;symbols=0;eq_count=0;cexs=[]
        S=[""];E=list(self.alpha)
        def query(word:str)->str:
            nonlocal count,symbols
            if word not in cache:
                if count>=self.max_membership:
                    raise UnknownStateStructure("MEMBERSHIP_BUDGET_EXHAUSTED")
                raw=membership(word)
                if type(raw)!=str or len(raw)!=len(word) or any(x not in self.outputs for x in raw):
                    raise UnknownStateStructure("INVALID_ORACLE_OUTPUT")
                cache[word]=raw
                count+=1;symbols+=len(word)
            return cache[word]
        def row(u:str)->tuple[str,...]:
            return tuple(query(u+e)[len(u):] for e in E)
        def finish(status,model=None):
            return InductionReceipt(
                model.to_source() if model else None,status,cexs[:],count,symbols,eq_count,
                None if model is None else len(model.transitions),
                (process_time_ns()-start)/1e6,len(cache))
        try:
            while True:
                # Closed, consistent finite quotient of observed source traces.
                for iteration in range(500):
                    representatives={row(s):s for s in S}
                    new_prefix=None
                    for s in S:
                        for a in self.alpha:
                            sa=s+a
                            if row(sa) not in representatives:
                                new_prefix=sa
                                break
                        if new_prefix is not None:break
                    if new_prefix is not None:
                        if new_prefix not in S:S.append(new_prefix)
                        if len(S)>self.max_states*8:
                            raise UnknownStateStructure("PREFIX_BUDGET_EXHAUSTED")
                        continue
                    added=None
                    for i,s in enumerate(S):
                        for t in S[i+1:]:
                            if row(s)!=row(t):continue
                            for a in self.alpha:
                                if query(s+a)[len(s)]!=query(t+a)[len(t)]:
                                    added=a;break
                                if row(s+a)!=row(t+a):
                                    for e in E:
                                        if query(s+a+e)[len(s)+1:]!=query(t+a+e)[len(t)+1:]:
                                            added=a+e;break
                                    if added is None:raise UnknownStateStructure("CONSISTENCY_MISSING_WITNESS")
                                    break
                            if added is not None:break
                        if added is not None:break
                    if added is not None:
                        if added in E:
                            raise UnknownStateStructure("STALLED_DISTINGUISHING_SUFFIX")
                        E.append(added)
                        continue
                    break
                else:
                    raise UnknownStateStructure("OBSERVATION_TABLE_ITERATION_BUDGET")
                signatures={}
                for s in S:
                    k=row(s)
                    if k not in signatures:signatures[k]=s
                ordered=list(signatures.items())
                if len(ordered)>self.max_states:
                    raise UnknownStateStructure("MODEL_STATE_LIMIT")
                state_ids={k:i for i,(k,_) in enumerate(ordered)}
                initial_id=state_ids[row("")]
                trans=[];emissions=[]
                for key,rep in ordered:
                    tr=[];eo=[]
                    for a in self.alpha:
                        successor=row(rep+a)
                        if successor not in state_ids:
                            raise UnknownStateStructure("MODEL_NOT_CLOSED")
                        tr.append(state_ids[successor])
                        eo.append(query(rep+a)[len(rep)])
                    trans.append(tuple(tr));emissions.append(tuple(eo))
                model=MealyProgram(self.alpha,self.outputs,tuple(trans),tuple(emissions),initial_id)
                if eq_count>=self.max_equivalence:
                    raise UnknownStateStructure("EQUIVALENCE_BUDGET_EXHAUSTED")
                eq_count+=1
                answer=equivalence(model)
                if answer is None:
                    return finish("SCOPED_ALL_LENGTHS_PROVED",model)
                if type(answer)!=str or not answer or any(x not in self.alpha for x in answer):
                    raise UnknownStateStructure("INVALID_COUNTEREXAMPLE")
                if model.run(answer)==query(answer):
                    raise UnknownStateStructure("UNSOUND_COUNTEREXAMPLE_ORACLE")
                cexs.append(answer)
                grew=False
                for i in range(len(answer)):
                    suffix=answer[i:]
                    if suffix not in E:E.append(suffix);grew=True
                for i in range(len(answer)+1):
                    prefix=answer[:i]
                    if prefix not in S:S.append(prefix);grew=True
                if not grew:
                    raise UnknownStateStructure("COUNTEREXAMPLE_NO_PROGRESS")
        except UnknownStateStructure as exc:
            return finish("UNKNOWN:"+str(exc))
