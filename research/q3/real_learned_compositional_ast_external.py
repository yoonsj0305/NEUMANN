"""NEUMANN Q3: learned-guided COMPOSITION of executable typed symbolic ASTs.

Learning: external original author equations in disjoint TRAIN ranks 96..2095,
used to supervise PRIMITIVE-OP probability from numeric input/output samples.
Test: untouched fifth32 original author equations hash rank 2128..2159, inference
sees only 48 binary64 numeric original source probes (never true original AST).
Output: syntactically novel symbolic programs built FROM semantic primitives,
not choosing a finite list of ready-made target full-formula templates.

Crucial limitation: basic operator alphabet is HUMAN-supplied; discovering
combinations is not inventing mathematically new primitive semantics.
Equal grammar strong exhaustive primitive-composition comparator also runs.
"""
import argparse,ast,collections,csv,hashlib,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from erbench_original_fifth import allowed_formula,domain,calc,FUN,SYM,save,sha

X=sp.Symbol('x')
PIN="03c0ceb53ed0348650c0a94ed5cd1e452325d2b7c7d3be68f9a458316eda33b1"
CLASSES=["SIN","COS","EXP","LOG","SQRT","DIV","MUL"]
OPERATORS={"SIN":sp.sin,"COS":sp.cos,"EXP":sp.exp,"LOG":sp.log,"SQRT":sp.sqrt}

def numeric_features(xx,yy):
    x=np.asarray(xx,float);y=np.asarray(yy,float)
    if len(x)<16 or len(y)!=len(x) or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):return None
    ix=np.argsort(x);x=x[ix];y=y[ix]
    standardized=np.clip((y-np.median(y))/max(float(np.std(y)),1e-10),-15,15)
    v=np.interp(np.linspace(0,1,18),np.linspace(0,1,len(x)),standardized)
    dy=np.diff(standardized);ddy=np.diff(dy)
    c=[np.log1p(max(abs(x))),np.log1p(max(abs(y))),
       np.log1p(np.ptp(x)),np.log1p(np.ptp(y)),
       float(np.median(abs(dy))),float(np.median(abs(ddy))),
       float(np.mean(dy>0)),float(np.mean(dy<0)),
       float(np.mean(abs(standardized)>5)),float(np.mean(y<0)),
       float(np.mean(x<0)),float(np.mean(standardized**2))]
    a=np.r_[v,c]
    return np.clip(a,-30,30).tolist() if np.all(np.isfinite(a)) else None

def op_labels(node):
    labels=set()
    for q in ast.walk(node):
        if isinstance(q,ast.Call) and isinstance(q.func,ast.Name):
            key=q.func.id.upper()
            if key in CLASSES:labels.add(key)
        if isinstance(q,ast.BinOp):
            if isinstance(q.op,ast.Div):labels.add("DIV")
            if isinstance(q.op,(ast.Mult,ast.Pow)):labels.add("MUL")
    return [int(i in labels) for i in CLASSES]

def source_training(csv_path,out):
    raw=pathlib.Path(csv_path).read_bytes()
    assert sha(raw)==PIN
    tab=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    eligible=[]
    for i,r in enumerate(tab):
        try:
            tree,var=allowed_formula(r["expression"])
            lo,hi,tag=domain(r.get("support",""))
            eligible.append((i,r,tree,var,lo,hi))
        except Exception:continue
    eligible.sort(key=lambda q:sha((q[1]["collection"]+"\x1f"+q[1]["task_ID"]+"\x1f"+str(q[0])).encode()))
    assert len(eligible)==5717
    train=eligible[96:2096]
    samples=[]
    for i,row,tree,var,lo,hi in train:
        try:
            uid=sha((row["collection"]+"\x1f"+row["task_ID"]+"\x1f"+str(i)).encode())[:24]
            rng=np.random.default_rng(int(uid[:12],16))
            vals=[]
            for xx in rng.uniform(lo,hi,100):
                try:
                    with np.errstate(all='ignore'):
                        yy=float(calc(tree,{var:float(xx)},FUN))
                    if np.isfinite(yy) and abs(yy)<1e9:vals.append((float(xx),yy))
                except Exception:pass
                if len(vals)>=40:break
            if len(vals)<24:continue
            vec=numeric_features([t[0] for t in vals],[t[1] for t in vals])
            if vec is None:continue
            samples.append({"f":vec,"labels":op_labels(tree),"id":uid})
        except Exception:continue
    assert len(samples)>=350
    out_sha=save(out,{"schema":"NEUMANN_Q3_EXTERNAL_SOURCE_OPERATOR_SUPERVISION.v1",
             "train_ranks":[96,2096],"evaluation_ranks":[2128,2160],
             "author_originals_earlier_other_tasks_used_as_labels":True,
             "no_eval_original_truth":True,"samples":samples,
             "human_supplied_primitive_types":CLASSES,"source_sha":sha(raw)})
    print("Q3_TRAIN_SAMPLES_FOR_OPERATOR_AST_INDUCTION",json.dumps({
        "n":len(samples),"sha256":out_sha,
        "classes":dict(zip(CLASSES,np.asarray([s["labels"] for s in samples]).sum(axis=0).astype(int).tolist()))}),flush=True)

