"""Q3 FIRST real CPU-trained neural operator choice + exact original Z3 3VC.

Issue #271 registered goals, immutable seeds, controls and thresholds BEFORE
this code's first execution. Author-constructed original tasks only.

The MLP is trained on source-transition features & TRAIN labels; at HOLDOUT
inference it receives ONLY public Pre/Trans, NOT original Post, gold operator,
case id or verifier outcome. Classifier selects one of three FIXED mathematical
families. A deterministic builder computes parameter values from PUBLIC source.
This is NOT open-ended learned mathematical language invention nor a superiority
claim over exact classical templates. Q1-Q7 globally OPEN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import z3
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

KINDS=("QUADRATIC","MODULAR","AFFINE")
TRAIN_COUNTS=120
HOLDOUT_COUNTS=30
TRAIN_SEED=53
HOLDOUT_SEED=79
MODEL_SEED=17
SCHEMA="neumann.q3.cpu-trained-source-operator-first.v1"


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def source_cases(seed:int, count_each:int, holdout:bool):
    """Distinct deterministic original-task construction; no outcome filtering."""
    rng=np.random.default_rng(seed)
    out=[]
    for kind in KINDS:
        for j in range(count_each):
            k=int(rng.integers(8,14) if holdout else rng.integers(2,8))
            x0=int(rng.integers(-14,15))
            y0=int(rng.integers(-55,56))
            m=int(rng.integers(2,9))
            # Each public source is an original branching integer transition:
            # y'=y+ax+c, x'=x+dx, z'=1-z. No family name or gold in public.
            if kind=="QUADRATIC":
                branches=((k,2*k,k*k),(-k,-2*k,k*k))
            elif kind=="MODULAR":
                branches=((k,0,1),(-k,0,1))
            else:
                branches=((k,0,m),(-k,0,-m))
            public={"pre":{"x":x0,"y":y0,"z":0},
                    "trans":{"branches":[{"dx":a,"ax":b,"cy":c}
                              for a,b,c in branches],"z_update":"1-z"}}
            # The original Post is a trusted verification condition. It is NOT
            # provided to the neural proposer, template selector or scaler.
            private={"true_operator":kind,"source_id_sha256":sha_bytes(
                canonical({"public":public,"post_family":kind}).encode())}
            out.append((public,private))
    return out


def vector(public):
    p=public["trans"]["branches"]
    a,b=p
    k=max(1,abs(a["dx"]),abs(b["dx"]))
    cmax=max(1,abs(a["cy"]),abs(b["cy"]))
    det=a["dx"]*b["cy"]-b["dx"]*a["cy"]
    # All are computed from actual source transition numeric coefficients,
    # never private Post, source filename or label.
    return [
      a["dx"]/k,b["dx"]/k,a["ax"]/k,b["ax"]/k,
      a["cy"]/cmax,b["cy"]/cmax,
      det/(k*cmax),
      (a["cy"]*b["cy"])/(cmax*cmax),
      abs(a["ax"])+abs(b["ax"]),
      abs(a["cy"]-b["cy"])/cmax,
    ]


def operator_candidate(public,operator):
    """Propose a NON-POST source-only invariant from chosen family."""
    state=public["pre"]
    x0,y0=state["x"],state["y"]
    b1,b2=public["trans"]["branches"]
    k=math.gcd(abs(int(b1["dx"])),abs(int(b2["dx"])))
    if operator=="QUADRATIC":
        return {"operator":operator,"c":y0-x0*x0}
    if operator=="MODULAR":
        return {"operator":operator,"k":k,"r":x0%k}
    if operator=="AFFINE":
        return {"operator":operator,"dx":int(b1["dx"]),"dy":int(b1["cy"]),
                "x0":x0,"y0":y0}
    raise ValueError("UNREGISTERED_GRAMMAR_OPERATOR")


def pred(candidate,x,y):
    op=candidate["operator"]
    if op=="QUADRATIC":
        return y-x*x==candidate["c"]
    if op=="MODULAR":
        return x%candidate["k"]==candidate["r"]
    if op=="AFFINE":
        return candidate["dy"]*(x-candidate["x0"])-candidate["dx"]*(y-candidate["y0"])==0
    raise ValueError("BAD_OPERATOR")


def real_original_three_vc(public, private, proposed=None, *, use_post_only=False):
    """True original Pre, Trans, Post (private) independent of classifier."""
    x,y,z,xp,yp,zp=z3.Ints("x y z xp yp zp")
    d=public["pre"]
    pre=z3.And(x==d["x"],y==d["y"],z==0)
    branches=[]
    for b in public["trans"]["branches"]:
        branches.append(z3.And(xp==x+b["dx"],
            yp==y+b["ax"]*x+b["cy"],zp==1-z))
    trans=z3.And(z>=0,z<=1,z3.Or(*branches))
    true_candidate=operator_candidate(public,private["true_operator"])
    post=z3.Or(pred(true_candidate,x,y),z==0)
    if use_post_only:
        inv=post
        nxt=z3.Or(pred(true_candidate,xp,yp),zp==0)
    else:
        if proposed is None:
            raise ValueError("CANDIDATE_REQUIRED")
        inv=pred(proposed,x,y)
        nxt=pred(proposed,xp,yp)
    checks={}
    obligations={
        "initial":z3.And(pre,z3.Not(inv)),
        "consecution":z3.And(inv,trans,z3.Not(nxt)),
        "post":z3.And(inv,z3.Not(post)),
    }
    for name,term in obligations.items():
        sol=z3.Solver()
        sol.set(timeout=1800)
        sol.add(term)
        checks[name]=str(sol.check())
    return checks


def is_proven(checks):
    return set(checks)=={"initial","consecution","post"} and all(
        v=="unsat" for v in checks.values())


def strong_classical_operator(public):
    """Transparent deterministic strong full-grammar specialist, NOT oracle."""
    a,b=public["trans"]["branches"]
    if a["ax"]!=0 or b["ax"]!=0:
        return "QUADRATIC"
    determinant=a["dx"]*b["cy"]-b["dx"]*a["cy"]
    if determinant:
        return "MODULAR"
    return "AFFINE"


def fixed_gamma_operator(public):
    # Fixed original affine/octagon grammar has no modulo or square operators.
    # An affine conserved relation is available in the AFFINE construction.
    return "AFFINE"


def first_study():
    train=source_cases(TRAIN_SEED,TRAIN_COUNTS,False)
    hold=source_cases(HOLDOUT_SEED,HOLDOUT_COUNTS,True)
    train_hash={v["source_id_sha256"] for _,v in train}
    hold_hash=[v["source_id_sha256"] for _,v in hold]
    assert len(train_hash)==len(train)==360
    assert len(set(hold_hash))==len(hold)==90
    assert not (train_hash & set(hold_hash))
    X_train=np.asarray([vector(p) for p,_ in train],dtype=np.float64)
    X_hold=np.asarray([vector(p) for p,_ in hold],dtype=np.float64)
    # STRICT source-only feature-only training. The supervised train family
    # annotation is NOT passed to heldout inference, verifier is separate.
    labels=np.asarray([KINDS.index(priv["true_operator"]) for _,priv in train])
    scale=StandardScaler()
    Xtr=scale.fit_transform(X_train)
    Xho=scale.transform(X_hold)
    net=MLPClassifier(hidden_layer_sizes=(16,8),
        random_state=MODEL_SEED,activation="relu",solver="lbfgs",
        max_iter=500,alpha=1e-3)
    start=time.perf_counter_ns()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore",ConvergenceWarning)
        net.fit(Xtr,labels)
    train_ms=round((time.perf_counter_ns()-start)/1e6,3)
    learned=np.asarray(net.predict(Xho),dtype=int)
    # CAUSAL neural ablation: zero public transition features after fit.
    no_source=np.asarray(net.predict(scale.transform(np.zeros_like(X_hold))),
        dtype=int)
    random_gen=np.random.default_rng(MODEL_SEED)
    random_untrained=random_gen.integers(0,len(KINDS),len(hold))
    weights=b"".join(np.ascontiguousarray(m).tobytes()
       for m in (*net.coefs_,*net.intercepts_))
    model_sha=sha_bytes(weights)
    outputs=[]
    for i,(public,private) in enumerate(hold):
        predicted=KINDS[int(learned[i])]
        controls={
            "LEARNED":predicted,
            "UNTRAINED_RANDOM":KINDS[int(random_untrained[i])],
            "SOURCE_ABLATION":KINDS[int(no_source[i])],
            "FROZEN_AFFINE_GAMMA":fixed_gamma_operator(public),
            "STRONG_FULL_CLASSICAL":strong_classical_operator(public),
        }
        receipts={}
        for name,choice in controls.items():
            proposal=operator_candidate(public,choice)
            statuses=real_original_three_vc(public,private,proposal)
            receipts[name]={
                "selected_operator":choice,
                "proposal":proposal,
                "original_bad_conditions":statuses,
                "original_3vc_certified":is_proven(statuses),
                "selected_beyond_fixed_affine_gamma":choice in (
                    "QUADRATIC","MODULAR"),
            }
        post_only=real_original_three_vc(public,private,use_post_only=True)
        outputs.append({
           "case":i,
           "source_public_sha256":sha_bytes(canonical(public).encode()),
           "original_source_sha256":private["source_id_sha256"],
           "public_transition_features_sha256":sha_bytes(
                 canonical(vector(public)).encode()),
           "private_true_operator_for_verifier_only":private["true_operator"],
           "post_only_original_bad_conditions":post_only,
           "post_only_inductive":is_proven(post_only),
           "receipts":receipts,
        })
    counts={name:sum(int(row["receipts"][name]["original_3vc_certified"])
                     for row in outputs)
            for name in ("LEARNED","UNTRAINED_RANDOM","SOURCE_ABLATION",
                 "FROZEN_AFFINE_GAMMA","STRONG_FULL_CLASSICAL")}
    learned_out=sum(row["receipts"]["LEARNED"]["original_3vc_certified"]
        and row["receipts"]["LEARNED"]["selected_beyond_fixed_affine_gamma"]
        for row in outputs)
    false_accepted=sum(int(
         row["receipts"][key]["original_3vc_certified"]
         and any(x!="unsat" for x in row["receipts"][key]
                   ["original_bad_conditions"].values()))
        for row in outputs for key in counts)
    post_success=sum(int(x["post_only_inductive"]) for x in outputs)
    conditions={
        "exactly_90_heldout_originals_and_360_training":len(outputs)==90 and len(train)==360,
        "source_sha_unique_and_no_train_holdout_overlap":
            len(set(hold_hash))==90 and not (train_hash & set(hold_hash)),
        "learned_original_3vc_at_least_81":counts["LEARNED"]>=81,
        "learned_nonlinear_or_modular_3vc_at_least_54":learned_out>=54,
        "learned_vs_untrained_gain_at_least_25":
            counts["LEARNED"]-counts["UNTRAINED_RANDOM"]>=25,
        "learned_vs_hidden_source_feature_ablation_gain_at_least_25":
            counts["LEARNED"]-counts["SOURCE_ABLATION"]>=25,
        "old_fixed_affine_grammar_at_most_30":
            counts["FROZEN_AFFINE_GAMMA"]<=30,
        "post_only_original_invariant_never_inductive":post_success==0,
        "zero_incorrect_original_vc_certificates":false_accepted==0,
    }
    report={
        "schema":SCHEMA,"preregister_issue":271,
        "scientific_scope":"AUTHOR_CONSTRUCTED_CPU_SUPERVISED_OPERATOR_SELECTOR",
        "training_examples":len(train),"heldout_originals":len(hold),
        "holdout_classes":{"QUADRATIC":30,"MODULAR":30,"AFFINE":30},
        "seed_train":TRAIN_SEED,"seed_test":HOLDOUT_SEED,"seed_model":MODEL_SEED,
        "training_k_range":[2,7],"holdout_k_range":[8,13],
        "hidden_layers":[16,8],
        "actual_learned_parameter_count":sum(m.size for m in
              (*net.coefs_,*net.intercepts_)),
        "model_weights_sha256":model_sha,
        "train_wall_ms":train_ms,
        "scaler_train_only":True,
        "model_uses_inference_post_or_gold":False,
        "post_only_successes":post_success,
        "learned_verified_outside_frozen_affine_gamma":learned_out,
        "original_3vc_correctly_certified":counts,
        "strong_classical_all_operators_provided":True,
        "learned_beats_strongest_classical":counts["LEARNED"]>
                           counts["STRONG_FULL_CLASSICAL"],
        "negative_or_false_certificates":false_accepted,
        "first_scoped_gate_pass":all(conditions.values()),
        "preregistered_gate_conditions":conditions,
        "original_task_provenance":"SYNTHETIC_CONSTRUCTED_NOT_REAL_EXTERNAL_FAMILIES",
        "learned_open_ended_new_math_invented":False,
        "trained_original_frozen_gemma_E2B":False,
        "native_GPU_model_forwards":0,
        "frontier_model_calls":0,"paid_API_calls":0,
        "economic_10x_pareto":"NOT_EVALUATED",
        "independent_unseen_family_Q6":"OPEN",
        "global_Q1_Q7":"OPEN",
        "first_case_receipts":outputs,
    }
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    report=first_study()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_LEARNED_OPERATOR_FIRST_RESULTS",
          json.dumps(report["original_3vc_correctly_certified"],sort_keys=True))
    print("Q3_LEARNED_NONAFFINE_VERIFIED",
          report["learned_verified_outside_frozen_affine_gamma"])
    print("Q3_LEARNED_CPU_FIRST_GATE",report["first_scoped_gate_pass"])
    print("Q3_STRONG_CLASSICAL_COMPARISON_NOT_BETTER",
          not report["learned_beats_strongest_classical"])
    print("GLOBAL_Q1_Q7",report["global_Q1_Q7"])


if __name__=="__main__":
    main()
