"""Q3 evidence-growth regression. Important: conditional successes, false certainty rejected."""
import itertools,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"))
from variable_state_growth import learned_equal_future,invent,run

def hidden_cycle(n):
    # Source-only oracle: exact end-to-end I/O, no transition labels exported
    def oracle(word):
        state=0;result=[]
        for symbol in word:
            result.append(int(symbol==0 and state==n-1))
            state=(state+1)%n if symbol==0 else 0
        return tuple(result)
    return oracle

def test_frozen_learned_residual_discriminator():
    assert learned_equal_future((1,0,1),(1,0,1))
    assert not learned_equal_future((1,0,1),(1,1,1))

def test_provisional_growth_works_for_unseen_5_6_state_examples():
    for k in (5,6):
        source=hidden_cycle(k)
        candidate=invent(source,depth=5)
        assert candidate["states"]==k
        assert candidate["status"].startswith("PROVISIONAL")
        for n in range(1,10):
            for w in itertools.product((0,1),repeat=n):
                assert run(candidate,w)==source(w)

def test_higher_capacity_7_is_unidentifiable_at_fixed_depth():
    source=hidden_cycle(7)
    candidate=invent(source,depth=5)
    assert candidate["states"]==1
    assert run(candidate,(0,)*7)!=source((0,)*7)
    assert candidate["status"].startswith("PROVISIONAL")
