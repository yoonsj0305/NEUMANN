"""Q3 actual learned STRUCTURAL GRAPH ACTION policy, first original tenth32.

The neural network learns which NEW GRAPH CONNECTION operation to execute:
ADD_BRANCH, MULTIPLY_BRANCH, COMPOSE_UNARY, RATIONAL_REWRITE, REUSE_BINDING.
All atom semantics, coefficient solver and action executors are explicit
HUMAN supplied. The program chooses its structural edit by a trained contextual
reward model, never by reading true original author target equations.

Rewards come from source-only 48 x-y samples of distinct ERBench original author
tasks, not any gold formula, winning program trace, or test source labels.
At evaluation, neural chooses top2 graph actions; controls random2, fixed2, ALL5.
This is source-reward LEARNED action selection, not open-ended unrestricted
new primitive invention. A executes all same action families, often stronger.
"""
import argparse,collections,hashlib,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from sklearn.neural_network import MLPRegressor
from erbench_original_tenth import sha,save,allowed_formula,calc,SYM,rational_fit
from learned_additive_macro_ninth32 import BASIS,numop,original_shape,X

ACTIONS=("ADD_BRANCH","MULTIPLY_BRANCH","COMPOSE_UNARY","RATIONAL_REWRITE","REUSE_BINDING")
TRAIN_SEED=835019
MAX_SOURCE_ROWS=128
REWARD_SAMPLES_PER_TRAIN=3
FEATURE_TOP=22
BOUND_DEN=1000

def valid(row):
    return "x" in row and original_shape(row.get("x",[]),row.get("y",[])) is not None

def source_context(row):
    x=np.asarray(row["x"],dtype=float)
    y=np.asarray(row["y"],dtype=float)
    values=[];ids=[]
    for i,b in enumerate(BASIS):
        with np.errstate(all="ignore"):
            z=np.asarray(numop(b["op"],b["scale"]*x+b["shift"]),dtype=float)
        if z.shape==x.shape and np.all(np.isfinite(z)) and max(abs(z))<1e10 and np.std(z[:32])>1e-10:
            values.append(z);ids.append(i)
    if not values:return None
    m=np.column_stack(values)
    ym=np.mean(y[:32]);center=y[:32]-ym
    zm=m[:32,:]-np.mean(m[:32,:],axis=0)
    norm=np.linalg.norm(zm,axis=0)
    score=np.abs(zm.T@center)/np.maximum(norm,1e-14)
    rank=np.argsort(-score,kind="stable")
    return {"x":x,"y":y,"values":m,"ids":ids,"rank":rank,
         "scores":score,"feature":original_shape(x,y)}

def normalized_error(y,pred):
    with np.errstate(all="ignore"):
        rel=np.abs(pred-y)/(1+np.abs(y))
    return float(np.max(rel)) if np.all(np.isfinite(rel)) else float("inf")

def fit_two(source,cols):
    y=source["y"]
    A=np.column_stack(list(cols)+[np.ones(len(y))])
    try:
        params=np.linalg.lstsq(A[:32],y[:32],rcond=1e-12)[0]
        if not np.all(np.isfinite(params)) or max(abs(params))>1e9:return None
        output=A@params
        err=normalized_error(y,output)
        if not np.isfinite(err):return None
        return params,err
    except Exception:return None

def rationalize(source,feature_symbols,coefficients):
    try:
        params=[sp.Rational(float(v)).limit_denominator(BOUND_DEN) for v in coefficients]
        if len(params)!=len(feature_symbols)+1:return None
        expression=sp.cancel(sum(params[i]*feature_symbols[i] for i in range(len(feature_symbols)))+params[-1])
        # Construction precedes original-truth grader. Exact output rational coefficients.
        func=sp.lambdify(X,expression,modules="numpy")
        with np.errstate(all="ignore"):
            out=np.broadcast_to(np.asarray(func(source["x"]),dtype=float),source["y"].shape)
        err=normalized_error(source["y"],out)
        if err>1e-8:return None
        return {"named_lambda":"lambda x: "+str(expression),
                "defined_operator_AST":str(expression),
                "numerical_source_error":err}
    except Exception:return None

