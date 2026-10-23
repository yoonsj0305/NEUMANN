"""Q3 next primitive-compositional experiment: induce named reusable macros by source
reward and train typed graph EDIT policy over recursive depth-three language.

Unlike last finite 2048 arithmetic-only grammar, the interpreter can introduce
nested nonlinear functions + naming/binding: agent builds lambda x: a*t(x)+b,
where t is GENERATED sequentially from x by three graph edits and includes
sin/cos/exp/log/sqrt/recip/powers/etc. Train ONLY from old frozen
original-author numeric x/y (original author truth absent). Transfer on
first untouched seventh32 author originals. Strong full-expanded-grammar
classical has exact same actions and oracle; learning can win cost not expressivity.

This is meaningful compositional abstraction, NOT spontaneous new atomic
semantics; previous fixed grammar does not contain trig/exp/log sqrt.
"""
import argparse,collections,hashlib,itertools,json,pathlib,time,warnings
import numpy as np
from sklearn.neural_network import MLPClassifier
import sympy as sp
from erbench_original_seventh import sha,save,allowed_formula,calc,SYM

X=sp.Symbol("x")
ACTION=("ID","ADD1","SUB1","ADD2","MUL2","MULX",
        "POW2","POW3","RECIP","SIN","COS","EXP","LOG","SQRT","ABS",
        "DIVX1","NEG")
PATHS=tuple(itertools.product(ACTION,repeat=3))
assert len(PATHS)==4913
INDEX={name:i for i,name in enumerate(ACTION)}
TRAIN_LOCK="c773efe1e31bee25fae5587f86c2d447b96888e3daf36ff73f071116ee4d5fd2"
SEED=19041
def apply(name,val,x):
    if name=="ID":return val
    if name=="ADD1":return val+1
    if name=="SUB1":return val-1
    if name=="ADD2":return val+2
    if name=="MUL2":return 2*val
    if name=="MULX":return x*val
    if name=="POW2":return val*val
    if name=="POW3":return val*val*val
    if name=="RECIP":return 1/val
    if name=="SIN":return np.sin(val)
    if name=="COS":return np.cos(val)
    if name=="EXP":return np.exp(val)
    if name=="LOG":return np.log(val)
    if name=="SQRT":return np.sqrt(val)
    if name=="ABS":return np.abs(val)
    if name=="DIVX1":return val/(x+1)
    if name=="NEG":return -val
    raise ValueError(name)
def symstep(name,e):
    if name=="ID":return e
    if name=="ADD1":return e+1
    if name=="SUB1":return e-1
    if name=="ADD2":return e+2
    if name=="MUL2":return 2*e
    if name=="MULX":return X*e
    if name=="POW2":return e**2
    if name=="POW3":return e**3
    if name=="RECIP":return 1/e
    if name=="SIN":return sp.sin(e)
    if name=="COS":return sp.cos(e)
    if name=="EXP":return sp.exp(e)
    if name=="LOG":return sp.log(e)
    if name=="SQRT":return sp.sqrt(e)
    if name=="ABS":return sp.Abs(e)
    if name=="DIVX1":return e/(X+1)
    if name=="NEG":return -e
    raise ValueError(name)
def numeric(row,path):
    x=np.asarray(row["x"],dtype=float)
    z=x.copy()
    with np.errstate(all="ignore"):
        for step in path:z=apply(step,z,x)
    z=np.broadcast_to(np.asarray(z,dtype=float),x.shape)
    if not np.all(np.isfinite(z)) or max(abs(z))>1e12 or np.std(z)<1e-11:
        return None
    return z
def graph_macro(path):
    expr=X
    for step in path:expr=symstep(step,expr)
    return expr
