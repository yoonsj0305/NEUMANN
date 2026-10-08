"""Read-only historical inventory/schema inspection. No solver/model execution."""
from pathlib import Path
import gzip
import json
import re
import subprocess

repo = Path(__file__).resolve().parents[2]
workspace = repo.parents[1]
files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo, text=True).splitlines()
versions = sorted((p for p in files if re.fullmatch(r"docs/experiments/v0\.0\.\d+(?:\.\d+)?\.md", p)),
                  key=lambda p: tuple(map(int, re.search(r"v0\.0\.(\d+(?:\.\d+)?)", p)[1].split("."))))
print("VERSION_DOCS", len(versions), [Path(p).stem for p in versions])
print("NOTION_NEUMANN", [p.name for p in (workspace / "Notion/pages").glob("*.md")
                         if "NEUMANN" in p.name.upper() or re.search(r"v0\.[1-5](?:\.|\s|_)", p.name)])

def shape(value, depth=0):
    if isinstance(value, dict):
        return {str(k): shape(v, depth + 1) if depth < 2 else
                {"type": type(v).__name__, "len": len(v) if hasattr(v, "__len__") else None}
                for k, v in value.items()}
    if isinstance(value, list):
        return {"list_length": len(value), "first": shape(value[0], depth + 1) if value and depth < 2 else None}
    return value

schemas = {}
targets = [
    "docs/experiments/results/v102_first_evaluation.json.gz",
    "docs/experiments/results/v101_first_expansion.json.gz",
    "docs/experiments/results/v100_first_refit.json.gz",
    "docs/experiments/results/q5_first_evaluation/report.json",
    "docs/experiments/results/q5_first_evaluation/observation_0000.json.gz",
    "docs/experiments/results/q5_first_sources/q5_m64_w16_r0_base.json.gz",
    "docs/experiments/results/m106_bp_transfer_first/report.json",
    "docs/experiments/results/m106_bp_transfer_first/observation_0000.json.gz",
    "docs/experiments/results/m106_bp_transfer_first/m106_bp_k8_r0.json.gz",
    "docs/experiments/results/v104_transfer_admission_first/report.json",
]
for name in targets:
    path = repo / name
    if not path.is_file():
        schemas[name] = {"missing": True}
        continue
    raw = gzip.decompress(path.read_bytes()) if name.endswith(".gz") else path.read_bytes()
    obj = json.loads(raw)
    schemas[name] = shape(obj)
    print("SCHEMA", name, json.dumps(schemas[name], ensure_ascii=False)[:9000])
with (repo / "research/audit/SCHEMA_INSPECTION.json").open("x", encoding="utf-8") as sink:
    json.dump(schemas, sink, indent=2, ensure_ascii=False)
