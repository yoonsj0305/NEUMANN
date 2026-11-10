"""Learn inverse executable-program discovery from SELF-PLAY worlds only.

Unlike prior 7 SOURCE teacher SFT, the original pretrained model authored the
entire executable curriculum; no human wrote any target transformation.
The only supervision is the generator program's independently re-executed
SOURCE behavior. Synthetic proofs are NOT original author benchmark proofs.
"""
from __future__ import annotations

import argparse,hashlib,json
from pathlib import Path

from neumann1.q3_prompt_contract import (
    source_discovery_prompt,model_training_ids)
from neumann1.q3_trainable_code_policy import DEFAULT_MODEL,_dependencies
from neumann1.open_program_inventor import (
    IsolatedPython,validate_code,source_same_value)
from research.q3.q3_selfplay_worlds import SCHEMA,canonical


def validate_worlds(worlds_file,runner):
    raw=Path(worlds_file).read_bytes()
    result=[]
    visited=set()
    for line in raw.decode().splitlines():
        if not line.strip():continue
        w=json.loads(line)
        if (w.get("schema")!=SCHEMA
            or w.get("authorship")!="FROZEN_PRETRAINED_MODEL_GENERATED"
            or w.get("all_labels_from_isolated_execution") is not True
            or w.get("original_author_target_gold_read") is not False):
            raise ValueError("not a model-authored verified world")
        code=validate_code(w["program"])
        if hashlib.sha256(code.encode()).hexdigest()!=w["program_sha256"]:
            raise ValueError("self-play world code SHA mismatch")
        if code in visited:
            raise ValueError("duplicate executable world")
        visited.add(code)
        examples=(
            w["source_train"]+w["source_sealed_check"]+w["synthetic_test"])
        if len(examples)!=6:
            raise ValueError("world evidence set altered")
        observed=runner.evaluate(code,[x for x,y in examples])
        if observed.status!="EXECUTED" or len(observed.outputs)!=6 or any(
            not source_same_value(got,y)
            for got,(_,y) in zip(observed.outputs,examples)):
            raise ValueError("self-authored teacher failed real executor")
        result.append(w)
    if not 2<=len(result)<=100:
        raise ValueError("not enough independently executable self-play teachers")
    return result,hashlib.sha256(raw).hexdigest()


def train(worlds_file,revision,adapter_output,*,steps=24,seed=1007,
          lr=0.00015,rank=4):
    if not 1<=steps<=64:
        raise ValueError("explicit self-play gradient budget required")
    runner=IsolatedPython(max_seconds=8)
    worlds,source_sha=validate_worlds(worlds_file,runner)
    torch,Model,Tokenizer=_dependencies()
    from peft import LoraConfig,get_peft_model
    torch.manual_seed(seed)
    tok=Tokenizer.from_pretrained(
        DEFAULT_MODEL,revision=revision,trust_remote_code=False)
    if tok.pad_token_id is None:
        tok.pad_token=tok.eos_token
    base=Model.from_pretrained(
        DEFAULT_MODEL,revision=revision,trust_remote_code=False)
    model=get_peft_model(base,LoraConfig(
        r=rank,lora_alpha=2*rank,lora_dropout=0.0,
        bias="none",task_type="CAUSAL_LM",
        target_modules=["q_proj","v_proj"]))
    model.train()
    device=next(model.parameters()).device
    optimizer=torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad),
        lr=lr)
    losses=[]
    for step in range(steps):
        w=worlds[step%len(worlds)]
        prompt=source_discovery_prompt(w["source_train"])
        completion=w["program"]+tok.eos_token
        full_ids,labels=model_training_ids(
            tok,prompt,completion,max_length=4096)
        x=torch.tensor([full_ids],dtype=torch.long,device=device)
        y=torch.tensor([labels],dtype=torch.long,device=device)
        optimizer.zero_grad(set_to_none=True)
        loss=model(input_ids=x,labels=y).loss
        if not torch.isfinite(loss):
            raise ValueError("nonfinite self-generated program-learning loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            (p for p in model.parameters() if p.requires_grad),1.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    output=Path(adapter_output)
    output.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(output)
    tok.save_pretrained(output)
    manifest={
        "schema":"NEUMANN.Q3.MODEL-SELFPLAY-INVENTION-LEARNING.v1",
        "base_model":DEFAULT_MODEL,
        "model_revision":revision,
        "training_objective":"model_generated_program_inverse_induction",
        "self_play_only":True,
        "source_worlds_sha256":source_sha,
        "distinct_model_written_worlds":len(worlds),
        "steps":steps,
        "loss_first":losses[0],
        "loss_last":losses[-1],
        "original_author_TARGET_gold_read":False,
        "independent_original_TASK_tested":False,
        "q3_global":"OPEN",
    }
    (output/"neumann_selfplay_training_manifest.json").write_text(
        canonical(manifest)+"\n")
    print("Q3_SELF_PLAY_REAL_POLICY_GRADIENT",manifest,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--worlds",required=True)
    p.add_argument("--revision",required=True)
    p.add_argument("--adapter",required=True)
    p.add_argument("--steps",type=int,default=24)
    a=p.parse_args()
    train(a.worlds,a.revision,a.adapter,steps=a.steps)
