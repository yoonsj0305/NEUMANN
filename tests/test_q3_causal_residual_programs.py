"""Q3 causal-residual synthesizer contract, not Q3 author generalization."""
from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_causal_residual_programs import (
    induce_causal_residual_programs,
)


def test_new_program_from_intermediate_causal_residual_in_sandbox():
    train=[
        ([[0,1,2,0]],[[0,3,4,0]]),
        ([[2,0,1,0]],[[4,0,3,0]]),
    ]
    checker=([[1,2,1,0]],[[3,4,3,0]])
    runner=IsolatedPython(max_seconds=8)
    candidates=induce_causal_residual_programs(
        train,runner,max_first=6,max_second=10,max_candidates=6)
    assert candidates
    assert all(x.representation==
        "source-induced-residual-causal-composition" for x in candidates)
    results=[runner.evaluate(x.program,[checker[0]]) for x in candidates]
    assert any(r.status=="EXECUTED" and len(r.outputs)==1
               and source_same_value(r.outputs[0],checker[1])
               for r in results)


def test_invalid_source_budget_fails_closed():
    class NoSandbox:
        def evaluate(self,program,inputs):
            raise AssertionError("must never evaluate invalid source")
    import pytest
    with pytest.raises(ValueError,match="bounded"):
        induce_causal_residual_programs([([[0]],[[1]])],NoSandbox())