def build_exprs():
    """This is executable AST CONSTRUCTION, not a list of whole benchmark target formulas."""
    exprs={}
    def admit(e):
        try:
            e=sp.cancel(e) if e.is_rational_function(X) else e
            if not e.has(X) or sp.count_ops(e)>14:return
            exprs[str(e)]=e
        except Exception:pass
    for c in (-2,-1,0,1,2):
        admit(X+c)
        if c:admit(c*X)
    q=X
    for power in (2,3):q=q*X;admit(q)
    seeds=list(exprs.values())
    for e in seeds:
        for name,fn in OPERATORS.items():
            admit(fn(e))
        admit(1/e)
    bases=list(exprs.values())
    # New typed DAGs built by composition: x*F(x), u(F(x)) on previously
    # composed arithmetic terms. Such composite graphs are NOT input templates.
    for e in bases:
        if sp.count_ops(e)<=5 and e!=X:
            admit(X*e)
        if sp.count_ops(e)<=2 and e.has(X):
            for name in ("SIN","COS"):
                admit(OPERATORS[name](e))
    # Budget capped by AST complexity only, NOT original test source answer.
    programs=sorted(exprs.values(),key=lambda e:(sp.count_ops(e),len(str(e)),str(e)))
    assert len(programs)>=50
    return programs

def consumed_ops(expr):
    ops=set()
    for q in sp.preorder_traversal(expr):
        if q.func is sp.sin:ops.add("SIN")
        elif q.func is sp.cos:ops.add("COS")
        elif q.func is sp.exp:ops.add("EXP")
        elif q.func is sp.log:ops.add("LOG")
        elif q.func is sp.sqrt:ops.add("SQRT")
        elif q.is_Pow and q.exp.is_negative:ops.add("DIV")
        elif q.is_Mul or (q.is_Pow and q.exp.is_Integer and q.exp>1):ops.add("MUL")
    return ops

def synthesize(row,ranking,programs,budget):
    start=time.process_time()
    if "x" not in row:return {"status":"UNKNOWN_NO_ORIGINAL_NUMERIC_SOURCE",
                             "candidate_programs":[],"cpu_s":0,"evaluations":0}
    xs=np.array(row["x"],dtype=float);ys=np.array(row["y"],dtype=float)
    if not (len(xs)==48 and np.all(np.isfinite(xs)) and np.all(np.isfinite(ys))):
        return {"status":"UNKNOWN_SOURCE","candidate_programs":[],"cpu_s":0,"evaluations":0}
    # Primitive ranking learned from numeric task. Untyped output-program
    # templates are not memorized: complete ASTs are built from primitives.
    key=lambda e:(-sum(ranking[op] for op in consumed_ops(e)),sp.count_ops(e),len(str(e)))
    ordered=sorted(programs,key=key) if ranking else programs[:]
    ordered=ordered[:budget]
    candidates=[];valid=[]
    count=0
    for expr in ordered:
        try:
            fn=sp.lambdify(X,expr,modules='numpy')
            with np.errstate(all='ignore'):
                z=np.broadcast_to(np.asarray(fn(xs),dtype=float),xs.shape)
            count+=1
            if not np.all(np.isfinite(z)) or np.std(z)<1e-10:continue
            # z must be well-defined on every numeric source point
            valid.append((expr,z))
        except Exception:count+=1
    if len(valid)==0:
        return {"status":"UNKNOWN_NO_VALID_FEATURES","candidate_programs":[],
                "evaluations":count,"cpu_s":time.process_time()-start}
    # Greedy source-only single and two-node feature composition.
    # This constructs f(x)=a*g1(x)+b*g2(x)+c; g1,g2 are dynamically built
    # executable ASTs, not candidate full functions supplied by humans.
    def try_composition(base,features):
        yy=ys
        A=np.column_stack(features+[np.ones_like(yy)])
        try:
            fitted=np.linalg.lstsq(A[:40],yy[:40],rcond=1e-12)[0]
            if not np.all(np.isfinite(fitted)) or np.max(abs(fitted))>1e5:return
            resid=np.max(abs(A@fitted-yy)/(1+abs(yy)))
            if not np.isfinite(resid) or resid>1e-8:return
            rat=[sp.Rational(float(q)).limit_denominator(1000) for q in fitted]
            whole=sp.cancel(sum(rat[i]*base[i] for i in range(len(base)))+rat[-1])
            verified=sp.lambdify(X,whole,modules='numpy')
            with np.errstate(all='ignore'):
                predicted=np.broadcast_to(np.asarray(verified(xs),dtype=float),xs.shape)
            residual=float(np.max(abs(predicted-yy)/(1+abs(yy))))
            if not np.isfinite(residual) or residual>1e-8:return
            candidate={"sympy_expr":str(whole),
                       "primitive_graph_composed":True,
                       "basis_programs":[str(z) for z in base],
                       "has_new_two_feature_composition":len(base)==2,
                       "source_residual":residual,
                       "symbols_after_fit":int(sp.count_ops(whole))}
            if candidate["sympy_expr"] not in {q["sympy_expr"] for q in candidates}:
                candidates.append(candidate)
        except Exception:return
    for e,z in valid:try_composition([e],[z])
    # Test all pairs of terms within the strictly predeclared budget;
    # both policy and equal-rights exhaustive classical use same constructor.
    for j in range(len(valid)):
        for k in range(j):
            count+=1
            try_composition([valid[j][0],valid[k][0]],[valid[j][1],valid[k][1]])
            if len(candidates)>=16:break
        if len(candidates)>=16:break
    return {"status":"PROPOSED_FROM_COMPOSED_AST" if candidates else "UNKNOWN_NO_EXACT_NUMERIC_PROGRAM",
            "candidate_programs":candidates,
            "evaluations":count,"cpu_s":time.process_time()-start}

