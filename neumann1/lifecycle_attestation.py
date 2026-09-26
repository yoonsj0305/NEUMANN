from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Iterable

from .family_registry import ManagedPluginRegistry, builtin_family_registry
from .persistent_plugin_isolation import (
    WorkerStatePolicy,
    _build_unattested_persistent_adapter_for_conformance,
)
from .plugin_manifest import PluginManifest
from .registry_engine import RegistryEngine
from .types import Problem, SolveResult
from .worker_lifecycle import WorkerStateClass, require_persistent_compatible


LIFECYCLE_ATTESTATION_VERSION = "neumann.lifecycle-attestation.v1"
MIN_ATTESTATION_CASES = 3
MIN_WARM_REPETITIONS = 2


class AttestationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class LifecycleConformanceCase:
    case_id: str
    raw_text: str
    expected_answer_subset: dict[str, Any]
    metadata: dict[str, Any] | None = None

    def validate(self) -> None:
        if not self.case_id or not self.case_id.strip():
            raise ValueError("case_id must be nonempty")
        if not isinstance(self.raw_text, str) or not self.raw_text:
            raise ValueError("raw_text must be nonempty")
        if not isinstance(self.expected_answer_subset, dict):
            raise ValueError("expected_answer_subset must be an object")
        _json_bytes(self.canonical_dict())

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "raw_text": self.raw_text,
            "expected_answer_subset": self.expected_answer_subset,
            "metadata": dict(self.metadata or {}),
        }


def conformance_corpus_digest(cases: Iterable[LifecycleConformanceCase]) -> str:
    rows = tuple(cases)
    if not rows:
        raise ValueError("lifecycle conformance corpus must not be empty")
    ids = [case.case_id for case in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("lifecycle conformance case_id values must be unique")
    for case in rows:
        case.validate()
    return hashlib.sha256(_json_bytes([case.canonical_dict() for case in rows])).hexdigest()


@dataclass(frozen=True)
class LifecycleAttestation:
    attestation_version: str
    manifest_digest_sha256: str
    plugin_id: str
    worker_state_class: WorkerStateClass
    corpus_digest_sha256: str
    case_count: int
    warm_repetitions: int
    warm_passed: bool
    recycled_passed: bool
    cross_generation_passed: bool
    semantic_equivalence_rate: float
    warm_generation_count: int
    recycled_generation_count: int
    cross_generation_count: int
    status: AttestationStatus
    failure_reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.attestation_version != LIFECYCLE_ATTESTATION_VERSION:
            raise ValueError("unsupported lifecycle attestation version")
        if len(self.manifest_digest_sha256) != 64:
            raise ValueError("manifest_digest_sha256 must be a SHA-256 hex digest")
        if len(self.corpus_digest_sha256) != 64:
            raise ValueError("corpus_digest_sha256 must be a SHA-256 hex digest")
        if self.worker_state_class not in {WorkerStateClass.STATELESS, WorkerStateClass.CACHE_ONLY}:
            raise ValueError("only STATELESS and CACHE_ONLY can receive persistent attestation")
        if self.case_count < MIN_ATTESTATION_CASES:
            raise ValueError(f"attestation requires at least {MIN_ATTESTATION_CASES} cases")
        if self.warm_repetitions < MIN_WARM_REPETITIONS:
            raise ValueError(f"attestation requires at least {MIN_WARM_REPETITIONS} warm repetitions")
        if not (0.0 <= self.semantic_equivalence_rate <= 1.0):
            raise ValueError("semantic_equivalence_rate must be between 0 and 1")
        if min(
            self.warm_generation_count,
            self.recycled_generation_count,
            self.cross_generation_count,
        ) < 1:
            raise ValueError("attestation generation counts must be positive")
        if self.status == AttestationStatus.PASS:
            if not (self.warm_passed and self.recycled_passed and self.cross_generation_passed):
                raise ValueError("PASS attestation requires every execution mode to pass")
            if self.semantic_equivalence_rate != 1.0:
                raise ValueError("PASS attestation requires semantic_equivalence_rate == 1.0")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "attestation_version": self.attestation_version,
            "manifest_digest_sha256": self.manifest_digest_sha256,
            "plugin_id": self.plugin_id,
            "worker_state_class": self.worker_state_class.value,
            "corpus_digest_sha256": self.corpus_digest_sha256,
            "case_count": self.case_count,
            "warm_repetitions": self.warm_repetitions,
            "warm_passed": self.warm_passed,
            "recycled_passed": self.recycled_passed,
            "cross_generation_passed": self.cross_generation_passed,
            "semantic_equivalence_rate": self.semantic_equivalence_rate,
            "warm_generation_count": self.warm_generation_count,
            "recycled_generation_count": self.recycled_generation_count,
            "cross_generation_count": self.cross_generation_count,
            "status": self.status.value,
            "failure_reasons": list(self.failure_reasons),
        }

    @property
    def digest_sha256(self) -> str:
        return hashlib.sha256(_json_bytes(self.canonical_dict())).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        data = self.canonical_dict()
        data["attestation_digest_sha256"] = self.digest_sha256
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LifecycleAttestation":
        attestation = cls(
            attestation_version=str(data["attestation_version"]),
            manifest_digest_sha256=str(data["manifest_digest_sha256"]),
            plugin_id=str(data["plugin_id"]),
            worker_state_class=WorkerStateClass(str(data["worker_state_class"])),
            corpus_digest_sha256=str(data["corpus_digest_sha256"]),
            case_count=int(data["case_count"]),
            warm_repetitions=int(data["warm_repetitions"]),
            warm_passed=bool(data["warm_passed"]),
            recycled_passed=bool(data["recycled_passed"]),
            cross_generation_passed=bool(data["cross_generation_passed"]),
            semantic_equivalence_rate=float(data["semantic_equivalence_rate"]),
            warm_generation_count=int(data["warm_generation_count"]),
            recycled_generation_count=int(data["recycled_generation_count"]),
            cross_generation_count=int(data["cross_generation_count"]),
            status=AttestationStatus(str(data["status"])),
            failure_reasons=tuple(str(x) for x in data.get("failure_reasons", ())),
        )
        attestation.validate()
        claimed = data.get("attestation_digest_sha256")
        if claimed is not None and str(claimed) != attestation.digest_sha256:
            raise ValueError("lifecycle attestation digest mismatch")
        return attestation


