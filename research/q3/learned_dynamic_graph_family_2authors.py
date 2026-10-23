"""Q3 discriminative structural GRAPH-EDIT policy trained only on verifiable
numeric source outcomes; first prospective Keijzer7 + Neat5 OTHER AUTHORS.

5 executable human-provided typed graph edit skill families:
  RECURSIVE_POLYNOMIAL (MUL_POWER, ADD_TERM, rationalize)
  PRODUCT_OR_SUM_TRIG (APPLY_SIN, APPLY_COS, MULTIPLY_NODES, ADD)
  LOG_SUM (DEFINE_LOG(POLY), ADD, REUSE)
  EXP_ROOT_COMPOSE (APPLY_EXP/ROOT to varied input nodes)
  OLD_SAFE (fixed prior SAFE source solver).

All complete expressions built by programmable source graph edits from
smaller atoms (not hard-coded external original formulas). The trained
small MLP learns *which family of graph constructions to EXECUTE* using
self-source numeric reward from independent synthetic original tasks.
Core leaf unary functions are human-given and bounded; neither neural
atomic semantic invention nor CEGIS novelty is claimed.

Each method has same 48 x-y source; test first prediction SHA sealed before
gold original author analytic expression is delivered to grade job.
"""
import argparse,collections,hashlib,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from sklearn.neural_network import MLPRegressor
from erbench_original_eleventh import sha,save
from learned_additive_macro_ninth32 import original_shape
from dynamic_source_ast_graph_livermore_first8 import search
from learned_derived_power_eleventh32 import eval_action

X=sp.Symbol("x")
ACTIONS=("POLYNOMIAL","TRIG_PRODUCT","LOG_SUM","EXP_ROOT","SAFE")
TRAIN_SEED=10172026
PROBE_SHAPE=(48,)

def source_valid(r):
    return "x" in r and original_shape(r.get("x",[]),r.get("y",[])) is not None

def numerical_error(y,z):
    with np.errstate(all="ignore"):
        rel=np.abs(y-z)/(1+np.abs(y))
    return float(np.max(rel)) if np.all(np.isfinite(rel)) else float("inf")

def make_grammar(family):
    # Only SYMBOLIC atoms and graph rewrite operations, not any task solution.
    # Keep the same registry independent of first published Keijzer/Neat truth.
    x=X
    if family=="TRIG_PRODUCT":
        sines=[sp.sin(x**i) for i in range(1,6)]
        cosines=[sp.cos(x**i) for i in range(1,6)]
        combined=[sp.sin(x**i+x**j) for i in range(1,4) for j in range(i+1,5)]
        products=[a*b for a in sines for b in cosines]
        return tuple(dict.fromkeys(sines+cosines+combined+products))
    if family=="LOG_SUM":
        inners=[x**d+1 for d in range(1,7)]
        inners +=[x**d+x**e for d in range(2,7) for e in range(1,d)]
        inners +=[x**d-1 for d in range(1,5)]
        return tuple(dict.fromkeys(sp.log(z) for z in inners))
    if family=="EXP_ROOT":
        powers=[sp.Rational(-2),sp.Rational(-1),sp.Rational(-1,2),
                sp.Rational(1,2),sp.Rational(1),sp.Rational(2)]
        exps=[sp.exp(q*x**d) for q in powers for d in range(1,5)]
        roots=[sp.Pow(x+shift,p) for shift in (0,1,2)
               for p in (sp.Rational(1,2),sp.Rational(1,3),
                         sp.Rational(1,5),sp.Rational(2,3))]
        return tuple(dict.fromkeys(exps+roots))
    raise ValueError(family)

GRAMMARS={family:make_grammar(family) for family in ("TRIG_PRODUCT","LOG_SUM","EXP_ROOT")}
assert all(len(g)>=20 for g in GRAMMARS.values())

