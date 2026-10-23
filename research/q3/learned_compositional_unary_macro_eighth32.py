"""Q3: learn and transfer NAMED NONLINEAR COMPOSITION macros on real author formulas.

- Eighth32 SHA-ranked untouched public original ERBench source equations; gold expressions
  PHYSICALLY never available to numeric source learner or candidate program generator.
- Own-reward training uses 128 prior author tasks with ONLY numeric input/output.
- Typed graph = affine rational leaf -> inner unary -> outer unary. Every complete
  MACRO's syntax is BUILT by the sequentially predicted edit action, never supplied
  as a target formula label.
- Strong exact same-grammar COMPLETE 3920 source syntaxes and budget matched random
  and complexity-ranked nonlearning controls.
- Claims limited: finite HUMAN unary primitives, scale/shift alphabet and output
  linear coefficients. A complete same-grammar classical source search cannot be
  beaten on EXPRESSIVITY; only measured bounded evaluation work/time could improve.
"""
import argparse,collections,hashlib,itertools,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from sklearn.neural_network import MLPClassifier
from erbench_original_eighth import sha,save,allowed_formula,calc,SYM

X=sp.Symbol("x")
BASE=("ID","SIN","COS","EXP","LOG","SQRT","RECIP","SQUARE","CUBE","ABS","TAN","SINH","COSH","TANH")
SCALE={"S1":sp.Rational(1),"SN1":sp.Rational(-1),"S2":sp.Rational(2),"SHALF":sp.Rational(1,2)}
SHIFT={"Z0":sp.Integer(0),"Z1":sp.Integer(1),"ZN1":sp.Integer(-1),"Z2":sp.Integer(2),"ZN2":sp.Integer(-2)}
CHOOSE=(tuple(SCALE),tuple(SHIFT),BASE,BASE)
TOKENS=tuple(sorted(set(sum([list(c) for c in CHOOSE],[]))))
TOKIDX={k:i for i,k in enumerate(TOKENS)}
ACTIONS=tuple(itertools.product(*CHOOSE))
assert len(ACTIONS)==3920

def f_num(kind,x):
    with np.errstate(all="ignore"):
        if kind=="ID":return x
        if kind=="SIN":return np.sin(x)
        if kind=="COS":return np.cos(x)
        if kind=="EXP":return np.exp(np.clip(x,-500,500))
        if kind=="LOG":return np.log(x)
        if kind=="SQRT":return np.sqrt(x)
        if kind=="RECIP":return 1/x
        if kind=="SQUARE":return x*x
        if kind=="CUBE":return x*x*x
        if kind=="ABS":return np.abs(x)
        if kind=="TAN":return np.tan(x)
        if kind=="SINH":return np.sinh(x)
        if kind=="COSH":return np.cosh(x)
        if kind=="TANH":return np.tanh(x)
    raise ValueError(kind)

def f_sym(kind,x):
    mapping={"ID":lambda a:a,"SIN":sp.sin,"COS":sp.cos,"EXP":sp.exp,
        "LOG":sp.log,"SQRT":sp.sqrt,"RECIP":lambda a:1/a,
        "SQUARE":lambda a:a*a,"CUBE":lambda a:a*a*a,"ABS":sp.Abs,
        "TAN":sp.tan,"SINH":sp.sinh,"COSH":sp.cosh,"TANH":sp.tanh}
    return mapping[kind](x)

def build_macro(action):
    scale,shift,inside,outside=action
    a=SCALE[scale]*X+SHIFT[shift]
    return f_sym(outside,f_sym(inside,a))

def features(xs,ys):
    x=np.asarray(xs,float);y=np.asarray(ys,float)
    if x.shape!=(48,) or y.shape!=(48,) or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        return None
    order=np.argsort(x);x=x[order];y=y[order]
    v=(y-np.median(y))/max(float(np.std(y)),1e-10)
    vec=list(np.interp(np.linspace(0,1,16),np.linspace(0,1,48),np.clip(v,-10,10)))
    vec+=list(np.log1p([np.max(abs(x)),np.max(abs(y)),np.ptp(x),np.ptp(y)]))
    vec+=list((np.mean(np.diff(v)>0),np.mean(np.diff(v)<0),
              np.mean(y<0),np.mean(x<0)))
    arr=np.asarray(vec,dtype=float)
    if len(arr)!=24 or not np.all(np.isfinite(arr)):return None
    return np.clip(arr,-30,30)

