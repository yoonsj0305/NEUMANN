"""Architecture fixtures, not trained performance evidence."""
import inspect

import pytest
torch = pytest.importorskip('torch')
from experiments.lp_state_models_v087 import GraphStateModel, roster


def test_compaction_actually_removes_states_and_graph_work():
    models = roster()
    compact, full = models['compact16'], models['full16']
    assert list(inspect.signature(compact.forward).parameters) == ['matrix', 'row_features', 'col_features']
    assert all(torch.equal(v, full.state_dict()[k]) for k, v in compact.state_dict().items())
    A, rf, cf = torch.randn(4, 64), torch.randn(4, 8), torch.randn(64, 8)
    with torch.inference_mode(): a, b = compact(A, rf, cf), full(A, rf, cf)
    assert a['state_columns'] == 8 and b['state_columns'] == 64
    assert a['edge_multiply_terms'] == 2*4*64*16 + 4*4*8*16
    assert a['edge_multiply_terms'] < b['edge_multiply_terms']
    assert a['scores'].shape == (64,) and a['y'].shape == (4,)
    assert sum((a['scores'] > -1e6).tolist()) == 8
    assert all(sum(p.numel() for p in model.parameters()) <= 400000 for model in models.values())


def test_full_model_column_permutation_equivariance():
    torch.manual_seed(87001)
    model = GraphStateModel(16, False).eval()
    A, rf, cf = torch.randn(4, 25), torch.randn(4, 8), torch.randn(25, 8)
    order = torch.randperm(25)
    with torch.inference_mode(): a, b = model(A, rf, cf), model(A[:, order], rf, cf[order])
    torch.testing.assert_close(a['scores'][order], b['scores'])
    torch.testing.assert_close(a['x'][order], b['x'])
    torch.testing.assert_close(a['y'], b['y'])


def test_small_problem_no_shortlist_removal_equals_full_model():
    models = roster()
    A, rf, cf = torch.randn(4, 5), torch.randn(4, 8), torch.randn(5, 8)
    with torch.inference_mode(): a, b = models['compact16'](A, rf, cf), models['full16'](A, rf, cf)
    torch.testing.assert_close(a['scores'], b['scores'])
    assert a['state_columns'] == b['state_columns'] == 5
