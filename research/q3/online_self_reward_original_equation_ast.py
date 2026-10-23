"""Q3 first source-original transfer of SELF-REWARDED learned AST graph editing.

Training feedback: ONLY exact-ish numerical source residual from 48 x/y samples
for 128 other external author ERBench problems, never author formula labels.
The policy learns its OWN rewarded six discrete graph-edit action sequences
and samples executable new composite macro programs for the SIXTH
previously unused external original source cohort 2160:2192.
Native original author full symbolic equality is a separate grading job.

This is bounded-human-grammar composition, not new atomic meaning/whole Q3.
Matched 256 oracle-call random no-learning arm, full 2048-graph specialist.
"""
import argparse,ast,collections,csv,hashlib,itertools,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from erbench_original_sixth import allowed_formula,domain,calc,FUN,SYM,save,sha
from sklearn.neural_network import MLPClassifier

X=sp.Symbol("x")
PIN="03c0ceb53ed0348650c0a94ed5cd1e452325d2b7c7d3be68f9a458316eda33b1"
OPS=("ADD","SUB","MUL","DIV")
TERMS=("X","ONE","TWO","NEGONE")
SIDES=("LEFT","RIGHT")
CHOICES=(OPS,SIDES,OPS,TERMS,TERMS,TERMS)
CHARS=tuple(sorted(set(sum((list(c) for c in CHOICES),[]))))
C_INDEX={v:i for i,v in enumerate(CHARS)}
ALL_ACTIONS=tuple(itertools.product(*CHOICES))
assert len(ALL_ACTIONS)==2048

def training_source(source_csv,out):
    raw=pathlib.Path(source_csv).read_bytes()
    assert sha(raw)==PIN
    original=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    valid=[]
    for i,r in enumerate(original):
        try:
            tree,v=allowed_formula(r["expression"])
            lo,hi,_=domain(r.get("support",""))
            valid.append((i,r,tree,v,lo,hi))
        except Exception:pass
    valid.sort(key=lambda row:sha((row[1]["collection"]+"\x1f"+row[1]["task_ID"]+"\x1f"+str(row[0])).encode()))
    assert len(valid)==5717
    train=valid[96:224];assert len(train)==128
    payload=[]
    for i,r,tree,var,lo,hi in train:
        uid=sha((r["collection"]+"\x1f"+r["task_ID"]+"\x1f"+str(i)).encode())[:24]
        rng=np.random.default_rng(int(uid[:12],16))
        points=[]
        for x in rng.uniform(lo,hi,size=380):
            try:
                with np.errstate(all="ignore"):
                    y=float(calc(tree,{var:float(x)},FUN))
                if np.isfinite(y) and abs(y)<1e9:points.append((float(x),y))
            except Exception:pass
            if len(points)>=48:break
        if len(points)<48:
            payload.append({"id":uid,"status":"UNKNOWN_NOT_ENOUGH_NUMERIC_SOURCE"})
        else:
            payload.append({"id":uid,"status":"SOURCE_NUMERIC_READY",
                            "x":[v[0] for v in points],"y":[v[1] for v in points]})
    res={"schema":"NEUMANN_Q3_EXTERNAL_ORIGINAL_ONLINE_REWARD_TRAIN_SOURCE.v1",
        "source_original_dataset_SHA256":PIN,"selection":"sha-rank 96:224 first128, independent of sixth32 2160:2192",
        "true_author_formula_excluded":True,"train_source_only":payload}
    sig=save(out,res)
    print("Q3_SIXTH_TRAIN_DIFFERENT_ORIGINAL_NUMERIC_ONLY",json.dumps({
        "sha256":sig,"train_rows":len(payload),"usable":sum("x" in r for r in payload)}),flush=True)

def tree_ast(actions):
    if len(actions)!=6:raise ValueError("invalid actions")
    root,side,inside,a,b,c=actions
    for v,choices in zip(actions,CHOICES):
        if v not in choices:raise ValueError("bad graph edit token")
    val={"X":X,"ONE":sp.Integer(1),"TWO":sp.Integer(2),"NEGONE":sp.Integer(-1)}
    op={"ADD":lambda u,v:u+v,"SUB":lambda u,v:u-v,
        "MUL":lambda u,v:u*v,"DIV":lambda u,v:u/v}
    core=op[inside](val[b],val[c])
    return sp.cancel(op[root](core,val[a]) if side=="LEFT" else op[root](val[a],core))

