"""L2b-0 R (stage3/DESIGN.md 11.5-3, 11.7, 11.10-1): the hand-composed programs multi_add and mulNM (stage3/recomb.py,
unchanged language and programs) run with the admitted H' table modules (stage3/l2b_hprime.py).

Admitted module per function (11.10; 11.7-4 rule "several pass -> the smallest", here the smallest table number):
the first of tables 1, 2, 3 whose H' final.json has admission_checks_pass and M_all_1.000.
Bins (11.5-3 + 11.7 + 11.10-1), each from its own generation seed "L2b-0:R:<task>:<bin>":
  mulNM: n, m in-distribution 1-10, out of distribution 11-20 / 21-30 / 31-50 (500 each), 51-100 (200);
  multi_add: (k 2-5, digits 1-10), (k 6-10, 11-20), (k 11-20, 21-30), (k 21-40, 31-50) (500 each).
  Draw (recorded; as recomb.composite_example): n, m and every operand's digit count independent uniform in the bin,
  k uniform; numbers canonical (no leading zero).
A module call that meets a key not in T_S stops; the example is then wrong (recorded as "missing key").
mulNM 51-100 calls add on operands up to ~200 digits, beyond the add module's checked range (closure 4-100, M 1-100):
that bin rests on the H' argument (11.7) only.

  run --task multi_add|mulNM
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np                                                   # noqa: E402

OUT = pathlib.Path(os.environ.get("L2B_R_OUT", HERE / "results" / "L2b-0" / "R"))
HP = HERE / "results" / "L2b-0" / "Hprime"
BINS = {"mulNM": [("id_1-10", 1, 10, None, 500), ("ood_11-20", 11, 20, None, 500), ("ood_21-30", 21, 30, None, 500),
                  ("ood_31-50", 31, 50, None, 500), ("ood_51-100", 51, 100, None, 200)],
        "multi_add": [("id_k2-5_1-10", 1, 10, (2, 5), 500), ("ood_k6-10_11-20", 11, 20, (6, 10), 500),
                      ("ood_k11-20_21-30", 21, 30, (11, 20), 500), ("ood_k21-40_31-50", 31, 50, (21, 40), 500)]}


def admitted(module):
    for i in (1, 2, 3):
        f = HP / ("%s_table%d" % (module, i)) / "final.json"
        if f.exists():
            r = json.loads(f.read_text())
            if r.get("admission_checks_pass") and r.get("M_all_1.000"):
                return i, r
    return None, None


class TableModule:
    def __init__(self, module, i):
        import l2b_h as H
        import l2b_hprime as HPm
        import tasks as T
        self.module, self.i = module, i
        self.table = H.table_of(module, i)
        z = np.load(HP / ("%s_table%d" % (module, i)) / "T_S.npz")
        self.ky, self.out, self.cols = z["keys"], z["out"], [int(c) for c in z["cols"]]
        train = T.train_set(H.MODULE_TASK[module], 100000, HPm.data_seed(i))
        F, Y, _ = HPm.features_ids(train, self.table)
        self.coder = HPm.Coder(F)
        k = self.coder.key(self.coder.codes(F), self.cols)
        ky, out = HPm.build_table(k, Y)
        assert np.array_equal(ky, self.ky) and np.array_equal(out, self.out)    # same T_S as the H' run

    def __call__(self, prompts):
        """prompts: token strings ending with '=' -> [(answer strings, status)]"""
        import l2b_hprime as HPm
        import tasks as T
        ids = [[T.TOK[t] for t in p] for p in prompts]
        mx = max(len(p) for p in prompts) + 2
        dec = HPm.table_decode(ids, self.table, self.coder, self.cols, self.ky, self.out, max_new=mx)
        return [([T.VOCAB[v] for v in o], st) for o, st in dec]


def execute(program, prompts, backends):
    """recomb.execute with per-example module-failure flags"""
    import recomb as RC
    n = len(prompts)
    gens, req, out = [], {}, [None] * n
    calls = [{m: 0 for m in backends} for _ in range(n)]
    fail = [None] * n

    def advance(i, value):
        try:
            req[i] = gens[i].send(value)
        except StopIteration as e:
            out[i] = e.value
    for i, p in enumerate(prompts):
        assert p[-1] == "="
        gens.append(program(p[:-1]))
        advance(i, None)
    while req:
        by = {}
        for i, (m, args) in req.items():
            by.setdefault(m, []).append((i, RC.FORMAT[m](*args)))
        req = {}
        for m, items in by.items():
            ans = backends[m]([q for _, q in items])
            for (i, _), (a, st) in zip(items, ans):
                calls[i][m] += 1
                if st != "ok":
                    if fail[i] is None:
                        fail[i] = "%s:%s" % (m, st)
                    out[i] = None
                    gens[i].close()
                    continue
                advance(i, a)
    return out, calls, fail


def example(task, rng, lo, hi, k):
    import recomb as RC
    return RC.composite_example(task, rng, lo, hi, k)


def cmd_run(a):
    import h0a
    import l2b_h as H
    import recomb as RC
    H._setup("mul1")
    t00 = time.time()
    d = OUT / a.task
    d.mkdir(parents=True, exist_ok=True)
    mods = {}
    for m in ("add", "mul1") if a.task == "mulNM" else ("add",):
        i, r = admitted(m)
        assert i is not None, "no admitted H' module for %s" % m
        mods[m] = (i, r["S"]["config"])
    (d / "config.json").write_text(json.dumps({
        "design": "stage3/DESIGN.md 11.5-3, 11.7, 11.10-1", "task": a.task, "program": "stage3/recomb.py %s" % a.task,
        "modules": {m: {"H'_table": i, "S": s} for m, (i, s) in mods.items()},
        "bins": BINS[a.task], "generation_seed": "L2b-0:R:%s:<bin label>" % a.task,
        "draw": "recomb.composite_example: n, m and every operand's digit count independent uniform in the bin, "
                "k uniform; canonical numbers",
        "correct": "exact match of the program output with the integer result; a module call meeting a key not in "
                   "T_S makes the example wrong"}, indent=1))
    (d / "env.json").write_text(json.dumps(h0a.env(["stage3/l2b_r.py", "stage3/l2b_hprime.py", "stage3/recomb.py"]),
                                           indent=1))
    backends = {m: TableModule(m, i) for m, (i, _) in mods.items()}
    done = set()
    if (d / "log.jsonl").exists():
        done = {json.loads(l)["bin"] for l in (d / "log.jsonl").read_text().splitlines() if l.strip()}
    for lab, lo, hi, k, n in BINS[a.task]:
        if lab in done:
            continue
        t0 = time.time()
        rng = random.Random("L2b-0:R:%s:%s" % (a.task, lab))
        exs = [example(a.task, rng, lo, hi, k) for _ in range(n)]
        outs, calls, fail = execute(RC.PROGRAMS[a.task], [p for p, _ in exs], backends)
        ok = [o == ans for o, (_, ans) in zip(outs, exs)]
        c = [sum(x.values()) for x in calls]
        rec = {"bin": lab, "lengths": [lo, hi], "k": k, "examples": n, "accuracy": sum(ok) / n,
               "wrong": n - sum(ok), "module_failures": {s: sum(f == s for f in fail) for s in set(fail) if s},
               "wrong_without_module_failure": sum((not o) and f is None for o, f in zip(ok, fail)),
               "calls_mean": sum(c) / n, "calls_max": max(c),
               "calls_by_module_max": {m: max(x[m] for x in calls) for m in backends},
               "answer_digits_max": max(len(ans) for _, ans in exs), "seconds": round(time.time() - t0, 1),
               "wrong_examples": [{"prompt": "".join(p), "answer": "".join(ans),
                                   "output": None if o is None else "".join(o), "failure": f}
                                  for (p, ans), o, f, g in zip(exs, outs, fail, ok) if not g][:20]}
        with open(d / "log.jsonl", "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print({k2: v for k2, v in rec.items() if k2 != "wrong_examples"}, flush=True)
    recs = [json.loads(l) for l in (d / "log.jsonl").read_text().splitlines() if l.strip()]
    acc = {r["bin"]: r["accuracy"] for r in recs}
    (d / "final.json").write_text(json.dumps({
        "task": a.task, "accuracy": acc,
        "ood_all_>=0.90": all(v >= 0.90 for b, v in acc.items() if b.startswith("ood")),
        "modules": {m: {"H'_table": i, "S": s} for m, (i, s) in mods.items()},
        "seconds_total": round(sum(r["seconds"] for r in recs), 1),
        "note_51-100": ("mulNM 51-100 calls add on operands beyond the add module's checked range; rests on the H' "
                        "argument only" if a.task == "mulNM" else None)}, indent=1))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("run")
    q.add_argument("--task", choices=tuple(BINS), required=True)
    a = p.parse_args()
    {"run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    main()
