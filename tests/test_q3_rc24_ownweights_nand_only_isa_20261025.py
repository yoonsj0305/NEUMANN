"""Q3 RC24: reject host-code injections; test learned TRUE runnable grammar."""
import sys,pathlib,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc24"))
from learned_nand_language import *

def test_auto_registered_dynamic_opcode_text_from_learned_nand_programs():
    machine,names=compiled_learned_instructions()
    assert names=={"xor":"AUTO_ce5d5a6bb041",
                   "and":"AUTO_9c0761f0ee85","or":"AUTO_d9745c5341f5"}
    for task,body in LEARNED_NAND_GRAMMAR.items():
        assert len(body)<=6
        assert parse_grammar(emit_grammar(body))[1]==body
        for x,y in itertools.product((0,1),repeat=2):
            assert machine.apply(names[task],x,y)==TASK_SPEC[task](x,y)
    assert scoped_science_gate()["global_Q3"]=="OPEN"

def test_fulladder_uses_only_learned_ops_inherited_from_pyweights():
    machine,names=compiled_learned_instructions()
    count=0
    for n in range(1,7):
        for a in range(1<<n):
            for b in range(1<<n):
                assert add_assembled_by_researcher(machine,names,a,b,n)==a+b
                count+=1
    assert count==5460

def test_safety_unknown_and_separate_proof():
    machine,names=compiled_learned_instructions()
    for source in ("DEF A(a,b)\nEVAL x\nEND\n",
                   "DEF A(a,b)\nNAND 0 99\nEND\n",
                   "import os","DEF A(a,b)\nNAND 0 1\n"):
        assert machine.register(source,"xor")["status"]!="SCOPED_CERTIFIED"
    m=list(LEARNED_NAND_GRAMMAR["xor"])
    m[0]=(0,0)
    assert machine.register(emit_grammar(m),"xor")["status"]!="SCOPED_CERTIFIED"
    try:machine.apply("UNKNOWN",1,0)
    except ValueError:pass
    else:raise AssertionError("unregistered instruction accepted")
