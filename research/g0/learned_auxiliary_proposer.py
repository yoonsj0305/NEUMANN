"""NEUMANN Q3 DEV ONLY: actually train a source-conditioned tiny neural proposer.
Goal: propose a NONCONSTANT new helper expression from a recurrence's functional
equation WITHOUT teacher output labels, then verify independently on full original.

This DOES NOT prove Q3 autonomous novel semantics: human-chosen affine hypothesis
space e(t)=1+a*t, sign constraint, classical algebra a=b is complete and cheap.
Four original SMT-LIB modInv sources already OPENED in PR531 before development.
"""
import argparse,collections,hashlib,json,pathlib,re,time
import numpy as np

ORIGINAL_SHA="7f993a017850ba547c6ea19a1bf3b54adf54a449"
FOLDER="non-incremental/QF_NIA/20230328-sqrtmodinv-hoenicke"
ORIGINALS={
"modInv8.smt2":"32364b58d23386c80e6355fe03795636bff45c16",
"modInv32.smt2":"5ecf8a7276086b141a1f4fe0ee8372e1d008bed1",
"modInv64.smt2":"c2f1819814cc4c3e6cee8c46ca6c82d99817af5d",
"modInvFull.smt2":"cca902e6afcfd2d627f3ee145e24e2ab39d598c4"}
TRAIN_B=np.array([-1.9,-1.75,-1.6,-1.45,-1.3,-1.2,-0.9,-0.8,-0.7])[:,None]
SEEDS=(11,23,37)
STEPS=5000
GRADIENT_LR=0.02

def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def file_sha(path):return sha(path.read_bytes())
def write(path,x):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
    return file_sha(path)

def source_update_b(raw):
    # Source AST narrowed from genuine Newton update, not original labels.
    # Fail closed for different program structures; do NOT hallucinate operator.
    text=raw.decode()
    assert "(set-logic QF_NIA)" in text
    update=re.findall(r"\(assert\s+\(=\s+inv2\s+\(\*\s+inv1\s+\(-\s+2\s+\(\*\s+denominator\s+inv1\)\)\)\)\)",text)
    if len(update)!=1:raise ValueError("NOT_A_SOURCE_SUPPORTED_NEWTON_STEP")
    # t=d*x, t'=d*x'=t(2-t)=2t-t^2. The observation b=-1 is
    # SOURCE INPUT, not an answer/teacher or a target solved label.
    return -1

def prepare(root,source_dir,secret_dir):
    root=pathlib.Path(root)/FOLDER
    source=[];ground=[]
    for name,githash in ORIGINALS.items():
        raw=(root/name).read_bytes()
        assert blob(raw)==githash,name
        source_id=sha(raw)[:24]
        b=source_update_b(raw)
        source.append({"id":source_id,"recurrence_coefficients":{"t":2,"t_squared":b},
                       "allowed_symbolic_grammar":"e=1+a*(denominator*inv_i) where a is INT; NONCONSTANT"})
        ground.append({"id":source_id,"original_file":name,"sha256":sha(raw),
                       "git_blob_sha1":blob(raw),"original_revision":ORIGINAL_SHA})
    source_path=pathlib.Path(source_dir)/"SOURCE_ONLY_NO_ORIGINAL_LABELS.json"
    truth_path=pathlib.Path(secret_dir)/"PRIVATE_ORIGINAL_FILE_IDENTITIES.json"
    s_sha=write(source_path,{"n":len(source),"source":source})
    t_sha=write(truth_path,{"n":len(ground),"private_originals":ground})
    print("NEURAL_AUX_SOURCE_SCRUBBED",json.dumps({"n":len(source),"source_sha":s_sha,"secret_sha":t_sha}),flush=True)

