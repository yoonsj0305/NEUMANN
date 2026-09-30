"""Preserve the first relational screen; no corpus download or model training."""
import argparse
import json
from pathlib import Path
from neumann1.relational_headroom_v080 import run_audit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("retain the first audit; use an explicit replication path")
    result = run_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))
