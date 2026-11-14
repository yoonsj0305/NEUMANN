"""Derived named power operator from existing EXP and LOG primitives.

This is a SOURCE-INDUCED composition, not invention of an atomic math
operator. Only b positive INTEGER and k INTEGER; exp(k*x*log(b)) is
symbolically compiled and checked to b**(k*x) before external original
author truth is ever available. Name, gain, offset, and two-summand
composition inferred from numeric x-y.
"""
import itertools
import numpy as np
import sympy as sp
from learned_additive_macro_ninth32 import original_shape,X
from learned_structural_graph_action_tenth32 import source_context,best_program
COMBINATIONS=tuple(itertools.product(range(2,17),(-1,1,2,3,4)))
assert len(COMBINATIONS)==75
def macro(b,k):
    expr=sp.exp(sp.Integer(k)*X*sp.log(sp.Integer(b)))
    expected=sp.Pow(sp.Integer(b),sp.Integer(k)*X)
    assert sp.powdenest(expr,force=True)==expected,(b,k)
    return expected,{"EXPLOG_original_graph":str(expr),
                     "positive_base_certified_compiled_graph":str(expected),
                     "base":int(b),"slope":int(k)}
def valid(row):
    return "x" in row and original_shape(row.get("x",[]),row.get("y",[])) is not None
def relerr(y,v):
    with np.errstate(all="ignore"):
        z=np.abs(y-v)/(1+np.abs(y))
    return float(np.max(z)) if np.all(np.isfinite(z)) else float("inf")
def matrix(row):
    if not valid(row):return None
    x=np.asarray(row["x"],float);y=np.asarray(row["y"],float)
    pool=[];params=[]
    for b,k in COMBINATIONS:
        with np.errstate(all="ignore"):
            z=np.power(float(b),float(k)*x)
        if z.shape==(48,) and np.all(np.isfinite(z)) and max(abs(z))<1e12:
            pool.append(z);params.append((b,k))
    if not pool:return None
    raw=np.column_stack(pool)
    center=raw[:32]-raw[:32].mean(axis=0)
    norm=np.linalg.norm(center,axis=0)
    good=norm>1e-14
    if not np.any(good):return None
    centered=center[:,good]/norm[good]
    return {"x":x,"y":y,"raw":raw[:,good],"params":[p for p,g in zip(params,good) if g],
            "normalized":centered}
def repair_exact_rational(m,y,idx,co):
    try:
        qq=[sp.Rational(float(v)).limit_denominator(1000) for v in co]
        pieces=[macro(*m["params"][j]) for j in idx]
        expression=sp.Add(*(qq[i]*pieces[i][0] for i in range(len(idx))),qq[-1])
        fn=sp.lambdify(X,expression,"numpy")
        with np.errstate(all="ignore"):
            yy=np.broadcast_to(np.asarray(fn(m["x"]),float),y.shape)
        if relerr(y,yy)>1e-8:return None
        return {"named_lambda":"lambda x: "+str(expression),
                "defined_operator_AST":str(expression),
                "derived_EXPLOG_macros":[p[1] for p in pieces],
                "exact_source_rationalized":True}
    except Exception:return None
def best_power(row,arity,limit=180):
    m=matrix(row)
    if m is None:return float("inf"),None,0
    y=m["y"];Z=m["normalized"];c=Z.T@(y[:32]-np.mean(y[:32]));n=len(c)
    if arity==1:
        sequences=[(int(i),) for i in np.argsort(-abs(c))[:limit]]
    else:
        gram=Z.T@Z
        den=1-gram*gram
        with np.errstate(all="ignore",divide="ignore",invalid="ignore"):
            score=np.divide(c[:,None]**2+c[None,:]**2-2*gram*c[:,None]*c[None,:],
                            den,out=np.full_like(gram,-np.inf),where=den>1e-10)
        score=np.where(np.triu(np.ones_like(score,dtype=bool),1),score,-np.inf)
        ordered=np.argsort(-score.ravel(),kind="stable")[:limit]
        sequences=[tuple(map(int,np.unravel_index(int(i),score.shape))) for i in ordered if np.isfinite(score.ravel()[int(i)])]
    best=float("inf");program=None;attempts=0
    for idx in sequences:
        attempts+=1
        A=np.column_stack([m["raw"][:,j] for j in idx]+[np.ones(48)])
        try:
            coef=np.linalg.lstsq(A[:32],y[:32],rcond=1e-12)[0]
            if not np.all(np.isfinite(coef)) or max(abs(coef))>1e9:continue
            e=relerr(y,A@coef)
            if e<best:
                best=e
                if e<1e-7:
                    p=repair_exact_rational(m,y,idx,coef)
                    if p is not None:
                        p["structure_action"]="DEFINE_EXPLOG_DERIVED_POWER_"+str(arity)
                        program=p
        except Exception:continue
    return best,program,attempts
def old_safe(row):
    src=source_context(row)
    if src is None:return float("inf"),[],0
    best=float("inf");programs=[];n=0
    for action in ("ADD_BRANCH","RATIONAL_REWRITE"):
        err,prog,c=best_program(src,action,[])
        n+=c;best=min(best,err)
        if prog is not None and prog["named_lambda"] not in {v["named_lambda"] for v in programs}:
            programs.append(prog)
    return best,programs,n
