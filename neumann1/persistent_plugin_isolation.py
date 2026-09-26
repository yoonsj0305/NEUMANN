from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .family_registry import FamilyAdapter
from .plugin_isolation import (
    MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, OutOfProcessCompiler,
    OutOfProcessSolver, OutOfProcessVerifier, PluginProcessError,
    PluginProcessTimeout, PluginProtocolError, _merge_ledger,
)
from .plugin_manifest import ActivationPolicy, PluginManifest
from .worker_lifecycle import require_persistent_compatible


PERSISTENT_PLUGIN_RPC_VERSION = "neumann.plugin.persistent-rpc.v1"

@dataclass(frozen=True)
class WorkerStatePolicy:
    """Lifecycle policy for persistent plugin workers.

    max_requests_per_worker counts plugin operations (compile/solve/verify), not
    initialization or shutdown messages. None means no automatic count-based
    recycle. Semantic correctness must not depend on retained hidden worker state.
    """
    max_requests_per_worker: int | None = None

    def validate(self) -> None:
        if self.max_requests_per_worker is not None and self.max_requests_per_worker <= 0:
            raise ValueError("max_requests_per_worker must be positive or None")


@dataclass(frozen=True)
class WorkerRecycleEvent:
    reason: str
    generation_id: str | None
    worker_pid: int | None
    requests_in_generation: int


