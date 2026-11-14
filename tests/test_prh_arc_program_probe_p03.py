"""Open-development guard tests; no blind ARC performance claimed."""
import json
from pathlib import Path
import numpy as np
from experiments.prh_arc_program_probe_p03 import (
    CONTRACT, synthesize, predict_with_consensus, score_opened_task,
)

FIXTURES = Path(__file__).resolve().parents[1]/'experiments'/'fixtures'/'arc_agi1_opened'


def canonical_fnv1a(blob):
    normalized = json.dumps(blob, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    h = 2166136261
    for byte in normalized.encode('utf-8'):
        h = ((h ^ byte)*16777619) & 0xffffffff
    return f'{h:08x}'


def test_fixture_source_identity_matches_upstream():
    expected = {'007bbfb7':'d3700067','05f2a901':'383f48ef','08ed6ac7':'b77aca22','0d3d703e':'fc22f712'}
    for task_id, hash_ in expected.items():
        data = json.loads((FIXTURES/f'{task_id}.json').read_text())
        assert canonical_fnv1a(data) == hash_


def test_test_output_cannot_affect_program_selection():
    orig = json.loads((FIXTURES/'0d3d703e.json').read_text())
    a, _ = synthesize(orig['train'])
    # Mutating public test answer does NOT reach or alter the synthesizer.
    orig['test'][0]['output'] = [[1000]]
    b, _ = synthesize(orig['train'])
    assert a['program_names'] == b['program_names'] == ['inferred_color_map']


def test_unseen_palette_abstains():
    task = json.loads((FIXTURES/'0d3d703e.json').read_text())
    _, winners = synthesize(task['train'])
    prediction, status = predict_with_consensus(winners, [[37, 37]])
    assert prediction is None and status == 'ABSTAIN_TEST_EXECUTION'


def test_missing_candidate_keeps_fail_not_oracle_repair():
    task = json.loads((FIXTURES/'05f2a901.json').read_text())
    result = score_opened_task(task, '05f2a901')
    assert result['task_solved'] is False
    assert result['search_status'] == 'ABSTAIN_NO_PROGRAM'


def test_local_scope_immutable():
    assert CONTRACT['stage'] == 'OPENED_DEVELOPMENT_NOT_HOLDOUT'
    assert CONTRACT['claims']['new_operator_invented'] is False
    assert CONTRACT['claims']['global_q1_to_q7'] == 'OPEN'
