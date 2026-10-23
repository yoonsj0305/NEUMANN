"""NEUMANN Q3 independent Actions Keijzer-6 numerical self-reward FOLD-SUM study.

Modes run as separate CI jobs:
prepare: published author original H_n in physically separated truth artifact;
infer: train ONLY on synthetic numeric sources; infer on first50 source;
grade: open true author recurrence and exact heldout 51..120 AFTER source saved.

FOLD_SUM, first difference and reciprocal candidate grammar are HUMAN given.
The neural MLP only learns which structural representation to choose.
"""
import argparse,collections,hashlib,json,pathlib,pickle,time
from fractions import Fraction
import numpy as np
import sympy as sp
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

N=sp.Symbol("n",integer=True,positive=True)
K=sp.Symbol("k",integer=True,positive=True)
SEED=197311
IDENT=hashlib.sha256(b"PUBLISHED_GPBENCHMARK_KEIJZER6_HARMONIC_N_POSITIVE_INTEGERS").hexdigest()[:24]
def sha(b):return hashlib.sha256(b).hexdigest()
def write(path,obj):
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    return sha(p.read_bytes())
def original_preparation(args):
    h=Fraction(0,1);values=[]
    for n in range(1,51):
        h+=Fraction(1,n);values.append(float(h))
    source={"schema":"KEIJZER6_SOURCE_NUMERIC_ONLY.v1",
         "source_numeric_without_equations":[{"id":IDENT,"x":list(range(1,51)),"y":values}],
         "published_benchmark":"Keijzer-6 EuroGP2003, n1..50 source, n1..120 test",
         "original_author_truth_in_source":False}
    held=[];h=Fraction(0,1)
    for n in range(1,121):
        h+=Fraction(1,n)
        if n>=51:held.append({"n":n,"num":str(h.numerator),"den":str(h.denominator)})
    true={"schema":"KEIJZER6_PUBLISHED_TRUE_AUTHOR.v1","source_id":IDENT,
          "true_function":"harmonic(n)","true_recurrence":"f(n)-f(n-1)=1/n",
          "first_initial_value":"1","domain":"positive integers",
          "heldout_exact_51_120":held}
    source_sha=write(args.source,source);true_sha=write(args.truth,true)
    print("Q3_KEIJZER6_CI_SOURCE_AND_TRUE_AUTHOR_PHYSICALLY_SEPARATED",json.dumps(
         {"source_sha":source_sha,"private_author_sha":true_sha,"original_source_points":50,
          "heldout_exact_rationals":70},sort_keys=True),flush=True)
def valid(row):
    try:
        x=np.asarray(row["x"],float);y=np.asarray(row["y"],float)
        return len(x)==len(y)==50 and x[0]==1 and np.all(np.diff(x)==1) and np.all(np.isfinite(y))
    except Exception:return False
def fvec(row):
    y=np.asarray(row["y"],float);d=np.diff(y)
    slog=lambda z:float(np.sign(z)*np.log1p(abs(z)))
    ratio=lambda a,b:float(np.clip(a/max(abs(b),1e-12),-200,200))
    return np.asarray([slog(y[0]),slog(y[-1]),slog(y[-1]-y[0]),
         slog(d[0]),slog(d[-1]),ratio(d[-1],d[0]),ratio(d[1],d[0]),
         ratio(d[-1],d[-2]),float(np.mean(d>0)),float(np.mean(np.diff(d)>0)),
         slog(np.max(abs(np.diff(d)))),slog(np.max(abs(d)))],float)
def maxerr(actual,pred):
    y=np.asarray(actual,float);v=np.asarray(pred,float)
    if y.shape!=v.shape or not np.all(np.isfinite(v)):return float("inf")
    return float(np.max(abs(v-y)/(1+abs(y))))
def direct(row):
    if not valid(row):return None,0
    x=row["x"];y=row["y"];calls=0
    for degree in range(7):
        calls+=1
        try:
            xs=[sp.Integer(int(v)) for v in x[:degree+1]]
            ys=[sp.Rational(float(v)).limit_denominator(10000) for v in y[:degree+1]]
            expr=sp.interpolate(list(zip(xs,ys)),N)
            fun=sp.lambdify(N,expr,"numpy")
            err=maxerr(y,np.broadcast_to(fun(np.asarray(x,float)),(50,)))
            if err<1e-10:return {"status":"SOURCE_VALID","ast":{"node":"POLYNOMIAL","expr":str(expr)},
                                "source_error":err},calls
        except Exception:continue
    return None,calls
