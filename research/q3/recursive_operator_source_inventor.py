"""NEUMANN P2: create NEW RECURSIVELY DEFINED executable semantic symbols from source.

Crucial difference from prior closed-form fixed-grammar trials:
Given exact-rational sample sequence y(1)..y(48), synthesizes a NEW
lambda-like recursive function M, its INITIAL STATE and its INCREMENT
program r(n), searching rational programs for differences. It does NOT
contain a named HARMONIC primitive or a lookup of target equations.

The human has programmed GENERAL recurrence semantics and restricted a
rational numerator/denominator grammar, so full autonomous semantic-atom
invention is still NOT proved. The discovered concrete M(n), unlike its
generic ability to DEFINE_RECURRENCE, is not in the human supplied list.

Retains every original input and explicitly emits UNKNOWN for no proof.
"""
from fractions import Fraction
import hashlib,json,pathlib
import numpy as np
import sympy as sp
from sympy.polys.polyfuncs import rational_interpolate

N=sp.Symbol("n",integer=True,positive=True)
RECURRENCE_MAX_COMPLEXITY=6
LOG_SQRT_ATOMS={
    "ID":N,
    "SQUARE":N**2,
    "CUBE":N**3,
    "RECIP":1/N,
    "LOG":sp.log(N),
    "SQRT":sp.sqrt(N),
    "SIN":sp.sin(N),
    "COS":sp.cos(N),
    "LOG_SHIFT1":sp.log(N+1),
    "SQRT_SHIFT1":sp.sqrt(N+1),
}
def sha(data):
    if isinstance(data,(bytes,bytearray)):return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(str(data).encode("utf-8")).hexdigest()
def save(path,obj):
    p=pathlib.Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    return sha(p.read_bytes())
def shape(row):
    try:
        x=np.asarray(row["x"],float);y=np.asarray(row["y"],float)
        if len(x)!=48 or len(y)!=48:return None
        if not(np.all(np.isfinite(x)) and np.all(np.isfinite(y))):return None
        if np.max(np.abs(y))>1e12:return None
        v=np.diff(y)
        scale=max(float(np.median(abs(v))),1e-9)
        z=(v/scale)
        # Shape-only features: not the published author expression.
        features=np.r_[np.clip(z[::3][:16],-15,15),
            np.log1p([np.max(abs(y)),np.ptp(y),np.mean(abs(v)),np.std(v)]),
            np.mean(np.diff(v)>0),np.mean(np.diff(v)<0),
            np.mean(v>0),np.mean(v<0),
            np.median(np.abs(np.diff(v)))/max(float(np.median(abs(v))),1e-9)]
        assert len(features)==25
        return features
    except Exception:return None

def recurrence_source(row):
    """Construct new typed operator M from SOURCE-only rational sequence samples.

    All 47 sample differences must exactly equal one small rational
    program recovered from the FIRST FEW differences. The remaining
    source differences are held out from the interpolation. This is
    stronger than floating tolerance but NOT general proof of arbitrary
    author original outside the source observations.
    """
    xs=row.get("x",[])
    exact=row.get("y_exact",[])
    if len(xs)!=48 or len(exact)!=48:return None,0
    pairs=sorted(zip(xs,exact))
    try:
        ix=[int(x) for x,_ in pairs]
        if any(float(x)!=i for (x,_),i in zip(pairs,ix)):return None,0
        if any(ix[j+1]!=ix[j]+1 for j in range(47)):return None,0
        y=[sp.Rational(v) for _,v in pairs]
        observed=[(sp.Integer(ix[i]),y[i+1]-y[i]) for i in range(47)]
    except Exception:return None,0
    calls=0
    for complexity in range(1,RECURRENCE_MAX_COMPLEXITY+1):
        for degree_p in range(min(3,complexity-1)+1):
            degree_q=complexity-1-degree_p
            if degree_q>4:continue
            minimum=degree_p+degree_q+1
            if minimum+4>len(observed):continue
            calls+=1
            try:
                expr=sp.cancel(rational_interpolate(observed[:minimum],degree_p,N))
                if not expr.is_rational_function(N):continue
                if any(sp.cancel(expr.subs(N,n)-delta)!=0 for n,delta in observed):
                    continue
                if sp.count_ops(expr)>18:continue
                # Audit a running PROGRAM rather than just a numeric fit:
                # M(first)=initial; for n>=first: M(n+1)=M(n)+expr(n)
                current=y[0]
                for i in range(47):
                    current=sp.cancel(current+expr.subs(N,ix[i]))
                    assert sp.cancel(current-y[i+1])==0
                return {
                  "kind":"NEW_EXECUTABLE_RECURSIVE_SYMBOL",
                  "new_symbol":"M",
                  "definition":"M(%d)=%s; M(n+1)=M(n)+(%s)"%(ix[0],y[0],expr),
                  "base_n":ix[0],"base_y":str(y[0]),
                  "step_increment_AST":str(expr),
                  "source_heldout_differences_verified":47-minimum,
                  "all_47_source_rational_equalities_exact":True,
                  "learned_expression_complexity":complexity,
                  "not_a_prior_human_registered_named_primitive":True,
                  "generated_from_original_target_formula":False,
                },calls
            except Exception:continue
    return None,calls

