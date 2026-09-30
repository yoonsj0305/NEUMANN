"""Run the first retained v0.0.82 audit. Never overwrite an existing archive."""
import argparse
import json
from pathlib import Path

from neumann1.lp_basis_headroom_v082 import run_audit, validate_archive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(
            "preserve the first audit; choose an explicit replication path"
        )
    report = run_audit(require_single_thread=True)
    validate_archive(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
