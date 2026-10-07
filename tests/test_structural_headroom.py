"""Correctness/negative controls only; no full G0 grid timing."""
import io
import json
import zipfile

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from experiments import structural_headroom as g0
from experiments.legacy_control_asset_audit import sha, validate_zip


def test_true_twin_quotient_preserves_original_optimum():
    spec = {"family": "graph", "m": 5, "copies": 2, "seed": 414, "density": .5}
    case = g0.generate(spec)
    public = g0.public_view(case, "graph")
    assert set(public) == {"adjacency", "weights"}
    expected = int(public["weights"][g0.graph_milp(public)].sum())
    for route in g0.ROUTES["graph"]:
        witness = g0.solve(public, route, case["oracle_labels"] if route.startswith("FREE_") else None)
        assert g0.graph_check(public, witness, expected)


def test_superficially_similar_vertices_are_not_equivalent():
    public = {"adjacency": np.array([[0, 1, 1], [1, 0, 0], [1, 0, 0]], dtype=bool),
              "weights": np.array([1, 5, 7])}
    labels = g0.discover_twins(public)
    assert len(set(labels)) == 3  # Open-neighborhood similarity is insufficient.
    assert not g0.graph_check(public, [0, 1, 2], 13)
    assert not g0.graph_check(public, [2, 2], 14)


def test_pivoted_cholesky_and_free_factor_check_original_matrix():
    case = g0.generate({"family": "matrix", "n": 18, "rank": 3, "seed": 415})
    public = g0.public_view(case, "matrix")
    assert set(public) == {"A", "b"}
    with threadpool_limits(limits=1):
        u = g0.discover_factor(public)
        assert np.allclose(u @ u.T, public["A"] - np.eye(18), atol=1e-9)
        for route in g0.ROUTES["matrix"]:
            x = g0.solve(public, route, case["oracle_factor"] if route.startswith("FREE_") else None)
            assert g0.matrix_check(public, x)
        assert not g0.matrix_check(public, np.zeros(18))
        changed = {"A": public["A"] + np.diag(np.arange(18) / 5), "b": public["b"]}
        assert not g0.matrix_check(changed, g0.factor_solve(public["b"], case["oracle_factor"]))


def make_archive(members):
    manifest = {n: sha(raw) for n, raw in members.items()}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
        archive.writestr("archive-manifest.json", json.dumps(manifest).encode())
    return buf.getvalue()


def test_original_archive_identity_and_unsafe_paths_fail_closed():
    raw = make_archive({"report.json": b"{}"})
    assert validate_zip(raw, sha(raw))["report.json"] == b"{}"
    with pytest.raises(ValueError, match="identity"):
        validate_zip(raw, "0" * 64)
    bad = make_archive({"../report.json": b"{}"})
    with pytest.raises(ValueError, match="Unsafe"):
        validate_zip(bad, sha(bad))


def test_archive_terminal_cannot_change_original_member():
    raw = make_archive({"report.json": b"{}", "terminal.json": json.dumps({"files": {"report.json": "0" * 64}}).encode()})
    with pytest.raises(ValueError, match="Terminal"):
        validate_zip(raw, sha(raw))


def test_no_free_oracle_is_never_promoted_to_global_optimum_or_training():
    result = g0.summarize([])
    assert result["status"] == "INCOMPLETE"
    assert result["decision"] == "G0_NO_G1_TRAINING_ADMISSION"
    assert not result["global_optimal_representation_proven"]
    assert not result["g1_training_started"]
