"""True original cut-out-1 SAT search with classical SciPy and exact validation.

Purpose: prospectively fixed post-source-open numerical feasibility search.
The solver receives the complete unmodified source formula and optimizes
continuous feasibility; NO source gold SAT/UNSAT data. All original
constraints are re-evaluated as arbitrary precision exact Fractions, and
full ORIGINAL SMT2 grounded SAT must be independently Z3 and cvc5 SAT.

This is pure classical nonlinear optimizer, not learned Q3 uniqueness.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math,re,subprocess,sys,time
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.optimize import minimize,differential_evolution

FROZEN_SOURCE="non-incremental/NRA/20220222-cut-three-circles/cut-out-1.smt2"
FROZEN_GIT_SHA="0c0cd2fa878deac4791b790a8a13cb2747df5b14"
FROZEN_BYTES=2970
CONTRACT_SHA="5a118900a63a5cdb3f941b5cd0b0172d9a85cc4f"
RNG=np.random.default_rng(101)
SOFT_MAX_WALL_SEC=155
NUMERICAL_RESTARTS=120

def git_blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def source_native_assert(src):
    match=re.search(r"\(assert\s",src)
    if match is None or len(re.findall(r"\(assert\s",src))!=1:
        raise ValueError("TRUE_ORIGINAL_HAS_NOT_EXACT_ONE_SMT_ASSERT")
    toks=re.findall(r"\(|\)|[^\s()]+",src[match.start():])
    def parse(i):
        if toks[i]!="(":return toks[i],i+1
        out=[];i+=1
        while i<len(toks) and toks[i]!=")":
            obj,i=parse(i);out.append(obj)
        if i>=len(toks):raise ValueError("MALFORMED_ORIGINAL_SMT2")
        return out,i+1
    tree,_=parse(0)
    q=tree[1]
    if len(tree)!=2 or tree[0]!="assert" or len(q)!=3 or q[0]!="exists":
        raise ValueError("REAL_ORIGINAL_MUST_BE_EXISTENTIAL")
    bound=[v[0] for v in q[1]]
    if bound!=["x"+str(k) for k in range(1,13)] or any(v[1]!="Real" for v in q[1]):
        raise ValueError("ACTUAL_ORIGINAL_BINDER_IDENTITY_CHANGED")
    if q[2][0]!="and" or len(q[2])-1!=39:
        raise ValueError("ACTUAL_ORIGINAL_CONSTRAINTS_COUNT_CHANGED")
    return {"variables":bound,"constraints":q[2][1:],"actual_original_ast":q[2]}

def compile_native_num(node,typ):
    if isinstance(node,str):
        if re.fullmatch(r"x(?:[1-9]|1[0-2])",node):
            i=int(node[1:])-1
            return lambda x,i=i:x[i]
        val=Fraction(node) if typ is Fraction else float(node)
        return lambda x,v=val:v
    op=node[0]
    children=[compile_native_num(v,typ) for v in node[1:]]
    if op=="+":
        return lambda x,s=children:sum((f(x) for f in s),typ(0))
    if op=="*":
        def evaluate(x,s=children):
            y=typ(1)
            for f in s:y*=f(x)
            return y
        return evaluate
    if op=="-":
        if len(children)==1:
            return lambda x,f=children[0]:-f(x)
        return lambda x,s=children:s[0](x)-sum((f(x) for f in s[1:]),typ(0))
    if op=="/":
        if len(children)!=2:raise ValueError("UNSUPPORTED_SOURCE_DIVISION")
        return lambda x,f=children[0],g=children[1]:f(x)/g(x)
    raise ValueError("UNKNOWN_ORIGINAL_NATIVE_SMT_ARITH:"+str(op))

def native_margin_clauses(formulas,typ):
    all_tests=[]
    for n,term in enumerate(formulas):
        op=term[0]
        if op not in ("<","<=",">",">=","="):
            raise ValueError("ORIGINAL_UNEXPECTED_SOURCE_BOOLEAN:"+str(op))
        f=[compile_native_num(v,typ) for v in term[1:]]
        if len(f)<2:raise ValueError("INVALID_ORIGINAL_SMT2_INEQ")
        for j in range(len(f)-1):
            a,b=f[j:j+2]
            if op in ("<","<="):
                fun=lambda x,a=a,b=b:b(x)-a(x)
            elif op in (">",">="):
                fun=lambda x,a=a,b=b:a(x)-b(x)
            else:raise ValueError("UNEXPECTED_EQUALITY_IN_SOURCE_REQUIRE_SPECIAL_PROOF")
            all_tests.append({"original_assertion_index":n,
                              "strict":op in ("<",">"),
                              "fn":fun,"original_operator":op})
    return all_tests

def smt_fraction(v):
    q=Fraction(v)
    def k(n):
        return f"{n}.0" if n>=0 else f"(- {abs(n)}.0)"
    if q.denominator==1:return k(q.numerator)
    return f"(/ {k(q.numerator)} {k(q.denominator)})"

def sexpr(z):
    return z if isinstance(z,str) else "("+" ".join(sexpr(q) for q in z)+")"

def full_grounded_original_Z3_cvc5(original,assignment):
    # Use ORIGINAL source (exact full 39 native constraints), merely bind its
    # existential original variables to exact rational constants. If all are
    # truly satisfied, both original solvers must return SAT.
    assignments=" ".join("("+x+" "+smt_fraction(assignment[i])+")"
                         for i,x in enumerate(original["variables"]))
    text="\n".join(["(set-logic QF_NRA)","(assert (let ("+assignments+") "+
                    sexpr(original["actual_original_ast"])+"))",
                    "(check-sat)","(exit)",""])
    receipts={}
    for engine in ("Z3","cvc5"):
        start=time.perf_counter_ns()
        if engine=="Z3":
            program="import z3,sys;s=z3.SolverFor('QF_NRA');s.set(timeout=5000);s.from_string(sys.stdin.read());print(s.check())"
            cmd=[sys.executable,"-c",program]
        else:
            cmd=["cvc5","--lang=smt2","--tlimit-per=5000","-"]
        status="UNKNOWN";error=None
        try:
            process=subprocess.run(cmd,input=text,text=True,capture_output=True,timeout=7)
            vals=[v.strip().upper() for v in process.stdout.splitlines()
                  if v.strip().lower() in ("sat","unsat","unknown")]
            if process.returncode==0 and vals:status=vals[0]
            else:error="EXIT_"+str(process.returncode)+":"+process.stderr[:200]
        except Exception as e:
            error=type(e).__name__+":"+str(e)[:250]
        receipts[engine]={"actual_original_SMT2_grounded_status":status,
                          "full_original_counterpart_wall_ms":(time.perf_counter_ns()-start)/1e6,
                          "error":error}
    return {"actual_source_grounded_original_sha256":hashlib.sha256(text.encode()).hexdigest(),
            "independent_real_original_full_Z3_cvc5_SAT":
               receipts["Z3"]["actual_original_SMT2_grounded_status"]==
               receipts["cvc5"]["actual_original_SMT2_grounded_status"]=="SAT",
            "original_two_solver_checks":receipts}

def solve(root,contract):
    t0=time.perf_counter()
    path=root/FROZEN_SOURCE
    raw=path.read_bytes()
    if len(raw)!=FROZEN_BYTES or git_blob(raw)!=FROZEN_GIT_SHA:
        raise RuntimeError("FROZEN_AUTHENTIC_ORIGINAL_SOURCE_BLOB_CHANGED")
    actual=source_native_assert(raw.decode("utf-8"))
    float_tests=native_margin_clauses(actual["constraints"],float)
    exact_tests=native_margin_clauses(actual["constraints"],Fraction)
    print("CIRCLES1_ACTUAL_ORIGINAL_AUTHENTIC",True,"TRUE_CONSTRAINTS",len(actual["constraints"]),
          "NATIVE_PAIRWISE_INEQUALITIES",len(float_tests),flush=True)
    n=0;best=float("inf");winner=None;costs=[];successful_exact=False
    bounds=[(0.01,3.0)]*4+[(0.01,2.0)]*4+[(0.01,1.0)]*4
    starts=[
        [2.3,.88,.8,3,2,.88,1.8,.8,.98,.44,.4,.4],
        [1.96,3,2,.8,1.96,2,1.2,1.2,.98,.48,.4,.4],
    ]
    def violated(x):
        try:
            out=np.array([float(c["fn"](x)) for c in float_tests],dtype=float)
            if not np.isfinite(out).all():return None
            return out
        except (OverflowError,ZeroDivisionError,ValueError):
            return None
    def cost(x):
        vals=violated(x)
        if vals is None:return 1e22
        eps=np.array([.001 if c["strict"] else 0 for c in float_tests])
        negative=np.minimum(vals-eps,0)
        return float(np.dot(negative,negative))
    def check_exact(arr,from_method):
        nonlocal winner,successful_exact
        for digits in (4,5,6,7,8):
            exact=[Fraction(str(round(float(v),digits))) for v in arr]
            acceptable=all(
                (q["fn"](exact)>0 if q["strict"] else q["fn"](exact)>=0)
                for q in exact_tests)
            if acceptable:
                proof=full_grounded_original_Z3_cvc5(actual,exact)
                winner={"source_full_integer_rational_assignment":[str(v) for v in exact],
                        "decimal_rounding_precision":digits,
                        "numeric_solver_method":from_method,
                        "original_exact_every_native_SMT2_constraint_checked":len(exact_tests),
                        "all_original_source_native_constraints_satisfied_with_Fraction":True,
                        "independent_original_full_SMT2_SAT_Z3_cvc5":proof}
                successful_exact=proof["independent_real_original_full_Z3_cvc5_SAT"]
                return successful_exact
        return False
    for index in range(NUMERICAL_RESTARTS):
        if time.perf_counter()-t0>SOFT_MAX_WALL_SEC:break
        if index<len(starts):x0=np.array(starts[index],dtype=float)
        else:
            # Numeric trajectory is not a gold-retrieval route.
            rs=RNG.uniform(.1,.92,4)
            s2=float(np.dot(rs,rs))
            if s2>0:rs=np.minimum(0.995,rs*math.sqrt(1.5/s2))
            posx=RNG.uniform(0.1,3,4)
            posy=RNG.uniform(0.1,2,4)
            x0=np.concatenate([posx,posy,rs])
        try:
            optimize=minimize(cost,x0,method="L-BFGS-B",bounds=bounds,
                 options={"maxiter":160,"ftol":1e-10,"maxls":12})
            x=optimize.x;current=cost(x)
            if current<best:
                best=current
                print("CIRCLES1_NUMERIC_BEST",index,"PENALTY",round(best,10),
                      "TRUE_CONSTRAINT_MIN_MARGIN",round(float(min(violated(x))),10),flush=True)
            if current<5e-6:
                refined=minimize(lambda xx: 0.0,x,method="SLSQP",
                    bounds=bounds,
                    constraints=[{"type":"ineq","fun":lambda xx,typ=typ:np.array(
                          [float(q["fn"](xx))-(.0005 if q["strict"] else 0)
                           for q in typ])} for typ in [float_tests]],
                    options={"maxiter":220,"ftol":1e-11})
                if cost(refined.x)<current:x=refined.x;current=cost(x)
                if check_exact(x,"fixed_seed_LBFGSB_then_SLSQP"):
                    break
            n+=1
        except Exception as e:
            costs.append(type(e).__name__+":"+str(e)[:180])
    return {"actual_original_source_git_sha_verified":True,
            "all_39_original_true_source_assertions_preserved":True,
            "numerical_trials_executed":n,
            "numeric_minimum_constraint_violation_squared":best,
            "actual_original_SAT_dual_verified":successful_exact,
            "true_original_full_source_exact_rational_witness":winner,
            "first_frozen_seed":101,
            "bounded_registered_runtime_wall_ms":(time.perf_counter()-t0)*1000,
            "source_grounded_solver_failure_messages":costs[:10],
            "source_status":"CERTIFIED_TRUE_ORIGINAL_SAT" if successful_exact else "UNKNOWN_CLASSICAL_NUMERIC_OPTIMIZER_NO_CERTIFIED_SOURCE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();c=json.loads(a.contract.read_text())
    if c["schema"]!="neumann.q3.cut1_posthoc_exact_source_SAT_search_no_learning.v1":
        raise RuntimeError("ORIGINAL_EXACT_NUMERIC_SEARCH_CONTRACT_CHANGED")
    record={"schema":"neumann.q3.source_cut1_classical_numeric_with_original_exact_dual_v1",
            "preregistered_method_frozen_sha":"5a118900a63a5cdb3f941b5cd0b0172d9a85cc4f",
            "posthoc_same_original_source_already_opened":True,
            "learned_model_training":False,
            "direct_matched_with_same_scipy_has_exact_algorithm_access":True,
            "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN"}
    try:
        record["real_original_numeric_and_exact_evidence"]=solve(a.root,c)
    except Exception as e:
        record["original_status"]="ABSTAIN_SOURCE_OR_RUNTIME_ERROR"
        record["error"]=type(e).__name__+":"+str(e)[:450]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    v=record.get("real_original_numeric_and_exact_evidence",{})
    print("CIRCLES1_FULL_UNCHANGED_REAL_ORIGINAL_SAT_DUAL",v.get("actual_original_SAT_dual_verified",False))
    print("CIRCLES1_TRUE_FULL_ORIGINAL_STATUS",v.get("source_status",record.get("original_status")))
    print("CIRCLES1_Q3_GLOBAL_OPEN",record["global_Q3"])
if __name__=="__main__":
    main()