def fold(row):
    if not valid(row):return None,0
    x=np.asarray(row["x"],int);y=np.asarray(row["y"],float)
    differences=np.diff(y);n=x[1:];calls=0
    for p in (1,2,3):
        for b in range(-2,8):
            if np.min(x+b)<=0:continue
            calls+=1
            a=sp.Rational(float(np.median(differences[:25]*(n[:25]+b).astype(float)**p))).limit_denominator(1000)
            if not a:continue
            predicted=float(a)/(n+b).astype(float)**p
            error=maxerr(differences,predicted)
            if error>1e-11:continue
            initial=sp.Rational(float(y[0])).limit_denominator(100000)
            recovered=np.r_[float(initial),float(initial)+np.cumsum(predicted)]
            numeric_error=maxerr(y,recovered)
            if numeric_error>1e-10:continue
            body={"node":"FOLD_SUM","start":int(x[0])+1,"stop":"n","op":"PLUS",
                  "base":str(initial),"term":{"node":"RECIPROCAL_SHIFT_POWER",
                             "numerator":str(a),"offset":b,"power":p}}
            expr=str(initial+sp.Sum(a/(K+sp.Integer(b))**p,(K,int(x[0])+1,N)))
            name="M_"+sha(expr.encode())[:10]
            return {"status":"SOURCE_VALID","ast":{"node":"DEFINE_MACRO",
                  "name":name,"params":["n"],"body":body},
                  "named_symbolic_program":expr,"source_error":numeric_error,
                  "delta_source_error":error},calls
    return None,calls
def training_rows():
    rng=np.random.default_rng(SEED);rows=[]
    for j in range(112):
        n=np.arange(1,51,dtype=float)
        if j%2==0:
            degree=int(rng.integers(1,6))
            coefficients=rng.integers(-4,5,size=degree+1)
            if not np.any(coefficients[1:]):coefficients[1]=1
            y=sum(float(coefficients[k])*n**k for k in range(degree+1))
        else:
            b=int(rng.integers(1,7)) # Keijzer b=0 NOT in training
            p=int(rng.integers(1,4))
            a=int(rng.choice([-3,-2,-1,1,2,3]))
            c=int(rng.integers(-3,4))
            y=c+np.cumsum(a/(n+b)**p)
        rows.append({"id":sha(f"{SEED}_SYNTHETIC_{j}".encode())[:20],
                     "x":list(range(1,51)),"y":y.tolist()})
    return rows
def source_only_inference(args):
    source_bytes=pathlib.Path(args.source).read_bytes()
    source=json.loads(source_bytes)
    assert len(source["source_numeric_without_equations"])==1
    row=source["source_numeric_without_equations"][0]
    assert row["id"]==IDENT and valid(row)
    assert "true_function" not in source and "harmonic" not in source_bytes.decode()
    train=training_rows();features=[];labels=[];evidence=[];n_calls=0
    train_start=time.process_time()
    for task in train:
        one,dc=direct(task);two,rc=fold(task);n_calls+=dc+rc
        exists_d=one is not None;exists_f=two is not None
        if exists_f and not exists_d:act="DEFINE_FOLD_SUM"
        elif exists_d:act="DIRECT_POLYNOMIAL"
        else:continue
        labels.append(act);features.append(fvec(task))
        evidence.append({"id":task["id"],"direct":exists_d,"fold":exists_f,"rewarded_action":act})
    train_source_CPU=time.process_time()-train_start
    assert len(labels)==112 and collections.Counter(labels)=={
          "DIRECT_POLYNOMIAL":56,"DEFINE_FOLD_SUM":56},collections.Counter(labels)
    model=make_pipeline(StandardScaler(),MLPClassifier(
          hidden_layer_sizes=(12,),random_state=SEED,
          max_iter=400,learning_rate_init=.008,alpha=.05))
    start=time.process_time();model.fit(np.asarray(features),np.asarray(labels))
    model_cpu=time.process_time()-start
    checkpoint=pickle.dumps(model,protocol=4)
    assert model.predict(features).tolist()==pickle.loads(checkpoint).predict(features).tolist()
    start=time.process_time();modes={}
    for name,actions in {
        "D_trained_TOP1":[model.predict([fvec(row)])[0]],
        "C_nolearn_direct":["DIRECT_POLYNOMIAL"],
        "C_nolearn_fold":["DEFINE_FOLD_SUM"],
        "A_all_same_rights":["DIRECT_POLYNOMIAL","DEFINE_FOLD_SUM"],
    }.items():
        t=time.process_time();attempts=[];calls=0
        for action in actions:
            if action=="DEFINE_FOLD_SUM":program,n=fold(row)
            else:program,n=direct(row)
            calls+=n
            attempts.append({"action":action,"program":program,"candidate_checks":n})
        modes[name]={"attempts":attempts,"oracle_calls":calls,"source_CPU_s":time.process_time()-t}
    info={"schema":"Q3_KEIJZER6_REAL_TRAINED_RECURSIVE_FOLD_FIRST_SOURCE_ONLY.v1",
          "prior_source_no_gold":True,
          "first_Keijzer_original_source_sha256":sha(source_bytes),
          "trained_on_synthetic_numeric_only_112":True,
          "no_Keijzer_b0_training_examples":True,
          "source_verifier_action_counts":dict(collections.Counter(labels)),
          "train_numeric_reward_trace_sha":sha(json.dumps(evidence,sort_keys=True).encode()),
          "train_math_oracle_calls":n_calls,
          "train_source_CPU_s":train_source_CPU,
          "train_model_CPU_s":model_cpu,
          "pickle_bytes":len(checkpoint),
          "pickle_model_sha256":sha(checkpoint),
          "trained_source_tasks":112,"methods":modes,
          "human_provided":"DIRECT,FOLD_SUM, DELTA, rational candidate families and fitting",
          "global_Q3":"OPEN","G1":"HOLD"}
    path=pathlib.Path(args.pred)
    predict_sha=write(path,info)
    ckpath=path.parent/"TRUSTED_TRAINED_MODEL.pkl";ckpath.write_bytes(checkpoint)
    assert sha(ckpath.read_bytes())==info["pickle_model_sha256"]
    print("Q3_KEIJZER6_CI_FROZEN_TRAINED_RECURSION_PREDICTIONS_BEFORE_GOLD",
           json.dumps({"prediction_sha256":predict_sha,"train_oracle":n_calls,
             "rewards":info["source_verifier_action_counts"],
             "model_sha":info["pickle_model_sha256"],
             "methods":{k:{"calls":v["oracle_calls"],"actions":
                    [a["action"] for a in v["attempts"]],"programs":
                    [a["program"] for a in v["attempts"]]}
                    for k,v in modes.items()}},sort_keys=True),flush=True)