def exact_fit(xs,ys,names,vals,counter):
    counter["fits"]+=1
    A=np.column_stack(list(vals)+[np.ones(48)])
    try:
        coefficients=np.linalg.lstsq(A[:32],ys[:32],rcond=1e-11)[0]
        if not np.all(np.isfinite(coefficients)) or max(abs(coefficients))>1e10:return None,None
        float_error=numerical_error(ys,A@coefficients)
        if float_error>1e-6:return float_error,None
        Q=[sp.Rational(float(c)).limit_denominator(1000) for c in coefficients]
        ast=sp.Add(*(Q[i]*names[i] for i in range(len(names))),Q[-1])
        f=sp.lambdify(X,ast,"numpy")
        with np.errstate(all="ignore"):
            corrected=np.broadcast_to(np.asarray(f(xs),float),ys.shape)
        corrected_error=numerical_error(ys,corrected)
        if corrected_error>1e-8:return float_error,None
        return corrected_error,{"defined_operator_AST":str(ast),
           "named_lambda":"lambda x: "+str(ast),
           "defined_macro_graph_children":[str(a) for a in names],
           "source_numeric_error":corrected_error,
           "author_formula_access_during_source_fit":False}
    except Exception:return None,None

def compose_from_grammar(row,family):
    """Source-only generate nodes by graph edits, rank and fit one/two nodes.

    Does NOT select any complete expressions using gold expression labels.
    Model action = which grammar expansion family to execute.
    """
    if not source_valid(row):return None,0,0
    x=np.asarray(row["x"],float);y=np.asarray(row["y"],float)
    base=[];v=[];calls=collections.Counter()
    for expr in GRAMMARS[family]:
        calls["graph_nodes"]+=1
        try:
            fn=sp.lambdify(X,expr,modules="numpy")
            with np.errstate(all="ignore"):
                out=np.broadcast_to(np.asarray(fn(x),float),x.shape)
            if not np.all(np.isfinite(out)) or max(abs(out))>1e10 or np.std(out[:32])<1e-12:
                continue
            base.append(expr);v.append(out)
        except Exception:continue
    if not base:return None,calls["fits"],calls["graph_nodes"]
    mat=np.column_stack(v)
    centered=mat[:32]-np.mean(mat[:32],axis=0)
    norms=np.linalg.norm(centered,axis=0)
    score=abs(centered.T@(y[:32]-np.mean(y[:32])))/np.maximum(norms,1e-12)
    best=float("inf");champ=None
    ranked=np.argsort(-score,kind="stable")[:min(22,len(base))]
    for j in ranked:
        e,macro=exact_fit(x,y,[base[j]],[mat[:,j]],calls)
        if e is not None and e<best:
            best=e
            if macro:champ=macro
    if champ:return champ,calls["fits"],calls["graph_nodes"]
    # Joint two-branch graph ADD, never provided as complete expression.
    # Use all source feature correlations; rank exact optimal pair gains.
    Z=centered/np.maximum(norms,1e-12)
    gram=Z.T@Z
    c=Z.T@(y[:32]-np.mean(y[:32]))
    with np.errstate(all="ignore"):
        denom=1-gram**2
        gains=np.divide(c[:,None]**2+c[None,:]**2-2*gram*c[:,None]*c[None,:],
              denom,out=np.full_like(gram,-np.inf),where=denom>1e-11)
    gains=np.where(np.triu(np.ones_like(gains,dtype=bool),1),gains,-np.inf)
    for idx in np.argsort(-gains.ravel(),kind="stable")[:min(140,gains.size)]:
        if not np.isfinite(gains.flat[int(idx)]):break
        a,b=np.unravel_index(int(idx),gains.shape)
        e,macro=exact_fit(x,y,[base[a],base[b]],[mat[:,a],mat[:,b]],calls)
        if e is not None and e<best:
            best=e
            if macro:champ=macro
        if champ:break
    return champ,calls["fits"],calls["graph_nodes"]

