from __future__ import annotations

from dataclasses import replace

import neumann1.anti_shortcut_v042 as v042

from neumann1.anti_shortcut_v042 import (
    E_METHODS, _discover, observe_peeling_method,
)
from neumann1.anti_shortcut_v042_dataset import v042_contract_examples
from neumann1.block_discovery import route_incidence_one_locals
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.mixed_coupled_dataset import generate_mixed_cell
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer
from neumann1.mixed_coupled import oracle_block_candidates


def test_fresh_contract_variants_recover_exact_verified_reference():
    scorer = fit_frozen_v033_scorer()
    for arm, example in v042_contract_examples():
        assert materialize_mixed_reference(example) is not None
        for method in E_METHODS:
            observation = observe_peeling_method(
                example, method, frozen_scorer=scorer,
            )
            assert observation.verified
            assert observation.unsafe_accepted_reductions == 0
            assert observation.rejected_joint_materializations == 0
            assert observation.derivation_calls >= observation.accepted_block_count
            if method == "E2_residual_peeling":
                assert observation.solver_savings_recovery == 1.0
                assert observation.elimination_recovery == 1.0
            if arm == "coefficient":
                assert observation.block_true_positive_count == example.block_count


def test_discovery_ignores_oracle_labels_and_core_dimension():
    scorer = fit_frozen_v033_scorer()
    for _, example in v042_contract_examples():
        local = route_incidence_one_locals(example, frozen_scorer=scorer)
        shadow = replace(example, oracle_blocks=(), oracle_easy_leaves=(),
                         core_dimension=1)
        for method in E_METHODS:
            assert _discover(example, method, local) == _discover(shadow, method, local)


def test_no_reduction_control_remains_unchanged():
    scorer = fit_frozen_v033_scorer()
    for k in (2, 4):
        example = generate_mixed_cell(
            k, k, count=1, split="v042_control", seed=1_312_000+k,
        )[0]
        for method in E_METHODS:
            observation = observe_peeling_method(
                example, method, frozen_scorer=scorer,
            )
            assert observation.verified
            assert observation.accepted_local_count == 0
            assert observation.accepted_block_count == 0
            assert observation.final_solver_ops == observation.baseline_solver_ops


def test_invalid_joint_proposal_falls_back_to_verified_full_solve(monkeypatch):
    scorer = fit_frozen_v033_scorer()
    example = dict(v042_contract_examples())["overlap"]
    valid = oracle_block_candidates(example)[0]
    rule = replace(valid.rules[0], constant=valid.rules[0].constant + 1)
    corrupted = replace(valid, rules=(rule, valid.rules[1]))
    monkeypatch.setattr(
        v042, "_discover", lambda *args: v042.PeelingDiscovery(
            (corrupted,), 0, 1, 1,
        ),
    )
    result = observe_peeling_method(
        example, "E2_residual_peeling", frozen_scorer=scorer,
    )
    assert result.verified
    assert result.rejected_joint_materializations == 1
    assert result.accepted_block_count == 0
    assert result.accepted_local_count == 0
    assert result.final_solver_ops == result.baseline_solver_ops
    assert result.unsafe_accepted_reductions == 0
