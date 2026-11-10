"""One neural policy learns latent world hypotheses from real SOURCE evidence.

Unlike SOURCE->Python-code teacher forcing, train world prediction from every
trusted intervention observation, including failures. When a *model-authored*
hypothesis predicts an observation correctly, also train the SAME weights
to reproduce that latent representation. No task-specific rules, oracle gold
or answer-program memory. Actual Q3/Q6 gain requires independent original
A/B/C evidence and is NOT claimed by this implementation.
"""
from __future__ import annotations

from hashlib import sha256
import json


def _canonical(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=True,
                      separators=(",",":"),allow_nan=False)


WORLD_SYSTEM=(
    "Infer a latent causal world model from SOURCE observations. "
    "Return one JSON OBJECT, not a JSON array or markdown. "
    "Its key 'hypotheses' must contain 1 or 2 hypothesis objects. "
    "Each hypothesis has: name (short string), kind ('neumann.latent'), "
    "latent_variables (map of newly hypothesized variables to meanings), "
    "relations (map of testable relationships), and predictions "
    "(map from ACTUAL authorized_query_inputs keys to predicted outcomes). "
    "Do not copy placeholder keys like 'query_id' or template descriptions. "
    "Use ONLY the real query IDs in the user input. No SOURCE answer oracle. "
    "Your concepts may be novel; no Python code or fixed answer DSL required."
)
PREDICTION_SYSTEM=(
    "Predict what the next SOURCE intervention will cause. Given a latent "
    "hypothesis, query and its prior prediction, output exactly the actual "
    "observation as JSON. Never write code or a target answer."
)


def _chat(tokenizer,system,user):
    messages=[{"role":"system","content":system},
              {"role":"user","content":user}]
    if tokenizer.chat_template is None:
        return system+"\n"+user+"\nRESPONSE:\n"
    return tokenizer.apply_chat_template(
        messages,tokenize=False,add_generation_prompt=True)