class LifecycleAttestationRegistry:
    """Trusted control-plane registry for exact-manifest lifecycle evidence."""

    def __init__(self, attestations: Iterable[LifecycleAttestation] = ()):
        self._by_manifest_digest: dict[str, LifecycleAttestation] = {}
        self._digests_by_plugin: dict[str, set[str]] = {}
        for attestation in attestations:
            self.register(attestation)

    def register(self, attestation: LifecycleAttestation) -> None:
        attestation.validate()
        self._by_manifest_digest[attestation.manifest_digest_sha256] = attestation
        self._digests_by_plugin.setdefault(attestation.plugin_id, set()).add(
            attestation.manifest_digest_sha256
        )

    def get(self, manifest_digest_sha256: str) -> LifecycleAttestation | None:
        return self._by_manifest_digest.get(manifest_digest_sha256)

    def require_manifest(self, manifest: PluginManifest) -> LifecycleAttestation:
        manifest.validate()
        attestation = self._by_manifest_digest.get(manifest.digest_sha256)
        if attestation is None:
            known = self._digests_by_plugin.get(manifest.plugin_id, set())
            if known:
                raise PermissionError(
                    "lifecycle attestation is stale or bound to a different manifest digest"
                )
            raise PermissionError("passing lifecycle attestation required for persistent execution")
        if attestation.plugin_id != manifest.plugin_id:
            raise PermissionError("lifecycle attestation plugin identity mismatch")
        if attestation.worker_state_class != manifest.worker_state_class:
            raise PermissionError("lifecycle attestation state-class mismatch")
        if attestation.status != AttestationStatus.PASS:
            raise PermissionError("lifecycle attestation did not pass")
        attestation.validate()
        return attestation


