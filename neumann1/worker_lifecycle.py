from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .plugin_manifest import PluginManifest


class WorkerStateClass(str, Enum):
    STATELESS = "STATELESS"
    CACHE_ONLY = "CACHE_ONLY"
    STATEFUL_EXPLICIT = "STATEFUL_EXPLICIT"
    NON_PERSISTENT = "NON_PERSISTENT"


class LifecycleMode(str, Enum):
    FRESH_PROCESS = "fresh_process"
    PERSISTENT_WORKER = "persistent_worker"


@dataclass(frozen=True)
class LifecycleDecision:
    allowed: bool
    mode: LifecycleMode
    state_class: WorkerStateClass | None
    reason: str


def parse_worker_state_class(value: object | None) -> WorkerStateClass | None:
    if value is None:
        return None
    try:
        return WorkerStateClass(str(value))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in WorkerStateClass)
        raise ValueError(
            f"unknown worker_state_class {value!r}; expected one of: {allowed}"
        ) from exc


def persistent_lifecycle_decision(manifest: "PluginManifest") -> LifecycleDecision:
    state_class = manifest.worker_state_class
    if state_class is None:
        return LifecycleDecision(
            allowed=False,
            mode=LifecycleMode.PERSISTENT_WORKER,
            state_class=None,
            reason="persistent execution requires explicit worker_state_class declaration",
        )
    if state_class == WorkerStateClass.NON_PERSISTENT:
        return LifecycleDecision(
            allowed=False,
            mode=LifecycleMode.PERSISTENT_WORKER,
            state_class=state_class,
            reason="NON_PERSISTENT family cannot use a persistent worker",
        )
    if state_class == WorkerStateClass.STATEFUL_EXPLICIT:
        return LifecycleDecision(
            allowed=False,
            mode=LifecycleMode.PERSISTENT_WORKER,
            state_class=state_class,
            reason=(
                "STATEFUL_EXPLICIT requires an explicit state-transfer protocol; "
                "v0.0.23 does not implement one"
            ),
        )
    return LifecycleDecision(
        allowed=True,
        mode=LifecycleMode.PERSISTENT_WORKER,
        state_class=state_class,
        reason=f"{state_class.value} is compatible with persistent reuse",
    )


def fresh_lifecycle_decision(manifest: "PluginManifest") -> LifecycleDecision:
    state_class = manifest.worker_state_class
    if state_class == WorkerStateClass.STATEFUL_EXPLICIT:
        return LifecycleDecision(
            allowed=False,
            mode=LifecycleMode.FRESH_PROCESS,
            state_class=state_class,
            reason=(
                "STATEFUL_EXPLICIT requires an explicit state-transfer protocol; "
                "fresh per-operation workers cannot preserve that semantic state"
            ),
        )
    return LifecycleDecision(
        allowed=True,
        mode=LifecycleMode.FRESH_PROCESS,
        state_class=state_class,
        reason=(
            "legacy undeclared manifest allowed only on fresh-process path"
            if state_class is None
            else f"{state_class.value} is compatible with fresh-process execution"
        ),
    )


def require_persistent_compatible(manifest: "PluginManifest") -> LifecycleDecision:
    decision = persistent_lifecycle_decision(manifest)
    if not decision.allowed:
        raise PermissionError(decision.reason)
    return decision


def require_fresh_compatible(manifest: "PluginManifest") -> LifecycleDecision:
    decision = fresh_lifecycle_decision(manifest)
    if not decision.allowed:
        raise PermissionError(decision.reason)
    return decision