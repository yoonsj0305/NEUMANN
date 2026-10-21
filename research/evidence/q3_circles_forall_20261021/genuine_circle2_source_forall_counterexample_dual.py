"""Exact source counterexample to genuine original quantified circle-cutting
constraint (not a rendered approximation). Posthoc, no neural inference.

The original source is ∀ x1..x12. (original antecedent) => (original
consequent). We find exact rational positive circle positions/radii that
satisfy EVERY native antecedent and contradict original consequent.
Then independently Z3/cvc5 SAT on grounded ORIGINAL entire implication's
negation proves full source quantified assertion UNSAT for all contexts.
"""
from __future__ import annotations
import argparse,fractions,hashlib,json,re,subprocess,sys,time
from pathlib import Path

FIRST_SOURCE_SHA_META="5412a4fb16c96694ab2bf629c34f6e41737f7a7f"
SOURCE_PATH="non-incremental/NRA/20220222-cut-three-circles/cut-out-2.smt2"

def sha1_blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def sha256(b):return hashlib.sha256(b).hexdigest()

def parse_source_expr(src):
    match=re.search(r"\(assert\s",src)
    if match is None or len(re.findall(r"\(assert\s",src))!=1:
        raise ValueError("ORIGINAL_CIRCLE_ONE_ASSERTION_REQUIRED")
    tokens=re.findall(r"\(|\)|[^\s()]+",src[match.start():])
    def parse(i):
        if tokens[i]!="(":return tokens[i],i+1
        q=[];i+=1
        while i<len(tokens) and tokens[i]!=")":
            p,i=parse(i);q.append(p)
        if i>=len(tokens):raise ValueError("SOURCE_UNBALANCED_S_EXPR")
        return q,i+1
    ast,_=parse(0)
    if len(ast)!=2 or ast[0]!="assert" or not isinstance(ast[1],list) or ast[1][0]!="forall":
        raise ValueError("TRUE_ORIGINAL_EXPECT_ONE_FORALL")
    forall=ast[1]
    names=[x[0] for x in forall[1]]
    if len(names)!=12 or set(names)!={f"x{i}" for i in range(1,13)}:
        raise ValueError("REAL_ORIGINAL_TWELVE_CIRCLE_DIMENSIONS_MISMATCH")
    if any(x[1]!="Real" for x in forall[1]):
        raise ValueError("REAL_ORIGINAL_ALL_CIRCLE_VARS_MUST_REAL")
    pred=forall[2]
    if len(pred)!=3 or pred[0]!="=>" or pred[1][0]!="and":
        raise ValueError("ACTUAL_SOURCE_NOT_ORIGINAL_GEOMETRY_IMPLICATION")
    if len(pred[1])<20:raise ValueError("MISSING_TRUE_ORIGINAL_GEOMETRY_CONSTRAINTS")
    return {"variables":names,"original_native_forall":forall,
            "entire_original_antecedent":pred[1],"original_entire_consequent":pred[2],
            "native_antecedent_conjunct_count":len(pred[1])-1}

def numeric(expr,env):
    if isinstance(expr,str):
        if expr in env:return fractions.Fraction(env[expr])
        return fractions.Fraction(expr)
    if not expr or not isinstance(expr,list):raise ValueError("INVALID_ORIGINAL_NATIVE_TERM")
    op=expr[0];args=[numeric(x,env) for x in expr[1:]]
    if op=="+":return sum(args,fractions.Fraction(0))
    if op=="-":
        return -args[0] if len(args)==1 else args[0]-sum(args[1:],fractions.Fraction(0))
    if op=="*":
        y=fractions.Fraction(1)
        for z in args:y*=z
        return y
    if op=="/":
        if len(args)!=2 or args[1]==0:raise ValueError("UNSUPPORTED_SOURCE_DIVISION")
        return args[0]/args[1]
    raise ValueError("INVALID_ORIGINAL_ARITHMETIC:"+str(op))