def run_lifecycle_conformance_attestation(
    manifest: PluginManifest,
    authorization_ledger: object,
    cases: Iterable[LifecycleConformanceCase],
    *,
    warm_repetitions: int = MIN_WARM_REPETITIONS,
    timeout_seconds: float = 8.0,
) -> LifecycleAttestation:
    manifest.validate()
    require_persistent_compatible(manifest)
    if manifest.worker_state_class not in {WorkerStateClass.STATELESS, WorkerStateClass.CACHE_ONLY}:
        raise ValueError("only persistent-compatible state classes can be attested")
    rows = tuple(cases)
    corpus_digest = conformance_corpus_digest(rows)
    if len(rows) < MIN_ATTESTATION_CASES:
        raise ValueError(f"attestation requires at least {MIN_ATTESTATION_CASES} cases")
    if warm_repetitions < MIN_WARM_REPETITIONS:
        raise ValueError(f"warm_repetitions must be >= {MIN_WARM_REPETITIONS}")

    failures: list[str] = []
    passed_checks = 0
    total_checks = len(rows) * (warm_repetitions + 2)

    warm_adapter, warm_engine = _conformance_engine(
        manifest, authorization_ledger, timeout_seconds=timeout_seconds, state_policy=WorkerStatePolicy()
    )
    try:
        warm_ok = True
        for case in rows:
            for repeat in range(warm_repetitions):
                result = warm_engine.solve(Problem(case.raw_text, metadata=dict(case.metadata or {})))
                ok = _result_matches(result, case.expected_answer_subset)
                passed_checks += int(ok)
                warm_ok = warm_ok and ok
                if not ok:
                    failures.append(f"warm:{case.case_id}:repeat={repeat}")
        warm_generations = _unique_generation_count(warm_adapter)
    finally:
        warm_adapter.compiler.dispatcher.close()

    recycled_adapter, recycled_engine = _conformance_engine(
        manifest, authorization_ledger, timeout_seconds=timeout_seconds, state_policy=WorkerStatePolicy()
    )
    try:
        recycled_ok = True
        for case in rows:
            recycled_adapter.compiler.dispatcher.recycle("lifecycle_attestation_case_boundary")
            result = recycled_engine.solve(Problem(case.raw_text, metadata=dict(case.metadata or {})))
            ok = _result_matches(result, case.expected_answer_subset)
            passed_checks += int(ok)
            recycled_ok = recycled_ok and ok
            if not ok:
                failures.append(f"recycled:{case.case_id}")
        recycled_generations = _unique_generation_count(recycled_adapter)
    finally:
        recycled_adapter.compiler.dispatcher.close()

    cross_adapter, cross_engine = _conformance_engine(
        manifest,
        authorization_ledger,
        timeout_seconds=timeout_seconds,
        state_policy=WorkerStatePolicy(max_requests_per_worker=1),
    )
    try:
        cross_ok = True
        for case in rows:
            result = cross_engine.solve(Problem(case.raw_text, metadata=dict(case.metadata or {})))
            ok = _result_matches(result, case.expected_answer_subset)
            passed_checks += int(ok)
            cross_ok = cross_ok and ok
            if not ok:
                failures.append(f"cross_generation:{case.case_id}")
        cross_generations = _unique_generation_count(cross_adapter)
    finally:
        cross_adapter.compiler.dispatcher.close()

    rate = passed_checks / total_checks if total_checks else 0.0
    status = (
        AttestationStatus.PASS
        if warm_ok and recycled_ok and cross_ok and rate == 1.0
        else AttestationStatus.FAIL
    )
    attestation = LifecycleAttestation(
        attestation_version=LIFECYCLE_ATTESTATION_VERSION,
        manifest_digest_sha256=manifest.digest_sha256,
        plugin_id=manifest.plugin_id,
        worker_state_class=manifest.worker_state_class,
        corpus_digest_sha256=corpus_digest,
        case_count=len(rows),
        warm_repetitions=warm_repetitions,
        warm_passed=warm_ok,
        recycled_passed=recycled_ok,
        cross_generation_passed=cross_ok,
        semantic_equivalence_rate=rate,
        warm_generation_count=warm_generations,
        recycled_generation_count=recycled_generations,
        cross_generation_count=cross_generations,
        status=status,
        failure_reasons=tuple(failures),
    )
    attestation.validate()
    return attestation


def _conformance_engine(manifest, authorization_ledger, *, timeout_seconds, state_policy):
    adapter = _build_unattested_persistent_adapter_for_conformance(
        manifest,
        authorization_ledger,
        timeout_seconds=timeout_seconds,
        state_policy=state_policy,
    )
    registry = ManagedPluginRegistry(builtin_family_registry(), authorization_ledger)
    registry.register_plugin(manifest, adapter)
    return adapter, RegistryEngine(adapter.compiler, registry)


def _result_matches(result: SolveResult, expected_subset: dict[str, Any]) -> bool:
    if not result.verified or not isinstance(result.answer, dict):
        return False
    for key, expected in expected_subset.items():
        if key not in result.answer or result.answer[key] != expected:
            return False
    return True


def _unique_generation_count(adapter) -> int:
    ids = {
        str(row.get("generation_id"))
        for row in adapter.compiler.dispatcher.dispatch_timings
        if row.get("generation_id")
    }
    return max(1, len(ids))


def _json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"lifecycle attestation data must be JSON-serializable: {exc}") from exc