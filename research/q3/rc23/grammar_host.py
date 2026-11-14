"""RC23 minimal host for ACTUALLY executing new model-generated grammar.

The HOST interpreter is written AFTER the GPT-6 source proposal SHA freeze.
It does not imply the local NEUMANN weights invented this interpreter.
"""
import ast
from generated_language import Packed,NEW_LANGUAGE_SYNTAX

ALLOWED={v.split("(",1)[0] for rules in NEW_LANGUAGE_SYNTAX.values() for v in rules}
def _make(k):return Packed.make(k)
def _write(t,x):return t.write(x)
def _front(t):return t.take_front()
def _back(t):return t.take_back()
def _match(a,b):return int(a==b)
def _empty(t):return int(t.n==0)
DISPATCH={"MAKE":_make,"WRITE":_write,"READ_FRONT":_front,
          "READ_BACK":_back,"MATCH":_match,"EXHAUSTED":_empty}
assert set(DISPATCH)==ALLOWED

class RejectSyntax(Exception):pass

def run_generated_grammar(source,max_commands=500):
    try:program=ast.parse(source)
    except SyntaxError as e:raise RejectSyntax("not a valid program") from e
    if len(program.body)>max_commands:raise RejectSyntax("budget")
    env={}
    def val(z):
        if isinstance(z,ast.Name):
            if z.id not in env:raise RejectSyntax("unbound")
            return env[z.id]
        if isinstance(z,ast.Constant) and type(z.value)==int:return z.value
        raise RejectSyntax("unapproved argument")
    def bind(z,v):
        if isinstance(z,ast.Name):
            if z.id.startswith("_"):raise RejectSyntax("reserved")
            env[z.id]=v
        elif isinstance(z,ast.Tuple):
            if type(v)!=tuple or len(z.elts)!=len(v):raise RejectSyntax("arity")
            for a,b in zip(z.elts,v):bind(a,b)
        else:raise RejectSyntax("target")
    for st in program.body:
        if type(st)!=ast.Assign or len(st.targets)!=1 or type(st.value)!=ast.Call:
            raise RejectSyntax("only assignments from opcodes")
        call=st.value
        if type(call.func)!=ast.Name or call.keywords or call.func.id not in ALLOWED:
            raise RejectSyntax("not a declared opcode")
        try:v=DISPATCH[call.func.id](*(val(a) for a in call.args))
        except (TypeError,ValueError,AttributeError) as e:
            raise RejectSyntax("contract violation") from e
        bind(st.targets[0],v)
    return env
