"""FRESH registry for Q3 V2/V3 (MBPP + HumanEval), built BEFORE any task is run.

Selection is mechanical and decided here, not after looking at outcomes:
  T1 every test assert has the form  assert f(<literal>) == <literal>  with exactly ONE positional argument that
     is a list of ints, and an expected value that is an int, a bool or a list of ints (MBPP: test_list and
     challenge_test_list; HumanEval: every assert in check() that calls `candidate`, at least 2 of them);
  T2 the reference solution passes a static audit: imports only from ALLOWED; none of FORBIDDEN names; no
     attribute starting with "__";
No other criterion.  The task texts are not read by this script beyond these fields.

python research/q3/fresh/registry.py <mbpp.jsonl> <HumanEval.jsonl.gz> <commits.txt> <out.json>
"""
from __future__ import annotations
import ast, gzip, hashlib, json, sys

ALLOWED = {"math", "collections", "itertools", "heapq", "functools", "operator", "bisect", "re", "string",
           "statistics", "typing", "array"}
FORBIDDEN = {"open", "exec", "eval", "compile", "__import__", "input", "globals", "locals", "getattr", "setattr",
             "delattr", "vars", "breakpoint", "exit", "quit", "memoryview", "help"}


def lit(n):
    try:
        return ast.literal_eval(n)
    except Exception:
        return None


def intlist(v):
    return isinstance(v, list) and all(isinstance(e, int) and not isinstance(e, bool) for e in v)


def out_ok(v):
    return (isinstance(v, (int, bool)) and v is not None) or intlist(v)


def parse_assert(node, callee):
    """(arg, expected) if node is `assert callee(<intlist>) == <ok>`, else None."""
    if not isinstance(node, ast.Assert) or not isinstance(node.test, ast.Compare):
        return None
    c = node.test
    if len(c.ops) != 1 or not isinstance(c.ops[0], ast.Eq) or not isinstance(c.left, ast.Call):
        return None
    call = c.left
    if not isinstance(call.func, ast.Name) or (callee and call.func.id != callee) or len(call.args) != 1 or call.keywords:
        return None
    a, y = lit(call.args[0]), lit(c.comparators[0])
    if intlist(a) and out_ok(y):
        return call.func.id, a, y
    return None


def audit(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "syntax"
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            if any(a.name.split(".")[0] not in ALLOWED for a in n.names):
                return "import"
        if isinstance(n, ast.ImportFrom):
            if (n.module or "").split(".")[0] not in ALLOWED:
                return "import"
        if isinstance(n, ast.Name) and n.id in FORBIDDEN:
            return "forbidden name " + n.id
        if isinstance(n, ast.Attribute) and n.attr.startswith("__"):
            return "dunder attribute"
    return None


def mbpp(path):
    out, why = [], {}
    for line in open(path):
        d = json.loads(line)
        tests = d["test_list"] + d.get("challenge_test_list", [])
        parsed = []
        for t in tests:
            try:
                node = ast.parse(t.strip()).body[0]
            except Exception:
                node = None
            p = parse_assert(node, None) if node is not None else None
            parsed.append(p)
        if not parsed or None in parsed or len({p[0] for p in parsed}) != 1:
            why[d["task_id"]] = "T1"
            continue
        a = audit(d["code"])
        if a:
            why[d["task_id"]] = "T2 " + a
            continue
        out.append({"id": "mbpp/%d" % d["task_id"], "entry": parsed[0][0], "code": d["code"],
                    "tests": [[p[1], p[2]] for p in parsed]})
    return out, why


def humaneval(path):
    out, why = [], {}
    for line in gzip.open(path, "rt"):
        d = json.loads(line)
        try:
            tree = ast.parse(d["test"])
        except SyntaxError:
            why[d["task_id"]] = "T1"
            continue
        check = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "check"), None)
        asserts = [n for n in ast.walk(check) if isinstance(n, ast.Assert)] if check else []
        calls = [n for n in asserts if any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "candidate"
                                           for c in ast.walk(n))]
        parsed = [parse_assert(n, "candidate") for n in calls]
        if len(parsed) < 2 or None in parsed:
            why[d["task_id"]] = "T1"
            continue
        code = d["prompt"] + d["canonical_solution"]
        a = audit(code)
        if a:
            why[d["task_id"]] = "T2 " + a
            continue
        out.append({"id": "humaneval/%s" % d["task_id"].split("/")[1], "entry": d["entry_point"], "code": code,
                    "tests": [[p[1], p[2]] for p in parsed]})
    return out, why


def main(mbpp_path, he_path, commits, out_path):
    gr, he = open(commits).read().split()
    m, wm = mbpp(mbpp_path)
    h, wh = humaneval(he_path)
    tasks = m + h
    reg = {"schema": "neumann.q3-fresh-registry.v1",
           "sources": {"mbpp": {"repo": "google-research/google-research", "commit": gr, "path": "mbpp/mbpp.jsonl",
                                "sha256": hashlib.sha256(open(mbpp_path, "rb").read()).hexdigest(),
                                "license": "repository Apache-2.0; dataset card CC-BY-4.0"},
                       "humaneval": {"repo": "openai/human-eval", "commit": he, "path": "data/HumanEval.jsonl.gz",
                                     "sha256": hashlib.sha256(open(he_path, "rb").read()).hexdigest(), "license": "MIT"}},
           "selection_rule": __doc__.split("Selection is mechanical")[1].split("python research")[0].strip(),
           "allowed_imports": sorted(ALLOWED), "forbidden_names": sorted(FORBIDDEN),
           "selected": [t["id"] for t in tasks],
           "task_sha256": {t["id"]: hashlib.sha256(json.dumps(t, sort_keys=True).encode()).hexdigest() for t in tasks},
           "excluded_counts": {"mbpp": len(wm), "humaneval": len(wh)},
           "excluded_by_audit": sorted([k for k, v in wm.items() if v.startswith("T2")] + [k for k, v in wh.items() if v.startswith("T2")], key=str)}
    reg["registry_sha256"] = hashlib.sha256(json.dumps(reg, sort_keys=True).encode()).hexdigest()
    json.dump(reg, open(out_path, "w"), indent=1, sort_keys=True)
    json.dump(tasks, open(out_path.replace(".json", "_tasks.json"), "w"))
    print("selected", len(tasks), "mbpp", len(m), "humaneval", len(h), "excluded by audit", reg["excluded_by_audit"])


if __name__ == "__main__":
    main(*sys.argv[1:5])
