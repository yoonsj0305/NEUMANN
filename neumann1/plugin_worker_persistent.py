from __future__ import annotations

import contextlib
import json
import os
import sys
import time
from typing import Any

from .plugin_loading import resolve_python_entry_point
from .plugin_manifest import PluginActivator, PluginManifest
from .plugin_worker import _ledger_to_dict, _rep_from_dict, _rep_to_dict
from .types import CostLedger, Problem, VerificationResult


PERSISTENT_PLUGIN_RPC_VERSION = "neumann.plugin.persistent-rpc.v1"
MAX_LINE_BYTES = 256 * 1024


def _write(response: dict[str, Any]) -> None:
    raw = json.dumps(response, separators=(",", ":"), ensure_ascii=True)
    sys.stdout.write(raw + "\n")
    sys.stdout.flush()


def _read_line() -> bytes | None:
    raw = sys.stdin.buffer.readline(MAX_LINE_BYTES + 1)
    if not raw:
        return None
    if len(raw) > MAX_LINE_BYTES:
        raise ValueError("persistent RPC line exceeds byte limit")
    return raw


def _handle(adapter, request: dict[str, Any]) -> dict[str, Any]:
    if request.get("protocol_version") != PERSISTENT_PLUGIN_RPC_VERSION:
        raise ValueError("unsupported persistent plugin RPC version")

    request_id = int(request["request_id"])
    operation = str(request["operation"])
    payload = dict(request.get("payload", {}))
    ledger = CostLedger()
    service_start = time.perf_counter()

    with contextlib.redirect_stdout(sys.stderr):
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

        elif operation == "shutdown":
            result = {"shutdown": True}

        else:
            raise ValueError(f"unsupported persistent RPC operation: {operation}")

    return {
        "ok": True,
        "protocol_version": PERSISTENT_PLUGIN_RPC_VERSION,
        "request_id": request_id,
        "worker_pid": os.getpid(),
        "service_seconds": time.perf_counter() - service_start,
        "ledger": _ledger_to_dict(ledger),
        "result": result,
    }


def main() -> int:
    try:
        init_raw = _read_line()
        if init_raw is None:
            return 2
        init = json.loads(init_raw.decode("utf-8"))
        if not isinstance(init, dict):
            raise ValueError("init request must be an object")
        if init.get("protocol_version") != PERSISTENT_PLUGIN_RPC_VERSION:
            raise ValueError("unsupported persistent plugin RPC version")
        if init.get("operation") != "initialize":
            raise ValueError("first persistent RPC operation must be initialize")

        manifest = PluginManifest.from_dict(dict(init["manifest"]))
        with contextlib.redirect_stdout(sys.stderr):
            adapter = PluginActivator(resolve_python_entry_point).activate(manifest)

        _write({
            "ok": True,
            "protocol_version": PERSISTENT_PLUGIN_RPC_VERSION,
            "request_id": int(init.get("request_id", 0)),
            "worker_pid": os.getpid(),
            "manifest_digest_sha256": manifest.digest_sha256,
            "result": {"initialized": True},
        })

        while True:
            raw = _read_line()
            if raw is None:
                break
            try:
                request = json.loads(raw.decode("utf-8"))
                if not isinstance(request, dict):
                    raise ValueError("RPC request must be an object")
                response = _handle(adapter, request)
            except BaseException as exc:
                response = {
                    "ok": False,
                    "protocol_version": PERSISTENT_PLUGIN_RPC_VERSION,
                    "request_id": (
                        request.get("request_id")
                        if isinstance(locals().get("request"), dict)
                        else None
                    ),
                    "worker_pid": os.getpid(),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            _write(response)
            if response.get("ok") and response.get("result", {}).get("shutdown"):
                break
        return 0
    except BaseException as exc:
        _write({
            "ok": False,
            "protocol_version": PERSISTENT_PLUGIN_RPC_VERSION,
            "request_id": 0,
            "worker_pid": os.getpid(),
            "error": f"{type(exc).__name__}: {exc}",
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())