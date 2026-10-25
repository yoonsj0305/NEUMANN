"""RC26 compact tests: actual extracted state syntax, not raw RNN training."""
import sys,pathlib,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'research'/'q3'/'rc26'))
from verified_grammar import *
def test_model_behavior_compiled_formal_all_lengths():
    for k in (3,5):
        name=f'mod{k}'
        assert admission(name)=='SCOPED_ALL_LENGTH_PASS'
        machine=parse(FROZEN_GRAMMAR[name])
        assert len(machine[1])==k
        for length in range(1,11):
            for seq in itertools.product((0,1),repeat=length):
                count=0;expected=[]
                for b in seq:
                    count=(count+b)%k;expected.append(int(count==0))
                assert run(machine,seq)==tuple(expected)

def test_wrong_prog_rejected_and_scope_stays_open():
    assert independent_product_proof(FROZEN_GRAMMAR['mod3'],5)!='SCOPED_ALL_LENGTH_PASS'
    assert admission('unseen_external')=='UNKNOWN_NEW_FAMILY'
    for change in ('READ 2','EVAL 0','OUT 3'):
        sample=FROZEN_GRAMMAR['mod5'].replace('READ 0',change,1)
        try:parse(sample)
        except ValueError:pass
        else:raise AssertionError('malformed program accepted')
    assert SCIENCE['model_autonomously_invents_base_ISA']=='OPEN'
    assert SCIENCE['GRU_all_length_certified'] is False
