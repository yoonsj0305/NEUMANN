"""Learn which graph STRUCTURE action to use including dynamically defined
EXP(LOG(positive integer base)*integer slope*x) executable macros.

Train ONLY on 128 other author numeric x-y sources, not original functions.
Self-reward contextual MLP predicts POWER_ONE, POWER_TWO or SAFE_ADD_RATIONAL.
Original author true function is physically withheld until separate grader.
Full same rights classical A evaluates all action types. Neural-only beyond A
is NOT possible under this identical action and local candidate grammar.
"""
import argparse,collections,hashlib,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from sklearn.neural_network import MLPRegressor
from erbench_original_eleventh import sha,save,allowed_formula,calc,SYM
from learned_additive_macro_ninth32 import original_shape,X
from exp_log_derived_power_core import macro,valid,best_power,old_safe,COMBINATIONS
ACTIONS=("POWER_ONE","POWER_TWO","SAFE")
SEED=30817

def feature(shape,action):
    f=np.zeros(len(ACTIONS))
    f[ACTIONS.index(action)]=1
    return np.r_[shape,f]
def reward(err,valid_macro):
    if valid_macro:return 1.
    if not np.isfinite(err):return 0.
    return float(1/(1+np.log1p(1e4*min(err,1e12))))
def eval_action(row,act):
    if act=="POWER_ONE":
        e,m,n=best_power(row,1)
        return e,[m] if m else [],n
    if act=="POWER_TWO":
        e,m,n=best_power(row,2)
        return e,[m] if m else [],n
    return old_safe(row)

def train(path):
    rows=json.loads(pathlib.Path(path).read_text())["train_source_only"]
    assert len(rows)==128
    rollouts=[];memory=[];calls=0
    t0=time.process_time()
    rng=np.random.default_rng(SEED)
    for row in rows:
        if not valid(row):continue
        acts=list(ACTIONS);rng.shuffle(acts)
        for act in acts:
            error,programs,n=eval_action(row,act)
            calls+=n
            for item in programs:
                if len(memory)<75 and item["named_lambda"] not in [v["named_lambda"] for v in memory]:
                    memory.append(item)
            rollouts.append({"source":row["id"],"numeric_shape":original_shape(row["x"],row["y"]).tolist(),
                 "action":act,"source_reward":reward(error,bool(programs)),
                 "numeric_source_macro_proven":bool(programs)})
    source_cpu=time.process_time()-t0
    assert len(rollouts)>=100
    x=np.asarray([feature(v["numeric_shape"],v["action"]) for v in rollouts])
    y=np.asarray([v["source_reward"] for v in rollouts])
    assert len(set(y))>3
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model=MLPRegressor(hidden_layer_sizes=(24,12),random_state=SEED,
                          max_iter=350,learning_rate_init=.005,alpha=.02)
        t=time.process_time();model.fit(x,y);mlpcpu=time.process_time()-t
    info={"training_numeric_source_sha256":sha(pathlib.Path(path).read_bytes()),
      "numeric_reward_only_original_task_count":128,
      "actual_source_reward_rollouts":len(rollouts),
      "source_reward_verifier_calls":calls,
      "source_reward_training_CPU_s":source_cpu,
      "actual_neural_structural_MLP_CPU_s":mlpcpu,
      "own_source_verified_named_macro_count":len(memory),
      "learned_graph_action_values":{a:{"source_verified_cases":sum(q["numeric_source_macro_proven"] for q in rollouts if q["action"]==a),
          "mean_reward":float(np.mean([q["source_reward"] for q in rollouts if q["action"]==a]))} for a in ACTIONS},
      "training_rewards_SHA256":sha(json.dumps(rollouts,sort_keys=True).encode()),
      "trained_weights_SHA256":sha(json.dumps([z.tolist() for z in model.coefs_],sort_keys=True).encode()),
      "memory_SHA256":sha(json.dumps(memory,sort_keys=True).encode()),
      "no_true_author_original_formula_labels_used":True,
      "human_semantic_primitives":"EXP,LOG,ADD,MUL and bounded positive integer parameters",
      "trained_action":"CHOOSE_DERIVE_ONE_TWO_OR_SAFE",
      "original_cross_family_new_atomic_semantics":"NOT_PROVED"}
    return model,info