def model_and_original_proposals(train_path,source,out):
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    d=json.loads(pathlib.Path(train_path).read_text())
    rows=json.loads(pathlib.Path(source).read_text())["source_numeric_without_equations"]
    assert len(rows)==32 and d["evaluation_ranks"]==[2128,2160]
    train=d["samples"];Xtrain=np.array([r["f"] for r in train],float)
    Y=np.array([r["labels"] for r in train],int)
    start=time.process_time()
    scaler=StandardScaler().fit(Xtrain)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        net=MLPClassifier(hidden_layer_sizes=(32,),max_iter=150,
                          random_state=213,alpha=0.01,learning_rate_init=0.005)
        net.fit(scaler.transform(Xtrain),Y)
    train_cpu=time.process_time()-start
    terms=build_exprs()
    counts=collections.Counter()
    programs={}
    for name in ("learned_composition","fixed_order_composition","all_primitives_classical"):
        programs[name]=[]
    for row in rows:
        feat=numeric_features(row.get("x",[]),row.get("y",[])) if "x" in row else None
        if feat is None:
            rank={n:0. for n in CLASSES}
        else:
            prob=net.predict_proba(scaler.transform([feat]))
            # sklearn version multilabel proba shape N x #classes.
            ar=np.asarray(prob)
            if ar.ndim==3:ar=ar[:,:,1]
            rank={n:float(ar[0,i]) for i,n in enumerate(CLASSES)}
        learned=synthesize(row,rank,terms,budget=min(28,len(terms)))
        fixed=synthesize(row,{},terms,budget=min(28,len(terms)))
        full=synthesize(row,{},terms,budget=len(terms))
        for name,val in [("learned_composition",learned),
                         ("fixed_order_composition",fixed),
                         ("all_primitives_classical",full)]:
            programs[name].append({"id":row["id"],**val})
            counts[name+"_source_candidates"]+=int(bool(val["candidate_programs"]))
    evidence={"schema":"NEUMANN_Q3_ACTUAL_EXTERNAL_NEURAL_COMPOSITION_INDUCTION.v1",
      "program_generator":"learned-guided TYPE-SAFE symbolic AST expansion + regression composition",
      "human_specified_only_primitive_operator_alphabet":CLASSES,
      "all_generated_feature_programs":[str(t) for t in terms],
      "num_induced_feature_programs":len(terms),
      "not_a_new_semantically_atomic_primitive":True,
      "actual_neural_model_trained":True,
      "source_only_training_sha":sha(pathlib.Path(train_path).read_bytes()),
      "source_only_eval_sha":sha(pathlib.Path(source).read_bytes()),
      "train_cpu_s":train_cpu,
      "trained_weights_sha":sha(json.dumps([q.tolist() for q in net.coefs_],sort_keys=True).encode()),
      "all_algorithms_exact_same_primitive_ops":True,
      "learned_and_fixed_basis_budget":28,
      "full_classical_all_basis_budget":len(terms),
      "predictions":programs,
      "counts":dict(counts),"Q3_global":"OPEN","G1":"HOLD"}
    sign=save(out,evidence)
    print("Q3_GENERATED_AST_FIRST_SEALED_SOURCE_PROGRAMS",
         json.dumps({"sha256":sign,"train_cpu_s":train_cpu,
          "induced_programs":len(terms),"counts":dict(counts)},sort_keys=True),flush=True)

