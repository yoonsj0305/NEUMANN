"""G-0 failure type of reverse (stage2/DESIGN.md 7.7, failure-type record): head read positions of the compiled tables
of seeds 9, 10, 11 and of the correct table (stage2/g0a.py), on the first examples of the selection set and on one
example per out-of-distribution bin.  Reads only the committed compile results and the G-0a table; no training.

For every answer step (current token '=' or an answer token) the read token of every head.  End marker: the correct
table's head 1 reads a non-digit ('=') exactly at the step whose target is <eos> (offset 0) and digits at the other
answer steps after the first -- the information its controller uses (<eos> when head 1 reads '=').  Per table and
head: the fraction of examples in which the head reads a non-digit at exactly one answer step after the first, and
that step's offset from the <eos> step (0 = the <eos> step, -1 = one step before it, which a register can carry to
the <eos> step).

  python stage2/g0_reverse_paths.py      # writes stage2/results/g0/reverse_paths.json
  python stage2/g0_reverse_paths.py --phase g0p --seeds 12 13 14      # G-0': stage2/results/g0p/reverse_paths.json
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g_tasks as G            # noqa: E402
import g0a                     # noqa: E402

V = G.VOCAB


def end_marker(seq, plen, path):
    """per head: the offset from the <eos> step of its single non-digit read after the first answer step, or None"""
    steps = list(range(plen, len(seq) - 1))           # answer steps after the first ('=') one
    last = len(seq) - 2                                # the step whose target is <eos>
    out = {}
    for j in range(3):
        nd = [t - last for t in steps if seq[path[t][j]] not in g0a.DIG]
        out[j] = nd[0] if len(nd) == 1 else None
    return out


def main(a):
    RES = HERE / "results" / a.phase
    tabs = {"correct": g0a.TABLES["reverse"]}
    for s in a.seeds:
        tabs["compiled_s%d" % s] = json.loads((RES / ("reverse_compile_s%d" % s) / "compile_result.json")
                                              .read_text())["policy"]
    exs = G.selection_set("reverse")[:200]
    out = {"tables": tabs, "end_marker": {}, "example": {}}
    for name, tab in tabs.items():
        cnt = {}
        anyh = 0
        for p, a in exs:
            seq = p + a
            m = end_marker(seq, len(p), g0a.head_path(seq, tab))
            for j, d in m.items():
                if d is not None:
                    k = "head%d_offset%d" % (j, d)
                    cnt[k] = cnt.get(k, 0) + 1
            anyh += any(d in (0, -1) for d in m.values())
        res = {k: v / len(exs) for k, v in sorted(cnt.items())}
        res["any_head_offset_0_or_-1"] = anyh / len(exs)
        out["end_marker"][name] = res
        p, a = next(e for e in exs if len(e[0]) - 1 == 4)
        seq = p + a
        path = g0a.head_path(seq, tab)
        out["example"][name] = {"tokens": " ".join(V[i] for i in seq),
                                "answer_steps": [{"x_t": V[seq[t]], "target": V[seq[t + 1]], "heads": path[t],
                                                  "reads": [V[seq[q]] for q in path[t]]}
                                                 for t in range(len(p) - 1, len(seq) - 1)]}
    (RES / "reverse_paths.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["end_marker"], indent=1))
    for name, e in out["example"].items():
        print(name, e["tokens"])
        for r in e["answer_steps"]:
            print("   ", r["x_t"], "->", r["target"], r["heads"], r["reads"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="g0")
    ap.add_argument("--seeds", type=int, nargs="+", default=[9, 10, 11])
    main(ap.parse_args())
