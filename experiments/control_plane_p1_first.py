"""P1 first-only real Gemma route scoring. No answers, tools or generation."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import traceback
from importlib.metadata import version
from dataclasses import asdict
from pathlib import Path
from time import perf_counter_ns

from neumann1.control_plane_v1 import ROUTES, ScoreFailure, canonical, digest, finite, public_view, route_prompt, snapshot
from neumann1.control_plane_p1_contract import MODEL, PUBLIC_SHA256, TASK_IDS, P1Budget, CRITERIA, evaluate, manifest, route_statistics, validate_identity

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "docs/experiments/control_plane_p1_v1.preregister.json"
PUBLIC = ROOT / "docs/experiments/control_plane_p1_opened_public.json"


def elapsed(start):
    return (perf_counter_ns() - start) / 1e6


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as out:
        out.write(canonical(value) + "\n")


def registered_sources():
    registration = json.loads(REGISTRATION.read_bytes())
    if registration["contract"] != manifest():
        raise ValueError("frozen P1 contract drift")
    for name, expected in registration["source_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("registered source drift: " + name)
    data = json.loads(PUBLIC.read_bytes())
    rows = data["rows"]
    if tuple(r["task_id"] for r in rows) != TASK_IDS:
        raise ValueError("exact opened task coverage required")
    if any(set(r) != {"task_id", "view"} for r in rows):
        raise ValueError("only bookkeeping ID and public view allowed")
    views = [public_view(r["view"]) for r in rows]
    if digest(views) != PUBLIC_SHA256:
        raise ValueError("original 12 public model-view identity mismatch")
    return registration, rows


def forbid_generation(core):
    """Install a hard tripwire on both core and underlying model generation."""
    counter = {"calls": 0}
    def forbidden(*args, **kwargs):
        counter["calls"] += 1
        raise RuntimeError("P1 generation forbidden")
    core.generate = forbidden
    core.model.generate = forbidden
    return counter


def score_task(row, scorer, ledger, task_budget_ms=P1Budget().task_wall_ms):
    view = public_view(row["view"])
    before = snapshot(scorer.identity)
    prompt = route_prompt(view["instruction"], view["public"])
    began = perf_counter_ns()
    passes = []
    record = {"task_id": row["task_id"], "view_sha256": digest(view), "status": "STARTED", "passes": passes}
    original_batch = scorer.backend.batch_size
    try:
        for mode, labels, batch_size in (("batch4", ROUTES, 4), ("unbatched1", ROUTES, 1),
                                         ("reverse_batch4", tuple(reversed(ROUTES)), 4)):
            started = perf_counter_ns()
            observation = {"mode": mode, "status": "STARTED", "batch_size": batch_size}
            passes.append(observation)
            scorer.backend.batch_size = batch_size
            plan = scorer.prepare((prompt,), labels)
            plan.validate()
            if plan.labels != labels or plan.prompt_count != 1:
                raise ValueError("request/encoded-plan drift")
            if max(len(r.prompt_ids) + len(r.label_ids) for r in plan.rows) > P1Budget().context_tokens:
                raise ValueError("context admission; no truncation")
            if max(len(r.label_ids) for r in plan.rows) > P1Budget().label_tokens:
                raise ValueError("candidate label token cap")
            forward_bound = scorer.forward_bound(plan)
            if forward_bound != (1 if batch_size == 4 else 4):
                raise ValueError("registered batch/forward layout drift")
            increments = {"evaluated_tokens": plan.evaluated_tokens, "score_rows": len(plan.rows),
                          "forward_calls": forward_bound,
                          "padded_tokens": sum(max(len(r.prompt_ids) + len(r.label_ids) for r in plan.rows[i:i+batch_size])
                                               * len(plan.rows[i:i+batch_size]) for i in range(0, 4, batch_size))}
            if any(ledger[k] + v > getattr(P1Budget(), k) for k, v in increments.items()):
                raise ValueError("complete study scoring admission cap")
            observation.update(labels=list(labels), encoded_rows=[asdict(r) for r in plan.rows],
                               planned= increments, scored_tokens=plan.scored_tokens, generated_tokens=0)
            remaining = min(task_budget_ms - elapsed(began), ledger["remaining_study_ms"]())
            if remaining <= 0:
                raise TimeoutError("P1 complete deadline before forward")
            try:
                result = scorer.evaluate(plan, remaining)
            except ScoreFailure as exc:
                ledger["forward_calls"] += exc.forward_calls
                ledger["padded_tokens"] += exc.padded_tokens
                observation.update(known_partial_forward_calls=exc.forward_calls,
                                   known_partial_padded_tokens=exc.padded_tokens,
                                   backend_complete_ms=exc.complete_ms)
                raise
            if result.forward_calls != forward_bound or result.padded_tokens != increments["padded_tokens"]:
                raise ValueError("exact scoring accounting mismatch")
            for key, value in increments.items():
                ledger[key] += value
            ledger["scored_tokens"] += plan.scored_tokens
            if len(result.scores) != 1 or len(result.scores[0]) != 4:
                raise ValueError("exact route score matrix required")
            mapping = {label: finite(v) for label, v in zip(labels, result.scores[0])}
            if any(v > 0 for v in mapping.values()):
                raise ValueError("positive log probability forbidden")
            if type(result.peak_accelerator_memory_bytes) is not int or result.peak_accelerator_memory_bytes <= 0:
                raise ValueError("actual scoring peak VRAM receipt required")
            observation.update(status="COMPLETE", scores=mapping, complete_ms=elapsed(started),
                               actual=increments, peak_accelerator_memory_bytes=result.peak_accelerator_memory_bytes)
            if scorer.identity != before:
                raise ValueError("scorer identity drift")
            if elapsed(began) > task_budget_ms or ledger["remaining_study_ms"]() <= 0:
                raise TimeoutError("P1 complete deadline after forward; work retained")
        vectors = [[p["scores"][r] for r in ROUTES] for p in passes]
        stats = route_statistics(vectors[0])
        deltas = [max(abs(a-b) for a, b in zip(vectors[0], vec)) for vec in vectors[1:]]
        stable = stats["margin_nats"] <= CRITERIA["strict_winner_margin_nats"] or all(
            route_statistics(v)["winner"] == stats["winner"] for v in vectors[1:])
        record.update(status="COMPLETE", canonical_scores=vectors[0], statistics=stats,
                      max_batch_delta_nats=deltas[0], max_order_delta_nats=deltas[1],
                      stable_large_margin_winner=stable)
    except Exception as exc:
        record.update(status="FAILED", error=type(exc).__name__ + ": " + str(exc),
                      failure_traceback=traceback.format_exc())
    finally:
        scorer.backend.batch_size = original_batch
        record["complete_ms"] = elapsed(began)
        record["trace_sha256"] = digest(passes)
    return record


def run_study(directory, frozen_head, core_factory=None):
    """Exclusive directory admission; failed first attempts are never replaced."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    study = perf_counter_ns()
    write_new(directory / "study_started.json", {"schema": manifest()["schema"], "frozen_head": frozen_head,
                                                 "no_replacement": True})
    records = []
    core = None
    generation = {"calls": 0}
    audit = {}
    error = None
    startup_ms = None
    ledger = {k: 0 for k in ("evaluated_tokens", "padded_tokens", "forward_calls", "score_rows", "scored_tokens")}
    ledger["remaining_study_ms"] = lambda: P1Budget().study_wall_ms - elapsed(study)
    try:
        registration, rows = registered_sources()
        write_new(directory / "manifest.json", {"registration": registration, "frozen_head": frozen_head,
                                                 "public_rows": rows, "generate_calls": 0, "tool_calls": 0})
        actual_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        if actual_head != frozen_head:
            raise ValueError("frozen execution commit mismatch")
        subprocess.run(["git", "diff", "--exit-code", "HEAD", "--"], cwd=ROOT, check=True, capture_output=True)
        if core_factory is None:
            for package, expected in manifest()["runtime"].items():
                if version(package) != expected:
                    raise ValueError("registered runtime mismatch before model load: " + package)
            from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
            core_factory = FrozenAcceleratorCore
        core = core_factory()
        validate_identity(core.identity)
        generation = forbid_generation(core)
        identity = snapshot(core.identity)
        write_new(directory / "core.json", identity)
        from neumann1.control_plane_scoring_v1 import attach_frozen_gemma
        scorer = attach_frozen_gemma(core, batch_size=4)
        startup_ms = elapsed(study)
        write_new(directory / "scorer.json", scorer.identity)
        for index, row in enumerate(rows):
            write_new(directory / ("task_%02d_started.json" % index), {"task_id": row["task_id"], "view_sha256": digest(row["view"])})
            record = score_task(row, scorer, ledger)
            records.append(record)
            write_new(directory / ("task_%02d.json" % index), record)
            print(canonical({"completed": len(records), "task_id": row["task_id"], "status": record["status"],
                             "winner": record.get("statistics", {}).get("winner"), "complete_ms": record["complete_ms"]}), flush=True)
            if record["status"] != "COMPLETE":
                raise RuntimeError("partial scoring failure; stop and preserve first attempt")
        audit = core.audit()
        if core.identity != identity:
            audit["unchanged"] = False
    except Exception as exc:
        error = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    if core is not None and not audit:
        try:
            audit = core.audit()
        except Exception as exc:
            audit = {"unchanged": False, "error": str(exc)}
    accounting_complete = (error is None and len(records) == 12 and all(r["status"] == "COMPLETE" for r in records))
    verdict = evaluate(records, audit, generation["calls"], elapsed(study), accounting_complete)
    report = {"schema": manifest()["schema"], "status": "COMPLETE" if accounting_complete else "INCOMPLETE",
              "decision": verdict, "observations": len(records), "generated_calls": generation["calls"],
              "generated_tokens": 0 if generation["calls"] == 0 else None, "tool_calls": 0,
              "ledger": {k:v for k,v in ledger.items() if not callable(v)}, "startup_ms": startup_ms,
              "whole_study_ms": elapsed(study), "core_audit": audit, "error": error,
              "accounting_complete": accounting_complete, "energy_j": None, "flops": None, "cost_money": None,
              "ledger_semantics": "completed passes plus known partial forwards; missing partial token counts UNKNOWN",
              "new_training": False, "frontier_calls": 0, "sealed_data_opened": False,
              "general_capability_gate": "NOT_EVALUATED", "global_questions_closed": []}
    write_new(directory / "report.json", report)
    pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob("*.json"))}
    write_new(directory / "terminal.json", {"schema": manifest()["schema"], "files": pins,
                                           "no_replacement": True, "complete": accounting_complete,
                                           "decision": verdict["verdict"]})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory")
    parser.add_argument("--frozen-head")
    parser.add_argument("--check-registration", action="store_true")
    args = parser.parse_args()
    if args.check_registration:
        registration, rows = registered_sources()
        print(canonical({"registration_valid": True, "public_rows": len(rows), "contract_sha256": digest(registration["contract"]), "model_inference": False}))
    else:
        if not args.directory or not args.frozen_head:
            parser.error("first execution requires directory and frozen head")
        result = run_study(args.directory, args.frozen_head)
        print(canonical(result))
        raise SystemExit(0 if result["decision"]["verdict"] == "PASS" else 2)
