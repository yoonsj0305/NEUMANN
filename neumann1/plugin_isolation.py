from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from .family_registry import FamilyAdapter
from .plugin_manifest import ActivationPolicy, PluginManifest
from .worker_lifecycle import require_fresh_compatible
from .types import (
    CostLedger, IRKind, Problem, Representation, VerificationResult, kind_id,
)


PLUGIN_RPC_VERSION = "neumann.plugin.rpc.v1"
MAX_REQUEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 256 * 1024


class PluginProcessError(RuntimeError):
    pass


class PluginProcessTimeout(PluginProcessError):
    pass


class PluginProtocolError(PluginProcessError):
    pass


def _kind_text(kind) -> str:
    return kind.value if isinstance(kind, IRKind) else str(kind)


def _rep_to_dict(rep: Representation) -> dict[str, Any]:
    return {
        "kind": _kind_text(rep.kind),
        "payload": rep.payload,
        "confidence": rep.confidence,
        "rationale": rep.rationale,
    }


def _rep_from_dict(data: dict[str, Any]) -> Representation:
    raw_kind = str(data["kind"])
    try:
        kind = IRKind(raw_kind)
    except ValueError:
        kind = raw_kind
    return Representation(
        kind=kind,
        payload=dict(data.get("payload", {})),
        confidence=float(data.get("confidence", 0.0)),
        rationale=str(data.get("rationale", "")),
    )


def _merge_ledger(target: CostLedger, child: dict[str, Any]) -> None:
    target.representation_steps += int(child.get("representation_steps", 0))
    target.solver_steps += int(child.get("solver_steps", 0))
    target.verification_steps += int(child.get("verification_steps", 0))
    target.fallback_steps += int(child.get("fallback_steps", 0))


@dataclass
class SubprocessPluginDispatcher:
    manifest: PluginManifest
    authorization_ledger: object
    timeout_seconds: float = 2.0
    python_executable: str = sys.executable
    worker_pids: list[int] = field(default_factory=list)
    launch_count: int = 0
    dispatch_timings: list[dict[str, float | str | int]] = field(default_factory=list)

    def __post_init__(self):
        self.manifest.validate()
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def dispatch(
        self, operation: str, payload: dict[str, Any], ledger: CostLedger
    ) -> dict[str, Any]:
        # Authorization is checked immediately before process creation.
        self.authorization_ledger.require_manifest(self.manifest)

        request = {
            "protocol_version": PLUGIN_RPC_VERSION,
            "manifest": self.manifest.canonical_dict(),
            "operation": operation,
            "payload": payload,
        }
        try:
            raw = json.dumps(
                request, separators=(",", ":"), ensure_ascii=True
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise PluginProtocolError(
                f"request is not JSON-serializable: {exc}"
            ) from exc

        if len(raw) > MAX_REQUEST_BYTES:
            raise PluginProtocolError("request exceeds byte limit")

        self.launch_count += 1
        dispatch_start = time.perf_counter()
        try:
            completed = subprocess.run(
                [self.python_executable, "-m", "neumann1.plugin_worker"],
                input=raw,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise PluginProcessTimeout(
                f"plugin {operation} exceeded {self.timeout_seconds}s timeout"
            ) from exc

        if completed.returncode != 0:
            raise PluginProcessError(
                f"plugin worker exited with status {completed.returncode}"
            )
        if len(completed.stdout) > MAX_RESPONSE_BYTES:
            raise PluginProtocolError("plugin response exceeds byte limit")

        try:
            response = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PluginProtocolError("plugin worker returned invalid JSON") from exc

        if not isinstance(response, dict):
            raise PluginProtocolError("plugin response must be a JSON object")
        if not response.get("ok"):
            raise PluginProcessError(str(response.get("error", "plugin operation failed")))
        if response.get("protocol_version") != PLUGIN_RPC_VERSION:
            raise PluginProtocolError("plugin response protocol version mismatch")

        dispatch_seconds = time.perf_counter() - dispatch_start
        service_seconds = float(response.get("service_seconds", 0.0))
        worker_pid = int(response["worker_pid"])
        self.worker_pids.append(worker_pid)
        self.dispatch_timings.append({
            "operation": operation,
            "worker_pid": worker_pid,
            "dispatch_seconds": dispatch_seconds,
            "service_seconds": service_seconds,
            "outside_service_seconds": max(0.0, dispatch_seconds - service_seconds),
        })
        _merge_ledger(ledger, dict(response.get("ledger", {})))
        return dict(response["result"])


class OutOfProcessCompiler:
    def __init__(self, dispatcher: SubprocessPluginDispatcher):
        self.dispatcher = dispatcher

    def form(self, problem: Problem, ledger: CostLedger) -> Representation:
        try:
            result = self.dispatcher.dispatch(
                "compile",
                {"problem": {"raw_text": problem.raw_text, "metadata": problem.metadata}},
                ledger,
            )
            return _rep_from_dict(dict(result["representation"]))
        except (PermissionError, PluginProcessError) as exc:
            ledger.fallback_steps += 1
            return Representation(
                kind=IRKind.UNKNOWN,
                payload={},
                confidence=0.0,
                rationale=f"out-of-process compiler fail-closed: {exc}",
            )


class OutOfProcessSolver:
    def __init__(self, dispatcher: SubprocessPluginDispatcher):
        self.dispatcher = dispatcher
        self.name = f"oop:{dispatcher.manifest.family_id}"

    def supports(self, representation: Representation) -> bool:
        try:
            return kind_id(representation.kind) == kind_id(self.dispatcher.manifest.kind)
        except (TypeError, ValueError):
            return False

    def solve(self, representation: Representation, ledger: CostLedger):
        result = self.dispatcher.dispatch(
            "solve", {"representation": _rep_to_dict(representation)}, ledger
        )
        return result.get("answer")


class OutOfProcessVerifier:
    def __init__(self, dispatcher: SubprocessPluginDispatcher):
        self.dispatcher = dispatcher

    def verify(
        self, problem: Problem, representation: Representation, answer, ledger: CostLedger
    ) -> VerificationResult:
        result = self.dispatcher.dispatch(
            "verify",
            {
                "problem": {"raw_text": problem.raw_text, "metadata": problem.metadata},
                "representation": _rep_to_dict(representation),
                "answer": answer,
            },
            ledger,
        )
        data = dict(result["verification"])
        return VerificationResult(ok=bool(data["ok"]), reason=str(data["reason"]))


def build_out_of_process_adapter(
    manifest: PluginManifest,
    authorization_ledger: object,
    *,
    timeout_seconds: float = 2.0,
    python_executable: str = sys.executable,
    policy: ActivationPolicy | None = None,
) -> FamilyAdapter:
    """Create proxy components without importing plugin code in the core process."""
    manifest.validate()
    (policy or ActivationPolicy()).check(manifest)
    authorization_ledger.require_manifest(manifest)
    require_fresh_compatible(manifest)

    dispatcher = SubprocessPluginDispatcher(
        manifest=manifest,
        authorization_ledger=authorization_ledger,
        timeout_seconds=timeout_seconds,
        python_executable=python_executable,
    )
    return FamilyAdapter(
        family_id=manifest.family_id,
        ir_kind=manifest.kind,
        compiler=OutOfProcessCompiler(dispatcher),
        solver=OutOfProcessSolver(dispatcher),
        answer_verifier=OutOfProcessVerifier(dispatcher),
        contract_version=manifest.family_contract_version,
    )