def reward(row,path):
    if "x" not in row:return None
    try:
        y=np.asarray(row["y"],float); z=numeric(row,path)
        if z is None or len(y)!=48:return None
        A=np.column_stack((z,np.ones(len(z))))
        coef=np.linalg.lstsq(A[:32],y[:32],rcond=1e-12)[0]
        if not np.all(np.isfinite(coef)) or max(abs(coef))>1e6:return None
        approx=A@coef
        if np.max(abs(approx-y)/(1+abs(y)))>1e-8:return None
        a=sp.Rational(float(coef[0])).limit_denominator(1000)
        b=sp.Rational(float(coef[1])).limit_denominator(1000)
        if a==0:return None
        expr=sp.cancel(a*graph_macro(path)+b) if all(v not in path for v in ("SIN","COS","EXP","LOG","SQRT","ABS")) else a*graph_macro(path)+b
        # Re-evaluate after exact-rational parameter restoration.
        f=sp.lambdify(X,expr,modules="numpy")
        with np.errstate(all="ignore"):
            mapped=np.broadcast_to(np.asarray(f(np.asarray(row["x"],float)),float),y.shape)
        if not np.all(np.isfinite(mapped)):return None
        err=float(np.max(abs(mapped-y)/(1+abs(y))))
        if not np.isfinite(err) or err>1e-8:return None
        return {"named_macro":"lambda x: "+str(expr),
                "generated_path":list(path),
                "recovered_coefficient_a":str(a),
                "recovered_coefficient_b":str(b),
                "numerical_source_residual":err,
                "new_recursive_graph_created":True}
    except Exception:return None
def shape(row):
    x=np.asarray(row["x"],float);y=np.asarray(row["y"],float)
    order=np.argsort(x);x=x[order];y=y[order]
    z=np.clip((y-np.median(y))/max(1e-10,float(np.std(y))),-15,15)
    q=np.interp(np.linspace(0,1,16),np.linspace(0,1,len(z)),z)
    scalars=[np.log1p(max(abs(x))),np.log1p(max(abs(y))),
             np.log1p(np.ptp(x)),np.log1p(np.ptp(y)),
             np.mean(np.diff(z)>0),np.mean(np.diff(z)<0),
             np.mean(y<0),np.mean(x<0)]
    val=np.r_[q,scalars]
    assert len(val)==24
    return np.clip(val,-30,30)
def action_vec(shape,idx,prefix):
    z=np.zeros(24+3+3*len(ACTION),float)
    z[:24]=shape;z[24+idx]=1
    for i,p in enumerate(prefix):z[27+i*len(ACTION)+INDEX[p]]=1
    return z
def train_proposer(train_json):
    raw=pathlib.Path(train_json).read_bytes()
    assert sha(raw)==TRAIN_LOCK,"PREVIOUS_EXTERNAL_TRAIN_SOURCE_CHANGED"
    rows=json.loads(raw)["train_source_only"]
    assert len(rows)==128
    rng=np.random.default_rng(SEED)
    positives=[];tasks=collections.Counter();attempts=0
    begin=time.process_time()
    for row in rows:
        if "x" not in row:continue
        inds=rng.choice(len(PATHS),size=256,replace=False)
        for k in inds:
            actions=PATHS[int(k)]
            attempts+=1
            r=reward(row,actions)
            if r is not None:
                positives.append({"source_id":row["id"],"path":list(actions),"features":shape(row).tolist(),
                                  "macro":r["named_macro"]})
                tasks[row["id"]]+=1
    search_cpu=time.process_time()-begin
    observed=collections.Counter(tuple(r["path"]) for r in positives)
    library=[{"typed_named_lambda":"library_auto_"+sha(str(path).encode())[:10],
               "edits":list(path),"training_task_count":len({p["source_id"] for p in positives if tuple(p["path"])==path}),
               "reward_occurrences":count} for path,count in observed.most_common(24)]
    # All training data are agent's own rewarded programs, NOT gold source AST.
    model=None;net_cpu=0;train_count=0;digest=None
    if len(positives)>=8 and len(tasks)>=3:
        xx=[];yy=[]
        for p in positives:
            for i,a in enumerate(p["path"]):
                xx.append(action_vec(np.asarray(p["features"]),i,p["path"][:i]))
                yy.append(a)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model=MLPClassifier(hidden_layer_sizes=(32,),random_state=SEED,max_iter=300,
                                alpha=0.01,learning_rate_init=0.008)
            start=time.process_time();model.fit(np.asarray(xx),np.asarray(yy))
            net_cpu=time.process_time()-start
        train_count=len(xx)
        digest=sha(json.dumps([v.tolist() for v in model.coefs_],sort_keys=True).encode())
    proof={"schema":"NEUMANN_Q3_LEARNED_RECURSIVE_TYPED_LIBRARY_v1",
       "original_training_numeric_source_SHA256":TRAIN_LOCK,
       "original_author_true_formulas_never_available":True,
       "training_source_examples":len(rows),"usable":sum("x" in row for row in rows),
       "exact_original_author_formula_labeled_examples":0,
       "self_rewarded_program_graph_proposals":attempts,
       "self_verified_numeric_programs":len(positives),
       "self_rewarded_training_tasks":len(tasks),
       "auto_constructed_named_reusable_lambda_library":library,
       "auto_discovered_distinct_recursive_edit_paths":len(observed),
       "prefix_edit_neural_training_examples":train_count,
       "actual_learned_model":model is not None,
       "learned_weights_sha256":digest,
       "training_source_reward_cpu_s":search_cpu,
       "neural_training_cpu_s":net_cpu,
       "human_provided_base_semantics":list(ACTION),
       "macro_full_expressions_not_passed_as_human_templates":True}
    return model,proof
