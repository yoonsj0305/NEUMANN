"""NEUMANN G4 own-weight gradient model proposes typed ARRAY relational lemmas.

Experimental scope ONLY source-free synthetic. First prereg five unseen whole
kind/dst/src triples and a strong *same source rights* deterministic compiler
were frozen before running. A real NumPy gradient model emits three
compositional typed AST roles. No exact stored whole-program labels, no
external CHC input or original 2025 reserved target access.

Every proposal must pass the independently written Z3 source PRE/TRANS/POST
three-UNSAT checker; the model's exact token prediction is NOT a certificate.
"""
from __future__ import annotations

import argparse,hashlib,json,re,time
from pathlib import Path
import numpy as np

from research.g4.array_invariant_verifier import (
 ARRAYS,KINDS,ArrayTask,Candidate,generate_source,
 check_invariant,
)

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs/experiments/G4_OWNWEIGHT_ARRAY_LEMMA_SYNTHETIC_FIRST_PREREG_2026_11_06.json"
SEED=1729
ALL_TRIPLES=(
 tuple(("FILL",d,None)) for d in ARRAYS
)
CROSS_TRIPLES=tuple((kind,d,s) for kind in ("COPY","ADD")
                  for d in ARRAYS for s in ARRAYS if d!=s)
TRIPLES=tuple(ALL_TRIPLES)+CROSS_TRIPLES


def source_parse(source:str)->tuple[str,str|None,tuple[float,...]]:
    """Typed lexer, NOT a stored task solution or trained head.

    Raw source text indicates whether there is a SELECT or ADD sub-expression,
    and which array registers are used. The trained heads must independently
    select expression SHAPE, target register, and source register.
    """
    m=re.search(r"store\(([ABC]),index,(.*?)\); index'=index\+1",source)
    if not m:
        raise ValueError("BAD_ARRAY_PROGRAM_SOURCE_INTERFACE")
    dest,rhs=m.group(1),m.group(2)
    sm=re.search(r"select\(([ABC]),index\)",rhs)
    src=sm.group(1) if sm else None
    use_select=sm is not None
    use_add=rhs.startswith("add(") and use_select
    if rhs.count("select(")>1:
        raise ValueError("NOT_IN_TYPED_ONE_SELECTED_INDEX_PROTOCOL")
    feats=[1.0,float(use_select),float(use_add),float(not use_select)]
    feats += [float(dest==name) for name in ARRAYS]
    feats += [float(src==name) for name in ARRAYS]
    return dest,src,tuple(feats)


def deterministic_classical_compiler(raw_source:str)->Candidate:
    """Human-written direct source compiler, same raw text access as learner.

    This may dominate the proposed NN on both capability and end-to-end cost.
    That is a valid negative scientific result, not a benchmark defect.
    """
    dest,src,_=source_parse(raw_source)
    fragment=re.search(r"store\([ABC],index,(.*?)\); index'=index\+1",raw_source).group(1)
    if src is None:
        if not re.fullmatch(r"-?\d+",fragment):raise ValueError("INVALID_FILL")
        return Candidate("FILL",dest,None)
    if fragment==f"select({src},index)":
        return Candidate("COPY",dest,src)
    if re.fullmatch(r"add\(select\("+src+r",index\),-?\d+\)",fragment):
        return Candidate("ADD",dest,src)
    raise ValueError("CLASSICAL_SOURCE_SYNTAX_UNSUPPORTED")


def split():
    spec=json.loads(CONTRACT.read_text())
    reserved=tuple(tuple(x) for x in spec["exact_heldout_synthetic_pairs"])
    if len(reserved)!=5 or len(TRIPLES)!=15 or len(set(TRIPLES))!=15:
        raise ValueError("SYNTHETIC_TOTAL_DENOMINATOR_CHANGED")
    if any(x not in TRIPLES for x in reserved):
        raise ValueError("UNKNOWN_REGISTERED_SYNTHETIC_HELDOUT")
    train=tuple(x for x in TRIPLES if x not in reserved)
    assert len(train)==10
    return train,reserved


def softmax(logits):
    z=logits-np.max(logits,axis=1,keepdims=True)
    e=np.exp(z)
    return e/e.sum(axis=1,keepdims=True)


class OwnWeightProposer:
 def __init__(self,seed=SEED):
    rng=np.random.default_rng(seed)
    self.W=[rng.normal(0,0.025,size=(10,3)) for _ in range(3)]
 def raw(self,X):
    return [X@w for w in self.W]
 def predict(self,source:str)->Candidate|None:
    _,_,x=source_parse(source)
    X=np.array([x],dtype=np.float64)
    labels=[int(np.argmax(q[0])) for q in self.raw(X)]
    kind=KINDS[labels[0]]
    dst=ARRAYS[labels[1]]
    src=None if kind=="FILL" else ARRAYS[labels[2]]
    try:return Candidate(kind,dst,src)
    except ValueError:return None
 def train(self,X,targets,epochs=1350,lr=0.45)->dict:
    if X.shape[0]<10 or X.shape[1]!=10:raise ValueError("SOURCE_TRAIN_INPUT_SHAPE_CHANGED")
    n=X.shape[0]
    last_losses=[]
    for t in range(epochs):
        for i in range(3):
            probs=softmax(X@self.W[i])
            labels=targets[:,i]
            mask=np.ones(n) if i!=2 else (targets[:,0]!=0).astype(float)
            denom=mask.sum()
            clipped=np.clip(probs[np.arange(n),labels],1e-15,1.0)
            if t==epochs-1:
                last_losses.append(float(-(np.log(clipped)*mask).sum()/denom))
            derivative=probs
            derivative[np.arange(n),labels]-=1
            derivative=derivative*mask[:,None]/denom
            gradient=X.T@derivative
            self.W[i] -= lr*gradient
    return {"train_losses_by_role":last_losses,"total_loss":sum(last_losses),
       "epochs":epochs,"learning_rate":lr,
       "weights_sha256":self.hash_weights()}
 def hash_weights(self):
    digest=hashlib.sha256()
    for W in self.W:digest.update(np.asarray(W,dtype="<f8").tobytes())
    return digest.hexdigest()


