from unittest.mock import patch

import benchmark_v068

from neumann1.learned_compression_dataset import generate_learned_compression_cell
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def test_all_paths_verify_same_original_answer():
    case = generate_learned_compression_cell(
        2, 8, count=1, split="v068_smoke", seed=681008
    )[0]
    scorer = fit_frozen_v033_scorer()
    observations = [
        benchmark_v068._time_once(case, method, scorer)
        for method in benchmark_v068.METHODS
    ]
    assert all(row["verified"] for row in observations)
    assert observations[0]["candidates"] == 0
    assert observations[1]["candidates"] > 0
    assert observations[0]["total_ms"] > 0
    assert observations[1]["total_ms"] >= observations[1]["score_ms"]


def test_final_grid_is_new_and_has_all_cells():
    # Corpus validation is cheap compared with the timed complete benchmark.
    with patch.object(benchmark_v068, "CASES_PER_CELL", 1):
        cases = benchmark_v068._cases()
    assert len(cases) == len(benchmark_v068.learned_scale_grid())
    assert len({case.signature for case in cases}) == len(cases)
    assert set(case.signature for case in cases).isdisjoint(
        benchmark_v068.prior_v036_signatures()
    )
    assert set(case.signature for case in cases).isdisjoint(
        case.signature for case in benchmark_v068.v036_final_examples()
    )