def numeric_exact_source_reward(row,action):
    """48 available ORIGINAL numeric source points, fit first32, verify all48.

    Never reads the full author true equation. Includes exact-rationalization
    of numeric output gains before any candidate is admitted.
    """
    if "x" not in row:return None
    xs=np.asarray(row["x"],dtype=float);ys=np.asarray(row["y"],dtype=float)
    if xs.shape!=(48,) or ys.shape!=(48,) or not np.all(np.isfinite(xs)) or not np.all(np.isfinite(ys)):
        return None
    try:
        scale,shift,inside,outside=action
        z=f_num(outside,f_num(inside,float(SCALE[scale])*xs+float(SHIFT[shift])))
        if np.shape(z)!=xs.shape or not np.all(np.isfinite(z)) or max(abs(z))>1e9:return None
        zc=z[:32]-np.mean(z[:32]);yc=ys[:32]-np.mean(ys[:32])
        denom=float(zc@zc)
        if denom<1e-15:return None
        a=float(zc@yc/denom)
        b=float(np.mean(ys[:32])-a*np.mean(z[:32]))
        if not np.isfinite(a) or not np.isfinite(b) or max(abs(a),abs(b))>1e7:return None
        if np.max(abs(a*z+b-ys)/(1+abs(ys)))>1e-8:return None
        ar=sp.Rational(a).limit_denominator(1000)
        br=sp.Rational(b).limit_denominator(1000)
        expr=sp.cancel(ar*build_macro(action)+br)
        fun=sp.lambdify(X,expr,"numpy")
        with np.errstate(all="ignore"):
            pred=np.broadcast_to(np.asarray(fun(xs),dtype=float),ys.shape)
        if not np.all(np.isfinite(pred)):return None
        residual=float(np.max(abs(pred-ys)/(1+abs(ys))))
        if residual>1e-8:return None
        return {"named_lambda":"lambda x: "+str(expr),"action_graph_edits":list(action),
                "source_max_normalized_error":residual,
                "new_nested_macro_definition":inside!="ID" and outside!="ID",
                "source_condition": "numeric_fit32_plus_outof_fit16_and_exact_Q_coeff"}
    except Exception:
        return None

def action_features(shape,position,prefix):
    arr=np.zeros(24+4+4*len(TOKENS),dtype=float)
    arr[:24]=shape
    arr[24+position]=1.
    for j,tok in enumerate(prefix):arr[28+j*len(TOKENS)+TOKIDX[tok]]=1.
    return arr

def source_train(train_path):
    train=json.loads(pathlib.Path(train_path).read_text())
    rows=train["train_source_only"]
    assert len(rows)==128
    rng=np.random.default_rng(20261023)
    successes=[];counter=collections.Counter()
    train_start=time.process_time()
    for row in rows:
        if features(row.get("x",[]),row.get("y",[])) is None:continue
        # Frozen NONORIGINAL source reward budget per training original.
        draws=rng.choice(len(ACTIONS),size=1200,replace=False)
        local=set()
        for idx in draws:
            path=ACTIONS[int(idx)]
            found=numeric_exact_source_reward(row,path)
            if found is not None and found["named_lambda"] not in local:
                local.add(found["named_lambda"])
                successes.append({"id":row["id"],"shape":features(row["x"],row["y"]).tolist(),
                    "action":list(path),"macro":found["named_lambda"],
                    "nonlinear":str(build_macro(path)).find("x")==-1 or (
                          path[2] not in ("ID",) or path[3] not in ("ID",))})
                counter[row["id"]]+=1
    verifier_cpu=time.process_time()-train_start
    xx=[];yy=[]
    for item in successes:
        for i,tok in enumerate(item["action"]):
            xx.append(action_features(np.array(item["shape"]),i,item["action"][:i]))
            yy.append(tok)
    model=None;model_cpu=0.
    if len(successes)>=3 and len(set(yy))>1:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model=MLPClassifier(hidden_layer_sizes=(48,24),
                     random_state=23,max_iter=320,
                     learning_rate_init=0.01,alpha=0.03)
            t0=time.process_time()
            model.fit(np.asarray(xx),np.asarray(yy))
            model_cpu=time.process_time()-t0
    details={
        "source_training_data_sha256":sha(pathlib.Path(train_path).read_bytes()),
        "train_rows":128,"own_source_program_trials":1200*sum(
             features(r.get("x",[]),r.get("y",[])) is not None for r in rows),
        "distinct_self_verified_macro_definitions":len(successes),
        "source_training_tasks_with_any_verified_macro":len(counter),
        "self_reward_training_task_ids":dict(counter),
        "verifier_source_train_CPU_s":verifier_cpu,
        "actual_MLP_fitting_CPU_s":model_cpu,
        "no_author_formula_training_labels":True,
        "does_not_train_on_hidden_eighth32":True,
        "training_policy":"uniform own graph-edit exploration, OFF-POLICY reward-filtered behavior cloning",
        "not_genuine_online_RL":True,
        "earned_named_macros":[{"macro":i["macro"],"action":i["action"],
            "training_source_id":i["id"]} for i in successes[:30]],
        "macros_sha256":sha(json.dumps(successes,sort_keys=True).encode()),
        "weights_sha256":(sha(json.dumps([v.tolist() for v in model.coefs_],
             sort_keys=True).encode()) if model else None)}
    return model,details,successes

