"""Fast contract tests for P1.7; no retraining and no result retuning."""
import json
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments'))
from q3_operator_good_views_p17 import CONTRACT, ALL_OPS, execute, pair_batch, make_split


def test_operator_shapes_and_binary_values():
    sample = np.zeros((12,12), dtype=np.float32)
    sample[1,2] = 1
    for op in ALL_OPS:
        out = execute(sample, op)
        assert out.shape == (12,12)
        assert set(np.unique(out)).issubset({0,1})
        assert out.sum()==1


def test_symbolic_direction_identity():
    x = np.zeros((12,12), dtype=np.float32)
    x[3,5] = 1
    assert execute(x,'up')[2,5]==1
    assert execute(x,'down')[4,5]==1
    assert execute(x,'left')[3,4]==1
    assert execute(x,'right')[3,6]==1
    np.testing.assert_array_equal(execute(execute(x, 'rot90'), 'rot270'), x)


def test_good_view_independence():
    a,b = pair_batch(np.random.default_rng(20261117), 'good')
    # Independently sampled scenes, not two masked versions of the exact same input.
    assert a.shape == b.shape == (6,2,12,12)
    assert not (a[:,0]==b[:,0]).all()
    assert all(np.array_equal(execute(a[i,0].numpy(),op), a[i,1].numpy()) for i,op in enumerate(CONTRACT['training_operators']))
    assert all(np.array_equal(execute(b[i,0].numpy(),op), b[i,1].numpy()) for i,op in enumerate(CONTRACT['training_operators']))


def test_disjoint_split_seed_and_total():
    support,_ = make_split(CONTRACT['support_seed'],CONTRACT['support_per_operator'])
    query,_ = make_split(CONTRACT['query_seed'],CONTRACT['query_per_operator'])
    assert support.shape == (8*24,2,12,12)
    assert query.shape == (8*48,2,12,12)
    assert not np.array_equal(support[0].numpy(),query[0].numpy())


def test_immutable_first_receipt_scope():
    data=json.loads((ROOT / 'docs/experiments/results/q3_operator_good_views_p17_FIRST.json').read_text())
    assert data['local_view_gate'] == 'FAIL_OPERATOR_VIEW_ABLATION'
    assert data['global_q1_q7'] == 'OPEN'
    assert data['contract']['JEPA'] == 'NOT_RUN'
    assert data['good']['query_count'] == 384
    assert data['strong_symbolic_direct']['correct'] == 384
