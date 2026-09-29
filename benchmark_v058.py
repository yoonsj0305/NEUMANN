"""Nonblind MIPLIB 2017 workload triage against existing presolve.

Official raw feature tables summarize *trivial* SCIP-based preprocessing;
the optional HiGHS probe is a separate, stronger native-presolve observation.
Neither proves residual reducibility or a full-path speed advantage.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from hashlib import sha256
from pathlib import Path
from statistics import median
from zipfile import ZipFile


RAW_HASH = "0f6220fd54212062bad551bf0bae754a412e23a176c12baf9b0a7d916d29f4dc"
BENCHMARK_HASH = "cbd74ea7d59ff8f2f0214d110aeb9002dcef53fd13dce30526d62a95714f51d2"
BEASLEY_HASH = "37350bc46bdb84a6373e9044eb3d0d65202427fe2bcba64ed282f894699d75dd"


def _checked(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected:
        raise ValueError(f"source hash mismatch: {path}")
    return raw


def _features(archive: ZipFile, name: str) -> dict[str, dict[str, str]]:
    with archive.open(f"data_download/{name}.csv") as stream:
        rows = list(csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8")))
    by_name = {r["instance_name"].split("/")[-1].removesuffix(".mps.gz"): r
               for r in rows}
    if len(by_name) != len(rows):
        raise ValueError("ambiguous instance basename in raw features")
    return by_name


def _count(row: dict[str, str], field: str) -> int:
    # Official CSV stores some large integer counts in rounded scientific
    # notation. Never use these rounded counts as exact solution evidence.
    value = float(row[field])
    if not value.is_integer() or value < 0:
        raise ValueError(f"invalid count in {field}")
    return int(value)


def screen(raw_zip: Path, benchmark_html: Path) -> dict:
    html = _checked(benchmark_html, BENCHMARK_HASH).decode("utf-8")
    names = re.findall(r'<a href="instance_details_[^"<>]+\.html">([^<]+)</a>', html)
    if len(names) != 240 or len(set(names)) != 240:
        raise ValueError("expected 240 distinct official benchmark names")
    with ZipFile(io.BytesIO(_checked(raw_zip, RAW_HASH))) as archive:
        original = _features(archive, "features_original")
        trivial = _features(archive, "features_after_trivial_presolving")
    if set(original) != set(trivial) or len(original) != 5718:
        raise ValueError("unmatched official raw feature rows")
    cases = []
    for name in names:
        before, after = original[name], trivial[name]
        vars_before, vars_after = _count(before, "vars"), _count(after, "vars")
        if vars_before <= 0 or vars_after > vars_before:
            raise ValueError("unexpected trivial presolve counts")
        cases.append({"name": name, "variables_original": vars_before,
                      "variables_after_trivial": vars_after,
                      "constraints_original": _count(before, "constr"),
                      "aggregation_rows_original": _count(before, "linaggr_constr"),
                      "fraction_removed_trivial": (vars_before - vars_after) / vars_before})
    # Metadata-only shortlist. The thresholds identify inspectable examples,
    # not predicted wins. In particular, aggregates may already be captured
    # by the native presolver, as the separate beasleyC3 probe demonstrates.
    candidates = [c["name"] for c in cases
                  if 1000 <= c["variables_original"] <= 10000
                  and c["constraints_original"] <= 10000
                  and c["aggregation_rows_original"] >= 100
                  and c["fraction_removed_trivial"] <= 0.10]
    fractions = [c["fraction_removed_trivial"] for c in cases]
    return {"source": "MIPLIB 2017 official raw feature archive and benchmark-set page",
            "raw_archive_sha256": RAW_HASH, "benchmark_page_sha256": BENCHMARK_HASH,
            "raw_feature_rows": len(original), "cases": cases,
            "summary": {"benchmark_cases": len(cases),
                        "unchanged_by_trivial": sum(f == 0 for f in fractions),
                        "at_least_50pct_removed_trivial": sum(f >= 0.5 for f in fractions),
                        "median_fraction_removed_trivial": median(fractions),
                        "metadata_shortlist": candidates}}


def native_probe(path: Path) -> dict:
    _checked(path, BEASLEY_HASH)
    import highspy  # Optional audit tool, deliberately not a runtime dependency.

    solver = highspy.Highs()
    solver.setOptionValue("output_flag", False)
    if solver.readModel(str(path)) != highspy.HighsStatus.kOk:
        raise ValueError("HiGHS could not read original MPS")
    original = {"variables": solver.getNumCol(), "constraints": solver.getNumRow(),
                "nonzeros": solver.getNumNz()}
    if original != {"variables": 2500, "constraints": 1750, "nonzeros": 5000}:
        raise ValueError("unexpected original beasleyC3 shape")
    if solver.presolve() != highspy.HighsStatus.kOk:
        raise ValueError("native presolve failed")
    reduced = solver.getPresolvedLp()
    return {"instance": "beasleyC3", "source_sha256": BEASLEY_HASH,
            "highs_version": solver.version(), "original": original,
            "after_native_presolve": {"variables": reduced.num_col_,
                                      "constraints": reduced.num_row_,
                                      "nonzeros": len(reduced.a_matrix_.value_)},
            "scope": "presolve shape only; no solution, postsolve, runtime or residual win"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-zip", type=Path, required=True)
    parser.add_argument("--benchmark-html", type=Path, required=True)
    parser.add_argument("--beasley-mps", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = screen(args.raw_zip, args.benchmark_html)
    if args.beasley_mps:
        result["native_probe"] = native_probe(args.beasley_mps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"],
                      "native_probe": result.get("native_probe")}, indent=2))
