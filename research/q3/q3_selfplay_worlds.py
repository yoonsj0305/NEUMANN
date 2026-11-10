"""NEUMANN Q3 self-generated executable worlds: unsupervised task curriculum.

The SAME pretrained code model, not a developer, invents every executable
transform. The existing isolated Python verifier executes model-authored
programs to synthesize SOURCE pairs and independently checks new inputs.
Then a separate policy may learn inverse program discovery from these
source-certified SELF_GENERATED worlds. No hand-coded answer operator,
ARC/task-family solver, external TARGET gold, or task-ID dispatch.

This is SELF-PLAY: a synthetic curriculum. A pass here is NOT independent
real AUTHOR/Q3 proof. Training/heldout task programs are SHA-disjoint.
"""
from __future__ import annotations

import argparse,hashlib,json,random
from pathlib import Path

from neumann1.open_program_inventor import (
    IsolatedPython,UnsafeProposal,validate_code,source_same_value)
from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy

SCHEMA="NEUMANN.Q3.SELF-AUTHORED-EXECUTABLE-WORLD.v1"
KINDS=("integer","array","nested-array","object")


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=True,
                      allow_nan=False,separators=(",",":"))


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def make_json_inputs(kind,seed,*,n=6):
    """General typed JSON inputs, NEVER a target answer transform."""
    if kind not in KINDS or not 4<=n<=12:
        raise ValueError("generic bounded JSON type required")
    rng=random.Random(seed)
    seen=set()
    out=[]
    while len(out)<n:
        if kind=="integer":
            v=rng.randint(-20,30)
        elif kind=="array":
            v=[rng.randint(-9,15)
               for _ in range(rng.randint(3,8))]
        elif kind=="nested-array":
            v=[[rng.randint(-4,8) for _ in range(rng.randint(2,5))]
               for _ in range(rng.randint(2,5))]
        else:
            v={"a":rng.randint(-10,10),"b":rng.randint(-10,10),
               "items":[rng.randint(0,9) for _ in range(4)]}
        key=canonical(v)
        if key in seen:continue
        seen.add(key);out.append(v)
    return out


