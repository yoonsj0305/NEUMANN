"""RC32 compact CI proof and new-language execution smoke."""
import pathlib,sys,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc32"))
from rewrite_language import (MODEL_WEIGHT_EMITTED,register,emit,execute,
                              counts_by_matrix_power,strict_symbolic_certificate,GrammarRejected)

def test_model_code_truly_emits_executable_productions_and_heldouts():
    assert len(MODEL_WEIGHT_EMITTED)==3
    for task,gold in MODEL_WEIGHT_EMITTED.items():
        grammar=register(emit(gold))
        assert grammar==gold
        for word in ("A","ABC","CAC","BAAB"):
            for n in range(0,8):
                expanded=execute(grammar,word,n)
                assert counts_by_matrix_power(grammar,word,n)==tuple(expanded.count(c) for c in "ABC")
        assert strict_symbolic_certificate(grammar,gold).startswith("PROVED_")

def test_meta_language_string_rejection_and_unknown_certificate():
    sample=MODEL_WEIGHT_EMITTED[0]
    for bad in ('A ::= import os\nB ::= B\nC ::= C','A ::= D\nB ::= A\nC ::= A',
                'A ::= A\nB ::= B','A ::= A\nB ::= B\nB ::= C\nC ::= A',
                'A ::= AAAA\nB ::= B\nC ::= A'):
        try:register(bad)
        except GrammarRejected:pass
        else:raise AssertionError("invalid production admitted")
    changed=dict(sample);changed["B"]="BC"
    assert strict_symbolic_certificate(changed,sample)=="UNKNOWN_NOT_PROVEN"
    try:execute(sample,"ABC",1000)
    except GrammarRejected:pass
    else:raise AssertionError("unbounded materialization admitted")

def test_no_confusion_with_foundational_invention():
    assert MODEL_WEIGHT_EMITTED[0] != MODEL_WEIGHT_EMITTED[1]
    assert MODEL_WEIGHT_EMITTED[1] != MODEL_WEIGHT_EMITTED[2]
