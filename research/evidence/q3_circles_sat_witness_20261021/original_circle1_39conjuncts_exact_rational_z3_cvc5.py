"""True source original circle-cutting existential SAT from exact rationals.

Posthoc human-directed numerical search found 12 rational coordinates. This
script reads the unchanged ORIGINAL quantified 39-inequality SMT-LIB source,
checks each original conjunct with arbitrary-precision fractions and asks
both Z3 and cvc5 to check the FULL ORIGINAL original body under its witness.
No guessing SAT from floating point or altering source clauses. Negative
control deliberately violates an original native source bound and must
be UNSAT independently in both engines.
"""
from __future__ import annotations
import argparse,fractions,hashlib,json,re,subprocess,sys,time
from pathlib import Path

FIRST_SOURCE_METADATA_COMMIT="5412a4fb16c96694ab2bf629c34f6e41737f7a7f"
PATH="non-incremental/NRA/20220222-cut-three-circles/cut-out-1.smt2"

def sha1_blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def sha256(b):return hashlib.sha256(b).hexdigest()

def parse_source(source):
    match=re.search(r"\(assert\s",source)
    if match is None or len(re.findall(r"\(assert\s",source))!=1:
        raise ValueError("ORIGINAL_ONE_ASSERTION_REQUIRED")
    tokens=re.findall(r"\(|\)|[^\s()]+",source[match.start():])
    def step(i):
        if tokens[i]!="(":return tokens[i],i+1
        out=[];i+=1
        while i<len(tokens) and tokens[i]!=")":
            v,i=step(i);out.append(v)
        if i>=len(tokens):raise ValueError("SOURCE_ASSERTION_UNBALANCED")
        return out,i+1
    node,_=step(0)
    if not (len(node)==2 and node[0]=="assert" and
            isinstance(node[1],list) and node[1][0]=="exists"):
        raise ValueError("ACTUAL_ORIGINAL_NOT_EXISTENTIAL")
    q=node[1]
    decl=q[1]
    if len(decl)!=12 or set(x[0] for x in decl)!={
            "x"+str(i) for i in range(1,13)}:
        raise ValueError("ORIGINAL_TWELVE_REAL_VARIABLES_MISSING")
    if any(len(x)!=2 or x[1]!="Real" for x in decl):
        raise ValueError("ORIGINAL_12_REAL_TYPE_CHECK_FAILED")
    body=q[2]
    if not (isinstance(body,list) and body[0]=="and" and
            len(body)==40):
        raise ValueError("ORIGINAL_FULL_39_NATIVE_CONJUNCTS_MISSING")
    return {"varnames":[x[0] for x in decl],
            "quantifier":"exists",
            "entire_original_39_conjuncts":body[1:],
            "original_entire_native_conjunction_AST":body,
            "full_original_conjunct_count":len(body)-1}

def evaluate_arith(node,values):
    if isinstance(node,str):
        if node in values:return values[node]
        return fractions.Fraction(node)
    op=node[0]
    args=[evaluate_arith(t,values) for t in node[1:]]
    if op=="+":return sum(args,fractions.Fraction(0))
    if op=="-":
        return -args[0] if len(args)==1 else args[0]-sum(args[1:],fractions.Fraction(0))
    if op=="*":
        r=fractions.Fraction(1)
        for t in args:r*=t
        return r
    if op=="/":
        if len(args)!=2 or args[1]==0:
            raise ValueError("UNSUPPORTED_SOURCE_DIVISION")
        return args[0]/args[1]
    raise ValueError("UNSUPPORTED_ACTUAL_SOURCE_ARITHMETIC_OPERATOR_"+str(op))

