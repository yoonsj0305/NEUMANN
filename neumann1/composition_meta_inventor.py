"""Task-family-independent invention by CEGIS composition of causal residuals.

One unchanged controller invents an executable COMPOSITION between a known
classical preprocessing operator and a source-induced residual solver.
Concrete interpreters may differ (finite grids, exact rational functions);
the learned grammar constructor does not dispatch on domain labels.
Classical solutions are accepted before any residual search. A learned
candidate must fit disjoint SOURCE verification examples to be promoted.

The base classical transformers and residual-learning algorithms are
human-provided; this is NOT universal invention of arbitrary semantics.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from time import perf_counter_ns
from typing import Callable

from .active_numeric_inventor import _fit, _monomials, _evaluate


@dataclass(frozen=True)
class CallablePrimitive:
    name: str
    execute: Callable

    def __post_init__(self):
        if type(self.name) is not str or not self.name or not callable(self.execute):
            raise ValueError("a stable named executable primitive is required")


@dataclass(frozen=True)
class InventedComposition:
    ast: tuple
    pre: CallablePrimitive
    residual: Callable
    source_fit_count: int
    verification_fit_count: int
    candidate_attempts: int
    elapsed_ms: float
    conditional_on_source_semantics: bool = True

    def apply(self, x):
        return self.residual(self.pre.execute(x))


@dataclass(frozen=True)
class CompositionDecision:
    status: str
    executable: object | None
    exact_source_checks: int
    residual_attempts: int
    elapsed_ms: float

    def apply(self, x):
        if self.executable is None:
            raise ValueError("unsupported or counterexample-falsified operator")
        if isinstance(self.executable, InventedComposition):
            return self.executable.apply(x)
        return self.executable.execute(x)


class CompositionInventor:
    """Invent across typed mathematical domains without a domain-name router."""

    def __init__(self, *, max_pre_candidates=16):
        if type(max_pre_candidates) is not int or max_pre_candidates<1:
            raise ValueError("bounded positive source program search required")
        self.max_pre_candidates=max_pre_candidates

    def discover(self, source_examples, source_verification,
                 *, classical_candidates, pre_candidates, learn_residual):
        t0=perf_counter_ns()
        train=list(source_examples)
        checks=list(source_verification)
        if len(train)<2 or not checks or not callable(learn_residual):
            raise ValueError("at least two source demonstrations, fresh verification and learner")
        if not all(isinstance(p,CallablePrimitive) for p in classical_candidates):
            raise TypeError("classical candidates must be executable primitives")
        if not all(isinstance(p,CallablePrimitive) for p in pre_candidates):
            raise TypeError("preprocessing candidates must be executable primitives")
        queried=0
        def agrees(fn,examples):
            nonlocal queried
            for x,y in examples:
                try:
                    out=fn(x)
                except (TypeError, ValueError, ArithmeticError):
                    return False
                queried+=1
                if out!=y:return False
            return True

        # Classical FIRST. A source-confirmed solution does not trigger
        # residual invention and does not require access to target labels.
        for classical in classical_candidates:
            if agrees(classical.execute,train) and agrees(classical.execute,checks):
                return CompositionDecision(
                    "CLASSICAL_VERIFIED",classical,queried,0,
                    (perf_counter_ns()-t0)/1e6)

        attempted=0
        for pre in list(pre_candidates)[:self.max_pre_candidates]:
            attempted+=1
            try:
                projected=[(pre.execute(x),y) for x,y in train]
                model=learn_residual(projected)
            except (TypeError, ValueError, ArithmeticError):
                model=None
            if model is None or not callable(model):
                continue
            candidate=InventedComposition(
                ast=("compose",("learned_residual",attempted),
                     ("classical",pre.name)),
                pre=pre,residual=model,source_fit_count=len(train),
                verification_fit_count=len(checks),
                candidate_attempts=attempted,
                elapsed_ms=(perf_counter_ns()-t0)/1e6)
            if not agrees(candidate.apply,train):
                continue
            if not agrees(candidate.apply,checks):
                continue
            return CompositionDecision(
                "SOURCE_VERIFIED_NEW_COMPOSITION",candidate,queried,attempted,
                (perf_counter_ns()-t0)/1e6)
        return CompositionDecision(
            "ABSTAIN_UNSUPPORTED",None,queried,attempted,
            (perf_counter_ns()-t0)/1e6)


def exact_polynomial_residual(observations, *, max_degree=2):
    """Domain-specific plugin: construct an exact rational polynomial rule.

    No target outputs are supplied. Callers must provide disjoint original
    source validation; finite fit does not certify arbitrary extrapolation.
    """
    points=[];ys=[]
    for x,y in observations:
        if type(x) not in (int,Fraction) or type(y) not in (int,Fraction):
            return None
        points.append((Fraction(x),))
        ys.append(Fraction(y))
    for degree in range(max_degree+1):
        terms=_monomials(1,degree)
        coeff=_fit(points,ys,terms)
        if coeff is None:continue
        def predict(z,term=terms,cs=coeff):
            if type(z) not in (int,Fraction):return None
            p=(Fraction(z),)
            return sum((c*_evaluate(t,p) for t,c in zip(term,cs)),
                       Fraction(0))
        if all(predict(x)==y for x,y in observations):
            return predict
    return None