def execute(row,action):
    if not source_valid(row):return None,0,0
    if action=="POLYNOMIAL":
        r=search(row,mode="POLYNOMIAL_ONLY")
        return r["source_verified_program"],r["fitting_calls"],r["candidate_graphs_constructed"]
    if action=="SAFE":
        _,programs,calls=eval_action(row,"SAFE")
        return programs[0] if programs else None,calls,0
    return compose_from_grammar(row,action)

def shape_action(shape,action):
    bits=np.zeros(len(ACTIONS),float);bits[ACTIONS.index(action)]=1
    return np.r_[shape,bits]

def train_synthetic():
    """Synthetic original PROGRAMS constructed independently from test author.

    NO labels from generator formula passed to train. Training TARGET is
    measured source success/cost of EXECUTING each candidate graph family.
    60 different numeric tasks, ~300 individual source checks.
    """
    rng=np.random.default_rng(TRAIN_SEED)
    samples=[];counts=collections.Counter();reward_rows=[]
    for family in ("POLYNOMIAL","TRIG_PRODUCT","LOG_SUM","EXP_ROOT","SAFE"):
        for case in range(12):
            left,right=(.3,1.9) if family in ("LOG_SUM","EXP_ROOT") else (-.9,.9)
            xs=rng.uniform(left,right,48)
            if family=="POLYNOMIAL":
                degree=int(rng.integers(2,8))
                cc=[int(rng.integers(-3,4)) for _ in range(degree)]
                yy=sum(cc[k-1]*xs**k for k in range(1,degree+1))+int(rng.integers(-2,3))
            elif family=="TRIG_PRODUCT":
                a,b=int(rng.integers(1,5)),int(rng.integers(1,5))
                yy=np.sin(xs**a)*np.cos(xs**b)*int(rng.choice([-3,-2,1,2,3]))+int(rng.integers(-2,3))
            elif family=="LOG_SUM":
                a,b=int(rng.integers(1,5)),int(rng.integers(1,5))
                yy=np.log(xs**a+1)+np.log(xs**b+xs)
            elif family=="EXP_ROOT":
                a,b=int(rng.integers(1,4)),int(rng.choice([-2,-1,1,2]))
                yy=int(rng.choice([-2,-1,1,2]))*np.exp(b*xs**a)+int(rng.integers(-2,3))
            else:
                a,b=int(rng.integers(-3,4)),int(rng.integers(-3,4))
                yy=(a*xs+b)/(1+xs**2)
            if not np.all(np.isfinite(yy)):continue
            row={"id":f"synthetic_{family}_{case}","x":xs.tolist(),"y":yy.tolist()}
            if not source_valid(row):continue
            samples.append((family,row))
    t0=time.process_time()
    for generator_family,row in samples:
        context=original_shape(row["x"],row["y"])
        for action in ACTIONS:
            prog,ver,graphs=execute(row,action)
            counts["verifier_calls"]+=ver
            counts["generated_graph_nodes"]+=graphs
            # Gold syntax from training generator is never consulted.
            # Binary SOURCE numerical proof reward, independent of generator.
            outcome=float(prog is not None)
            reward_rows.append({"source_id":row["id"],"shape":context.tolist(),
                "sampled_action":action,"source_verified_reward":outcome,
                "source_verifier_calls":ver})
    source_cpu=time.process_time()-t0
    features=np.asarray([shape_action(np.asarray(r["shape"]),r["sampled_action"])
                          for r in reward_rows])
    targets=np.asarray([r["source_verified_reward"] for r in reward_rows])
    assert len(reward_rows)>=240 and len(set(targets))==2
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m=MLPRegressor(hidden_layer_sizes=(48,24),random_state=TRAIN_SEED,
               max_iter=380,learning_rate_init=.006,alpha=.025)
        t=time.process_time();m.fit(features,targets);train_cpu=time.process_time()-t
    meta={"source_train_programs":len(samples),
      "actual_source_self_reward_action_rollouts":len(reward_rows),
      "source_verifier_calls":counts["verifier_calls"],
      "constructed_training_graph_nodes":counts["generated_graph_nodes"],
      "source_verifier_train_cpu":source_cpu,
      "trained_neural_CPU":train_cpu,
      "training_trace_sha256":sha(json.dumps(reward_rows,sort_keys=True).encode()),
      "trained_neural_weight_SHA256":sha(json.dumps([x.tolist() for x in m.coefs_],sort_keys=True).encode()),
      "learned_program_origin":"independent synthetic numeric x-y, NOT Keijzer or Neat author true formulas",
      "trained_action_value_by_family":{action:{
             "source_positive":sum(r["source_verified_reward"]==1 for r in reward_rows if r["sampled_action"]==action)}
             for action in ACTIONS}}
    return m,meta