def learned_actions(model,shape,rng,count):
    if model is None:
        return [ACTIONS[int(i)] for i in rng.choice(len(ACTIONS),size=count,replace=False)],count
    unseen=set();out=[];draws=0
    while len(out)<count and draws<8000:
        draws+=1
        if rng.random()<0.22:
            action=ACTIONS[int(rng.integers(len(ACTIONS)))]
        else:
            prefix=[]
            for step,choices in enumerate(CHOOSE):
                probs0=model.predict_proba([action_features(shape,step,prefix)])[0]
                allcls=list(model.classes_)
                prob=np.array([float(probs0[allcls.index(k)]) if k in allcls else 0.
                         for k in choices],dtype=float)
                prob=0.94*prob+0.06/len(choices)
                prob/=prob.sum()
                prefix.append(str(rng.choice(choices,p=prob)))
            action=tuple(prefix)
        if action not in unseen:
            unseen.add(action);out.append(action)
    fallback=0
    if len(out)<count:
        for act in ACTIONS:
            if act not in unseen:
                out.append(act);fallback+=1
                if len(out)>=count:break
    return out,fallback

def first_source_inference(train_path,source_path,output):
    model,training,successes=source_train(train_path)
    source=json.loads(pathlib.Path(source_path).read_text())
    assert len(source["source_numeric_without_equations"])==32
    learned_macros={tuple(i["action"]) for i in successes}
    rng=np.random.default_rng(201123)
    evidence={}
    for mode in ("learned_graph_edit_512","nolearn_random_512",
                 "nolearn_simple_first_512","complete_3920_classical"):
        started=time.process_time();cases=[];counts=collections.Counter()
        for row in source["source_numeric_without_equations"]:
            shape=features(row.get("x",[]),row.get("y",[]))
            if shape is None:
                cases.append({"id":row["id"],"status":"UNKNOWN_NO_48_SOURCE","generated_macros":[],
                    "actual_program_evaluations":0})
                continue
            if mode=="learned_graph_edit_512":
                trials,fallback=learned_actions(model,shape,rng,512)
                counts["fallback_to_unlearned_graphs"]+=fallback
            elif mode=="nolearn_random_512":
                trials=[ACTIONS[int(i)] for i in rng.choice(len(ACTIONS),512,replace=False)]
            elif mode=="nolearn_simple_first_512":
                # Prioritize short direct operators/affine parameters,
                # then nonlinear transformations and nesting.
                trials=sorted(ACTIONS,key=lambda a:(
                    int(a[2]!="ID")+int(a[3]!="ID"),
                    a[0]!="S1",a[1]!="Z0",
                    a[2]!="ID",a[3]!="ID",
                    a))[:512]
            else: trials=ACTIONS
            detected=[];dedup=set()
            for action in trials:
                found=numeric_exact_source_reward(row,action)
                if found is not None and found["named_lambda"] not in dedup:
                    dedup.add(found["named_lambda"])
                    found["reused_own_training_macro_graph"]=tuple(action) in learned_macros
                    detected.append(found)
            cases.append({"id":row["id"],
                          "status":"SOURCE_MACRO_PROPOSED" if detected else "UNKNOWN_NO_NUMERIC_MACRO",
                          "generated_macros":detected[:30],
                          "actual_program_evaluations":len(trials)})
            counts["case_with_macro"]+=int(bool(detected))
            counts["macro_definitions"]+=len(detected)
            counts["candidate_probes"]+=len(trials)
        evidence[mode]={"predictions":cases,
              "cpu_s":time.process_time()-started,
              "totals":dict(counts)}
    p={"schema":"NEUMANN_Q3_AUTHOR_ORIGINAL_EIGHTH32_LEARNED_NESTED_MACRO_SOURCE.v1",
       "source_only_original_sha256":sha(pathlib.Path(source_path).read_bytes()),
       "train_source_only_original_sha256":sha(pathlib.Path(train_path).read_bytes()),
       "training":training,
       "typed_primitive_operators_given_by_humans":list(BASE),
       "unary_nested_graph_edit_paths":len(ACTIONS),
       "new_named_compositional_macros_constructed_online":True,
       "self_rewarded_not_original_gold_supervised":True,
       "identical_programming_language_and_numerical_source_rights":True,
       "methods":evidence,"G1_global":"HOLD","Q3_global":"OPEN",
       "frontier_total_10x":"NOT_PROVED"}
    sig=save(output,p)
    print("Q3_SELF_REWARDED_COMPOSITIONAL_EIGHTH32_BEFORE_ORIGINAL_GRADE",json.dumps({
        "sha256":sig,"self_reward_positive_macros":training["distinct_self_verified_macro_definitions"],
        "training_tasks":training["source_training_tasks_with_any_verified_macro"],
        "known_training_CPU":training["verifier_source_train_CPU_s"]+training["actual_MLP_fitting_CPU_s"],
        "methods":{m:{"tested":v["totals"].get("candidate_probes",0),
           "source_macros":v["totals"].get("macro_definitions",0),
           "source_tasks":v["totals"].get("case_with_macro",0),
           "cpu_s":v["cpu_s"]} for m,v in evidence.items()}},sort_keys=True),flush=True)

