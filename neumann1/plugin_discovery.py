from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Iterable, Any

from .plugin_manifest import PluginManifest, PluginCatalog


MANIFEST_DIRECTORY = "neumann_plugins"
MAX_MANIFEST_BYTES = 64 * 1024


@dataclass(frozen=True)
class DiscoveredManifest:
    distribution_name: str
    distribution_version: str
    relative_path: str
    manifest: PluginManifest

    @property
    def manifest_digest_sha256(self) -> str:
        return self.manifest.digest_sha256


@dataclass(frozen=True)
class DiscoveryIssue:
    distribution_name: str
    relative_path: str
    reason: str


@dataclass(frozen=True)
class DiscoveryReport:
    manifests: tuple[DiscoveredManifest, ...]
    issues: tuple[DiscoveryIssue, ...]

    @property
    def discovered_count(self) -> int:
        return len(self.manifests)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


def _distribution_identity(dist: Any) -> tuple[str, str]:
    metadata = getattr(dist, "metadata", None)
    name = None
    if metadata is not None:
        try:
            name = metadata.get("Name")
        except Exception:
            name = None
    name = str(name or "<unknown-distribution>")
    version = str(getattr(dist, "version", "") or "<unknown-version>")
    return name, version


def _is_manifest_path(path_text: str) -> bool:
    normalized = path_text.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    return (
        MANIFEST_DIRECTORY in parts
        and bool(parts)
        and parts[-1].lower().endswith(".json")
    )


def discover_installed_manifests(
    distributions: Iterable[Any] | None = None,
    *,
    max_manifest_bytes: int = MAX_MANIFEST_BYTES,
) -> DiscoveryReport:
    """Discover static manifest files from installed distribution metadata.

    This function reads files listed by importlib.metadata. It never resolves or
    loads a plugin entry point and never imports the plugin module.
    """
    if max_manifest_bytes <= 0:
        raise ValueError("max_manifest_bytes must be positive")

    dists = (
        list(importlib_metadata.distributions())
        if distributions is None
        else list(distributions)
    )

    found: list[DiscoveredManifest] = []
    issues: list[DiscoveryIssue] = []

    for dist in dists:
        dist_name, dist_version = _distribution_identity(dist)
        files = getattr(dist, "files", None) or ()

        for file_ref in files:
            rel = str(file_ref)
            if not _is_manifest_path(rel):
                continue

            try:
                located = Path(dist.locate_file(file_ref))
                data = located.read_bytes()
                if len(data) > max_manifest_bytes:
                    raise ValueError(
                        f"manifest exceeds {max_manifest_bytes} byte limit"
                    )
                text = data.decode("utf-8")
                manifest = PluginManifest.from_json(text)
            except Exception as exc:
                issues.append(
                    DiscoveryIssue(
                        distribution_name=dist_name,
                        relative_path=rel,
                        reason=str(exc),
                    )
                )
                continue

            found.append(
                DiscoveredManifest(
                    distribution_name=dist_name,
                    distribution_version=dist_version,
                    relative_path=rel,
                    manifest=manifest,
                )
            )

    return DiscoveryReport(tuple(found), tuple(issues))


def catalog_from_discovery(report: DiscoveryReport) -> PluginCatalog:
    """Build a static catalog from already discovered manifests.

    Duplicate IDs/kinds remain hard failures because ambiguity should not be
    silently resolved by discovery order.
    """
    return PluginCatalog(item.manifest for item in report.manifests)