def invent_worlds(*,model_revision,out_train,out_holdout,out_report,
                  candidates=32,seed=1007):
    if not 8<=candidates<=96:
        raise ValueError("fixed finite self-play cost bound required")
    model=LocalCausalCodePolicy(
        model_revision=model_revision,max_new_tokens=320,
        temperature=0.45,seed=seed,max_context_tokens=4096)
    runner=IsolatedPython(max_seconds=8)
    worlds=[];attempts=[]
    seen_code=set()
    for index in range(candidates):
        kind=KINDS[index%len(KINDS)]
        prompt=(
            "Invent a new nontrivial, deterministic executable Python "
            "transformation method for a JSON "+kind+" input x. Write "
            "ONLY a single def transform(x) function and its actual "
            "algorithm. Do not return x unchanged. Avoid imports, "
            "external calls, random numbers and constant outputs. "
            "Choose the method yourself; no human-defined solution or "
            "target result is given. Make it work for varied inputs."
        )
        model.seed=seed+index*1009
        row={"attempt":index,"kind":kind}
        try:
            code=validate_code(model.propose(prompt))
        except (ValueError,UnsafeProposal) as exc:
            row["status"]="ABSTAIN_INVALID_MODEL_PROGRAM"
            row["error_type"]=type(exc).__name__
            attempts.append(row);continue
        fingerprint=sha(code)
        if fingerprint in seen_code:
            row["status"]="ABSTAIN_DUPLICATE_CODE"
            attempts.append(row);continue
        seen_code.add(fingerprint)
        inputs=make_json_inputs(kind,seed+index*37,n=6)
        verified=runner.evaluate(code,inputs)
        if verified.status!="EXECUTED" or len(verified.outputs)!=6:
            row["status"]="ABSTAIN_NOT_EXECUTABLE_ON_VARIATION"
            attempts.append(row);continue
        outputs=verified.outputs
        if (any(len(canonical(y))>2000 for y in outputs) or
                sum(not source_same_value(x,y)
                    for x,y in zip(inputs,outputs))<4 or
                len({canonical(y) for y in outputs})<3):
            row["status"]="ABSTAIN_TRIVIAL_OR_DEGENERATE_WORLD"
            attempts.append(row);continue
        # No human-supplied answer: the exact method is authored by model.
        world={
            "schema":SCHEMA,
            "world_id":fingerprint,
            "program":code,
            "program_sha256":fingerprint,
            "authorship":"FROZEN_PRETRAINED_MODEL_GENERATED",
            "program_generation_type":kind,
            "source_train":list(zip(inputs[:3],outputs[:3])),
            "source_sealed_check":list(zip(inputs[3:5],outputs[3:5])),
            "synthetic_test":list(zip(inputs[5:],outputs[5:])),
            "all_labels_from_isolated_execution":True,
            "original_author_target_gold_read":False,
        }
        worlds.append(world)
        row["status"]="MODEL_EXECUTABLE_WORLD_ACCEPTED"
        row["sha256"]=fingerprint
        attempts.append(row)
        print("Q3_SELF_PLAY_WORLD_INVENTED",{
            "index":index,"kind":kind,"program_sha256":fingerprint},
            flush=True)
    # V2 precommitted count-independent-of-test partition protocol:
    # rank ONLY program SHA fingerprints under a fixed new seed salt.
    # Unlike the original 1-in-5 hash split, any >=8 accepted programs
    # now reserve at least 3 entire distinct PROGRAMS as heldout.
    # We never inspect source-prediction outcomes to pick those IDs.
    worlds.sort(key=lambda w:sha(
        "q3.selfplay.v2.seed.3007/"+w["world_id"]))
    if len(worlds)>=8:
        heldout_count=max(3,round(len(worlds)*0.35))
    elif len(worlds)>=2:
        heldout_count=max(1,len(worlds)//3)
    else:
        heldout_count=0
    heldout=worlds[:heldout_count]
    train=worlds[heldout_count:]
    Path(out_train).write_text(
        "".join(canonical(w)+"\n" for w in train))
    Path(out_holdout).write_text(
        "".join(canonical(w)+"\n" for w in heldout))
    summary={
        "schema":"NEUMANN.Q3.AUTOGENERATED-WORLD-CURRICULUM-REPORT.v1",
        "model_revision":model_revision,
        "attempted_worlds":candidates,
        "generation_seed":seed,
        "heldout_partition_precommit":"q3.selfplay.v2.seed.3007/",
        "verified_nontrivial_worlds":len(worlds),
        "selfplay_training_worlds":len(train),
        "program_disjoint_synthetic_heldout":len(heldout),
        "train_hash":hashlib.sha256(Path(out_train).read_bytes()).hexdigest(),
        "heldout_hash":hashlib.sha256(Path(out_holdout).read_bytes()).hexdigest(),
        "real_author_original_TEST_gold_read":False,
        "no_human_authored_answer_operators":True,
        "synthetic_success_is_not_Q3_generalization":True,
        "q3_global":"OPEN",
        "attempts":attempts,
    }
    Path(out_report).write_text(canonical(summary)+"\n")
    print("Q3_SELF_PLAY_VERIFIED_WORLD_CURRICULUM",{
        k:v for k,v in summary.items() if k!="attempts"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-revision",required=True)
    p.add_argument("--train",required=True)
    p.add_argument("--heldout",required=True)
    p.add_argument("--report",required=True)
    p.add_argument("--candidates",type=int,default=32)
    p.add_argument("--seed",type=int,default=1007)
    a=p.parse_args()
    invent_worlds(model_revision=a.model_revision,
                  out_train=a.train,out_holdout=a.heldout,
                  out_report=a.report,candidates=a.candidates,seed=a.seed)
