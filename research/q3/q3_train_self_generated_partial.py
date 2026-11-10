"""Train the SAME shared open-program neural policy on its own partial SOURCE feedback.

This is a general policy update with no hand-coded task-solving operator.
Unlike positive exact-SOURCE teachers, these pairs are ONLY *relative SOURCE*
improvements. Both are real executable model programs. Their preference is
recomputed by the same no-network Docker SOURCE checker before every update.
No independent SOURCE or original TARGET inputs/outputs are accessed here.
"""
from __future__ import annotations

import argparse,hashlib,json
from pathlib import Path

from neumann1.q3_trainable_code_policy import DEFAULT_MODEL,_dependencies
from neumann1.q3_preference_learning import preference_loss
from neumann1.q3_prompt_contract import source_discovery_prompt
from neumann1.q3_semantic_credit import preference_from_source
from neumann1.open_program_inventor import IsolatedPython,validate_code


SCHEMA="NEUMANN.Q3.SOURCE-ONLY-SELF-GENERATED-PREFERENCE.v1"


def _canon(v):
    return json.dumps(v,ensure_ascii=True,sort_keys=True,
                      separators=(",",":"),allow_nan=False)


def _sha(v):
    return hashlib.sha256(v).hexdigest()


def recertify_partial_pairs(path,runner):
    payload=Path(path).read_bytes()
    items=[]
    ids=set()
    for line in payload.decode().splitlines():
        if not line.strip():continue
        record=json.loads(line)
        if (record.get("schema")!=SCHEMA
            or record.get("independent_source_certified") is not False
            or record.get("original_target_gold_read") is not False
            or record.get("origin")!=
                "TWO_ACTUAL_SAME_MODEL_SOURCE_RUNNABLE_PROPOSALS"):
            raise ValueError("partial preference MUST NOT pretend to certify Q3")
        ident=record.get("task_id")
        if not ident or ident in ids:
            raise ValueError("duplicate or absent SOURCE task ID")
        ids.add(ident)
        pairs=record.get("source_train")
        if not isinstance(pairs,list) or not 1<=len(pairs)<=32:
            raise ValueError("source-only training demonstrations required")
        prompt=source_discovery_prompt(pairs)
        if _sha(prompt.encode())!=record.get("prompt_sha256"):
            raise ValueError("training-source observation changed")
        positive=validate_code(record["positive_program"])
        negative=validate_code(record["negative_program"])
        if (_sha(positive.encode())!=record["positive_program_sha256"] or
            _sha(negative.encode())!=record["negative_program_sha256"]):
            raise ValueError("source program SHA not authenticated")
        actual=preference_from_source(
            pairs,runner,positive,negative,margin=0.02)
        if (actual is None or
            actual["positive_program"]!=positive or
            actual["negative_program"]!=negative or
            actual["positive_credit"]!=record["positive_credit"] or
            actual["negative_credit"]!=record["negative_credit"]):
            raise ValueError("claimed partial improvement refuted by actual SOURCE")
        items.append((prompt,positive,negative,ident))
    if not items:
        raise ValueError("NO_ACTUAL_PARTIAL_SELF_GENERATED_SOURCE_PREFERENCES")
    return items,_sha(payload)


def train(pairs_file,adapter_output,revision,*,max_steps=8,seed=1007,rank=4,
          lr=0.00015):
    if not (1<=max_steps<=100 and 1<=rank<=16 and 0<lr<=0.005):
        raise ValueError("bounded partial-credit training required")
    runner=IsolatedPython(max_seconds=8)
    items,source_sha=recertify_partial_pairs(pairs_file,runner)
    torch,Model,Tokenizer=_dependencies()
    from peft import LoraConfig,get_peft_model
    torch.manual_seed(seed)
    tok=Tokenizer.from_pretrained(
        DEFAULT_MODEL,trust_remote_code=False,revision=revision)
    if tok.pad_token_id is None:tok.pad_token=tok.eos_token
    base=Model.from_pretrained(
        DEFAULT_MODEL,trust_remote_code=False,revision=revision)
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
    margins=[]
    for step in range(max_steps):
        prompt,positive,negative,ident=items[step%len(items)]
        optimizer.zero_grad(set_to_none=True)
        loss,diag=preference_loss(
            model,tok,prompt,positive,negative,
            device=device,beta=1.0,max_length=4096)
        if not torch.isfinite(loss):
            raise ValueError("nonfinite Q3 SOURCE-only preference update")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            (p for p in model.parameters() if p.requires_grad),1.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
        margins.append(diag)
    directory=Path(adapter_output)
    directory.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(directory)
    tok.save_pretrained(directory)
    manifest={
        "schema":"NEUMANN.Q3.UNVERIFIED-PARTIAL-SOURCE-SELF-LEARNING.v1",
        "base_model":DEFAULT_MODEL,
        "model_revision":revision,
        "training_objective":"source_partial_preference",
        "source_sha256":source_sha,
        "source_partial_preference_count":len(items),
        "repair_examples":0,
        "independent_source_certified_preferences":0,
        "original_target_gold_read":False,
        "steps":max_steps,"rank":rank,"learning_rate":lr,
        "loss_first":losses[0],"loss_last":losses[-1],
        "preference_margins":margins,
        "q3_global":"OPEN",
    }
    (directory/"neumann_source_training_manifest.json").write_text(
        _canon(manifest)+"\n")
    print("Q3_ACTUAL_SELF_GENERATED_PARTIAL_CREDIT_WEIGHT_UPDATE",{
        k:v for k,v in manifest.items() if k!="preference_margins"},
        flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--pairs",required=True)
    parser.add_argument("--adapter-output",required=True)
    parser.add_argument("--model-revision",required=True)
    parser.add_argument("--steps",type=int,default=8)
    args=parser.parse_args()
    train(args.pairs,args.adapter_output,args.model_revision,
          max_steps=args.steps)