class TrainableLatentWorldPolicy:
    """One shared trainable world proposer; optional local Qwen+LoRA backend."""

    def __init__(self,*,model_name="Qwen/Qwen2.5-Coder-0.5B-Instruct",
                 revision=None,max_new_tokens=500,max_context_tokens=3072,
                 learning_rate=0.00015,max_updates=32,seed=1007):
        if (not 64<=max_new_tokens<=2048
            or not 512<=max_context_tokens<=8192
            or not 1<=max_updates<=128 or not 0<learning_rate<=0.005):
            raise ValueError("bounded online causal learning required")
        from .q3_trainable_code_policy import _dependencies
        torch,Model,Tokenizer=_dependencies()
        try:
            from peft import LoraConfig,get_peft_model
        except ImportError as exc:
            raise RuntimeError("peft needed for actual neural updating") from exc
        self.torch=torch
        self.tokenizer=Tokenizer.from_pretrained(
            model_name,revision=revision,trust_remote_code=False)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token=self.tokenizer.eos_token
        base=Model.from_pretrained(
            model_name,revision=revision,trust_remote_code=False,
            torch_dtype=torch.float32)
        self.model=get_peft_model(base,LoraConfig(
            r=4,lora_alpha=8,lora_dropout=0.0,
            bias="none",task_type="CAUSAL_LM",
            target_modules=["q_proj","v_proj"]))
        self.model.eval()
        self.device=next(self.model.parameters()).device
        self.optimizer=torch.optim.AdamW(
            (p for p in self.model.parameters() if p.requires_grad),
            lr=learning_rate)
        self.max_new_tokens=max_new_tokens
        self.max_context_tokens=max_context_tokens
        self.max_updates=max_updates
        self.update_count=0
        self.seed=seed
        self._last_latent_prefix=None

    def _ids(self,text):
        ids=self.tokenizer(
            text,add_special_tokens=False,truncation=False)["input_ids"]
        if len(ids)>self.max_context_tokens:
            from .q3_prompt_contract import SourceContextOverflow
            raise SourceContextOverflow(
                "latent SOURCE context exceeds budget; no data truncated")
        return ids

    def hypotheses(self,context,source_history,allowed_queries):
        if any(r.get("scope")!="TRUSTED_SOURCE_ONLY" for r in source_history):
            raise ValueError("non-SOURCE experience in causal context")
        user=_canonical({
            "current_observation":context,
            "prior_source_experiences":list(source_history)[-12:],
            "authorized_query_inputs":allowed_queries,
            "instruction":"propose 1 or 2 diverse falsifiable latent hypotheses",
        })
        prefix=_chat(self.tokenizer,WORLD_SYSTEM,user)
        ids=self._ids(prefix)
        x=self.torch.tensor([ids],dtype=self.torch.long,device=self.device)
        self.torch.manual_seed(
            (self.seed+int(sha256(prefix.encode()).hexdigest()[:8],16))
            %(2**31))
        self.model.eval()
        with self.torch.inference_mode():
            output=self.model.generate(
                input_ids=x,attention_mask=self.torch.ones_like(x),
                max_new_tokens=self.max_new_tokens,
                do_sample=True,temperature=0.3,top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id)
        raw=self.tokenizer.decode(
            output[0][x.shape[1]:],skip_special_tokens=True).strip()
        fence=chr(96)*3
        if raw.startswith(fence):
            raw=raw.split("\n",1)[-1].split(fence,1)[0].strip()
        from .causal_experience import LatentHypothesisFormatError
        try:
            parsed=json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LatentHypothesisFormatError(
                "model did not produce latent-state JSON") from exc
        if not isinstance(parsed,dict):
            raise LatentHypothesisFormatError(
                "latent hypotheses must be a JSON object")
        proposals=parsed.get("hypotheses")
        if not isinstance(proposals,list) or not 1<=len(proposals)<=2:
            raise LatentHypothesisFormatError(
                "model must propose 1 or 2 world hypotheses")
        if any(
            not isinstance(item,dict) or
            not isinstance(item.get("predictions"),dict) or
            not item.get("predictions") or
            set(item["predictions"])-set(allowed_queries)
            for item in proposals
        ):
            raise LatentHypothesisFormatError(
                "model produced no real authorized SOURCE query predictions")
        self._last_latent_prefix=prefix
        return proposals

    def _world_teacher(self,event):
        if event.get("scope")!="TRUSTED_SOURCE_ONLY":
            raise ValueError("independent TARGET outcome cannot train")
        return (
            _chat(self.tokenizer,PREDICTION_SYSTEM,_canonical({
                "query":event["query"],
                "proposed_latent_state":event["hypothesis"],
                "prediction_made_before_measurement":event["predicted"],
            })),
            _canonical(event["observed"]),
        )

    def _loss(self,prefix,completion):
        # All SOURCE observations, even fully refuted programs, can supervise
        # prediction. No pre-authored final solution or hidden teacher concept.
        a=self._ids(prefix)
        b=self.tokenizer(
            completion+self.tokenizer.eos_token,
            add_special_tokens=False)["input_ids"]
        if not b or len(a)+len(b)>self.max_context_tokens+512:
            raise ValueError("causal world outcome too long for training")
        x=self.torch.tensor(
            [a+b],dtype=self.torch.long,device=self.device)
        labels=self.torch.tensor(
            [[-100]*len(a)+b],dtype=self.torch.long,device=self.device)
        return self.model(input_ids=x,labels=labels).loss

    def learn_from_counterexample(self,events):
        """Real optimizer step on SOURCE consequences plus good latent proposal.

        A correct SOURCE prediction is *weak training feedback*, not a
        certificate of a true causal law. Sealed SOURCE and TARGET remain out.
        """
        if not events or self.update_count>=self.max_updates:
            return None
        if any(event.get("scope")!="TRUSTED_SOURCE_ONLY"
               for event in events):
            raise ValueError("only authorized SOURCE experiences can train")
        if len({(e["task_id"],e["query_id"],e["evidence_id"])
                for e in events})!=1:
            raise ValueError("one coherent SOURCE observation per update")
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        # Same observation must not get multiplied gradient by the number
        # of nearly identical hypotheses.
        losses=[self._loss(*self._world_teacher(e)) for e in events]
        prediction_loss=sum(losses)/len(losses)
        correct=[e for e in events if not e["contradicted"]]
        objective=prediction_loss
        reinforced=False
        if correct and self._last_latent_prefix is not None:
            # Only the MODEL-authored SOURCE-consistent concept is reinforced,
            # never a human-provided target solution.
            target=_canonical({"hypotheses":[correct[0]["hypothesis"]]})
            objective=objective+0.25*self._loss(
                self._last_latent_prefix,target)
            reinforced=True
        if not self.torch.isfinite(objective):
            raise ValueError("nonfinite causal learning loss")
        trainable=[p for p in self.model.parameters() if p.requires_grad]
        before=[p.detach().clone() for p in trainable]
        objective.backward()
        self.torch.nn.utils.clip_grad_norm_(trainable,1.0)
        self.optimizer.step()
        delta=sum(float((p.detach()-b).abs().sum().cpu())
                  for p,b in zip(trainable,before))
        self.model.eval()
        self.update_count+=1
        return {
            "schema":"NEUMANN.CAUSAL.NEURAL-WEIGHT-UPDATE.v1",
            "updates":self.update_count,
            "loss":float(objective.detach().cpu()),
            "world_prediction_loss":float(prediction_loss.detach().cpu()),
            "reinforced_model_authored_latent":reinforced,
            "actual_trainable_weight_delta_l1":delta,
            "outcome_provenance":"TRUSTED_SOURCE_ONLY",
            "not_independent_Q3_Q6_proof":True,
        }

    def learn_grounded_source_without_hypothesis(
            self,*,task_id,context,query,observed,evidence_id):
        """Actual SOURCE consequence gradient when NO hypothesis was formed.

        This is *not* causal theory discovery. It trains the SAME weights
        used by hypotheses() to predict a verified next observation and
        thereby removes the zero-learning deadlock caused by invalid JSON.
        No fabricated concept, TARGET gold, new model or added task solver.
        """
        if self.update_count>=self.max_updates:
            return None
        if (not isinstance(task_id,str) or not task_id or
                not isinstance(evidence_id,str) or not evidence_id):
            raise ValueError("authorized SOURCE and evidence IDs required")
        prefix=_chat(self.tokenizer,PREDICTION_SYSTEM,_canonical({
            "task_id":task_id,
            "prior_world_observations":context,
            "authorized_SOURCE_query":query,
            "formed_hypothesis":None,
            "hypothesis_formation_failed":True,
        }))
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        loss=self._loss(prefix,_canonical(observed))
        if not self.torch.isfinite(loss):
            raise ValueError("nonfinite verified observation loss")
        trainable=[p for p in self.model.parameters() if p.requires_grad]
        before=[p.detach().clone() for p in trainable]
        loss.backward()
        self.torch.nn.utils.clip_grad_norm_(trainable,1.0)
        self.optimizer.step()
        delta=sum(float((p.detach()-b).abs().sum().cpu())
                  for p,b in zip(trainable,before))
        self.model.eval()
        self.update_count+=1
        return {
            "schema":"NEUMANN.CAUSAL.PREHYPOTHESIS-SOURCE-UPDATE.v1",
            "updates":self.update_count,
            "learning_objective":"VERIFIED_NEXT_OBSERVATION_NO_HYPOTHESIS",
            "source_prediction_loss":float(loss.detach().cpu()),
            "actual_trainable_weight_delta_l1":delta,
            "original_TARGET_gold_seen":False,
            "provenance":"TRUSTED_SOURCE_ONLY",
            "new_causal_concept_proven":False,
            "generalization_proven":False,
        }

    def save_learned_weights(self,directory):
        """Explicit opt-in checkpoint, never implicit TARGET learning."""
        from pathlib import Path
        target=Path(directory)
        target.mkdir(parents=True,exist_ok=True)
        self.model.save_pretrained(target)
        self.tokenizer.save_pretrained(target)
        return str(target)
