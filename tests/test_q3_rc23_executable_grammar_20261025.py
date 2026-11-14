"""RC23.1 modeled syntax MUST actually parse and execute; negative controls."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc23"))
from grammar_host import run_generated_grammar,RejectSyntax

def test_model_defined_new_grammar_executes():
    p='''\nt=MAKE(3)\nt=WRITE(t,1)\nt=WRITE(t,2)\nleft,t=READ_FRONT(t)\nright,t=READ_BACK(t)\ndone=EXHAUSTED(t)\nmatch=MATCH(left,1)\n'''
    e=run_generated_grammar(p)
    assert (e["left"],e["right"],e["done"],e["match"])==(1,2,1,1)

def test_unknown_or_host_language_splice_blocked():
    for p in ("x=NOT_AN_INSTRUCTION(2)",
              "x=__import__('os')",
              "x=MAKE(2)\ny=x.__class__",
              "x=MAKE(2)\nwhile True:\n    x=WRITE(x,1)",
              "x=MAKE(2)\ny=WRITE(x,True)",
              "_private=MAKE(2)",
              "x=MAKE(2)\ny=WRITE(x,5)"):
        try:run_generated_grammar(p)
        except RejectSyntax:pass
        else:raise AssertionError("untrusted syntax entered host runtime")
