"""Q3: invent a new latent feature language from raw binary input/output facts.

General source-side algorithm, not a numeric/graph/string task-specific
operator: create interaction features as needed, solve exact constraints in
GF(2), and emit a NEW executable polynomial representation (ANF).

The method and GF(2) algebra are conventional classical algorithms; the
interaction masks and exact executable representation are learned from data.
The uniqueness proof is CONDITIONAL on a bounded-degree polynomial model.
Arbitrary-function or frontier-level Q3 remains OPEN.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from math import comb
from random import Random
from time import perf_counter_ns
from typing import Callable


class IncompleteInformation(ValueError):
    pass


def _validate_point(x, width):
    if not isinstance(x,(tuple,list)) or len(x)!=width:
        raise IncompleteInformation("raw Boolean width mismatch")
    if any(type(bit) is not int or bit not in (0,1) for bit in x):
        raise IncompleteInformation("raw Boolean input required")
    return tuple(x)


def _basis(width,degree):
    return tuple(sum(1<<j for j in coords)
                 for k in range(degree+1)
                 for coords in combinations(range(width),k))


def _encode(x):
    return sum(v<<i for i,v in enumerate(x))


def _feature_row(x,masks):
    return sum(1<<i for i,m in enumerate(masks) if x&m==m)


def _gf2_unique(rows,outputs,count):
    """Classical exact elimination with uniqueness/inconsistency certificate."""
    pivots={}
    for row,label in zip(rows,outputs):
        r,y=row,label
        while r:
            p=r.bit_length()-1
            if p not in pivots:
                pivots[p]=(r,y)
                break
            prior,known=pivots[p]
            r^=prior
            y^=known
        if not r and y:
            return None,len(pivots),True
    rank=len(pivots)
    if rank<count:
        return None,rank,False
    coefficients=0
    for pivot in sorted(pivots):
        row,label=pivots[pivot]
        prior=row&((1<<pivot)-1)
        bit=label^((prior&coefficients).bit_count()&1)
        coefficients|=bit<<pivot
    if any((r&coefficients).bit_count()%2!=y
           for r,y in zip(rows,outputs)):
        raise AssertionError("GF2 source certificate invalid")
    return coefficients,rank,False


@dataclass(frozen=True)
class InventedRepresentation:
    input_width:int
    degree:int
    latent_features:tuple[int,...]
    proof_rank:int
    discovery_ms:float
    source_count:int
    verifier_count:int
    checked_degrees:tuple[int,...]

    @property
    def ast(self):
        return ("learned_GF2_polynomial_representation",self.input_width,
                self.degree,
                tuple(("source_inferred_interaction_mask",mask)
                      for mask in self.latent_features),
                ("reduce","xor"))

    @property
    def latent_dimension(self):
        return len(self.latent_features)

    @property
    def proof(self):
        return ("Conditional on exact degree <= k Boolean polynomial: "
                "full column rank of source design matrix proves a unique "
                "matching polynomial within the bounded-degree language.")

    def representation(self,raw):
        x=_encode(_validate_point(raw,self.input_width))
        return tuple(int(x&m==m) for m in self.latent_features)

    def apply(self,raw):
        return sum(self.representation(raw))%2


@dataclass(frozen=True)
class Discovery:
    status:str
    program:InventedRepresentation|None
    classical:Callable|None
    source_checks:int
    degrees_tried:tuple[int,...]
    elapsed_ms:float
    failure:str|None=None

    def apply(self,raw):
        if self.status=="CLASSICAL_VERIFIED" and self.classical is not None:
            return self.classical(raw)
        if self.status=="SOURCE_VERIFIED_NEW_REPRESENTATION" and self.program:
            return self.program.apply(raw)
        raise IncompleteInformation("not source-verified, abstain")


class CausalRepresentationInventor:
    def __init__(self,*,max_degree=3,max_features=1000,max_width=20,
                 max_source_ms=3000):
        if not (type(max_degree) is int and 0<=max_degree<=8
                and type(max_features) is int and max_features>=1
                and type(max_width) is int and 1<=max_width<=32
                and type(max_source_ms) in (int,float)
                and 1<=max_source_ms<=120000):
            raise ValueError("finite typed representation search budgets")
        self.max_degree=max_degree
        self.max_features=max_features
        self.max_width=max_width
        self.max_source_ms=max_source_ms

    def invent(self,source_pairs,*,independent_source_checks,
               classical_solvers=()):
        start=perf_counter_ns()
        train=tuple(source_pairs)
        checks=tuple(independent_source_checks)
        if len(train)<2 or not checks:
            raise IncompleteInformation("two sources and independent checks required")
        width=len(train[0][0])
        if width<1 or width>self.max_width:
            raise IncompleteInformation("bounded bit width required")
        seen=set()
        for x,y in train+checks:
            x=_validate_point(x,width)
            if type(y) is not int or y not in (0,1):
                raise IncompleteInformation("binary output required")
            if x in seen:
                raise IncompleteInformation("source verifier must be disjoint")
            seen.add(x)
        # A fully adequate known classical solver gets precedence. No
        # representation discovery is attempted if it already solves source.
        for classical in classical_solvers:
            if all(classical(x)==y for x,y in train+checks):
                return Discovery("CLASSICAL_VERIFIED",None,classical,
                                 len(train)+len(checks),(),
                                 (perf_counter_ns()-start)/1e6)
        degrees=[]
        cumulative=0
        for degree in range(self.max_degree+1):
            if (perf_counter_ns()-start)/1e6>self.max_source_ms:
                return Discovery("ABSTAIN_BUDGET",None,None,cumulative,
                                 tuple(degrees),(perf_counter_ns()-start)/1e6)
            nfeatures=sum(comb(width,k) for k in range(degree+1))
            if nfeatures>self.max_features:
                return Discovery("ABSTAIN_BUDGET",None,None,cumulative,
                                 tuple(degrees),(perf_counter_ns()-start)/1e6)
            masks=_basis(width,degree)
            rows=[_feature_row(_encode(x),masks) for x,y in train]
            labels=[y for x,y in train]
            coefficients,rank,inconsistent=_gf2_unique(
                rows,labels,nfeatures)
            cumulative+=len(train)
            degrees.append(degree)
            if inconsistent:
                continue
            if coefficients is None:
                return Discovery("ABSTAIN_UNIDENTIFIABLE",None,None,cumulative,
                                 tuple(degrees),(perf_counter_ns()-start)/1e6,
                                 f"rank={rank}, features={nfeatures}")
            invented=InventedRepresentation(
                width,degree,
                tuple(mask for i,mask in enumerate(masks)
                      if coefficients&(1<<i)),
                rank,(perf_counter_ns()-start)/1e6,len(train),
                len(checks),tuple(degrees))
            cumulative+=len(checks)
            if all(invented.apply(x)==y for x,y in checks):
                return Discovery("SOURCE_VERIFIED_NEW_REPRESENTATION",
                                 invented,None,cumulative,tuple(degrees),
                                 (perf_counter_ns()-start)/1e6)
            return Discovery("ABSTAIN_VERIFIER_COUNTEREXAMPLE",None,None,
                             cumulative,tuple(degrees),
                             (perf_counter_ns()-start)/1e6)
        return Discovery("ABSTAIN_OUTSIDE_LANGUAGE",None,None,cumulative,
                         tuple(degrees),(perf_counter_ns()-start)/1e6)


@dataclass(frozen=True)
class ActiveDiscovery:
    discovery:Discovery
    source_probes:int
    source_verification_probes:int
    domain_size:int
    source_examples:tuple

    @property
    def source_probe_fraction(self):
        return self.source_probes/self.domain_size


def invent_with_active_source_queries(source_oracle,*,width,max_degree=3,
                                     independent_checks=64,seed=1007,
                                     classical_solvers=()):
    """Design a rank-complete SOURCE experiment before any outputs are known.

    The source oracle is an explicit experiment interface, never a private
    target evaluation source. Query choice depends only on input width and
    allowable representation degree, not gold outputs.
    """
    if not (callable(source_oracle) and type(width) is int
            and 1<=width<=20 and type(max_degree) is int
            and 0<=max_degree<=width and type(independent_checks) is int
            and independent_checks>=1 and type(seed) is int):
        raise ValueError("bounded source query plan")
    basis=_basis(width,max_degree)
    sample=tuple(tuple(int(m&(1<<j)!=0) for j in range(width))
                 for m in basis)
    total=1<<width
    if len(sample)+independent_checks>=total:
        raise IncompleteInformation("no disjoint verifier and heldout pool")
    excluded=set(sample)
    remainder=[tuple((k>>j)&1 for j in range(width))
               for k in range(total)
               if tuple((k>>j)&1 for j in range(width)) not in excluded]
    Random(seed).shuffle(remainder)
    source=tuple((x,source_oracle(x)) for x in sample)
    verification=tuple((x,source_oracle(x))
                       for x in remainder[:independent_checks])
    discovery=CausalRepresentationInventor(
        max_degree=max_degree,max_width=width).invent(
        source,independent_source_checks=verification,
        classical_solvers=classical_solvers)
    return ActiveDiscovery(discovery,len(source),len(verification),
                           total,source)