def infer(src_path,out_path):
    model,training=train_synthetic()
    source=json.loads(pathlib.Path(src_path).read_text())
    rows=source["source_numeric_without_equations"]
    assert len(rows)==12 and all("original_expression" not in r for r in rows)
    methods=("D_NEURAL_TOP2_GRAPH_FAMILIES","C_FIXED_POLY_SAFE",
             "C_FIXED_TRIG_LOG","C_FIXED_EXP_SAFE","C_RANDOM_TWO",
             "A_ALL_SAME_GRAPH_ACTIONS")
    rng=np.random.default_rng(6224)
    arm={}
    for name in methods:
        first=time.process_time();cases=[];ct=collections.Counter()
        for row in rows:
            if not source_valid(row):
                cases.append({"id":row["id"],"status":"UNKNOWN_INVALID_SOURCE",
                   "selected_graph_edit_families":[],"source_valid_defined_macros":[],
                   "verifier_calls":0,"constructed_graph_nodes":0})
                continue
            if name=="D_NEURAL_TOP2_GRAPH_FAMILIES":
                profile=original_shape(row["x"],row["y"])
                pred={a:float(model.predict([shape_action(profile,a)])[0]) for a in ACTIONS}
                chosen=sorted(ACTIONS,key=lambda a:(-pred[a],a))[:2]
            elif name=="C_FIXED_POLY_SAFE":chosen=["POLYNOMIAL","SAFE"]
            elif name=="C_FIXED_TRIG_LOG":chosen=["TRIG_PRODUCT","LOG_SUM"]
            elif name=="C_FIXED_EXP_SAFE":chosen=["EXP_ROOT","SAFE"]
            elif name=="C_RANDOM_TWO":chosen=list(rng.choice(ACTIONS,2,replace=False))
            else:chosen=list(ACTIONS)
            programs=[];calls=0;nodes=0
            for action in chosen:
                proposal,n,g=execute(row,action)
                calls+=n;nodes+=g
                if proposal is not None and proposal["named_lambda"] not in [x["named_lambda"] for x in programs]:
                    programs.append({**proposal,"structural_action_family":action})
            ct["verifier_calls"]+=calls;ct["new_graph_nodes"]+=nodes
            ct["source_valid_task"]+=int(bool(programs))
            cases.append({"id":row["id"],"status":"SOURCE_VERIFIED" if programs else "UNKNOWN",
                "selected_graph_edit_families":chosen,
                "source_valid_defined_macros":programs,
                "verifier_calls":calls,"constructed_graph_nodes":nodes})
        arm[name]={"cases":cases,"source_counts":dict(ct),"eval_CPU_s":time.process_time()-first}
    receipt={"schema":"NEUMANN_Q3_FIRST_TWO_OTHER_AUTHOR_FAMILIES_NEURAL_RECURSIVE_GRAPH_EDIT.v1",
       "first_true_author_keijzer_neat_numeric_only_sha256":sha(pathlib.Path(src_path).read_bytes()),
       "synthetic_neural_training":training,
       "trained_policy_chooses_graph_structure_expansion":True,
       "human_given_program_primitive_meanings_and_structure_edit_schemas":True,
       "all_same_model_input_rights_per_method":True,
       "methods":arm,"G1":"HOLD","Q3_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN"}
    digest=save(out_path,receipt)
    print("Q3_FIRST_NEW_KEIJZER7_NEAT5_NEURAL_GRAPH_EDIT_FAMILY_SOURCE_PROPOSALS",json.dumps({
       "sha256":digest,"training":training,
       "methods":{a:{"s":r["source_counts"],"cpu":r["eval_CPU_s"]} for a,r in arm.items()}},sort_keys=True),flush=True)