def best_program(source,action,memory,top=FEATURE_TOP):
    """Human-coded execution of MODEL-SELECTED STRUCTURAL ACTION.

    Returns (best float-source heldout residual, source-valid named lambda).
    Even when rational candidate can't be recovered, its float residual is a
    mathematical SOURCE-only feedback reward for training action policy.
    """
    ys=source["y"];v=source["values"];ids=source["ids"]
    order=source["rank"][:top];spec=[];floatbest=float("inf");winner=None;calls=0
    if action=="RATIONAL_REWRITE":
        # Entire source polynomial/rational candidate, but not gold formula.
        out,secs=rational_fit(source["x"],ys)
        calls=15
        if out:
            try:
                expr=sp.sympify(out["expr"],locals={"x":X})
                fn=sp.lambdify(X,expr,"numpy")
                z=np.broadcast_to(np.asarray(fn(source["x"]),float),ys.shape)
                e=normalized_error(ys,z)
                if e<floatbest:
                    floatbest=e
                    winner={"named_lambda":"lambda x: "+str(expr),
                           "defined_operator_AST":str(expr),"numerical_source_error":e}
            except Exception:pass
        return floatbest,winner,calls
    if action=="REUSE_BINDING":
        for item in memory[:35]:
            calls+=1
            try:
                expr=sp.sympify(item["defined_operator_AST"],locals={"x":X})
                fn=sp.lambdify(X,expr,"numpy")
                with np.errstate(all="ignore"):
                    z=np.broadcast_to(np.asarray(fn(source["x"]),float),ys.shape)
                if not np.all(np.isfinite(z)) or np.max(abs(z))>1e10:continue
                res=fit_two(source,[z])
                if res is None:continue
                p,e=res
                if e<floatbest:
                    floatbest=e
                    validprog=rationalize(source,[expr],p)
                    if validprog:
                        winner={**validprog,"reused_from_memory":True,
                                "source_memory_symbol":item["defined_operator_AST"]}
            except Exception:continue
        return floatbest,winner,calls
    if action=="ADD_BRANCH":
        for q in range(len(order)):
            a=int(order[q])
            for j in range(q+1,len(order)):
                b=int(order[j]);calls+=1
                solved=fit_two(source,[v[:,a],v[:,b]])
                if not solved:continue
                p,e=solved
                if e<floatbest:
                    floatbest=e
                    if e<4e-7:
                        candidate=rationalize(source,[BASIS[ids[a]]["sym"],BASIS[ids[b]]["sym"]],p)
                        if candidate:
                            winner={**candidate,"graph_action":"ADD_BRANCH",
                                    "source_defined_children":[BASIS[ids[a]]["formula"],BASIS[ids[b]]["formula"]]}
        return floatbest,winner,calls
    if action=="MULTIPLY_BRANCH":
        for q in range(len(order)):
            a=int(order[q])
            for j in range(q,len(order)):
                b=int(order[j]);calls+=1
                with np.errstate(all="ignore"):z=v[:,a]*v[:,b]
                if not np.all(np.isfinite(z)) or max(abs(z))>1e10:continue
                solved=fit_two(source,[z])
                if not solved:continue
                p,e=solved
                if e<floatbest:
                    floatbest=e
                    if e<4e-7:
                        expr=BASIS[ids[a]]["sym"]*BASIS[ids[b]]["sym"]
                        candidate=rationalize(source,[expr],p)
                        if candidate:
                            winner={**candidate,"graph_action":"MULTIPLY_BRANCH",
                                    "source_defined_children":[BASIS[ids[a]]["formula"],BASIS[ids[b]]["formula"]]}
        return floatbest,winner,calls
    if action=="COMPOSE_UNARY":
        outer={"SQUARE":(lambda z:z*z,lambda e:e**2),
               "CUBE":(lambda z:z*z*z,lambda e:e**3),
               "SIN":(np.sin,sp.sin),"COS":(np.cos,sp.cos),
               "TANH":(np.tanh,sp.tanh),
               "EXP":(np.exp,sp.exp),"RECIP":(lambda z:1/z,lambda e:1/e)}
        for j in order:
            a=int(j)
            for op,(nfunc,sfunc) in outer.items():
                calls+=1
                with np.errstate(all="ignore",over="ignore"):
                    z=nfunc(v[:,a])
                if not np.all(np.isfinite(z)) or max(abs(z))>1e10:continue
                solved=fit_two(source,[z])
                if not solved:continue
                p,e=solved
                if e<floatbest:
                    floatbest=e
                    if e<4e-7:
                        candidate=rationalize(source,[sfunc(BASIS[ids[a]]["sym"])],p)
                        if candidate:
                            winner={**candidate,"graph_action":"COMPOSE_UNARY",
                                    "source_defined_children":[BASIS[ids[a]]["formula"]],
                                    "learned_chosen_composition_operator":op}
        return floatbest,winner,calls
    raise ValueError("INVALID_SEMANTIC_GRAPH_EDIT_ACTION")

