"""Q3-S3 FIRST: synthesize dense 3-variable invariants outside conjunctive Γ2 octagons.
This is a CONSTRUCTED classical exact algebra demonstration, NOT learned invention.
First experiment preregistration GitHub Issue #251 (before this code/CI).
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from time import perf_counter_ns

import sympy as sp
import z3

NORMALS = (
    (1,1,1),(1,2,3),(2,3,5),(3,2,1),
    (1,-2,3),(2,-3,5),(3,1,-2),(5,-2,3),
    (1,4,7),(4,3,-2),(5,3,2),(2,-1,-3),
)
assert len(NORMALS)==12

def canonical_bytes(data):
    return json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def primitive(vec):
    """Return primitive signed integer normal with fixed positive first coordinate."""
    vals=[sp.Rational(x) for x in vec]
    den=math.lcm(*(int(v.q) for v in vals))
    ints=[int(v*den) for v in vals]
    g=math.gcd(*[abs(v) for v in ints])
    if g==0:raise ValueError("NULL_INVARIANT")
    ints=[v//g for v in ints]
    if next(v for v in ints if v)!=abs(next(v for v in ints if v)):
        ints=[-v for v in ints]
    return tuple(ints)

def source_from_normal(v,index):
    """Author-constructed originals; v is private evaluator metadata."""
    a,b,c=v
    if a*b*c==0 or math.gcd(abs(a),abs(b),abs(c))!=1:
        raise ValueError("UNSUITABLE_DENSE_NORMAL")
    initial=(index%5-2,(index*index)%7-3,(index*3)%9-4)
    d1=(b,-a,0)
    d2=(c,0,-a)
    steps=(d1,tuple(-x for x in d1),d2,tuple(-x for x in d2))
    return {"initial":initial,"steps":steps,
       "original_post_private":{"normal":v,
           "constant":sum(x*y for x,y in zip(v,initial)),
           "disjunct":"conservation OR first_coordinate_equals_initial"}}

def propose_from_public(initial,steps):
    """ONLY source Pre singleton and transition deltas; no post, target, labels."""
    if len(initial)!=3 or len(steps)!=4:
        raise ValueError("UNSUPPORTED_DIMENSION_OR_TRANSITION")
    mat=sp.Matrix([[int(x) for x in d] for d in steps])
    if mat.rank()!=2:
        raise ValueError("NOT_RANK_TWO")
    ns=mat.nullspace()
    if len(ns)!=1:
        raise ValueError("NOT_UNIQUE_CONSERVED_HYPERPLANE")
    normal=primitive(ns[0])
    constant=sum(int(a)*int(b) for a,b in zip(normal,initial))
    if len([x for x in normal if x])!=3:
        raise ValueError("INVARIANT_IN_OLD_TWO_VARIABLE_DOMAIN")
    if any(sum(a*b for a,b in zip(normal,d))!=0 for d in steps):
        raise ValueError("PROPOSER_CONSERVATION_CHECK_FAIL")
    return {"normal":normal,"constant":constant,
        "method":"EXACT_TRANSITION_DIFFERENCE_NULLSPACE",
        "private_post_read":False,"oracle_gold_used":False,
        "neural_calls":0}

def octagon_atoms():
    out=[]
    for i in range(3):
        for a in (-1,1):
            q=[0]*3;q[i]=a;out.append(tuple(q))
    for i,j in itertools.combinations(range(3),2):
        for a,b in itertools.product((-1,1),repeat=2):
            q=[0]*3;q[i]=a;q[j]=b;out.append(tuple(q))
    assert len(out)==18 and len(set(out))==18
    return out

def octagon_impossibility(steps):
    """Every candidate finite Γ2 atom is unbounded above on reachable states.

    Each ±step transition may repeat unboundedly. If q·d≠0, the reachable
    sequence s0+n*(sign(q·d)*d) makes q·s→+∞. Hence no finite upper-bound
    Γ2 atom, or nonempty finite conjunction thereof, includes all reachable states.
    """
    witness=[]
    for q in octagon_atoms():
        witness_d=next((d for d in steps
                 if sum(a*b for a,b in zip(q,d))>0),None)
        if witness_d is None:
            return {"separation_proved":False,"failed_octagon_atom":q}
        witness.append({"atom":q,"repeat_positive_delta":witness_d,
            "slope":sum(a*b for a,b in zip(q,witness_d))})
    return {"separation_proved":True,
       "bounded_signed_octagon_directions_ruled_out":18,
       "unbounded_reachable_witnesses":witness,
       "class":"CONJUNCTIVE_SIGNED_OCTAGON_FINITE_BOUND"}

def s_check(name,expression,expected):
    solver=z3.Solver()
    solver.set(timeout=2500)
    solver.add(expression)
    got=solver.check()
    result=str(got)
    script=solver.to_smt2()
    return {"name":name,"observed":result,"expected":expected,
        "pass":result==expected,"smt2_sha256":sha256(script.encode())}

def one_case(v,index):
    original=source_from_normal(v,index)
    original_hash=sha256(canonical_bytes(original))
    pub={"initial":original["initial"],"steps":original["steps"]}
    t0=perf_counter_ns()
    proposal=propose_from_public(**pub)
    # PRIVATE original's specification is first touched in the INDEPENDENT
    # original verifier, not in the proposer. It is never supplied as a hint.
    target=original["original_post_private"]
    x=z3.Ints("x y z")
    xp=z3.Ints("xp yp zp")
    initial=original["initial"]
    N=proposal["normal"]
    C=proposal["constant"]
    T=target["normal"]
    TC=target["constant"]
    def lin(vec,vars):
        return z3.Sum(*[int(a)*b for a,b in zip(vec,vars)])
    pre=z3.And(*[s==int(n) for s,n in zip(x,initial)])
    trans=z3.Or(*[z3.And(*[
       b==a+int(di) for a,b,di in zip(x,xp,delta)])
       for delta in original["steps"]])
    inv=lin(N,x)==int(C)
    invp=lin(N,xp)==int(C)
    post=z3.Or(lin(T,x)==int(TC),x[0]==int(initial[0]))
    postp=z3.Or(lin(T,xp)==int(TC),xp[0]==int(initial[0]))
    tests=[
        s_check("pre_nonvacuous",pre,"sat"),
        s_check("notpost_nonvacuous",z3.Not(post),"sat"),
        s_check("original_pre_implies_invariant",z3.And(pre,z3.Not(inv)),"unsat"),
        s_check("original_invariant_inductive",z3.And(inv,trans,z3.Not(invp)),"unsat"),
        s_check("original_invariant_implies_post",z3.And(inv,z3.Not(post)),"unsat"),
        s_check("NEGATIVE_original_post_alone_not_inductive",
            z3.And(post,trans,z3.Not(postp)),"sat"),
        s_check("NEGATIVE_shifted_invariant_fails_pre",
            z3.And(pre,z3.Not(lin(N,x)==int(C+1))),"sat"),
    ]
    mutated_delta=tuple(a+(1 if i==0 else 0)
                        for i,a in enumerate(original["steps"][0]))
    mutant_trans=z3.And(*[b==a+int(di)
                          for a,b,di in zip(x,xp,mutated_delta)])
    tests.append(s_check("NEGATIVE_one_mutated_branch_breaks_conservation",
        z3.And(inv,mutant_trans,z3.Not(invp)),"sat"))
    octproof=octagon_impossibility(original["steps"])
    assert all(t["pass"] for t in tests), (index,tests)
    assert octproof["separation_proved"] and len(octproof["unbounded_reachable_witnesses"])==18
    # The only shared exact kernel over Q is +/- the original normal.
    exact_expected=primitive(target["normal"])
    assert proposal["normal"]==exact_expected
    return {"case_index":index,"original_sha256":original_hash,
       "synthesized_relation":{"coefficients":N,"constant":C,
            "relation":"dot(coefficients,state)==constant"},
       "proposal_source":"ONLY_PRE_AND_TRANSITION_STEPS",
       "original_3vc":{
           t["name"]:t["observed"] for t in tests[2:5]},
       "checks":tests,
       "octagon_expressivity":octproof,
       "whole_case_ms":round((perf_counter_ns()-t0)/1e6,3),
       "training_calls":0}

def run():
    results=[one_case(v,i) for i,v in enumerate(NORMALS)]
    certified=sum(all(t["pass"] for t in r["checks"]) for r in results)
    separation=sum(r["octagon_expressivity"]["separation_proved"] for r in results)
    total_mutants=sum(all(t["pass"] and t["observed"]=="sat"
        for t in r["checks"] if t["name"].startswith("NEGATIVE"))
        for r in results)
    summary={"originals":12,"exact_original_3vc_pass":certified,
       "conjunctive_signed_octagon_expressivity_separation":separation,
       "all_three_negative_classes_rejected_per_case":total_mutants,
       "negative_checks_total":36,
       "actual_z3_original_vc_queries":36,
       "octagon_directions_checked":216,
       "frozen_first_gate_pass":certified==12 and separation==12 and total_mutants==12}
    return {"study":"Q3_S3_DENSE_3VAR_CLASSICAL_NULLSPACE_VS_SIGNED_OCTAGON_GAMMA2",
       "prereg_issue":251,"scientific_scope":"CONSTRUCTED_SOURCE_ONLY_CLASSICAL",
       "source_originals_are_independent_unseen":False,
       "operator_new_to_existing_octagon_gamma2":True,
       "operator_new_to_all_classical_algebra":False,
       "learned_new_operator":False,"neural_model_forwards":0,"gpu_calls":0,
       "strong_specialist_comparison":"NOT_EVALUATED",
       "frontier_comparison":"NOT_EVALUATED","complete_cost_10x":"UNPROVEN",
       "global_Q3":"OPEN","global_Q1_Q7":"OPEN","cases":results,"summary":summary}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    report=run()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3S3_FIRST_SUMMARY",json.dumps(report["summary"],sort_keys=True))
    print("Q3S3_FIRST_RESULTS",[(r["case_index"],
        r["synthesized_relation"]["coefficients"],
        r["original_3vc"]) for r in report["cases"]])
    print("Q3S3_FIRST_GATE",report["summary"]["frozen_first_gate_pass"])
