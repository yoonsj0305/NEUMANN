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


class LatentHypothesisFormatError(ValueError):
    """Only model-authored hypothesis formatting can trigger SOURCE bootstrap.

    SOURCE validation errors and actual infrastructure failures never do.
    """


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
        self._sealed_queries=set()
        self._episode_bindings={}
        self._source_certified=False
        self._source_certification_opened=False
        self._allow_grounded_bootstrap=False
        self._last_context=None
        self._proposal_format_error_sha=None

    def freeze(self):
        """No original-target outcome may update the learned policy."""
        self._frozen=True

    @property
    def frozen(self):
        return self._frozen

    @property
    def hypotheses(self):
        return self._hypotheses

    @property
    def task_id(self):
        return self._task

    def start(self,task_id,context,allowed_queries,*,
              sealed_queries=(),episode_bindings=None,
              allow_grounded_bootstrap=False):
        """Open only explicit, bounded observations; never open target gold."""
        if self._frozen:
            raise ValueError("cannot start new hypothesis during frozen scoring")
        if not isinstance(task_id,str) or not task_id:
            raise ValueError("source identity required")
        if not isinstance(allowed_queries,dict) or not 1<=len(allowed_queries)<=16:
            raise ValueError("authorized SOURCE query map required")
        context=json.loads(_json(context))
        allowed_queries=json.loads(_json(allowed_queries))
        sealed=set(sealed_queries)
        if not sealed.issubset(allowed_queries) or not sealed:
            raise ValueError("at least one predeclared sealed SOURCE check required")
        # SOURCE interventions used to certify one latent mechanism must
        # belong to that same externally registered episode/mechanism.
        # A sample of unrelated stories may test broad domain accuracy,
        # but it CANNOT certify discovery of the TARGET causal mechanism.
        if (not isinstance(episode_bindings,dict) or
                set(episode_bindings)!=set(allowed_queries) or
                any(not isinstance(x,str) or not x
                    for x in episode_bindings.values()) or
                len(set(episode_bindings.values()))!=1):
            raise ValueError(
                "causal SOURCE certificate requires one predeclared "
                "same-mechanism episode across all queried interventions")
        # Reuse causal failures as SOURCE experience, not cached answers.
        history=tuple(self.experiences[-self.max_experiences:])
        # A model that prints an invalid hypothesis template must not block
        # learning from an independently verified SOURCE outcome. Only
        # recognized model-output format failures can use this explicit
        # research opt-in; bad provenance/permissions still fail closed.
        format_error=None
        try:
            raw=self.policy.hypotheses(
                context,history,dict(allowed_queries))
        except LatentHypothesisFormatError as exc:
            if (not allow_grounded_bootstrap or not callable(
                    getattr(self.policy,
                            "learn_grounded_source_without_hypothesis",
                            None))):
                raise
            raw=()
            format_error=_digest({
                "failure":"UNFORMED_LATENT_HYPOTHESIS",
                "error":str(exc)})
        if raw or format_error is None:
            if (not isinstance(raw,(list,tuple)) or
                    not 1<=len(raw)<=self.max_hypotheses):
                raise ValueError("model must propose bounded latent hypotheses")
        # Freeze the model-authored candidate bytes before SOURCE is opened.
        # A mutable dict in policy memory must not rewrite old predictions.
        candidates=tuple(
            Hypothesis(**json.loads(_json(
                h.as_dict() if isinstance(h,Hypothesis) else h)))
            for h in raw)
        if len({h.digest for h in candidates})!=len(candidates):
            raise ValueError("duplicate latent hypotheses")
        if any(set(h.predictions)-set(allowed_queries) for h in candidates):
            raise ValueError("candidate predicted unauthorized observation")
        self._task=task_id
        self._allowed=dict(allowed_queries)
        self._hypotheses=candidates
        self._evaluated_queries=set()
        self._sealed_queries=sealed
        self._episode_bindings=dict(episode_bindings)
        self._source_certified=False
        self._source_certification_opened=False
        self._last_update=None
        self._last_context=context
        self._allow_grounded_bootstrap=bool(allow_grounded_bootstrap)
        self._proposal_format_error_sha=format_error
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
            if query in self._evaluated_queries or query in self._sealed_queries:
                continue
            guesses=[_json(h.predictions[query]) for h in self._hypotheses
                     if query in h.predictions]
            if len(guesses)<2:
                continue
            distinct=len(set(guesses))
            if distinct>1:
                choices.append((distinct,query))
        if not choices:
            # A single self-authored hypothesis still needs an empirical
            # falsification. The old disagreement-only selector returned
            # None when the neural proposer (intentionally) emitted one
            # candidate, so the autonomous Q3 loop could NEVER observe
            # a counterexample without a human manually picking the query.
            # Do not turn a missing hypothesis into a fake discovery:
            # bootstrap still requires an explicit source-only opt-in.
            if self._hypotheses or self._allow_grounded_bootstrap:
                usable=set(self._allowed)-self._sealed_queries-self._evaluated_queries
                return min(usable) if usable else None
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
        if query_id in self._sealed_queries:
            raise ValueError("reserved independent SOURCE check may not train policy")
        if query_id in self._evaluated_queries:
            raise ValueError("no repeat tuning on an already revealed query")
        if len(self.experiences)+len(self._hypotheses)>self.max_experiences:
            raise ValueError("experience budget exhausted")
        if not isinstance(evidence_id,str) or not evidence_id:
            raise ValueError("external observation provenance required")
        observed=json.loads(_json(observed))
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
            if not self._allow_grounded_bootstrap or self._hypotheses:
                raise ValueError("no hypothesis predicted the authorized measurement")
            learner=getattr(
                self.policy,"learn_grounded_source_without_hypothesis",
                None)
            if not callable(learner):
                raise ValueError("no permitted grounded SOURCE learner")
            receipt=learner(
                task_id=self._task,context=self._last_context,
                query=self._allowed[query_id],observed=observed,
                evidence_id=evidence_id)
            event={
                "schema":"NEUMANN.CAUSAL.UNFORMED-SOURCE-EVIDENCE.v1",
                "task_id":self._task,"query_id":query_id,
                "query":self._allowed[query_id],
                "hypothesis":None,"hypothesis_sha256":"UNFORMED",
                "predicted":None,"observed":observed,
                "contradicted":False,
                "no_prior_hypothesis_was_falsified":True,
                "proposal_format_error_sha":self._proposal_format_error_sha,
                "evidence_id":evidence_id,"scope":"TRUSTED_SOURCE_ONLY",
                "learning_receipt":receipt,
            }
            self.experiences.append(event)
            self._evaluated_queries.add(query_id)
            result=CausalUpdate(
                task_id=self._task,query_id=query_id,
                hypothesis_sha256="UNFORMED",predicted=None,
                observed=observed,contradicted=False,
                learning_receipt=receipt,evidence_sha256=_digest(event))
            self._last_update=(result,)
            return self._last_update
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
        sealed=set(self._sealed_queries)
        bindings=dict(self._episode_bindings)
        result=self.start(
            task,context,allowed,
            sealed_queries=sealed,episode_bindings=bindings,
            allow_grounded_bootstrap=self._allow_grounded_bootstrap)
        self._evaluated_queries=used
        return result

    def certify_sealed_source(self,query_id,observed,*,evidence_id,
                              verify_source):
        """One-shot, sealed SOURCE check of the *frozen* top hypothesis.

        Never feeds outcomes into hypothesis generation or weight updates.
        If wrong, the latent representation stays unsupported/low confidence.
        """
        if not self._frozen or self._task is None:
            raise ValueError("freeze hypotheses before independent SOURCE check")
        if query_id not in self._sealed_queries:
            raise ValueError("this query was not pre-registered as sealed")
        if self._source_certification_opened:
            raise ValueError("sealed SOURCE checker is one-shot")
        if not isinstance(evidence_id,str) or not evidence_id:
            raise ValueError("independent SOURCE evidence identity required")
        observed=json.loads(_json(observed))
        # Even an unsuccessful attempt consumes the sealed checker. No
        # adaptive label/provenance probing on a second try.
        self._source_certification_opened=True
        if not callable(verify_source) or verify_source(
                self._task,query_id,self._allowed[query_id],
                observed,evidence_id) is not True:
            raise ValueError("unverified sealed SOURCE observation")
        if not self._hypotheses:
            self._source_certified=False
            return False
        hypothesis=self._hypotheses[0]
        # A hypothesis that contradicts *known* SOURCE may not be admitted
        # just because one sealed example happens to agree.
        known={
            e["query_id"]:e["observed"] for e in self.experiences
            if e["task_id"]==self._task and
               e["query_id"] not in self._sealed_queries
        }
        consistent_training=bool(known) and all(
            q in hypothesis.predictions and
            _json(hypothesis.predictions[q])==_json(actual)
            for q,actual in known.items())
        self._source_certified=(
            consistent_training and
            query_id in hypothesis.predictions and
            _json(hypothesis.predictions[query_id])==_json(observed))
        return self._source_certified

    def representation(self):
        """Expose an unverified latent state; downstream verifier still rules."""
        from .types import Representation,IRKind
        if not self._hypotheses:
            return Representation(IRKind.UNKNOWN,{},0.0,
                                  "no model-generated latent hypothesis")
        h=self._hypotheses[0]
        # Boolean SOURCE admission is represented as 1.0/0.0 only because
        # the existing Representation interface requires a float. This is
        # observed SOURCE consistency, NOT statistical or physical certainty.
        return Representation(
            kind=h.kind,
            payload={"latent_variables":h.latent_variables,
                     "relations":h.relations,
                     "hypothesis_sha256":h.digest},
            confidence=1.0 if self._source_certified else 0.0,
            rationale=("observed SOURCE plus one-shot sealed SOURCE agreed; "
                       "binary admission, not calibrated probability; "
                       "still requires downstream TARGET verification"
                       if self._source_certified else
                       "unverified model-induced latent representation; "
                       "requires independent downstream validation"),
        )