def xaction_features(shape,action):
    one=np.zeros(len(ACTIONS),float);one[ACTIONS.index(action)]=1.0
    return np.r_[shape,one]

def training_policy(source_json):
    data=json.loads(pathlib.Path(source_json).read_text())
    rows=data["train_source_only"]
    assert len(rows)==MAX_SOURCE_ROWS
    rng=np.random.default_rng(TRAIN_SEED)
    examples=[];memory=[];counts=collections.Counter()
    t0=time.process_time()
    for row in rows:
        if not valid(row):continue
        src=source_context(row)
        if src is None:continue
        # Actual bandit exploration: SELF-CHOSEN structural graph-edit actions,
        # rewarded solely on 48 source x-y, NO teacher winner/source gold AST.
        picks=rng.choice(len(ACTIONS),size=REWARD_SAMPLES_PER_TRAIN,replace=False)
        for idx in picks:
            act=ACTIONS[int(idx)]
            error,macro,calls=best_program(src,act,memory)
            counts["verifier_evaluations"]+=calls
            counts["explored_structural_actions"]+=1
            if not np.isfinite(error):error=1e8
            # Numeric source-only bandit reward. Large exact fit positive,
            # graded smooth improvement, no target author expression.
            reward=1/(1+np.log1p(1e4*min(error,1e8)))
            if macro is not None:
                reward=1.0
                counts["source_valid_MACRO_candidates"]+=1
                if len(memory)<60 and all(m["defined_operator_AST"]!=macro["defined_operator_AST"] for m in memory):
                    memory.append(macro)
                    counts["defined_reusable_macros"]+=1
            examples.append({"shape":src["feature"].tolist(),"action":act,
                             "verifier_source_reward":float(reward),
                             "exact_source_only":macro is not None})
    verifier_cpu=time.process_time()-t0
    # Learn conditional *structural action* values from own source task rewards.
    Xtrain=np.asarray([xaction_features(np.array(v["shape"]),v["action"]) for v in examples])
    Ytrain=np.asarray([v["verifier_source_reward"] for v in examples])
    assert len(examples)>100 and len(np.unique(Ytrain))>4
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        policy=MLPRegressor(hidden_layer_sizes=(24,12),random_state=20261023,
                   max_iter=300,learning_rate_init=0.006,alpha=.01)
        t1=time.process_time()
        policy.fit(Xtrain,Ytrain)
        learn_cpu=time.process_time()-t1
    details={"training_numeric_original_only_SHA256":sha(pathlib.Path(source_json).read_bytes()),
        "other_source_original_train_tasks":len(rows),
        "source_reward_samples":len(examples),
        "reward_trajectories_sha256":sha(json.dumps(examples,sort_keys=True).encode()),
        "reward_values_distinct":len(np.unique(Ytrain)),
        "train_cpu_source_oracle_s":verifier_cpu,
        "train_cpu_structural_policy_s":learn_cpu,
        "direct_original_author_formulas_used":False,
        "source_verifier_calls":counts["verifier_evaluations"],
        "self_rewarded_defined_macros":counts["defined_reusable_macros"],
        "training_memory_ast_sha256":sha(json.dumps(memory,sort_keys=True).encode()),
        "learned_action_model_weight_SHA256":sha(json.dumps([v.tolist() for v in policy.coefs_],sort_keys=True).encode()),
        "model_learns":"conditional value of graph ADD/MULTIPLY/COMPOSE/RATIONAL_REWRITE/REUSE actions",
        "human_gives":"primitive semantics, candidate feature pool, rational fit executor, maximum graph depth",
        "source_reward_does_not_equal_original_exact_author_formula_proof":True}
    return policy,memory,details

