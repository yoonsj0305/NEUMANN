"""Q3V: COMPLETE joint affine-equality hull for a SINGLE initial affine system.

A mathematical/classical fragment result, not a trained Q3 neural operator.
Prereg: docs/research/Q3V_KRYLOV_AFFINE_HULL_PREREG_20261018.md
"""
from __future__ import annotations
import argparse, hashlib, json, math, random, sys, time
from pathlib import Path
import sympy as sp
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3u-exact-transition-nullspace-20261018"))
from first_real_affine_nullspace import (
    exact_update_matrix, check_parity, check_cover,
    PROVEN, flat_and, blobhash, sexprs, extract_mixed_original,
    native_original_relations, independent_native_bad_query,
)
UPSTREAM="6ac90265b11431c9477dfbd33e3e3380234c0499"
ORIGINAL="benchmarks/LIA/2017.ASE_FiB/fib_01.sl"
SOURCE_BLOB="480ddf9d1ddb0c2c3e6d2aabf6af2e38f8f26f09"

def primitive(v):
    v=[sp.Rational(t) for t in v]
    denom=math.lcm(*(int(t.q) for t in v))
    a=[int(t*denom) for t in v]
    g=math.gcd(*[abs(t) for t in a])
    if not g: raise AssertionError("ZERO_CERTIFICATE_ROW")
    a=[t//g for t in a]
    if next(t for t in a if t)!=abs(next(t for t in a if t)):
        a=[-t for t in a]
    return a

def construct(A,b,x0):
    n=A.rows
    assert A.cols==n and b.shape==(n,1) and x0.shape==(n,1)
    M=A.row_join(b).col_join(sp.zeros(1,n).row_join(sp.ones(1,1)))
    y0=x0.col_join(sp.ones(1,1))
    d=n+1
    cols=[y0]
    for _ in range(1,d): cols.append(M*cols[-1])
    K=sp.Matrix.hstack(*cols)
    raw=K.T.nullspace()
    R=sp.Matrix([primitive(v) for v in raw]) if raw else sp.zeros(0,d)
    # These are EXACT algebraic certificates. Sampling alone never proves soundness.
    assert R.cols==d
    assert R*y0==sp.zeros(R.rows,1)
    assert R*K==sp.zeros(R.rows,d)
    assert R*M*K==sp.zeros(R.rows,d)
    assert R.col_join(R*M).rank()==R.rank()
    assert R.rows==d-K.rank()
    assert (R*K)==sp.zeros(R.rows,d)
    return M,y0,K,R

def rowspace_completeness(K,R):
    d=K.rows
    # Any linear equation true for the infinite trajectory annihilates K;
    # exact row-space criterion follows from Cayley-Hamilton.
    for j in range(d):
        e=sp.zeros(1,d);e[0,j]=1
        belongs=e.col_join(R).rank()==R.rank()
        assert belongs == (e*K==sp.zeros(1,K.cols))
    return True

def exact_suite():
    started=time.perf_counter()
    sizes={}
    for n in (2,3,4,5):
        rng=random.Random(1000+n)
        for trial in range(80):
            A=sp.Matrix(n,n,[rng.randint(-3,3) for _ in range(n*n)])
            b=sp.Matrix(n,1,[rng.randint(-3,3) for _ in range(n)])
            x0=sp.Matrix(n,1,[rng.randint(-3,3) for _ in range(n)])
            M,y,K,R=construct(A,b,x0)
            rowspace_completeness(K,R)
            for t in range(2*n+2):
                assert R*(M**t*y)==sp.zeros(R.rows,1)
        sizes[str(n)]=80
    rng=random.Random(987654)
    for t in range(40):
        n=2+t%4
        def q(): return sp.Rational(rng.randint(-5,5),rng.randint(1,5))
        A=sp.Matrix(n,n,[q() for _ in range(n*n)])
        b=sp.Matrix(n,1,[q() for _ in range(n)])
        x0=sp.Matrix(n,1,[q() for _ in range(n)])
        M,y,K,R=construct(A,b,x0)
        rowspace_completeness(K,R)
        for j in range(2*n+2):
            assert R*(M**j*y)==sp.zeros(R.rows,1)
    return {"integer_cases":sizes,"rational_cases":40,
            "exact_algebraic_certification":True,
            "wall_ms":round((time.perf_counter()-started)*1000,3)}

def row_formula(R,states):
    terms=list(states)+[z3.IntVal(1)]
    if not all(sp.Rational(v).q==1 for v in R): 
        raise ValueError("CERTIFICATE_NOT_PRIMITIVE_INTEGER")
    clauses=[]
    for i in range(R.rows):
        clauses.append(z3.Sum(*[z3.IntVal(int(R[i,j]))*terms[j]
                        for j in range(R.cols)])==0)
    return z3.And(*clauses)

def centered_rotation_control():
    x,y=z3.Ints("q3v_x q3v_y")
    xp,yp=z3.Ints("q3v_xp q3v_yp")
    A=sp.Matrix([[0,-1],[1,0]]);b=sp.Matrix([8,2]);x0=sp.Matrix([3,5])
    M,y0,K,R=construct(A,b,x0)
    assert A.det()!=0 and (A-sp.eye(2)).det()!=0
    # Previous individually-inductive RESET / CONSERVATION bases are empty.
    assert not A.T.nullspace() and not (A-sp.eye(2)).T.nullspace()
    base={"now":[x,y],"next":[xp,yp],"pre":z3.And(x==3,y==5),
          "trans":z3.And(xp==8-y,yp==x+2),"post":x>=3}
    relation=row_formula(R,[x,y])
    post_alone=check_cover(base["post"],base)["status"]
    each=[
        check_cover(x==3,base)["status"],
        check_cover(y==5,base)["status"]
    ]
    joint=check_cover(z3.And(base["post"],relation),base)
    corrupted={**base,"trans":z3.And(xp==8-y,yp==x+3)}
    stale=check_cover(z3.And(base["post"],relation),corrupted)["status"]
    assert joint["status"]==PROVEN and post_alone!=PROVEN
    assert all(q!=PROVEN for q in each)
    assert stale!=PROVEN
    assert R.rows==2 and K.rank()==1
    # Independent exact trajectory: fixed center is the only reachable point.
    assert M*y0==y0
    return {"new_joint_equations":[[int(v) for v in row] for row in R.tolist()],"post_only":post_alone,
            "each_individual_equality":each,"full_joint_original_3vc":joint["status"],
            "mutated_old_certificate_rejected":stale!=PROVEN,
            "old_reset_nullspace_dim":0,"old_conservation_nullspace_dim":0}

def initial_singleton(pre,now):
    s=z3.Solver();s.set(timeout=2500);s.add(pre)
    if s.check()!=z3.sat:raise ValueError("ORIGINAL_PRE_NOT_PROVEN_SAT")
    m=s.model()
    vals=[m.eval(v,model_completion=True) for v in now]
    if not all(z3.is_int_value(v) for v in vals):
        raise ValueError("ORIGINAL_PRE_NOT_INTEGER")
    s.add(z3.Or(*[v!=constant for v,constant in zip(now,vals)]))
    if s.check()!=z3.unsat:
        raise ValueError("ORIGINAL_PRE_NOT_UNIQUE_OR_UNKNOWN")
    return sp.Matrix([v.as_long() for v in vals])

def original_case(root):
    path=root/ORIGINAL
    data=path.read_bytes()
    assert blobhash(data)==SOURCE_BLOB
    orig=extract_mixed_original(sexprs(data))
    if orig["num_bool"]!=0 or orig["num_int"]>8: raise ValueError("STATE_OUT_OF_FROZEN_SCOPE")
    native=native_original_relations(sexprs(data),orig)
    native.update({"now":orig["now"],"next":orig["next"]})
    parity=check_parity(orig,native)
    assert parity=={"pre":"unsat","trans":"unsat","post":"unsat"}
    A,b=exact_update_matrix(orig)
    now,nxt=native["now"],native["next"]
    # A mere syntactic assignment is not enough: source Trans must be EXACTLY
    # the total deterministic graph, not a guarded subset or approximation.
    graph=z3.And(*[
        nxt[i]==z3.Sum(*[z3.IntVal(int(A[i,j]))*now[j]
                            for j in range(len(now))])+int(b[i])
        for i in range(len(nxt))])
    strict=z3.Solver();strict.set(timeout=2500)
    strict.add(z3.Xor(native["trans"],graph))
    assert strict.check()==z3.unsat,"NOT_UNGUARDED_TOTAL_AFFINE_ORIGINAL"
    x0=initial_singleton(native["pre"],now)
    M,y0,K,R=construct(A,b,x0)
    claim=row_formula(R,now)
    prem=z3.Solver();prem.set(timeout=2500);prem.add(native["pre"])
    assert prem.check()==z3.sat
    non=z3.Solver();non.set(timeout=2500);non.add(z3.Not(native["post"]))
    assert non.check()==z3.sat
    full=check_cover(z3.And(claim,native["post"]),native)
    alone=check_cover(native["post"],native)
    strong=independent_native_bad_query(native,now,nxt)
    assert full["status"]==PROVEN,"ACTUAL_ORIGINAL_THREE_VC_FAILED"
    assert strong["status"]=="unsat","ORIGINAL_CLASSICAL_SPECIALIST_FAILED"
    assert alone["status"]!=PROVEN,"POST_ALONE_CONTROL_NOT_DISCRIMINATING"
    return {"source":ORIGINAL,"blob":SOURCE_BLOB,"parser_xor":parity,
            "original_total_transition_exact":True,
            "original_pre_singleton_exact":list(map(int,x0)),
            "complete_hull_rank":K.rank(),
            "complete_hull_integer_equalities":[[int(v) for v in row] for row in R.tolist()],
            "source_3vc":{k:full.get(k) for k in ("initial","consecution","post")},
            "post_only":alone["status"],"strong_spacer":strong["status"],
            "strong_spacer_ms":strong.get("native_solver_wall_ms")}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    started=time.perf_counter()
    synthetic=centered_rotation_control()
    randomized=exact_suite()
    real=original_case(a.root)
    report={"study":"Q3V_KRYLOV_COMPLETE_SINGLETON_AFFINE_JOINT_INVARIANT",
            "status":"FIRST_EXACT_ALGEBRA_AND_ORIGINAL_3VC_PASS",
            "theorem_scope":"complete rational affine equality hull for deterministic total unguarded affine transition and one initial state",
            "frozen_pre_registration_commit":"55114ec5ba2cf87340825e74c37b054a669ac870",
            "source_revision":UPSTREAM,
            "synthetic_joint_invariant_strict_advantage":synthetic,
            "exact_random_regression":randomized,
            "authentic_original_formal_check":real,
            "trained_neural_forward_calls":0,
            "global_q1_q7":"OPEN",
            "new_unseen_original_families_used":0,
            "q3f_escrow_chc_targets_opened":False,
            "full_wall_ms":round((time.perf_counter()-started)*1000,3)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3V_FIRST_FROZEN",json.dumps(report,sort_keys=True))
if __name__=="__main__":main()
