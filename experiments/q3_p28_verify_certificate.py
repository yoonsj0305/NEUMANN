"""Independent (Python) verifier for P2.8 factored execution certificates.

This is an *execution proof* for a fixed small AST, not a formal proof of
future correctness, operator novelty, or cross-family generalization.
No ARC TEST gold is used or accepted here.
"""
import json
import sys
from pathlib import Path

SCHEMA = "neumann.q3.p28.proof-certificate.v1"
LABELS = ("zero", "outer", "inner")


def _valid_grid(grid):
    return (
        isinstance(grid, list)
        and 1 <= len(grid) <= 30
        and isinstance(grid[0], list)
        and 1 <= len(grid[0]) <= 30
        and all(
            isinstance(row, list)
            and len(row) == len(grid[0])
            and all(type(c) is int and 0 <= c <= 9 for c in row)
            for row in grid
        )
    )


def independent_execute(ast, grid):
    if (not _valid_grid(grid) or not isinstance(ast, dict)
        or set(ast.keys()) != {"kind", "selector"}
        or ast["kind"] != "factorized-zero-conditional"
        or not isinstance(ast["selector"], list)
        or len(ast["selector"]) != 4
        or any(type(x) is not str or x not in LABELS for x in ast["selector"])):
        raise ValueError("INVALID_PROGRAM_OR_GRID")
    h, w = len(grid), len(grid[0])
    if h * h > 30 or w * w > 30:
        raise ValueError("OUTPUT_SHAPE_EXCEEDS_LIMIT")
    result = [[0 for _ in range(w*w)] for _ in range(h*h)]
    for i in range(h):
        for j in range(w):
            a = grid[i][j]
            for rr in range(h):
                for cc in range(w):
                    b = grid[rr][cc]
                    mask = 2*int(a == 0) + int(b == 0)
                    rule = ast["selector"][mask]
                    result[i*h+rr][j*w+cc] = 0 if rule == "zero" else (a if rule == "outer" else b)
    return result


def verify_certificate(cert):
    if not isinstance(cert, dict) or set(cert) != {"schema", "ast", "train", "test_inputs", "predicted_test"}:
        raise ValueError("BAD_CERTIFICATE_FIELDS")
    if cert["schema"] != SCHEMA:
        raise ValueError("BAD_CERTIFICATE_SCHEMA")
    tr = cert["train"]
    ti = cert["test_inputs"]
    preds = cert["predicted_test"]
    if (not isinstance(tr, list) or not tr or not isinstance(ti, list) or not ti
            or not isinstance(preds, list) or len(ti) != len(preds)):
        raise ValueError("EMPTY_OR_MISMATCHED_EVIDENCE")
    for item in tr:
        if not isinstance(item, dict) or set(item) != {"input", "output"} or not _valid_grid(item["output"]):
            raise ValueError("BAD_TRAIN_PAIR")
        if independent_execute(cert["ast"], item["input"]) != item["output"]:
            raise ValueError("TRAIN_COUNTEREXAMPLE")
    for inp, pred in zip(ti, preds):
        if not _valid_grid(pred) or independent_execute(cert["ast"], inp) != pred:
            raise ValueError("TEST_PREDICTION_COUNTEREXAMPLE")
    return {"status": "EXECUTION_PROOF_PASS", "train_pairs": len(tr),
            "test_inputs": len(ti), "not_a_generalization_proof": True}


def main():
    if len(sys.argv) != 2:
        print("Usage: python q3_p28_verify_certificate.py <cert.json>", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(json.dumps(verify_certificate(data), sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("CERTIFICATE_REJECTED:" + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
