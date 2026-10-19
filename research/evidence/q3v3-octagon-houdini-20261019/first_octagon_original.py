"""Q3V3: bounded signed-octagon candidate Houdini on ten ALREADY OPENED originals.
Never imply learned structure invention, first-time blind family, or G0 cost win.
Research preregistration: Q3V2 PR #237 comment #6257150546.
"""
import argparse, hashlib, itertools, json, sys, time
from pathlib import Path
import z3

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "q3v-branch-common-nullspace-20261019"))
from first_original_branch_nullspace import (
    check_parity, check_cover, check_formula, extract_mixed_original,
    native_original_relations, sexprs, sample, blobhash, LICENSE_GIT_BLOB, REV,
    PROVEN,
)

MAX_DIM=8
MAX_CANDIDATES=150
MAX_STEPS=160
TIMEOUT_MS=2500

class Abstain(Exception):
    pass

def check_sat(*formulas):
    s=z3.Solver()
    s.set(timeout=TIMEOUT_MS)
    s.add(*formulas)
    v=s.check()
    if v==z3.unknown:
        raise Abstain("SMT_UNKNOWN_"+s.reason_unknown()[:80])
    return v,s.model() if v==z3.sat else None

def lin(co,x):
    return z3.Sum([z3.IntVal(int(a))*v for a,v in zip(co,x) if a])

def exact_state(m,xs):
    r=[]
    for v in xs:
        n=m.eval(v,model_completion=True)
        if not z3.is_int_value(n):raise Abstain("NONINT_MODEL")
        r.append(int(n.as_long()))
    return r

def coeffs(n):
    out=[]
    for i in range(n):
        for a in [-1,1]:
            v=[0]*n;v[i]=a;out.append(tuple(v))
    for i,j in itertools.combinations(range(n),2):
        for a,b in itertools.product([-1,1],repeat=2):
            v=[0]*n;v[i]=a;v[j]=b;out.append(tuple(v))
    assert len(out)==2*n+4*n*(n-1)//2
    return out

def houdini(pre,trans,now,nxt):
    if len(now)!=len(nxt) or not 1<=len(now)<=MAX_DIM:
        raise Abstain("DIMENSION_OUTSIDE_CAP")
    s,m=check_sat(pre)
    if s!=z3.sat:raise Abstain("ORIGINAL_PRE_NOT_SAT")
    x0=exact_state(m,now)
    pool=[{"coeff":c,"bound":sum(int(a)*int(b) for a,b in zip(c,x0))}
          for c in coeffs(len(now))]
    if len(pool)>MAX_CANDIDATES:raise Abstain("GRAMMAR_CAP")
    original_count=len(pool)
    queries={"pre":0,"induction":0,"models_removed":0}
    # Pre's entire semantic set, NOT merely the selected witness, must satisfy I.
    for turn in range(MAX_STEPS):
        current=[lin(p["coeff"],now)<=p["bound"] for p in pool]
        if not current:break
        state,model=check_sat(pre,z3.Or([z3.Not(t) for t in current]))
        queries["pre"]+=1
        if state==z3.unsat:break
        bad=[j for j,v in enumerate(current) if z3.is_false(model.eval(v,model_completion=True))]
        if not bad:raise Abstain("BAD_PRE_COUNTEREXAMPLE")
        excluded=set(bad)
        pool=[p for j,p in enumerate(pool) if j not in excluded]
        queries["models_removed"]+=1
    else: raise Abstain("PRE_HOUDINI_ITERATION_CAP")
    for turn in range(MAX_STEPS):
        current=[lin(p["coeff"],now)<=p["bound"] for p in pool]
        nexts=[lin(p["coeff"],nxt)<=p["bound"] for p in pool]
        state,model=check_sat(z3.And(*current),trans,
                    z3.Or([z3.Not(t) for t in nexts]))
        queries["induction"]+=1
        if state==z3.unsat:break
        bad=[j for j,v in enumerate(nexts) if z3.is_false(model.eval(v,model_completion=True))]
        if not bad:raise Abstain("BAD_INDUCTIVE_COUNTEREXAMPLE")
        excluded=set(bad)
        pool=[p for j,p in enumerate(pool) if j not in excluded]
        queries["models_removed"]+=1
    else: raise Abstain("INDUCTION_ITERATION_CAP")
    inv=z3.And(*[lin(p["coeff"],now)<=p["bound"] for p in pool])
    return inv,pool,original_count,queries

