from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Iterable

from .family_registry import FAMILY_CONTRACT_VERSION, FamilyAdapter
from .types import kind_id
from .worker_lifecycle import WorkerStateClass, parse_worker_state_class


PLUGIN_MANIFEST_VERSION = "neumann.plugin.manifest.v1"
_PLUGIN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)+$")
_ENTRY_POINT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")

# Metadata declarations only. These are not a sandbox or permission enforcement layer.
KNOWN_CAPABILITIES = frozenset({
    "compile",
    "solve",
    "verify",
    "cpu",
    "network",
    "filesystem.read",
    "filesystem.write",
    "subprocess",
})


@dataclass(frozen=True)
class PluginManifest:
    manifest_version: str
    plugin_id: str
    plugin_version: str
    family_id: str
    kind: str
    family_contract_version: str
    entry_point: str
    capabilities: tuple[str, ...] = ()
    worker_state_class: WorkerStateClass | None = None
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginManifest":
        required = {
            "manifest_version",
            "plugin_id",
            "plugin_version",
            "family_id",
            "kind",
            "family_contract_version",
            "entry_point",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"missing manifest fields: {', '.join(missing)}")

        manifest = cls(
            manifest_version=str(data["manifest_version"]),
            plugin_id=str(data["plugin_id"]),
            plugin_version=str(data["plugin_version"]),
            family_id=str(data["family_id"]),
            kind=str(data["kind"]),
            family_contract_version=str(data["family_contract_version"]),
            entry_point=str(data["entry_point"]),
            capabilities=tuple(str(x) for x in data.get("capabilities", ())),
            worker_state_class=parse_worker_state_class(data.get("worker_state_class")),
            description=str(data.get("description", "")),
        )
        manifest.validate()
        return manifest

    @classmethod
    def from_json(cls, text: str) -> "PluginManifest":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid plugin manifest JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("plugin manifest JSON must contain an object")
        return cls.from_dict(data)

    def validate(self) -> None:
        if self.manifest_version != PLUGIN_MANIFEST_VERSION:
            raise ValueError(
                f"unsupported manifest version {self.manifest_version!r}; "
                f"expected {PLUGIN_MANIFEST_VERSION!r}"
            )
        if self.family_contract_version != FAMILY_CONTRACT_VERSION:
            raise ValueError(
                f"unsupported family contract {self.family_contract_version!r}; "
                f"expected {FAMILY_CONTRACT_VERSION!r}"
            )
        if not _PLUGIN_ID_RE.fullmatch(self.plugin_id):
            raise ValueError("plugin_id must be a lowercase namespaced identifier")
        if not _PLUGIN_ID_RE.fullmatch(self.family_id):
            raise ValueError("family_id must be a lowercase namespaced identifier")
        if not self.plugin_version or any(ch.isspace() for ch in self.plugin_version):
            raise ValueError("plugin_version must be a nonempty whitespace-free string")
        # kind_id performs namespace and reserved-core checks for external strings.
        kind_id(self.kind)
        if not _ENTRY_POINT_RE.fullmatch(self.entry_point):
            raise ValueError("entry_point must use 'module.path:factory' syntax")
        unknown_caps = sorted(set(self.capabilities) - KNOWN_CAPABILITIES)
        if unknown_caps:
            raise ValueError(f"unknown declared capabilities: {unknown_caps}")
        if "compile" not in self.capabilities or "solve" not in self.capabilities or "verify" not in self.capabilities:
            raise ValueError("family plugins must declare compile, solve, and verify capabilities")

    def canonical_dict(self) -> dict[str, Any]:
        data = {
            "manifest_version": self.manifest_version,
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "family_id": self.family_id,
            "kind": self.kind,
            "family_contract_version": self.family_contract_version,
            "entry_point": self.entry_point,
            "capabilities": list(self.capabilities),
            "description": self.description,
        }
        if self.worker_state_class is not None:
            data["worker_state_class"] = self.worker_state_class.value
        return data

    @property
    def digest_sha256(self) -> str:
        payload = json.dumps(
            self.canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class PluginCatalog:
    """Static manifest catalog. Registration never imports or executes plugin code."""

    def __init__(self, manifests: Iterable[PluginManifest] = ()):
        self._by_plugin_id: dict[str, PluginManifest] = {}
        self._by_family_id: dict[str, PluginManifest] = {}
        self._by_kind: dict[str, PluginManifest] = {}
        for manifest in manifests:
            self.register(manifest)

    def register(self, manifest: PluginManifest) -> None:
        manifest.validate()
        canonical_kind = kind_id(manifest.kind)
        if manifest.plugin_id in self._by_plugin_id:
            raise ValueError(f"duplicate plugin_id: {manifest.plugin_id}")
        if manifest.family_id in self._by_family_id:
            raise ValueError(f"duplicate family_id: {manifest.family_id}")
        if canonical_kind in self._by_kind:
            raise ValueError(f"duplicate plugin kind: {canonical_kind}")

        self._by_plugin_id[manifest.plugin_id] = manifest
        self._by_family_id[manifest.family_id] = manifest
        self._by_kind[canonical_kind] = manifest

    def manifests(self) -> tuple[PluginManifest, ...]:
        return tuple(self._by_plugin_id.values())

    def get(self, plugin_id: str) -> PluginManifest | None:
        return self._by_plugin_id.get(plugin_id)

    def get_by_kind(self, kind: str) -> PluginManifest | None:
        return self._by_kind.get(kind_id(kind))


@dataclass(frozen=True)
class ActivationPolicy:
    """Metadata-only activation policy.

    This can refuse activation before import. It does NOT sandbox code after import.
    """

    denied_capabilities: frozenset[str] = frozenset({"network", "filesystem.write", "subprocess"})
    allowed_plugin_ids: frozenset[str] | None = None

    def check(self, manifest: PluginManifest) -> None:
        if self.allowed_plugin_ids is not None and manifest.plugin_id not in self.allowed_plugin_ids:
            raise PermissionError(f"plugin not on allowlist: {manifest.plugin_id}")
        denied = sorted(set(manifest.capabilities) & set(self.denied_capabilities))
        if denied:
            raise PermissionError(f"plugin declares denied capabilities: {denied}")


class PluginActivator:
    """Explicitly turn a validated manifest into a FamilyAdapter.

    resolver(entry_point) is injected so discovery/catalog operations remain code-free.
    """

    def __init__(self, resolver, policy: ActivationPolicy | None = None):
        self.resolver = resolver
        self.policy = policy or ActivationPolicy()

    def activate(self, manifest: PluginManifest) -> FamilyAdapter:
        manifest.validate()
        self.policy.check(manifest)

        factory = self.resolver(manifest.entry_point)
        if not callable(factory):
            raise TypeError("resolved plugin entry point must be callable")
        adapter = factory()
        if not isinstance(adapter, FamilyAdapter):
            raise TypeError("plugin factory must return FamilyAdapter")

        if adapter.family_id != manifest.family_id:
            raise ValueError("plugin adapter family_id differs from manifest")
        if adapter.canonical_kind_id != kind_id(manifest.kind):
            raise ValueError("plugin adapter kind differs from manifest")
        if adapter.contract_version != manifest.family_contract_version:
            raise ValueError("plugin adapter contract version differs from manifest")
        return adapter
