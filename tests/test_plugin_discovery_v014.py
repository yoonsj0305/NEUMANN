import json
from pathlib import PurePosixPath

import pytest

from neumann1.plugin_discovery import (
    MAX_MANIFEST_BYTES,
    catalog_from_discovery,
    discover_installed_manifests,
)
from neumann1.plugin_manifest import PLUGIN_MANIFEST_VERSION


def manifest_dict(plugin_id="example.sum_plugin", family_id="example.sum", kind="example.sum"):
    return {
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": plugin_id,
        "plugin_version": "0.1.0",
        "family_id": family_id,
        "kind": kind,
        "family_contract_version": "neumann.family.v1",
        "entry_point": "example_plugin:factory",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    }


class FakeDistribution:
    def __init__(self, root, name="example-dist", version="1.2.3"):
        self.root = root
        self.metadata = {"Name": name}
        self.version = version
        self.files = []

    def add_file(self, relative_path, content):
        rel = PurePosixPath(relative_path)
        path = self.root / str(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        self.files.append(rel)

    def locate_file(self, file_ref):
        return self.root / str(file_ref)


def test_static_distribution_manifest_is_discovered_without_import(tmp_path):
    dist = FakeDistribution(tmp_path)
    dist.add_file(
        "package/neumann_plugins/sum.json",
        json.dumps(manifest_dict()),
    )
    dist.add_file("package/__init__.py", "raise RuntimeError('must not import')")

    report = discover_installed_manifests([dist])

    assert report.discovered_count == 1
    assert report.issue_count == 0
    item = report.manifests[0]
    assert item.distribution_name == "example-dist"
    assert item.distribution_version == "1.2.3"
    assert item.manifest.plugin_id == "example.sum_plugin"
    assert len(item.manifest_digest_sha256) == 64


def test_malformed_and_oversized_manifests_become_issues_not_code_execution(tmp_path):
    malformed = FakeDistribution(tmp_path / "bad", name="bad-dist")
    malformed.add_file("neumann_plugins/bad.json", "{not json")

    oversized = FakeDistribution(tmp_path / "huge", name="huge-dist")
    oversized.add_file(
        "neumann_plugins/huge.json",
        b"x" * (MAX_MANIFEST_BYTES + 1),
    )

    report = discover_installed_manifests([malformed, oversized])

    assert report.discovered_count == 0
    assert report.issue_count == 2
    reasons = " | ".join(issue.reason for issue in report.issues)
    assert "invalid plugin manifest JSON" in reasons
    assert "byte limit" in reasons


def test_non_manifest_files_are_ignored(tmp_path):
    dist = FakeDistribution(tmp_path)
    dist.add_file("package/config.json", json.dumps(manifest_dict()))
    dist.add_file("package/neumann_plugins/readme.txt", "not a manifest")

    report = discover_installed_manifests([dist])
    assert report.discovered_count == 0
    assert report.issue_count == 0


def test_discovered_manifests_can_build_catalog(tmp_path):
    dist = FakeDistribution(tmp_path)
    dist.add_file(
        "neumann_plugins/plugin.json",
        json.dumps(manifest_dict()),
    )
    report = discover_installed_manifests([dist])
    catalog = catalog_from_discovery(report)

    assert catalog.get("example.sum_plugin") is not None


def test_duplicate_discovered_kinds_are_not_silently_resolved(tmp_path):
    a = FakeDistribution(tmp_path / "a", name="dist-a")
    b = FakeDistribution(tmp_path / "b", name="dist-b")
    a.add_file(
        "neumann_plugins/a.json",
        json.dumps(manifest_dict("vendor.a", "vendor.family_a", "vendor.shared")),
    )
    b.add_file(
        "neumann_plugins/b.json",
        json.dumps(manifest_dict("vendor.b", "vendor.family_b", "vendor.shared")),
    )

    report = discover_installed_manifests([a, b])
    assert report.discovered_count == 2
    with pytest.raises(ValueError):
        catalog_from_discovery(report)
