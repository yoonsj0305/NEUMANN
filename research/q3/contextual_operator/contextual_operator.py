"""Research-only Q3: promote literal recolor effects into example-bound operator parameters.

The operator BODY comes from an external generator. This deterministic compiler does NOT
invent the body or train neural weights. Python AST filtering is NOT an OS security jail.
"""
import ast
from functools import lru_cache

class UnknownContext(ValueError):pass

_SAFE={'len':len,'range':range,'next':next,'all':all,'max':max,'min':min,'set':set,'sorted':sorted,
       'sum':sum,'enumerate':enumerate,'abs':abs,'list':list,'tuple':tuple}
_BAD=(ast.Import,ast.ImportFrom,ast.While,ast.Global,ast.Nonlocal,ast.ClassDef,ast.Try,
      ast.With,ast.Raise,ast.Delete,ast.Await,ast.Yield,ast.YieldFrom)

def _check(tree):
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef):raise UnknownContext('One function required')
    for node in ast.walk(tree):
        if isinstance(node,_BAD) or isinstance(node,ast.Name) and node.id.startswith('__'):
            raise UnknownContext('Unsafe AST')
        if isinstance(node,ast.Attribute) and (node.attr!='append' or not isinstance(node.value,ast.Name)):
            raise UnknownContext('Unsafe attribute')
        if isinstance(node,ast.Call):
            good=isinstance(node.func,ast.Name) and node.func.id in _SAFE
            good|=isinstance(node.func,ast.Attribute) and node.func.attr=='append' and isinstance(node.func.value,ast.Name)
            if not good:raise UnknownContext('Unsafe call')

class _Lift(ast.NodeTransformer):
    def __init__(self):self.pairs=[]
    def visit_IfExp(self,node):
        self.generic_visit(node);c=node.test
        if (isinstance(c,ast.Compare) and len(c.ops)==1 and isinstance(c.ops[0],ast.Eq)
            and len(c.comparators)==1 and isinstance(c.left,ast.Name)
            and isinstance(c.comparators[0],ast.Constant) and type(c.comparators[0].value)==int
            and isinstance(node.body,ast.Constant) and type(node.body.value)==int
            and isinstance(node.orelse,ast.Name) and node.orelse.id==c.left.id
            and 1<=c.comparators[0].value<=9 and 1<=node.body.value<=9):
            pair=(c.comparators[0].value,node.body.value)
            if pair[0]!=pair[1]:
                self.pairs.append(pair)
                c.comparators[0]=ast.Name(id='src_color',ctx=ast.Load())
                node.body=ast.Name(id='dst_color',ctx=ast.Load())
        return node

def _foreground(g):
    if not g or any(len(row)!=len(g[0]) for row in g):raise UnknownContext('Bad grid')
    return {v for row in g for v in row if v!=0}

def infer_binding(demos):
    if len(demos)<2:raise UnknownContext('Need at least two examples')
    pairs=[]
    for d in demos:
        a,b=_foreground(d['input']),_foreground(d['output'])
        if len(a)!=1 or len(b)!=1:raise UnknownContext('Ambiguous palette')
        pairs.append((next(iter(a)),next(iter(b))))
    if len(set(pairs))!=1:raise UnknownContext('Contradictory palette examples')
    return pairs[0]

@lru_cache(maxsize=32)
def _template(source):
    t=ast.parse(source)
    _check(t)
    lifted=_Lift();t=lifted.visit(t)
    if len(set(lifted.pairs))>1:raise UnknownContext('Unidentifiable multiple mappings')
    if lifted.pairs:
        f=t.body[0]
        f.args.args.extend([ast.arg(arg='src_color'),ast.arg(arg='dst_color')])
        f.args.defaults.extend([ast.Constant(value=lifted.pairs[0][0]),ast.Constant(value=lifted.pairs[0][1])])
    ast.fix_missing_locations(t)
    scope={'__builtins__':_SAFE}
    exec(compile(t,'<q3-research-only>','exec'),scope,scope)
    return scope[t.body[0].name], bool(lifted.pairs)

def bind_operator(source,demos):
    f,lifted=_template(source)
    binding=infer_binding(demos) if lifted else ()
    def op(grid):return f(grid,*binding)
    if any(op(d['input'])!=d['output'] for d in demos):raise UnknownContext('Demonstration mismatch')
    return op
