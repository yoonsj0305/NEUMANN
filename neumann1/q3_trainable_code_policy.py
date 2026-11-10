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

from .q3_prompt_contract import (
    model_prefix,model_training_ids,source_discovery_prompt)



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
    def __init__(self,*,model_name=DEFAULT_MODEL,model_revision=None,
                 adapter_path=None,max_new_tokens=400,temperature=0.3,
                 seed=1007):
        if not 32<=max_new_tokens<=2048 or not 0<temperature<=1:
            raise ValueError("finite generation bounds required")
        torch,Model,Tokenizer=_dependencies()
        self.torch=torch
        self.tokenizer=Tokenizer.from_pretrained(
            model_name,trust_remote_code=False,revision=model_revision)
        # Pin weights as well as tokenizer. BF16 memory reduces host
        # requirement for an unbiased CPU-only comparison.
        self.model=Model.from_pretrained(
            model_name,trust_remote_code=False,
            revision=model_revision,
            torch_dtype=torch.bfloat16)
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
        self.seed=seed
        self.device=next(self.model.parameters()).device

    def propose(self,prompt):
        rendered=model_prefix(self.tokenizer,prompt)
        tokens=self.tokenizer(
            rendered,return_tensors="pt",add_special_tokens=False,
            truncation=True,max_length=1536).to(self.device)
        # Source-prompt-derived RNG makes first proposals IDENTICAL across
        # the opaque-error and typed-counterexample causal ablations.
        # Later prompts legitimately diverge only when feedback differs.
        generated_seed=(self.seed+int(hashlib.sha256(
            prompt.encode()).hexdigest()[:8],16))%(2**31)
        self.torch.manual_seed(generated_seed)
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
                or not isinstance(record.get("independent_checks"),int)
                or not 1<=record["independent_checks"]<len(record["pairs"])):
            raise ValueError(
                "training file includes non-source/uncertified proposal")
        actual=hashlib.sha256(record["program"].encode()).hexdigest()
        if record.get("sha256")!=actual:
            raise ValueError("tampered training program SHA")
        records.append(record)
    return records,hashlib.sha256(source_bytes).hexdigest()


def recertify_source_rows(rows, *, runner=None):
    """No self-signed JSON may train weights without executing all SOURCE labels.

    Reuse the exact same SOURCE-only memory verifier, not a second
    task-domain-specific oracle. No isolated Docker => fail closed.
    """
    from .open_program_inventor import IsolatedPython
    from .q3_single_discovery_core import SourceMethodMemory
    if not rows or len(rows) > 4096:
        raise ValueError("bounded nonempty original SOURCE teachers required")
    memory = SourceMethodMemory(
        runner if runner is not None else IsolatedPython(max_seconds=8),
        max_episodes=len(rows))
    imported = memory.import_source_teachers(rows)
    memory.freeze()
    return tuple(entry.identity for entry in imported)


def finetune_source_policy(
        source_jsonl,adapter_output,*,model_name=DEFAULT_MODEL,
        model_revision=None,max_steps=40,lr=0.00015,rank=4,seed=1007,
        training_objective="source_program_imitation"):
    """LoRA gradient update of generator weights on prior certified SOURCE.

    Does NOT train on target test answers or private reference programs.
    The model learns to produce a *code program* when conditioned on source
    examples. The loop does not promise improved external task accuracy.
    """
    if (not 1<=max_steps<=10000 or not 0<lr<=0.01 or
            not 1<=rank<=32):
        raise ValueError("bounded explicit training contract")
    if training_objective not in (
            "source_program_imitation","source_repair","source_hypothesis_repair"):
        raise ValueError("unknown Q3 learning objective")
    source,source_sha=source_training_rows(source_jsonl)
    if not source:
        raise ValueError("no independently source-certified programs to learn")
    teacher_receipts=recertify_source_rows(source)
    # A real invention-policy update conditions the new program on an
    # *actual failed executable method* and an independent SOURCE
    # counterexample, NOT merely on unrelated solved program texts.
    if training_objective in ("source_repair","source_hypothesis_repair"):
        from .open_program_inventor import IsolatedPython
        from .q3_source_repair_learning import recertified_repair_prompt
        runner=IsolatedPython(max_seconds=8)
        if training_objective=="source_hypothesis_repair":
            from .q3_latent_hypothesis_policy import recertified_hypothesis_repair_row
        learning_rows=[]
        for row in source:
            if "repair_prior_program" not in row:
                continue
            if training_objective=="source_hypothesis_repair":
                prompt,teacher_completion,phase=recertified_hypothesis_repair_row(row,runner)
            else:
                prompt,phase=recertified_repair_prompt(row,runner)
                teacher_completion=row["program"]
            learning_rows.append((prompt,teacher_completion,phase,
                                  row["repair_prior_sha256"],row["sha256"]))
        if not learning_rows:
            raise ValueError("no independently SOURCE-falsified repair episodes")
    else:
        learning_rows=[]
        for row in source:
            n=row["independent_checks"]
            # Never silently train on the reserved independent SOURCE check.
            prompt=source_discovery_prompt(row["pairs"][:-n])
            learning_rows.append((prompt,row["program"],
                                  "SOURCE_PROGRAM_IMITATION","",row["sha256"]))
    torch,Model,Tokenizer=_dependencies()
    try:
        from peft import LoraConfig,get_peft_model
    except ImportError as exc:
        raise RuntimeError("optional peft package required") from exc
    torch.manual_seed(seed)
    tokenizer=Tokenizer.from_pretrained(model_name,trust_remote_code=False,
                                       revision=model_revision)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token=tokenizer.eos_token
    base=Model.from_pretrained(model_name,trust_remote_code=False,
                              revision=model_revision)
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
        prompt,teacher_code,_,_,_=learning_rows[step%len(learning_rows)]
        # This exact prompt is seen by the live local model on SOURCE
        # refutation. All targets below are *certified executable programs*
        # from prior original-author SOURCE episodes, never TARGET answers.
        completion=teacher_code+tokenizer.eos_token
        full_ids,labels=model_training_ids(
            tokenizer,prompt,completion,max_length=1536)
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
        "base_model":model_name,"model_revision":model_revision,
        "prompt_contract":("source_hypothesis_repair+chat_template.v1"\n            if training_objective=="source_hypothesis_repair"\n            else "source_discovery_prompt+chat_template.v1"),
        "source_sha256":source_sha,
        "source_programs":len(source),
        "training_objective":training_objective,
        "repair_examples":sum(phase in ("TRAIN_SOURCE","INDEPENDENT_SOURCE")
                              for _,_,phase,_,_ in learning_rows),
        "training_pairs_sha256":hashlib.sha256(json.dumps(
            [(phase,prior,cert) for _,_,phase,prior,cert in learning_rows],
            sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "docker_source_reverified":len(teacher_receipts),
        "source_proof_receipts_sha256":hashlib.sha256(
            json.dumps(teacher_receipts).encode()).hexdigest(),
        "steps":max_steps,
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
    p.add_argument("--model-revision",default=None)
    p.add_argument("--steps",type=int,default=40)
    p.add_argument("--seed",type=int,default=1007)
    p.add_argument("--objective",choices=(
        "source_program_imitation","source_repair","source_hypothesis_repair"),
        default="source_program_imitation")
    args=p.parse_args()
    print(json.dumps(
        finetune_source_policy(
            args.sources,args.adapter_output,model_name=args.model,
            model_revision=args.model_revision,
            max_steps=args.steps,seed=args.seed,
            training_objective=args.objective),indent=2))