def synthetic():
    x,y=z3.Ints("q3v3_sx q3v3_sy")
    xp,yp=z3.Ints("q3v3_sxp q3v3_syp")
    pre=z3.And(x==0,y==0)
    trans=z3.Or(z3.And(xp==x+1,yp==y+100),z3.And(xp==x,yp==y))
    post=z3.Or(x<4,y>2)
    orig={"now":[x,y],"next":[xp,yp],"pre":pre,"trans":trans,"post":post}
    inv,pool,_,q=houdini(pre,trans,[x,y],[xp,yp])
    safe=check_cover(inv,orig)
    assert safe["status"]==PROVEN,safe
    assert check_cover(post,orig)["status"]!=PROVEN
    # Invalid transition is deliberately reachable and breaks the old invariant.
    changed={**orig,"trans":z3.Or(
        z3.And(xp==x+1,yp==y-100),z3.And(xp==x,yp==y))}
    assert check_cover(inv,changed)["status"]!=PROVEN
    assert any(p["coeff"]==(-1,0) for p in pool)
    assert any(p["coeff"]==(1,-1) for p in pool)
    a,b,w,z=z3.Ints("q3v3_a q3v3_b q3v3_w q3v3_z")
    ap,bp,wp,zp=z3.Ints("q3v3_ap q3v3_bp q3v3_wp q3v3_zp")
    pre2=z3.And(a==0,b==0,w==1,z==0)
    t2=z3.Or(z3.And(w==1,z==0,ap==a+1,bp==b+1,wp==0,zp==1),
        z3.And(w!=1,z==0,ap==a,bp==b+1,wp==w,zp==1),
        z3.And(w==1,z!=0,ap==a+1,bp==b,wp==0,zp==z),
        z3.And(w!=1,z!=0,ap==a,bp==b,wp==w,zp==z))
    original2={"now":[a,b,w,z],"next":[ap,bp,wp,zp],
               "pre":pre2,"trans":t2,"post":a==b}
    inv2,pool2,_,q2=houdini(pre2,t2,original2["now"],original2["next"])
    assert check_cover(inv2,original2)["status"]==PROVEN
    assert check_cover(a==b,original2)["status"]!=PROVEN
    changed2={**original2,"trans":z3.Or(z3.And(
        w==1,z==0,ap==a+1,bp==b+2,wp==0,zp==1),*list(t2.children())[1:])}
    assert check_cover(inv2,changed2)["status"]!=PROVEN
    return {"synthetic_octagonal_post_noninductive":"PASS",
            "synthetic_branch_guard_conjunction":"PASS",
            "synthetic_unsafe_mutants":"REJECTED_2_OF_2",
            "synthetic1_remaining":len(pool),
            "synthetic2_remaining":len(pool2),
            "source_answers_leaked":False}

def evaluate(path,root):
    raw=path.read_bytes()
    rec={"source":path.relative_to(root).as_posix(),"git_blob":blobhash(raw),
         "status":"UNDETERMINED"}
    start=time.perf_counter_ns()
    try:
        form=sexprs(raw)
        src=extract_mixed_original(form)
        native=native_original_relations(form,src)
        native.update({"now":src["now"],"next":src["next"]})
        if any(value!="unsat" for value in check_parity(src,native).values()):
            raise Abstain("ORIGINAL_SOURCE_NATIVE_PARITY_NOT_UNSAT")
        if src["num_bool"]!=0:raise Abstain("BOOL_STATE_NOT_IN_GRAMMAR")
        if check_formula(native["pre"])!="sat" or \
           check_formula(z3.Not(native["post"]))!="sat":
            raise Abstain("ORIGINAL_GOAL_VACUOUS_OR_UNKNOWN")
        inv,pool,n0,q=houdini(native["pre"],native["trans"],src["now"],src["next"])
        proof=check_cover(inv,native)
        post_only=check_cover(native["post"],native)
        rec.update({"status":"ORIGINAL_VC_CHECKED",
                    "candidate_grammar":n0,"surviving_candidates":len(pool),
                    "bulk_counterexample_queries":q,
                    "original_full_3vc":proof["status"],
                    "original_full_3vc_checks":{
                        k:proof.get(k) for k in ("initial","consecution","post")},
                    "post_alone_original_3vc":post_only["status"],
                    "new_nontrivial_original_proof":proof["status"]==PROVEN
                           and post_only["status"]!=PROVEN,
                    "final_exact_octagonal_coefficients":pool})
    except Exception as e:
        rec.update({"status":"ABSTAIN","error_class":type(e).__name__,
                    "reason":str(e)[:140]})
    rec["case_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    return rec

def run(root):
    assert blobhash((root/"LICENSE.md").read_bytes())==LICENSE_GIT_BLOB
    controls=synthetic()
    cases=[evaluate(p,root) for p in sample(root)]
    if len(cases)!=10 or len({x["git_blob"] for x in cases})!=10:
        raise ValueError("HISTORICAL_ORIGINAL_IDENTITY_NOT_TEN")
    result={"name":"Q3V3_CLASSICAL_PRE_ANCHORED_OCTAGON_HOUDINI_FIRST",
            "upstream_revision":REV,"first_controls":controls,
            "first_existing_opened_source_results":cases,
            "summary":{"originals":len(cases),
                "full_3vc":sum(x.get("original_full_3vc")==PROVEN for x in cases),
                "post_nontrivial_full_3vc":sum(x.get("new_nontrivial_original_proof",False) for x in cases),
                "unsupported":sum(x["status"]=="ABSTAIN" for x in cases),
                "fib_08_nontrivial":next((x.get("new_nontrivial_original_proof",False)
                    for x in cases if x["source"].endswith("/fib_08.sl")),False),
                "fib_10_nontrivial":next((x.get("new_nontrivial_original_proof",False)
                    for x in cases if x["source"].endswith("/fib_10.sl")),False)},
            "learned_new_operator":False,"training_calls":0,
            "source_family_blind":False,"global_Q1_Q7":"OPEN"}
    result["predeclared_joint_admission"]=bool(
        result["summary"]["fib_08_nontrivial"] and result["summary"]["fib_10_nontrivial"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=run(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("Q3V3_FIRST_SUMMARY",json.dumps(r["summary"],sort_keys=True))
    print("Q3V3_FIRST_ORIGINAL_CASES",[(x["source"],x["status"],x.get("original_full_3vc"),x.get("new_nontrivial_original_proof"),x.get("reason")) for x in r["first_existing_opened_source_results"]])
    print("Q3V3_FIRST_ADMISSION",r["predeclared_joint_admission"])
