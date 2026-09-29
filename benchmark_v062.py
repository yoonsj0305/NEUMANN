"""Descriptive residual-structure screen after native MIP presolve.

This is a nonblind opportunity screen, not a transformation or speed test.
The original MPS files are supplied locally and never redistributed here.
"""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import highspy
import numpy as np
from scipy.sparse import bmat, csc_matrix, csgraph


SOURCES = {
    "beasleyC3": "37350bc46bdb84a6373e9044eb3d0d65202427fe2bcba64ed282f894699d75dd",
    "n5-3": "48efedf21c4057851a4ef7efc79fbbcbd292b68ee5f6b6a16e904d11ab11bacc",
    "binkar10_1": "94282c38edd6c83bb6c2d788d823fd82f218218e8e07c98d1d1ab42c1e91039e",
}


def shape(lp):
    return {"variables": lp.num_col_, "constraints": lp.num_row_,
            "nonzeros": len(lp.a_matrix_.value_)}


def motifs(lp):
    matrix = lp.a_matrix_
    if matrix.format_ != highspy.MatrixFormat.kColwise:
        raise ValueError("column-wise matrix required")
    a = csc_matrix((matrix.value_, matrix.index_, matrix.start_),
                   shape=(lp.num_row_, lp.num_col_))
    a.eliminate_zeros()
    degree = np.diff(a.indptr)
    continuous = np.array([kind == highspy.HighsVarType.kContinuous
                           for kind in lp.integrality_], dtype=bool)
    if len(continuous) != lp.num_col_:
        raise ValueError("missing integrality declarations")
    leaf = (degree == 1) & continuous
    rows = a.tocsr()
    equality_leaf_rows = sum(
        lp.row_lower_[i] == lp.row_upper_[i]
        and abs(lp.row_lower_[i]) < 1e20
        and bool(np.any(leaf[rows.indices[rows.indptr[i]:rows.indptr[i + 1]]]))
        for i in range(lp.num_row_))

    graph = bmat([[None, a], [a.T, None]], format="csr")
    n_components, labels = csgraph.connected_components(graph, directed=False)
    components = []
    for k in range(n_components):
        row_ids = np.flatnonzero(labels[:lp.num_row_] == k)
        col_ids = np.flatnonzero(labels[lp.num_row_:] == k)
        components.append({"rows": len(row_ids), "columns": len(col_ids),
                           "integer_columns": sum(lp.integrality_[int(j)] !=
                                                  highspy.HighsVarType.kContinuous
                                                  for j in col_ids),
                           "nonzeros": a[row_ids][:, col_ids].nnz})
    components.sort(key=lambda c: (-c["columns"], -c["rows"]))

    signatures = []
    for j in range(lp.num_col_):
        start, end = matrix.start_[j:j + 2]
        signatures.append((tuple(matrix.index_[start:end]),
                           tuple(matrix.value_[start:end]), lp.col_cost_[j],
                           lp.col_lower_[j], lp.col_upper_[j], str(lp.integrality_[j])))
    sizes = Counter(signatures)
    return {"shape": shape(lp), "degree_one_continuous_columns": int(leaf.sum()),
            "equality_rows_with_degree_one_continuous_column": int(equality_leaf_rows),
            "exact_identical_column_excess": sum(size - 1 for size in sizes.values()),
            "components": components}


def screen(paths):
    cases = []
    for name in SOURCES:
        path = paths[name]
        digest = sha256(path.read_bytes()).hexdigest()
        if digest != SOURCES[name]:
            raise ValueError(f"source hash mismatch for {name}")
        solver = highspy.Highs()
        solver.setOptionValue("output_flag", False)
        solver.setOptionValue("threads", 1)
        if solver.readModel(str(path)) != highspy.HighsStatus.kOk:
            raise ValueError(f"cannot read {name}")
        original = motifs(solver.getLp())
        if solver.presolve() != highspy.HighsStatus.kOk:
            raise ValueError(f"native presolve failed for {name}")
        residual = motifs(solver.getPresolvedLp())
        cases.append({"name": name, "source_sha256": digest,
                      "original": original, "native_presolved": residual})
    return {"protocol": "v0.0.62 nonblind descriptive residual-motif screen",
            "highs_version": solver.version(), "cases": cases,
            "scope": "no solve, reduction certificate, postsolve, runtime or speedup claim"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in SOURCES:
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = screen({name: getattr(args, name.replace("-", "_")) for name in SOURCES})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({case["name"]: case["native_presolved"]["shape"]
                      for case in result["cases"]}, indent=2))
