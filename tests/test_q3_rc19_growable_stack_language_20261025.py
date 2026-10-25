"""RC19 thin independent test, not claimed as raw neural checkpoint replay."""
import pathlib,sys,random,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'research'/'q3'/'rc19'))
from stack_macro import *

def test_learned_language_proof_gated():
    p=ProofGatedGrammar()
    token=p.register(LEARNED_PROGRAM,'a'*64)
    assert token=='LEARNED_DMEM_691cce3b103f'
    assert p.register((0,1,0,0,0,0),'a'*64)=='UNKNOWN_UNPROVED'
    try:p.run('UNREGISTERED',())
    except ValueError:pass
    else:raise AssertionError('unproved language executed')

def test_exact_all_short_streams_and_long_balanced_adversaries():
    p=ProofGatedGrammar();token=p.register(LEARNED_PROGRAM,'b'*64)
    for n in range(1,6):
        for word in itertools.product(tuple(itertools.product((0,1),(0,1))),repeat=n):
            assert p.run(token,word)==p.fallback(word)
    rng=random.Random(20261025)
    for k in (3,8,16):
        for depth in (4,16,128):
            opening=tuple((0,rng.randrange(k)) for _ in range(depth))
            closure=tuple((1,t) for _,t in reversed(opening))
            good=opening+closure
            bad=opening+closure[:-1]+((1,(closure[-1][1]+1)%k),)
            for word in (good,bad):
                assert p.run(token,word)==p.fallback(word)

def test_all_depth_information_lower_bound():
    for depth in range(1,128):
        assert necessary_information_bits(depth,2)==depth
        assert necessary_information_bits(depth,4)==2*depth