def exact_truth(expr,values):
    if not isinstance(expr,list):raise ValueError("INVALID_BOOL_ORIGINAL_TERM")
    op=expr[0]
    if op=="and":return all(exact_truth(x,values) for x in expr[1:])
    if op=="or":return any(exact_truth(x,values) for x in expr[1:])
    if op=="not":return not exact_truth(expr[1],values)
    if op=="=>":return not exact_truth(expr[1],values) or exact_truth(expr[2],values)
    nums=[evaluate_arith(x,values) for x in expr[1:]]
    if len(nums)<2:raise ValueError("ORIGINAL_NATIVE_NON_BINARY_COMPARATOR")
    for a,b in zip(nums,nums[1:]):
        if op=="<" and not a<b:return False
        if op=="<=" and not a<=b:return False
        if op==">" and not a>b:return False
        if op==">=" and not a>=b:return False
        if op=="=" and not a==b:return False
    if op not in ("<","<=",">",">=","="):
        raise ValueError("UNSUPPORTED_ORIGINAL_NATIVE_BOOLEAN_"+str(op))
    return True

def native(expr):
    return expr if isinstance(expr,str) else "("+" ".join(native(q) for q in expr)+")"

def real_const(x):
    f=fractions.Fraction(x)
    def atom(n):return str(n)+".0" if n>=0 else "(- "+str(-n)+".0)"
    if f.denominator==1:return atom(f.numerator)
    return "(/ "+atom(f.numerator)+" "+atom(f.denominator)+")"

