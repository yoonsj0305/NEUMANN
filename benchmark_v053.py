"""First preregistered full-path interleaved exact-component reuse audit."""

import argparse
import json
import platform
from pathlib import Path

import numpy
import scipy

from neumann1.numeric_order_v052 import MATRICES, load_pinned
from neumann1.repeated_matrix_v053 import BASES, COPIES, audit_case, summarize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = [audit_case(load_pinned(args.data_root / f"{name}.mtx.gz", name), name, copies)
             for name in BASES for copies in COPIES]
    slopes = {name: {policy: float(numpy.polyfit(numpy.log(COPIES),
                       numpy.log([case["median_total_ns"][policy] for case in cases
                                  if case["name"] == name]), 1)[0])
                     for policy in ("NATURAL", "COLAMD", "REUSE")}
              for name in BASES}
    result = {"protocol": "v0.0.53 first audit; seven balanced repetitions and one warmup",
              "versions": {"python": platform.python_version(), "numpy": numpy.__version__,
                           "scipy": scipy.__version__, "platform": platform.platform()},
              "sources": {name: MATRICES[name][1] for name in BASES},
              "cases": cases, "descriptive_log_log_slopes": slopes,
              "summary": summarize(cases)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"],
                      "median_ns": {f'{c["name"]}:{c["copies"]}': c["median_total_ns"]
                                    for c in cases}}, indent=2))


if __name__ == "__main__":
    main()