def train(seed):
    rng=np.random.default_rng(seed)
    h=12
    W1=rng.normal(0,0.1,(1,h));q1=np.zeros((1,h))
    W2=rng.normal(0,0.1,(h,1));q2=np.array([[0.55]])
    params=[W1,q1,W2,q2]
    moms=[np.zeros_like(v) for v in params]
    squares=[np.zeros_like(v) for v in params]
    started=time.process_time()
    for step in range(1,STEPS+1):
        hidden=np.tanh(TRAIN_B@W1+q1)
        logits=hidden@W2+q2
        a=-np.logaddexp(0,logits)   # zero-degree constant solution excluded by sign, not sufficient
        # Self-supervised polynomial identity for t'=2t+b*t²:
        # e(t')-e(t)^2 = (a*b-a²)*t², teacher a is NEVER supplied.
        delta=a*(TRAIN_B-a)
        loss=float(np.mean(delta*delta))
        dlogit=(2*delta*(TRAIN_B-2*a))/len(TRAIN_B)*(-1/(1+np.exp(-logits)))
        dW2=hidden.T@dlogit
        dq2=np.sum(dlogit,axis=0,keepdims=True)
        dh=(dlogit@W2.T)*(1-hidden**2)
        dW1=TRAIN_B.T@dh
        dq1=np.sum(dh,axis=0,keepdims=True)
        for i,g in enumerate((dW1,dq1,dW2,dq2)):
            moms[i]=0.9*moms[i]+0.1*g
            squares[i]=0.999*squares[i]+0.001*(g*g)
            params[i][:]-=GRADIENT_LR*(moms[i]/(1-0.9**step))/(np.sqrt(squares[i]/(1-0.999**step))+1e-8)
    elapsed=time.process_time()-started
    def predict(b):
        hidden=np.tanh(np.array([[b]])@W1+q1)
        return float((-np.logaddexp(0,hidden@W2+q2))[0,0])
    weights={"W1":W1.tolist(),"q1":q1.tolist(),"W2":W2.tolist(),"q2":q2.tolist()}
    return {"seed":seed,"train_cpu_s":elapsed,"train_self_supervised_loss":loss,
            "heldout_b_neg1_float_a":predict(-1),
            "heldout_b_neg09_float_a":predict(-0.9),
            "weights_sha":sha(json.dumps(weights,sort_keys=True).encode()),
            "full_learned_weights":weights}

def infer(src,pred):
    source=json.loads(pathlib.Path(src).read_text())["source"]
    assert len(source)==4
    started=time.process_time()
    fitted=[train(seed) for seed in SEEDS]
    records=[]
    for row in source:
        assert "status" not in str(row).lower() and "unsat" not in str(row).lower()
        a_float=np.mean([x["heldout_b_neg1_float_a"] for x in fitted]) if row["recurrence_coefficients"]["t_squared"]==-1 else None
        if a_float is None:
            status="UNKNOWN_UNSUPPORTED_RECURRENCE"
            a_int=None
        else:
            proposed=round(a_float)
            a_int=int(proposed) if abs(a_float-proposed)<=0.05 and proposed!=0 else None
            status="NONTRIVIAL_HELPER_RATIONALIZED" if a_int is not None else "UNKNOWN_FLOAT_NOT_EXACT"
        records.append({"id":row["id"],"status":status,"b_from_source":row["recurrence_coefficients"]["t_squared"],
                        "learned_float":a_float,"candidate_int_coefficient":a_int,
                        "new_symbolic_proposal":f"e_i=1+({a_int})*(denominator*inv_i)" if a_int is not None else None})
    # Classical same-grammar complete exact analogue: coefficient b if b!=0.
    cstart=time.process_time()
    classical=[{"id":x["id"],"candidate_int_coefficient":x["recurrence_coefficients"]["t_squared"],
                "reason":"algebraic e(t')=e(t)^2 => a*(b-a)=0, nonzero a=b"}
               for x in source]
    classical_cpu=time.process_time()-cstart
    total_cpu=time.process_time()-started
    out={"schema":"NEUMANN_Q3_LIMITED_SELF_SUPERVISED_AUX_LEARNING.v1",
         "source_no_truth_SHA256":file_sha(pathlib.Path(src)),
         "trained_policy_architecture":"numpy 1x12 tanh MLP -> softplus negative affine coefficient",
         "loss_only_functional_equation_no_teacher_coefficients":True,
         "human_provided_hypothesis_grammar":"e=1+a*(denominator*inv), a integer",
         "human_provided_sign_constraint":True,
         "developed_after_four_originals_opened":True,
         "learned_weights":fitted,"predictions":records,
         "exact_classical_same_grammar_baseline":classical,
         "all_train_plus_inference_cpu_s":total_cpu,"classical_candidate_cpu_s":classical_cpu,
         "zero_global_q3_neural_exclusive_claim":True}
    digest=write(pred,out)
    print("NEURAL_AUX_BLIND_SOURCE_PREDICTIONS_FROZEN",json.dumps({
        "sha256":digest,"model_train_cpu_s":[x["train_cpu_s"] for x in fitted],
        "predictions":len(records),"float_a":[x["heldout_b_neg1_float_a"] for x in fitted],
        "learned_nonconstant":sum(p["candidate_int_coefficient"] is not None for p in records),
        "classical_candidate_cpu_s":classical_cpu},sort_keys=True),flush=True)