def logical(pred,env):
    if not isinstance(pred,list):raise ValueError("ORIGINAL_EXPECT_BOOLEAN_TERM")
    op=pred[0]
    if op=="and":return all(logical(x,env) for x in pred[1:])
    if op=="or":return any(logical(x,env) for x in pred[1:])
    if op=="not":return not logical(pred[1],env)
    if op=="=>":return not logical(pred[1],env) or logical(pred[2],env)
    if op in ("<","<=",">",">=","="):
        if len(pred)!=3:raise ValueError("ORIGINAL_NONBINARY_COMPARE")
        x,y=numeric(pred[1],env),numeric(pred[2],env)
        return {"<":lambda:x<y,"<=":lambda:x<=y,">":lambda:x>y,
                ">=":lambda:x>=y,"=":lambda:x==y}[op]()
    raise ValueError("UNSUPPORTED_ORIGINAL_BOOLEAN_OPERATOR:"+str(op))

def candidates():
    # deterministic constructive placement, NOT a learned coordinate prior.
    # Upper 3x2 geometry and all source inequalities tested EXACTLY as-is.
    for r in (fractions.Fraction(1,20),fractions.Fraction(1,10),
              fractions.Fraction(3,20)):
      for near in (fractions.Fraction(2,5),fractions.Fraction(1,2),
                   fractions.Fraction(3,5)):
        for far in (fractions.Fraction(12,5),fractions.Fraction(5,2),
                    fractions.Fraction(13,5)):
          for low in (fractions.Fraction(3,10),fractions.Fraction(2,5)):
            for high in (fractions.Fraction(8,5),fractions.Fraction(17,10)):
              q=[near,far,near,far,low,low,high,high,r,r,r,r]
              yield {f"x{i+1}":value for i,value in enumerate(q)}

def sexpr(node):
    return node if isinstance(node,str) else "("+" ".join(sexpr(z) for z in node)+")"

def real_literal(q):
    f=fractions.Fraction(q)
    def pos(v):return str(v)+".0" if v>=0 else "(- "+str(-v)+".0)"
    if f.denominator==1:return pos(f.numerator)
    return "(/ "+pos(f.numerator)+" "+pos(f.denominator)+")"

