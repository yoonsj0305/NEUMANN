"""REFERENCE CLASSICAL backends for testing a generic discovery-policy core.

These are NOT new task-specific NEUMANN inventors. They expose the same
attempt(complexity, source_checks) interface to the learned controller.
One backend uses GF2 polynomial interpolation, the other periodic symbolic
process induction. Neither domain name reaches the meta-policy interpreter.
"""
from random import Random
from neumann1.recursive_method_discovery import Step
from neumann1.causal_representation_inventor import (
    _basis,_encode,_feature_row,_gf2_unique,InventedRepresentation)


class BooleanPolynomialBackend:
    """Classical GF(2) interpolation with source-only experiment ledger."""
    def __init__(self,width,source,seed):
        self.width=width
        self.source=source
        self.rng=Random(seed)

    def attempt(self,k,checks):
        if k>self.width:
            return Step("UNIDENTIFIABLE",None,k,0)
        masks=_basis(self.width,k)
        for mask in masks:
            raw=tuple(int(bool(mask&(1<<i))) for i in range(self.width))
            self.source.ask(raw)
        observed=list(self.source.cache.items())
        rows=[_feature_row(_encode(x),masks) for x,_ in observed]
        coeff,rank,bad=_gf2_unique(rows,[y for _,y in observed],len(masks))
        if bad:
            return Step("REFUTED",None,k,len(masks))
        if coeff is None:
            return Step("UNIDENTIFIABLE",None,k,len(masks))
        model=InventedRepresentation(
            self.width,k,tuple(m for i,m in enumerate(masks)
                               if coeff&(1<<i)),rank,0,0,checks,())
        def executable(x):
            return model.apply(x)
        candidates=list(range(1<<self.width))
        self.rng.shuffle(candidates)
        n=0
        for v in candidates:
            x=tuple((v>>i)&1 for i in range(self.width))
            if x in self.source.forbidden or x in self.source.cache:
                continue
            truth=self.source.ask(x)
            n+=1
            if executable(x)!=truth:
                return Step("REFUTED",None,k,len(masks)+n)
            if n>=checks:
                break
        if n<checks:
            return Step("UNIDENTIFIABLE",None,k,len(masks)+n)
        return Step("VERIFIED",executable,k,len(masks)+n)


class PeriodicProcessBackend:
    """Independent semantics: classical repeated symbolic word inference."""
    def __init__(self,source,seed,max_source_index=200):
        self.source=source
        self.rng=Random(seed)
        self.max_source_index=max_source_index

    def attempt(self,k,checks):
        for t in range(2*k):
            self.source.ask(t)
        exemplar=tuple(self.source.ask(t) for t in range(k))
        model=lambda t,p=exemplar:t>=0 and p[t%len(p)]
        if any(model(t)!=v for t,v in self.source.cache.items()):
            return Step("REFUTED",None,k,2*k)
        probes=list(range(40,self.max_source_index))
        self.rng.shuffle(probes)
        n=0
        for t in probes:
            if t in self.source.forbidden or t in self.source.cache:
                continue
            v=self.source.ask(t)
            n+=1
            if model(t)!=v:
                return Step("REFUTED",None,k,2*k+n)
            if n>=checks:
                break
        if n<checks:
            return Step("UNIDENTIFIABLE",None,k,2*k+n)
        return Step("VERIFIED",model,k,2*k+n)