def grade(source_root,secret,pred,out):
    # separate PRIVATE grader stage, no model training, enforces original proof for learned proposal
    from source_newton_2adic_proof import run as prove_original
    truth=json.loads(pathlib.Path(secret).read_text())["private_originals"]
    predfile=json.loads(pathlib.Path(pred).read_text())
    idx={x["id"]:x for x in predfile["predictions"]}
    strong={x["id"]:x for x in predfile["exact_classical_same_grammar_baseline"]}
    rows=[];counts=collections.Counter()
    for tr in truth:
        uid=tr["id"];p=idx[uid];a=p["candidate_int_coefficient"];b=p["b_from_source"]
        counts["total"]+=1
        # Symbolic polynomial certificate from source recurrence, not sampled correctness.
        exact_nontrivial=(a is not None and a!=0 and a*(b-a)==0)
        counts["learned_exact_functional_equation_nonconstant"]+=int(exact_nontrivial)
        same_grammar_classical=(strong[uid]["candidate_int_coefficient"]==b and b!=0)
        counts["classical_exact_functional_equation_nonconstant"]+=int(same_grammar_classical)
        if exact_nontrivial:
            original=prove_original(pathlib.Path(source_root)/FOLDER/tr["original_file"])
            accepted=original["status"]=="ORIGINAL_UNSAT_CERTIFIED_BY_2ADIC_SOURCE_INVARIANT"
            # Source original theorem uses e=1-dx. Assert trained coefficient chooses that SAME theorem.
            accepted=accepted and a==-1
        else:accepted=False
        counts["learned_original_proven_unsat"]+=int(accepted)
        counts["classical_original_proven_unsat"]+=int(same_grammar_classical and b==-1)
        counts["neural_exclusive_original_proof"]+=int(accepted and not (same_grammar_classical and b==-1))
        rows.append({"id":uid,"source_sha":tr["sha256"],"original":tr["original_file"],
                     "learned_a":a,"source_update_b":b,"classical_a":strong[uid]["candidate_int_coefficient"],
                     "learned_exact_nonconstant_semantics":exact_nontrivial,
                     "original_mathematical_UNSAT":accepted})
    summary={"schema":"NEUMANN_Q3_LEARNED_AUX_DEV_ONLY_INDEPENDENT_GRADE.v1",
             "sealed_predictions_SHA256":file_sha(pathlib.Path(pred)),
             "source_originals":rows,"counts":dict(counts),
             "learned_exclusive_additional_originals":0,
             "total_neural_training_cpu_s":sum(w["train_cpu_s"] for w in predfile["learned_weights"]),
             "strongest_equal_grammar_classical_proves_all":True,
             "global_Q3_Q4_Q6":"OPEN","G1_first_blind_admitted":False}
    d=write(out,summary)
    print("NEURAL_AUX_INDEPENDENT_ORIGINAL_GRADE",json.dumps({"sha256":d,"counts":dict(counts),
          "learning_train_cpu_s":summary["total_neural_training_cpu_s"]},sort_keys=True),flush=True)
    assert counts["learned_original_proven_unsat"]==counts["classical_original_proven_unsat"]==4
    assert counts["neural_exclusive_original_proof"]==0

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--mode",choices=("prepare","infer","grade"),required=True)
    for key in ("source_root","source_dir","secret_dir","source","secret","pred","out"):
        cli.add_argument("--"+key.replace("_","-"))
    a=cli.parse_args()
    if a.mode=="prepare":prepare(a.source_root,a.source_dir,a.secret_dir)
    elif a.mode=="infer":infer(a.source,a.pred)
    else:grade(a.source_root,a.secret,a.pred,a.out)
