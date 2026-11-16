"""Independent literal AST interpreter reused from PR #777, commit dd64cd5.
No Q3 compiler, task loader or discovery policy is imported.
"""
import re
CAP = 10 ** 18

class Undefined(Exception):
    pass


def parse_program(text):
    kind = "ast"
    if text.startswith("<"):
        m = re.fullmatch(r"<(zmap|zfilter) e=\$0 j=\$1 r=\$2 pre=\$3 suf=\$4 x=\$5 \| (.*)>", text)
        if not m:
            raise ValueError("unsupported program wrapper")
        kind, text = m.groups()
    tokens = re.findall(r"\(|\)|[^\s()]+", text)
    pos = 0

    def node():
        nonlocal pos
        if pos == len(tokens):
            raise ValueError("truncated program")
        t = tokens[pos]
        pos += 1
        if t == "(":
            if pos == len(tokens):
                raise ValueError("missing operator")
            op = tokens[pos]
            pos += 1
            children = []
            while pos < len(tokens) and tokens[pos] != ")":
                children.append(node())
            if pos == len(tokens):
                raise ValueError("unclosed program")
            pos += 1
            return (op, *children)
        if t.startswith("$"):
            return ("v", int(t[1:]))
        if re.fullmatch(r"-?\d+", t):
            return ("k", int(t))
        if t == "nil":
            return ("nil",)
        raise ValueError("unknown token " + t)

    ast = node()
    if pos != len(tokens):
        raise ValueError("trailing tokens")
    return kind, ast


def interpret(ast, env, meter=None):
    """Literal substrate semantics, independent of the production closures.

    Failure is an exception until the public boundary; if is lazy. All integer
    arithmetic and cons/range caps reproduce the declared substrate domain.
    """
    if meter is not None:
        meter[0] += 1
    op, *cs = ast
    if op == "v":
        return env[cs[0]]
    if op == "k":
        return cs[0]
    if op == "nil":
        return ()
    if op in ("ifI", "ifL"):
        return interpret(cs[1] if interpret(cs[0], env, meter) else cs[2], env, meter)
    if op.startswith("fold"):
        body, init, xs = cs
        acc = interpret(init, env, meter)
        seq = interpret(xs, env, meter)
        if op not in ("foldrI", "foldlI", "foldrL", "foldlL"):
            raise ValueError("unknown fold")
        for x in (reversed(seq) if op.startswith("foldr") else seq):
            acc = interpret(body, (*env, x, acc), meter)
        return acc
    if op in ("map", "filter"):
        seq = interpret(cs[1], env, meter)
        if op == "map":
            return tuple(interpret(cs[0], (*env, x), meter) for x in seq)
        return tuple(x for x in seq if interpret(cs[0], (*env, x), meter))
    vs = [interpret(c, env, meter) for c in cs]
    if op in ("add", "sub", "mul"):
        a, b = vs
        r = a + b if op == "add" else a - b if op == "sub" else a * b
        if abs(r) > CAP:
            raise Undefined()
        return r
    if op in ("div", "mod"):
        a, b = vs
        if b <= 0:
            raise Undefined()
        return a // b if op == "div" else a % b
    if op == "cons":
        if len(vs[1]) >= 40:
            raise Undefined()
        return (vs[0],) + vs[1]
    if op in ("head", "tail"):
        if not vs[0]:
            raise Undefined()
        return vs[0][0] if op == "head" else vs[0][1:]
    if op == "range":
        if not 0 <= vs[0] <= 40:
            raise Undefined()
        return tuple(range(vs[0]))
    if op == "eq":
        return vs[0] == vs[1]
    if op == "lt":
        return vs[0] < vs[1]
    if op == "not":
        return not vs[0]
    if op == "isnil":
        return not vs[0]
    raise ValueError("unknown substrate operator " + op)


def execute(sol, inputs, meter=None):
    try:
        kind, ast = sol
        if kind == "ast":
            return interpret(ast, tuple(inputs), meter)
        x, = inputs
        out = []
        for j, v in enumerate(x):
            state = (v, j, len(x) - j - 1, x[:j][::-1], x[j + 1:], x)
            y = interpret(ast, state, meter)
            if kind == "zmap":
                out.append(y)
            elif kind == "zfilter":
                if y:
                    out.append(v)
            else:
                raise ValueError("unknown method kind")
        return tuple(out)
    except Undefined:
        return None


