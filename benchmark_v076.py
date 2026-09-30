"""v0.0.76 frozen Q4 task-admissibility audit."""

import argparse
import json
import platform
from pathlib import Path

from neumann1.q4_admissibility_v076 import run_audit


def run():
    result = run_audit()
    result["environment"] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = run()
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)

    print(json.dumps(result["summary"], indent=2))