def cheap_graph_value(actions,x):
    d={"X":x,"ONE":np.ones_like(x),"TWO":np.full_like(x,2.),
       "NEGONE":np.full_like(x,-1.)}
    def op(kind,a,b):
        if kind=="ADD":return a+b
        if kind=="SUB":return a-b
        if kind=="MUL":return a*b
        return a/b
    root,side,inner,a,b,c=actions
    with np.errstate(all="ignore"):
        branch=op(inner,d[b],d[c])
        return op(root,branch,d[a]) if side=="LEFT" else op(root,d[a],branch)

def features(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float)
    ind=np.argsort(x);x=x[ind];y=y[ind]
    v=(y-np.median(y))/max(float(np.std(y)),1e-10)
    vec=list(np.interp(np.linspace(0,1,16),np.linspace(0,1,len(v)),np.clip(v,-10,10)))
    vec+=list(np.log1p([max(abs(x)),max(abs(y)),np.ptp(x),np.ptp(y)]))
    vec+=list((np.mean(np.diff(v)>0),np.mean(np.diff(v)<0),
              np.mean(y<0),np.mean(x<0)))
    ans=np.asarray(vec,dtype=float)
    assert len(ans)==24
    return np.clip(ans,-30,30)

def gen_reward(row,action,strict=True):
    # source-only fitness and construction; exact author formula NEVER opened.
    if "x" not in row:return None
    xs=np.asarray(row["x"],float);ys=np.asarray(row["y"],float)
    try:
        z=np.asarray(cheap_graph_value(action,xs),dtype=float)
        z=np.broadcast_to(z,xs.shape)
        if not np.all(np.isfinite(z)) or np.std(z)<1e-10:return None
        A=np.column_stack((z,np.ones(len(z))))
        p=np.linalg.lstsq(A[:32],ys[:32],rcond=1e-12)[0]
        if not np.all(np.isfinite(p)) or max(abs(p))>1e7:return None
        predict=A@p
        error=np.max(abs(predict-ys)/(1+abs(ys)))
        if not np.isfinite(error) or error>1e-6:return None
        if strict and np.max(abs(predict[32:]-ys[32:])/(1+abs(ys[32:])))>1e-8:return None
        # Turn the self-reward discovered graph into a NEW named executable lambda.
        graph=tree_ast(action)
        macro=sp.cancel(sp.Rational(float(p[0])).limit_denominator(1000)*graph+
                        sp.Rational(float(p[1])).limit_denominator(1000))
        fn=sp.lambdify(X,macro,modules="numpy")
        with np.errstate(all="ignore"):
            recovered=np.broadcast_to(np.asarray(fn(xs),float),xs.shape)
        if not np.all(np.isfinite(recovered)):return None
        res=float(np.max(abs(recovered-ys)/(1+abs(ys))))
        if res>1e-7:return None
        return {"lambda_expression":str(macro),"graph_edit_sequence":list(action),
                "source_residual":res,"new_named_composite_program":True}
    except Exception:return None

def action_vec(shape,step,prefix):
    v=np.zeros(24+6+6*len(CHARS),float)
    v[:24]=shape
    v[24+step]=1
    for j,tok in enumerate(prefix):
        v[30+j*len(CHARS)+C_INDEX[tok]]=1
    return v

