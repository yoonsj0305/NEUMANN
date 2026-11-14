"""RC30 compact own-weight model-generated two-stage syntax regression."""
import sys,pathlib,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc30"))
from joint_language import FROZEN,name,emit,parse,run,prove,authorize

def test_both_generated_instruction_and_loop_definitions():
    assert name([1,0,0,1])=="OP_afa751810630"
    assert name([0,0,0,1])=="OP_b40711a88c70"
    assert name([0,1,1,0])=="OP_d5e2d2ac07b7"
    assert name([1,0,1,1])=="OP_52a5c4a10657"
    for task,code in FROZEN.items():
        text=emit(code)
        assert parse(text)==code
        assert authorize(text,task)=="SCOPED_CERTIFIED"
        assert prove(code,task)=="SCOPED_ALL_FINITE_LENGTHS"

def test_unseen_widths_and_complete_short_cases():
    for n in range(1,8):
        for x in range(1<<n):
            xb=tuple((x>>j)&1 for j in range(n))
            for y in range(1<<n):
                yb=tuple((y>>j)&1 for j in range(n))
                goal_all=int(x==y)
                goal_any=int(any(a==b for a,b in zip(xb,yb)))
                assert run(FROZEN["all_equal"],xb,yb)==goal_all
                assert run(FROZEN["any_equal"],xb,yb)==goal_any

def test_fail_closed_and_semantic_mutations():
    for task,code in FROZEN.items():
        source=emit(code)
        for replaced in (source.replace("EMIT","EXEC"),
                         source.replace("INITIAL 1","INITIAL 3"),
                         source.replace("EACH_PAIR","PYTHON_IMPORT"),
                         "import os"):
            if replaced!=source:assert authorize(replaced,task)=="UNKNOWN_BAD_GRAMMAR"
        for slot in ("compare","reduce"):
            for index in range(4):
                mutant={k:(list(v) if isinstance(v,list) else v) for k,v in code.items()}
                mutant[slot][index]^=1
                assert prove(mutant,task)=="FAIL"
