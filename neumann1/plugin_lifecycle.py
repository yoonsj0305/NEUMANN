from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import sys

from .family_registry import FamilyAdapter
from .plugin_isolation import build_out_of_process_adapter
from .plugin_manifest import ActivationPolicy, PluginManifest, PluginStateClass
from .persistent_plugin_isolation import (
    WorkerStatePolicy, build_persistent_out_of_process_adapter,
)


class LifecycleMode(str, Enum):
    PERSISTENT = "persistent"
    FRESH_PROCESS = "fresh_process"
    REJECT = "reject"


class LifecyclePolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class LifecycleResolution:
    state_class: PluginStateClass | None
    mode: LifecycleMode
    reason: str
    worker_state_policy: WorkerStatePolicy | None = None


def resolve_plugin_lifecycle(
    manifest: PluginManifest,
    *,
    state_policy: WorkerStatePolicy | None = None,
) -> LifecycleResolution:
    manifest.validate()
    declared = manifest.state_class

    if declared is None:
        return LifecycleResolution(
            state_class=None,
            mode=LifecycleMode.FRESH_PROCESS,
            reason="legacy_or_undeclared_state_class_fails_safe_to_fresh_process",
            worker_state_policy=None,
        )

    if declared == PluginStateClass.STATELESS_SEMANTICS:
        return LifecycleResolution(
            state_class=declared,
            mode=LifecycleMode.PERSISTENT,
            reason="semantic_correctness_declared_independent_of_hidden_worker_state",
            worker_state_policy=state_policy or WorkerStatePolicy(),
        )

    if declared == PluginStateClass.CACHE_ONLY:
        effective = state_policy or WorkerStatePolicy()
        if effective.max_requests_per_worker is None:
            raise LifecyclePolicyError(
                "cache_only plugins require an explicit finite max_requests_per_worker"
            )
        effective.validate()
        return LifecycleResolution(
            state_class=declared,
            mode=LifecycleMode.PERSISTENT,
            reason="cache_state_allowed_but_bounded_by_mandatory_worker_recycling",
            worker_state_policy=effective,
        )

    if declared == PluginStateClass.EXPLICIT_STATEFUL:
        return LifecycleResolution(
            state_class=declared,
            mode=LifecycleMode.REJECT,
            reason=(
                "explicit_stateful semantics require a session/state protocol that "
                "NEUMANN does not yet implement"
            ),
            worker_state_policy=None,
        )

    if declared == PluginStateClass.NON_PERSISTENT_ONLY:
        return LifecycleResolution(
            state_class=declared,
            mode=LifecycleMode.FRESH_PROCESS,
            reason="plugin explicitly forbids persistent worker reuse",
            worker_state_policy=None,
        )

    raise LifecyclePolicyError(f"unsupported plugin state class: {declared!r}")


def build_declared_lifecycle_adapter(
    manifest: PluginManifest,
    authorization_ledger: object,
    *,
    timeout_seconds: float = 2.0,
    python_executable: str = sys.executable,
    policy: ActivationPolicy | None = None,
    state_policy: WorkerStatePolicy | None = None,
) -> FamilyAdapter:
    resolution = resolve_plugin_lifecycle(manifest, state_policy=state_policy)

    if resolution.mode == LifecycleMode.REJECT:
        raise LifecyclePolicyError(resolution.reason)

    if resolution.mode == LifecycleMode.FRESH_PROCESS:
        return build_out_of_process_adapter(
            manifest,
            authorization_ledger,
            timeout_seconds=timeout_seconds,
            python_executable=python_executable,
            policy=policy,
        )

    return build_persistent_out_of_process_adapter(
        manifest,
        authorization_ledger,
        timeout_seconds=timeout_seconds,
        python_executable=python_executable,
        policy=policy,
        state_policy=resolution.worker_state_policy,
    )