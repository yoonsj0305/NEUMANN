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
        # Never silently delete original SOURCE evidence to fit a model:
        # abstain if memory+problem cannot fit the actual prompt budget.
        tokens=self.tokenizer(
            rendered,return_tensors="pt",add_special_tokens=False,
            truncation=False)
        if tokens["input_ids"].shape[1] > 4096:
            raise ValueError("SOURCE_PROMPT_EXCEEDS_CONTEXT:ABSTAIN")
        tokens=tokens.to(self.device)
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
                or record.get("independent_checks",0)<1):
            raise ValueError(
                "training file includes non-source/uncertified proposal")
        actual=hashlib.sha256(record["program"].encode()).hexdigest()
        if record.get("sha256")!=actual:
            raise ValueError("tampered training program SHA")
        records.append(record)
    return records,hashlib.sha256(source_bytes).hexdigest()


def certified_source_memory(rows, *, runner=None):
    """Re-execute all SOURCE labels once before learning or reuse."""
    from .open_program_inventor import IsolatedPython
    from .q3_single_discovery_core import SourceMethodMemory
    if not rows or len(rows) > 4096:
        raise ValueError("bounded nonempty original SOURCE teachers required")
    memory = SourceMethodMemory(
        runner if runner is not None else IsolatedPython(max_seconds=8),
        max_episodes=len(rows))
    memory.import_source_teachers(rows)
    memory.freeze()
    return memory


def recertify_source_rows(rows, *, runner=None):
    return tuple(
        row.identity for row in
        certified_source_memory(rows,runner=runner).episodes)


def contextual_training_prompt(row, memory):
    """Leave SELF out: learn method transfer rather than answer copying.

    This is exactly the same two-method SOURCE-only context as deployment B/C.
    Neither input examples nor self program can be retrieved from prior memory.
    """
    identity=row.get("original_id",row.get("source_id"))
    if identity is None:
        raise ValueError("no source identity for meta-training")
    identity=str(identity)
    if not identity.startswith("source-teacher/"):
        identity="source-teacher/"+identity
    if identity not in {entry.source_id for entry in memory.episodes}:
        raise ValueError("training source not in certified memory")
    context=memory.context(
        excluded_ids=(identity,),max_methods=2,max_chars_per_method=320)
    if not context:
        raise ValueError("no disjoint method from which to learn")
    return source_discovery_prompt(row["pairs"][:6],
                                   method_context=context)


def finetune_source_policy(
        source_jsonl,adapter_output,*,model_name=DEFAULT_MODEL,
        model_revision=None,max_steps=40,lr=0.00015,rank=4,seed=1007,
        contextual_methods=False,source_refutation_training=False,
        onpolicy_repair_episodes_path=None):
    """LoRA gradient update of generator weights on prior certified SOURCE.

    Does NOT train on target test answers or private reference programs.
    The model learns to produce a *code program* when conditioned on source
    examples. The loop does not promise improved external task accuracy.
    """
    if (not 1<=max_steps<=10000 or not 0<lr<=0.01 or
            not 1<=rank<=32):
        raise ValueError("bounded explicit training contract")
    if (source_refutation_training or onpolicy_repair_episodes_path) and not contextual_methods:
        raise ValueError("repair learning requires shared method-context training")
    if source_refutation_training and onpolicy_repair_episodes_path:
        raise ValueError("synthetic and on-policy curricula are distinct A/B controls")
    source,source_sha=source_training_rows(source_jsonl)
    if not source:
        raise ValueError("no independently source-certified programs to learn")
    certified_memory=certified_source_memory(source)
    teacher_receipts=tuple(e.identity for e in certified_memory.episodes)
    if contextual_methods and len(teacher_receipts)<2:
        raise ValueError("meta-learning requires >=2 independent source methods")
    refutations=[]
    if source_refutation_training:
        from .q3_refutation_learning import source_refutation_episodes
        refutations=source_refutation_episodes(
            source,certified_memory,certified_memory.runner,
            max_per_teacher=2)
        if len(refutations)<2:
            raise ValueError("no SOURCE-falsified AST mutation repair episodes")
    if onpolicy_repair_episodes_path:
        from .q3_onpolicy_repair import verify_onpolicy_episodes
        raw=[
            json.loads(line)
            for line in Path(onpolicy_repair_episodes_path).open(
                encoding="utf-8") if line.strip()]
        refutations=verify_onpolicy_episodes(
            source,certified_memory,certified_memory.runner,raw)
        if len(refutations)<2:
            raise ValueError("at least 2 real model-generated SOURCE failures required")
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
        row=source[step%len(source)]
        # Match the live SOURCE-only 6-example prompt *exactly*, rather
        # than training with a separate text format never seen at inference.
        teacher_pairs=row["pairs"][:6]
        prompt=(contextual_training_prompt(row,certified_memory)
                if contextual_methods else source_discovery_prompt(teacher_pairs))
        completion=row["program"]+tokenizer.eos_token
        if (source_refutation_training or onpolicy_repair_episodes_path) and step%2==1:
            repair=refutations[(step//2)%len(refutations)]
            prompt=repair["prompt"]
            completion=repair["program"]+tokenizer.eos_token
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
        "prompt_contract":"source_discovery_prompt+chat_template.v1",
        "contextual_method_training":bool(contextual_methods),
        "leave_self_out_from_past_methods":bool(contextual_methods),
        "source_counterexample_repair_training":bool(
            source_refutation_training or onpolicy_repair_episodes_path),
        "repair_negative_origin":(
            "REAL_FROZEN_MODEL_GENERATION" if onpolicy_repair_episodes_path else
            "SYNTHETIC_AST_MUTATION" if source_refutation_training else
            "NONE"),
        "model_generated_falsified_repairs":(
            len(refutations) if onpolicy_repair_episodes_path else 0),
        "source_falsified_repair_episodes":len(refutations),
        "onpolicy_source_file_sha256":(
            hashlib.sha256(Path(onpolicy_repair_episodes_path).read_bytes()).hexdigest()
            if onpolicy_repair_episodes_path else None),
        "repair_teacher_sources":sorted({
            x["original_source_id"] for x in refutations}),
        "repair_witness_sha256":hashlib.sha256(
            json.dumps([x["witness_sha256"] for x in refutations],
                       sort_keys=True).encode()).hexdigest(),
        "source_sha256":source_sha,
        "source_programs":len(source),
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
    p.add_argument("--contextual-method-training",action="store_true")
    p.add_argument("--source-refutation-training",action="store_true")
    p.add_argument("--onpolicy-source-repairs",default=None,
                   help="frozen model-generated SOURCE failures, independently recertified")
    args=p.parse_args()
    print(json.dumps(
        finetune_source_policy(
            args.sources,args.adapter_output,model_name=args.model,
            model_revision=args.model_revision,
            max_steps=args.steps,seed=args.seed,
            contextual_methods=args.contextual_method_training,
            source_refutation_training=args.source_refutation_training,
            onpolicy_repair_episodes_path=args.onpolicy_source_repairs),indent=2))
