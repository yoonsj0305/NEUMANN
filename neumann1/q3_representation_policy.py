"""Learn a transferable REPRESENTATION-selection policy from real SOURCE falsification.

Existing structural candidate generators are shared with the unlearned
control. This policy changes only WHICH causal representation to try first.
It is trained on independently SOURCE-certified, disjoint prior method
episodes. On each prior task it generates candidate structural explanations
using TRAIN SOURCE and executes those explanations on never-shared CHECK
SOURCE. Successful and refuted representation choices become the learned
policy. It does NOT learn from test targets, benchmark names or hand-entered
answer labels, and cannot declare Q3 global success.

Learning *which existing representation* to choose is a measurable step
towards self-improving discovery policy; it is not yet autonomous invention
of a new operator grammar.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .open_program_inventor import source_same_value
from .q3_object_graph_invention import induce_object_graph_factors
from .q3_source_residual_probes import (
    induce_source_residual_probes,source_edit_f1)
from .q3_residual_composition import induce_source_compositions
from .q3_structure_factorization import induce_structural_factors
from .q3_coordinate_morphisms import induce_coordinate_morphisms
from .q3_periodic_residual_invention import induce_periodic_residual_rules
from .q3_relational_predicate_invention import induce_relational_comprehensions
from .q3_relational_reduce_invention import induce_relational_reducers


@dataclass(frozen=True)
class FeatureOutcome:
    name: str
    successful_transfer: int
    falsified_transfer: int
    partial_transfer: int = 0


@dataclass(frozen=True)
class LearnedRepresentationPrior:
    outcomes: tuple[FeatureOutcome, ...]
    source_episode_sha256: tuple[str, ...]
    check_executions: int

    @classmethod
    def learn(cls, certified_episodes,runner,*,max_episodes=128):
        if not 1<=max_episodes<=4096:
            raise ValueError("finite certified SOURCE teaching budget required")
        sources=tuple(certified_episodes)
        if len(sources)>max_episodes:
            raise ValueError("SOURCE training episodes exceed registered budget")
        ledger={}
        receipts=[]
        executions=0
        identifiers=set()
        for episode in sources:
            sid=episode.source_id
            if sid in identifiers or not episode.independent_pairs:
                raise ValueError("unproven or duplicate source teacher")
            identifiers.add(sid)
            # Independently recertify the teacher, not its self-reported
            # 'SOURCE_VERIFIED' string. Missing sandbox must fail CLOSED.
            all_pairs=tuple(episode.source_pairs)+tuple(
                episode.independent_pairs)
            evaluated=runner.evaluate(
                episode.program,[x for x,y in all_pairs])
            if (evaluated.status!="EXECUTED"
                    or len(evaluated.outputs)!=len(all_pairs)
                    or not all(source_same_value(got,y)
                               for got,(_,y) in zip(
                                   evaluated.outputs,all_pairs))):
                raise ValueError("independent SOURCE teacher recertification failed")
            executions+=1
            receipts.append(episode.identity)
            # Never use reserved SOURCE checks to invent a candidate.
            # Every feature receives its own true transfer outcome.
            proposals=induce_object_graph_factors(
                episode.source_pairs,max_candidates=12)
            for factor in proposals:
                name=factor.representation.rsplit("/",1)[-1]
                score=ledger.setdefault(name,[0,0])
                observed=runner.evaluate(
                    factor.program,[x for x,y in episode.independent_pairs])
                executions+=1
                accepted=(observed.status=="EXECUTED"
                    and len(observed.outputs)==len(episode.independent_pairs)
                    and all(source_same_value(got,y)
                        for got,(_,y) in zip(
                            observed.outputs,episode.independent_pairs)))
                score[0 if accepted else 1]+=1
        return cls(
            tuple(FeatureOutcome(key,p[0],p[1]) for key,p in
                  sorted(ledger.items())),
            tuple(sorted(receipts)),executions)

    @classmethod
    def learn_source_trials(cls, original_source_trials, runner, *,
                            max_episodes=256):
        """Learn successes AND real failures from source-only original tasks.

        This unlike .learn() does NOT demand a previously solved task: a
        model with no success must still be able to learn from its failed
        representations. SOURCE observations are split by original input
        identity. The final original test outputs are never accepted here.
        """
        if not 1<=max_episodes<=2048:
            raise ValueError("finite SOURCE teaching budget required")
        trials=list(original_source_trials)
        if len(trials)>max_episodes:
            raise ValueError("SOURCE task budget exceeded")
        ledger={}
        receipts=[]
        seen_ids=set()
        executions=0
        for source_id,train,checks in trials:
            if (not isinstance(source_id,str) or not source_id or
                    source_id in seen_ids):
                raise ValueError("duplicate or missing original SOURCE ID")
            seen_ids.add(source_id)
            train=tuple((x,y) for x,y in train)
            checks=tuple((x,y) for x,y in checks)
            if not 2<=len(train)<=32 or not 1<=len(checks)<=32:
                raise ValueError("disjoint SOURCE train/check required")
            # Explicit type-preserving JSON serialization guards the
            # original observation provenance and duplicate inputs.
            def canonical(v):
                return json.dumps(v,sort_keys=True,separators=(",",":"),
                                  ensure_ascii=True,allow_nan=False)
            known=[canonical(x) for x,y in train]
            reserved=[canonical(x) for x,y in checks]
            if (len(set(known))!=len(known) or
                    len(set(reserved))!=len(reserved) or
                    set(known)&set(reserved)):
                raise ValueError("original SOURCE inputs overlap across split")
            receipts.append(sha256(canonical(
                [source_id,train,checks]).encode()).hexdigest())
            # Use only training SOURCE to create hypotheses. Independent
            # SOURCE check labels are consumed by the real verifier ONLY.
            # First-principles deletion: stop demanding a perfect SOURCE
            # program before the discovery policy can learn from errors.
            # Probe grammars are available to BOTH frozen-classical A and C.
            # The inference core exposes multiple representation families.
            # Previously the SOURCE learner observed only THREE. Thus the
            # discovery prior remained exactly zero for index-morphisms,
            # periodic causal residuals, and structural factorization on
            # every independent task. Give every shared A/C family real
            # SOURCE success AND refutation evidence. The per-family cap
            # is fixed before seeing independent checks.
            factors=(
                tuple(induce_structural_factors(
                    train,max_candidates=4))
                +tuple(induce_object_graph_factors(
                    train,max_candidates=4))
                +tuple(induce_source_compositions(
                    train,max_candidates=4))
                +tuple(induce_source_residual_probes(
                    train,max_probes=4))
                +tuple(induce_coordinate_morphisms(
                    train,max_candidates=4))
                +tuple(induce_periodic_residual_rules(
                    train,max_candidates=4))
                +tuple(induce_relational_comprehensions(
                    train,max_candidates=4))
                +tuple(induce_relational_reducers(
                    train,max_candidates=4))
            )
            for factor in factors:
                key=factor.representation
                scores=ledger.setdefault(key,[0,0,0])
                output=runner.evaluate(factor.program,[x for x,y in checks])
                executions+=1
                accepted=(
                    output.status=="EXECUTED" and
                    len(output.outputs)==len(checks) and
                    all(source_same_value(value,y)
                        for value,(_,y) in zip(output.outputs,checks)))
                scores[0 if accepted else 1]+=1
                if not accepted and output.status=="EXECUTED" and (
                        len(output.outputs)==len(checks)):
                    # Partial causal explanations are useful learning data,
                    # but NEVER counted as independently correct solutions.
                    gain=sum(source_edit_f1(x,y,p) for p,(x,y)
                             in zip(output.outputs,checks))/len(checks)
                    if gain>0.0:
                        scores[2]+=1
        return cls(
            tuple(FeatureOutcome(key,v[0],v[1],v[2])
                  for key,v in sorted(ledger.items())),
            tuple(sorted(receipts)),executions)

    @classmethod
    def from_source_snapshot(cls, snapshot):
        if (not isinstance(snapshot,dict)
                or snapshot.get("schema")!="NEUMANN.Q3.SOURCE-REPRESENTATION-POLICY.v1"
                or snapshot.get("target_gold_read") is not False):
            raise ValueError("untrusted frozen SOURCE representation snapshot")
        rows=snapshot.get("outcomes")
        ids=snapshot.get("source_episode_sha256")
        if not isinstance(rows,list) or not isinstance(ids,list):
            raise ValueError("missing certified SOURCE preference data")
        if (len(set(ids))!=len(ids) or
                any(not isinstance(x,str) or len(x)!=64 for x in ids)):
            raise ValueError("invalid or duplicated SOURCE identity")
        outcomes=tuple(FeatureOutcome(
            str(x["name"]),int(x["successful_transfer"]),
            int(x["falsified_transfer"]),
            int(x.get("partial_transfer",0))) for x in rows)
        if (len({x.name for x in outcomes})!=len(outcomes)
                or any(x.successful_transfer<0 or x.falsified_transfer<0
                       or x.partial_transfer<0
                       or x.partial_transfer>x.falsified_transfer
                       for x in outcomes)):
            raise ValueError("corrupted learned preference counts")
        return cls(outcomes,tuple(ids),int(snapshot["check_executions"]))

    def source_snapshot(self):
        return {
            "schema":"NEUMANN.Q3.SOURCE-REPRESENTATION-POLICY.v1",
            "target_gold_read":False,
            "source_episode_sha256":list(self.source_episode_sha256),
            "check_executions":self.check_executions,
            "outcomes":[{
                "name":x.name,
                "successful_transfer":x.successful_transfer,
                "falsified_transfer":x.falsified_transfer,
                "partial_transfer":x.partial_transfer}
                for x in self.outcomes],
            "q3_global":"OPEN"}

    def score(self,representation):
        """Beta(1,1) smoothed probability, not a fabricated exact win."""
        for evidence in self.outcomes:
            # Accept either exact source-inferred graph name or a qualified
            # source-probe name. Avoid silently merging unrelated feature
            # families with a coincidentally equal suffix.
            if (evidence.name==representation or
                    evidence.name==representation.rsplit("/",1)[-1]):
                total=(evidence.successful_transfer+
                       evidence.falsified_transfer)
                # Center on the unobserved Beta(1,1) prior. Otherwise
                # even 100% REFUTED hypotheses score > 0 and are ranked
                # ahead of entirely untried representations (score 0).
                # Partial edits are NOT exact success: they stay in the
                # audit ledger, but cannot turn refutation into proof.
                return ((evidence.successful_transfer+1)/(total+2)
                        -0.5)
        return 0.0

    def order_key(self,factor):
        return (-self.score(factor.representation),
                factor.description_length,
                factor.representation,
                len(factor.program))

    def evidence(self):
        return {
            "source_training_ids_sha256":sha256(json.dumps(
                self.source_episode_sha256,separators=(",",":")
                ).encode()).hexdigest(),
            "transfer_observations":sum(
                x.successful_transfer+x.falsified_transfer
                for x in self.outcomes),
            "real_verifier_executions":self.check_executions,
            "outcomes":[{
                "feature":o.name,
                "pass":o.successful_transfer,
                "refuted":o.falsified_transfer,
                "partial_edit_improvements_not_exact":o.partial_transfer
            } for o in self.outcomes],
            "target_gold_read":False,
            "q3_global":"OPEN",
        }
