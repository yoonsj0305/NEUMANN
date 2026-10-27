#!/usr/bin/env python3
"""TRAIN ONLY: genuine torch learning of an SGI program selection prior.
Reads only the previously opened twelve original tasks and their frozen old FIRST.
Never reads or searches a heldout *new* original test body.
"""
import hashlib,json,math,os,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_active_oracle_v1 import top_level_forms,get_cmd,io_form,source_without_forms,sha256,proposal_function,helpers_for,model_eval
from sgi_active_oracle_v1_postfirst_grade_fast import source_verified

PIN="e7ae840e5546e9243ff94afb1a29064fc050011c"
OLD_FIRST="a2713cee7e4a54506501927c07ff65f78d4ad110e4c9568892d937f3a0aa8185"
SOURCE=pathlib.Path("upstream")
FIRST=pathlib.Path("training_first")
OUT=pathlib.Path("training_weights")
SEEDS=(5,13,29)
OPS=("bvnot","bvand","bvor","bvxor","bvadd","ehad","arba","shesh","smol","im","let")
DIM=24

def features(program,src_count,src_bytes,probe_pred,future_pred,arm):
    """All 24 features are source program, metadata or UNLABELED prediction."""
    def count(x):return float(len(re.findall(r"\b"+re.escape(x)+r"\b",program)))
    pop=lambda s:bin(int(s[2:],16)).count("1")/64.
    v=[
        math.log1p(len(program))/9.,
        math.log1p(program.count("("))/8.,
        *(min(count(op),20.)/10. for op in OPS),
        min(program.count("#x"),40)/20.,
        min(count("bvshl"),20.)/10.,
        min(len(re.findall(r"\bx\b",program)),30)/15.,
        math.log1p(src_count)/8.,
        math.log1p(src_bytes)/12.,
        pop(probe_pred),pop(future_pred),
        ((int(probe_pred[2:],16)^int(future_pred[2:],16)).bit_count())/64.,
        float(arm==0),float(arm==1),float(arm==2),
    ]
    assert len(v)==DIM,(len(v),v)
    return v

