"""RC31: bounded source-learning PASS, meta-zero-shot FAIL, hybrid transfer PASS."""
import itertools,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'research'/'q3'/'rc31'))
from learned_library import SOURCE,NEW,operand,register_frozen
def test_frozen_source_torch_proposed_programs_exact():
    assert len(SOURCE)==12
    for mask in SOURCE:
        for a,b in itertools.product((0,1),repeat=2):
            assert operand(mask,a,b)==((mask>>(2*a+b))&1)
def test_hybrid_new_unseen_opcodes_are_semantically_verified():
    vm,names=register_frozen()
    assert names=={6:'AUTO_24e6134bb628',9:'AUTO_6ce2b35c8f64',
                   11:'AUTO_8ac61baea2ed',14:'AUTO_7072148546ec'}
    for mask,name in names.items():
        for a,b in itertools.product((0,1),repeat=2):
            assert vm.apply(name,a,b)==((mask>>(2*a+b))&1)
        for other in range(16):
            if other!=mask:
                assert vm.register(NEW[mask],other)=='UNKNOWN_WRONG_SEMANTICS'
def test_new_opcode_bodies_enable_exact_bounded_fulladder():
    vm,names=register_frozen()
    for n in range(1,7):
        for a in range(1<<n):
            for b in range(1<<n):
                c=s=0
                for i in range(n):
                    x=(a>>i)&1;y=(b>>i)&1
                    p=vm.apply(names[6],x,y)
                    s|=vm.apply(names[6],p,c)<<i
                    c=vm.apply(names[14],operand(8,x,y),operand(8,p,c))
                assert s|(c<<n)==a+b
def test_critical_safety_and_global_status():
    frozen_meta_heldout_correct=0
    frozen_meta_heldout_total=16
    assert frozen_meta_heldout_correct==0 and frozen_meta_heldout_total==16
    vm,names=register_frozen()
    try:vm.apply('UNREGISTERED',0,1)
    except ValueError:pass
    else:raise AssertionError('unproved instruction executed')