def closed_form_source(row):
    """Old-style finite ordinary expression grammar, matched same source.

    Allowed 10 HUMAN given unary shapes, with source-fitted rational
    gain/offset; no recurrence symbol, harmonic, digamma or asinh.
    """
    xs=np.asarray(row.get("x",[]),float)
    ys=np.asarray(row.get("y",[]),float)
    if len(xs)!=48 or len(ys)!=48:return None,0
    calls=0
    for kind,expr in LOG_SQRT_ATOMS.items():
        calls+=1
        try:
            fn=sp.lambdify(N,expr,"numpy")
            with np.errstate(all="ignore"):
                z=np.broadcast_to(np.asarray(fn(xs),float),ys.shape)
            if not np.all(np.isfinite(z)) or np.ptp(z[:32])<1e-12:continue
            A=np.column_stack((z[:32],np.ones(32)))
            b=np.linalg.lstsq(A,ys[:32],rcond=1e-12)[0]
            if not np.all(np.isfinite(b)):continue
            rational=[sp.Rational(float(v)).limit_denominator(1000) for v in b]
            symbolic=sp.Add(rational[0]*expr,rational[1])
            exact=sp.lambdify(N,symbolic,"numpy")
            with np.errstate(all="ignore"):
                yy=np.broadcast_to(np.asarray(exact(xs),float),ys.shape)
                error=np.max(abs(ys-yy)/(1+abs(ys)))
            if np.isfinite(error) and error<1e-9:
                return {
                  "kind":"FINITE_REGISTERED_UNARY_EXPRESSION",
                  "source_generated_AST":str(symbolic),
                  "original_unary_name":kind,
                  "numerically_verified_48_points":True,
                  "max_scaled_error":float(error),
                },calls
        except Exception:continue
    return None,calls

def action_result(row,action):
    if action=="DEFINE_RECURRENCE":return recurrence_source(row)
    if action=="OLD_CLOSED_FORM":return closed_form_source(row)
    raise ValueError(action)

def recurrence_induction_check(hyp,author_name):
    """INDEPENDENT AUTHOR GRADER ONLY, never called during model inference.

    For published Keijzer-6 F(n)=SUM_{k=1}^n 1/k, prove entire
    positive-integer domain by F(1)=M(1) and matching first differences.
    The model must have guessed M from source values only.
    """
    if author_name!="Keijzer-6":return {"status":"NOT_A_RECURSIVE_ORIGINAL"}
    if not hyp or hyp.get("kind")!="NEW_EXECUTABLE_RECURSIVE_SYMBOL":
        return {"status":"UNKNOWN"}
    first=int(hyp["base_n"])
    init=sp.Rational(hyp["base_y"])
    delta=sp.sympify(hyp["step_increment_AST"],locals={"n":N})
    author=sp.harmonic(N)
    base_is_exact=bool(sp.simplify(author.subs(N,first)-init)==0)
    author_step=sp.expand_func(sp.harmonic(N+1)-sp.harmonic(N))
    step_is_exact=bool(sp.simplify(author_step-delta)==0)
    return {
      "status":"ALL_POSITIVE_INTEGER_AUTHOR_SEMANTICS_PROVED_BY_INDUCTION"
       if base_is_exact and step_is_exact and first==1 else "UNKNOWN",
      "author_step_after_exact_function_expansion":str(author_step),
      "source_generated_step":str(delta),
      "author_initial_state_equal":base_is_exact,
      "inductive_step_equal_FOR_ALL_integer_n_ge1":step_is_exact,
      "not_merely_finite_sample_interpolation":base_is_exact and step_is_exact,
      "proof_principle":"mathematical induction of identical base and every successor step",
    }
