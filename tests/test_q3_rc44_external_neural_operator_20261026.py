"""RC44 regression uses a data snapshot whose origin is ARC Prize
public TRAINING task 12422b43; no claim that it is private/unseen to GPT-6.
"""
import pathlib,sys,random,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc44"))
from marker_periodic import marker_periodic_fill,source_gate

TEST_INPUT=[[5,0,4,4,4,0,0],[5,0,0,8,0,0,0],[5,0,0,6,0,0,0],
            [0,0,2,2,0,0,0]]+[[0]*7 for _ in range(6)]
FROZEN_FIRST_OUTPUT=[
 [5,0,4,4,4,0,0],[5,0,0,8,0,0,0],[5,0,0,6,0,0,0],
 [0,0,2,2,0,0,0],[0,0,4,4,4,0,0],[0,0,0,8,0,0,0],
 [0,0,0,6,0,0,0],[0,0,4,4,4,0,0],[0,0,0,8,0,0,0],
 [0,0,0,6,0,0,0]]
def test_one_actual_arc2_target_from_frozen_first_model_prediction():
    assert marker_periodic_fill(TEST_INPUT)==FROZEN_FIRST_OUTPUT
    assert len(FROZEN_FIRST_OUTPUT)==10
    assert sum(map(len,FROZEN_FIRST_OUTPUT))==70

def test_source_checked_promotion_then_unknown():
    src=[[5,0,6,8,0,0],[0,0,8,3,0,0]]+[[0]*6 for _ in range(5)]
    gold=[[5,0,6,8,0,0],[0,0,8,3,0,0]]+[[0,0,6,8,0,0] for _ in range(5)]
    assert source_gate([{"input":src,"output":gold}])["status"]=="SOURCE_FIT_ONLY"
    gold[-1][2]=9
    assert source_gate([{"input":src,"output":gold}])["status"]=="UNKNOWN_SOURCE_MISMATCH"
    assert source_gate([])["status"]=="UNKNOWN_NO_DEMONSTRATIONS"

def test_invalid_inputs_fail_closed():
    for x in ([],[[]],[[0,0],[0,0]],[[3,1],[0]],[[3,4],[3,4]],[[5,3],[0,4]]):
        with pytest.raises(ValueError):marker_periodic_fill(x)

def test_operator_semantics_without_neural_or_external_gold():
    r=random.Random(44)
    for _ in range(100):
        n=r.randint(1,4);extra=r.randint(1,6);width=r.randint(2,10)
        marker=r.randint(1,9)
        top=[[marker]+[r.randint(0,9) for _ in range(width-1)] for _ in range(n)]
        g=top+[[0]*width for _ in range(extra)]
        got=marker_periodic_fill(g)
        assert got[:n]==top
        assert all(got[n+i]==[0]+top[i%n][1:] for i in range(extra))
