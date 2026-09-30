"""Explicit opened-data audit; no external download and no model training."""
import argparse
import json
from pathlib import Path
from neumann1.natural_arithmetic_v078 import run_audit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("retain the existing audit; choose an explicit replication path")
    result = run_audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result["summary"], indent=2))
