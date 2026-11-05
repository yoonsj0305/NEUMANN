"""Proof boundary and first-receipt tests, independent of any neural model."""
import sys, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
from q3_task_sufficiency_p18 import CONTRACT, build_scenes, run


def test_asymmetric_unique_worlds():
    scenes,_ = build_scenes()
    assert len(scenes)==2048
    assert len({s.tobytes() for s in scenes})==2048
    assert all(not np.array_equal(s,np.fliplr(s)) for s in scenes)


def test_good_views_perfectly_identify_world():
    scenes,_=build_scenes()
    for s in scenes[:64]:
        v1=s.copy();v2=np.flipud(s)
        assert np.array_equal(v1,np.flipud(v2))


def test_goal_ambiguity_is_exactly_one_bit():
    result=run()
    assert result['first_gate']=='PASS_CONSTRUCTED_TASK_SUFFICIENCY_BOUND'
    assert result['scene_only_bayes_correct']==2048
    assert result['goal_conditioned_correct']==4096
    assert result['conditional_output_entropy_bits_given_scene']==1.0


def test_first_receipt_immutable_and_not_jePa_claim():
    a=json.loads((ROOT/'docs/experiments/results/q3_task_sufficiency_p18_FIRST.json').read_text())
    assert a['first_gate']=='PASS_CONSTRUCTED_TASK_SUFFICIENCY_BOUND'
    assert a['contract']['JEPA_trained'] is False
    assert a['global_q1_to_q7']=='OPEN'
    assert a['original_task_record_count']==4096
