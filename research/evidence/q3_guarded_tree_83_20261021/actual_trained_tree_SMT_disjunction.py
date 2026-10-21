"""POSTHOC original 83.c.sl: FIT a real DecisionTree from native Pre/Trans
positive states and native NotPost negative states. Distill Boolean DNF,
calibrate only numeric thresholds with Z3, certify full original with Z3+cvc5.
Compare exhaustive no-learning two-literal OR on same data and solver rights.
Prior human witness exists but is NOT a model target or input.
"""
import argparse,hashlib,itertools,json,math,time
from pathlib import Path
import numpy as np
import z3
from sklearn.tree import DecisionTreeClassifier
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare,verified_3vc
SOURCE="lib/Inv_Track/xujie_code2inv/83.c.sl"
SHA="364ed512df08efcdd3877c56f7743766d325ef49"
GRID=(-6000,-5002,-5001,-5000,-100,-5,-1,0,1,2,5,100,4999,5000,5001,6000)
def getmodel(s,variables):
    return tuple(s.model().eval(x,model_completion=True).as_long() for x in variables)
def sample(formula,symbols,features):
    allrows=set()
    for ix in (-1,0,1):
        for v in ([None] if ix<0 else GRID):
            s=z3.Solver();s.set(timeout=1000);s.add(formula)
            if ix>=0:s.add(symbols[ix]==v)
            for _ in range(3):
                if s.check()!=z3.sat:break
                row=getmodel(s,features);allrows.add(row)
                s.add(z3.Or(*[x!=z for x,z in zip(features,row)]))
    return allrows
def dataset(src,native):
    v=src["now"][:2];n=src["next"][:2]
    pos=sample(native["pre"],v,v)|sample(z3.And(native["pre"],native["trans"]),n,n)
    for y in GRID:
        s=z3.Solver();s.set(timeout=800)
        s.add(native["pre"],native["trans"],v[1]==y)
        if s.check()==z3.sat:pos.add(getmodel(s,n))
    neg=sample(z3.Not(native["post"]),v,v)
    if pos&neg:raise RuntimeError("REAL_POSITIVE_NEGATIVE_DATA_CONFLICT")
    return sorted(pos),sorted(neg)
def terms(tree,values):
    q=tree.tree_;positive=list(tree.classes_).index(1);leaves=[]
    def rec(node,conds):
        left=q.children_left[node]
        if left<0:
            if q.value[node][0,positive]>=max(q.value[node][0]):
                leaves.append(list(conds))
            return
        f=int(q.feature[node]);k=int(values[node])
        rec(left,conds+[(f,"le",k)])
        rec(q.children_right[node],conds+[(f,"gt",k)])
    rec(0,[])
    return leaves
def formula(clauses,state):
    return z3.Or(*[z3.And(*[(state[i]<=c if sign=="le" else state[i]>c)
                             for i,sign,c in term]) for term in clauses])
def fast_prove(src,native,inv):
    nxt=z3.substitute(inv,*list(zip(src["now"],src["next"])))
    for clause in (z3.And(native["pre"],z3.Not(inv)),
                   z3.And(inv,native["trans"],z3.Not(nxt)),
                   z3.And(inv,z3.Not(native["post"]))):
        s=z3.Solver();s.set(timeout=220);s.add(clause)
        if s.check()!=z3.unsat:return False
    return True