def independent_author_grader(args):
    pub=pathlib.Path(args.truth).read_bytes()
    first=pathlib.Path(args.pred).read_bytes()
    true=json.loads(pub);report=json.loads(first)
    assert true["source_id"]==IDENT and true["true_function"]=="harmonic(n)"
    assert report["schema"]=="Q3_KEIJZER6_REAL_TRAINED_RECURSIVE_FOLD_FIRST_SOURCE_ONLY.v1"
    methods={}
    for name,method in report["methods"].items():
        accepted=[]
        for attempt in method["attempts"]:
            program=attempt["program"]
            if not program or program["status"]!="SOURCE_VALID":continue
            node=program["ast"]
            if node.get("node")!="DEFINE_MACRO":continue
            op=node["body"];t=op["term"]
            initial=sp.Rational(op["base"])
            a=sp.Rational(t["numerator"]);b=sp.Integer(t["offset"]);p=sp.Integer(t["power"])
            # Independent published recurrence: H1=1, Hn-H(n-1)=1/n for all n>=2.
            formula=initial+sp.Sum(a/(K+b)**p,(K,op["start"],N))
            step=sp.cancel(a/(N+b)**p-1/N)
            induction=(op["start"]==2 and initial==1 and step==0)
            exact_out=0
            for point in true["heldout_exact_51_120"]:
                n=int(point["n"])
                held=Fraction(int(point["num"]),int(point["den"]))
                derived=Fraction(str(initial))
                for k in range(2,n+1):
                    derived+=Fraction(str(a))*Fraction(1,(k+int(b))**int(p))
                exact_out+=int(held==derived)
            if induction and exact_out==70:
                accepted.append({"name":node["name"],"certified_expr":str(formula),
                 "base_exact":True,"recurrence_all_n_exact":True,
                 "mathematical_induction_all_positive_n":True,
                 "original_exact_heldout_51_120":exact_out})
        methods[name]={"full_original_all_n_proved":bool(accepted),
                        "certificates":accepted,"source_calls":method["oracle_calls"]}
    assert len(methods)==4
    assert methods["D_trained_TOP1"]["full_original_all_n_proved"]
    assert not methods["C_nolearn_direct"]["full_original_all_n_proved"]
    assert methods["C_nolearn_fold"]["full_original_all_n_proved"]
    assert methods["A_all_same_rights"]["full_original_all_n_proved"]
    result={"schema":"Q3_KEIJZER6_CI_INDEPENDENT_FULL_POSITIVE_INTEGER_ORIGINAL_PROOF.v1",
      "frozen_pregrade_prediction_sha256":sha(first),
      "original_true_author_sha256":sha(pub),
      "all_positive_integer_harmonic_exact_via_induction":True,
      "external_original_70_of_70_exact_unseen_rational_values":True,
      "per_method":methods,
      "general_rational_function_impossibility":"H_n >= log(n+1) unbounded, H_n <= 1+log(n) so H_n/n->0; rational functions either bounded or grow polynomial order >=1",
      "human_FOLD_SUM_primitive":True,"no_neural_only_v_classical":True,
      "G1":"HOLD","Q3_GLOBAL":"OPEN","Q4_ALLIN10X":"NOT_PROVED"}
    grade_sha=write(args.out,result)
    print("Q3_KEIJZER6_CI_INDEPENDENT_AUTHOR_ALL_N_RECURSIVE_MACRO_PROOF",
      json.dumps({"sha256":grade_sha,"author_proof":{k:v["full_original_all_n_proved"] for k,v in methods.items()},
           "model_macro":methods["D_trained_TOP1"]["certificates"]},sort_keys=True),flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--mode",choices=("prepare","infer","grade"),required=True)
    for k in ("source","truth","pred","out"):a.add_argument("--"+k)
    args=a.parse_args()
    if args.mode=="prepare":original_preparation(args)
    if args.mode=="infer":source_only_inference(args)
    if args.mode=="grade":independent_author_grader(args)
