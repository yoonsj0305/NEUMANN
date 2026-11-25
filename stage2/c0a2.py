"""C-0a' -- the first revision of C-0a (stage2/DESIGN.md 11.11, 11.12).  O arm (hand tables), five tasks, student seed 21.

Student: the C-0b D-arm student (stage2/c0b.py SharedLM: one embedding table per coupling head shared by its key and
query IDs) with ONE layer: d 128, 4 heads, 1 pre-LN NoPE layer (models.Block).  Coupling (11.7 channels, 11.8
prompt-only key IDs: stage2/c0a.py coupling_ids), offsets 0..100 per sequence and head, and the stage-1 training
protocol (stage1/run.py executed with stage2/c0a.py PATCHES; the FLOPs use cfg["layers"] = 1) are unchanged; the
judgment checkpoint is kept (--keep-best).

  check --task T   the 11.8 pre-training checks again, written to results/c0a2/: (a) invariance and (c) query = key of
                   the read position on the student code (stage2/c0a.py cmd_check), and (b) the share of examples whose
                   prompt key IDs depend on the answer length (stage2/c0a_coupling_check.keys_ext, 200 per bin)
  train --task T   one run
  diag --task T    at the judgment checkpoint, in-distribution exact match (1,000): unchanged, all IDs 0 (ablation,
                   reference), every non-zero query ID + one random integer 1..50 per sequence (shuffle, keys unchanged)
                   -- as stage2/c0b.py
  report           table, pass rule (>= 4 of 5 tasks with OOD bins 1 and 2 >= 0.90), the drops, and the learning-curve
                   shape (11.12): the first step with in-distribution >= 0.5 and >= 0.99 and the OOD bin-1 value then
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402
import c0a                       # noqa: E402
import c0b                       # noqa: E402

OUT = pathlib.Path(os.environ.get("C0A2_OUT", HERE / "results" / "c0a2"))
SEED = 21
TASKS = c0a.TASKS
TAG = "shared_1layer"


def register(table):
    import models as M
    M.SCALES["coupled"] = {"1M": dict(M.SCALES["abacus"]["1M"], layers=1, table=table, shared=True)}
    inner = M.build

    def build(kind, vocab, digit_ids, cfg):
        if kind == "coupled":
            cfg = dict(cfg)
            assert cfg.pop("shared", False)
            return c0b.SharedLM(vocab, **cfg)
        return inner(kind, vocab, digit_ids, cfg)
    M.build = build


def run_dir(task):
    return OUT / ("c0a2_%s__coupled__1M__s%d__N100000__%s" % (task, SEED, TAG))


def cmd_check(a):
    c0a.OUT = OUT
    c0a.cmd_check(a)                                       # (a), (c): writes OUT/pretraining_check_<task>.json
    import c0a_coupling_check as CK
    res = {}
    for lab, ex in CK.sets(a.task).items():
        dep = 0
        for p, ans in ex:
            s = p + ans
            k0 = CK.keys_ext(s, len(p), CK.TAB[a.task])
            k1 = CK.keys_ext(s + [CK.FILL], len(p), CK.TAB[a.task])
            dep += [r[:len(p)] for r in k0] != [r[:len(p)] for r in k1]
        res[lab] = {"examples": len(ex), "depends_on_answer_length": dep / len(ex)}
        print(a.task, lab, res[lab], flush=True)
    (OUT / ("coupling_check_prompt_extended_%s.json" % a.task)).write_text(json.dumps(
        {"design": "stage2/DESIGN.md 11.8 check 3 (b), stage2/c0a_coupling_check.keys_ext", "results": res}, indent=1))


def cmd_train(a):
    c0a.install(a.task)
    register(c0a.hand_table(a.task))
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in c0a.PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    argv = ["--task", a.task, "--kind", "coupled", "--scale", "1M", "--seed", str(SEED), "--N", "100000",
            "--max-steps", os.environ.get("C0A2_MAX_STEPS", "20000"), "--phase", "c0a2", "--out-root", str(OUT),
            "--threads", "1", "--tag", TAG, "--keep-best"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


def cmd_diag(a):
    c0a.install(a.task)
    register(c0a.hand_table(a.task))
    import tasks as T
    import models as M
    import h0a
    torch.set_num_threads(1)
    d = run_dir(a.task)
    ck = torch.load(d / "teacher_best.pt", weights_only=False)
    fin = json.loads((d / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"]
    model = M.build("coupled", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
    model.load_state_dict(ck["model"])
    model.eval()
    assert len(model.blocks) == 1 and model.qry is model.key
    ev = T.eval_sets(a.task, 1000, 500)
    lab = list(ev)[0]
    rng = random.Random("c0a2:shuffle:%s" % a.task)
    with torch.no_grad():
        base = c0b.exact(model, ev[lab], "none", rng)
        abl = c0b.exact(model, ev[lab], "ablate", rng)
        shf = c0b.exact(model, ev[lab], "shuffle", rng)
    res = {"task": a.task, "judgment_step": ck["step"], "in_distribution": {
        "unchanged": base, "run_judgment_acc": fin["judgment"]["acc"][lab], "ablation_all_ids_0": abl,
        "ablation_drop": base - abl, "shuffle_query_plus_1_50": shf, "shuffle_drop": base - shf},
        "env": h0a.env(["stage2/c0a2.py", "stage2/c0b.py", "stage2/c0a.py"])}
    (OUT / ("diag_%s.json" % a.task)).write_text(json.dumps(res, indent=1))
    print(json.dumps(res["in_distribution"]), flush=True)


def curve(d):
    rows = [json.loads(l) for l in open(d / "log.jsonl") if l.strip() and "event" not in json.loads(l)]
    labs = list(rows[0]["acc"])
    out = {}
    for th in (0.5, 0.99):
        r = next((r for r in rows if r["acc"][labs[0]] >= th), None)
        out["id_ge_%s" % th] = None if r is None else {"step": r["step"], "ood_bin1": r["acc"][labs[1]]}
    out["ood_bin1_max"] = max(r["acc"][labs[1]] for r in rows)
    out["ood_bin2_max"] = max(r["acc"][labs[2]] for r in rows)
    out["rows"] = [{"step": r["step"], "acc": r["acc"]} for r in rows]
    return out


def cmd_report(a):
    rows, ok = [], 0
    for t in TASKS:
        f = json.loads((run_dir(t) / "final.json").read_text())
        dg = json.loads((OUT / ("diag_%s.json" % t)).read_text())
        acc = f["judgment"]["acc"]
        labs = list(acc)
        win = acc[labs[1]] >= 0.90 and acc[labs[2]] >= 0.90
        ok += win
        rows.append({"task": t, "params": f["params"], "judgment_step": f["judgment"]["step"], "steps": f["steps"],
                     "stopped": f["stopped"], "acc": acc, "last_acc": f["last"]["acc"],
                     "judgment_flops": f["judgment"]["train_flops_cum"], "train_flops": f["train_flops"],
                     "wall_s": f["wall_train_s"] + f["wall_eval_s"], "ood_first_two_ge_0.90": win,
                     "in_distribution_drops": dg["in_distribution"], "curve": curve(run_dir(t))})
    out = {"design": "stage2/DESIGN.md 11.11 (pass: >= 4 of 5 tasks with OOD bins 1 and 2 >= 0.90), 11.12 (curve)",
           "tasks": rows, "tasks_meeting": ok, "pass": ok >= 4}
    (OUT / "summary.json").write_text(json.dumps(out, indent=1))
    print("| 과제 | 판정 step (실행, 멈춤) | 분포 안 · 밖 1 · 2 · 3 | 학습 FLOPs | 시간 | 제거 하락 | 뒤섞기 하락 | 분포 안 ≥0.5 step (밖 1) | ≥0.99 step (밖 1) | 밖 1·2 ≥0.90 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        c, dr = r["curve"], r["in_distribution_drops"]
        fmt = lambda x: "—" if x is None else "%d (%.3f)" % (x["step"], x["ood_bin1"])   # noqa: E731
        print("| %s | %d (%d, %s) | %s | %.2e | %.0f s | %.3f | %.3f | %s | %s | %s |" % (
            r["task"], r["judgment_step"], r["steps"], r["stopped"][:10], " · ".join("%.3f" % v for v in r["acc"].values()),
            r["train_flops"], r["wall_s"], dr["ablation_drop"], dr["shuffle_drop"], fmt(c["id_ge_0.5"]),
            fmt(c["id_ge_0.99"]), "예" if r["ood_first_two_ge_0.90"] else "아니오"))
    print("tasks meeting: %d of 5 -> pass %s" % (ok, ok >= 4))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("check")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--n", type=int, default=200)
    q = sp.add_parser("train")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--resume", action="store_true")
    q = sp.add_parser("diag")
    q.add_argument("--task", choices=TASKS, required=True)
    sp.add_parser("report")
    a = p.parse_args()
    {"check": cmd_check, "train": cmd_train, "diag": cmd_diag, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
