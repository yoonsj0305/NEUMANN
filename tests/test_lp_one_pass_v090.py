from unittest.mock import patch
import pytest
torch = pytest.importorskip('torch')
from experiments.lp_state_models_v087 import roster
from experiments.lp_one_pass_v090 import early_indices, observe


@pytest.mark.parametrize('seed',[87001,87002])
@pytest.mark.parametrize('shape',[(4,64),(4,5)])
def test_early_compact_retained_set_is_same_and_late_updates_not_called(seed,shape):
    torch.manual_seed(seed)
    models=roster(seed); m,n=shape
    args=(torch.randn(m,n),torch.randn(m,8),torch.randn(n,8))
    with torch.inference_mode():
        expected=models['compact16'](*args)['selected'].tolist()
        with patch.object(models['compact16'].to_row[1],'forward',side_effect=AssertionError('late update')), \
             patch.object(models['compact16'].primal,'forward',side_effect=AssertionError('answer head')):
            assert early_indices(models['compact16'],*args)==expected
        # Equal initialization makes the shared Direct coarse call identical.
        assert early_indices(models['full16'],*args)==expected
        out=models['point16'](*args)
        expected_point=torch.argsort(out['scores'],descending=True,stable=True)[:min(n,2*m)].tolist()
        assert early_indices(models['point16'],*args)==expected_point


def test_nonfinite_proposal_abstains_instead_of_becoming_authority():
    model=roster()['compact16']
    with torch.no_grad():model.coarse.bias.fill_(float('nan'))
    assert early_indices(model,torch.ones(2,8),torch.ones(2,8),torch.ones(8,8))==[]


def test_unknown_architecture_rejected():
    with pytest.raises(TypeError):early_indices(object(),torch.ones(1,2),torch.ones(1,8),torch.ones(2,8))
