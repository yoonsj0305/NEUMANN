"""Q3 posthoc: exact minimal-cardinality proof within 8 signed original predicates.

Requires sympy 1.14. Source is fixed to LoopInvGen poly2.sl, NOT a new
blind experiment, transferable model, frontier claim, or neural Q3 proof.
Rational LP feasibility is equivalent to integer feasibility here because
all candidate inequalities are homogeneous and bad Post conditions have
unit lower/upper violation thresholds (rational witnesses scale).
"""
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path
import sympy as sp
from sympy.solvers.simplex import InfeasibleLPError, lpmin

SOURCE_BLOB="17448225fffad0cef48634b9d68f4f9193d616d8"
SOURCE_SHA256="2a8a874b4f0861cb8219059dfc9572c6f02a827e80d0c0cc583c7f13c251eb7d"

def pinned(raw):
    blob=hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()
    assert blob==SOURCE_BLOB, "WRONG_SOURCE_GIT_BLOB"
    assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA256,"WRONG_SOURCE_SHA256"

def all_source_candidates():
    whole=[]; pretight=[]; inductive=[]
    for w in itertools.product((-1,0,1),repeat=5):
        if not any(w):continue
        whole.append(w)
        a,b,d,e,f=w
        # Source Pre c=0,x=x0,y=y0; x0,y0 range over all integers.
        if b+e or d+f:continue
        pretight.append(w)
        # Source Trans: c'=c+1 and either x'=x-1-t or y'=y+1+t,
        # t>=0. Both branches are enabled at a Pre boundary state.
        # Exact necessary/sufficient individual predicate inductiveness.
        if b<=0 and d>=0 and a-b>=0 and a+d>=0:
            inductive.append(w)
    assert (len(whole),len(pretight),len(inductive))==(242,26,8)
    return whole,pretight,inductive

C,U,V=sp.symbols("c u v",real=True)
def feasible(constraints):
    try:
        lpmin(0,constraints)
        return True
    except InfeasibleLPError:
        return False

def full_original_post_proved(chosen,atoms):
    # u=x-x0,v=y-y0, source x-y=(x0-y0)+u-v.
    constraints=[]
    for i in chosen:
        a,b,d,_,_=atoms[i]
        constraints.append(a*C+b*U+d*V>=0)
    # Exhaustive ORIGINAL Post violation cases, no source goal weakening:
    positive=feasible(constraints+[C>=1,C+U-V>=1])
    negative=feasible(constraints+[C<=-1,U-V>=1])
    return not positive and not negative,(positive,negative)

def run(path):
    began=time.perf_counter_ns()
    raw=Path(path).read_bytes()
    pinned(raw)
    whole,pre,atoms=all_source_candidates()
    checked=0;minimal=[];singleton_results={}
    for count in (0,1,2):
        found=[]
        for chosen in itertools.combinations(range(len(atoms)),count):
            valid,bad=full_original_post_proved(chosen,atoms)
            checked+=1
            if count==1:
                singleton_results[str(chosen[0])]={
                    "safe":valid,"bad_positive":bad[0],"bad_negative":bad[1]}
            if valid:found.append(chosen)
        if found:
            minimal=found
            break
    assert checked==37 and set(minimal)=={(0,5),(0,6)}
    # All possible active integer transition magnitudes t>=0 preserve
    # each chosen predicate because coefficient slopes and intercepts >=0.
    for chosen in minimal:
        for i in chosen:
            a,b,d,_,_=atoms[i]
            assert -b>=0 and d>=0 and a-b>=0 and a+d>=0
    # Adversarial mutation c'=c+2, x'=x-1 breaks essential predicate 0.
    a,b,d,_,_=atoms[0]
    assert 2*a-b<0
    try:
        pinned(raw+b"\n")
    except AssertionError:
        forged_rejected=True
    else:
        raise AssertionError("FORGED_SOURCE_ACCEPTED")
    return {
        "result":"PASS_FIXED_GRAMMAR_MINIMUM_WITH_EXACT_RATIONAL_CERTIFICATE",
        "previously_opened_posthoc":True,
        "source_sha256":SOURCE_SHA256,"source_git_blob_sha1":SOURCE_BLOB,
        "searched_signed_full5":len(whole),
        "source_pre_tight":len(pre),
        "individual_inductive":len(atoms),
        "individual_predicates":[list(w) for w in atoms],
        "goal_subset_checks":checked,
        "minimum_predicates_from_this_eight_atom_set":len(minimal[0]),
        "all_minimum_pairs":[list(x) for x in minimal],
        "all_minimum_coefficients":[[list(atoms[i]) for i in xs] for xs in minimal],
        "all_singleton_counterexample_statuses":singleton_results,
        "source_mutation_rejected":forged_rejected,
        "transition_mutation_rejected":True,
        "original_source_reduction_proof":
        "Pre exact, three Trans branch deltas exact, bad Post reduced into two mutually complete cases; rational witnesses scale to integers",
        "Z3_cvc5_recheck_for_this_minimized_pair":False,
        "learned_neural_proposer":False,"new_blind_origins":0,
        "global_q1_q7":"OPEN",
        "local_wall_ms":round((time.perf_counter_ns()-began)/1e6,3),
    }

if __name__=="__main__":
    print(json.dumps(run(sys.argv[1]),indent=2,sort_keys=True))