def independent_original_author_exact_grader(truth_file,pred_file,output):
    gold=json.loads(pathlib.Path(truth_file).read_text())["private_true_equations"]
    pred=json.loads(pathlib.Path(pred_file).read_text())
    assert len(gold)==32 and len(pred["methods"])==4
    totals={};cases={}
    for mode,method in pred["methods"].items():
        table={r["id"]:r for r in method["predictions"]}
        record=[];cnt=collections.Counter()
        for t in gold:
            ident=t["id"];r=table[ident];cnt["total_originals"]+=1
            certified=[]
            try:
                node,var=allowed_formula(t["original_expression"])
                author=calc(node,{var:X},SYM)
                for proposal in r["generated_macros"]:
                    expression=sp.sympify(proposal["named_lambda"].replace("lambda x: ",""),
                          locals={"x":X})
                    if sp.simplify(author-expression)==0:
                        certified.append(proposal)
            except Exception:pass
            if certified:cnt["original_exact"]+=1
            else:cnt["original_UNKNOWN"]+=1
            if any(t["new_nested_macro_definition"] for t in certified):cnt["original_nested_exact"]+=1
            if any(t["reused_own_training_macro_graph"] for t in certified):
                cnt["original_macro_graph_reused_from_reward_train"]+=1
            record.append({"id":ident,"collection":t["collection"],"task_ID":t["task_ID"],
                "original_sha256":sha(t["original_expression"].encode()),
                "source_proposals":len(r["generated_macros"]),
                "certified_exact_named_lambdas":certified[:6],
                "status":"FULL_ORIGINAL_AUTHOR_SYMBOLICALLY_IDENTICAL" if certified else "UNKNOWN"})
        totals[mode]=dict(cnt);cases[mode]=record
    d={m:{r["id"] for r in rows if r["status"]=="FULL_ORIGINAL_AUTHOR_SYMBOLICALLY_IDENTICAL"} for m,rows in cases.items()}
    learned=d["learned_graph_edit_512"]
    report={"schema":"NEUMANN_Q3_FIRST_UNTOUCHED_EIGHTH32_NESTED_LAMBDA_SOURCE_TRUTH.v1",
      "frozen_source_predictions_sha256":sha(pathlib.Path(pred_file).read_bytes()),
      "previously_private_original_truth_sha256":sha(pathlib.Path(truth_file).read_bytes()),
      "original_count":32,"native_full_source_exact_author_grade":totals,
      "cases":cases,
      "learned_exclusive_over_nolearn_random_512":sorted(learned-d["nolearn_random_512"]),
      "learned_exclusive_over_nolearn_simple_first_512":sorted(learned-d["nolearn_simple_first_512"]),
      "learned_exclusive_over_complete_3920_classical":sorted(learned-d["complete_3920_classical"]),
      "independent_original_nonlinear_macro_exact_proof":
          totals["learned_graph_edit_512"].get("original_nested_exact",0),
      "reused_true_source_macro_graph_exact":
          totals["learned_graph_edit_512"].get("original_macro_graph_reused_from_reward_train",0),
      "human_supplied_primitive_operator_alphabet":True,
      "strong_external_PySR_Operon_comparison":"NOT_RUN",
      "global_Q3":"OPEN","G1":"HOLD","total_system_10x":"NOT_PROVED"}
    sig=save(output,report)
    print("Q3_EIGHTH32_INDEPENDENT_AUTHOR_NESTED_MACRO_FULL_TRUTH",json.dumps({
        "sha256":sig,"scores":totals,
        "learned_exclusive_vs_random":len(report["learned_exclusive_over_nolearn_random_512"]),
        "learned_exclusive_vs_classical":len(report["learned_exclusive_over_complete_3920_classical"])},sort_keys=True),flush=True)
    assert all(v["total_originals"]==32 for v in totals.values())

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("infer","grade"),required=True)
    for k in ("train","source","truth","pred","out"):parser.add_argument("--"+k,required=False)
    a=parser.parse_args()
    if a.mode=="infer":first_source_inference(a.train,a.source,a.pred)
    else:independent_original_author_exact_grader(a.truth,a.pred,a.out)
