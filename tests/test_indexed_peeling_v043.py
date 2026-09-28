from dataclasses import replace

import neumann1.indexed_peeling_v043 as v043
from neumann1.block_discovery import route_incidence_one_locals
from neumann1.coupled_block import derive_block_candidate
from neumann1.indexed_peeling_v043_dataset import v043_contract_examples
from neumann1.mixed_coupled_dataset import generate_mixed_cell
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def test_indexed_matches_frozen_on_three_contract_arms():
    scorer = fit_frozen_v033_scorer()
    for _, example in v043_contract_examples():
        old = v043.execute_peeling(example, frozen_scorer=scorer, indexed=False)
        new = v043.execute_peeling(example, frozen_scorer=scorer, indexed=True)
        assert old.verified and new.verified
        assert old.local_keys == new.local_keys
        assert old.block_keys == new.block_keys
        assert old.answer == new.answer
        assert old.retained_dimension == new.retained_dimension
        assert old.solver_ops == new.solver_ops
        assert new.row_pair_examinations <= old.row_pair_examinations


def test_discovery_is_blind_to_oracle_labels_and_core_dimension():
    scorer = fit_frozen_v033_scorer()
    for _, example in v043_contract_examples():
        local = route_incidence_one_locals(example, frozen_scorer=scorer)
        shadow = replace(example, oracle_blocks=(), oracle_easy_leaves=(), core_dimension=1)
        assert v043.discover_indexed(example, local) == v043.discover_indexed(shadow, local)


def test_full_system_control_has_no_proposal_or_rejection():
    scorer = fit_frozen_v033_scorer()
    for k in (2, 4):
        example = generate_mixed_cell(
            k, k, count=1, split="v043_control", seed=1_712_000+k,
        )[0]
        result = v043.execute_peeling(example, frozen_scorer=scorer, indexed=True)
        assert result.verified
        assert result.local_keys == result.block_keys == ()
        assert result.materialization_attempts == result.rejected_materializations == 0
        assert result.retained_dimension == k


def test_corrupted_joint_candidate_fails_closed(monkeypatch):
    scorer = fit_frozen_v033_scorer()
    example = dict(v043_contract_examples())["overlap"]
    old = v043.discover_indexed(example, ())
    valid = old.candidates[0]
    rule = replace(valid.rules[0], constant=valid.rules[0].constant + 1)
    corrupted = replace(valid, rules=(rule, valid.rules[1]))
    monkeypatch.setattr(v043, "discover_indexed", lambda *args: replace(
        old, candidates=(corrupted,),
    ))
    result = v043.execute_peeling(example, frozen_scorer=scorer, indexed=True)
    assert result.verified
    assert result.rejected_materializations == 1
    assert result.local_keys == result.block_keys == ()
    assert result.retained_dimension == example.apparent_dimension
