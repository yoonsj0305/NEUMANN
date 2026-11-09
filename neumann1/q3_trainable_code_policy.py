"""Trainable Q3 program proposal policy (not another fixed domain grammar).

Use an open-weight local code model to generate *new full algorithms*, then
update its proposal weights using independently SOURCE-certified program traces
produced by GenerativeProgramInventor. That is actual model adaptation, not
an AST cache or a source-candidate priority reorder.

Costs: loading and training models requires hardware and disk resources.
This module never provisions GPUs or consumes paid inference services.
Training is explicit and offline; do not fine-tune on heldout target gold.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence


DEFAULT_MODEL="Qwen/Qwen2.5-Coder-0.5B-Instruct"


def _dependencies():
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "opt-in install required: torch transformers; model not loaded") from exc
    return torch,AutoModelForCausalLM,AutoTokenizer


class LocalCausalCodePolicy:
    def __init__(self,*,model_name=DEFAULT_MODEL,adapter_path=None,
                 max_new_tokens=400,temperature=0.3):
        if not 32<=max_new_tokens<=2048 or not 0<temperature<=1:
            raise ValueError("finite generation bounds required")
        torch,Model,Tokenizer=_dependencies()
        self.torch=torch
        self.tokenizer=Tokenizer.from_pretrained(
            model_name,trust_remote_code=False)
        self.model=Model.from_pretrained(
            model_name,trust_remote_code=False)
        if adapter_path is not None:
            try:
                from peft import PeftModel
            except ImportError as exc:
                raise RuntimeError(
                    "LoRA adapters require optional peft dependency") from exc
            self.model=PeftModel.from_pretrained(
                self.model,adapter_path,is_trainable=False)
        self.model.eval()
        self.max_new_tokens=max_new_tokens
        self.temperature=temperature
        self.device=next(self.model.parameters()).device

    def propose(self,prompt):
        msgs=[
            {"role":"system","content":
             "You synthesize correct general Python algorithms from source "
             "input/output. Output only a single transform(x) function, "
             "no imports, no comments outside Python source."},
            {"role":"user","content":prompt},
        ]
        if self.tokenizer.chat_template is not None:
            rendered=self.tokenizer.apply_chat_template(
                msgs,tokenize=False,add_generation_prompt=True)
        else:
            rendered=msgs[0]["content"]+"\n"+prompt+"\nPROGRAM:\n"
        tokens=self.tokenizer(
            rendered,return_tensors="pt",truncation=True,
            max_length=1536).to(self.device)
        with self.torch.inference_mode():
            output=self.model.generate(
                **tokens,do_sample=True,temperature=self.temperature,
                top_p=0.9,max_new_tokens=self.max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id)
        text=self.tokenizer.decode(
            output[0][tokens["input_ids"].shape[1]:],
            skip_special_tokens=True).strip()
        fence=chr(96)*3
        if fence in text:
            chunks=text.split(fence)
            if len(chunks)>=3:
                body=chunks[1].lstrip()
                if body.startswith("python"):
                    body=body[len("python"):].lstrip()
                text=body.strip()
        return text


def source_training_rows(path):
    path=Path(path)
    records=[]
    source_bytes=path.read_bytes()
    for i,line in enumerate(source_bytes.decode("utf-8").splitlines()):
        if not line.strip():
            continue
        record=json.loads(line)
        if (record.get("schema")!="NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1"
                or record.get("provenance")!="ORIGINAL_SOURCE_ONLY"
                or not isinstance(record.get("pairs"),list)
                or not record["pairs"]
                or not isinstance(record.get("program"),str)
                or record.get("independent_checks",0)<1):
            raise ValueError(
                "training file includes non-source/uncertified proposal")
        actual=hashlib.sha256(record["program"].encode()).hexdigest()
        if record.get("sha256")!=actual:
            raise ValueError("tampered training program SHA")
        records.append(record)
    return records,hashlib.sha256(source_bytes).hexdigest()


def finetune_source_policy(
        source_jsonl,adapter_output,*,model_name=DEFAULT_MODEL,
        max_steps=40,lr=0.00015,rank=4,seed=1007):
    """LoRA gradient update of generator weights on prior certified SOURCE.

    Does NOT train on target test answers or private reference programs.
    The model learns to produce a *code program* when conditioned on source
    examples. The loop does not promise improved external task accuracy.
    """
    if (not 1<=max_steps<=10000 or not 0<lr<=0.01 or
            not 1<=rank<=32):
        raise ValueError("bounded explicit training contract")
    source,source_sha=source_training_rows(source_jsonl)
    if not source:
        raise ValueError("no independently source-certified programs to learn")
    torch,Model,Tokenizer=_dependencies()
    try:
        from peft import LoraConfig,get_peft_model
    except ImportError as exc:
        raise RuntimeError("optional peft package required") from exc
    torch.manual_seed(seed)
    tokenizer=Tokenizer.from_pretrained(model_name,trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token=tokenizer.eos_token
    base=Model.from_pretrained(model_name,trust_remote_code=False)
    config=LoraConfig(
        r=rank,lora_alpha=rank*2,lora_dropout=0.0,
        bias="none",task_type="CAUSAL_LM",
        target_modules=["q_proj","v_proj"])
    model=get_peft_model(base,config)
    model.train()
    device=next(model.parameters()).device
    optimizer=torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad),
        lr=lr)
    losses=[]
    for step in range(max_steps):
        row=source[step%len(source)]
        preamble=(
            "Infer a reusable Python transform(x) program from these "
            "independently certified SOURCE observations. Output only code.\n"+
            "\n".join(
                "Input: "+json.dumps(pair[0],ensure_ascii=True)+
                "\nOutput: "+json.dumps(pair[1],ensure_ascii=True)
                for pair in row["pairs"])+"\nPROGRAM:\n")
        completion=row["program"]+tokenizer.eos_token
        prompt_ids=tokenizer(
            preamble,add_special_tokens=False)["input_ids"]
        full_ids=tokenizer(
            preamble+completion,add_special_tokens=False,
            truncation=True,max_length=1536)["input_ids"]
        if len(full_ids)<=len(prompt_ids):
            raise ValueError("training example truncated target code")
        # Teacher-forcing loss only on previously SOURCE-certified code,
        # never on the prompt or original TARGET outputs.
        labels=[-100]*len(prompt_ids)+full_ids[len(prompt_ids):]
        inputs=torch.tensor([full_ids],dtype=torch.long,device=device)
        targets=torch.tensor([labels],dtype=torch.long,device=device)
        optimizer.zero_grad(set_to_none=True)
        loss=model(input_ids=inputs,labels=targets).loss
        if not torch.isfinite(loss):
            raise ValueError("nonfinite model learning loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            (p for p in model.parameters() if p.requires_grad),1.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    directory=Path(adapter_output)
    directory.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(directory)
    tokenizer.save_pretrained(directory)
    manifest={
        "schema":"NEUMANN.Q3.SOURCE-PROGRAM-LORA.v1",
        "base_model":model_name,"source_sha256":source_sha,
        "source_programs":len(source),"steps":max_steps,
        "learning_rate":lr,"rank":rank,"seed":seed,
        "loss_first":losses[0],"loss_last":losses[-1],
        "no_target_gold_or_external_solution_training":True,
        "no_claim_of_generalization_from_training_loss":True}
    (directory/"neumann_source_training_manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--sources",required=True)
    p.add_argument("--adapter-output",required=True)
    p.add_argument("--model",default=DEFAULT_MODEL)
    p.add_argument("--steps",type=int,default=40)
    p.add_argument("--seed",type=int,default=1007)
    args=p.parse_args()
    print(json.dumps(
        finetune_source_policy(
            args.sources,args.adapter_output,model_name=args.model,
            max_steps=args.steps,seed=args.seed),indent=2))
