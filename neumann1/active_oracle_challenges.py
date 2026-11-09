"""Q3: active challenge queries for falsely generalized source-fit programs.

An oracle is ONLY a function from proposed INPUT to observed SOURCE OUTPUT.
The learner cannot inspect the author's reference implementation, hidden
TARGET outputs, task ID, or previously scored test. An independent benchmark
adapter enforces the oracle's finite input budget and isolated execution.

Queries are generated from structural perturbations of SOURCE inputs, without
program-family names or hidden expected outputs. A model's current executable
program ranks probes by predicted behavior changes and disagreement. Matched
random selection from the exact same candidate pool and oracle budget
distinguishes the value of active challenge selection from more observations.

An oracle response is learning data (a new SOURCE observation), NEVER test gold.
The evaluation must still freeze predictions before the held-out originals.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
import random
from difflib import SequenceMatcher


def _key(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=True,
                      separators=(",",":"),default=str)


def _unique(xs,*,limit=400):
    output=[]
    seen=set()
    for x in xs:
        try:
            key=_key(x)
        except (ValueError,TypeError,RecursionError):
            continue
        if len(key)>1300 or key in seen:
            continue
        seen.add(key)
        output.append(x)
        if len(output)>=limit:break
    return tuple(output)


def _scalar_variants(value):
    if type(value) is bool:
        return (not value,)
    if type(value) is int:
        if abs(value)>10**10:return ()
        a=[0,1,-1,2,3,value+1,value-1,value+2,value-2,
           value*2,value//2,abs(value),-value]
        if value>=0:
            digits=str(value)
            a.extend(int("".join(t)) for t in itertools.islice(
                itertools.permutations(digits),50))
            if len(digits)>1:
                a.extend((int("".join(sorted(digits))),
                          int("".join(sorted(digits,reverse=True))),
                          int(digits[-1]+digits[:-1]),
                          int(digits[1:]+digits[0]),
                          int(digits[0]+digits[-1]+digits[1:-1])))
        return _unique(a,limit=90)
    if type(value) is float:
        if not abs(value)<1e8:return ()
        return _unique((0,1,value+1,value-1,value*2,value/2,
                        round(value),abs(value),-value))
    if type(value) is str:
        if len(value)>150:return ()
        a=[
            "",value[::-1],value.lower(),value.upper(),
            value[:max(1,len(value)//2)],value[1:],value[:-1],
            value+value,value[:1],value[-1:],
            "".join(sorted(value)),"".join(sorted(value,reverse=True)),
            value[:1]*max(1,len(value)),value[-1:]*max(1,len(value)),
        ]
        if len(value)>2:
            a.extend((
                value[0]+value[2]+value[1]+value[3:],
                value[1]+value[0]+value[2:],
                value[0]+value[-1]+value[1:-1],
                value[:-2]+value[-1]+value[-2],
            ))
        if value.isalpha():
            a.extend((chr(v) for v in range(65,91)))
            a.extend((chr(v) for v in range(97,123)))
            a.extend(("AB","BA","AA","ABC","CBA","ABCD","BACD"))
        if "," in value:
            a.extend((value.split(",")[0],value.replace(",",""),
                      value.replace(",",";")))
        if "-" in value:
            a.extend((value.replace("-",""),value.split("-")[0]))
        return _unique(a,limit=100)
    return ()


def perturb_inputs(inputs,*,limit=320):
    """Typed structural transformations, never task-specific answer rules."""
    out=[]
    for x in inputs:
        if isinstance(x,(list,tuple)):
            seq=list(x)
            if not seq or len(seq)>64:continue
            if len(seq)==2:
                a,b=seq
                # Relational intervention: test equivalence, order, symmetry
                # and identity, whatever the contents' semantic domain.
                out.extend((
                    [a,a],[b,b],[b,a],
                    [a,b],[b,a],
                ))
                if type(a) is str and type(b) is str:
                    out.extend((
                        [a,a[::-1]],[a[::-1],a],
                        [a,b[::-1]],[a[::-1],b],
                        [a[:1],a[:1]],[b[:1],b[:1]],
                        [a[:1],b[:1]],[b[:1],a[:1]],
                        [a+b,b+a],[b+a,a+b],
                        [a.upper(),a.upper()],
                    ))
                if type(a) is int and type(b) is int:
                    out.extend((
                        [a,0],[a,1],[a,a],[b,a],
                        [a+1,b],[a,b+1],[a*2,b],[a,b*2]))
            if all(type(v) is int for v in seq):
                out.extend((
                    list(reversed(seq)),
                    sorted(seq),sorted(seq,reverse=True),
                    seq+seq,
                    [seq[0]]*len(seq),
                    list(dict.fromkeys(seq))))
            if all(type(v) is str for v in seq):
                out.extend((
                    list(reversed(seq)),sorted(seq),
                    [v[::-1] for v in seq]))
            for i,v in enumerate(seq[:5]):
                for alternative in _scalar_variants(v)[:22]:
                    y=list(seq)
                    y[i]=alternative
                    out.append(y)
            out.extend((seq[:-1],seq[1:],seq+[seq[0]]))
        else:
            out.extend(_scalar_variants(x))
    return _unique(out,limit=limit)


def _structural_distance(x,y):
    a,b=_key(x),_key(y)
    ratio=SequenceMatcher(None,a,b).ratio()
    return 1-ratio


def _relational_novelty(x,old):
    """Numeric+string equality symmetry are generic input interventions."""
    if not isinstance(x,(list,tuple)) or len(x)!=2:
        return 0.0
    if x[0]!=x[1]:return 0.0
    if any(isinstance(y,(list,tuple)) and len(y)==2
           and y[0]==y[1] for y in old):
        return 0.0
    return 0.7


@dataclass(frozen=True)
class ProbeBatch:
    queries:tuple
    pool_count:int
    policy:str
    selected_sha256:str
    disagreements:int


def choose_probes(source_pairs,*,count=4,mode="active",
                  prediction_functions=(),seed=1007):
    """Freeze probe inputs BEFORE the oracle reveals any labels.

    Prediction functions only provide outputs on inputs; the controller does
    not receive source code or target gold. If no runnable model exists,
    active structural novelty still explores observed invariances.
    """
    if mode not in ("active","random"):raise ValueError("mode")
    if not 1<=count<=12:raise ValueError("finite oracle query budget")
    observed=[a for a,b in source_pairs]
    forbidden={_key(x) for x in observed}
    pool=[p for p in perturb_inputs(observed)
          if _key(p) not in forbidden]
    if not pool:raise ValueError("no valid contrast inputs")
    rng=random.Random(seed)
    if mode=="random":
        selected=rng.sample(pool,min(count,len(pool)))
        return ProbeBatch(tuple(selected),len(pool),mode,
                          hashlib.sha256(_key(selected).encode()).hexdigest(),0)
    scored=[]
    for order,p in enumerate(pool):
        opinions=[]
        for fn in prediction_functions[:4]:
            try:
                out=fn(p)
                opinions.append(_key(out))
            except Exception:
                pass
        disagree=int(len(set(opinions))>1)
        distance=min((_structural_distance(p,x) for x in observed),
                     default=0.0)
        contrast=_relational_novelty(p,observed)
        # Diversity of predicted behavior and structural invariants. Sorting
        # not based on oracle response. No benchmark task ID dependence.
        score=3.0*disagree+contrast+0.5*distance
        scored.append((-score,order,p,disagree))
    scored.sort(key=lambda x:(x[0],x[1]))
    selected=[]
    disagreements=0
    for negative_score,order,p,disagree in scored:
        if len(selected)>=count:break
        if any(_structural_distance(p,x)<0.06 for x in selected):
            continue
        selected.append(p)
        disagreements+=disagree
    if len(selected)<count:
        for _,_,p,disagree in scored:
            if len(selected)>=count:break
            if _key(p) not in {_key(x) for x in selected}:
                selected.append(p)
                disagreements+=disagree
    return ProbeBatch(
        tuple(selected),len(pool),mode,
        hashlib.sha256(_key(selected).encode()).hexdigest(),
        disagreements)


@dataclass(frozen=True)
class OracleEvidence:
    inputs:tuple
    outputs:tuple
    query_count:int
    input_sha256:str
    refuted_model_count:int
    executable_program_count:int


def source_intervention(batch,*,reference_oracle,prediction_functions=()):
    """Only this explicit boundary may request new true SOURCE labels.

    reference_oracle is a black box. This API never reads any reference
    implementation. The integration runner owns separate author code.
    """
    answers=[]
    for x in batch.queries:
        answers.append(reference_oracle(x))
    refutations=0
    for fn in prediction_functions[:4]:
        for x,y in zip(batch.queries,answers):
            try:
                if fn(x)!=y:
                    refutations+=1
            except Exception:
                refutations+=1
    return OracleEvidence(
        batch.queries,tuple(answers),len(answers),
        batch.selected_sha256,refutations,len(prediction_functions))