def evaluate(policy,source,training):
    rng=np.random.default_rng(550732)
    methods=("D_learned_structural_top2","C_nolearn_random2",
             "C_fixed_add_plus_rational","A_full_five_structure_actions")
    results={}
    for method in methods:
        started=time.process_time()
        cases=[];ct=collections.Counter()
        for record in source["source_numeric_without_equations"]:
            if not valid(record):
                cases.append({"id":record["id"],"status":"UNKNOWN_SOURCE","candidate_macros":[],
                              "actions_executed":[],"math_verifier_calls":0});continue
            context=source_context(record)
            if context is None:
                cases.append({"id":record["id"],"status":"UNKNOWN_SOURCE","candidate_macros":[],
                              "actions_executed":[],"math_verifier_calls":0});continue
            if method=="D_learned_structural_top2":
                priorities={a:float(policy.predict([xaction_features(context["feature"],a)])[0]) for a in ACTIONS}
                acts=sorted(ACTIONS,key=lambda a:(-priorities[a],a))[:2]
            elif method=="C_nolearn_random2":
                acts=[ACTIONS[int(v)] for v in rng.choice(len(ACTIONS),size=2,replace=False)]
            elif method=="C_fixed_add_plus_rational":
                acts=["ADD_BRANCH","RATIONAL_REWRITE"]
            else:acts=list(ACTIONS)
            known=[];trials=0;errs={}
            for act in acts:
                error,macro,count=best_program(context,act,training)
                trials+=count
                errs[act]=error if np.isfinite(error) else None
                if macro is not None and macro["named_lambda"] not in {v["named_lambda"] for v in known}:
                    known.append(macro)
            known=known[:12]
            cases.append({"id":record["id"],"status":"SOURCE_VERIFIED" if known else "UNKNOWN",
                         "candidate_macros":known,"actions_executed":acts,
                         "source_numeric_errors_by_action":errs,
                         "math_verifier_calls":trials})
            ct["source_valid_cases"]+=int(bool(known));ct["source_verifier_calls"]+=trials
            ct["source_programs"]+=len(known)
        results[method]={"cases":cases,"source_counts":dict(ct),
                          "test_candidate_CPU_s":time.process_time()-started}
    return results

def train_and_seal(trainpath,sourcepath,outpath):
    policy,mem,train=training_policy(trainpath)
    source=json.loads(pathlib.Path(sourcepath).read_text())
    assert len(source["source_numeric_without_equations"])==32
    assert not any("original_expression" in r for r in source["source_numeric_without_equations"])
    r=evaluate(policy,source,mem)
    res={"schema":"NEUMANN_Q3_ACTUAL_LEARNED_STRUCTURAL_EDIT_POLICY_TENTH32_FIRST.v1",
         "training":train,
         "fresh_external_original_source_only_SHA256":sha(pathlib.Path(sourcepath).read_bytes()),
         "model_makes_graph_topology_action_decisions":True,
         "new_define_named_macro_programs_from_source_only":True,
         "reuse_named_macros_from_other_original_train_sources":True,
         "training_memory_reused_without_original_formula":True,
         "human_implemented_action_semantics_and_candidate_fits":True,
         "unbounded_new_atomic_math_semantics":"NOT_PROVED",
         "actions":list(ACTIONS),
         "methods":r,"global_Q3":"OPEN","G1":"HOLD"}
    sig=save(outpath,res)
    print("Q3_FIRST_EXTERNAL_TENTH32_ACTUALLY_LEARNED_GRAPH_EDIT_STRUCTURE_PREDICTION",json.dumps({
       "sha256":sig,"train_original_numeric_tasks":train["other_source_original_train_tasks"],
       "self_reward_samples":train["source_reward_samples"],
       "reward_verifier_calls":train["source_verifier_calls"],
       "new_named_memory_macros":train["self_rewarded_defined_macros"],
       "train_CPU_s":train["train_cpu_source_oracle_s"]+train["train_cpu_structural_policy_s"],
       "methods":{m:{"source":v["source_counts"],
             "cpu":v["test_candidate_CPU_s"]} for m,v in r.items()}},sort_keys=True),flush=True)