def dual_native_complete_source_counterexample(forall,point):
    # Source symbol names are the real originally bound variables, not
    # invented auxiliary strengthening of any original condition.
    body=sexpr(forall[2])
    bindings=" ".join(f"({name} {real_literal(point[name])})"
                     for name in [x[0] for x in forall[1]])
    formula="(let ("+bindings+") "+body+")"
    script="\n".join(["(set-logic QF_NRA)",
                     "(assert (not "+formula+"))","(check-sat)","(exit)",""])
    outcomes={}
    for engine in ("z3","cvc5"):
        t=time.perf_counter_ns()
        if engine=="z3":
            code="import z3,sys;s=z3.Solver();s.set(timeout=4000);s.from_string(sys.stdin.read());print(s.check())"
            cmd=[sys.executable,"-c",code]
        else:cmd=["cvc5","--lang=smt2","--tlimit-per=4000","-"]
        state="UNKNOWN";error=None
        try:
            p=subprocess.run(cmd,input=script,text=True,capture_output=True,timeout=6)
            statuses=[q.strip().upper() for q in p.stdout.splitlines()
                      if q.strip().lower() in ("sat","unsat","unknown")]
            if p.returncode==0 and statuses:state=statuses[0]
            else:error="exit:"+str(p.returncode)+":"+p.stderr[:210]
        except Exception as e:error=type(e).__name__+":"+str(e)[:180]
        outcomes[engine]={"result":state,
             "full_original_grounded_SMT2_query_wall_ms":(time.perf_counter_ns()-t)/1e6,
             "error":error}
    return {"unchanged_original_forall_countermodel_QF_NRA_SHA256":sha256(script.encode()),
            "native_original_entire_consequent_not_omitted":True,
            "both_Z3_and_cvc5_full_source_ground_counterexample_SAT":
                 outcomes["z3"]["result"]==outcomes["cvc5"]["result"]=="SAT",
            "two_independent_solver_receipts":outcomes}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    o=p.parse_args()
    contract=json.loads(o.contract.read_text())
    if contract["schema"]!="neumann.q3.posthoc_actual_cut_three_circles_source_exact_forall_counterexample.v1":
        raise RuntimeError("SOURCE_ORIGINAL_COUNTERMODEL_CONTRACT_CHANGED")
    meta=json.loads(o.freeze.read_text())
    case=next(x for x in meta["cases"] if x["path"]==SOURCE_PATH)
    start=time.perf_counter_ns()
    receipt={"original_source_Git_SHA_authenticated":False,
             "original_forall_actually_refuted":False,
             "status":"UNKNOWN_NO_TRUE_COUNTEREXAMPLE",
             "source_original_posthoc_not_learned_discovery":True}
    try:
        b=(o.root/SOURCE_PATH).read_bytes()
        if len(b)!=case["bytes"] or sha1_blob(b)!=case["git_blob"]:
            raise RuntimeError("ORIGINAL_SOURCE_SHA_AND_SIZE_NOT_FROZEN")
        receipt["original_source_Git_SHA_authenticated"]=True
        receipt["real_source_SHA256"]=sha256(b)
        original=parse_source_expr(b.decode("utf-8"))
        receipt["full_original_assertion_antecedent_native_conjunct_count"]=original["native_antecedent_conjunct_count"]
        tested=0
        for trial in candidates():
            tested+=1
            conjunction=original["entire_original_antecedent"]
            consequent=original["original_entire_consequent"]
            passed=[logical(x,trial) for x in conjunction[1:]]
            if not all(passed):continue
            if logical(consequent,trial):continue
            receipt["exact_countermodel_source_native_rational_vector"]={
                k:str(v) for k,v in trial.items()}
            receipt["ALL_actual_original_antecedent_conjuncts_TRUE"] = all(passed)
            receipt["actual_original_consequent_FALSE"]=True
            receipt["number_original_antecedent_clauses_exactly_checked"]=len(passed)
            receipt["registered_bounded_geometric_trial_count"]=tested
            proof=dual_native_complete_source_counterexample(original["original_native_forall"],trial)
            receipt["original_full_native_SMT2_dual_Z3_cvc5"]=proof
            receipt["original_forall_actually_refuted"]=proof["both_Z3_and_cvc5_full_source_ground_counterexample_SAT"]
            receipt["status"]="ORIGINAL_TRUE_QUANTIFIED_UNSAT_VIA_SOURCE_EXACT_COUNTEREXAMPLE_DUAL" if receipt["original_forall_actually_refuted"] else "UNKNOWN_FAILED_NATIVE_DUAL_FULL_SOURCE"
            break
        else:
            receipt["registered_bounded_geometric_trial_count"]=tested
    except Exception as e:
        receipt["status"]="ABSTAIN_ORIGINAL_SOURCE_ARITH_OR_VERIFIER_EXCEPTION"
        receipt["error"]=type(e).__name__+":"+str(e)[:360]
    receipt["all_true_original_source_geometry_and_independent_dual_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    report={"schema":"neumann.q3.real_original_circles2_all_real_UNSAT_counterexample.v1",
        "source_git_sha_before_first_original_content_commit":FIRST_SOURCE_SHA_META,
        "source_original_status_in_historical_18_expert_screen":"UNKNOWN",
        "source_body_opened_in_parent_historical_FIRST_CI":True,
        "actual_original_sat_or_unsat_result":receipt["status"],
        "actual_original_source_evidence":receipt,
        "not_neural_or_learned_new_structure":True,
        "no_silent_upgrade_historical_original_18_13_solved_data":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN"}
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q3_REAL_CIRCLE2_AUTHENTIC",receipt["original_source_Git_SHA_authenticated"])
    print("Q3_REAL_CIRCLE2_FOREALL_ORIGINAL_FALSE_DUAL",receipt["original_forall_actually_refuted"])
    print("Q3_REAL_CIRCLE2_EXACT_RATIONAL_WITNESS",receipt.get("exact_countermodel_source_native_rational_vector"))
    print("Q3_REAL_CIRCLE2_TRUE_ORIGINAL_STATUS",receipt["status"])
    print("Q3_Q4_GLOBAL_OPEN",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
