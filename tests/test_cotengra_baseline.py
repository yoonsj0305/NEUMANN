import pytest
from neumann1.cotengra_baseline import plan


@pytest.mark.parametrize("variant", ["GREEDY128", "RECONF32"])
def test_reused_optimizer_keeps_original_hyperedge_goal(variant):
    public = {"equation": "ab,bc,bd->acd", "shapes": [[2, 3], [3, 2], [3, 2]]}
    result = plan(public, variant, 13, repeats=2, reconfigure_iterations=1)
    assert result["certificate"]["accepted"] and result["certificate"]["ordered_output"] == "acd"
    assert not result["oracle_used"] and not result["learned"]
    assert result["trials"] == 2
