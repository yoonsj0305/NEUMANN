"""P1.12 opened-development runtime helpers.

No import-time model loading or inference.
"""
from __future__ import annotations

from time import perf_counter_ns

from neumann1.control_plane_v1 import digest, finite, snapshot
from neumann1.control_plane_p13 import execute_selected
from neumann1.control_plane_p14 import _routing_from_proposal
from neumann1.control_plane_p17 import compile_references
from neumann1.control_plane_p18 import prune_candidates
from neumann1.control_plane_p112 import select_unique_top, build_joint_pairs
from neumann1.control_plane_p112_semantic import build_bundle
from experiments.control_plane_p14_dev import _hidden_verifier
from experiments.control_plane_p112_registration import (
    GATE, BOUNDARY, COUNTS, semantic_ir_from_bundle, lexical_overlap_receipt,
)

IDS = tuple("p112d_b%02d" % i for i in range(1, 13))
COST_KEYS = (
    "model_calls",
    "neural_forward_calls",
    "generated_calls",
    "input_rows",
    "input_tokens",
    "padded_tokens",
    "tool_calls",
    "verifier_calls",
    "feasibility_calls",
    "feasibility_nodes",
    "feasibility_constraint_checks",
    "witness_cache_hits",
)


def known_sum(rows, key):
    values = [row.get(key) for row in rows]
    return sum(values) if all(type(value) is int and value >= 0 for value in values) else None


def totals(rows):
    return {key: known_sum(rows, key) for key in COST_KEYS}


def _raw_top_candidate(ir, logits, entity_to_candidate):
    if type(logits) is not list or len(logits) != len(ir["pairs"]):
        raise ValueError("complete P1.12 joint-logit vector required")
    position = min(
        range(len(logits)),
        key=lambda i: (-float(logits[i]), ir["pairs"][i]["entity"]),
    )
    return entity_to_candidate[ir["pairs"][position]["entity"]]


def evaluate(rows, refs, core_unchanged, complete, whole_ms):
    out = lambda verdict, reason, **extra: {
        **BOUNDARY,
        "verdict": verdict,
        "reason": reason,
        **extra,
    }
    if complete is not True or tuple(row.get("task_id") for row in rows) != IDS:
        return out("NOT_EVALUATED", "INCOMPLETE_OR_COVERAGE_DRIFT")
    if tuple(ref.get("task_id") for ref in refs) != IDS or core_unchanged is not True:
        return out("NOT_EVALUATED", "REFERENCE_OR_CORE_IDENTITY_DRIFT")
    if finite(whole_ms, True) > GATE["whole_study_wall_ms"]:
        return out("FAIL", "COMPLETE_COST_WALL_CAP")
    if any(finite(row.get("complete_ms"), True) > GATE["per_item_wall_ms"] for row in rows):
        return out("FAIL", "TASK_WALL_CAP")

    try:
        for index, row in enumerate(rows):
            if row.get("accounting_complete") is not True or type(row.get("accepted")) is not bool:
                raise ValueError
            if row.get("selector_complete") is not True:
                raise ValueError
            for key in COST_KEYS:
                if type(row.get(key)) is not int or row[key] < 0:
                    raise ValueError
            for key in (
                "extraction_ms", "feasibility_ms", "ir_ms", "lexical_ms",
                "selection_ms", "compile_ms", "routing_ms", "execution_ms",
                "verification_ms", "complete_ms",
            ):
                finite(row.get(key), True)
            if row["model_calls"] != 1 or row["neural_forward_calls"] != 1:
                raise ValueError
            if row["generated_calls"] != 0 or row["feasibility_calls"] != COUNTS[index]:
                raise ValueError
            lexical = row.get("lexical_baseline")
            if type(lexical) is not dict or lexical.get("unique_selection") is not None:
                raise ValueError
            selected = row.get("selected_candidate")
            if selected is None:
                if (
                    row["tool_calls"] != 0
                    or row["verifier_calls"] != 0
                    or row.get("executed") is not False
                    or row.get("status") != "SEMANTIC_ABSTAINED"
                ):
                    raise ValueError
            else:
                if (
                    row["tool_calls"] != 1
                    or row["verifier_calls"] != 1
                    or row.get("executed") is not True
                    or row.get("status") not in ("ACCEPTED", "REJECTED_BY_ORIGINAL_VERIFIER")
                ):
                    raise ValueError
    except Exception:
        return out("FAIL", "CONTROL_WORK_ACCOUNTING_FAILURE", cost_totals=totals(rows))

    path = {
        "model_calls": known_sum(rows, "model_calls"),
        "neural_forward_calls": known_sum(rows, "neural_forward_calls"),
        "generated_calls": known_sum(rows, "generated_calls"),
        "feasibility_calls": known_sum(rows, "feasibility_calls"),
        "selector_complete": sum(row["selector_complete"] is True for row in rows),
        "lexical_unique_selections": sum(
            row["lexical_baseline"]["unique_selection"] is not None for row in rows
        ),
    }
    expected = {
        "model_calls": GATE["model_calls_exact"],
        "neural_forward_calls": GATE["neural_forward_calls_exact"],
        "generated_calls": GATE["generated_calls_exact"],
        "feasibility_calls": GATE["feasibility_calls_exact"],
        "selector_complete": GATE["selector_complete_exact"],
        "lexical_unique_selections": GATE["lexical_unique_selections_exact"],
    }
    if path != expected:
        return out("FAIL", "CONTROL_PATH_COST_DRIFT", path_cost=path, cost_totals=totals(rows))

    accepted = sum(row["accepted"] for row in rows)
    selected = sum(row.get("selected_candidate") is not None for row in rows)
    rejected = sum(row.get("status") == "REJECTED_BY_ORIGINAL_VERIFIER" for row in rows)
    abstained = sum(row.get("status") == "SEMANTIC_ABSTAINED" for row in rows)
    raw_correct = sum(
        row.get("raw_top_candidate") == ref["expected_candidate"]
        for row, ref in zip(rows, refs)
    )
    diagnostics = {
        "accepted": accepted,
        "selected": selected,
        "verifier_rejected": rejected,
        "semantic_abstained": abstained,
        "raw_top_correct": raw_correct,
        "path_cost": path,
        "cost_totals": totals(rows),
    }
    passed = accepted >= GATE["accepted_min"]
    return out(
        "PASS" if passed else "FAIL",
        "OPENED_P112_CROSS_ENCODER_DIAGNOSTIC_ONLY"
        if passed else "P112_SEMANTIC_CAPABILITY_FAILURE",
        **diagnostics,
        next=(
            "FREEZE_P112_THEN_REGISTER_NEW_FRESH_VALIDATION"
            if passed else "RETAIN_FIRST_P112_FAILURE_AND_DIAGNOSE"
        ),
    )


