"""NEUMANN: one experience -> latent-world-hypothesis -> strategy update loop.

This is not a solver, an ARC grammar, a program cache or a declaration that
general intelligence has been achieved. It is a *shared learning interface*.

A trainable policy supplies newly proposed concepts and predictions for
arbitrary JSON observations. The core gathers only authorized SOURCE
measurements, checks predictions, and sends the complete *model-authored*
hypothesis and its real counterexample back to the SAME policy's learning
interface. Thus a failure can change the hypothesis generator itself,
not merely its final answer or the order of cached Python programs.

A held-out independent evaluator must freeze learning before scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


def _json(value: Any) -> str:
    return json.dumps(value,sort_keys=True,ensure_ascii=True,
                      separators=(",",":"),allow_nan=False)


def _digest(value: Any) -> str:
    return sha256(_json(value).encode()).hexdigest()


@dataclass(frozen=True)
class Hypothesis:
    """A model-proposed *mutable conceptual state*, not an executable answer."""
    name: str
    kind: str
    latent_variables: dict
    relations: Any
    predictions: dict

    def __post_init__(self):
        from .types import kind_id
        if (not isinstance(self.name,str) or not self.name
                or len(self.name)>128):
            raise ValueError("bounded model-generated hypothesis name required")
        # A new, namespaced representation is allowed. No fixed kind enum.
        kind_id(self.kind)
        if not isinstance(self.latent_variables,dict) or not self.latent_variables:
            raise ValueError("model must propose at least one latent variable")
        if not isinstance(self.predictions,dict):
            raise ValueError("predictions keyed by authorized query ID required")
        if len(self.predictions)>16:
            raise ValueError("bounded predictive query set required")
        _json(self.as_dict())

    def as_dict(self):
        return {
            "name":self.name,"kind":self.kind,
            "latent_variables":self.latent_variables,
            "relations":self.relations,"predictions":self.predictions,
        }

    @property
    def digest(self):
        return _digest(self.as_dict())


@dataclass(frozen=True)
class CausalUpdate:
    """Receipt for authorized SOURCE experience, never an original TEST score."""
    task_id: str
    query_id: str
    hypothesis_sha256: str
    predicted: Any
    observed: Any
    contradicted: bool
    learning_receipt: Any
    evidence_sha256: str


class CausalExperienceCore:
    """One trainable policy, changing representation, and optional active query.

    Expected policy interface:
      hypotheses(context, source_history, allowed_queries) -> iterable of
          Hypothesis (or dicts with the same fields).
      learn_from_counterexample(event) -> an explicit learning receipt.

    The policy may be a neural network, a mixed neural-symbolic learner,
    or an experimental Bayesian system. Policy update is NOT simulated by
    merely storing a new event in this core: receipt=None means NOT LEARNED.
    """

    def __init__(self,policy,*,max_hypotheses=4,max_experiences=64):
        if not callable(getattr(policy,"hypotheses",None)):
            raise TypeError("a genuine latent-hypothesis proposer is required")
        if not 1<=max_hypotheses<=16 or not 1<=max_experiences<=512:
            raise ValueError("finite hypothesis and experience budgets required")
        self.policy=policy
        self.max_hypotheses=max_hypotheses
        self.max_experiences=max_experiences
        self.experiences=[]
        self._frozen=False
        self._task=None
        self._allowed={}
        self._hypotheses=()
        self._evaluated_queries=set()
        self._last_update=None

    def freeze(self):
        """No original-target outcome may update the learned policy."""
        self._frozen=True

    @property
    def frozen(self):
        return self._frozen

    @property
    def hypotheses(self):
        return self._hypotheses

    def start(self,task_id,context,allowed_queries):
        """Open only explicit, bounded observations; never open target gold."""
        if not isinstance(task_id,str) or not task_id:
            raise ValueError("source identity required")
        if not isinstance(allowed_queries,dict) or not 1<=len(allowed_queries)<=16:
            raise ValueError("authorized SOURCE query map required")
        _json(context);_json(allowed_queries)
        # Reuse causal failures as SOURCE experience, not cached answers.
        history=tuple(self.experiences[-self.max_experiences:])
        raw=self.policy.hypotheses(context,history,dict(allowed_queries))
        if not isinstance(raw,(list,tuple)) or not 1<=len(raw)<=self.max_hypotheses:
            raise ValueError("model must propose bounded latent hypotheses")
        candidates=tuple(h if isinstance(h,Hypothesis)
                         else Hypothesis(**h) for h in raw)
        if len({h.digest for h in candidates})!=len(candidates):
            raise ValueError("duplicate latent hypotheses")
        if any(set(h.predictions)-set(allowed_queries) for h in candidates):
            raise ValueError("candidate predicted unauthorized observation")
        self._task=task_id
        self._allowed=dict(allowed_queries)
        self._hypotheses=candidates
        self._evaluated_queries=set()
        self._last_update=None
        return candidates

    def select_query(self):
        """Active information acquisition without reading actual outcomes.

        Choose the permitted, unused query on which model-authored hypotheses
        disagree most. Return None if no informative/authorized query exists.
        The caller must explicitly authorize and perform any physical action.
        """
        if self._task is None:
            raise ValueError("start a SOURCE hypothesis first")
        choices=[]
        for query in sorted(self._allowed):
            if query in self._evaluated_queries:
                continue
            guesses=[_json(h.predictions[query]) for h in self._hypotheses
                     if query in h.predictions]
            if len(guesses)<2:
                continue
            distinct=len(set(guesses))
            if distinct>1:
                choices.append((distinct,query))
        if not choices:
            return None
        return sorted(choices,key=lambda item:(-item[0],item[1]))[0][1]

    def observe(self,query_id,observed,*,evidence_id,verify_source):
        """Real SOURCE measurement -> causal refutation -> SAME policy update.

        The verifier attests that this observation came from the declared
        authorized SOURCE and is not hidden TARGET gold. The independent
        TARGET scorer must freeze() before it is consulted.
        """
        if self._frozen:
            raise ValueError("frozen independent evaluation cannot learn")
        if self._task is None or query_id not in self._allowed:
            raise ValueError("unregistered SOURCE query")
        if query_id in self._evaluated_queries:
            raise ValueError("no repeat tuning on an already revealed query")
        if len(self.experiences)>=self.max_experiences:
            raise ValueError("experience budget exhausted")
        if not isinstance(evidence_id,str) or not evidence_id:
            raise ValueError("external observation provenance required")
        _json(observed)
        if not callable(verify_source) or verify_source(
                self._task,query_id,self._allowed[query_id],observed,evidence_id
        ) is not True:
            raise ValueError("unverified/out-of-scope SOURCE observation")
        events=[]
        for h in self._hypotheses:
            if query_id not in h.predictions:
                continue
            prediction=h.predictions[query_id]
            event={
                "schema":"NEUMANN.CAUSAL.SOURCE-EVIDENCE.v1",
                "task_id":self._task,"query_id":query_id,
                "query":self._allowed[query_id],
                "hypothesis":h.as_dict(),
                "hypothesis_sha256":h.digest,
                "predicted":prediction,"observed":observed,
                "contradicted":_json(prediction)!=_json(observed),
                "evidence_id":evidence_id,
                "scope":"TRUSTED_SOURCE_ONLY",
            }
            events.append(event)
        if not events:
            raise ValueError("no hypothesis predicted the authorized measurement")
        # Model weights/strategy can change here. This is NOT automatically a
        # Q3 success; null receipt honestly means no policy learning.
        learner=getattr(self.policy,"learn_from_counterexample",None)
        receipt=learner(tuple(events)) if callable(learner) else None
        self._evaluated_queries.add(query_id)
        updates=[]
        for event in events:
            record={**event,"learning_receipt":receipt}
            self.experiences.append(record)
            updates.append(CausalUpdate(
                task_id=event["task_id"],query_id=query_id,
                hypothesis_sha256=event["hypothesis_sha256"],
                predicted=event["predicted"],observed=observed,
                contradicted=event["contradicted"],
                learning_receipt=receipt,
                evidence_sha256=_digest(record)))
        self._last_update=tuple(updates)
        return self._last_update

    def revise(self,context):
        """Use updated SAME proposer weights and real counterexamples.

        A new latent variable or relation can appear here. The core never
        writes domain rules, mutates Python programs or accepts a TARGET label.
        """
        if self._frozen:
            raise ValueError("cannot revise during independent evaluation")
        if self._task is None:
            raise ValueError("no open SOURCE investigation")
        # A revision is NOT a new task. Keep already disclosed SOURCE
        # query IDs sealed against repeat optimization after the revision.
        used=set(self._evaluated_queries)
        task=self._task
        allowed=dict(self._allowed)
        result=self.start(task,context,allowed)
        self._evaluated_queries=used
        return result

    def representation(self):
        """Expose an unverified latent state; downstream verifier still rules."""
        from .types import Representation,IRKind
        if not self._hypotheses:
            return Representation(IRKind.UNKNOWN,{},0.0,
                                  "no model-generated latent hypothesis")
        h=self._hypotheses[0]
        # A SOURCE hypothesis does NOT get a numeric truth probability from
        # mere fit, nor become eligible for unverified physical actuation.
        return Representation(
            kind=h.kind,
            payload={"latent_variables":h.latent_variables,
                     "relations":h.relations,
                     "hypothesis_sha256":h.digest},
            confidence=0.0,
            rationale="unverified model-induced latent representation; "
                      "requires independent downstream validation",
        )
