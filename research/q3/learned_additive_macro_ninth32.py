"""Q3: induction of new executable reusable ADDITIVE macro definitions.

Not a library of enumerated complete target formulas: each emitted target AST is
f(x)=a * u(x) + b * v(x) + c where source numerical rewards decide which TWO
typed base semantic programs u,v and infer exact-rational coefficients. Learned
family policy is trained without original author formulas, on different public
author source x-y. A full-source mathematical grade happens ONLY after SHA seal.

Hypothesis language has human given unary primitives, bounded depth/two summands,
so no claim of novel atomic math operator or complete unbounded language.
"""
import argparse,collections,hashlib,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from sklearn.neural_network import MLPClassifier
from erbench_original_ninth import sha,save,allowed_formula,calc,SYM

X=sp.Symbol("x")
SCALES=(sp.Rational(1),sp.Rational(-1),sp.Rational(2),sp.Rational(1,2))
SHIFTS=(sp.Rational(-2),sp.Rational(-1),sp.Rational(0),sp.Rational(1),sp.Rational(2))
PRIMITIVES=("ID","SQUARE","CUBE","RECIP","SIN","COS","EXP","LOG","SQRT","ABS","TANH","ATAN","SINH","COSH")
def symop(k,v):
    f={"ID":lambda z:z,"SQUARE":lambda z:z*z,"CUBE":lambda z:z*z*z,
       "RECIP":lambda z:1/z,"SIN":sp.sin,"COS":sp.cos,"EXP":sp.exp,
       "LOG":sp.log,"SQRT":sp.sqrt,"ABS":sp.Abs,"TANH":sp.tanh,
       "ATAN":sp.atan,"SINH":sp.sinh,"COSH":sp.cosh}
    return f[k](v)
def numop(k,v):
    with np.errstate(all="ignore"):
        f={"ID":lambda z:z,"SQUARE":lambda z:z*z,"CUBE":lambda z:z*z*z,
           "RECIP":lambda z:1/z,"SIN":np.sin,"COS":np.cos,"EXP":np.exp,
           "LOG":np.log,"SQRT":np.sqrt,"ABS":np.abs,"TANH":np.tanh,
           "ATAN":np.arctan,"SINH":np.sinh,"COSH":np.cosh}
        return f[k](v)
def make_basis():
    found={};all_=[]
    for op in PRIMITIVES:
        for a in SCALES:
            for b in SHIFTS:
                p=symop(op,a*X+b)
                key=str(p)
                if key in found:continue
                found[key]=1
                all_.append({"formula":key,"sym":p,"op":op,"scale":float(a),"shift":float(b)})
    assert len(all_)>=130
    return all_
BASIS=make_basis()
print("NINTH_COMPOSITIONAL_ATOMIC_BASIS_NUM",len(BASIS),flush=True)