def first_source(trainfile,sourcefile,out):
    model,meta=train(trainfile)
    originals=json.loads(pathlib.Path(sourcefile).read_text())["source_numeric_without_equations"]
    assert len(originals)==32
    methods=("D_learned_derived_power_top2","C_safe_add_rational",
       "C_untrained_power_one_and_two","C_random_two","A_full_same_actions")
    rng=np.random.default_rng(71701)
    result={}
    for method in methods:
        t0=time.process_time();rows=[];total=collections.Counter()
        for source in originals:
            if not valid(source):
                rows.append({"id":source["id"],"status":"UNKNOWN_SOURCE",
                    "graph_actions":[],"source_proposals":[],"source_verifier_calls":0})
                continue
            if method=="D_learned_derived_power_top2":
                shape=original_shape(source["x"],source["y"])
                scores={a:float(model.predict([feature(shape,a)])[0]) for a in ACTIONS}
                actions=sorted(ACTIONS,key=lambda a:(-scores[a],a))[:2]
            elif method=="C_safe_add_rational":actions=["SAFE"]
            elif method=="C_untrained_power_one_and_two":actions=["POWER_ONE","POWER_TWO"]
            elif method=="C_random_two":actions=[ACTIONS[int(k)] for k in rng.choice(len(ACTIONS),size=2,replace=False)]
            else:actions=list(ACTIONS)
            proposals=[];ncalls=0
            for act in actions:
                _,found,n=eval_action(source,act)
                ncalls+=n
                for p in found:
                    if p["named_lambda"] not in [e["named_lambda"] for e in proposals]:
                        proposals.append(p)
            rows.append({"id":source["id"],"status":"VALID_SOURCE" if proposals else "UNKNOWN",
                "graph_actions":actions,"source_proposals":proposals,"source_verifier_calls":ncalls})
            total["math_oracle_calls"]+=ncalls
            total["source_macros"]+=len(proposals)
            total["task_with_source_macro"]+=int(bool(proposals))
        result[method]={"cases":rows,"source_totals":dict(total),"inference_CPU_s":time.process_time()-t0}
    record={"schema":"NEUMANN_Q3_FIRST_ELEVENTH32_LEARNED_INDUCED_EXPLOG_POWER_MACROS.v1",
        "training":meta,
        "eleventh32_new_original_numeric_only_SHA256":sha(pathlib.Path(sourcefile).read_bytes()),
        "derived_exp_log_compilation_exact_for_all_75_parameter_pairs":all(
             sp.powdenest(sp.exp(sp.Integer(k)*X*sp.log(sp.Integer(b))),force=True)==
             sp.Pow(sp.Integer(b),sp.Integer(k)*X) for b,k in COMBINATIONS),
        "derived_named_reusable_operator_language":"lambda x: exp(log(b)*k*x) compiled to b**(k*x), k integer, b positive integer",
        "program_structure_learned_to_choose_action":True,
        "not_learned_new_atomic_primitive":True,
        "methods":result,
        "G1":"HOLD","Q3_global":"OPEN","Q4_total_10x":"OPEN"}
    digest=save(out,record)
    print("Q3_ELEVENTH32_INDUCED_EXPLOG_DERIVED_OPERATOR_SEALED_BEFORE_AUTHOR_GRADE",
       json.dumps({"sha256":digest,
         "reward_source_calls":meta["source_reward_verifier_calls"],
         "train_CPU":meta["source_reward_training_CPU_s"]+meta["actual_neural_structural_MLP_CPU_s"],
         "named_operators":meta["own_source_verified_named_macro_count"],
         "methods":{k:{"CPU":v["inference_CPU_s"],"source":v["source_totals"]} for k,v in result.items()}},sort_keys=True),flush=True)

def independent_grade(truthfile,predfile,out):
    true=json.loads(pathlib.Path(truthfile).read_text())["private_true_equations"]
    source=json.loads(pathlib.Path(predfile).read_text())
    assert len(true)==32
    t={r["id"]:r for r in true}
    grades={};cases={}
    for method,m in source["methods"].items():
        totals=collections.Counter();record=[]
        for entry in m["cases"]:
            original=t[entry["id"]];exact=[]
            try:
                tree,var=allowed_formula(original["original_expression"])
                f=calc(tree,{var:X},SYM)
                for cand in entry["source_proposals"]:
                    g=sp.sympify(cand["named_lambda"].removeprefix("lambda x: "),locals={"x":X})
                    if sp.simplify(f-g)==0:exact.append(cand)
            except Exception:pass
            totals["all"]+=1;totals["exact"]+=int(bool(exact))
            totals["unknown"]+=int(not exact)
            totals["native_derived_exp_log_exact"]+=int(any("derived_EXPLOG_macros" in x for x in exact))
            record.append({"id":entry["id"],"original":original["collection"]+":"+original["task_ID"],
              "original_formula_sha256":sha(original["original_expression"].encode()),
              "status":"WHOLE_ORIGINAL_AUTHOR_PROVED" if exact else "UNKNOWN",
              "certified_named_macros":exact})
        grades[method]=dict(totals);cases[method]=record
    solved={k:{z["id"] for z in v if z["status"]=="WHOLE_ORIGINAL_AUTHOR_PROVED"} for k,v in cases.items()}
    d=solved["D_learned_derived_power_top2"]
    output={"schema":"NEUMANN_Q3_FIRST_ELEVENTH32_DERIVED_MACROS_NATIVE_FULL_AUTHOR_GRADE.v1",
      "first_source_pred_SHA256":sha(pathlib.Path(predfile).read_bytes()),
      "sealed_author_original_truth_SHA256":sha(pathlib.Path(truthfile).read_bytes()),
      "grades":grades,"cases":cases,
      "learned_sole_originals_v_previous_safe_baseline":sorted(d-solved["C_safe_add_rational"]),
      "learned_sole_originals_v_same_rights_FULL":sorted(d-solved["A_full_same_actions"]),
      "learned_sole_originals_v_random":sorted(d-solved["C_random_two"]),
      "new_atomic_semantics":"NOT_PROVED",
      "G1":"HOLD","Q3":"OPEN","frontier_allin10x":"NOT_PROVED"}
    digest=save(out,output)
    print("Q3_ELEVENTH32_INDEPENDENT_REAL_AUTHOR_EXACT_EXPLOG_MACRO_GRADE",
       json.dumps({"sha256":digest,"grade":grades,
         "new_over_safe":len(output["learned_sole_originals_v_previous_safe_baseline"]),
         "new_over_full":len(output["learned_sole_originals_v_same_rights_FULL"])},sort_keys=True),flush=True)
    assert all(v["all"]==32 for v in grades.values())
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("infer","grade"),required=True)
    for k in ("train","source","truth","pred","out"):parser.add_argument("--"+k)
    o=parser.parse_args()
    if o.mode=="infer":first_source(o.train,o.source,o.pred)
    else:independent_grade(o.truth,o.pred,o.out)
