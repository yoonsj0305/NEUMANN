import numpy as np,pickle
from experiments.einsum_original_kernel import agreement,original


def test_relative_comparison_rejects_zeros_for_tiny_answers():
    assert not agreement(np.zeros(3),np.full(3,1e-200))
    assert not agreement(np.ones((1,3)),np.ones(3))
    assert not agreement(np.array([np.inf]),np.array([np.inf]))
    assert agreement(np.array([-1.0,0,2]),np.array([-1.0,0,2]))


def test_original_loader_returns_only_arrays_and_equation():
    class Teacher:
        def __reduce__(self):return (eval,('1/0',))
    a=np.arange(6,dtype=np.float64).reshape(2,3)
    raw=pickle.dumps(('ab->', [a],Teacher(),Teacher()),protocol=5)
    equation,arrays,meta=original(raw)
    assert equation=='ab->';assert np.array_equal(arrays[0],a);assert meta[0]['shape']==[2,3]