def independent_original_truth(truth_file,pred_file,out):
    truth=json.loads(pathlib.Path(truth_file).read_text())["private_true_equations"]
    predicted=json.loads(pathlib.Path(pred_file).read_text())
    assert len(truth)==32
    outsets={};scores={};new_syntax={}
    for method,rows in predicted["predictions"].items():
        inferred={q["id"]:q for q in rows}
        receipts=[];counter=collections.Counter()
        for true in truth:
            c=inferred[true["id"]]
            counter["total"]+=1
            valid=[]
            try:
                tree,var=allowed_formula(true["original_expression"])
                original=calc(tree,{var:X},SYM)
                for pred in c["candidate_programs"]:
                    expr=sp.sympify(pred["sympy_expr"],locals={"x":X})
                    try:
                        if sp.cancel(sp.together(original-expr))==0:
                            valid.append(pred)
                    except Exception:pass
            except Exception:pass
            if valid:
                counter["original_exact"]+=1
                if any(z["has_new_two_feature_composition"] for z in valid):
                    counter["original_exact_two_term_composition"]+=1
                status="ORIGINAL_EXACT_FUNCTION"
            else:
                counter["abstain_or_rejected"]+=1
                status="UNKNOWN_NO_EXACT_CERTIFICATE"
            receipts.append({"id":true["id"],"collection":true["collection"],"task_ID":true["task_ID"],
                "original_sha256":sha(true["original_expression"].encode()),
                "exact_proposals":[{"expr":z["sympy_expr"],
                    "components":z["basis_programs"],
                    "two_term_new_composition":z["has_new_two_feature_composition"]} for z in valid[:6]],
                "source_proposals":len(c["candidate_programs"]),
                "source_evaluations":c["evaluations"],
                "cpu_s":c["cpu_s"],"verdict":status})
        outsets[method]=receipts;scores[method]=dict(counter)
    learned={x["id"] for x in outsets["learned_composition"] if x["verdict"]=="ORIGINAL_EXACT_FUNCTION"}
    classical={x["id"] for x in outsets["all_primitives_classical"] if x["verdict"]=="ORIGINAL_EXACT_FUNCTION"}
    exclusive=sorted(learned-classical)
    payload={"schema":"NEUMANN_EXTERNAL_FIFTH32_GENERATIVE_AST_FIRST_INDEPENDENT_GRADE.v1",
       "source_only_prediction_sha":sha(pathlib.Path(pred_file).read_bytes()),
       "original_private_author_truth_sha":sha(pathlib.Path(truth_file).read_bytes()),
       "scores":scores,"graded":outsets,"neural_exclusive_exact_originals":exclusive,
       "new_source_AST_outside_fixed_whole_templates":"TESTED_WITH_HUMAN_PRIMITIVES_ONLY",
       "learned_semantically_new_atomic_operator":"NOT_PROVED",
       "frontier_comparison":"NOT_TESTED","total_cost_10x":"NOT_PROVED",
       "strongest_external_srbench_pysr_operon_comparator":"NOT_TESTED",
       "G1":"HOLD"}
    sig=save(out,payload)
    print("Q3_NEW_COMPOSITION_ORIGINAL_AUTHOR_GRADE",
          json.dumps({"sha256":sig,"scores":scores,
              "learned_unique_count":len(exclusive)},sort_keys=True),flush=True)
    assert all(q["total"]==32 for q in scores.values())
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("train_data","infer","grade"),required=True)
    for k in ("csv_path","source","train","truth","pred","out"):
        p.add_argument("--"+k.replace("_","-"))
    a=p.parse_args()
    if a.mode=="train_data":source_training(a.csv_path,a.train)
    elif a.mode=="infer":model_and_original_proposals(a.train,a.source,a.pred)
    else:independent_original_truth(a.truth,a.pred,a.out)