def grade(gold_path,pred_path,out_path):
    g=json.loads(pathlib.Path(gold_path).read_text())["private_true_equations"]
    p=json.loads(pathlib.Path(pred_path).read_text())
    assert len(g)==12
    true={r["id"]:r for r in g}
    methods={};original={}
    for name,arm in p["methods"].items():
        counts=collections.Counter();cases=[]
        for source in arm["cases"]:
            original_row=true[source["id"]]
            exact=[]
            # The published-generator sympy uses real=True for x; all
            # candidate programs use plain x. Substitute identical symbols
            # before strict whole analytic original equality, never grade
            # two physically distinct SymPy x objects as mismatch.
            f=sp.sympify(original_row["author_full_expression_sympy"],
                locals={"x":sp.Symbol("x",real=True)}).subs(
                    sp.Symbol("x",real=True),X)
            for prop in source["source_valid_defined_macros"]:
                try:
                    h=sp.sympify(prop["defined_operator_AST"],locals={"x":X})
                    if sp.simplify(f-h)==0:exact.append(prop)
                except Exception:pass
            counts["all"]+=1;counts["author_full_exact"]+=int(bool(exact))
            counts["unknown"]+=int(not exact)
            cases.append({"id":source["id"],"published_original_name":original_row["task_ID"],
                 "first_author_gold_sha256":sha(original_row["original_expression"].encode()),
                 "status":"WHOLE_REAL_AUTHOR_EXACT" if exact else "UNKNOWN",
                 "certified_source_built_macros":exact})
        methods[name]=dict(counts);original[name]=cases
    solved={k:{r["id"] for r in v if r["status"]=="WHOLE_REAL_AUTHOR_EXACT"} for k,v in original.items()}
    D=solved["D_NEURAL_TOP2_GRAPH_FAMILIES"]
    other=set.union(*(v for k,v in solved.items() if k.startswith("C_")))
    verdict={"schema":"NEUMANN_Q3_FIRST_INDEPENDENT_KEIJZER_NEAT_REAL_ORIGINAL_AUTHOR_FULL_GRADE.v1",
      "frozen_graph_policy_source_proposals_SHA256":sha(pathlib.Path(pred_path).read_bytes()),
      "private_published_author_original_full_truth_sha256":sha(pathlib.Path(gold_path).read_bytes()),
      "method_full_author_symbolic_exact":methods,"all_original_cases":original,
      "neural_only_over_union_ALL_fixedbudget_no_learners":sorted(D-other),
      "neural_only_over_FULL_classical":sorted(D-solved["A_ALL_SAME_GRAPH_ACTIONS"]),
      "G1":"HOLD","Q3_GLOBAL":"OPEN","Q4_ALLIN10X":"UNPROVEN"}
    digest=save(out_path,verdict)
    print("Q3_FIRST_NEW_KEIJZER7_NEAT5_WHOLE_AUTHORED_FORMULA_EXACT_GRADE",json.dumps({
      "sha256":digest,"scores":methods,"learner_only_over_no_learn_union":len(verdict["neural_only_over_union_ALL_fixedbudget_no_learners"]),
      "learner_only_over_all":len(verdict["neural_only_over_FULL_classical"])},sort_keys=True),flush=True)
    assert all(x["all"]==12 for x in methods.values())

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--mode",choices=("infer","grade"),required=True)
    for s in ("source","truth","pred","out"):a.add_argument("--"+s)
    p=a.parse_args()
    if p.mode=="infer":infer(p.source,p.pred)
    else:grade(p.truth,p.pred,p.out)