def task_set(triples,constants):
    return [ArrayTask(kind,dst,src,c) for kind,dst,src in triples for c in constants]


def training_data(triples):
    # Training constants and task identities are disjoint from heldout tuple
    # combinations; the model does not memorize any complete target program.
    data=task_set(triples,(-3,0,2,7))
    X=np.array([source_parse(generate_source(t))[2] for t in data],dtype=np.float64)
    Y=np.array([(KINDS.index(t.kind),ARRAYS.index(t.dest),
               ARRAYS.index(t.src) if t.src else 0) for t in data],dtype=np.int64)
    return X,Y,data


def test(external_verifier:bool=True):
    train_keys,test_keys=split()
    X,Y,_=training_data(train_keys)
    network=OwnWeightProposer()
    weights_before=network.hash_weights()
    ablation=OwnWeightProposer()
    start=time.perf_counter_ns()
    receipt=network.train(X,Y)
    train_wall_ms=round((time.perf_counter_ns()-start)/1e6,3)
    if weights_before==network.hash_weights():
        raise ValueError("NO_ACTUAL_WEIGHT_TRAINING")
    # EXACT registered unseen whole-program source/dst/op tuples, c never
    # equals the original synthetic training constant set.
    tests=task_set(test_keys,(5,11))
    rows=[]
    for task in tests:
        original_source=generate_source(task)
        model_start=time.perf_counter_ns()
        proposal=network.predict(original_source)
        inference_ms=round((time.perf_counter_ns()-model_start)/1e6,3)
        classical_start=time.perf_counter_ns()
        native=deterministic_classical_compiler(original_source)
        classical_compile_ms=round((time.perf_counter_ns()-classical_start)/1e6,3)
        random_ablation=ablation.predict(original_source)
        def proof(candidate):
            if not external_verifier:return {"verified":False,"status":"NOT_RUN_NO_Z3"}
            if candidate is None:return {"verified":False,"status":"ILL_TYPED_ABSTAIN"}
            return check_invariant(task,candidate,timeout_ms=2000)
        learned_proof=proof(proposal)
        classical_proof=proof(native)
        ablation_proof=proof(random_ablation)
        expected=Candidate(task.kind,task.dest,task.src)
        rows.append({
         "task_source_sha256":hashlib.sha256(original_source.encode()).hexdigest(),
         "heldout_unseen_whole_AST":True,
         "source_class":[task.kind,task.dest,task.src],
         "constant_pass_through_int":task.constant,
         "ownweight_output_roles":(
             [proposal.kind,proposal.dest,proposal.src] if proposal else None),
         "ownweight_exact_new_AST":proposal==expected,
         "ownweight_source_proof":learned_proof,
         "untrained_ablation_output":(
             [random_ablation.kind,random_ablation.dest,random_ablation.src] if random_ablation else None),
         "random_weight_ablation_source_proof":ablation_proof,
         "native_classical_source_proof":classical_proof,
         "native_classical_ast_exact":native==expected,
         "ownweight_inference_ms":inference_ms,
         "classical_compilation_ms":classical_compile_ms,
         })
    n=len(rows)
    student_count=sum(x["ownweight_source_proof"]["verified"] for x in rows)
    classical_count=sum(x["native_classical_source_proof"]["verified"] for x in rows)
    ablated_count=sum(x["random_weight_ablation_source_proof"]["verified"] for x in rows)
    final={
      "schema":"neumann.g4.ownweight-typed-array-index-relation-sourcefree-FIRST.v1",
      "model_weights_sha256":network.hash_weights(),
      "frozen_random_initial_sha256":weights_before,
      "learning_real_update":True,
      "train":receipt,
      "test_synthetic_heldout_whole_pair_count":len(test_keys),
      "total_synthetic_heldout_programs":n,
      "metrics":{
        "learned_source_UNSAT_threeproof":student_count,
        "learned_generated_AST_exact":sum(x["ownweight_exact_new_AST"] for x in rows),
        "ablation_source_UNSAT_threeproof":ablated_count,
        "strong_classical_same_source_rights_source_UNSAT_threeproof":classical_count,
        "learned_exclusive_over_strong_classical":sum(
          x["ownweight_source_proof"]["verified"] and
          not x["native_classical_source_proof"]["verified"] for x in rows),
        "neural_training_ms":train_wall_ms,
        "neural_inference_total_ms":round(sum(x["ownweight_inference_ms"] for x in rows),3),
        "neural_verifier_total_ms":round(sum(x["ownweight_source_proof"].get("full_proof_wall_ms",0) for x in rows),3),
        "classical_compilation_total_ms":round(sum(x["classical_compilation_ms"] for x in rows),3),
        "classical_verifier_total_ms":round(sum(x["native_classical_source_proof"].get("full_proof_wall_ms",0) for x in rows),3),
        "new_ARC_public_eval_IDs":0,
        "external_original_reserved_2025_array8_consumed":0,
      },
      "scientific_scope":"ONLY_DISJOINT_SYNTHETIC_PROGRAM_COMPOSITION_NOT_FRONTIER_GENERALIZATION",
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "rows":rows}
    return final


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--skip-z3",action="store_true")
    a=ap.parse_args()
    result=test(external_verifier=not a.skip_z3)
    print(json.dumps(result,indent=2,sort_keys=True))