def main():
    import z3
    import numpy as np
    import torch
    torch.set_num_threads(1)
    assert subprocess.check_output(["git","-C",str(SOURCE),"rev-parse","HEAD"],text=True).strip()==PIN
    raw=(FIRST/"FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json").read_bytes()
    assert sha256(raw)==OLD_FIRST
    first=json.loads(raw)
    assert len(first["rows"])==12
    rows=[];X=[];Y=[]
    t0=time.process_time()
    for r in first["rows"]:
        name=r["path"];b=(SOURCE/name).read_bytes()
        assert sha256(b)==r["original_sha256"]
        fs=top_level_forms(b.decode("utf-8"))
        cs=[f for f in fs if get_cmd(f[2])=="constraint"]
        pairs=[io_form(f[2]) for f in cs]
        assert len(cs)==r["n_constraints"]
        assert sha256(cs[-2][2].encode())==r["probe_constraint_sha256"]
        assert sha256(cs[-1][2].encode())==r["future_constraint_sha256"]
        source=source_without_forms(b.decode("utf-8"),cs[-2:])
        assert sha256(source.encode())==r["source_only_sha256"]
        h=helpers_for(source)
        source_expr=[]
        for f in cs[:-2]:
            m=re.fullmatch(r"\(\s*constraint\s+(.*)\s*\)",f[2],re.S)
            assert m
            source_expr.append(m.group(1))
        row={"index":r["index"],"path":name,"source_count":len(cs)-2,"cases":[]}
        for j in range(3):
            s=(FIRST/f"{r['index']:02d}_{j}.stdout").read_bytes()
            assert sha256(s)==r["proposals"][j]["stdout_sha256"]
            c={"arm":j,"candidate_sha256":sha256(s),"valid":False}
            try:
                program=proposal_function(s.decode("utf8","replace"))
                verified=source_verified(z3,h,program,source_expr)
                if not verified:raise ValueError("NOT_SOURCE_CONSISTENT")
                probe=model_eval(h,program,pairs[-2][0])
                future=model_eval(h,program,pairs[-1][0])
                xx=features(program,len(cs)-2,len(source),probe,future,j)
                truth=int(future==pairs[-1][1])
                X.append(xx);Y.append(truth)
                c.update({"valid":True,"train_label_exact":truth,
                   "features_sha256":sha256(json.dumps(xx).encode()),
                   "candidate_program_sha256":sha256(program.encode())})
            except Exception as e:
                c.update({"reason":type(e).__name__+":"+str(e)[:140]})
            row["cases"].append(c)
        rows.append(row)
        print("TRAIN_SOURCE_ONLY",r["index"],[c.get("train_label_exact","HOLD") for c in row["cases"]],flush=True)
    if len(X)<12 or len(set(Y))<2:
        raise RuntimeError("TRAINING_NOT_ADMISSIBLE_INSUFFICIENT_OR_ALL_ONE_CLASS")
    x=torch.tensor(np.asarray(X,dtype="float32"))
    y=torch.tensor(np.asarray(Y,dtype="float32")).unsqueeze(-1)
    weights={}
    for mode in ("A","B"):
        for seed in SEEDS:
            torch.manual_seed(seed)
            model=torch.nn.Linear(DIM,1)
            optimizer=torch.optim.Adam(model.parameters(),lr=.025,weight_decay=.01)
            yy=y.clone()
            if mode=="B":
                g=np.random.default_rng(seed+11089)
                yy=torch.tensor(g.permutation(np.asarray(Y)).astype("float32")).unsqueeze(-1)
            for _ in range(240):
                optimizer.zero_grad()
                loss=torch.nn.functional.binary_cross_entropy_with_logits(model(x),yy)
                loss.backward();optimizer.step()
            with torch.no_grad():
                score=torch.sigmoid(model(x))
                w=model.weight.detach().numpy().flatten().tolist()
                bias=float(model.bias.detach().numpy().flatten()[0])
                loss=float(torch.nn.functional.binary_cross_entropy(score,yy).item())
            weights[f"{mode}_{seed}"]={
                "mode":mode,"seed":seed,"weights":[float(u) for u in w],
                "bias":bias,"train_BCE":loss,
                "label_permutation":"true-permuted-across-training-candidates" if mode=="B" else "actual-original-heldout",
            }
            print("TRAIN_WEIGHTS",mode,seed,round(loss,5),flush=True)
    OUT.mkdir(exist_ok=True)
    evidence={"purpose":"real ownweight torch logistic A vs shuffled-target B; train on opened SGI12 ONLY",
       "original_benchmark_repo":"Barnard-PL-Labs/sygus-sgi-1",
       "benchmark_sha":PIN,"old_first_sha256":OLD_FIRST,
       "ownweight_model":"PyTorch torch.nn.Linear(24,1) gradient-descended BCE fullbatch Adam",
       "pre_registered_feature_dim":DIM,
       "features_type":"source-only executable program syntax, unlabeled program predictions, source count, 3 arm flags",
       "hyperparameters":{"epochs":240,"lr":.025,"weight_decay":.01,"seeds":list(SEEDS)},
       "n_candidates":len(X),"n_positive":sum(Y),"n_negative":len(Y)-sum(Y),
       "training_rows":rows,
       "weights":weights,
       "training_cpu_seconds":round(time.process_time()-t0,6),
       "test_source_accessed":False,"test_gold_accessed":False,
       "global_Q1_Q7":"OPEN","G1":"HOLD"}
    p=OUT/"FROZEN_TRAINED_A_B_WEIGHTS.json"
    p.write_text(json.dumps(evidence,sort_keys=True,indent=2))
    print("TRAINED_WEIGHTS_SHA256",sha256(p.read_bytes()))
    print("COUNTS",len(X),sum(Y),len(Y)-sum(Y),flush=True)
if __name__=="__main__":main()
