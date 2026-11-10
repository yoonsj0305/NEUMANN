"""One task-agnostic neural predictive-state core, not a code generator.

ROOT CAUSE ADDRESSED: previous SOURCE->latent JSON interface produced a
template list of placeholder strings, so C never received gradient. This
core does NOT require the model to first print valid symbolic hypotheses.
The SAME learned weights directly represent observed context in hidden states,
predict permitted query consequences, and update from trusted SOURCE errors.

No domain/family algorithm, program cache, DSL, external TARGET labels or
label-specific code. Answer options are supplied as generic query metadata.
A change in hidden representation or cross-domain accuracy is evidence to
measure, NOT automatically autonomous invention of a concept or Q3/Q6 PASS.
"""
from __future__ import annotations

import json
import math
from hashlib import sha256


def canonical(x):
    return json.dumps(x,ensure_ascii=True,sort_keys=True,
                      separators=(",",":"),allow_nan=False)


class PredictiveStatePolicy:
    def __init__(self,*,revision,seed=1007,lr=0.00015,
                 max_context_tokens=4096,max_updates=4):
        if not 1<=max_updates<=16 or not 512<=max_context_tokens<=8192:
            raise ValueError("bounded shared predictive learner required")
        from .q3_trainable_code_policy import _dependencies
        try:
            from peft import LoraConfig,get_peft_model
        except ImportError as e:
            raise RuntimeError("real LoRA required") from e
        torch,Model,Tokenizer=_dependencies()
        self.torch=torch
        torch.manual_seed(seed)
        self.tokenizer=Tokenizer.from_pretrained(
            "Qwen/Qwen2.5-Coder-0.5B-Instruct",
            revision=revision,trust_remote_code=False)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token=self.tokenizer.eos_token
        base=Model.from_pretrained(
            "Qwen/Qwen2.5-Coder-0.5B-Instruct",
            revision=revision,trust_remote_code=False,
            torch_dtype=torch.float32)
        self.model=get_peft_model(base,LoraConfig(
            r=4,lora_alpha=8,lora_dropout=0.0,
            bias="none",task_type="CAUSAL_LM",
            target_modules=["q_proj","v_proj"]))
        self.device=next(self.model.parameters()).device
        self.optimizer=torch.optim.AdamW(
            (p for p in self.model.parameters() if p.requires_grad),
            lr=lr)
        self.max_context_tokens=max_context_tokens
        self.max_updates=max_updates
        self.update_count=0
        self.seed=seed

    def _prompt(self,context,memory,query):
        if not isinstance(query,dict) or not (
                isinstance(query.get("answer_set"),list)
                and 2<=len(query["answer_set"])<=12):
            raise ValueError("bounded original-author answer alternatives required")
        choices=query["answer_set"]
        if len(set(choices))!=len(choices) or not all(
                isinstance(c,str) and len(c)<=96 for c in choices):
            raise ValueError("invalid answer category")
        if not all(x.get("scope")=="TRUSTED_SOURCE_ONLY" for x in memory):
            raise ValueError("no TARGET labels permitted in predictive memory")
        user=canonical({
            "observed_context":context,
            "past_verified_SOURCE":memory,
            "new_unlabeled_observation_query":query,
            "instruction":"Infer the relation and select the one answer "
                          "that follows. Do not assume a known programming "
                          "language or a fixed family-specific solver.",
        })
        messages=[
            {"role":"system","content":"Infer a general latent relation from "
             "authorized observations. Predict the consequence of the new "
             "input. Output only one of the supplied answer alternatives."},
            {"role":"user","content":user},
        ]
        if self.tokenizer.chat_template is not None:
            prefix=self.tokenizer.apply_chat_template(
                messages,tokenize=False,add_generation_prompt=True)
        else:
            prefix="SYSTEM: "+messages[0]["content"]+"\nUSER: "+user+"\nAnswer:"
        ids=self.tokenizer(
            prefix,add_special_tokens=False,
            truncation=False)["input_ids"]
        if len(ids)>self.max_context_tokens-24:
            raise ValueError("SOURCE context exceeds model input budget")
        return ids,choices

    def _choice_loglik(self,prefix,choice):
        torch=self.torch
        suffix=self.tokenizer(
            " "+choice,add_special_tokens=False)["input_ids"]
        if not suffix or len(suffix)>24:
            raise ValueError("invalid outcome label tokenization")
        ids=prefix+suffix
        x=torch.tensor([ids],device=self.device,dtype=torch.long)
        output=self.model(input_ids=x)
        logits=output.logits[0,len(prefix)-1:len(ids)-1,:]
        target=torch.tensor(suffix,dtype=torch.long,device=self.device)
        token_logprob=torch.log_softmax(logits,dim=-1).gather(
            -1,target.view(-1,1)).squeeze(-1)
        # Normalize by answer-token count to avoid length artifacts;
        # scores are relative, NOT calibrated posterior probabilities.
        return token_logprob.mean()

    def _scores(self,context,memory,query):
        prefix,choices=self._prompt(context,memory,query)
        return self.torch.stack([
            self._choice_loglik(prefix,label) for label in choices]),choices

    def predict(self,context,memory,query):
        self.model.eval()
        with self.torch.inference_mode():
            scores,choices=self._scores(context,memory,query)
        idx=int(scores.argmax().item())
        return {
            "prediction":choices[idx],
            "raw_relative_loglik":[round(float(x),6) for x in scores.cpu()],
            # This path predicts original-author answer *labels*. Hidden
            # Transformer activations are NOT evidence that a reusable
            # causal concept, state coordinate or invention policy formed.
            "representation":"PRETRAINED_HIDDEN_STATE_OPTION_SCORING",
            "explicit_new_concept_discovered":False,
            "hypothesis_intervention_revision_learned":False,
            "calibrated_probability":False,
            "no_human_authored_domain_answer_rule":True,
        }

    def learn_source(self,context,memory,query,observed,*,evidence_id):
        if self.update_count>=self.max_updates:
            return None
        if not isinstance(evidence_id,str) or not evidence_id:
            raise ValueError("signed SOURCE provenance required")
        if observed not in query.get("answer_set",[]):
            raise ValueError("SOURCE observation outside declared answer space")
        self.model.eval()
        # First infer relative outcome probabilities without retaining any
        # long-sequence graphs. Cross-entropy exact gradient at this model
        # point is sum_i (p_i - 1[i=gold]) * grad(score_i).
        with self.torch.inference_mode():
            initial_scores,choices=self._scores(context,memory,query)
            probability=self.torch.softmax(
                initial_scores.detach().float(),dim=0).clone()
            observed_index=choices.index(observed)
            loss_value=float(-self.torch.log(
                probability[observed_index].clamp_min(1e-12)).cpu())
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        prefix,_=self._prompt(context,memory,query)
        trainable=[p for p in self.model.parameters() if p.requires_grad]
        before=[p.detach().clone() for p in trainable]
        for i,label in enumerate(choices):
            coefficient=float(probability[i])-(1.0 if i==observed_index else 0.0)
            if abs(coefficient)<1e-9:
                continue
            # Exactly one candidate's graph lives at once, crucial for
            # CPU local and 7 GB GitHub runner memory limits.
            score=self._choice_loglik(prefix,label)
            (coefficient*score).backward()
        self.torch.nn.utils.clip_grad_norm_(trainable,1.0)
        self.optimizer.step()
        delta=sum(float((p.detach()-b).abs().sum().cpu())
                  for p,b in zip(trainable,before))
        self.model.eval()
        self.update_count+=1
        return {
            "update":self.update_count,
            "actual_trainable_weight_delta_l1":delta,
            "source_prediction_loss":loss_value,
            "evidence_id":evidence_id,
            "scope":"TRUSTED_SOURCE_ONLY",
            "learning_objective":"OBSERVED_LABEL_CROSS_ENTROPY",
            "independent_concept_invention_demonstrated":False,
            "learning_strategy_self_improvement_demonstrated":False,
        }
