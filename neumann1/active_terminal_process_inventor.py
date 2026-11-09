"""Q3 active endpoint-only *program repair* from newly invented SOURCE experiments.

First endpoint-compatible program != reliable generalization.  This module
builds typed experiment expressions from the same primitive substrate and
SOURCE input values, requests new SOURCE terminal observations, and forces
transition AST resynthesis after a counterexample.

No target labels or target successor trajectories are accepted.  A terminal
oracle cannot identify the unique hidden transition, even with unlimited
queries, when two transitions have identical terminal functions.

Scientific gate: SOURCE-PROBE-CONSISTENT is not global Q3/Q6 PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from time import perf_counter_ns

from .higher_order_method_inventor import ControlProgram
from .terminal_only_process_inventor import (
    TerminalOnlyProcessInventor, InventedLatentProcess, _bounded_state)
from .typed_transition_inventor import _kind, _primitive_ops, evaluate_ast


@dataclass(frozen=True)
class SourceExperiment:
    ast: tuple
    output_type: str
    depth: int
    contains_input: bool


@dataclass(frozen=True)
class ProcessRevision:
    counterexample_input: object
    expected_terminal: object
    predicted_terminal: object
    old_ast: tuple
    new_ast: tuple | None


@dataclass(frozen=True)
class ActiveProcessResult:
    status: str
    program: InventedLatentProcess | None
    source_oracle_queries: int
    source_experiment_programs: int
    source_experiment_inputs: int
    revisions: tuple[ProcessRevision, ...]
    source_endpoints: int
    duration_ms: float
    version_hypotheses_examined: int = 0
    disagreement_oracle_queries: int = 0

    @property
    def source_consistent(self):
        return self.status == "SOURCE_PROBE_CONSISTENT"


def _probe_programs(kind, train_inputs, *, max_programs=512, depth_limit=2):
    """Generate new *test-input constructors*, not hand-pick signed integers.

    The input-transform program is a typed AST.  It can be transferred to
    integer/string/set source domains using the same search procedure.
    """
    if not (1 <= max_programs <= 10000 and 1 <= depth_limit <= 3):
        raise ValueError("finite experiment-generator budget required")
    programs = [SourceExperiment(("input",), kind, 0, True)]
    constants = [("int", 0), ("int", 1), ("int", 2)]
    if kind == "str":
        alphabet = sorted({character for x in train_inputs for character in x})
        constants += [("str", "")] + [
            ("str", c) for c in alphabet[:8]]
    elif kind == "set":
        constants += [("set", frozenset())]
    for typ, value in constants:
        programs.append(SourceExperiment(("constant", value), typ, 0, False))
    seen = {(p.output_type, repr(p.ast)) for p in programs}
    for depth in range(1, depth_limit + 1):
        parents = tuple(programs)
        for name, inputs, output, _ in _primitive_ops():
            typed = [
                tuple(p for p in parents if p.output_type == typ)
                for typ in inputs]
            if any(not options for options in typed):
                continue
            for terms in product(*typed):
                if len(programs) >= max_programs:
                    return tuple(programs)
                if not any(p.contains_input for p in terms):
                    continue
                if max(p.depth for p in terms) != depth - 1:
                    continue
                ast = (name,) + tuple(p.ast for p in terms)
                key = (output, repr(ast))
                if key in seen:
                    continue
                seen.add(key)
                programs.append(SourceExperiment(ast, output, depth, True))
    return tuple(programs)


def _source_probe_pool(kind, train_inputs, source_seen, forbidden, *,
                       max_programs, max_probes):
    experiments = _probe_programs(
        kind, train_inputs, max_programs=max_programs)
    probes = set()
    for exp in experiments:
        if not exp.contains_input or exp.output_type != kind:
            continue
        for x in train_inputs:
            try:
                transformed = evaluate_ast(exp.ast, x)
            except (IndexError, TypeError, ValueError, ZeroDivisionError,
                    OverflowError, RecursionError):
                continue
            if (_kind(transformed) != kind
                    or not _bounded_state(transformed)
                    or transformed in source_seen
                    or transformed in forbidden):
                continue
            probes.add(transformed)
            if len(probes) >= max_probes:
                break
        if len(probes) >= max_probes:
            break
    # Explicit deterministic novelty priority, not an adaptive target leak:
    # probe below and above the observed range before redundant interpolation.
    if kind == "int":
        low, high = min(train_inputs), max(train_inputs)
        def priority(x):
            outside = x < low or x > high
            distance = min(abs(x - v) for v in train_inputs)
            return (not outside, x >= low, -distance, x)
    else:
        def priority(x):
            return (len(x), repr(x))
    return tuple(sorted(probes, key=priority)), len(experiments)


def _terminal_behavior(program, x):
    try:
        result = program.compile().run(x)
        if result.status != "HALT_CERTIFIED_FIXED_POINT":
            return ("UNRESOLVED", result.status)
        return ("FIXED", result.value)
    except (IndexError, TypeError, ValueError,
            OverflowError, RecursionError):
        return ("UNRESOLVED", "EXCEPTION")


def _most_discriminating_probe(programs, probes, observed):
    """Generate a separating experiment from competing SOURCE-fit programs.

    Maximize the number of disagreeing candidate pairs (integer Gini score).
    When no pair disagrees, the source probe generator's own fixed ordering
    is used. Target labels are never used to select an experiment.
    """
    remaining = (x for x in probes if x not in observed)
    best = None
    best_disagreement = -1
    for x in remaining:
        if best is None:
            best = x
        if len(programs) <= 1:
            break
        labels = {}
        for program in programs:
            behavior = _terminal_behavior(program, x)
            labels[behavior] = labels.get(behavior, 0) + 1
        n = len(programs)
        disagreement = (n*n - sum(v*v for v in labels.values())) // 2
        if disagreement > best_disagreement:
            best, best_disagreement = x, disagreement
    return best, max(0, best_disagreement)


class ActiveTerminalProcessInventor:
    """Endpoint-only, source-oracle-active CEGIS of a *process AST*.

    SOURCE oracle is a permitted additional observation capability.  It is
    never an oracle for target scores or internal successor trajectories.
    The algorithm returns no process when its grammar cannot fit a newly
    observed counterexample.
    """

    def __init__(self, *, max_nodes=8, max_expressions=150000,
                 max_source_ms=25000, max_rounds=5,
                 max_oracle_queries=160, max_probe_programs=512,
                 max_probe_inputs=512, min_proven_steps=3):
        if not (1 <= max_rounds <= 32
                and 1 <= max_oracle_queries <= 20000
                and 16 <= max_probe_programs <= 10000
                and 8 <= max_probe_inputs <= 20000):
            raise ValueError("finite source experiment budgets required")
        self.inventor = TerminalOnlyProcessInventor(
            max_nodes=max_nodes, max_expressions=max_expressions,
            max_source_ms=max_source_ms, min_proven_steps=min_proven_steps)
        self.max_rounds = max_rounds
        self.max_oracle_queries = max_oracle_queries
        self.max_probe_programs = max_probe_programs
        self.max_probe_inputs = max_probe_inputs

    def discover(self, source_endpoints, *, independent_terminal_checks,
                 source_terminal_oracle, control: ControlProgram,
                 forbidden_target_inputs=(), known_classical=None):
        started = perf_counter_ns()
        train = tuple(source_endpoints)
        checks = list(independent_terminal_checks)
        forbidden = set(forbidden_target_inputs)
        if len(train) < 4 or len(checks) < 3:
            raise ValueError("independent source split required")
        kind = _kind(train[0][0])
        observed = {x: y for x, y in train + tuple(checks)}
        if (len(observed) != len(train) + len(checks)
                or forbidden.intersection(observed)
                or not callable(source_terminal_oracle)):
            raise ValueError("duplicate, forbidden or missing SOURCE observations")
        if any(_kind(x) != kind or _kind(y) != kind
               for x, y in train + tuple(checks)):
            raise ValueError("source type mismatch")
        if known_classical is not None and all(
                known_classical(x) == y for x, y in observed.items()):
            return ActiveProcessResult("CLASSICAL_FIRST", None, 0, 0, 0,
                                       (), len(observed),
                                       (perf_counter_ns() - started) / 1e6)
        probes, program_count = _source_probe_pool(
            kind, tuple(x for x, _ in train), set(observed), forbidden,
            max_programs=self.max_probe_programs,
            max_probes=self.max_probe_inputs)
        queries = 0
        revisions = []
        candidate = None
        compared_versions = 0
        discriminating_queries = 0

        def record(status, program=None):
            return ActiveProcessResult(
                status, program, queries, program_count, len(probes),
                tuple(revisions), len(observed),
                (perf_counter_ns() - started) / 1e6,
                compared_versions, discriminating_queries)

        for round_index in range(self.max_rounds + 1):
            try:
                # Unlabeled probes are part of SOURCE expression signatures.
                # They are NOT examples or verifier labels. This preserves
                # source-equivalent but extrapolation-distinct candidates.
                versions = self.inventor.invent_candidates(
                    train, independent_terminal_checks=tuple(checks),
                    control=control, known_classical=known_classical,
                    exploratory_probes=probes[:32], max_candidates=12)
            except (ValueError, TypeError):
                return record("ABSTAIN_GRAMMAR_GAP")
            if not versions:
                return record("CLASSICAL_FIRST")
            compared_versions += len(versions)
            candidate = versions[0]
            if revisions and revisions[-1].new_ast is None:
                prior = revisions[-1]
                if candidate.transition_ast == prior.old_ast:
                    return record("ABSTAIN_NO_STRUCTURAL_REVISION")
                revisions[-1] = ProcessRevision(
                    prior.counterexample_input, prior.expected_terminal,
                    prior.predicted_terminal, prior.old_ast,
                    candidate.transition_ast)

            counterexample = None
            # Select NEW questions by disagreement between SOURCE-fit
            # executable programs. After every oracle answer, filter the
            # version space without reading target data or successor states.
            while True:
                probe, disagreement = _most_discriminating_probe(
                    versions, probes, observed)
                if probe is None:
                    break
                if queries >= self.max_oracle_queries:
                    return record("ABSTAIN_ORACLE_BUDGET")
                try:
                    gold = source_terminal_oracle(probe)
                except (ValueError, TypeError, OverflowError):
                    return record("ABSTAIN_SOURCE_ORACLE_ERROR")
                queries += 1
                discriminating_queries += int(disagreement > 0)
                try:
                    valid_gold = (_kind(gold) == kind and _bounded_state(gold))
                except TypeError:
                    valid_gold = False
                if not valid_gold:
                    return record("ABSTAIN_INVALID_SOURCE_EVIDENCE")
                observed[probe] = gold
                behavior = _terminal_behavior(candidate, probe)
                predicted = behavior[1] if behavior[0] == "FIXED" else None
                if predicted != gold:
                    counterexample = (probe, gold, predicted)
                    checks.append((probe, gold))
                    break
                versions = tuple(
                    method for method in versions
                    if _terminal_behavior(method, probe) == ("FIXED", gold))
            if counterexample is None:
                return record("SOURCE_PROBE_CONSISTENT", candidate)
            if round_index >= self.max_rounds:
                revisions.append(ProcessRevision(
                    *counterexample, candidate.transition_ast, None))
                return record("ABSTAIN_REPAIR_BUDGET")
            revisions.append(ProcessRevision(
                *counterexample, candidate.transition_ast, None))
        return record("ABSTAIN_REPAIR_BUDGET")
