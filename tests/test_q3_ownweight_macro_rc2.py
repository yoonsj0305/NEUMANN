"""CI smoke: the registered own-weight macro names implement real new functions relative to primitives."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"research"/"q3"))
from ownweight_macro_rc2 import FROZEN_MACRO_BODIES, apply_one, call_named, compile_named_program, execute

def test_32_nontrivial_definitions_and_unique_meanings():
    probes=[[(17*i+11*j*i+3*j)%11 for j in range(6)] for i in range(1,21)]
    assert len(FROZEN_MACRO_BODIES)==32
    primitive={tuple(x for v in probes for x in apply_one(v, k)) for k in range(10)}
    distinct=set()
    for name,body in FROZEN_MACRO_BODIES.items():
        assert len(body)==2
        code_signature=tuple(x for v in probes for x in call_named(name,v))
        # A witness on a probe proves not universally equal to that primitive.
        assert code_signature not in primitive
        assert code_signature not in distinct
        distinct.add(code_signature)

def test_named_operator_reuse_and_expansion():
    samples=[[0,1,2,3,4,5],[1,1,2,3,5,8],[10,0,10,0,10,0],[4,3,2,1,0,10]]
    names=("NEU_DEF_27","NEU_DEF_29","NEU_DEF_13")
    flat=compile_named_program(names)
    assert flat==(2,6,4,9,5,6)
    for v in samples:
        y=list(v)
        for name in names:y=call_named(name,y)
        assert y==execute(flat,v)

def test_unregistered_or_bad_input_refused():
    import pytest
    with pytest.raises(KeyError):call_named("GOLD_ORACLE", [0]*6)
    with pytest.raises(ValueError):call_named("NEU_DEF_00", [0]*5)
    with pytest.raises(ValueError):call_named("NEU_DEF_00", [20]*6)
