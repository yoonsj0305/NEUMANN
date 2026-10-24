#!/usr/bin/env python3
"""Strict source-only Q3 ODE macro generator. NO public author formula registry,
truth file import, prepare() or independent grading code exists in this file.
The definitions of ODE family meanings and solver are HUMAN CODED.
"""
import hashlib,json,pathlib,time
from fractions import Fraction
import numpy as np
import sympy as sp
from scipy.optimize import least_squares
from numpy.polynomial.legendre import leggauss
ROOT=pathlib.Path('/mnt/data/neumann_q3_ode_v3_isolated')
ROOT.mkdir(exist_ok=True)
QUAD_N=128
nodes,weights=leggauss(QUAD_N)
x_sym=sp.Symbol('x',real=True)
FAMILIES=('QUAD_INV_ROOT','LINEAR_INV_ROOT','INV_LINEAR','EXP_DERIVATIVE')
def bsha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def save(path,content):
    pathlib.Path(path).write_text(json.dumps(content,sort_keys=True,indent=2)+'\n')
    return bsha(path)

def integrate(family, xs, p):
    xs=np.asarray(xs,float)
    A=float(p[0]); D=float(p[-1])
    anchor=1.0 if family=='INV_LINEAR' else 0.0
    hh=(xs-anchor)/2
    ts=anchor+hh[:,None]*(nodes+1)
    with np.errstate(all='ignore'):
        # Exact elementary integral of the inferred differential law,
        # avoids a sqrt endpoint singularity that defeated first local run.
        if family=='LINEAR_INV_ROOT':
            B=float(p[1])
            if B<0 or np.min(xs+B)<0:return np.full(xs.shape,1e9)
            return D+2*A*(np.sqrt(xs+B)-np.sqrt(B))
        if family=='INV_LINEAR':
            B=float(p[1])
            if np.min(xs+B)<=0 or 1+B<=0:return np.full(xs.shape,1e9)
            return D+A*np.log((xs+B)/(1+B))
        if family=='QUAD_INV_ROOT':
            B,C=float(p[1]),float(p[2]); q=ts*ts+B*ts+C
            if np.min(q)<=1e-12:return np.full(xs.shape,1e9)
            vals=A/np.sqrt(q)
        elif family=='EXP_DERIVATIVE':
            B=float(p[1]);z=B*ts
            if np.max(abs(z))>450:return np.full(xs.shape,1e9)
            vals=A*np.exp(z)
        else:raise ValueError(family)
    out=D+np.sum(weights*hh[:,None]*vals,axis=1)
    return np.asarray(out,float) if np.all(np.isfinite(out)) else np.full(xs.shape,1e9)

def fitting_initials(family):
    if family=='QUAD_INV_ROOT':return ([1,0,1,0],[0.5,0,2,0],[2,0,1,0])
    if family=='LINEAR_INV_ROOT':return ([0.5,0.01,0],[1,1,0])
    if family=='INV_LINEAR':return ([1,0,0],[0.5,1,0])
    return ([1,0,0],[0.5,0.1,0])

def exact_ode_from_params(family, rational):
    p=[sp.Rational(k) for k in rational]
    if family=='QUAD_INV_ROOT':rhs=p[0]/sp.sqrt(x_sym*x_sym+p[1]*x_sym+p[2]);anchor=sp.Integer(0)
    elif family=='LINEAR_INV_ROOT':rhs=p[0]/sp.sqrt(x_sym+p[1]);anchor=sp.Integer(0)
    elif family=='INV_LINEAR':rhs=p[0]/(x_sym+p[1]);anchor=sp.Integer(1)
    else:rhs=p[0]*sp.exp(p[1]*x_sym);anchor=sp.Integer(0)
    return rhs,anchor,p[-1]

def numerical_regression_family(xs,ys,family):
    ys=np.asarray(ys,float);xs=np.asarray(xs,float)
    scale=1+np.abs(ys)
    best=None
    for init in fitting_initials(family):
        try:
            r=least_squares(lambda p:(integrate(family,xs[:32],p)-ys[:32])/scale[:32],
                            init,max_nfev=50,ftol=2e-12,gtol=2e-12,xtol=2e-12)
            pred=integrate(family,xs,r.x)
            relative=float(np.max(abs(pred-ys)/scale))
            if best is None or relative<best[0]:best=(relative,r.x)
        except Exception:continue
    if best is None:return None
    # Source-only conversion into exact simple-rational parameters.
    q=[str(Fraction(float(z)).limit_denominator(128)) for z in best[1]]
    from_q=np.array([float(sp.Rational(z)) for z in q])
    calc=integrate(family,xs,from_q)
    source_err=float(np.max(abs(calc-ys)/scale))
    return {'family':family,'nonlinear_float_source_error':best[0],
            'rational_coefficients':q,'rationalized_source_error':source_err,
            'source_exact_rationalized':source_err<1e-8,
            'derived_executable_operator':{
               'lambda_signature':'M(x)',
               'ODE_RHS':str(exact_ode_from_params(family,q)[0]),
               'initial_x':str(exact_ode_from_params(family,q)[1]),
               'initial_M':str(exact_ode_from_params(family,q)[2]),
               'definition_origin':'DERIVED_SOURCE_NUMERIC_REGRESSION_NOT_AUTHOR_FORMULA'} }

def infer():
    src=json.loads((ROOT/'source_no_author_expression.json').read_text())['source_numeric_only']
    now=time.process_time();cases=[]
    for row in src:
        xs=np.asarray(row['x'],float);ys=np.asarray(row['y'],float)
        fit=[numerical_regression_family(xs,ys,f) for f in FAMILIES]
        accepted=[q for q in fit if q is not None and q['source_exact_rationalized']]
        cases.append({'task':row['task'],'source_only_candidate_actions':fit,
                      'accepted_source_derived_macros':accepted})
    runtime=time.process_time()-now
    r={'schema':'NEUMANN_Q3_DEVELOPMENT_V2_SOURCE_DEFINED_DIFFERENTIAL_MACROS.v1',
       'actual_source_SHA256':bsha(ROOT/'source_no_author_expression.json'),
       'original_true_author_formulas_available_to_inference':False,
       'primitive_ODE_family_semantics_and_optimizer_human_coded':True,
       'higher_level_unnamed_inverse_hyperbolic_primitive_used_by_inference':False,
       'candidate_families':list(FAMILIES),'cases':cases,'CPU_s':runtime,
       'Q3_GLOBAL':'OPEN','Q4_10x':'NOT_PROVEN'}
    proof=save(ROOT/'first_source_only_ODE_definitions.json',r)
    print(json.dumps({'mode':'infer','pred_SHA256':proof,'source_only_CPU_s':runtime,
                      'source_exact':{q['task']:[x['family'] for x in q['accepted_source_derived_macros']] for q in cases}}))
if __name__=='__main__': infer()
