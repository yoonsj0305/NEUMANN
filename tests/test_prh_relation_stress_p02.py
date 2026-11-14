"""P0.2 independent negative controls and safe fallback contract."""
import numpy as np
from experiments.prh_relation_stress_p02 import (
    CONTRACT, guarded_match, has_indistinguishable_fingerprints,
    symmetric_scene,
)


def test_perfect_symmetry_is_unidentifiable_and_abstains():
    x, y = symmetric_scene(5001)
    assert has_indistinguishable_fingerprints(x)
    assert has_indistinguishable_fingerprints(y)
    assert guarded_match(x, y, CONTRACT['geometric_consistency_threshold'])['status'] == 'ABSTAIN_SYMMETRY'


def test_partial_scene_fails_closed():
    rng = np.random.default_rng(3)
    x, y = rng.normal(size=(12, 4)), rng.normal(size=(10, 4))
    result = guarded_match(x, y, CONTRACT['geometric_consistency_threshold'])
    assert result['status'] == 'ABSTAIN_PARTIAL_SCENE'
    assert result['mapping'] is None


def test_unknown_evidence_is_not_global_success():
    assert CONTRACT['Q1_to_Q7'] == 'OPEN'
    assert CONTRACT['original_task_program_discovery'] == 'NOT_RUN'
    assert CONTRACT['JEPA'] == 'NOT_RUN'
