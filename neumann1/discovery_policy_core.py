"""Q3: synthesize and revise an executable DISCOVERY PROCEDURE.

Human-supplied primitives: rank-complete GF2 probes, exact elimination,
fresh source challenges, on-counterexample feature-space expansion, emit,
abstain. The conditional procedure AST is *composed and learned* by a
domain-name-free meta search, not a user-written problem-specific solver.

TRAINING tasks supply only source oracles and separately withheld
meta-grading inputs. The learned policy does not access fresh target gold.
Cache shared source observations across candidate meta programs and across
counterexample-triggered revisions; charge unique source acquisitions.

Bounded GF2-polynomial language, NOT universal autonomous AI invention.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from random import Random
from time import perf_counter_ns
from hashlib import sha256
from typing import Callable
import json
from .causal_representation_inventor import (
    InventedRepresentation, _basis, _encode, _feature_row, _gf2_unique,
    _validate_point,
)


class PolicyEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class DiscoveryStage:
    degree: int
    fresh_checks: int


@dataclass(frozen=True)
class InferredDiscoveryMethod:
    steps: tuple[DiscoveryStage, ...]

    @property
    def ast(self):
        result = ("ABSTAIN", "no_source_verified_representation")
        for stage in reversed(self.steps):
            result = (
                "IF_SOURCE_COUNTEREXAMPLE",
                ("BUILD_RANK_COMPLETE_SOURCE", stage.degree),
                ("SOLVE_EXACT_GF2",),
                ("CHALLENGE_FRESH_SOURCE", stage.fresh_checks),
                ("THEN", "EMIT_EXECUTABLE_REPRESENTATION"),
                ("ELSE", result),
            )
        return result

    @property
    def digest(self):
        return sha256(json.dumps(
            self.ast, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class MetaTask:
    oracle: Callable
    width: int
    grade_inputs: tuple[tuple[int, ...], ...]
    seed: int


@dataclass(frozen=True)
class SourceCertifiedClassical:
    fn: Callable
    width: int
    source_checks: int

    def apply(self, raw):
        result = self.fn(_validate_point(raw, self.width))
        if type(result) is not int or result not in (0, 1):
            raise PolicyEvidenceError("classical candidate returned nonbit")
        return result


@dataclass(frozen=True)
class ProcedureRun:
    status: str
    program: InventedRepresentation | SourceCertifiedClassical | None
    source_queries: int
    rank_probes: int
    challenge_probes: int
    stages_reached: int
    counterexample_count: int
    elapsed_ms: float
    trace: tuple[tuple, ...]

    def apply(self, raw):
        if (self.status not in ("SOURCE_VERIFIED",
                                "CLASSICAL_SOURCE_VERIFIED") or
                self.program is None):
            raise PolicyEvidenceError("abstain without source certificate")
        return self.program.apply(raw)


class DiscoveryProcedureExecutor:
    """Interpreter for recursively composed source-discovery procedures."""

    def __init__(self, *, max_queries=1024, max_width=20):
        if not 1 <= max_queries <= 100000 or not 1 <= max_width <= 24:
            raise ValueError("finite discovery budget required")
        self.max_queries = max_queries
        self.max_width = max_width

    def run(self, method: InferredDiscoveryMethod, source_oracle: Callable,
            *, width: int, seed: int, forbidden_inputs=(),
            classical_solvers=(), classical_probe_checks=32):
        start = perf_counter_ns()
        if not callable(source_oracle) or not isinstance(
                method, InferredDiscoveryMethod):
            raise TypeError("typed method and explicit source oracle required")
        if not (3 <= width <= self.max_width and type(seed) is int):
            raise PolicyEvidenceError("unsupported raw binary input width")
        if not method.steps or any(s.degree < 0 or s.degree > width or
                                   s.fresh_checks < 1 for s in method.steps):
            raise ValueError("invalid invented meta program")
        degrees = tuple(s.degree for s in method.steps)
        if degrees != tuple(sorted(set(degrees))):
            raise ValueError("feature degrees must expand strictly")
        forbidden = frozenset(_validate_point(x, width)
                              for x in forbidden_inputs)
        observations = {}
        rank_probes = challenge_probes = counterexamples = 0
        trace = []
        order = list(range(1 << width))
        Random(seed).shuffle(order)
        order = [n for n in order
                 if tuple((n >> j) & 1 for j in range(width))
                 not in forbidden]

        def ask(raw, kind):
            nonlocal rank_probes, challenge_probes
            if raw in forbidden:
                raise PolicyEvidenceError("target gold cannot be probed")
            if raw in observations:
                return observations[raw]
            if len(observations) >= self.max_queries:
                raise PolicyEvidenceError("source probe budget reached")
            y = source_oracle(raw)
            if type(y) is not int or y not in (0, 1):
                raise PolicyEvidenceError("source oracle must emit one bit")
            observations[raw] = y
            if kind == "rank":
                rank_probes += 1
            else:
                challenge_probes += 1
            return y

        def finish(status, model, stages):
            return ProcedureRun(
                status, model, len(observations),
                rank_probes, challenge_probes, stages,
                counterexamples, (perf_counter_ns()-start)/1e6,
                tuple(trace))

        try:
            if classical_solvers:
                if not 1 <= classical_probe_checks <= len(order):
                    raise ValueError("invalid known-classical probe budget")
                for classical in classical_solvers:
                    matched = True
                    for packed in order[:classical_probe_checks]:
                        point = tuple((packed >> i) & 1
                                      for i in range(width))
                        if classical(point) != ask(point, "challenge"):
                            matched = False
                    if matched:
                        trace.append(("CLASSICAL", "SOURCE_VERIFIED",
                                      classical_probe_checks))
                        return finish("CLASSICAL_SOURCE_VERIFIED",
                                      SourceCertifiedClassical(
                                          classical, width,
                                          classical_probe_checks), 0)
            for number, stage in enumerate(method.steps, 1):
                masks = _basis(width, stage.degree)
                for mask in masks:
                    raw = tuple(int(bool(mask & (1 << i)))
                                for i in range(width))
                    ask(raw, "rank")
                source = tuple(observations.items())
                rows = [_feature_row(_encode(x), masks)
                        for x, y in source]
                yvalues = [y for x, y in source]
                coefficients, rank, contradictory = _gf2_unique(
                    rows, yvalues, len(masks))
                if contradictory:
                    trace.append((stage.degree,
                                  "SOURCE_CONTRADICTION", rank))
                    continue
                if coefficients is None:
                    trace.append((stage.degree,
                                  "SOURCE_UNIDENTIFIABLE", rank))
                    continue
                model = InventedRepresentation(
                    width, stage.degree,
                    tuple(mask for i,mask in enumerate(masks)
                          if coefficients & (1 << i)),
                    rank, 0.0, len(source), stage.fresh_checks,
                    tuple(s.degree for s in method.steps[:number]),
                )
                candidates = [
                    packed for packed in order
                    if tuple((packed >> i) & 1 for i in range(width))
                    not in observations
                ]
                if len(candidates) < stage.fresh_checks:
                    return finish("ABSTAIN_INSUFFICIENT_FRESH_SOURCE",
                                  None, number)
                falsified = False
                for packed in candidates[:stage.fresh_checks]:
                    raw = tuple((packed >> i) & 1
                                for i in range(width))
                    if model.apply(raw) != ask(raw, "challenge"):
                        falsified = True
                if not falsified:
                    trace.append((stage.degree, "VERIFIED", rank))
                    return finish("SOURCE_VERIFIED", model, number)
                counterexamples += 1
                trace.append((stage.degree,
                              "COUNTEREXAMPLE_EXPAND", rank))
            return finish("ABSTAIN_ALL_ATTEMPTS_REFUTED",
                          None, len(method.steps))
        except PolicyEvidenceError:
            return finish("ABSTAIN_QUERY_LIMIT", None, len(trace))


def enumerate_method_ast(*, max_degree=3, verifier_counts=(8,16)):
    """Generate new conditional programs by recursion over primitive actions."""
    if max_degree not in (2,3,4):
        raise ValueError("bounded meta language required")
    for ncheck in verifier_counts:
        for prefix in range(1 << (max_degree-1)):
            stages = tuple(
                DiscoveryStage(k,ncheck)
                for k in range(1,max_degree)
                if prefix & (1 << (k-1))
            ) + (DiscoveryStage(max_degree,ncheck),)
            yield InferredDiscoveryMethod(stages)


@dataclass(frozen=True)
class PolicyCandidateScore:
    digest: str
    solved: int
    errors: int
    abstentions: int
    source_queries: int
    elapsed_ms: float
    policy: InferredDiscoveryMethod


@dataclass(frozen=True)
class LearnedDiscoveryPolicy:
    policy: InferredDiscoveryMethod
    trace: tuple[PolicyCandidateScore, ...]
    meta_training_queries: int
    meta_training_elapsed_ms: float
    training_task_count: int

    @property
    def digest(self):
        return self.policy.digest


class DiscoveryMethodLearner:
    """Learn a discovered conditional search AST, NOT source-domain labels."""

    def __init__(self, *, max_degree=3, verifier_counts=(8,16),
                 max_queries=1024, strict_accuracy=True):
        self.max_degree = max_degree
        self.verifier_counts = tuple(verifier_counts)
        self.executor = DiscoveryProcedureExecutor(max_queries=max_queries)
        self.strict_accuracy = strict_accuracy
        self._source_caches = {}
        self._meta_cpu_ms = 0.0

    def learn(self, training_tasks):
        start = perf_counter_ns()
        tasks = tuple(training_tasks)
        if len(tasks) < 3 or any(
                not isinstance(t,MetaTask) or not t.grade_inputs
                for t in tasks):
            raise PolicyEvidenceError("multiple meta source tasks required")
        caches = []
        for t in tasks:
            key = (id(t.oracle),t.width,t.seed)
            if key not in self._source_caches:
                # Retain callable strongly so id() cannot collide later.
                self._source_caches[key] = (t.oracle,{})
            original, cache = self._source_caches[key]
            if original is not t.oracle:
                raise PolicyEvidenceError("source identity collision")
            caches.append(cache)

        def cached_oracle(i):
            oracle=tasks[i].oracle
            cache=caches[i]
            def ask(x):
                x=tuple(x)
                if x not in cache:
                    y=oracle(x)
                    if type(y) is not int or y not in (0,1):
                        raise PolicyEvidenceError(
                            "invalid meta-source oracle")
                    cache[x]=y
                return cache[x]
            return ask

        shared=tuple(cached_oracle(i) for i in range(len(tasks)))
        candidate_scores=[]
        for candidate in enumerate_method_ast(
                max_degree=self.max_degree,
                verifier_counts=self.verifier_counts):
            correct=errors=abstained=charged=0
            t0=perf_counter_ns()
            for i,task in enumerate(tasks):
                oracle=shared[i]
                run=self.executor.run(
                    candidate,oracle,
                    width=task.width,seed=task.seed,
                    forbidden_inputs=task.grade_inputs)
                # Gross per-candidate source cost for audit. Real unique
                # source acquisition is separately counted in shared caches.
                charged += run.source_queries + len(task.grade_inputs)
                if run.program is None:
                    abstained += 1
                    continue
                wrong=any(run.apply(x)!=oracle(x)
                          for x in task.grade_inputs)
                if wrong:
                    errors += 1
                else:
                    correct += 1
            candidate_scores.append(PolicyCandidateScore(
                candidate.digest,correct,errors,abstained,charged,
                (perf_counter_ns()-t0)/1e6,candidate))
        if self.strict_accuracy and not any(
                s.solved==len(tasks) for s in candidate_scores):
            raise PolicyEvidenceError(
                "no meta-program solves all source development tasks")
        winner=min(candidate_scores,key=lambda s:(
            -s.solved,s.errors,s.abstentions,
            s.source_queries,len(s.policy.steps),s.digest))
        self._meta_cpu_ms += (perf_counter_ns()-start)/1e6
        return LearnedDiscoveryPolicy(
            winner.policy,tuple(candidate_scores),
            sum(len(pair[1]) for pair in self._source_caches.values()),
            self._meta_cpu_ms,len(tasks))


@dataclass(frozen=True)
class DiscoveryMethodRevision:
    previous_digest: str
    revised: LearnedDiscoveryPolicy
    original_feedback_errors: int
    repaired_feedback_errors: int
    feedback_source_query_charge: int
    feedback_grading_query_charge: int

    @property
    def revised_digest(self):
        return self.revised.digest

    @property
    def visible_meta_source_cost(self):
        return (self.revised.meta_training_queries +
                self.feedback_source_query_charge +
                self.feedback_grading_query_charge)


def revise_discovery_method(learner:DiscoveryMethodLearner,
                            prior:LearnedDiscoveryPolicy,
                            original_training_tasks,
                            new_counterexample_task:MetaTask):
    """Revise program procedure by meta-search after falsified evidence."""
    if not isinstance(new_counterexample_task,MetaTask):
        raise TypeError("typed counterexample task required")
    task=new_counterexample_task
    old=learner.executor.run(
        prior.policy,task.oracle,width=task.width,seed=task.seed,
        forbidden_inputs=task.grade_inputs)
    if old.program is None:
        wrong=len(task.grade_inputs)
    else:
        wrong=sum(old.apply(x)!=task.oracle(x)
                  for x in task.grade_inputs)
    if not wrong:
        raise PolicyEvidenceError(
            "no actual feedback counterexample; no policy rewrite")
    new=learner.learn(tuple(original_training_tasks)+(task,))
    trial=learner.executor.run(
        new.policy,task.oracle,width=task.width,seed=task.seed,
        forbidden_inputs=task.grade_inputs)
    unresolved=(len(task.grade_inputs) if trial.program is None else
                sum(trial.apply(x)!=task.oracle(x)
                    for x in task.grade_inputs))
    if unresolved or new.digest==prior.digest:
        raise PolicyEvidenceError(
            "proposed meta method did not repair observed failure")
    return DiscoveryMethodRevision(
        prior.digest,new,wrong,unresolved,
        old.source_queries,len(task.grade_inputs))
