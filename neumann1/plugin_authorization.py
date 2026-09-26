from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .family_registry import FamilyAdapter, FamilyRegistry
from .plugin_manifest import ActivationPolicy, PluginActivator, PluginManifest
from .types import KindLike, kind_id


@dataclass(frozen=True)
class AuthorizationEvent:
    sequence: int
    action: str
    plugin_id: str
    manifest_digest_sha256: str | None
    reason: str = ""


@dataclass(frozen=True)
class AuthorizationState:
    plugin_id: str
    manifest_digest_sha256: str | None
    active: bool
    sequence: int


class PluginAuthorizationLedger:
    """In-memory authoritative approval/revocation ledger for plugin manifests.

    Approval is bound to the exact canonical manifest SHA-256. A changed manifest
    requires a new approval. Revocation takes effect on the next authorization check.
    Persistence/signatures are future work.
    """

    def __init__(self):
        self._events: list[AuthorizationEvent] = []
        self._current: dict[str, AuthorizationState] = {}
        self._sequence = 0

    def _append(self, action: str, plugin_id: str, digest: str | None, reason: str) -> AuthorizationEvent:
        self._sequence += 1
        event = AuthorizationEvent(
            sequence=self._sequence,
            action=action,
            plugin_id=plugin_id,
            manifest_digest_sha256=digest,
            reason=reason,
        )
        self._events.append(event)
        self._current[plugin_id] = AuthorizationState(
            plugin_id=plugin_id,
            manifest_digest_sha256=digest,
            active=(action == "APPROVE"),
            sequence=self._sequence,
        )
        return event

    def approve(self, manifest: PluginManifest, reason: str = "") -> AuthorizationEvent:
        manifest.validate()
        return self._append(
            "APPROVE", manifest.plugin_id, manifest.digest_sha256, reason
        )

    def revoke(self, plugin_id: str, reason: str = "") -> AuthorizationEvent:
        current = self._current.get(plugin_id)
        digest = current.manifest_digest_sha256 if current else None
        return self._append("REVOKE", plugin_id, digest, reason)

    def current(self, plugin_id: str) -> AuthorizationState | None:
        return self._current.get(plugin_id)

    def events(self) -> tuple[AuthorizationEvent, ...]:
        return tuple(self._events)

    def require_manifest(self, manifest: PluginManifest) -> None:
        self.require_binding(manifest.plugin_id, manifest.digest_sha256)

    def require_binding(self, plugin_id: str, manifest_digest_sha256: str) -> None:
        state = self._current.get(plugin_id)
        if state is None:
            raise PermissionError(f"plugin has no approval: {plugin_id}")
        if not state.active:
            raise PermissionError(f"plugin authorization revoked: {plugin_id}")
        if state.manifest_digest_sha256 != manifest_digest_sha256:
            raise PermissionError(
                f"approved manifest digest differs for {plugin_id}"
            )


@dataclass(frozen=True)
class PluginRuntimeBinding:
    manifest: PluginManifest
    adapter: FamilyAdapter

    @property
    def kind_id(self) -> str:
        return self.adapter.canonical_kind_id


class ManagedPluginRegistry:
    """Family-registry facade with use-time plugin authorization checks.

    Built-in/core families are delegated to the base registry. Managed external
    families are checked against the authorization ledger every time get() is called.
    """

    def __init__(
        self,
        base_registry: FamilyRegistry,
        ledger: PluginAuthorizationLedger,
    ):
        self.base_registry = base_registry
        self.ledger = ledger
        self._plugins_by_kind: dict[str, PluginRuntimeBinding] = {}
        self._plugins_by_family: dict[str, PluginRuntimeBinding] = {}

    def register_plugin(self, manifest: PluginManifest, adapter: FamilyAdapter) -> None:
        manifest.validate()
        self.ledger.require_manifest(manifest)
        if adapter.family_id != manifest.family_id:
            raise ValueError("plugin adapter family_id differs from manifest")
        if adapter.canonical_kind_id != kind_id(manifest.kind):
            raise ValueError("plugin adapter kind differs from manifest")
        if self.base_registry.get(adapter.ir_kind) is not None:
            raise ValueError("plugin kind collides with base registry")
        if adapter.canonical_kind_id in self._plugins_by_kind:
            raise ValueError(f"duplicate managed plugin kind: {adapter.canonical_kind_id}")
        if adapter.family_id in self._plugins_by_family:
            raise ValueError(f"duplicate managed plugin family: {adapter.family_id}")

        binding = PluginRuntimeBinding(manifest=manifest, adapter=adapter)
        self._plugins_by_kind[binding.kind_id] = binding
        self._plugins_by_family[adapter.family_id] = binding

    def get(self, kind: KindLike) -> FamilyAdapter | None:
        base = self.base_registry.get(kind)
        if base is not None:
            return base
        binding = self._plugins_by_kind.get(kind_id(kind))
        if binding is None:
            return None
        self.ledger.require_binding(
            binding.manifest.plugin_id,
            binding.manifest.digest_sha256,
        )
        return binding.adapter

    def kind_ids(self) -> tuple[str, ...]:
        return tuple(self.base_registry.kind_ids()) + tuple(self._plugins_by_kind)

    def bindings(self) -> tuple[PluginRuntimeBinding, ...]:
        return tuple(self._plugins_by_kind.values())


class AuthorizedPluginActivator:
    """Require exact manifest approval before any resolver/import is called."""

    def __init__(
        self,
        ledger: PluginAuthorizationLedger,
        resolver,
        policy: ActivationPolicy | None = None,
    ):
        self.ledger = ledger
        self.activator = PluginActivator(resolver, policy=policy)

    def activate(self, manifest: PluginManifest) -> FamilyAdapter:
        self.ledger.require_manifest(manifest)
        return self.activator.activate(manifest)