def run_item(row, ref, encoder):
    began = perf_counter_ns()
    elapsed = lambda: (perf_counter_ns() - began) / 1e6
    record = {
        "task_id": row["task_id"],
        "stratum": row["stratum"],
        "accepted": False,
        "executed": False,
        "original_view_sha256": digest(row["view"]),
        "selected_candidate": None,
        "selected_route": None,
        "raw_top_candidate": None,
        "model_calls": 0,
        "neural_forward_calls": 0,
        "generated_calls": 0,
        "input_rows": 0,
        "input_tokens": 0,
        "padded_tokens": 0,
        "tool_calls": 0,
        "verifier_calls": 0,
        "feasibility_calls": 0,
        "feasibility_nodes": 0,
        "feasibility_constraint_checks": 0,
        "witness_cache_hits": 0,
        "accounting_complete": True,
        "selector_complete": False,
        "selection_error": None,
        "error": None,
        "extraction_ms": 0.0,
        "feasibility_ms": 0.0,
        "ir_ms": 0.0,
        "lexical_ms": 0.0,
        "selection_ms": 0.0,
        "compile_ms": 0.0,
        "routing_ms": 0.0,
        "execution_ms": 0.0,
        "verification_ms": 0.0,
        "proposal": None,
    }
    try:
        started = perf_counter_ns()
        parsed, bundle = build_bundle(row["view"])
        record["extraction_ms"] = (perf_counter_ns() - started) / 1e6
        record["parser_view"] = snapshot(parsed)
        record["bundle_sha256"] = bundle["bundle_sha256"]

        started = perf_counter_ns()
        pruning = prune_candidates(parsed, bundle)
        record["feasibility_ms"] = (perf_counter_ns() - started) / 1e6
        record["pruning_receipt"] = snapshot(pruning)
        record.update(
            feasibility_calls=pruning["probe_calls"],
            feasibility_nodes=pruning["nodes"],
            feasibility_constraint_checks=pruning["constraint_checks"],
        )
        if pruning["unknown_indexes"]:
            raise ValueError("P1.12 feasibility UNKNOWN")
        eligible = pruning["sat_indexes"]
        if len(eligible) < 2 or eligible != list(range(len(bundle["candidates"]))):
            raise ValueError("P1.12 development requires fully multi-feasible candidates")
        record["eligible_indexes"] = snapshot(eligible)

        started = perf_counter_ns()
        role_ir, by_candidate = semantic_ir_from_bundle(
            row["view"], parsed, bundle, eligible
        )
        ir = build_joint_pairs(
            row["view"]["instruction"],
            sorted(candidate["entity"] for candidate in role_ir["candidates"]),
        )
        record["ir_ms"] = (perf_counter_ns() - started) / 1e6
        record["semantic_ir"] = snapshot(ir)
        record["candidate_entities"] = snapshot(by_candidate)
        entity_to_candidate = {entity: index for index, entity in by_candidate.items()}

        started = perf_counter_ns()
        lexical = lexical_overlap_receipt(role_ir)
        record["lexical_ms"] = (perf_counter_ns() - started) / 1e6
        record["lexical_baseline"] = snapshot(lexical)
        if lexical["unique_selection"] is not None:
            raise ValueError("P1.12 lexical anti-triviality drift")

        if encoder is None:
            raise ValueError("P1.12 frozen semantic encoder required")
        record["model_calls"] = 1
        before = encoder.forward_calls
        selector_started = perf_counter_ns()
        try:
            model_output = encoder.score(ir)
        except Exception:
            attempt = getattr(encoder, "last_attempt", None)
            delta = encoder.forward_calls - before
            if type(delta) is int and delta >= 0:
                record["neural_forward_calls"] = delta
            if isinstance(attempt, dict):
                for key in ("input_rows", "input_tokens", "padded_tokens"):
                    value = attempt.get(key)
                    if type(value) is int and value >= 0:
                        record[key] = value
                record["selector_partial_receipt"] = snapshot(attempt)
                record["accounting_complete"] = all(
                    type(record[key]) is int and record[key] >= 0
                    for key in ("neural_forward_calls", "input_rows", "input_tokens", "padded_tokens")
                )
            else:
                record["accounting_complete"] = False
            raise

        selector_ms = (perf_counter_ns() - selector_started) / 1e6
        delta = encoder.forward_calls - before
        if delta != 1 or model_output.get("forward_calls") != 1:
            raise ValueError("P1.12 exact one-forward contract required")
        record.update(
            neural_forward_calls=1,
            input_rows=model_output["input_rows"],
            input_tokens=model_output["input_tokens"],
            padded_tokens=model_output["padded_tokens"],
            accounting_complete=True,
            selector_complete=True,
        )
        record["selector_receipt"] = {
            "status": "COMPLETE",
            "joint_ir_sha256": digest(ir),
            "logits": snapshot(model_output["logits"]),
            "forward_calls": 1,
            "input_rows": model_output["input_rows"],
            "input_tokens": model_output["input_tokens"],
            "padded_tokens": model_output["padded_tokens"],
            "tokenize_ms": model_output.get("tokenize_ms"),
            "forward_ms": model_output.get("forward_ms"),
            "logit_extract_ms": model_output.get("logit_extract_ms"),
            "device": model_output.get("device"),
            "complete_ms": selector_ms,
        }
        if selector_ms > GATE["selector_wall_ms"]:
            raise TimeoutError("P1.12 selector wall cap")

        record["raw_top_candidate"] = _raw_top_candidate(
            ir, model_output["logits"], entity_to_candidate
        )
        try:
            decision = select_unique_top(ir, model_output["logits"])
        except ValueError as exc:
            record.update(
                status="SEMANTIC_ABSTAINED",
                selection="JOINT_CROSS_ENCODER_ABSTAIN",
                selection_error=type(exc).__name__ + ": " + str(exc),
                selection_ms=selector_ms,
            )
            return record

        record["selection_ms"] = selector_ms
        selected_entity = decision["selected_entity"]
        chosen = entity_to_candidate[selected_entity]
        record["selector_decision"] = snapshot(decision)
        record.update(
            selected_candidate=chosen,
            selection="JOINT_CROSS_ENCODER_RANKING",
        )

        cached = pruning["candidates"][chosen]
        started = perf_counter_ns()
        proposal = compile_references(parsed, bundle, chosen)
        record["proposal"] = snapshot(proposal)
        record["compile_ms"] = (perf_counter_ns() - started) / 1e6

        started = perf_counter_ns()
        typed, routing = _routing_from_proposal(parsed, proposal)
        record["routing_ms"] = (perf_counter_ns() - started) / 1e6
        record["selected_route"] = routing["selected_route"]
        checker = _hidden_verifier(ref)

        def execute(route, project):
            record["tool_calls"] += 1
            inner = perf_counter_ns()
            try:
                if (
                    route != "CSP"
                    or cached["status"] != "SAT"
                    or cached["project_sha256"] != digest(project)
                ):
                    raise ValueError("cached witness/project drift")
                record["witness_cache_hits"] += 1
                return snapshot(cached["witness"])
            finally:
                record["execution_ms"] += (perf_counter_ns() - inner) / 1e6

        def verify(_typed, answer):
            record["verifier_calls"] += 1
            inner = perf_counter_ns()
            try:
                return checker(snapshot(row["view"]), answer)
            finally:
                record["verification_ms"] += (perf_counter_ns() - inner) / 1e6

        execution = execute_selected(typed, routing, execute, verify)
        record["execution"] = snapshot(execution)
        record.update(
            accepted=execution["accepted"],
            executed=execution["executed"],
            status=(
                "ACCEPTED"
                if execution["accepted"]
                else "REJECTED_BY_ORIGINAL_VERIFIER"
            ),
        )
        if elapsed() >= GATE["per_item_wall_ms"]:
            record.update(accepted=False, status="FAILED")
            raise TimeoutError("complete P1.12 item deadline")
    except Exception as exc:
        record["status"] = "FAILED"
        record["error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        record["complete_ms"] = elapsed()
    return record
