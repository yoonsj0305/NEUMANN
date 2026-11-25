"""Actively synthesize an exact rational polynomial representation from a source oracle.

The term basis, degree, sparse coefficients and executable function are
constructed from source observations. No task formula or target outputs enter
synthesis. Exactness outside source is conditional on bounded polynomial prior;
finite observations cannot certify that prior for arbitrary functions.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from random import Random
from typing import Callable

from .monoid_operator_inventor import EvidenceInsufficient
from .active_law_inventor import BudgetExhausted


def _monomials(dim, degree):
    return tuple(sorted((powers for powers in product(range(degree+1),repeat=dim)
                  if sum(powers)<=degree),key=lambda p:(sum(p),p)))


def _evaluate(powers,point):
    value=Fraction(1)
    for x,exp in zip(point,powers):
        value*=x**exp
    return value


def _fit(xs,ys,terms):
    """Exact Gauss-Jordan over Q, return None for no unique exact fit."""
    k=len(terms)
    if len(xs)<k:return None
    mat=[[_evaluate(term,x) for term in terms]+[y] for x,y in zip(xs,ys)]
    pivots=[]; r=0
    for c in range(k):
        pivot=next((i for i in range(r,len(mat)) if mat[i][c]!=0),None)
        if pivot is None:continue
        mat[r],mat[pivot]=mat[pivot],mat[r]
        den=mat[r][c]
        mat[r]=[v/den for v in mat[r]]
        for i in range(len(mat)):
            if i!=r and mat[i][c]!=0:
                scale=mat[i][c]
                mat[i]=[mat[i][j]-scale*mat[r][j] for j in range(k+1)]
        pivots.append(c);r+=1
        if r==len(mat):break
    if any(all(v==0 for v in row[:k]) and row[k]!=0 for row in mat):
        return None
    if len(pivots)!=k:return None
    coeff=[Fraction(0)]*k
    for i,c in enumerate(pivots):coeff[c]=mat[i][k]
    return tuple(coeff)


@dataclass(frozen=True)
class InventedNumericFunction:
    arity:int
    degree:int
    terms:tuple[tuple[int,...],...]
    coefficients:tuple[Fraction,...]
    source_facts:tuple[tuple[tuple[Fraction,...],Fraction],...]
    validation_queries:int
    validated_source_only:bool=True

    @property
    def nonzero_terms(self):
        return tuple((p,c) for p,c in zip(self.terms,self.coefficients) if c)

    def apply(self,*values):
        if len(values)!=self.arity:raise EvidenceInsufficient('arity mismatch')
        if not all(isinstance(x,(int,Fraction)) and not isinstance(x,bool)
                   for x in values):raise EvidenceInsufficient('exact rational input required')
        point=tuple(Fraction(x) for x in values)
        return sum((c*_evaluate(p,point)
                    for p,c in zip(self.terms,self.coefficients)),Fraction(0))


def invent_numeric_function(oracle:Callable, *, arity:int,
                            max_degree:int=3, budget:int=120,
                            validation:int=6, seed:int=0,
                            coordinate_bound:int=30):
    if arity<1 or arity>4 or max_degree<0 or max_degree>5:
        raise EvidenceInsufficient('unsupported bounded symbolic search')
    if validation<1 or budget<2 or coordinate_bound<2:
        raise EvidenceInsufficient('invalid exploration budget')
    rng=Random(seed)
    seen={}
    def ask(point):
        point=tuple(Fraction(x) for x in point)
        if point not in seen:
            if len(seen)>=budget:raise BudgetExhausted('numeric source query budget exhausted')
            output=oracle(*point)
            if not isinstance(output,(int,Fraction)) or isinstance(output,bool):
                raise EvidenceInsufficient('exact numerical oracle output required')
            seen[point]=Fraction(output)
        return seen[point]
    # Generate generic source coordinates; no knowledge of task formula.
    def new_point():
        for _ in range(1000):
            p=tuple(Fraction(rng.randint(-coordinate_bound,coordinate_bound))
                    for _ in range(arity))
            if p not in seen:return p
        raise EvidenceInsufficient('insufficient distinct source coordinates')
    for degree in range(max_degree+1):
        basis=_monomials(arity,degree)
        required=len(basis)+2
        while len(seen)<required:
            ask(new_point())
        # If the available samples do not span the feature basis, keep probing
        # until rank is full or the common source budget expires.
        for _ in range(budget-len(seen)+1):
            xs=list(seen);ys=[seen[x] for x in xs]
            coeff=_fit(xs,ys,basis)
            if coeff is not None:
                witness=[]
                falsified=False
                for _ in range(validation):
                    p=new_point()
                    guess=sum((c*_evaluate(t,p) for t,c in zip(basis,coeff)),Fraction(0))
                    target=ask(p)
                    witness.append((p,target))
                    if target!=guess:
                        falsified=True
                        break
                if not falsified:
                    return InventedNumericFunction(
                        arity=arity,degree=degree,terms=basis,coefficients=coeff,
                        source_facts=tuple(seen.items()),validation_queries=len(witness))
                # False prediction: do not accept; try more expressive basis.
                break
            # No fit means either inconsistent or rank deficient. When current
            # degree does not fit, adding more points cannot repair it.
            if len(seen)>required+arity+3:
                break
            ask(new_point())
    raise EvidenceInsufficient('no source-supported bounded polynomial construction')
