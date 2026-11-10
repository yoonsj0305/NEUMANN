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


@dataclass(frozen=True)
class FeatureOutcome:
    name: str
    successful_transfer: int
    falsified_transfer: int


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

    def score(self,representation):
        """Beta(1,1) smoothed probability, not a fabricated exact win."""
        name=representation.rsplit("/",1)[-1]
        for evidence in self.outcomes:
            if evidence.name==name:
                return ((evidence.successful_transfer+1)/
                        (evidence.successful_transfer+
                         evidence.falsified_transfer+2))
        return 0.5

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
                "refuted":o.falsified_transfer
            } for o in self.outcomes],
            "target_gold_read":False,
            "q3_global":"OPEN",
        }
