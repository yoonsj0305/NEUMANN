from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from .family_registry import FamilyAdapter
from .plugin_isolation import (
    MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, OutOfProcessCompiler,
    OutOfProcessSolver, OutOfProcessVerifier, PluginProcessError,
    PluginProcessTimeout, PluginProtocolError, _merge_ledger,
)
from .plugin_manifest import ActivationPolicy, PluginManifest


PERSISTENT_PLUGIN_RPC_VERSION = "neumann.plugin.persistent-rpc.v1"


@dataclass
class PersistentSubprocessPluginDispatcher:
    manifest: PluginManifest
    authorization_ledger: object
    timeout_seconds: float = 2.0
    python_executable: str = sys.executable
    start_count: int = 0
    request_count: int = 0
    worker_pids: list[int] = field(default_factory=list)
    dispatch_timings: list[dict[str, float | str | int]] = field(default_factory=list)
    startup_timings: list[float] = field(default_factory=list)

    def __post_init__(self):
        self.manifest.validate()
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._process = None
        self._responses = None
        self._reader = None
        self._request_id = 0
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def worker_pid(self) -> int | None:
        return self._process.pid if self.is_running else None

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
        if not response.get("ok"):
            error = str(response.get("error", "persistent plugin operation failed"))
            # Worker-level plugin errors invalidate this worker because plugin state
            # after an exception is not assumed trustworthy.
            self._kill_worker()
            raise PluginProcessError(error)

    def _ensure_started(self) -> None:
        if self.is_running:
            return
        self.authorization_ledger.require_manifest(self.manifest)
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

        init_id = 0
        try:
            self._send({
                "protocol_version": PERSISTENT_PLUGIN_RPC_VERSION,
                "request_id": init_id,
                "operation": "initialize",
                "manifest": self.manifest.canonical_dict(),
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
                self.authorization_ledger.require_manifest(self.manifest)
            except PermissionError:
                self.close()
                raise

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
            response = self._next_response(self.timeout_seconds)
            self._validate_response(response, request_id)

            dispatch_seconds = time.perf_counter() - dispatch_start
            service_seconds = float(response.get("service_seconds", 0.0))
            worker_pid = int(response["worker_pid"])
            self.dispatch_timings.append({
                "operation": operation,
                "worker_pid": worker_pid,
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

    def _kill_worker(self) -> None:
        process = self._process
        if process is not None and process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                pass
        self._reset_handles()

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


def build_persistent_out_of_process_adapter(
    manifest: PluginManifest,
    authorization_ledger: object,
    *,
    timeout_seconds: float = 2.0,
    python_executable: str = sys.executable,
    policy: ActivationPolicy | None = None,
) -> FamilyAdapter:
    manifest.validate()
    (policy or ActivationPolicy()).check(manifest)
    authorization_ledger.require_manifest(manifest)
    dispatcher = PersistentSubprocessPluginDispatcher(
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