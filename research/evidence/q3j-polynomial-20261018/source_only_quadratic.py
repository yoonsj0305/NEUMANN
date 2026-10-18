"""Q3J first fixed source-only quadratic-identity search for real original C.

Exactly one previously opened Loopy program. No published invariant label,
no frontier calls, no learned model, no CHC-COMP Q3F holdouts. Truthful fail.
"""
from __future__ import annotations
import argparse,hashlib,io,itertools,json,math,sys,time,zipfile
from pathlib import Path
from functools import reduce
import z3,z3.z3util
import sympy as sp

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3h-real-source-proof-20261018"))
from replay_real_c_loop_invariants import model_original,signed_domain,check,MIN_INT,MAX_INT,Unsupported
from source_only_houdini import pool

SOURCE="dataset/loop_invariants/LinearArbitrary-SeaHorn/loops/loops/sum04_true-unreach-call_true-termination.i.annot.c"
EXPECTED_SHA="7b1ed83d1a2e80a1e5aa97e27a23c7ac1a53bd734cc95808ecce4aa868c41a23"
EXPECTED_BLOB="17cac0f6734a39f0fe73558199cc2ad8d5c1a810"
SEEDS=(-4,-1,0,1,2,3,5,8,13,21)
MAX_DEPTH=16
MAX_SAMPLES=160
MAX_POLY=15

def subst(expr,canonical,actual):
    return z3.substitute(expr,*[(canonical[k],actual[k]) for k in canonical])

def extract_int(expr,model):
    val=model.eval(expr,model_completion=True)
    if not z3.is_int_value(val):raise Unsupported("NON_INTEGER_REACHABLE_SAMPLE")
    return val.as_long()

def sample_reachable(m):
    current=dict(m["after_prelude"])
    canonical=m["loop_state"]
    init=z3.And(*signed_domain(m["initial"]),*m["init_assumptions"])
    vars_=list(z3.z3util.get_vars(
        z3.And(init,*[z3.And(v>=MIN_INT,v<=MAX_INT) for v in current.values()])))
    base_limits=z3.And(*[z3.And(v>=MIN_INT,v<=MAX_INT) for v in vars_])
    conditions=z3.BoolVal(True)
    found=[];seen=set();depths={}
    for depth in range(MAX_DEPTH):
        n=0
        for seed in SEEDS:
            if len(found)>=MAX_SAMPLES:break
            s=z3.Solver();s.set(timeout=2500,random_seed=1+abs(seed))
            s.add(init,base_limits,conditions)
            s.add(*[z3.And(v>=MIN_INT,v<=MAX_INT) for v in current.values()])
            for var in vars_:
                s.add(var>=min(seed,0)-21,var<=max(seed,0)+21)
            answer=s.check()
            if answer==z3.sat:
                result=s.model()
                tup=tuple(extract_int(current[k],result) for k in sorted(canonical))
                if tup not in seen:
                    seen.add(tup);found.append(tup);n+=1
            elif answer==z3.unknown:
                raise Unsupported("REACHABLE_SAMPLE_SOLVER_UNKNOWN")
        depths[str(depth)]=n
        conditions=z3.And(conditions,subst(m["loop_test"],canonical,current))
        current={k:subst(m["body_state"][k],canonical,current) for k in canonical}
    return found,depths

def polynomial_terms(names,heads):
    terms=[("one",z3.IntVal(1),lambda x:1)]
    for i,k in enumerate(names):
        terms.append((k,heads[k],lambda x,i=i:x[i]))
    for i,k in enumerate(names):
        for j in range(i,len(names)):
            terms.append((k+"*"+names[j],heads[k]*heads[names[j]],
                          lambda x,i=i,j=j:x[i]*x[j]))
    return terms