@dataclass
class PersistentSubprocessPluginDispatcher:
    manifest: PluginManifest
    authorization_ledger: object
    attestation_registry: object | None = None
    timeout_seconds: float = 2.0
    python_executable: str = sys.executable
    state_policy: WorkerStatePolicy = field(default_factory=WorkerStatePolicy)
    start_count: int = 0
    request_count: int = 0
    worker_pids: list[int] = field(default_factory=list)
    dispatch_timings: list[dict[str, float | str | int]] = field(default_factory=list)
    startup_timings: list[float] = field(default_factory=list)
    recycle_events: list[WorkerRecycleEvent] = field(default_factory=list)

    def __post_init__(self):
        self.manifest.validate()
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.state_policy.validate()
        self._process = None
        self._responses = None
        self._reader = None
        self._request_id = 0
        self._generation_sequence = 0
        self._generation_id = None
        self._requests_in_generation = 0
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def worker_pid(self) -> int | None:
        return self._process.pid if self.is_running else None

    @property
    def generation_id(self) -> str | None:
        return self._generation_id if self.is_running else None

    @property
    def requests_in_generation(self) -> int:
        return self._requests_in_generation if self.is_running else 0

    def _reader_loop(self, process, responses):
        try:
            for raw in iter(process.stdout.readline, b""):
                responses.put(raw)
        finally:
            responses.put(None)

    def _next_response(self, timeout: float) -> dict[str, Any]:
        if self._responses is None:
            raise PluginProcessError("persistent worker response channel unavailable")
        try:
            raw = self._responses.get(timeout=timeout)
        except queue.Empty as exc:
            self._kill_worker()
            raise PluginProcessTimeout(
                f"persistent plugin request exceeded {timeout}s timeout"
            ) from exc
        if raw is None:
            code = self._process.poll() if self._process is not None else None
            self._reset_handles()
            raise PluginProcessError(
                f"persistent plugin worker closed response channel (status={code})"
            )
        if len(raw) > MAX_RESPONSE_BYTES:
            self._kill_worker()
            raise PluginProtocolError("persistent plugin response exceeds byte limit")
        try:
            response = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._kill_worker()
            raise PluginProtocolError("persistent plugin worker returned invalid JSON") from exc
        if not isinstance(response, dict):
            self._kill_worker()
            raise PluginProtocolError("persistent plugin response must be an object")
        return response

    def _send(self, request: dict[str, Any]) -> None:
        if not self.is_running or self._process.stdin is None:
            raise PluginProcessError("persistent plugin worker is not running")
        try:
            raw = json.dumps(
                request, separators=(",", ":"), ensure_ascii=True
            ).encode("utf-8") + b"\n"
        except (TypeError, ValueError) as exc:
            raise PluginProtocolError(
                f"request is not JSON-serializable: {exc}"
            ) from exc
        if len(raw) > MAX_REQUEST_BYTES:
            raise PluginProtocolError("persistent plugin request exceeds byte limit")
        try:
            self._process.stdin.write(raw)
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self._kill_worker()
            raise PluginProcessError("persistent plugin request pipe failed") from exc

    def _validate_response(self, response: dict[str, Any], request_id: int) -> None:
        if response.get("protocol_version") != PERSISTENT_PLUGIN_RPC_VERSION:
            self._kill_worker()
            raise PluginProtocolError("persistent plugin protocol version mismatch")
        if int(response.get("request_id", -1)) != request_id:
            self._kill_worker()
            raise PluginProtocolError("persistent plugin request/response ID mismatch")
        if response.get("generation_id") != self._generation_id:
            self._kill_worker()
            raise PluginProtocolError("persistent plugin generation ID mismatch")
        if not response.get("ok"):
            error = str(response.get("error", "persistent plugin operation failed"))
            # Worker-level plugin errors invalidate this worker because plugin state
            # after an exception is not assumed trustworthy.
            self._kill_worker()
            raise PluginProcessError(error)

    def _require_runtime_evidence(self) -> None:
        self.authorization_ledger.require_manifest(self.manifest)
        if self.attestation_registry is not None:
            require = getattr(self.attestation_registry, "require_manifest", None)
            if not callable(require):
                raise TypeError(
                    "attestation_registry must provide require_manifest(manifest)"
                )
            require(self.manifest)

    def _ensure_started(self) -> None:
        if self.is_running:
            return
        self._require_runtime_evidence()
        start = time.perf_counter()
        process = subprocess.Popen(
            [self.python_executable, "-m", "neumann1.plugin_worker_persistent"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )
        responses = queue.Queue()
        reader = threading.Thread(
            target=self._reader_loop, args=(process, responses), daemon=True
        )
        reader.start()
        self._process = process
        self._responses = responses
        self._reader = reader
        self.start_count += 1
        self._generation_sequence += 1
        self._generation_id = (
            f"{self.manifest.plugin_id}:g{self._generation_sequence}:{uuid.uuid4().hex}"
        )
        self._requests_in_generation = 0

        init_id = 0
        try:
            self._send({
                "protocol_version": PERSISTENT_PLUGIN_RPC_VERSION,
                "request_id": init_id,
                "operation": "initialize",
                "manifest": self.manifest.canonical_dict(),
                "generation_id": self._generation_id,
            })
            response = self._next_response(self.timeout_seconds)
            self._validate_response(response, init_id)
            if response.get("manifest_digest_sha256") != self.manifest.digest_sha256:
                self._kill_worker()
                raise PluginProtocolError("persistent worker initialized wrong manifest digest")
            self.worker_pids.append(int(response["worker_pid"]))
            self.startup_timings.append(time.perf_counter() - start)
        except BaseException:
            self._kill_worker()
            raise

    def dispatch(
        self, operation: str, payload: dict[str, Any], ledger
    ) -> dict[str, Any]:
        with self._lock:
            try:
                self._require_runtime_evidence()
            except PermissionError:
                # Authorization or evidence revocation is fail-closed: terminate
                # without sending any further protocol message to plugin code.
                self._kill_worker()
                raise

            limit = self.state_policy.max_requests_per_worker
            if (
                self.is_running
                and limit is not None
                and self._requests_in_generation >= limit
            ):
                self.recycle("max_requests_per_worker")

            self._ensure_started()
            self._request_id += 1
            request_id = self._request_id
            dispatch_start = time.perf_counter()
            self._send({
                "protocol_version": PERSISTENT_PLUGIN_RPC_VERSION,
                "request_id": request_id,
                "operation": operation,
                "payload": payload,
            })
            self.request_count += 1
            self._requests_in_generation += 1
            response = self._next_response(self.timeout_seconds)
            self._validate_response(response, request_id)

            dispatch_seconds = time.perf_counter() - dispatch_start
            service_seconds = float(response.get("service_seconds", 0.0))
            worker_pid = int(response["worker_pid"])
            self.dispatch_timings.append({
                "operation": operation,
                "worker_pid": worker_pid,
                "generation_id": str(self._generation_id),
                "requests_in_generation": self._requests_in_generation,
                "dispatch_seconds": dispatch_seconds,
                "service_seconds": service_seconds,
                "outside_service_seconds": max(0.0, dispatch_seconds - service_seconds),
            })
            _merge_ledger(ledger, dict(response.get("ledger", {})))
            return dict(response["result"])

    def _reset_handles(self) -> None:
        self._process = None
        self._responses = None
        self._reader = None
        self._generation_id = None
        self._requests_in_generation = 0

    def _kill_worker(self) -> None:
        process = self._process
        if process is not None and process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                pass
        self._reset_handles()

    def recycle(self, reason: str = "manual") -> None:
        event = WorkerRecycleEvent(
            reason=reason,
            generation_id=self._generation_id,
            worker_pid=self.worker_pid,
            requests_in_generation=self._requests_in_generation,
        )
        if self.is_running:
            self.recycle_events.append(event)
            self._kill_worker()

    def close(self) -> None:
        process = self._process
        if process is None:
            return
        if process.poll() is None:
            try:
                self._request_id += 1
                request_id = self._request_id
                self._send({
                    "protocol_version": PERSISTENT_PLUGIN_RPC_VERSION,
                    "request_id": request_id,
                    "operation": "shutdown",
                    "payload": {},
                })
                response = self._next_response(min(self.timeout_seconds, 1.0))
                self._validate_response(response, request_id)
                process.wait(timeout=1.0)
            except BaseException:
                if process.poll() is None:
                    process.kill()
                    try:
                        process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        pass
        self._reset_handles()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def _build_unattested_persistent_adapter_for_conformance(
    manifest: PluginManifest,
    authorization_ledger: object,
    *,
    timeout_seconds: float = 2.0,
    python_executable: str = sys.executable,
    policy: ActivationPolicy | None = None,
    state_policy: WorkerStatePolicy | None = None,
    runtime_attestation_registry: object | None = None,
) -> FamilyAdapter:
    """Conformance-only low-level builder.

    This function deliberately bypasses lifecycle attestation so the attestation
    harness can evaluate a candidate before privilege is granted. It still
    enforces manifest validation, activation policy, authorization, and lifecycle
    class compatibility. It is intentionally not exported from neumann1.__init__.
    """
    manifest.validate()
    (policy or ActivationPolicy()).check(manifest)
    authorization_ledger.require_manifest(manifest)
    require_persistent_compatible(manifest)
    dispatcher = PersistentSubprocessPluginDispatcher(
        manifest=manifest,
        authorization_ledger=authorization_ledger,
        attestation_registry=runtime_attestation_registry,
        timeout_seconds=timeout_seconds,
        python_executable=python_executable,
        state_policy=state_policy or WorkerStatePolicy(),
    )
    return FamilyAdapter(
        family_id=manifest.family_id,
        ir_kind=manifest.kind,
        compiler=OutOfProcessCompiler(dispatcher),
        solver=OutOfProcessSolver(dispatcher),
        answer_verifier=OutOfProcessVerifier(dispatcher),
        contract_version=manifest.family_contract_version,
    )

def build_persistent_out_of_process_adapter(
    manifest: PluginManifest,
    authorization_ledger: object,
    *,
    attestation_registry: object | None = None,
    timeout_seconds: float = 2.0,
    python_executable: str = sys.executable,
    policy: ActivationPolicy | None = None,
    state_policy: WorkerStatePolicy | None = None,
) -> FamilyAdapter:
    """Create an attestation-gated persistent plugin adapter.

    Persistent reuse is privileged: an exact-manifest PASS attestation must be
    present in the trusted attestation registry before any worker can be built.
    """
    manifest.validate()
    (policy or ActivationPolicy()).check(manifest)
    authorization_ledger.require_manifest(manifest)
    require_persistent_compatible(manifest)
    if attestation_registry is None:
        raise PermissionError(
            "passing lifecycle attestation required for persistent execution"
        )
    require = getattr(attestation_registry, "require_manifest", None)
    if not callable(require):
        raise TypeError("attestation_registry must provide require_manifest(manifest)")
    require(manifest)
    return _build_unattested_persistent_adapter_for_conformance(
        manifest,
        authorization_ledger,
        timeout_seconds=timeout_seconds,
        python_executable=python_executable,
        policy=policy,
        state_policy=state_policy,
        runtime_attestation_registry=attestation_registry,
    )
