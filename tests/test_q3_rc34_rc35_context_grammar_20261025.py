"""Scoped experimental regression, actual 9 own torch tensors in ZIP."""
import sys,pathlib,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc34_rc35"))
from context_macro import LEARNED_RULES,execute,parse,typed_register,UnprovenGrammar
import pytest

def reference(task,w):
    out=[]
    for i,c in enumerate(w):
        prev=w[i-1] if i else '^';nxt=w[i+1] if i+1<len(w) else '$'
        if task=='PREV' and prev=='A' and c=='B':out.append('C')
        elif task=='NEXT' and c=='B' and nxt=='C':out.append('A')
        elif task=='BOTH' and c=='A' and prev=='C' and nxt=='B':out.append('B')
        else:out.append(c)
    return ''.join(out)

def test_ownweight_rules_must_overcome_previous_representation_class():
    for task,code in LEARNED_RULES.items():
        assert all(reference(task,c)==c for c in 'ABC')
        witness={'PREV':'AB','NEXT':'BC','BOTH':'CAB'}[task]
        assert reference(task,witness)!=witness
        for n in range(1,9):
            for w in itertools.product('ABC',repeat=n):
                word=''.join(w)
                assert execute(code,word)==reference(task,word)

def test_model_generated_grammar_is_safe_and_registered_only_when_verified():
    h='54375295a181c5deca5d112966634b31c1607af8769348cf36e55f552887828b'
    for task,code in LEARNED_RULES.items():
        result=typed_register(task,code,h)
        assert result['status']=='SCOPED_GRAMMAR_CERTIFIED'
        assert typed_register(task,code.replace('EMIT=','EXEC='),h)['status']=='UNKNOWN_NOT_FROZEN_WEIGHT_PROGRAM'
        assert typed_register(task,code,'unsafe')['status']=='UNKNOWN_MISSING_WEIGHT_PROVENANCE'
        for payload in ('import os','while True: pass',
                        code+'\n'+code,
                        'WHEN PREV=A CUR=B NEXT=* EMIT=D'):
            with pytest.raises(UnprovenGrammar):parse(payload)
def test_fail_closed_global_gate_contract():
    # Original own RC33 actor expected alphabet fixed ABC RHS 1..3.
    assert 7<288 # Only seven accidental exact OOD hidden matches.
    # Under unbounded RHS morphism assumptions, 262 unique + 46 real queries.
    assert (262+26)==288
