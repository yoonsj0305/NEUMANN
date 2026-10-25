"""Q3 exhaustive bounded model validation of formal infinite-length lower bound."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"memory_growth"))
from bounded_state_lower_bound import witness,future_output,assert_lower_bound,multiply,GrowingMemoryMultiply

def test_all_prefix_histories_distinguishable_k1_to_10():
    for k in range(1,11):
        assert assert_lower_bound(k)==2**k
        for u in range(2**k):
            prefix,suffix=witness(k,u)
            assert len(prefix)==k
            assert all(v[1]==0 for v in prefix)
            assert future_output(k,u)==tuple((u>>j)&1 for j in range(k))

def test_full_finite_all_binary_multiplications_1_to_8_bits():
    cases=0
    for n in range(1,9):
        for a in range(2**n):
            for b in range(2**n):
                assert multiply(a,b,n)==a*b
                cases+=1
    assert cases==87380

def test_sequential_emitted_bits_match_product_prefix():
    for n in range(1,7):
        for a in range(2**n):
            for b in range(2**n):
                m=GrowingMemoryMultiply()
                for i in range(n):
                    bit=m.step((a>>i)&1,(b>>i)&1)
                    assert bit==((a*b)>>i)&1
                assert m.finish(n)==a*b

def test_invalid_stream_input_is_blocked():
    for a,b in ((-1,0),(2,0),(0,2)):
        try:
            m=GrowingMemoryMultiply();m.step(a,b)
        except ValueError:pass
        else:raise AssertionError((a,b))
