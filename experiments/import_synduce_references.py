"""Fetch a pinned, licensed public reference subset; no benchmark is executed."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

COMMIT = "b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89"
FILES = ["LICENSE", "README.md", "benchmarks/list/mps.ml", "benchmarks/list/mts.ml",
         "benchmarks/list/mss.ml", "benchmarks/list/sum.ml", "benchmarks/list/ConsList.ml",
         "benchmarks/list/ConcatList.ml"]


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in FILES:
        url = f"https://raw.githubusercontent.com/synduce/Synduce/{COMMIT}/{name}"
        with urllib.request.urlopen(url, timeout=20) as response:
            data = response.read(2*1024*1024+1)
        assert len(data) <= 2*1024*1024
        path = output/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append({"path": name, "url": url, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    assert "MIT License" in (output/"LICENSE").read_text(encoding="utf-8")
    report = {"repository": "https://github.com/synduce/Synduce", "commit": COMMIT, "license": "MIT",
              "files": rows, "source_role": "opened_development", "fresh_eligible": 0,
              "full_Synduce_installed_or_run": False, "performance_measured": False,
              "scope": "original public reference functions and source dependencies; no original executable or numerical benchmark claim"}
    (output/"manifest.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"commit": COMMIT, "files": len(rows), "license": "MIT"}))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
