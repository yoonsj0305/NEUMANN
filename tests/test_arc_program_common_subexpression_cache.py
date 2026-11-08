"""Q4: share exact immutable grid-operation subexpressions across methods."""
from neumann1.arc2_meta_grid_reasoner import (
    G,apply,_apply_immutable,_apply_uncached,PROGRAMS,predict)


def test_primitive_outputs_exactly_preserved_under_bounded_pure_memo():
    grids=[
        G([[0,1,0],[2,2,0],[0,1,3]]),
        G([[1,0,2,2],[0,1,0,2]]),
        G([[3]+[0]*62+[8]]),
    ]
    for g in grids:
        for program in PROGRAMS[:30]:
            p=program[0]
            assert apply(g,p)==_apply_uncached(g,p),p


def test_repeated_common_first_operator_evaluated_once():
    _apply_immutable.cache_clear()
    source=G([[0,1,2,0],[0,1,0,3]])
    for op in ("flip_lr","crop_nonzero","rotate90","extract_largest"):
        assert apply(source,op)==_apply_uncached(source,op)
        assert apply(source,op)==_apply_uncached(source,op)
    info=_apply_immutable.cache_info()
    assert info.hits>=4 and info.maxsize==4096
    assert info.currsize<=4096


def test_invalid_primitive_none_is_cached_and_no_unbounded_growth():
    _apply_immutable.cache_clear()
    grid=G([[1,2,3]])
    assert apply(grid,"down3") is None
    assert apply(grid,"down3") is None
    assert _apply_immutable.cache_info().hits>=1
    assert isinstance(predict(grid,("flip_lr","flip_lr")),tuple)
    # Public pure apply still tolerates legacy noncanonical list input.
    assert apply([[1,2]],"flip_lr")==((2,1),)
