"""Production Q6 representation interface for genuine 1D datasets.

The ARC2 2D 30x30 contract is untouched. Long one-dimensional arrays may
occupy the same <=900-pixel compute/memory budget. Both classical and
self-inventing interpreters must receive the SAME valid input domain.
"""
import pytest
from neumann1.relational_grid_inventor import grid,_fields,RelationalGridInventor
from neumann1.arc2_meta_grid_reasoner import G,valid,apply,PROGRAMS
from neumann1.hybrid_arc_grid_inventor import HybridArcGridInventor


def test_shared_original_arc2_and_longer_independent_1d_domain():
    for n in (1,30,31,64,128,900):
        raw=[[1 if i%3==0 else 0 for i in range(n)]]
        assert grid(raw)==G(raw)
        assert valid(G(raw))
        column=[[i%3] for i in range(n)]
        assert grid(column)==G(column)
        assert valid(G(column))
    assert len(grid([[0]*30]*30))==30
    for invalid in ([[0]*31]*2,[[0]*901],[[0]*30]*31):
        with pytest.raises(ValueError):
            grid(invalid)
        with pytest.raises(ValueError):
            G(invalid)


def test_long_row_feature_count_equivalent_to_unoptimized_definition():
    g=grid([[0,1,0,2,1,3]*13])  # 78 pixels
    fields=_fields(g)
    assert len(fields)==78
    for c in range(len(g[0])):
        v=g[0][c]
        assert fields[c]["row_color_count"]==sum(x==v for x in g[0])
        assert fields[c]["col_color_count"]==1
        assert fields[c]["row_nonzero_count"]==sum(x!=0 for x in g[0])
        assert fields[c]["col_nonzero_count"]==int(v!=0)


def test_old_and_new_program_languages_accept_one_dimensional_64_cell_inputs():
    source=grid([[1]+[0]*62+[2]])
    assert apply(source,"identity")==source
    assert apply(source,"flip_lr")==grid([[2]+[0]*62+[1]])
    inputs=[
        ([[4]+[0]*62+[8]],[[4]+[0]*62+[5]]),
        ([[8]+[0]*62+[3]],[[5]+[0]*62+[3]])]
    learned=RelationalGridInventor().solve(inputs)
    assert learned.source_fit
    target=[[8]+[0]*62+[1]]
    assert RelationalGridInventor().apply(learned,target)==grid([[5]+[0]*62+[1]])
    mixture=HybridArcGridInventor().solve(inputs,[target])
    assert mixture.candidates
    assert any(c.outputs==(grid([[5]+[0]*62+[1]]),) for c in mixture.candidates)
