"""Run the single preregistered NIST numerical matrix audit."""

import argparse
import json
import platform
from pathlib import Path

import numpy
import scipy

from neumann1.numeric_order_v052 import MATRICES, audit_matrix, load_pinned, summarize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = [audit_matrix(load_pinned(args.data_root / f"{name}.mtx.gz", name), name)
             for name in MATRICES]
    result = {
        "protocol": "v0.0.52 first audit: seven balanced repetitions, one discarded warmup",
        "versions": {"python": platform.python_version(), "numpy": numpy.__version__,
                     "scipy": scipy.__version__, "platform": platform.platform()},
        "sources": {name: {"url": f"https://math.nist.gov/pub/MatrixMarket2/Harwell-Boeing/bcsstruc1/{name}.mtx.gz",
                           "sha256": spec[1]} for name, spec in MATRICES.items()},
        "cases": cases, "summary": summarize(cases),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"],
                      "medians_ns": {c["name"]: c["median_total_ns"] for c in cases}}, indent=2))


if __name__ == "__main__":
    main()