def learned_paths(net,row,rng,limit):
    # 24 rewarded macro definitions from BEFORE sixth/seventh unseen test outcomes
    result=[];seen=set()
    def admit(p):
        t=tuple(p)
        if t not in seen and len(t)==3:
            seen.add(t);result.append(t)
    if net is None:return []
    f=shape(row)
    for _ in range(limit):
        trace=[]
        for i in range(3):
            probs=net.predict_proba([action_vec(f,i,trace)])[0]
            classes=list(net.classes_)
            w=np.asarray([float(probs[classes.index(c)]) if c in classes else 0. for c in ACTION])
            w=.85*w+.15/len(ACTION)
            w=w/w.sum()
            trace.append(str(rng.choice(ACTION,p=w)))
        admit(trace)
    return result
def infer(train_file,source_file,out):
    model,proof=train_proposer(train_file)
    original=json.loads(pathlib.Path(source_file).read_text())
    assert original["all_selected"]==32
    rows=original["source_numeric_without_equations"]
    rng=np.random.default_rng(12341)
    methods={}
    for name in ("D_learned_recursive_macro","C_uniform_same256","A_full_recursive_4913"):
        start=time.process_time();output=[];programs=0
        for row in rows:
            if "x" not in row:
                output.append({"id":row["id"],"programs_tested":0,"candidate_macros":[],"status":"UNKNOWN_SOURCE"})
                continue
            if name.startswith("D_"):
                cand=[]
                cand.extend(tuple(q["edits"]) for q in proof["auto_constructed_named_reusable_lambda_library"][:16])
                cand.extend(learned_paths(model,row,rng,240))
                paths=list(dict.fromkeys(cand))[:256]
            elif name.startswith("C_"):paths=[PATHS[int(i)] for i in rng.choice(len(PATHS),size=256,replace=False)]
            else:paths=PATHS
            vals=[];seen=set()
            for p in paths:
                r=reward(row,p)
                if r is not None and r["named_macro"] not in seen:
                    seen.add(r["named_macro"]);vals.append(r)
            programs+=len(paths)
            output.append({"id":row["id"],"programs_tested":len(paths),
                "candidate_macros":vals[:24],
                "status":"UNVERIFIED_SOURCE_MACRO" if vals else "UNKNOWN_NO_SOURCE_EXACT_MACRO"})
        methods[name]={"rows":output,"model_and_numeric_source_CPU_s":time.process_time()-start,
                       "total_AST_programs_tested":programs,
                       "source_cases_with_candidate":sum(bool(q["candidate_macros"]) for q in output)}
    record={"schema":"NEUMANN_Q3_FIRST_SEVENTH32_RECURSIVE_NAMED_LIBRARY_SEALED_v1",
       "training":proof,"eval_source_sha256":sha(pathlib.Path(source_file).read_bytes()),
       "recursive_macros_three_graph_edits_domain_fixed_by_humans":True,
       "same_program_grammar_rights_for_all_methods":True,
       "run_time_original_author_formula_absent":True,
       "all_methods":methods,"G1":"HOLD","global_Q3":"OPEN"}
    sign=save(out,record)
    print("Q3_SEVENTH32_LEARNED_INDUCED_RECURSIVE_MACRO_FIRST_PREDICTION",
          json.dumps({"sha256":sign,"trained":proof["actual_learned_model"],
             "training_rewarded":proof["self_verified_numeric_programs"],
             "distinct_learned_macros":proof["auto_discovered_distinct_recursive_edit_paths"],
             "train_source_tasks":proof["self_rewarded_training_tasks"],
             "scores_pregrade":{name:{"original_source_candidates":m["source_cases_with_candidate"],
                "cpu_s":m["model_and_numeric_source_CPU_s"],
                "calls":m["total_AST_programs_tested"]} for name,m in methods.items()}},sort_keys=True),flush=True)
