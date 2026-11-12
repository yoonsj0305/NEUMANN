"""Independent audit of opened invention iteration 2; never a new Q3 gate.

Only reproduce() imports the production solver. Parsing, execution, loading,
coverage validation and scoring deliberately share no production implementation.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import itertools
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
ARMS = ("S", "V0", "V")
PINS = {"rule": "092b196c1f8f14a54bbc62f24759d43bde46dd3b",
        "dc": "cb0e63f5c33cd2de360b791038b0f5272750270e"}
RULE_DIR = "bigbench/benchmark_tasks/list_functions"
CAP = 10 ** 18


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def sha_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def read_rows(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as f:
        return [json.loads(line) for line in f if line.strip()]


def validate_rows(rows, expected):
    """Reject invalid cohorts BEFORE a statistical or cost comparison."""
    keys = set()
    allowed = {(a, i) for a in ARMS for i in expected}
    for r in rows:
        k = (r.get("arm"), r.get("id"))
        if k not in allowed:
            raise ValueError("unregistered arm/id: %r" % (k,))
        if k in keys:
            raise ValueError("duplicate row: %r" % (k,))
        keys.add(k)
        for field in ("fit", "solved"):
            if type(r.get(field)) is not bool:
                raise ValueError("non-boolean " + field)
        c = r.get("cpu_seconds")
        if type(c) not in (int, float) or not math.isfinite(c) or c < 0:
            raise ValueError("invalid CPU")
        if r["solved"] and not r["fit"]:
            raise ValueError("solved without fit")
        if r["fit"] != (r.get("program") is not None):
            raise ValueError("fit/program inconsistency")
    if keys != allowed:
        raise ValueError("incomplete cohort: missing %d rows" % len(allowed - keys))
    return {(r["arm"], r["id"]): r for r in rows}


def paired_p(w, l):
    n = w + l
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(w, l) + 1)) / 2 ** n)


def rescore(rows, expected):
    by = validate_rows(rows, expected)
    out = {}
    for family in sorted({i.split("/")[0] for i in expected}):
        ids = {i for i in expected if i.startswith(family + "/")}
        solved = {a: {i for i in ids if by[a, i]["solved"]} for a in ARMS}
        cpu = {a: math.fsum(by[a, i]["cpu_seconds"] for i in ids) for a in ARMS}
        w, l = len(solved["V"] - solved["V0"]), len(solved["V0"] - solved["V"])
        exclusive = sorted(solved["V"] - solved["V0"] - solved["S"])
        p = paired_p(w, l)
        passed = {"J1": w >= 5 and p < 0.025, "J2": len(exclusive) >= 5,
                  "J3": cpu["V"] <= cpu["V0"]}
        out[family] = {"tasks": len(ids), "solved": {a: len(s) for a, s in solved.items()},
                       "fit": {a: sum(by[a, i]["fit"] for i in ids) for a in ARMS},
                       "cpu_seconds": cpu, "V_only": w, "V0_only": l,
                       "mcnemar_p": p, "exclusive": exclusive, "criterion_pass": passed,
                       "pass": all(passed.values())}
    return out


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


def _git(clone, *args):
    return subprocess.check_output(["git", "-C", str(clone), *args])


def _blob(clone, pin, path, manifest):
    raw = _git(clone, "show", pin + ":" + path)
    blob = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()
    actual = _git(clone, "rev-parse", pin + ":" + path).decode().strip()
    if blob != actual:
        raise ValueError("original blob mismatch")
    manifest.append({"commit": pin, "path": path, "blob_sha1": blob,
                     "sha256": hashlib.sha256(raw).hexdigest()})
    return json.loads(raw)


def _v(v):
    if isinstance(v, str):
        return _v(json.loads(v))
    if type(v) is list:
        return tuple(_v(x) for x in v)
    return v


def original_tasks(rule_clone, dc_clone, rule_ids):
    """Only opened rule IDs + the previously opened dc file. No registry import."""
    manifest, tasks = [], {}

    def task(tid, ti, to, ex):
        n = len(ex)
        cut = 8 if n >= 12 else math.ceil(2 * n / 3)
        return {"id": tid, "in_types": [ti], "out_type": to,
                "train": ex[:cut], "test": ex[cut:]}

    for tid in sorted(rule_ids):
        name = tid.split("/")[1]
        d = _blob(rule_clone, PINS["rule"], RULE_DIR + "/" + name + "/task.json", manifest)
        ex = []
        for e in d["examples"]:
            y = e["target"]
            if isinstance(y, list) and y and isinstance(y[0], str):
                y = y[0]
            ex.append(((_v(e["input"]),), _v(y)))
        tasks[tid] = task(tid, "L", "L", ex)
    data = _blob(dc_clone, PINS["dc"], "data/list_tasks.json", manifest)
    types = {"int": "I", "bool": "B", "list-of-int": "L"}
    for i, item in enumerate(data):
        ti, to = item["type"]["input"], item["type"]["output"]
        if ti not in ("int", "list-of-int") or to not in types:
            continue
        ex = [((_v(e["i"]),), bool(e["o"]) if to == "bool" else _v(e["o"]))
              for e in item["examples"]]
        tid = "dc/%03d" % i
        tasks[tid] = task(tid, types[ti], types[to], ex)
    return tasks, manifest


def replay(rows, tasks):
    mismatches, evaluations, fit_count, solved_count = [], 0, 0, 0
    prediction_digest = hashlib.sha256()
    for row in sorted(rows, key=lambda r: (r["id"], r["arm"])):
        task = tasks[row["id"]]
        fit, solved = False, False
        if row["program"] is not None:
            sol = parse_program(row["program"])
            predictions = {}
            for split in ("train", "test"):
                predictions[split] = [execute(sol, i) for i, _ in task[split]]
                evaluations += len(task[split])
            fit = all(type(p) is type(y) and p == y for p, (_, y) in zip(predictions["train"], task["train"]))
            solved = fit and all(type(p) is type(y) and p == y
                                 for p, (_, y) in zip(predictions["test"], task["test"]))
            prediction_digest.update(digest([row["arm"], row["id"], predictions]).encode())
        fit_count += fit
        solved_count += solved
        if (fit, solved) != (row["fit"], row["solved"]):
            mismatches.append({"arm": row["arm"], "id": row["id"],
                               "recorded": [row["fit"], row["solved"]], "independent": [fit, solved]})
    return {"rows": len(rows), "example_evaluations": evaluations, "fit": fit_count,
            "solved": solved_count, "mismatches": mismatches,
            "predictions_sha256": prediction_digest.hexdigest()}


def fake_unpaired_rows():
    return [dict(arm=a, id="%s/%s%d" % (f, a, i), fit=a == "V", solved=a == "V",
                 program="nil" if a == "V" else None, cpu_seconds=1.0, via="fixture")
            for f in ("rule", "dc") for a in ARMS for i in range(7)]


def controls():
    bad = fake_unpaired_rows()
    expected = {r["id"] for r in bad if r["arm"] == "V"}
    try:
        validate_rows(bad, expected)
    except ValueError as e:
        return {"disjoint_equal_count_cohort_rejected": True, "reason": str(e)}
    return {"disjoint_equal_count_cohort_rejected": False}


def reproduce_job(payload, queue):
    """No original TEST or expected future value enters this process."""
    sys.path.insert(0, str(ROOT))
    from neumann1 import invention_core as ic, inverted as iv, spec_core as sc
    task, arm, spec, ops = payload
    assert task["test"] == ()
    inv = sc.load_inverses(str(ROOT / sc.INVERSES))
    c0, w0 = time.process_time(), ic.WORK[0]
    result = sc.solve(task, 6, "S", inv) if arm == "S" else iv.solve(
        task, 6, inv, spec, ops if arm == "V" else {})
    elapsed, work = time.process_time() - c0, ic.WORK[0] - w0
    sol = result.get("sol")
    queue.put({"id": task["id"], "arm": arm, "program": result["program"],
               "sol": sol, "via": result["via"], "candidates": result["candidates"],
               "cpu_seconds": elapsed, "substrate_work": work,
               "train_only_discovery": True})


def reproduce(tasks, published_rows, destination):
    import multiprocessing as mp
    sys.path.insert(0, str(ROOT))
    from neumann1 import inverted as iv
    spec = json.loads((ROOT / "docs/experiments/results/invention_core_frozen.json").read_text())["spec"]
    derive0 = time.process_time()
    ops = iv.derive_op_inverses(spec)
    derive_cpu = time.process_time() - derive0
    by = {(r["arm"], r["id"]): r for r in published_rows}
    selected = sorted(i for i in tasks if by["V", i]["solved"] and not by["V0", i]["solved"])
    assert len(selected) == 12, "unexpected published discordance count"
    jobs = []
    for i in selected:
        t = {k: v for k, v in tasks[i].items() if k != "test"}
        t["test"] = ()
        for a in ARMS:
            jobs.append((t, a, spec, ops))
    ctx = mp.get_context("spawn")
    running, results = {}, []
    # Each child has a separate queue so one terminating worker cannot affect another.
    while jobs or running:
        while jobs and len(running) < 2:
            pld = jobs.pop(0)
            q = ctx.Queue()
            p = ctx.Process(target=reproduce_job, args=(pld, q))
            p.start()
            running[p] = (q, pld[0]["id"], pld[1], time.monotonic())
        for p, (q, tid, arm, start) in list(running.items()):
            try:
                result = q.get_nowait()
            except __import__("queue").Empty:
                result = None
            if result is not None:
                results.append(result)
                p.join(timeout=1)
                if p.is_alive():
                    p.terminate()
                    p.join()
                q.close()
                del running[p]
            elif time.monotonic() - start > 30 or (not p.is_alive() and p.exitcode):
                p.terminate() if p.is_alive() else None
                p.join()
                results.append({"id": tid, "arm": arm, "error": "TIMEOUT_OR_WORKER_FAILURE", "exitcode": p.exitcode})
                q.close()
                del running[p]
        time.sleep(0.02)
    results.sort(key=lambda r: (r["id"], r["arm"]))
    # Freeze submitted programs AND predictions before any reproduction grading.
    for r in results:
        if "error" not in r:
            sol = parse_program(r["program"]) if r["program"] is not None else None
            r["predictions"] = {
                split: [execute(sol, i) for i, _ in tasks[r["id"]][split]] if sol else []
                for split in ("train", "test")}
    program_path = destination / "reproduction_programs.json"
    program_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    with program_path.open("rb") as f:
        os.fsync(f.fileno())
    commitment = sha_file(program_path)
    grades = []
    for r in results:
        if "error" in r:
            grades.append(dict(r, independent_fit=False, independent_solved=False))
            continue
        t = tasks[r["id"]]
        preds = r["predictions"]
        def exact(split):
            return r["program"] is not None and all(type(p) is type(y) and p == y
                                           for p, (_, y) in zip(preds[split], t[split]))
        fit = exact("train")
        grades.append(dict(r, independent_fit=fit, independent_solved=fit and exact("test"), predictions=preds))
    # This is a postselected reproduction. Do not use a significance test here.
    summary = {a: {"solved": sum(r.get("independent_solved", False) for r in grades if r["arm"] == a),
                   "cpu_seconds": math.fsum(r.get("cpu_seconds", 0) for r in grades if r["arm"] == a),
                   "candidates": sum(r.get("candidates", 0) for r in grades if r["arm"] == a),
                   "substrate_work": sum(r.get("substrate_work", 0) for r in grades if r["arm"] == a)} for a in ARMS}
    return {"selected_ids": selected, "selection": "published V-only; postselected development reproduction",
            "cap_process_cpu_seconds": 6, "wall_cap_seconds": 30, "workers": 2,
            "inverse_derivation_cpu_seconds": derive_cpu, "ops": ops,
            "program_commitment_sha256": commitment, "rows": grades, "summary": summary,
            "failures": [r for r in grades if "error" in r]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-clone", required=True)
    ap.add_argument("--dc-clone", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reproduce", action="store_true")
    args = ap.parse_args()
    dest = pathlib.Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    row_path = ROOT / "docs/experiments/results/discovery_iter2_rows.jsonl.gz"
    rows = read_rows(row_path)
    # Rule IDs reconstructed from the original salted split, independently.
    all_rule = ["rule/c%03d" % i for i in range(1, 251)]
    salt = "neumann-invention-first-v1"
    def sortkey(tid):
        path = RULE_DIR + "/" + tid.split("/")[1] + "/task.json"
        return hashlib.sha256((salt + ":rule:" + path).encode()).hexdigest()
    rule_ids = set(sorted(all_rule, key=sortkey)[125:])
    tasks, manifest = original_tasks(args.rule_clone, args.dc_clone, rule_ids)
    assert len(rule_ids) == 125 and len(tasks) == 324
    score = rescore(rows, set(tasks))
    r = replay(rows, tasks)
    result = {"schema": "neumann.independent-invention-audit.v1", "base_commit": "0d1baec723f249a62a901d100af6e941234a43ac",
              "prereg_sha256": sha_file(ROOT / "docs/research/INDEPENDENT_INVENTION_AUDIT_PREREG_2026_11_12.md"),
              "auditor_sha256": sha_file(__file__), "historical_rows_sha256": sha_file(row_path),
              "originals": manifest, "paired_scoring": score, "independent_replay": r, "controls": controls(),
              "scientific_iteration2_pass": all(f["pass"] for f in score.values()),
              "global_Q1_Q7": "OPEN; this audit does not close global capability or cost gates"}
    result["audit_checks_pass"] = not r["mismatches"] and result["controls"]["disjoint_equal_count_cohort_rejected"]
    (dest / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("paired_scoring", "independent_replay", "controls", "audit_checks_pass")}, indent=2), flush=True)
    if args.reproduce:
        rep = reproduce(tasks, rows, dest)
        (dest / "reproduction.json").write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"reproduction": rep["summary"], "failures": rep["failures"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
