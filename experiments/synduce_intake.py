"""Archive a pinned public upstream implementation. No benchmark is executed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import urllib.parse
import zipfile

COMMIT = "b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89"


def intake(destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    url = f"https://codeload.github.com/synduce/Synduce/zip/{COMMIT}"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024:
        raise ValueError("upstream archive budget exceeded")
    archive = destination / "upstream.zip"
    archive.write_bytes(data)
    source = (destination / "upstream").resolve()
    source.mkdir()
    rows = []
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        if sum(item.file_size for item in members) > 256 * 1024 * 1024:
            raise ValueError("expanded archive budget exceeded")
        prefix = f"Synduce-{COMMIT}/"
        for item in members:
            if not item.filename.startswith(prefix):
                raise ValueError("unexpected archive root")
            relative = item.filename[len(prefix):]
            if not relative or item.is_dir():
                continue
            if "\\" in relative:
                raise ValueError("unsafe archive name")
            # Git permits colon names that Windows interprets as alternate streams.
            # Preserve exact bytes in ZIP and reversible percent-encoded local names.
            local_name = "/".join(urllib.parse.quote(part, safe="._- ") for part in relative.split("/"))
            path = (source / local_name).resolve()
            if not path.is_relative_to(source):
                raise ValueError("archive escapes destination")
            payload = bundle.read(item)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            rows.append({"path": relative, "local_path": local_name, "bytes": len(payload),
                         "sha256": hashlib.sha256(payload).hexdigest()})
    if "MIT License" not in (source / "LICENSE").read_text(encoding="utf-8"):
        raise ValueError("license changed")
    report = {"repository": "https://github.com/synduce/Synduce", "commit": COMMIT,
              "archive_url": url, "archive_sha256": hashlib.sha256(data).hexdigest(),
              "license": "MIT", "files": rows, "source_role": "OPENED_DEVELOPMENT",
              "fresh_eligible": 0, "benchmarks_executed": False, "training_admitted": False}
    (destination / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {"commit": COMMIT, "files": len(rows), "bytes": len(data),
            "benchmark_sources": sum(r["path"].startswith("benchmarks/") and
                                     r["path"].endswith((".ml", ".pmrs")) for r in rows)}


if __name__ == "__main__":
    print(json.dumps(intake(Path(sys.argv[1]))))
