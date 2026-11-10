"""Synthetic mechanism contracts. Original SOURCE and author TEST are separate."""
from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_relational_reduce_invention import induce_relational_reducers


def draw(main_color,minor_color,*,main_shape=(3,3),out=(3,3)):
    h,w=13,13
    grid=[[0]*w for _ in range(h)]
    mh,mw=main_shape
    for r in range(mh):
        for c in range(mw):
            grid[1+r][2+c]=main_color
    # Lower competing component with 4 pixels.
    for r in range(2):
        for c in range(2):
            grid[9+r][9+c]=minor_color
    return grid,[[main_color]*out[1] for _ in range(out[0])]


def test_argmax_reduce_invents_heldout_original_style_new_symbol():
    source=[draw(3,5),draw(4,6),draw(7,8)]
    heldout=draw(9,2,main_shape=(4,3))
    generator=induce_relational_reducers(source,max_candidates=4)
    assert generator
    runner=IsolatedPython(max_seconds=8)
    assert any(
        res.status=="EXECUTED" and len(res.outputs)==1 and
        source_same_value(res.outputs[0],heldout[1])
        for res in (
            runner.evaluate(p.program,[heldout[0]]) for p in generator)
    )


def test_no_constant_color_shortcut_can_claim_structural_invention():
    source=[draw(3,5),draw(3,6)]
    assert not induce_relational_reducers(source)
