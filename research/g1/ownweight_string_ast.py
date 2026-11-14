"""G1 own-weight TWO-TOKEN typed string-AST proposer (standard numpy only).

Training uses wholly synthetic input/output tasks and no external SyGuS task
contents. EVALUATE from a separate script after checkpoint SHA is frozen.
A linear softmax network has actual trained weights but the atom vocabulary,
feature design and semantics are HUMAN specified; no global Q3 claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any

import numpy as np

ATOMS = (
    "INPUT", "FIRST_WORD", "LAST_WORD", "HEAD1", "HEAD2",
    "TAIL1", "TAIL2", "BEFORE_DIGIT", "DIGIT_SUFFIX",
    "LOWER", "UPPER", "SPACE", "DOT", "DASH", "EMPTY",
)
ATOM_COUNT = len(ATOMS)
TRAIN_SEED = 41677
N_TRAIN = 3200
N_VALID = 320
STEPS = 120


def atom(name: str, src: str) -> str:
    if name == "INPUT":
        return src
    if name == "FIRST_WORD":
        return src.split(" ")[0]
    if name == "LAST_WORD":
        return src.split(" ")[-1]
    if name == "HEAD1":
        return src[:1]
    if name == "HEAD2":
        return src[:2]
    if name == "TAIL1":
        return src[-1:]
    if name == "TAIL2":
        return src[-2:]
    if name == "BEFORE_DIGIT":
        m = re.search(r"\d", src)
        return src[:m.start()] if m else src
    if name == "DIGIT_SUFFIX":
        m = re.search(r"\d+$", src)
        return m.group(0) if m else ""
    if name == "LOWER":
        return src.lower()
    if name == "UPPER":
        return src.upper()
    if name == "SPACE":
        return " "
    if name == "DOT":
        return "."
    if name == "DASH":
        return "-"
    if name == "EMPTY":
        return ""
    raise ValueError("NOT_AN_ATOM")


def run_ast(pair: tuple[int, int], src: str) -> str:
    return atom(ATOMS[pair[0]], src) + atom(ATOMS[pair[1]], src)


def features(examples: list[tuple[str, str]]) -> np.ndarray:
    if not examples:
        raise ValueError("NO_SOURCE_EXAMPLES")
    result = []
    for name in ATOMS:
        flags = []
        for x, y in examples:
            p = atom(name, x)
            valid = p != ""
            flags.append((
                float(p == y),
                float(valid and y.startswith(p)),
                float(valid and y.endswith(p)),
                float(valid and p in y),
                min(len(p), 64)/max(len(y), 1),
                min(len(p), 64)/max(len(x), 1),
            ))
        result.extend(np.mean(flags, axis=0).tolist())
    lens = np.asarray([(len(x),len(y)) for x,y in examples],dtype=float)
    result += [
        float(np.mean(lens[:,0]))/64,
        float(np.mean(lens[:,1]))/64,
        float(np.mean(lens[:,1]-lens[:,0]))/64,
        float(np.mean([x.count(" ") for x,_ in examples]))/12,
        float(np.mean([y.count(".") for _,y in examples]))/12,
        float(np.mean([sum(c.isdigit() for c in x) for x,_ in examples]))/24,
    ]
    return np.asarray(result, dtype=np.float64)


FIRST = ("Ducati", "Kara", "Andrew", "Mariya", "Nadia",
         "Hiro", "Ivan", "Anna", "Leona", "Honda",
         "Samir", "Mina", "Claire", "Yuna", "Taro")
LAST = ("Faber", "Kim", "Mori", "Cencici", "Santos",
        "Chen", "FreeHafer", "Kotas", "Sergienko", "Lee")


def sample_input(rng: random.Random, style: int) -> str:
    a = rng.choice(FIRST)
    b = rng.choice(LAST)
    if style == 0:
        return a + " " + b
    if style == 1:
        return a + str(rng.randint(100, 999))
    if style == 2:
        return a + "-" + b
    if style == 3:
        return a
    if style == 4:
        return rng.choice([a.lower(),a.upper(),a.title()]) + " " + b
    return a + " " + b + str(rng.randint(10, 99))


def reserved_pair(pair: tuple[int,int]) -> bool:
    # Roughly one fifth of possible AST compositions NEVER occur in TRAIN.
    # A true compositional novelty target must generate a held-out PAIR.
    return (pair[0]+3*pair[1])%5==0


def synthetic_task(rng: random.Random, split: str="train") -> tuple[list[tuple[str,str]],tuple[int,int],tuple[str,str]]:
    if split not in ("train","reserved"):
        raise ValueError("UNKNOWN_SYNTHETIC_SPLIT")
    while True:
        left = rng.randrange(ATOM_COUNT)
        right = rng.randrange(ATOM_COUNT)
        if reserved_pair((left,right))==(split=="reserved"):
            break
    style = rng.randrange(6)
    xs = [sample_input(rng, style) for _ in range(4)]
    pair = (left, right)
    train = [(x,run_ast(pair,x)) for x in xs[:3]]
    heldout = (xs[3],run_ast(pair,xs[3]))
    return train,pair,heldout


def make_data(n:int, rng: random.Random, split: str='train'):
    X=np.empty((n,ATOM_COUNT*6+6),dtype=np.float64)
    Y=np.empty((n,2),dtype=np.int64)
    examples=[]
    for i in range(n):
        train, ast, heldout=synthetic_task(rng,split)
        X[i]=features(train)
        Y[i]=ast
        examples.append((train,heldout))
    return X,Y,examples


def topk(weights: dict[str,Any], x:np.ndarray, max_pairs=32)->list[tuple[int,int]]:
    mu=np.asarray(weights["mean"],dtype=np.float64)
    sd=np.asarray(weights["std"],dtype=np.float64)
    normalized=np.clip((x-mu)/sd,-6.0,6.0)
    w=np.asarray(weights["weights"],dtype=np.float64)
    b=np.asarray(weights["bias"],dtype=np.float64)
    logits=np.einsum("f,ofc->oc",normalized,w)+b
    logits-=np.max(logits,axis=1,keepdims=True)
    p=np.exp(logits)
    p/=np.sum(p,axis=1,keepdims=True)
    pairs=sorted(((i,j) for i in range(ATOM_COUNT) for j in range(ATOM_COUNT)),
       key=lambda pair:(-float(p[0,pair[0]]*p[1,pair[1]]),pair[0],pair[1]))
    return pairs[:max_pairs]


def train(out:Path)->dict[str,Any]:
    rng=random.Random(TRAIN_SEED)
    X,Y,_=make_data(N_TRAIN,rng)
    validX,validY,_=make_data(N_VALID,rng,'reserved')
    mean=np.mean(X,axis=0)
    std=np.maximum(np.std(X,axis=0),0.05)
    normalized=np.clip((X-mean)/std,-6,6)
    pcount=ATOM_COUNT
    f=normalized.shape[1]
    w=np.zeros((2,f,pcount),dtype=np.float64)
    bias=np.zeros((2,pcount),dtype=np.float64)
    # Two actual learned parameter heads (output AST tokens, not a fixed
    # joint program classification). Deterministic Adam under NumPy BLAS.
    mw=np.zeros_like(w);vw=np.zeros_like(w)
    mb=np.zeros_like(bias);vb=np.zeros_like(bias)
    beta1,beta2=0.9,0.999
    lr=0.12
    for step in range(1,STEPS+1):
        logits=np.einsum("nf,ofc->noc",normalized,w)+bias
        logits=logits-np.max(logits,axis=2,keepdims=True)
        probs=np.exp(logits)
        probs/=probs.sum(axis=2,keepdims=True)
        grad=probs
        for token in range(2):
            grad[np.arange(N_TRAIN),token,Y[:,token]]-=1
        grad/=N_TRAIN
        gw=np.einsum("nf,noc->ofc",normalized,grad)+0.0001*w
        gb=np.sum(grad,axis=0)
        mw=beta1*mw+(1-beta1)*gw
        vw=beta2*vw+(1-beta2)*(gw**2)
        mb=beta1*mb+(1-beta1)*gb
        vb=beta2*vb+(1-beta2)*(gb**2)
        w-=lr*(mw/(1-beta1**step))/(np.sqrt(vw/(1-beta2**step))+1e-8)
        bias-=lr*(mb/(1-beta1**step))/(np.sqrt(vb/(1-beta2**step))+1e-8)
    weights={
        "schema":"neumann.g1.ownweight-two-token-string-ast-checkpoint.v2",
        "seed":TRAIN_SEED,"train_tasks":N_TRAIN,"validation_tasks":N_VALID,
        "gradient_steps":STEPS,
        "atoms":list(ATOMS),
        "feature_shape":f,
        "weights":w.round(9).tolist(),"bias":bias.round(9).tolist(),
        "mean":mean.round(9).tolist(),"std":std.round(9).tolist(),
        "trained_programs_count":N_TRAIN,
        "training_program_pairs_reserved_rule":"(left+3*right)%5!=0",
        "training_distinct_program_pairs":len({tuple(p) for p in Y.tolist()}),
        "reserved_pair_count":sum(reserved_pair((a,b)) for a in range(ATOM_COUNT) for b in range(ATOM_COUNT)),
        "original_external_tasks_accessed":0,
        "whole_program_label_classifier":False,
        "model_generates_two_independently_parameterized_AST_tokens":True
    }
    # Never evaluate source target or alter policy after original scoring.
    validation_position_accuracy=[]
    for j in range(2):
        z=np.clip((validX-mean)/std,-6,6)@w[j]+bias[j]
        validation_position_accuracy.append(float(np.mean(z.argmax(axis=1)==validY[:,j])))
    weights["synthetic_validation_token_accuracy"]=validation_position_accuracy
    data=(json.dumps(weights,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
    out.write_bytes(data)
    return {
        "checkpoint_sha256":hashlib.sha256(data).hexdigest(),
        "model_seed":TRAIN_SEED,
        "training_tasks":N_TRAIN,"validation_tasks":N_VALID,
        "validation_token_accuracy":validation_position_accuracy,
        "validation_entire_AST_accuracy":float(np.mean([
            tuple(topk(weights,validX[i],1)[0])==tuple(int(t) for t in validY[i])
            for i in range(N_VALID)
        ])),
        "training_distinct_program_pairs":weights["training_distinct_program_pairs"],
        "reserved_pair_count":weights["reserved_pair_count"],
        "checkpoint_size_bytes":len(data),
        "external_targets_opened":0
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("checkpoint",type=Path)
    args=ap.parse_args()
    print(json.dumps(train(args.checkpoint),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