def grade(truth_file,pred_file,out):
    truth=json.loads(pathlib.Path(truth_file).read_text())["private_true_equations"]
    pred=json.loads(pathlib.Path(pred_file).read_text())
    assert len(truth)==32
    totals={};rows={};actual={}
    for method,m in pred["all_methods"].items():
        idx={p["id"]:p for p in m["rows"]}
        counts=collections.Counter();results=[]
        for original in truth:
            target=idx[original["id"]];exact=[]
            try:
                node,var=allowed_formula(original["original_expression"])
                true=calc(node,{var:X},SYM)
                for trial in target["candidate_macros"]:
                    g=sp.sympify(trial["named_macro"].removeprefix("lambda x: "),locals={"x":X})
                    if sp.simplify(true-g)==0:
                        exact.append(trial)
            except Exception:pass
            counts["total"]+=1
            if exact:counts["original_exact"]+=1
            else:counts["not_proven"]+=1
            results.append({"id":original["id"],"collection":original["collection"],
              "task_ID":original["task_ID"],"full_original_formula_SHA256":sha(original["original_expression"].encode()),
              "original_truth":"FULL_AUTHOR_EXACT" if exact else "UNKNOWN",
              "new_named_macro_exact_matches":[q["named_macro"] for q in exact[:4]],
              "submitted_unverified_MACRO_count":len(target["candidate_macros"])})
        totals[method]=dict(counts);rows[method]=results
        actual[method]={r["id"] for r in results if r["original_truth"]=="FULL_AUTHOR_EXACT"}
    unique=actual["D_learned_recursive_macro"]-actual["A_full_recursive_4913"]
    printout={"schema":"NEUMANN_Q3_FIRST_SEVENTH32_INDEPENDENT_AUTHOR_FULL_FUNCTION_GRADE.v1",
      "frozen_prediction_sha256":sha(pathlib.Path(pred_file).read_bytes()),
      "private_original_author_truth_SHA256":sha(pathlib.Path(truth_file).read_bytes()),
      "all_method_exact_originals":totals,"per_original_receipts":rows,
      "neural_only_original_wins_beyond_complete_same_grammar":sorted(unique),
      "neural_outside_human_primitive_semantics":"NOT_PROVED",
      "new_recursive_reusable_named_macro_compiled":"SCOPED",
      "different_author_family_transfer":"NOT_PROVED_SAME_PUBLIC_BENCHMARK",
      "no_new_blind_after_grade_tuning":True,"G1":"HOLD","global_Q3":"OPEN",
      "full_lifecycle_10x":"NOT_PROVED"}
    digest=save(out,printout)
    print("Q3_SEVENTH32_EXTERNAL_ORIGINAL_COMPOSED_MACRO_INDEPENDENT_FULL_GRADE",
        json.dumps({"sha256":digest,"scores":totals,
            "new_originals_only_D":len(unique)},sort_keys=True),flush=True)
    assert all(x["total"]==32 for x in totals.values())
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("infer","grade"),required=True)
    for k in ("train","source","truth","pred","out"):parser.add_argument("--"+k)
    a=parser.parse_args()
    if a.mode=="infer":infer(a.train,a.source,a.pred)
    else:grade(a.truth,a.pred,a.out)
