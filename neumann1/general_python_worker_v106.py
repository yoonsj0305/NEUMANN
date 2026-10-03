"""Resource-capped pure Python subset worker. Not a general Python sandbox."""
import ast
import json
try:
    import resource
except ImportError:  # Windows
    resource = None
import sys

BUILTINS = {"sum": sum, "len": len, "min": min, "max": max, "abs": abs,
            "range": range, "enumerate": enumerate, "zip": zip, "sorted": sorted,
            "reversed": reversed, "list": list, "set": set, "dict": dict,
            "int": int, "bool": bool, "all": all, "any": any}
ALLOWED = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return,
    ast.Assign, ast.AugAssign, ast.If, ast.For, ast.While, ast.Break, ast.Continue,
    ast.Expr, ast.Pass, ast.Name, ast.Load, ast.Store, ast.Constant, ast.Call,
    ast.keyword, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp,
    ast.List, ast.Tuple, ast.Dict, ast.Set, ast.Subscript, ast.Slice,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.UAdd, ast.USub,
    ast.Not, ast.And, ast.Or, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn)


def execute(data):
    source = data["source"]
    args = data["arguments"]
    if type(source) is not str or len(source) > 8192 or type(args) is not list or len(args) > 64:
        raise ValueError("bounded source and input cases required")
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    if len(nodes) > 1024 or any(not isinstance(n, ALLOWED) for n in nodes):
        raise ValueError("unsupported Python subset")
    definitions = [n for n in nodes if isinstance(n, ast.FunctionDef)]
    if len(tree.body) != 1 or len(definitions) != 1 or tree.body[0] is not definitions[0]:
        raise ValueError("one pure solve function required")
    fn = definitions[0]
    if (fn.name != "solve" or fn.decorator_list or len(fn.args.args) != 1
            or fn.args.args[0].arg != "items" or fn.args.defaults or fn.args.kwonlyargs
            or fn.args.posonlyargs or fn.args.vararg or fn.args.kwarg or fn.returns):
        raise ValueError("exact solve(items) signature required")
    for n in nodes:
        if isinstance(n, ast.Name) and n.id.startswith("_"):
            raise ValueError("private names forbidden")
        if isinstance(n, ast.Call) and (not isinstance(n.func, ast.Name)
                or n.func.id not in set(BUILTINS) | {"solve"}):
            raise ValueError("pure allowed calls only")
        if isinstance(n, ast.Constant) and type(n.value) not in (int, str, bool, type(None)):
            raise ValueError("bounded literal types only")
    namespace = {"__builtins__": BUILTINS}
    exec(compile(tree, "<model-program>", "exec"), namespace)
    return [namespace["solve"](value) for value in args]


def main():
    # Unix gets kernel-enforced caps. Windows has no stdlib resource module;
    # the parent still enforces a hard subprocess timeout and this worker keeps
    # the same AST/builtin/input/output restrictions.
    if resource is not None:
        resource.setrlimit(resource.RLIMIT_CPU, (1, 2))
        resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
    try:
        raw = sys.stdin.read(100001)
        if len(raw) > 100000: raise ValueError("input byte cap")
        outputs = execute(json.loads(raw))
        result = json.dumps({"ok": True, "outputs": outputs}, allow_nan=False)
        if len(result) > 65536: raise ValueError("output byte cap")
        print(result)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__ + ": " + str(exc)}))


if __name__ == "__main__": main()
