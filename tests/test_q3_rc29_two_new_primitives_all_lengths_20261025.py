"""RC29c smallest regression of learned TWO-opcode semantics and grammar.
No claim that Python host or fold skeleton was autonomously invented.
"""
import itertools,pathlib,random,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc29"))
from joint_ownweight_language import OWN_LEARNED_PAIRS,CertifiedComposer,emit_from_own_weight_signs

def test_both_independent_own_weight_semantics_compile_and_generalize():
    for pair in OWN_LEARNED_PAIRS:
        host=CertifiedComposer()
        src=emit_from_own_weight_signs(*pair)
        r=host.register(src)
        assert r['status']=='SCOPED_CERTIFIED'
        name=r['name']
        for motif in ((1,0,1),(1,1,0),(0,1,1,0),(1,1,0,1)):
            for n in range(len(motif),11):
                for word in itertools.product((0,1),repeat=n):
                    expected=tuple(int(i>=len(motif)-1 and word[i-len(motif)+1:i+1]==motif) for i in range(n))
                    assert host.stream(name,word,motif)==expected
        g,rbits,init=pair
        assert all(rbits[2*s+g[2*a+b]]==s*int(a==b) for s in (0,1) for a in (0,1) for b in (0,1))

def test_unapproved_program_remains_unknown():
    h=CertifiedComposer()
    for g,r,init in OWN_LEARNED_PAIRS:
        source=emit_from_own_weight_signs(g,r,init)
        assert h.register(source.replace("INIT 1","INIT 0"))['status']=="UNKNOWN_NO_ALL_LENGTH_PROOF"
        assert h.register(source+"import os")['status']=="UNKNOWN_SYNTAX"
        try:h.compare("UNREGISTERED",(1,0),(1,0))
        except ValueError:pass
        else:raise AssertionError("unproven operator executed")
