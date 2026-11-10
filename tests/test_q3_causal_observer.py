"""Independent losslessness and no-domain-solver tests for causal observer."""
import json
import pytest
from neumann1.q3_causal_observer import (
    causal_json_edits,replay_observed_edits,lossless_causal_source_prompt)
from neumann1.open_program_inventor import (
    GenerativeProgramInventor,IsolatedPython)


@pytest.mark.parametrize("a,b",[
    ({"k":[1,{"x":True,"y":3}],"m":None},
     {"k":[1,{"x":False,"y":3}],"m":None}),
    ([[0,2],[2,0]],[[0,3],[2,0]]),
    ([1,2],[[3],4]),
    ({"a":1},{"a":1,"b":2}),
    (True,1),
    ([1,2],[1,2]),
])
def test_source_changes_reconstruct_exact_original_output(a,b):
    delta=causal_json_edits(a,b)
    assert json.dumps(replay_observed_edits(a,delta),sort_keys=True)==json.dumps(
        b,sort_keys=True)
    if a==b:
        assert delta==()


def test_source_patch_replay_refuses_forged_before_value():
    delta=causal_json_edits([0,1],[0,2])
    forged=[dict(delta[0])]
    forged[0]["before"]=4
    with pytest.raises(ValueError,match="patch before mismatch"):
        replay_observed_edits([0,1],forged)


def test_observer_has_no_target_access_or_program_replay():
    observed=[([[0,1],[0,0]],[[0,2],[0,0]]),
              ([[0,3],[0,0]],[[0,4],[0,0]])]
    prompt=lossless_causal_source_prompt(observed)
    assert "Observed input-to-output edits" in prompt
    assert '"path":[0,1]' in prompt
    assert "def transform(x)" in prompt
    assert "Source input:" in prompt
    assert "TARGET" not in prompt
    with pytest.raises(ValueError,match="bounded"):
        lossless_causal_source_prompt([])


def test_generic_causal_observer_reaches_unchanged_program_generator():
    """A constructed interface contract, never a claimed generalization."""
    class ObservedPolicy:
        def __init__(self):
            self.prompts=[]
        def propose(self,prompt):
            self.prompts.append(prompt)
            return "def transform(x):\n    return x+1"
    policy=ObservedPolicy()
    runner=IsolatedPython(max_seconds=8)
    d=GenerativeProgramInventor(
        policy,runner,max_proposals=1).discover(
        [(2,3),(4,5)],independent_source_checks=[(6,7)],
        source_observer="lossless-causal-edits")
    assert d.verified
    assert len(policy.prompts)==1
    assert "Observed input-to-output edits" in policy.prompts[0]
