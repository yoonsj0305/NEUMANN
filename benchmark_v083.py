"""Explicit no-overwrite first audit; not an ordinary CI benchmark."""
import argparse
import json
from pathlib import Path
from neumann1.lp_discovery_v083 import run_audit

parser = argparse.ArgumentParser()
parser.add_argument("output", type=Path)
args = parser.parse_args()
if args.output.exists():
    parser.error("refusing to overwrite retained evidence")
report = run_audit()
with args.output.open("x") as stream:
    json.dump(report, stream, indent=2)
print(json.dumps(report["summary"].get("forms", report["summary"]), indent=2))
