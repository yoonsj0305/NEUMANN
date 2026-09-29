"""First preregistered decomposition-versus-reuse mechanism audit."""

import argparse
import json
import platform
from pathlib import Path

import numpy
import scipy

from neumann1.numeric_order_v052 import MATRICES, load_pinned
from neumann1.repeated_matrix_v053 import BASES, COPIES
from neumann1.reuse_ablation_v054 import audit_case, summarize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = [audit_case(load_pinned(args.data_root / f"{name}.mtx.gz", name), name, k)
             for name in BASES for k in COPIES]
    result = {"protocol": "v0.0.54 first audit; one warmup, seven balanced repetitions",
              "versions": {"python": platform.python_version(), "numpy": numpy.__version__,
                           "scipy": scipy.__version__, "platform": platform.platform()},
              "sources": {name: MATRICES[name][1] for name in BASES},
              "cases": cases, "summary": summarize(cases)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"],
                      "median_ns": {f'{c["name"]}:{c["copies"]}': c["median_total_ns"]
                                    for c in cases}}, indent=2))


if __name__ == "__main__":
    main()