def train_agent(train_json,artifact):
    data=json.loads(pathlib.Path(train_json).read_text())
    rng=np.random.default_rng(34123)
    positive=[];count=collections.Counter();searched=0
    started=time.process_time()
    for row in data["train_source_only"]:
        if "x" not in row:continue
        shapes=features(row["x"],row["y"])
        # SAMPLE from the learner's own policy, which initially is uniform.
        # Agent ONLY observes success/failure after its own action graph.
        # 256 tries per original task, pre-registered fixed budget.
        indices=rng.choice(len(ALL_ACTIONS),size=256,replace=False)
        for k in indices:
            searched+=1
            acts=ALL_ACTIONS[int(k)]
            proposed=gen_reward(row,acts)
            if proposed is not None:
                positive.append({"id":row["id"],"features":shapes.tolist(),
                    "actions":list(acts),"lambda":proposed["lambda_expression"]})
                count[row["id"]]+=1
    training_verifier_cpu=time.process_time()-started
    xdata=[];ydata=[]
    for p in positive:
        for i,tok in enumerate(p["actions"]):
            xdata.append(action_vec(np.asarray(p["features"]),i,p["actions"][:i]))
            ydata.append(tok)
    if len(set(ydata))<2 or len(positive)<8:
        model=None;train_cpu=0;weight="UNKNOWN_FEW_SELF_REWARDED_PROGRAMS"
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model=MLPClassifier(hidden_layer_sizes=(32,),random_state=34123,
                max_iter=250,learning_rate_init=0.01,alpha=.05)
            beg=time.process_time()
            model.fit(np.asarray(xdata),np.asarray(ydata))
            train_cpu=time.process_time()-beg
        weight=sha(json.dumps([z.tolist() for z in model.coefs_],sort_keys=True).encode())
    dataout={"schema":"NEUMANN_Q3_EXTERNAL_SOURCE_SELF_REWARDED_GRAPH_EDIT_MODEL.v1",
        "training_numeric_source_sha256":sha(pathlib.Path(train_json).read_bytes()),
        "online_proposals":searched,"positive_own_source_reward":len(positive),
        "positive_unique_training_tasks":len(count),
        "self_reward_trace_sha256":sha(json.dumps(positive,sort_keys=True).encode()),
        "training_reward_and_candidate_CPU_s":training_verifier_cpu,
        "fitted_neural_CPU_s":train_cpu,
        "trained_weights_SHA256":weight,
        "correct_graph_structure_from_teacher":"NONE",
        "human_assigned_syntax_primitives":list(CHARS),
        "independent_external_test_sha_rank":[2160,2192],
        "positive_trace_training_examples":len(xdata),
        "positive_self_samples":[{"actions":r["actions"],"lambda":r["lambda"]} for r in positive[:20]],
        "no_proven_semantically_new_atomic_primitive":True}
    return model,dataout

def sampled_action_predictions(model,shape,rng,n):
    output=[];seen=set()
    for _ in range(n):
        if model is None:
            candidate=ALL_ACTIONS[int(rng.integers(len(ALL_ACTIONS)))]
        else:
            prefix=[]
            for i,choices in enumerate(CHOICES):
                v=action_vec(shape,i,prefix)
                probabilities=model.predict_proba([v])[0]
                probs=np.array([float(probabilities[list(model.classes_).index(t)]) if t in model.classes_ else 0
                                for t in choices])
                probs=(0.9*probs+0.1/len(choices))
                probs=probs/probs.sum()
                prefix.append(str(rng.choice(choices,p=probs)))
            candidate=tuple(prefix)
        if candidate not in seen:
            output.append(candidate);seen.add(candidate)
    return output

def infer(train_json,source_json,out):
    model,provenance=train_agent(train_json,None)
    source=json.loads(pathlib.Path(source_json).read_text())
    assert len(source["source_numeric_without_equations"])==32
    rows=source["source_numeric_without_equations"]
    policy={}
    rng=np.random.default_rng(41041)
    for strategy in ("online_neural_graph_edits","same256_random_nolearn","complete2048_classical"):
        t0=time.process_time()
        cases=[]
        for row in rows:
            if "x" not in row:
                cases.append({"id":row["id"],"status":"UNKNOWN_SOURCE","proposals":[],
                        "source_oracle_attempts":0});continue
            shape=features(row["x"],row["y"])
            if strategy=="online_neural_graph_edits":
                actions=sampled_action_predictions(model,shape,rng,256)
            elif strategy=="same256_random_nolearn":
                actions=[ALL_ACTIONS[int(k)] for k in rng.choice(len(ALL_ACTIONS),256,replace=False)]
            else:actions=ALL_ACTIONS
            candidates=[];seen=set()
            for acts in actions:
                result=gen_reward(row,acts)
                if result is not None and result["lambda_expression"] not in seen:
                    candidates.append(result)
                    seen.add(result["lambda_expression"])
            cases.append({"id":row["id"],
                "status":"SOURCE_PROPOSED" if candidates else "UNKNOWN",
                "proposals":candidates[:25],"source_oracle_attempts":len(actions)})
        policy[strategy]={"first_predictions":cases,
            "cpu_s":time.process_time()-t0,
            "source_graph_proposals":sum(len(c["proposals"]) for c in cases),
            "task_with_candidate":sum(c["status"]=="SOURCE_PROPOSED" for c in cases),
            "program_evaluation_calls":sum(c["source_oracle_attempts"] for c in cases)}
    outdata={"schema":"NEUMANN_Q3_SIXTH32_FIRST_SOURCE_ONLY_GENERATIVE_POLICY.v1",
        "external_source_SHA256":sha(pathlib.Path(source_json).read_bytes()),
        "self_reward_model":provenance,"hypothesis_program_count":len(ALL_ACTIONS),
        "test":policy,"target_formula_never_available":True,
        "G1_global":"HOLD","frontier_10x":"NOT_PROVED"}
    filehash=save(out,outdata)
    print("Q3_SIXTH32_SEALED_NEW_ONLINE_AST_SOURCE",json.dumps({
       "sha256":filehash,"learned_training_success":provenance["positive_own_source_reward"],
       "trained_on_tasks":provenance["positive_unique_training_tasks"],
       "methods":{k:{"source_candidates":v["source_graph_proposals"],
         "tasks":v["task_with_candidate"],"CPU_s":v["cpu_s"],
         "calls":v["program_evaluation_calls"]} for k,v in policy.items()}},sort_keys=True),flush=True)