def grade(truthfile,predfile,outfile):
    t=json.loads(pathlib.Path(truthfile).read_text())["private_true_equations"]
    p=json.loads(pathlib.Path(predfile).read_text())
    assert len(t)==32 and len(p["methods"])==4
    original={r["id"]:r for r in t}
    grades={};cases={}
    for name,method in p["methods"].items():
        ct=collections.Counter();rows=[]
        for r in method["cases"]:
            src=original[r["id"]];exact=[]
            try:
                node,var=allowed_formula(src["original_expression"])
                author=calc(node,{var:X},SYM)
                for cand in r["candidate_macros"]:
                    hyp=sp.sympify(cand["defined_operator_AST"],locals={"x":X})
                    if sp.simplify(author-hyp)==0:
                        exact.append(cand)
            except Exception:pass
            ct["all"]+=1;ct["exact"]+=int(bool(exact));ct["unknown"]+=int(not exact)
            if any(c.get("graph_action")=="MULTIPLY_BRANCH" for c in exact):
                ct["true_mult_branch"]+=1
            if any(c.get("graph_action")=="COMPOSE_UNARY" for c in exact):
                ct["true_compose_branch"]+=1
            if any(c.get("reused_from_memory") for c in exact):
                ct["true_reused_previous_named_macro"]+=1
            rows.append({"id":r["id"],"collection":src["collection"],"task_ID":src["task_ID"],
                         "original_expression_SHA256":sha(src["original_expression"].encode()),
                         "status":"COMPLETE_ORIGINAL_SYMBOLICALLY_EXACT" if exact else "UNKNOWN",
                         "original_exact_structural_macros":exact})
        grades[name]=dict(ct);cases[name]=rows
    good={k:{r["id"] for r in v if r["status"]=="COMPLETE_ORIGINAL_SYMBOLICALLY_EXACT"} for k,v in cases.items()}
    learned=good["D_learned_structural_top2"]
    result={"schema":"NEUMANN_Q3_FIRST_INDEPENDENT_AUTHOR_STRUCTURAL_GRAPH_EDIT_VERDICT.v1",
      "sealed_source_only_pred_SHA256":sha(pathlib.Path(predfile).read_bytes()),
      "actual_author_original_gold_SHA256":sha(pathlib.Path(truthfile).read_bytes()),
      "method_source_author_full_expression_grades":grades,
      "all_original32_case_receipts":cases,
      "learned_only_v_random":sorted(learned-good["C_nolearn_random2"]),
      "learned_only_v_fixed":sorted(learned-good["C_fixed_add_plus_rational"]),
      "learned_only_v_ALL5_same_rights":sorted(learned-good["A_full_five_structure_actions"]),
      "trained_new_semantically_atomic_operator":"NOT_PROVED",
      "complete_sota_external_specialist":"NOT_RUN",
      "first_new_original_author_family_different_distribution":"NOT_PROVED",
      "G1":"HOLD","Q3":"OPEN","Q4_total10x":"NOT_PROVED"}
    sig=save(outfile,result)
    print("Q3_FIRST_EXTERNAL_TENTH32_TRUE_AUTHOR_LEARNED_STRUCTURAL_EDIT_EXACT_GRADE",
       json.dumps({"sha256":sig,"grades":grades,
        "learner_only_over_ALL5":len(result["learned_only_v_ALL5_same_rights"]),
        "learner_only_over_fixed":len(result["learned_only_v_fixed"])},sort_keys=True),flush=True)
    assert all(z["all"]==32 for z in grades.values())
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=("infer","grade"))
    for s in ("train","source","truth","pred","out"):p.add_argument("--"+s)
    a=p.parse_args()
    if a.mode=="infer":train_and_seal(a.train,a.source,a.pred)
    else:grade(a.truth,a.pred,a.out)
