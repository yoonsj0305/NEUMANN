"""P1.8 P0: bounded feasibility before costly source-bound selection.

This reuses the frozen P1.7 grammar/compiler/scorer, without changing its
historical sources or result. SAT is not a semantic-equivalence certificate.
UNKNOWN is never UNSAT. Synthetic tests are not fresh model evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter_ns

from neumann1.control_plane_v1 import ROUTES, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL, validate_identity
from neumann1.control_plane_p11 import CodePlan, plan_cost
from neumann1.control_plane_p12 import CODE_TOKEN_IDS, PERMUTATIONS, aggregate, Budget as ScoreBudget
from neumann1.control_plane_p13 import admissibility, execute_selected
from neumann1.control_plane_p14 import _routing_from_proposal
from neumann1.control_plane_p17 import (
    build_candidates, compile_references, selector_prompt, FrozenEvidenceSelector, LEDGER_KEYS,
)

SCHEMA = "neumann.control-plane-p1.8.p0.v1"


@dataclass(frozen=True)
class Budget:
    # Shared across ALL ambiguity candidates, not reset per candidate.
    feasibility_nodes: int = 20000
    feasibility_constraint_checks: int = 100000
    feasibility_wall_ms: int = 2000
    whole_item_wall_ms: int = 180000

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in asdict(self).values()):
            raise ValueError("positive integer P1.8 budgets required")
        if self.feasibility_wall_ms > self.whole_item_wall_ms:
            raise ValueError("feasibility cannot exceed item budget")


def contract():
    return {"schema": SCHEMA, "stage": "P0_SYNTHETIC_CONTRACT_ONLY", "model": dict(MODEL),
            "grammar_compiler": "UNCHANGED_FROZEN_P1.7_SOURCE_REFERENCES",
            "admissibility": "UNCHANGED_P1.3", "budget": asdict(Budget()),
            "feasibility_statuses": ["SAT", "UNSAT", "UNKNOWN"],
            "unknown_policy": "STOP_NO_SELECTION_OR_EXECUTION",
            "selection": "0 SAT reject; 1 SAT zero neural; 2+ SAT masked full-S4 fallback",
            "mask": "original candidate indexes; no compaction or reindexing",
            "witness_reuse": "same source-bound IR only; original verifier always required",
            "generation": False, "retry": False, "cost_estimate_weight": 0.0,
            "feasibility_is_semantic_equivalence": False,
            "p17_result_rescued": False, "actual_gemma_run": "NOT_RUN",
            "development_registration": "NOT_REGISTERED", "fresh_validation_registered": False,
            "p2_registration_admitted": False, "p2_admitted": False, "decision3_admitted": False,
            "global_questions_closed": []}


class _Exhausted(Exception):
    pass


class _Meter:
    def __init__(self, budget):
        self.budget = budget
        self.started = perf_counter_ns()
        self.nodes = self.checks = 0

    def elapsed(self):
        return (perf_counter_ns() - self.started) / 1e6

    def tick(self, kind=None):
        if self.elapsed() >= self.budget.feasibility_wall_ms:
            raise _Exhausted("feasibility wall cap")
        if kind == "node":
            if self.nodes >= self.budget.feasibility_nodes:
                raise _Exhausted("feasibility node cap")
            self.nodes += 1
        if kind == "constraint":
            if self.checks >= self.budget.feasibility_constraint_checks:
                raise _Exhausted("feasibility constraint-check cap")
            self.checks += 1


def _probe(project, meter):
    """Complete deterministic DFS, with sound exhaustive UNSAT or UNKNOWN.

    Public finite domains/rules only. No model, reference or original checker.
    Every attempted assignment and evaluated relation is charged.
    """
    domains, constraints = project["domains"], project["constraints"]
    names = sorted(domains)
    def consistent(assignment):
        for op, name, other in constraints:
            meter.tick()
            if name not in assignment or (type(other) is str and other not in assignment):
                continue
            meter.tick("constraint")
            a = assignment[name]
            b = assignment[other] if type(other) is str else other
            if op == "eq" and a != b: return False
            if op == "ne" and a == b: return False
            if op == "lt" and not a < b: return False
            if op == "le" and not a <= b: return False
        return True
    def search(assignment):
        meter.tick()
        if len(assignment) == len(names):
            return dict(assignment)  # Every full relation was just checked.
        name = names[len(assignment)]
        for value in domains[name]:
            meter.tick("node")
            extended = {**assignment, name: value}
            if consistent(extended):
                found = search(extended)
                if found is not None: return found
        return None
    answer = search({})
    meter.tick()  # Do not report proof after the deadline.
    return answer


def prune_candidates(view, bundle, budget=Budget()):
    if bundle != build_candidates(view):
        raise ValueError("source/candidate drift before pruning")
    if not 2 <= len(bundle["candidates"]) <= 4 or any(c["route"] != "CSP" for c in bundle["candidates"]):
        raise ValueError("bounded ambiguous CSP candidates required")
    meter = _Meter(budget)
    receipt = {"bundle_sha256": bundle["bundle_sha256"], "budget": asdict(budget),
               "candidates": [], "probe_calls": 0}
    for index in range(len(bundle["candidates"])):
        start, nodes, checks = perf_counter_ns(), meter.nodes, meter.checks
        proposal = compile_references(view, bundle, index)
        typed, routing = _routing_from_proposal(view, proposal)
        if admissibility(typed)["admissible_routes"] != ["CSP"]:
            raise ValueError("only admitted CSP IR can be probed")
        project = routing["project"]
        row = {"index": index, "project_sha256": digest(project), "status": "UNKNOWN",
               "witness": None, "error": None, "search_started": False}
        try:
            meter.tick()
            row["search_started"] = True
            receipt["probe_calls"] += 1
            answer = _probe(project, meter)
            row.update(status="SAT" if answer is not None else "UNSAT", witness=answer)
        except _Exhausted as exc:
            row["error"] = str(exc)
        except Exception as exc:
            # An incidental solver failure is not an impossibility proof.
            # Retain completed work and forbid execution on this UNKNOWN row.
            row["error"] = type(exc).__name__ + ": " + str(exc)
        row.update(nodes=meter.nodes-nodes, constraint_checks=meter.checks-checks,
                   complete_ms=(perf_counter_ns()-start)/1e6)
        receipt["candidates"].append(row)
    receipt.update(nodes=meter.nodes, constraint_checks=meter.checks, complete_ms=meter.elapsed(),
                   sat_indexes=[r["index"] for r in receipt["candidates"] if r["status"] == "SAT"],
                   unknown_indexes=[r["index"] for r in receipt["candidates"] if r["status"] == "UNKNOWN"])
    return receipt


def _masked_choice(matrices, eligible):
    def winner(row):
        ordered = sorted(eligible, key=lambda i: (-finite(row[i]), i))
        if row[ordered[0]] - row[ordered[1]] <= 0.5:
            raise ValueError("feasible candidate margin failure")
        return ordered[0]
    picked = []
    for matrix in matrices:
        summary = aggregate(matrix)
        chosen = winner([summary["scores"][r] for r in ROUTES])
        if summary["max_centered_loo_delta_nats"] > 0.5 or any(winner(row) != chosen for row in summary["loo_scores"]):
            raise ValueError("feasible candidate LOO instability")
        picked.append(chosen)
    if len(set(picked)) != 1:
        raise ValueError("feasible candidate batch/order disagreement")
    if max(abs(matrices[0][i][j]-m[i][j]) for m in matrices[1:] for i in range(24) for j in range(4)) > 0.05:
        raise ValueError("batch/order numerical drift")
    return picked[0]


def validate_selection(view, bundle, eligible, receipt):
    """Same P1.7 raw-score audit; final choice masks ORIGINAL slot indexes.

    Prompts still score all original candidates. This P0 reuses rather than
    retunes the expensive fallback, and claims no residual-path speedup.
    """
    if bundle != build_candidates(view): raise ValueError("candidate/source drift")
    if (type(eligible) is not list or len(eligible) < 2 or
            any(type(i) is not int or not 0 <= i < len(bundle["candidates"]) for i in eligible) or
            eligible != sorted(set(eligible))):
        raise ValueError("distinct original eligible indexes required")
    if receipt.get("status") != "COMPLETE" or receipt.get("bundle_sha256") != bundle["bundle_sha256"]:
        raise ValueError("partial or wrong candidate receipt")
    if receipt.get("prompt_sha256") != [digest(selector_prompt(view, bundle, p)) for p in PERMUTATIONS]:
        raise ValueError("scored prompt identity drift")
    if any(receipt.get("identity", {}).get(k) != v for k, v in MODEL.items()) or receipt.get("unchanged") is not True:
        raise ValueError("frozen core identity required")
    validate_identity(receipt["identity"])
    if type(receipt.get("generated_calls")) is not int or receipt["generated_calls"] != 0:
        raise ValueError("control generation forbidden")
    passes = receipt.get("passes", [])
    if len(passes) != 3: raise ValueError("complete batch/order passes required")
    totals = dict.fromkeys(LEDGER_KEYS, 0)
    for p, (mode, size, order) in zip(passes, (("batch4", 4, list(range(24))),
            ("unbatched1", 1, list(range(24))), ("reverse_batch4", 4, list(reversed(range(24)))))):
        if p.get("mode") != mode or p.get("batch_size") != size or p.get("order") != order or p.get("status") != "COMPLETE":
            raise ValueError("exact scoring mode required")
        if p.get("code_ids") != list(CODE_TOKEN_IDS): raise ValueError("tokenizer code drift")
        plan = CodePlan(tuple(tuple(q) for q in p["prefixes"]), CODE_TOKEN_IDS)
        if any(len(q) > ScoreBudget().context_tokens for q in plan.prefixes):
            raise ValueError("selector context cap; no truncation")
        cost = plan_cost(plan, size)
        if len(plan.prefixes) != 24 or p.get("actual") != cost or p.get("planned") != cost:
            raise ValueError("complete prefix/cost coverage required")
        if type(p.get("peak_accelerator_memory_bytes")) is not int or p["peak_accelerator_memory_bytes"] <= 0:
            raise ValueError("accelerator memory receipt required")
        for key, value in cost.items(): totals[key] += value
    if totals != receipt.get("ledger") or any(v > getattr(ScoreBudget(), k) for k, v in totals.items()):
        raise ValueError("scoring ledger mismatch or cap")
    if passes[1]["prefixes"] != passes[0]["prefixes"] or passes[2]["prefixes"] != list(reversed(passes[0]["prefixes"])):
        raise ValueError("tokenized prefix identity drift")
    if finite(receipt.get("complete_ms"), True) > ScoreBudget().task_wall_ms:
        raise ValueError("selector wall cap")
    return _masked_choice([p["matrix"] for p in passes], eligible)


def interpret_and_execute(view, executor, original_verifier, selector_factory=None, budget=Budget()):
    began = perf_counter_ns()
    elapsed = lambda: (perf_counter_ns()-began)/1e6
    r = {"schema": SCHEMA, "status": "FAILED", "accepted": False, "executed": False,
         "original_view_sha256": digest(view), "budget": asdict(budget), "selected_route": None,
         "model_calls": 0, "neural_forward_calls": 0, "generated_calls": 0,
         "evaluated_tokens": 0, "padded_tokens": 0, "tool_calls": 0, "verifier_calls": 0,
         "feasibility_calls": 0, "feasibility_nodes": 0, "feasibility_constraint_checks": 0,
         "specialist_calls": 0, "witness_cache_hits": 0, "accounting_complete": True, "error": None,
         "extraction_ms": 0.0, "feasibility_ms": 0.0, "selection_ms": 0.0, "compile_ms": 0.0,
         "routing_ms": 0.0, "execution_ms": 0.0, "verification_ms": 0.0, "proposal": None}
    try:
        start = perf_counter_ns()
        try: bundle = build_candidates(view); r["bundle"] = snapshot(bundle)
        finally: r["extraction_ms"] = (perf_counter_ns()-start)/1e6
        cached = None
        if len(bundle["candidates"]) == 1:
            chosen = 0
            r["selection"] = "UNIQUE_COMPLETE_BOUNDED_GRAMMAR"
        else:
            start = perf_counter_ns()
            try:
                pruning = prune_candidates(view, bundle, budget)
                r["pruning_receipt"] = snapshot(pruning)
                r.update(feasibility_calls=pruning["probe_calls"], feasibility_nodes=pruning["nodes"],
                         feasibility_constraint_checks=pruning["constraint_checks"])
            finally: r["feasibility_ms"] = (perf_counter_ns()-start)/1e6
            if pruning["unknown_indexes"]:
                r["status"] = "FEASIBILITY_UNKNOWN"
                return r
            eligible = pruning["sat_indexes"]
            r["eligible_indexes"] = snapshot(eligible)
            if not eligible:
                r["status"] = "NO_FEASIBLE_CANDIDATE"
                return r
            if len(eligible) == 1:
                chosen = eligible[0]
                r["selection"] = "UNIQUE_PROVEN_FEASIBLE_ZERO_NEURAL"
            elif selector_factory is None:
                r["status"] = "NEEDS_BOUNDED_SEMANTIC_SELECTION"
                return r
            else:
                start = perf_counter_ns()
                r.update(model_calls=1, accounting_complete=False, neural_forward_calls=None,
                         generated_calls=None, evaluated_tokens=None, padded_tokens=None)
                try:
                    selector = selector_factory()
                    left = budget.whole_item_wall_ms-elapsed()
                    if left <= 0: raise TimeoutError("lazy selector startup deadline")
                    receipt = selector.score(snapshot(view), snapshot(bundle), left)
                    r["selector_receipt"] = snapshot(receipt)
                    for target, key in (("neural_forward_calls", "forward_calls"),
                            ("evaluated_tokens", "evaluated_tokens"), ("padded_tokens", "padded_tokens")):
                        value = receipt.get("ledger", {}).get(key)
                        if type(value) is int and value >= 0: r[target] = value
                    value = receipt.get("generated_calls")
                    if type(value) is int and value >= 0: r["generated_calls"] = value
                    chosen = validate_selection(view, bundle, eligible, receipt)
                    r.update(accounting_complete=True, selection="FEASIBLE_MASKED_FULL_S4")
                finally: r["selection_ms"] = (perf_counter_ns()-start)/1e6
            cached = pruning["candidates"][chosen]
        r["selected_candidate"] = chosen
        start = perf_counter_ns()
        try: proposal = compile_references(view, bundle, chosen); r["proposal"] = snapshot(proposal)
        finally: r["compile_ms"] = (perf_counter_ns()-start)/1e6
        start = perf_counter_ns()
        typed, routing = _routing_from_proposal(view, proposal)
        r["routing_ms"] = (perf_counter_ns()-start)/1e6
        r["selected_route"] = routing["selected_route"]
        if elapsed() >= budget.whole_item_wall_ms: raise TimeoutError("item deadline before execution")
        def execute(route, project):
            r["tool_calls"] += 1
            start = perf_counter_ns()
            try:
                if cached is not None:
                    if route != "CSP" or cached["status"] != "SAT" or cached["project_sha256"] != digest(project):
                        raise ValueError("witness/project drift")
                    r["witness_cache_hits"] += 1
                    return snapshot(cached["witness"])
                r["specialist_calls"] += 1
                return executor(route, project)
            finally: r["execution_ms"] += (perf_counter_ns()-start)/1e6
        def verify(_typed, answer):
            r["verifier_calls"] += 1
            start = perf_counter_ns()
            try: return original_verifier(snapshot(view), answer)
            finally: r["verification_ms"] += (perf_counter_ns()-start)/1e6
        execution = execute_selected(typed, routing, execute, verify)
        r["execution"] = snapshot(execution)
        r.update(accepted=execution["accepted"], executed=execution["executed"],
                 status="ACCEPTED" if execution["accepted"] else "REJECTED_OR_EXECUTION_FAILED")
        if elapsed() >= budget.whole_item_wall_ms:
            r.update(accepted=False, status="FAILED")
            raise TimeoutError("complete item deadline")
    except Exception as exc:
        r["error"] = type(exc).__name__+": "+str(exc)
    finally:
        r["complete_ms"] = elapsed()
    return r