def grade(truth_path,pred_path,out):
    truth=json.loads(pathlib.Path(truth_path).read_text())["private_true_equations"]
    predicted=json.loads(pathlib.Path(pred_path).read_text())
    assert len(truth)==32
    score={};cases={}
    for method,m in predicted["test"].items():
        entries={x["id"]:x for x in m["first_predictions"]}
        metric=collections.Counter();evaluated=[]
        for row in truth:
            entry=entries[row["id"]]
            exact=[]
            try:
                tree,var=allowed_formula(row["original_expression"])
                original=calc(tree,{var:X},SYM)
                for possible in entry["proposals"]:
                    g=sp.sympify(possible["lambda_expression"],locals={"x":X})
                    if sp.cancel(sp.together(original-g))==0:
                        exact.append(possible)
            except Exception:pass
            metric["total"]+=1
            if exact:metric["exact"]+=1
            else:metric["not_proved"]+=1
            evaluated.append({"id":row["id"],"original_formula_SHA256":sha(row["original_expression"].encode()),
                "status":"AUTHENTIC_ORIGINAL_FORMULA_EQUIVALENT" if exact else "UNKNOWN_NOT_FULLY_PROVED",
                "generated_exact_macro_definitions":[e["lambda_expression"] for e in exact[:6]],
                "candidate_count":len(entry["proposals"])})
        score[method]=dict(metric);cases[method]=evaluated
    learner={r["id"] for r in cases["online_neural_graph_edits"] if r["status"]=="AUTHENTIC_ORIGINAL_FORMULA_EQUIVALENT"}
    complete={r["id"] for r in cases["complete2048_classical"] if r["status"]=="AUTHENTIC_ORIGINAL_FORMULA_EQUIVALENT"}
    baseline={r["id"] for r in cases["same256_random_nolearn"] if r["status"]=="AUTHENTIC_ORIGINAL_FORMULA_EQUIVALENT"}
    ret={"schema":"NEUMANN_Q3_NEW_EXTERNAL_32_TRUE_ORIGINAL_SELF_REWARDED_AST_FIRST_GRADE.v1",
      "sealed_predictions_SHA256":sha(pathlib.Path(pred_path).read_bytes()),
      "original_author_truth_SHA256":sha(pathlib.Path(truth_path).read_bytes()),
      "scores":score,"cases":cases,
      "learned_true_exclusive_over_strong_classical":sorted(learner-complete),
      "learned_true_exclusive_over_samebudget_random":sorted(learner-baseline),
      "no_model_created_new_semantically_atomic_primitive":True,
      "specialist_PySR_Operon":"NOT_EXECUTED",
      "different_source_family_vs_previously_SMT":"YES_EXTERNAL_EQUATION_RECOVERY",
      "Q3_global":"OPEN","G1":"HOLD","total_lifecycle_10x":"NOT_PROVED"}
    sig=save(out,ret)
    print("Q3_SIXTH32_NEW_FAMILY_FIRST_INDEPENDENT_ORIGINAL_GRADE",
      json.dumps({"sha256":sig,"scores":score,
         "learned_only_vs_full":len(learner-complete),
         "learned_only_vs_random":len(learner-baseline)},sort_keys=True),flush=True)
    assert all(s["total"]==32 for s in score.values())
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("train_source","infer","grade"),required=True)
    for k in ("csv_path","train","source","pred","truth","out"):
        p.add_argument("--"+k.replace("_","-"))
    a=p.parse_args()
    if a.mode=="train_source":training_source(a.csv_path,a.train)
    elif a.mode=="infer":infer(a.train,a.source,a.pred)
    else:grade(a.truth,a.pred,a.out)
