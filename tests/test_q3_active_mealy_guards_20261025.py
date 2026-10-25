"""Two contract-level negative checks complementary to the 3 main runtime tests."""
import pathlib,sys,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"active_mealy"))
from learned_active_inference import learn,execute

def test_invalid_oracle_refuses_short_output():
    with pytest.raises(ValueError,match="oracle length"):
        learn(lambda word:(),alphabet=(0,1))

def test_without_equivalence_never_certifies_even_perfect_observations():
    machine={"transition":[[0,0]],"output":[[0,1]]}
    def oracle(word):return execute(machine,word)
    p=learn(oracle)
    assert p["states"]==1 and p["EQ_calls"]==0
    assert p["status"]=="PROVISIONAL_NO_EQ_OR_CLASS_PROOF"
    for n in range(1,9):
        assert execute(p,(0,)*n)==execute(machine,(0,)*n)