def independently_original_ground_SMT(source,values):
    binder=" ".join("("+n+" "+real_const(values[n])+")" for n in source["varnames"])
    smt="\n".join([
        "(set-logic QF_NRA)",
        "(assert (let ("+binder+") "+native(source["original_entire_native_conjunction_AST"])+"))",
        "(check-sat)","(exit)",""])
    observed={}
    for engine in ("z3","cvc5"):
        t=time.perf_counter_ns()
        if engine=="z3":
            py="import sys,z3;v=z3.Solver();v.set(timeout=5000);v.from_string(sys.stdin.read());print(v.check())"
            cmd=[sys.executable,"-c",py]
        else:
            cmd=["cvc5","--lang=smt2","--tlimit-per=5000","-"]
        status="UNKNOWN";error=None
        try:
            q=subprocess.run(cmd,input=smt,text=True,capture_output=True,timeout=7)
            found=[k.strip().upper() for k in q.stdout.splitlines()
                   if k.strip().lower() in ("sat","unsat","unknown")]
            if q.returncode==0 and found:status=found[0]
            else:error="exit="+str(q.returncode)+":"+q.stderr[:210]
        except Exception as e:
            error=type(e).__name__+":"+str(e)[:250]
        observed[engine]={"full_native_ground_original_result":status,
                           "original_full_formula_solver_wall_ms":(time.perf_counter_ns()-t)/1e6,
                           "error":error}
    return {"original_grounded_all_39_native_constraints_full_SMT2_SHA256":sha256(smt.encode()),
            "actual_Z3_cvc5_ground_full_original_source":observed,
            "both_authentic_independent_SAT":observed["z3"]["full_native_ground_original_result"]==
                                         observed["cvc5"]["full_native_ground_original_result"]=="SAT",
            "both_authentic_independent_UNSAT":observed["z3"]["full_native_ground_original_result"]==
                                           observed["cvc5"]["full_native_ground_original_result"]=="UNSAT"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text())
    meta=json.loads(a.freeze.read_text())
    if c["schema"]!="neumann.q3.posthoc_cutout1_concrete_12real_sat_candidate_v1":
        raise RuntimeError("PREREGISTERED_POSITIVE_CIRCLE_EXACT_FRACTIONS_CHANGED")
    item=next(q for q in meta["cases"] if q["path"]==PATH)
    if len(c["candidate_real_rational_decimal_strings"])!=12:
        raise RuntimeError("FROZEN_CONSTRUCTED_REAL_VECTOR_WRONG_DIMENSION")
    start=time.perf_counter_ns()
    evidence={"true_original_source_Git_blob_authenticated":False,
              "actual_original_12real_full_39constraints_SAT_certified":False,
              "source_witness_is_human_CPU_posthoc_NOT_learned":True,
              "status":"ABSTAIN"}
    try:
        raw=(a.root/PATH).read_bytes()
        if len(raw)!=item["bytes"] or sha1_blob(raw)!=item["git_blob"]:
            raise RuntimeError("ORIGINAL_SOURCE_SHA_OR_SIZE_MISMATCH")
        evidence["true_original_source_Git_blob_authenticated"]=True
        evidence["original_source_SHA256"]=sha256(raw)
        native_original=parse_source(raw.decode("utf-8"))
        values={"x"+str(i+1):fractions.Fraction(v) for i,v in enumerate(
            c["candidate_real_rational_decimal_strings"])}
        native_results=[exact_truth(predicate,values) for predicate in
                        native_original["entire_original_39_conjuncts"]]
        evidence["true_original_all_39_conjuncts_checked_exact_Fraction"] = len(native_results)
        evidence["original_39_exact_native_boolean_results"]=native_results
        evidence["all_39_original_true_with_no_floating_rounding"]=all(native_results)
        evidence["twelve_original_rational_values"]={k:str(v) for k,v in values.items()}
        if not all(native_results):
            raise RuntimeError("FROZEN_WITNESS_FAILS_ACTUAL_SOURCE_CLAUSES_INDEX:"+
                               str([i for i,ok in enumerate(native_results) if not ok]))
        independent=independently_original_ground_SMT(native_original,values)
        evidence["original_all_native_grounded_independent_Z3_cvc5_SAT"]=independent
        negative=dict(values)
        negative["x9"]=fractions.Fraction(2)
        wrong_results=[exact_truth(expr,negative) for expr in native_original[
            "entire_original_39_conjuncts"]]
        evidence["negative_control_actually_violates_original_geometry"]=not all(wrong_results)
        evidence["negative_control_actual_original_SMT2"]=independently_original_ground_SMT(native_original,negative)
        evidence["actual_original_12real_full_39constraints_SAT_certified"]=(
            independent["both_authentic_independent_SAT"] and
            evidence["negative_control_actually_violates_original_geometry"] and
            evidence["negative_control_actual_original_SMT2"]["both_authentic_independent_UNSAT"])
        evidence["status"]="TRUE_SOURCE_ORIGINAL_EXISTENTIAL_39CLAUSE_SAT_DUAL_SMT" if evidence[
            "actual_original_12real_full_39constraints_SAT_certified"] else "ABSTAIN_DUAL_SMT_OR_NEGATIVE_CONTROL"
    except Exception as e:
        evidence["status"]="ABSTAIN_AUTHENTIC_ORIGINAL_PROOF_EXCEPTION"
        evidence["error"]=type(e).__name__+":"+str(e)[:380]
    evidence["whole_full_actual_source_parse_arith_dual_and_controls_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    outcome={
      "schema":"neumann.q3.actual_original_all_real_circle1_full_existential_source_SAT.v1",
      "original_SHA_metadata_before_first_content_freeze_commit":FIRST_SOURCE_METADATA_COMMIT,
      "current_SAT_witness_constructed_only_AFTER_historical_source_18_first_expert_screen":True,
      "original_exact_Fraction_true_all_39_native_inequalities":evidence.get(
          "all_39_original_true_with_no_floating_rounding",False),
      "original_full_true_SMT2_dual_Z3_cvc5_SAT":evidence[
           "actual_original_12real_full_39constraints_SAT_certified"],
      "no_novel_neural_or_learned_model_discovery":True,
      "strong_classical_equal_rights_can_use_same_numerical_structure_search":True,
      "no_warm_runtime_or_train_cost_10x_claim":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "evidence":evidence
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n")
    print("Q3_CIRCLE1_TRUE_ORIGINAL_SHA",evidence["true_original_source_Git_blob_authenticated"])
    print("Q3_CIRCLE1_ALL_NATIVE_39_REAL_CONSTRAINTS_EXACT",evidence.get("all_39_original_true_with_no_floating_rounding"))
    print("Q3_CIRCLE1_REAL_SOURCE_FULL_Z3_CVC5_SAT",outcome["original_full_true_SMT2_dual_Z3_cvc5_SAT"])
    print("Q3_CIRCLE1_WRONG_MODEL_NEGATIVE_SAT_REJECTED",evidence.get("negative_control_actual_original_SMT2",{}).get("both_authentic_independent_UNSAT"))
    print("Q3_CIRCLE1_STATUS",evidence["status"])
    print("Q3_GLOBAL_Q3_Q4",outcome["global_Q3"],outcome["global_Q4"])
if __name__=="__main__":
    main()
