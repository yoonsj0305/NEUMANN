"""Public coding development interface; no task-specific role vocabulary.

Static execution admission supplements the upstream EvalPlus reliability guard.
This is a bounded scientific execution surface, not a general Python sandbox.
"""
import ast


IMPORTS = {"math", "cmath", "collections", "functools", "itertools", "typing", "re",
           "heapq", "bisect", "statistics", "string", "fractions", "decimal", "operator"}
FORBIDDEN = {"eval", "exec", "compile", "open", "input", "__import__", "globals",
             "locals", "vars", "getattr", "setattr", "delattr", "breakpoint", "help"}


def public_view(task):
    return {key: task[key] for key in ("task_id", "prompt", "entry_point")}


def messages(task):
    return [{"role": "system", "content": "Implement the requested Python function. Return only complete Python source in one python code block. Preserve the function signature. Use only the Python standard library. Do not include tests or explanations."},
            {"role": "user", "content": task["prompt"]}]


def admit(source, entry_point):
    if type(source) is not str or not source or len(source) > 20000:
        raise ValueError("bounded nonempty source required")
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    if len(nodes) > 4000:
        raise ValueError("source AST limit exceeded")
    if not any(isinstance(node, ast.FunctionDef) and node.name == entry_point for node in tree.body):
        raise ValueError("entry function missing")
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                       else [node.module or ""])
            if (isinstance(node, ast.ImportFrom) and node.level) or any(module.split(".")[0] not in IMPORTS for module in modules):
                raise ValueError("import outside execution contract")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError("private attribute access")
        if isinstance(node, ast.Name) and (node.id in FORBIDDEN or node.id.startswith("__")):
            raise ValueError("dynamic/system operation outside contract")
        if isinstance(node, (ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await)):
            raise ValueError("nonlocal/asynchronous operation outside contract")
    return source
