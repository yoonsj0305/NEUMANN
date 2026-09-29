"""Run the openly corrective all-13 original-matrix numerical audit."""

import argparse
import json
import platform
from pathlib import Path

import numpy
import scipy

from neumann1.natural_reuse_v055 import (MATRICES, cross_file_exact_groups,
                                         load_pinned, summarize)
from neumann1.natural_reuse_v056 import audit_case


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    matrices = {name: load_pinned(args.data_root / f"{name}.mtx.gz", name)
                for name in MATRICES}
    cases = [audit_case(matrices[name], name) for name in MATRICES]
    groups = cross_file_exact_groups(matrices)
    result = {
        "protocol": "v0.0.56 corrective audit after v0.0.55 invalid warmup; not a blind corpus",
        "versions": {"python": platform.python_version(), "numpy": numpy.__version__,
                     "scipy": scipy.__version__, "platform": platform.platform()},
        "sources": {name: {"url": f"https://math.nist.gov/pub/MatrixMarket2/Harwell-Boeing/bcsstruc1/{name}.mtx.gz",
                           "sha256": spec[1]} for name, spec in MATRICES.items()},
        "cases": cases, "cross_file_exact_groups_descriptive": groups,
        "summary": summarize(cases),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"],
                      "components": {c["name"]: [c["components"], c["distinct_blocks"]] for c in cases},
                      "cross_file_exact_groups": [g for g in groups if len(g)>1]}, indent=2))


if __name__ == "__main__":
    main()