def primitive_coefficients(q):
    den=math.lcm(*[int(t.q) for t in q])
    arr=[int(t*den) for t in q]
    g=reduce(math.gcd,[abs(a) for a in arr],0)
    if not g:return None
    arr=[a//g for a in arr]
    if next(a for a in arr if a)<0:arr=[-a for a in arr]
    return arr if max(abs(a) for a in arr)<=10000 else None

def synthesize(source):
    m=model_original(source,"1")
    heads=m["loop_state"];names=sorted(heads)
    samples,bydepth=sample_reachable(m)
    if len(samples)<3:raise Unsupported("TOO_FEW_REACHABLE_SAMPLES")
    terms=polynomial_terms(names,heads)
    mat=sp.Matrix([[f(row) for _,_,f in terms] for row in samples])
    basis=mat.nullspace()
    polys=[]
    for v in basis[:MAX_POLY]:
        c=primitive_coefficients(v)
        if c is None or not any(c[1:]):continue
        polynomial=z3.Sum(*[z3.IntVal(a)*term
                            for a,(_,term,_) in zip(c,terms) if a])
        polys.append(("quadratic:"+hashlib.sha256(str(c).encode()).hexdigest()[:12],
                      polynomial==0))
    arithmetic,_=pool(source,heads)
    combined=arithmetic+polys
    distinct={};dedup=[]
    for label,pred in combined:
        key=z3.simplify(pred).sexpr()
        if key not in distinct:
            distinct[key]=label;dedup.append((label,pred))
    if len(dedup)>500:raise Unsupported("OVER_500_CANDIDATES")
    prefix=z3.And(*signed_domain(m["initial"]),*m["init_assumptions"])
    bound=z3.And(*signed_domain(heads))
    guard=m["loop_test"]
    t0=time.perf_counter_ns();calls=0
    good=[]
    for label,pred in dedup:
        result=check(z3.And(prefix,z3.Not(subst(pred,heads,m["after_prelude"]))),timeout=2500)
        calls+=1
        if result=="unsat":good.append((label,pred))
    initial_good=len(good)
    cycle=0
    while True:
        cycle+=1
        if cycle>len(dedup)+1:raise Unsupported("FIXPOINT_NOT_REACHED")
        assumptions=z3.And(*[p for _,p in good])
        context=z3.And(bound,assumptions,guard)
        new=[]
        for label,pred in good:
            verdict=check(z3.And(context,z3.Not(subst(pred,heads,m["body_state"]))),timeout=2500)
            calls+=1
            if verdict=="unsat":new.append((label,pred))
        if len(new)==len(good):break
        good=new
    theorem=z3.And(*[p for _,p in good])
    precheck=check(z3.And(prefix,z3.Not(subst(theorem,heads,m["after_prelude"]))))
    inductive=check(z3.And(bound,theorem,guard,z3.Not(subst(theorem,heads,m["body_state"]))))
    safety=check(z3.And(bound,theorem,z3.Not(guard),z3.Not(m["post_assert"])))
    overflow=check(z3.And(bound,theorem,guard,z3.Or(*[
              z3.Or(t<MIN_INT,t>MAX_INT) for t in m["arithmetic_expressions"]
          ]))) if m["arithmetic_expressions"] else "unsat"
    mutation=check(z3.And(bound,theorem,z3.Not(guard)))
    empty=check(z3.And(bound,z3.Not(guard),z3.Not(m["post_assert"])))
    goodproof=(
       all(v=="unsat" for v in (precheck,inductive,safety,overflow))
       and mutation=="sat" and empty=="sat")
    return {
       "status":"QUADRATIC_CLASSICAL_REAL_ORIGINAL_FULLY_PROVEN" if goodproof
                else "QUADRATIC_CLASSICAL_ORIGINAL_NOT_PROVEN",
       "source_variables":names,
       "reachable_samples":len(samples),
       "samples_per_depth":bydepth,
       "feature_count":len(terms),
       "sample_rank":int(mat.rank()),
       "nullspace_dimension":len(basis),
       "polynomial_candidate_count":len(polys),
       "total_comparison_plus_polynomial_candidates":len(dedup),
       "initial_satisfying_candidates":initial_good,
       "final_inductive_candidates":len(good),
       "final_quadratic_candidates":sum(label.startswith("quadratic:") for label,_ in good),
       "final_quadratic_formula_hashes":[hashlib.sha256(t.sexpr().encode()).hexdigest()
                                  for label,t in good if label.startswith("quadratic:")],
       "houdini_iterations":cycle,
       "solver_queries":calls,
       "full_original":{"init":precheck,"inductive":inductive,
             "exit_safety":safety,"signed_overflow":overflow,
             "false_goal":mutation,"empty_invariant":empty},
       "candidate_and_proof_wall_ms":round((time.perf_counter_ns()-t0)/1e6,3),
       "actual_neural_calls":0,
       "published_invariant_used":False,
    }

def run(path):
    raw=path.read_bytes()
    blob=b"blob "+str(len(raw)).encode()+bytes([0])+raw
    if hashlib.sha1(blob).hexdigest()!=EXPECTED_BLOB:raise ValueError("DATASET_GIT_BLOB_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        program=z.read(SOURCE)
    if hashlib.sha256(program).hexdigest()!=EXPECTED_SHA:raise ValueError("ORIGINAL_C_SHA_MISMATCH")
    try:
        result=synthesize(program.decode("utf-8",errors="strict"))
    except Exception as e:
        result={"status":"ABSTAIN_OR_IMPLEMENTATION_ERROR",
                "error":f"{type(e).__name__}: {str(e)[:230]}","actual_neural_calls":0}
    return {"experiment":"Q3J_FIRST_SOURCE_ONLY_QUADRATIC_PROGRAM",
            "source_path":SOURCE,"source_sha256":EXPECTED_SHA,
            "source_byte_modified":False,"external_answer_label_loaded":False,
            "chc_comp_holdouts_read":False,"all_q1_q7":"OPEN","proof":result}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dataset",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args();result=run(a.dataset)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3J_FIRST_OUTCOME",result["proof"]["status"])
    print("Q3J_FOCUSED_DETAILS",{k:v for k,v in result["proof"].items()
           if k in ("source_variables","reachable_samples","feature_count",
                    "nullspace_dimension","polynomial_candidate_count",
                    "final_quadratic_candidates","full_original","error")})
    print("GLOBAL",result["all_q1_q7"])
