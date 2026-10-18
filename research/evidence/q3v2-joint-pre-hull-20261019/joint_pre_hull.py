"""Q3V2 bounded classical joint Pre-hull source relation discovery.
No neural learning, no new blind-family evaluation, no global Q3 closure.
Use as an additive development proof on top of the immutable Q3U/Q3V.
"""
from __future__ import annotations
import argparse, json, math, sys, time
from pathlib import Path
import sympy as sp

SMT_TIMEOUT_MS = 2500

class ExactnessUnknown(Exception):
    pass

def primitive(v):
    coeff=[sp.Rational(z) for z in v]
    if not any(coeff): raise ExactnessUnknown("ZERO_VECTOR")
    den=sp.ilcm(*[int(z.q) for z in coeff])
    a=[int(z*den) for z in coeff]
    g=math.gcd(*[abs(z) for z in a if z])
    a=[z//g for z in a]
    if next(z for z in a if z)<0: a=[-z for z in a]
    return tuple(a)

def joint_kernels(branches,x0,directions):
    """Exact normal-space intersection for ALL affine branches and Pre hull."""
    if not branches:raise ExactnessUnknown("NO_BRANCHES")
    n=branches[0][0].rows
    p=sp.Matrix(x0)
    if p.shape!=(n,1):raise ExactnessUnknown("BAD_PRE_POINT")
    D=sp.Matrix.hstack(*directions) if directions else sp.zeros(n,0)
    if D.rows!=n:raise ExactnessUnknown("BAD_PRE_HULL")
    C=[D.T]; R=[D.T,(p-branches[0][1]).T]
    for A,b in branches:
        if A.shape!=(n,n) or b.shape!=(n,1):raise ExactnessUnknown("BAD_MATRIX")
        C.extend([(A-sp.eye(n)).T,b.T]);R.append(A.T)
    b0=branches[0][1]
    R.extend((b-b0).T for A,b in branches[1:])
    out={}
    for name,rows in (("CONSERVATION",C),("RESET",R)):
        candidates=[];seen=set()
        for v in sp.Matrix.vstack(*rows).nullspace():
            coeff=primitive(v)
            k=int((sp.Matrix(coeff).T*p)[0])
            if (coeff,k) not in seen:
                candidates.append({"coefficients":coeff,"constant":k,"mechanism":name})
                seen.add((coeff,k))
        out[name]=candidates
    return out

def algebra_tests():
    A=sp.Matrix([[1,0,0],[0,1,0],[1,1,1]])
    b=sp.zeros(3,1)
    D=sp.Matrix([[1,1,0],[0,0,1]]).nullspace()
    old=[primitive(v) for v in sp.Matrix.vstack((A-sp.eye(3)).T,b.T).nullspace()]
    assert old==[(1,0,0),(0,1,0)],old
    expected=(1,1,0)
    one=joint_kernels([(A,b)],[0,0,0],D)
    assert [r["coefficients"] for r in one["CONSERVATION"]]==[expected],one
    shifts=[sp.Matrix([1,-1,0]),sp.Matrix([-2,2,0]),sp.zeros(3,1)]
    branches=[(A,v) for v in shifts]
    many=joint_kernels(branches,[0,0,0],D)
    assert [r["coefficients"] for r in many["CONSERVATION"]]==[expected]
    corrupted=branches.copy()
    corrupted[1]=(A,sp.Matrix([-2,3,0]))
    broken=joint_kernels(corrupted,[0,0,0],D)
    assert not any(r["coefficients"]==expected for r in broken["CONSERVATION"])
    resetA=sp.diag(0,0,1)
    reset=joint_kernels([(resetA,sp.Matrix([1,-1,0]))],[0,0,0],D)
    assert any(r["coefficients"]==expected for r in reset["RESET"]),reset
    return {"old_basis":old,"new_normal":expected,
            "global_branch_conservation":True,"mutant_rejected":True,
            "initial_condition_reset_intersection":True,
            "status":"EXACT_ALGEBRA_PASS"}

def original_source_checks(root):
    import z3
    HERE=Path(__file__).resolve().parent
    sys.path.insert(0,str(HERE.parent/"q3v-branch-common-nullspace-20261019"))
    from first_original_branch_nullspace import (
        all_exact_branch_updates,common_kernels,check_cover,
        check_formula,actual_relation,prove_candidate_relation,
        PROVEN,sample,native_original_relations,extract_mixed_original,
        sexprs,blobhash,check_parity,LICENSE_GIT_BLOB,REV)
    if blobhash((root/"LICENSE.md").read_bytes())!=LICENSE_GIT_BLOB:
        raise ExactnessUnknown("UPSTREAM_LICENSE_MISMATCH")

    def linear(c,x):
        p=primitive(c)
        return z3.Sum([z3.IntVal(int(a))*b for a,b in zip(p,x)])

    def state(pre, xs, extra=None):
        s=z3.Solver();s.set(timeout=SMT_TIMEOUT_MS);s.add(pre)
        if extra is not None:s.add(extra)
        result=s.check()
        if result==z3.unsat:return None
        if result!=z3.sat:raise ExactnessUnknown("AFFINE_HULL_QUERY_UNKNOWN")
        model=s.model();out=[]
        for var in xs:
            val=model.eval(var,model_completion=True)
            if not z3.is_int_value(val):raise ExactnessUnknown("NONINTEGER_MODEL")
            out.append(int(val.as_long()))
        return sp.Matrix(out)

    def pre_hull(pre,xs):
        n=len(xs)
        if n>8:raise ExactnessUnknown("PRE_HULL_DIMENSION_CAP")
        x0=state(pre,xs)
        if x0 is None:raise ExactnessUnknown("PRE_UNSAT")
        D=[];queries=0
        while True:
            basis=sp.Matrix.hstack(*D) if D else sp.zeros(n,0)
            normals=basis.T.nullspace()
            if not normals:return x0,D,queries
            extra=z3.Or([linear(c,xs)!=int((sp.Matrix(primitive(c)).T*x0)[0])
                         for c in normals])
            nextpoint=state(pre,xs,extra)
            queries+=1
            if nextpoint is None:return x0,D,queries
            direction=nextpoint-x0
            if sp.Matrix.hstack(basis,direction).rank()!=len(D)+1:
                raise ExactnessUnknown("HULL_RANK_NONINCREASE")
            D.append(direction)
            if queries>n+1:raise ExactnessUnknown("PRE_HULL_QUERY_CAP")

    def test_case(pre,trans,post,now,nxt):
        orig={"now":now,"next":nxt,"num_int":len(now),"num_bool":0,
              "pre":pre,"trans":trans,"post":post}
        branches=all_exact_branch_updates(orig)
        old=common_kernels(branches,orig)
        x0,D,nq=pre_hull(pre,now)
        found=joint_kernels(branches,x0,D)
        cert=[]
        for item in found["CONSERVATION"]+found["RESET"]:
            relation=actual_relation(item,now)
            if prove_candidate_relation(orig,orig,relation)["source_certified"]:
                cert.append((item,relation))
        full=check_cover(z3.And(post,*[p for _,p in cert]),orig)
        old_post=check_cover(post,orig)
        return {"old_count":len(old),"candidates":found,
                "certified":[x for x,_ in cert],"safety":full["status"],
                "post_alone":old_post["status"],"hull_queries":nq}

    x,y,t=z3.Ints("q3v2_x q3v2_y q3v2_t")
    xp,yp,tp=z3.Ints("q3v2_xp q3v2_yp q3v2_tp")
    pre=z3.And(x+y==0,t==0);post=t==0
    raw=z3.And(xp==x,yp==y,tp==t+x+y)
    positive=test_case(pre,raw,post,[x,y,t],[xp,yp,tp])
    assert positive["old_count"]==0
    assert positive["safety"]==PROVEN and positive["post_alone"]!=PROVEN
    assert any(q["coefficients"]==(1,1,0) for q in positive["certified"])
    mutated={"now":[x,y,t],"next":[xp,yp,tp],
        "pre":pre,"post":post,"trans":z3.And(xp==x,yp==y,tp==t+x+y+1)}
    assert check_cover(z3.And(post,x+y==0),mutated)["status"]!=PROVEN
    plus=z3.And(x>=0,xp==x+1,yp==y-1,tp==t+x+y)
    minus=z3.And(x<0,xp==x-2,yp==y+2,tp==t+x+y)
    guarded=test_case(pre,z3.Or(plus,minus),post,[x,y,t],[xp,yp,tp])
    assert guarded["safety"]==PROVEN and guarded["post_alone"]!=PROVEN
    assert any(q["coefficients"]==(1,1,0) for q in guarded["certified"])
    bad={"now":[x,y,t],"next":[xp,yp,tp],"pre":pre,"post":post,
         "trans":z3.Or(plus,z3.And(x<0,xp==x-2,yp==y+3,tp==t+x+y))}
    assert check_cover(z3.And(post,x+y==0),bad)["status"]!=PROVEN

    # Existing OPENED sources only: engineering regression, NOT fresh transfer.
    cases=[]
    for path in sample(root):
        data=path.read_bytes()
        r={"file":path.relative_to(root).as_posix(),"blob":blobhash(data)}
        start=time.perf_counter_ns()
        try:
            src=extract_mixed_original(sexprs(data))
            native=native_original_relations(sexprs(data),src)
            native.update({"now":src["now"],"next":src["next"]})
            if any(x!="unsat" for x in check_parity(src,native).values()):
                raise ExactnessUnknown("NATIVE_SOURCE_PARSER_PARITY_UNKNOWN")
            if check_formula(native["pre"])!="sat" or \
               check_formula(z3.Not(native["post"]))!="sat":
                raise ExactnessUnknown("VACUOUS_ORIGINAL")
            branches=all_exact_branch_updates(src)
            x0,D,nq=pre_hull(native["pre"],src["now"])
            search=joint_kernels(branches,x0,D)
            verified=[]
            for candidate in search["CONSERVATION"]+search["RESET"]:
                relation=actual_relation(candidate,src["now"])
                if prove_candidate_relation(src,native,relation)["source_certified"]:
                    verified.append(relation)
            full=check_cover(z3.And(native["post"],*verified),native)
            post_only=check_cover(native["post"],native)
            r.update({"status":"DEV_ORIGINAL_CHECKED",
                      "branch_count":len(branches),
                      "certified_relations":len(verified),
                      "full_3vc":full["status"],
                      "beyond_post":bool(verified) and full["status"]==PROVEN
                                     and post_only["status"]!=PROVEN})
        except Exception as exc:
            r.update({"status":"DEV_ABSTAIN",
                      "reason_type":type(exc).__name__,
                      "reason":str(exc)[:95]})
        r["wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
        cases.append(r)
    assert len(cases)==10 and len({x["blob"] for x in cases})==10
    return {"status":"Z3_SYNTHETIC_ORIGINAL_VCS_PASS",
        "single_branch":positive,"guarded_two_branch":guarded,
        "mutation_rejection":True,"opened_source_regression":cases,
        "source_revision":REV,"learned_q3":"OPEN"}

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path)
    a.add_argument("--out",type=Path)
    args=a.parse_args()
    result={"name":"Q3V2_PRE_AFFINE_HULL_JOINT_NULLSPACE",
        "algebra":algebra_tests(),"neural_training_calls":0,
        "new_blind_family_test":False,"global_Q1_Q7":"OPEN"}
    if args.root:result["proof"]=original_source_checks(args.root)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Q3V2_RESULT",json.dumps(result,sort_keys=True))
