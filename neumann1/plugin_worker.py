from __future__ import annotations

import contextlib
import json
import os
import sys
import time
from typing import Any

from .plugin_loading import resolve_python_entry_point
from .plugin_manifest import PluginActivator, PluginManifest
from .types import CostLedger, IRKind, Problem, Representation, VerificationResult


PLUGIN_RPC_VERSION = "neumann.plugin.rpc.v1"
MAX_REQUEST_BYTES = 64 * 1024


def _decode_kind(value: str):
    try:
        return IRKind(value)
    except ValueError:
        return value


def _rep_from_dict(data: dict[str, Any]) -> Representation:
    return Representation(
        kind=_decode_kind(str(data["kind"])),
        payload=dict(data.get("payload", {})),
        confidence=float(data.get("confidence", 0.0)),
        rationale=str(data.get("rationale", "")),
    )


def _rep_to_dict(rep: Representation) -> dict[str, Any]:
    kind = rep.kind.value if isinstance(rep.kind, IRKind) else str(rep.kind)
    return {
        "kind": kind,
        "payload": rep.payload,
        "confidence": rep.confidence,
        "rationale": rep.rationale,
    }


def _ledger_to_dict(ledger: CostLedger) -> dict[str, int]:
    return {
        "representation_steps": ledger.representation_steps,
        "solver_steps": ledger.solver_steps,
        "verification_steps": ledger.verification_steps,
        "fallback_steps": ledger.fallback_steps,
    }


def _run(request: dict[str, Any]) -> dict[str, Any]:
    if request.get("protocol_version") != PLUGIN_RPC_VERSION:
        raise ValueError("unsupported plugin RPC version")

    manifest = PluginManifest.from_dict(dict(request["manifest"]))
    operation = str(request["operation"])
    payload = dict(request.get("payload", {}))

    # Plugin import/output stays in the child process. Redirect ordinary Python
    # stdout from plugin code so protocol stdout remains JSON-only.
    with contextlib.redirect_stdout(sys.stderr):
        adapter = PluginActivator(resolve_python_entry_point).activate(manifest)
        ledger = CostLedger()

        if operation == "compile":
            problem_data = dict(payload["problem"])
            problem = Problem(
                raw_text=str(problem_data["raw_text"]),
                metadata=dict(problem_data.get("metadata", {})),
            )
            rep = adapter.compiler.form(problem, ledger)
            result = {"representation": _rep_to_dict(rep)}

        elif operation == "solve":
            rep = _rep_from_dict(dict(payload["representation"]))
            if not adapter.solver.supports(rep):
                raise ValueError("plugin solver rejected supplied representation")
            answer = adapter.solver.solve(rep, ledger)
            result = {"answer": answer, "solver_name": str(adapter.solver.name)}

        elif operation == "verify":
            problem_data = dict(payload["problem"])
            problem = Problem(
                raw_text=str(problem_data["raw_text"]),
                metadata=dict(problem_data.get("metadata", {})),
            )
            rep = _rep_from_dict(dict(payload["representation"]))
            vr = adapter.answer_verifier.verify(
                problem, rep, payload.get("answer"), ledger
            )
            if not isinstance(vr, VerificationResult):
                raise TypeError("plugin verifier must return VerificationResult")
            result = {"verification": {"ok": vr.ok, "reason": vr.reason}}

        else:
            raise ValueError(f"unsupported plugin RPC operation: {operation}")

    return {
        "ok": True,
        "protocol_version": PLUGIN_RPC_VERSION,
        "worker_pid": os.getpid(),
        "ledger": _ledger_to_dict(ledger),
        "result": result,
    }


def main() -> int:
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        response = {"ok": False, "error": "request exceeds byte limit"}
    else:
        try:
            request = json.loads(raw.decode("utf-8"))
            if not isinstance(request, dict):
                raise ValueError("RPC request must be a JSON object")
            service_start = time.perf_counter()
            response = _run(request)
            response["service_seconds"] = time.perf_counter() - service_start
        except BaseException as exc:
            response = {
                "ok": False,
                "protocol_version": PLUGIN_RPC_VERSION,
                "worker_pid": os.getpid(),
                "error": f"{type(exc).__name__}: {exc}",
                "service_seconds": None,
            }

    sys.stdout.write(json.dumps(response, separators=(",", ":"), ensure_ascii=True))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())