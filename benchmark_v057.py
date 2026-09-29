"""Descriptive, nonblind graph screen on the previously inspected corpus."""

import argparse
import json
from pathlib import Path

from neumann1.leaf_opportunity_v057 import peel_upper_bound
from neumann1.natural_reuse_v055 import MATRICES, load_pinned


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = []
    for name in MATRICES:
        matrix = load_pinned(args.data_root / f"{name}.mtx.gz", name)
        cases.append({"name": name, "sha256": MATRICES[name][1],
                      **peel_upper_bound(matrix)})
    result = {"protocol": "v0.0.57 descriptive screen; corpus inspected before writing this script",
              "scope": "structural degree <=1 peeling only; no numeric solver or speedup claim",
              "cases": cases,
              "summary": {"total": len(cases),
                          "max_fraction_upper_bound": max(c["fraction_upper_bound"] for c in cases),
                          "cases_with_10pct_structural_headroom": sum(
                              c["fraction_upper_bound"] >= 0.10 for c in cases)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
