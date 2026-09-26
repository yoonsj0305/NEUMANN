from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import tempfile

from neumann1.plugin_discovery import (
    catalog_from_discovery,
    discover_installed_manifests,
)
from neumann1.plugin_manifest import PLUGIN_MANIFEST_VERSION


class FakeDistribution:
    def __init__(self, root):
        self.root = Path(root)
        self.metadata = {"Name": "benchmark-external-plugin"}
        self.version = "0.1.0"
        self.files = []

    def add(self, relative, text):
        rel = PurePosixPath(relative)
        path = self.root / str(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.files.append(rel)

    def locate_file(self, file_ref):
        return self.root / str(file_ref)


def run():
    manifest = {
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.scalar_sum_plugin",
        "plugin_version": "0.1.0",
        "family_id": "benchmark.scalar_sum",
        "kind": "benchmark.scalar_sum",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "benchmark_plugin:factory",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    }

    with tempfile.TemporaryDirectory() as tmp:
        dist = FakeDistribution(tmp)
        dist.add(
            "sitepkg/neumann_plugins/scalar_sum.json",
            json.dumps(manifest),
        )
        dist.add(
            "sitepkg/benchmark_plugin.py",
            "raise RuntimeError('discovery must not import this module')",
        )

        report = discover_installed_manifests([dist])
        catalog = catalog_from_discovery(report)

        item = report.manifests[0]
        return {
            "discovered_count": report.discovered_count,
            "issue_count": report.issue_count,
            "distribution_name": item.distribution_name,
            "distribution_version": item.distribution_version,
            "relative_manifest_path": item.relative_path,
            "plugin_id": item.manifest.plugin_id,
            "manifest_digest_sha256": item.manifest_digest_sha256,
            "catalog_count": len(catalog.manifests()),
            "plugin_module_imported_by_discovery": False,
            "boundary": (
                "The benchmark uses an injected fake distribution to prove the "
                "discovery code path reads static package files without plugin import. "
                "It does not yet prove interoperability with independently published packages."
            ),
        }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
    with open("benchmark_v014_results.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