def grid_of(pos,neg,i,guess=0):
    vals=sorted(set(z[i] for z in pos+neg))
    choice={-1,0,1,int(guess),min(vals),max(vals),vals[len(vals)//2]}
    choice.update(v for v in vals if abs(v)<=6)
    return sorted(choice,key=lambda z:(abs(z-guess),abs(z),z))[:17]
def find_tree(src,native,model,pos,neg):
    q=model.tree_;nodes=[i for i in range(q.node_count) if q.children_left[i]>=0]
    candidates=[grid_of(pos,neg,int(q.feature[i]),math.floor(q.threshold[i])) for i in nodes]
    examined=0
    for options in itertools.product(*candidates):
        if examined>=1400:break
        examined+=1
        candidate=formula(terms(model,dict(zip(nodes,options))),src["now"][:2])
        if fast_prove(src,native,candidate):
            return candidate,{"trials":examined,"nodes":nodes,"adjusted_thresholds":options}
    return None,{"trials":examined,"nodes":nodes}
def find_no_fit(src,native,pos,neg):
    state=src["now"][:2];grids=[grid_of(pos,neg,i,0) for i in range(2)]
    examined=0
    for i,j in [(0,1),(1,0)]:
        for a,b in itertools.product(("le","gt"),repeat=2):
            for v,w in itertools.product(grids[i],grids[j]):
                inv=formula([[(i,a,v)],[(j,b,w)]],state)
                examined+=1
                if fast_prove(src,native,inv):
                    return inv,{"trials":examined}
    return None,{"trials":examined}
def main():
    p=argparse.ArgumentParser()
    for name in ("root","freeze","out"):p.add_argument("--"+name,required=True)
    a=p.parse_args()
    manifest=json.loads(Path(a.freeze).read_text())
    it=next(x for x in manifest["cases"] if x["path"]==SOURCE)
    assert it["git_blob"]==SHA
    raw,src,native,parity=prepare(Path(a.root),it)
    pos,neg=dataset(src,native)
    if len(pos)<8 or len(neg)<4:raise RuntimeError("INSUFFICIENT_SOURCE_GENERATED_TRAINING")
    X=np.asarray(pos+neg,dtype=np.int64)
    y=np.asarray([1]*len(pos)+[0]*len(neg))
    st=time.perf_counter_ns()
    clf=DecisionTreeClassifier(max_depth=2,max_leaf_nodes=3,min_samples_leaf=2,
                               class_weight="balanced",random_state=20261021).fit(X,y)
    elapsed_fit=(time.perf_counter_ns()-st)/1e6
    st=time.perf_counter_ns();candidate,search=find_tree(src,native,clf,pos,neg)
    search["wall_ms"]=(time.perf_counter_ns()-st)/1e6
    st=time.perf_counter_ns();baseline,control=find_no_fit(src,native,pos,neg)
    control["wall_ms"]=(time.perf_counter_ns()-st)/1e6
    def independent(expr):
        if expr is None:return {"proven":False}
        ok,vc=verified_3vc(src,native,expr)
        return {"proven":bool(ok),"source_AST":expr.sexpr(),"dual_Z3_cvc5_original_3VC":vc}
    t=independent(candidate);b=independent(baseline)
    result={"schema":"neumann.q3.posthoc_native_supervised_tree_DNF_induction.v1",
            "original_SHA":SHA,"native_original_source_parity":parity,
            "actual_native_positive_count":len(pos),"actual_native_negative_count":len(neg),
            "model":"sklearn DecisionTreeClassifier(depth2,max_leaves3)",
            "actual_model_training_wall_ms":elapsed_fit,
            "actual_tree_depth":clf.get_depth(),"actual_tree_leaves":clf.get_n_leaves(),
            "fitted_tree_original_DNF_before_calibration":
                terms(clf,{n:math.floor(clf.tree_.threshold[n]) for n in range(clf.tree_.node_count)
                           if clf.tree_.children_left[n]>=0}),
            "trained_model_source_proof_search":search,
            "trained_model_complete_original_dual_proof":t,
            "strong_same_source_no_fit_OR_search":control,
            "strong_same_source_no_fit_OR_dual_proof":b,
            "posthoc_human_answer_previously_known_but_NOT_fit_target":True,
            "learned_topology_calibrated_by_symbolic_verifier_not_solely_model":True,
            "originals_first_opened_in_PRIOR_PR408":True,
            "claim_global_10x_or_unique_discovery":False,
            "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"}
    Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2,default=lambda x: int(x) if isinstance(x,np.integer) else float(x) if isinstance(x,np.floating) else str(x))+"\n")
    print("TRAINED_ORIGINAL_BOOLEAN_DNF",t["proven"],"EXACT_NOFIT_OR",b["proven"],flush=True)
    print("LEARNED_TOPOLOGY",result["fitted_tree_original_DNF_before_calibration"],flush=True)
    print("SOURCE_SAMPLE_COUNTS",len(pos),len(neg),flush=True)
if __name__=="__main__":main()
