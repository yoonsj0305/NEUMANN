"""Pre-registered first frozen-Q3B real-source transfer audit.

No fitting, manual hints, source rewriting, opportunistic grammar expansion, or
hidden benchmark truth. Only structural EXACT training-language recognition
allows inference. Unsupported originals => ABSTAIN before calling model.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import time
import urllib.request

import z3

HERE=pathlib.Path(__file__).resolve().parent
CHECKPOINT=HERE.parent/"q3b-trained-two-relations-20261017"/"frozen_checkpoint.json"
CHECKPOINT_SHA="2d557d5d92f4627749ded23c762ec0faf343ee20db679cee0b3222f15bf1b360"
UPSTREAM="e5a86a1ad252fe1df75e06814769ec1d14540032"
PREREG_COMMIT="47e1677bb9206bbd62395673b526795d52037247"
TARGETS=("inc-max-2-base3-safe.smt2","lists-3-inc-some-safe.smt2")

def source_ident(raw):
    return {
       "sha256":hashlib.sha256(raw).hexdigest(),
       "git_blob_sha1":hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest(),
       "bytes":len(raw)
    }

def pull_original(name):
    if name not in TARGETS:raise ValueError("UNREGISTERED_NAME")
    u=f"https://raw.githubusercontent.com/chc-comp/rust-horn/{UPSTREAM}/{name}"
    with urllib.request.urlopen(u,timeout=30) as response:
        return response.read()

class Unsupported(Exception):
    pass

def is_pred(e):
    return (z3.is_app(e) and e.decl().kind()==z3.Z3_OP_UNINTERPRETED
            and e.sort().kind()==z3.Z3_BOOL_SORT)

def flatten(e):
    if z3.is_and(e):
        return sum((flatten(arg) for arg in e.children()),[])
    return [e]

def eq_guard(a,b):
    s=z3.Solver()
    s.set(timeout=1000)
    s.add(z3.Xor(a,b))
    return s.check()==z3.unsat

def get_rules(source_text):
    assertions=list(z3.parse_smt2_string(source_text))
    if len(assertions)!=5:
        raise Unsupported(f"RELATIONAL_GRAMMAR_CLAUSES_5_REQUIRED_GOT_{len(assertions)}")
    rules=[]
    relations={}
    for i,rule in enumerate(assertions):
        if not z3.is_quantifier(rule) or not rule.is_forall():
            raise Unsupported("NON_FORALL_ORIGINAL")
        local=[z3.Const(f"frozen_original_{i}_{j}",rule.var_sort(j))
               for j in range(rule.num_vars())]
        body=z3.substitute_vars(rule.body(),*local)
        if not z3.is_implies(body):raise Unsupported("ORIGINAL_NOT_IMPLIES")
        prem,head=body.children()
        atoms=flatten(prem)
        calls=[c for c in atoms if is_pred(c)]
        guards=[c for c in atoms if not is_pred(c)]
        if is_pred(head):
            calls2=calls+[head]
        elif z3.is_false(head):
            calls2=calls
        else:raise Unsupported("NON_PREDICATE_HEAD")
        for call in calls2:
            name=call.decl().name()
            relations[name]=call.decl()
            if call.num_args()!=2 or any(call.arg(j).sort().kind()!=z3.Z3_INT_SORT for j in range(2)):
                raise Unsupported("RELATION_NOT_TWO_INTEGER_ARGUMENTS")
        if len(calls)>1:raise Unsupported("NONLINEAR_MULTI_PREMISE")
        rules.append({"source_index":i,"original":rule,"head":head,"calls":calls,
                      "guards":guards})
    if len(relations)!=2:
        raise Unsupported(f"RELATION_GRAPH_REQUIRES_TWO_GOT_{len(relations)}")
    return assertions,rules,relations

def get_offset(head,call):
    increments=[]
    for j in range(2):
        diff=z3.simplify(head.arg(j)-call.arg(j))
        if not z3.is_int_value(diff):
            raise Unsupported("NON_CONSTANT_AFFINE_INCREMENT")
        increments.append(diff.as_long())
    return tuple(increments)

def extract_exact(source_text):
    assertions,rows,relations=get_rules(source_text)
    initial=[r for r in rows if is_pred(r["head"]) and not r["calls"]]
    if len(initial)!=1:raise Unsupported("NEED_SINGLE_INIT")
    r0=initial[0]
    A=r0["head"].decl().name()
    zero=z3.And(r0["head"].arg(0)==0,r0["head"].arg(1)==0)
    if not eq_guard(z3.And(*r0["guards"]),zero):
        raise Unsupported("INIT_NOT_ZERO_ZERO")
    cross=[r for r in rows if r["calls"] and is_pred(r["head"])
           and r["calls"][0].decl().name()==A and r["head"].decl().name()!=A]
    if len(cross)!=1:raise Unsupported("NEED_ONE_CROSS_TRANSITION")
    B=cross[0]["head"].decl().name()
    selfA=[r for r in rows if r["calls"] and is_pred(r["head"])
           and r["calls"][0].decl().name()==A and r["head"].decl().name()==A]
    selfB=[r for r in rows if r["calls"] and is_pred(r["head"])
           and r["calls"][0].decl().name()==B and r["head"].decl().name()==B]
    goals=[r for r in rows if z3.is_false(r["head"])]
    if len(selfA)!=len(selfB)!=1:
        raise Unsupported("SELF_LOOP_COUNT_MISMATCH")
    if len(selfA)!=1 or len(selfB)!=1 or len(goals)!=1:
        raise Unsupported("ORIGINAL_FIVE_RULE_SHAPE_DIFFERS")
    for r in selfA+selfB+[cross[0]]:
        if not eq_guard(z3.And(*r["guards"]),z3.BoolVal(True)):
            raise Unsupported("UNACCOUNTED_TRANSITION_GUARDS")
    if len(goals[0]["calls"])!=1 or goals[0]["calls"][0].decl().name()!=B:
        raise Unsupported("GOAL_MUST_CHECK_SECOND_PREDICATE")
    a,b=get_offset(selfA[0]["head"],selfA[0]["calls"][0])
    a2,b2=get_offset(selfB[0]["head"],selfB[0]["calls"][0])
    if (a,b)!=(a2,b2):raise Unsupported("DIFFERENT_SELF_LOOP_SEMANTICS")
    p,q=get_offset(cross[0]["head"],cross[0]["calls"][0])
    pred=goals[0]["calls"][0]
    goal=z3.And(pred.arg(1)==q,pred.arg(0)!=p)
    if not eq_guard(z3.And(*goals[0]["guards"]),goal):
        raise Unsupported("GOAL_NOT_TRAINING_SEMANTICS")
    if a==0 and b==0:raise Unsupported("DEGENERATE_SELF_LOOP")
    return (a,b,p,q), (A,B), assertions

def frozen_coefficients(a,b,p,q):
    raw=CHECKPOINT.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CHECKPOINT_SHA:
        raise ValueError("FROZEN_CHECKPOINT_IDENTITY_MISMATCH")
    W=json.loads(raw)["weights"]
    if len(W)!=5 or any(len(row)!=8 for row in W):
        raise ValueError("FROZEN_WEIGHT_SHAPE_MISMATCH")
    x=[a,b,p,q,a*p,a*q,b*p,b*q]
    return [round(sum(u*v for u,v in zip(row,x))) for row in W]

def num(i):
    return str(i) if i>=0 else f"(- {-i})"

def candidate_defs(names,coeff):
    A,B=names
    u,v,w,t,k=coeff
    return (f"(define-fun {A} ((x Int)(y Int)) Bool (= (+ (* {num(u)} x) (* {num(v)} y)) 0))\n"
            f"(define-fun {B} ((x Int)(y Int)) Bool (= (+ (* {num(w)} x) (* {num(t)} y)) {num(k)}))\n")

def check_original(assertions,names,coeff):
    defs=candidate_defs(names,coeff)
    results=[]
    for original in assertions:
        solver=z3.Solver()
        solver.set(timeout=5000)
        # Reparse original quantified formula under candidate interpretations.
        parsed=z3.parse_smt2_string(
          "(set-logic ALL)\n"+defs+"(assert (not "+original.sexpr()+"))")
        if len(parsed)!=1:raise ValueError("BAD_ORIGINAL_VERIFICATION_PARSE")
        solver.add(parsed[0])
        z=solver.check()
        results.append(str(z))
    return results

def case(name,raw):
    started=time.perf_counter_ns()
    result={"name":name, "original":source_ident(raw),
      "frozen_upstream":UPSTREAM,"frozen_checkpoint_sha256":CHECKPOINT_SHA,
      "science_verdict":"ABSTAIN_UNSUPPORTED_SOURCE_GRAPH",
      "model_inference_calls":0,"source_modified":False,
      "global_q1_q7":"OPEN"}
    try:
        content=raw.decode("utf-8")
        began=time.perf_counter_ns()
        info,names,assertions=extract_exact(content)
        result["structural_read_ms"]=(time.perf_counter_ns()-began)/1e6
        a,b,p,q=info
        begin=time.perf_counter_ns()
        proposed=frozen_coefficients(*info)
        result["model_inference_calls"]=1
        result["model_proposal_ms"]=(time.perf_counter_ns()-begin)/1e6
        classical=[-b,a,-b,a,-b*p+a*q]
        result["source_extracted_increments"]=info
        result["source_predicates"]=names
        result["proposed_coefficients"]=proposed
        result["equal_information_classical_coefficients"]=classical
        learned=check_original(assertions,names,proposed)
        baseline=check_original(assertions,names,classical)
        result["learned_clause_checks"]=learned
        result["classical_clause_checks"]=baseline
        result["zero_head_first"]=check_original([assertions[-1]],names,[0]*5)[0]
        result["science_verdict"]=("LEARNED_FULL_ORIGINAL_CERTIFIED_CLASSICAL_EQUAL"
          if len(learned)==5 and all(v=="unsat" for v in learned)
          and all(v=="unsat" for v in baseline)
          and result["zero_head_first"]=="sat" and proposed==classical
          else "ABSTAIN_ORIGINAL_PROOF_OR_ABLATION_FAILURE")
    except Unsupported as e:
        result["unsupported_reason"]=str(e)
    except Exception as e:
        result["science_verdict"]="BLOCKED_OR_ENGINEERING_ERROR"
        result["error"]=f"{type(e).__name__}: {str(e)[:500]}"
    result["whole_case_wall_ms"]=(time.perf_counter_ns()-started)/1e6
    return result

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=pathlib.Path)
    args=p.parse_args()
    result={"kind":"FGSR_Q3B_first_immutable_authentic_external_transfer",
      "preregistered_before_source_commit":PREREG_COMMIT,
      "external_repository":"chc-comp/rust-horn","revision":UPSTREAM,
      "model_checkpoint":CHECKPOINT_SHA,"model_retrained":False,
      "source_groups_not_independent":True,
      "global_q1_q7":"OPEN","results":[]}
    for target in TARGETS:
        try:
            raw=pull_original(target)
            result["results"].append(case(target,raw))
        except Exception as e:
            result["results"].append({"name":target,"science_verdict":"BLOCKED_SOURCE_FETCH",
              "error":f"{type(e).__name__}: {str(e)[:400]}",
              "model_inference_calls":0})
    result["model_calls_total"]=sum(r["model_inference_calls"] for r in result["results"])
    result["covered"]=sum(r["science_verdict"].startswith("LEARNED_FULL_ORIGINAL") for r in result["results"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3B_EXTERNAL",[ (x["name"],x["science_verdict"],x.get("unsupported_reason")) for x in result["results"]])
    print("COVERED",result["covered"],"MODEL_CALLS",result["model_calls_total"],"Q1-Q7",result["global_q1_q7"])

if __name__=="__main__":main()
