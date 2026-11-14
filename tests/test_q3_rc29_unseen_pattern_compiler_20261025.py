"""RC29 light smoke; complete weights/16-table classical audit in ZIP."""
import pathlib,sys,itertools,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc29"))
from shared_learned_opcode import *

def test_weight_derived_executable_program_and_all_held_out_three_bit_patterns():
    vm=ProofGatedGrammar()
    approved=vm.register(source_from_learned_weights())
    assert approved["status"]=="SCOPED_CERTIFIED"
    op=approved["opcode"]
    for p in ((1,0,1),(1,1,0)):
        for n in range(3,10):
            for w in itertools.product((0,1),repeat=n):
                want=tuple(0 if j<2 else int(w[j-2:j+1]==p) for j in range(n))
                assert vm.suffix_stream(op,w,p)==want
    rng=random.Random(20261025)
    for length in (1,2,8,17,128):
        for _ in range(32):
            x=tuple(rng.getrandbits(1) for _ in range(length))
            y=tuple(rng.getrandbits(1) for _ in range(length))
            assert vm.compare(op,x,y)==(x==y)

def test_semantics_proven_not_authorized_by_format_alone():
    vm=ProofGatedGrammar()
    assert vm.register(source_from_learned_weights((0,1,1,0)))["status"]=="UNKNOWN_SEMANTIC_PROOF"
    assert vm.register("DEF X(bit,bit)\nTABLE 1001\nEND")["status"]=="UNKNOWN_SYNTAX"
    assert vm.register(source_from_learned_weights()+"import os")["status"]=="UNKNOWN_SYNTAX"
    assert SCOPED_ADMISSION["global_Q3"]=="OPEN"
    try:vm.compare("UNKNOWN",(0,1),(1,0))
    except ValueError:pass
    else:raise AssertionError("unregistered program executed")