def original_shape(xx,yy):
    x=np.asarray(xx,float);y=np.asarray(yy,float)
    if x.shape!=(48,) or y.shape!=(48,) or not(np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    order=np.argsort(x);x=x[order];y=y[order]
    yy=(y-np.median(y))/max(np.std(y),1e-12)
    yprofile=np.interp(np.linspace(0,1,16),np.linspace(0,1,48),np.clip(yy,-10,10))
    stats=np.r_[np.log1p([max(abs(x)),max(abs(y)),np.ptp(x),np.ptp(y)]),
                np.mean(np.diff(yy)>0),np.mean(np.diff(yy)<0),
                np.mean(y<0),np.mean(x<0)]
    out=np.clip(np.r_[yprofile,stats],-30,30)
    return out if np.all(np.isfinite(out)) else None

def numeric_matrix(row):
    if "x" not in row:return None
    xs=np.array(row["x"],float);ys=np.array(row["y"],float)
    if original_shape(xs,ys) is None:return None
    cols=[];good=[];centers=[]
    for i,b in enumerate(BASIS):
        try:
            with np.errstate(all="ignore"):
                z=np.asarray(numop(b["op"],b["scale"]*xs+b["shift"]),float)
            if z.shape!=(48,) or not np.all(np.isfinite(z)) or np.max(abs(z))>1e12:
                continue
            avg=float(np.mean(z[:32]));z=z-avg
            norm=np.linalg.norm(z[:32])
            if norm<1e-11:continue
            cols.append(z/norm)
            good.append(i)
            centers.append(avg)
        except Exception:continue
    if not cols:return None
    mat=np.asarray(cols).T
    center_y=ys[:32]-np.mean(ys[:32])
    corr=abs(mat[:32,:].T@center_y)
    return xs,ys,mat,good,centers,corr

def fixed_rational(z):
    return sp.Rational(float(z)).limit_denominator(1000)

def source_program(row,subset,max_candidates=4):
    """CREATE new named two-branch macro AST from source selected basis nodes.

    Candidate regression on first32, numerical validation across all48.
    No target true author formula touched.
    """
    prepared=numeric_matrix(row)
    if prepared is None:return [],0
    xs,ys,mat,good,centers,corr=prepared
    selected=[j for j,b in enumerate(good) if b in set(subset)]
    if not selected:return [],0
    chosen=np.array(selected,int)
    # Source-driven orthogonal matching pursuit: try up to top12 first
    # and 14 alternative second terms to construct sum-of-two macro.
    starters=sorted(chosen,key=lambda j:-corr[j])[:12]
    attempts=0;proposals=[];seen=set()
    def trial(indices):
        nonlocal attempts
        attempts+=1
        A=np.column_stack([mat[:,q] for q in indices]+[np.ones(48)])
        try:
            coef=np.linalg.lstsq(A[:32,:],ys[:32],rcond=1e-12)[0]
            if not np.all(np.isfinite(coef)) or np.max(abs(coef))>1e9:return
            pred=A@coef
            residual=np.max(abs(pred-ys)/(1+abs(ys)))
            if residual>2e-7 or not np.isfinite(residual):return
            term=[]
            for i,j in enumerate(indices):
                # mat normalized (raw nonlinear feature minus training mean)
                rawscale=coef[i]/np.linalg.norm(
                    numop(BASIS[good[j]]["op"],BASIS[good[j]]["scale"]*xs[:32]+
                          BASIS[good[j]]["shift"])-
                    centers[j])
                term.append(rawscale)
            intercept=coef[-1]-sum(term[i]*centers[j] for i,j in enumerate(indices))
            coeffs=[fixed_rational(c) for c in term]+[fixed_rational(intercept)]
            expr=sp.Add(*(coeffs[i]*BASIS[good[j]]["sym"] for i,j in enumerate(indices)),
                        coeffs[-1],evaluate=True)
            # Re-check AFTER exact-rationalization. Reject false source fit.
            fn=sp.lambdify(X,expr,modules="numpy")
            with np.errstate(all="ignore"):
                numeric=np.broadcast_to(np.asarray(fn(xs),float),ys.shape)
            if not np.all(np.isfinite(numeric)):return
            fixed_err=float(np.max(abs(numeric-ys)/(1+abs(ys))))
            if fixed_err>1e-8:return
            key=str(expr)
            if key in seen:return
            seen.add(key)
            proposals.append({"named_lambda":"lambda x: "+key,
                "macro_nodes":[BASIS[good[j]]["formula"] for j in indices],
                "new_macro_definition_with_two_terms":len(indices)==2,
                "contains_nonlinear_primitive":any(BASIS[good[j]]["op"]
                  not in ("ID","SQUARE","CUBE","RECIP") for j in indices),
                "numeric_source_error":fixed_err})
        except Exception:return
    for j in starters:
        trial([int(j)])
    if len(proposals)>=max_candidates:return proposals[:max_candidates],attempts
    for a in starters:
        ycenter=ys[:32]-np.mean(ys[:32])
        residual=ycenter-mat[:32,a]*(mat[:32,a]@ycenter)
        nextcorr=abs(mat[:32,chosen].T@residual)
        ranked=chosen[np.argsort(-nextcorr)[:14]]
        for b in ranked:
            if int(b)==int(a):continue
            trial([int(a),int(b)])
            if len(proposals)>=max_candidates:return proposals[:max_candidates],attempts
    return proposals,attempts

def train_policy(trainfile):
    train=json.loads(pathlib.Path(trainfile).read_text())["train_source_only"]
    assert len(train)==128
    xs=[];targets=[];positive=[];seen_tasks=0;work=0
    t0=time.process_time()
    for row in train:
        data=numeric_matrix(row)
        if data is None:continue
        shape=original_shape(row["x"],row["y"])
        orig_x,orig_y,mat,good,centers,corr=data
        bestj=good[int(np.argmax(corr))]
        # LABEL DERIVED ONLY FROM NUMERIC SEMANTIC REWARD, not author gold AST.
        xs.append(shape);targets.append(BASIS[bestj]["op"])
        # First search for exact source task evidence and store discovered
        # TWO-BRANCH macro definitions; do not predeclare the full expressions.
        proposals,steps=source_program(row,range(len(BASIS)),max_candidates=5)
        work+=steps
        if proposals:
            seen_tasks+=1
            for p in proposals:
                positive.append({"source_task_id":row["id"],
                    "lambda":p["named_lambda"],"macro_nodes":p["macro_nodes"]})
    rewards_cpu=time.process_time()-t0
    model=None;fit_cpu=0;weights=None
    if len(set(targets))>=2 and len(xs)>=30:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model=MLPClassifier(hidden_layer_sizes=(32,),random_state=226,
                learning_rate_init=.003,max_iter=240,alpha=.02)
            t1=time.process_time()
            model.fit(np.asarray(xs),np.asarray(targets))
            fit_cpu=time.process_time()-t1
        weights=sha(json.dumps([a.tolist() for a in model.coefs_]).encode())
    output={"numeric_train_sha256":sha(pathlib.Path(trainfile).read_bytes()),
        "different_author_source_train_rows":128,
        "numeric_task_specific_reward_action_labels":len(xs),
        "own_source_rewarded_named_macros":len(positive),
        "source_tasks_with_valid_macro":seen_tasks,
        "induced_macro_samples":positive[:50],
        "induced_macro_sha256":sha(json.dumps(positive,sort_keys=True).encode()),
        "training_semantic_verifier_calls":work,
        "train_reward_verifier_cpu_s":rewards_cpu,
        "neural_fit_cpu_s":fit_cpu,
        "model_weights_sha256":weights,
        "fixed_existing_base_primitive_semantics_human_supplied":True,
        "no_gold_original_training_expressions_given":True}
    return model,output,positive

def selected_basis(method,row,model,rng):
    if method=="D_learned_macro_top80":
        if model is None:return rng.choice(len(BASIS),80,replace=False).tolist()
        shape=original_shape(row["x"],row["y"])
        probabilities=dict(zip(model.classes_,model.predict_proba([shape])[0]))
        scores=np.array([probabilities.get(b["op"],0) for b in BASIS])
        # learned semantic prior + guarded exploration; bounded 80 basis
        chosen=list(np.argsort(-scores)[:60])
        remain=[j for j in range(len(BASIS)) if j not in chosen]
        chosen+=list(rng.choice(remain,size=20,replace=False))
        return [int(q) for q in chosen]
    if method=="C_random_top80":return [int(q) for q in rng.choice(len(BASIS),80,replace=False)]
    if method=="C_complexity_top80":
        return sorted(range(len(BASIS)),key=lambda j:(
            sp.count_ops(BASIS[j]["sym"]),len(BASIS[j]["formula"])))[:80]
    if method=="C_source_correlation_top80":
        data=numeric_matrix(row)
        if data is None:return []
        _,_,mat,good,_,corr=data
        return [good[int(k)] for k in np.argsort(-corr)[:80]]
    return list(range(len(BASIS)))

def infer(trainfile,sourcefile,out):
    model,learning,macros=train_policy(trainfile)
    source=json.loads(pathlib.Path(sourcefile).read_text())["source_numeric_without_equations"]
    assert len(source)==32
    rng=np.random.default_rng(987741)
    arms={}
    for method in ("D_learned_macro_top80","C_random_top80","C_complexity_top80",
                   "C_source_correlation_top80","A_all_basis_greedy_OMP"):
        started=time.process_time()
        rows=[];total=collections.Counter()
        for row in source:
            subset=selected_basis(method,row,model,rng)
            found,trials=source_program(row,subset,max_candidates=6)
            rows.append({"id":row["id"],"exact_numeric_macro_candidates":found,
                         "semantic_pair_fit_trials":trials,"basis_size":len(subset)})
            total["numeric_source_candidate_programs"]+=len(found)
            total["source_rows_with_programs"]+=int(bool(found))
            total["semantic_fit_trials"]+=trials
        arms[method]={"predictions":rows,"cpu_s":time.process_time()-started,
                      "source_counts":dict(total)}
    data={"schema":"NEUMANN_Q3_NINTH32_NEW_INDUCED_ADDITIVE_MACRO.v1",
         "original_source_only_SHA256":sha(pathlib.Path(sourcefile).read_bytes()),
         "training":learning,"primitive_expression_dictionary_size":len(BASIS),
         "dynamic_macro_construction":"lambda x: rational*a*phi(x)+rational*b*psi(x)+rational*c",
         "source_valued_reward_only":True,"author_true_formula_available_in_inference":False,
         "A_full_basis_is_strong_greedy_OMP_NOT_exhaustive_all_2term_programs":True,
         "Arms":arms,"global_Q3":"OPEN","G1":"HOLD","full_10x":"NOT_PROVED"}
    digest=save(out,data)
    print("Q3_NINTH32_SOURCE_ONLY_INDUCED_ADDITIVE_MACROS_SEALED",json.dumps({
       "sha256":digest,"basis":len(BASIS),
       "training_positive_macros":learning["own_source_rewarded_named_macros"],
       "train_cpu_s":learning["train_reward_verifier_cpu_s"]+learning["neural_fit_cpu_s"],
       "arms":{k:{"counts":v["source_counts"],"cpu_s":v["cpu_s"]} for k,v in arms.items()}},
       sort_keys=True),flush=True)

def grade(predfile,truthfile,out):
    predictions=json.loads(pathlib.Path(predfile).read_text())
    true=json.loads(pathlib.Path(truthfile).read_text())["private_true_equations"]
    assert len(true)==32
    scores={};cases={}
    for method,arm in predictions["Arms"].items():
        table={r["id"]:r for r in arm["predictions"]}
        tally=collections.Counter();rows=[]
        for record in true:
            ident=record["id"];tally["total"]+=1
            exact=[]
            try:
                tree,var=allowed_formula(record["original_expression"])
                author=calc(tree,{var:X},SYM)
                for p in table[ident]["exact_numeric_macro_candidates"]:
                    formula=p["named_lambda"].replace("lambda x: ","")
                    candidate=sp.sympify(formula,locals={"x":X})
                    if sp.simplify(author-candidate)==0:exact.append(p)
            except Exception:pass
            tally["original_exact"]+=int(bool(exact))
            tally["original_UNKNOWN"]+=int(not exact)
            if any(p["contains_nonlinear_primitive"] for p in exact):
                tally["original_exact_with_nonlinear_primitive"]+=1
            if any(p["new_macro_definition_with_two_terms"] for p in exact):
                tally["original_exact_two_term_macro"]+=1
            rows.append({"id":ident,"task_ID":record["task_ID"],
                 "original_formula_SHA256":sha(record["original_expression"].encode()),
                 "status":"FULL_AUTHOR_ORIGINAL_EXACT" if exact else "UNKNOWN",
                 "certified_named_macros":exact[:5],
                 "source_proposals":len(table[ident]["exact_numeric_macro_candidates"])})
        scores[method]=dict(tally);cases[method]=rows
    solved={k:{r["id"] for r in rows if r["status"]=="FULL_AUTHOR_ORIGINAL_EXACT"} for k,rows in cases.items()}
    learner=solved["D_learned_macro_top80"]
    report={"schema":"NEUMANN_Q3_FIRST_NINTH32_AUTHOR_ORIGINAL_EXACT_ADDITIVE_MACROS.v1",
       "frozen_source_predictions_sha256":sha(pathlib.Path(predfile).read_bytes()),
       "independent_original_author_truth_sha256":sha(pathlib.Path(truthfile).read_bytes()),
       "score":scores,"cases":cases,
       "learner_only_vs_each_classical":{k:sorted(learner-v) for k,v in solved.items() if k!="D_learned_macro_top80"},
       "learner_only_vs_union_all_classical":sorted(learner-set.union(*(v for k,v in solved.items() if k!="D_learned_macro_top80"))),
       "independent_native_original_expression_grader":True,
       "full_spec_baseline_PySR_Operon":"NOT_RUN",
       "G1":"HOLD","Q3_GLOBAL":"OPEN","ALL_IN_10X":"NOT_PROVED"}
    digest=save(out,report)
    print("Q3_NINTH32_FIRST_EXACT_AUTHOR_ORIGINAL_ADDITIVE_MACRO_GRADE",json.dumps({
       "sha256":digest,"scores":scores,
       "learner_only_vs_all_classical":len(report["learner_only_vs_union_all_classical"])},sort_keys=True),flush=True)
    assert all(v["total"]==32 for v in scores.values())
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--mode",required=True,choices=("infer","grade"))
    for k in ("train","source","truth","pred","out"):a.add_argument("--"+k)
    o=a.parse_args()
    if o.mode=="infer":infer(o.train,o.source,o.pred)
    else:grade(o.pred,o.truth,o.out)
