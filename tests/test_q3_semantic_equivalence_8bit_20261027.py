import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"/"q3"/"discovery_policy"))
from semantic_equivalence_8bit import Program8, apply, truth_table, build_exact_index, library_membership

def test_all_xor_rotate_pair_equivalences():
    assert all(truth_table(Program8('XR',(c,r)))==truth_table(Program8('RX',(r,apply('R',c,r))))
               for c in range(256) for r in range(1,8))

def test_full_domain_not_syntax():
    ix=build_exact_index(('RX',))
    assert len(ix)==1792
    for c in range(128,256):
        for r in range(1,8):
            status,witness=library_membership(Program8('XR',(c,r)),ix)
            assert status=='CLASSICAL_EQUIVALENT'
            assert truth_table(witness)==truth_table(Program8('XR',(c,r)))

def test_controls_not_in_specific_grammar():
    ix=build_exact_index(('RX',))
    reverse=bytes(int(format(x,'08b')[::-1],2) for x in range(256))
    gray=bytes(x^(x>>1) for x in range(256))
    assert reverse not in ix and gray not in ix
    assert library_membership(Program8('RX',(2,37)),ix)[0]=='CLASSICAL_EQUIVALENT'
