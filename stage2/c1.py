"""C-1 main run, A arm (stage2/DESIGN.md 11.16, 11.17; verdict rule 11.5 with the 9.12 definitions).

Tables (11.3 reuse, compiled from the teachers and their training data only): addition C4 seeds 6, 7, 8
(stage1/results/c4/addition_compile_s<s>), copy / mul1 / prefix_sum G-0' seeds 12, 13, 14 (stage2/results/g0p), reverse
H-0 seeds 15, 16, 17 (stage2/results/h0, BOS).  Table i = 1, 2, 3 in that order.

Student (11.16, 11.17): stage2/c1a.py HardReadLM unchanged -- hard reads of the MOVING heads of the compiled table (every
head of these 15 tables moves), segment bits against the compiled path's read at the first scored step, token shift;
arm C = 4-layer NoPE transformer (d 128, 4 heads), arm M = 4 MLP blocks (diagnostic, not a verdict).  stage1/run.py with
the c1a.py textual changes, --keep-best.  Seeds: table i -> s = 30 + i; arm C restarts s and s + 100; arm M s only
(the run's data seed = its seed).  No all-stay (Occam) arm (11.17).

  check --task T   pre-training checks per table (11.16): (b) p_h(t) <= t; (c') causal invariance: for one random step
                   t per example, every token after t replaced by a random token of the task (digits, separators, '=',
                   <eos>) -- the read positions up to t unchanged (any t), and the segment bits up to t unchanged for t
                   at or after the first scored step t0 (the bit's reference is the read at t0, a prompt position;
                   prompt-internal future references are allowed by 11.8, so for t < t0 the bits are recorded only);
                   (d) local determinism recorded only: key (x_t, (x[p_h(t)], b_h(t)) for the moving heads, x_{t-1},
                   (x[p_h(t-1)], b_h(t-1))) -> next token from the student's training data (its seed, 100,000):
                   conflicts, covered-step table accuracy, coverage
  train --task T --table i --arm C|M --restart 0|1
  select --task T --table i   arm C: the two restarts' judgment checkpoints on "select:<task>" (1,000, teacher-forced
                   exact match); the higher; within 0.005 (5 of 1,000, the G-0 / C4 tolerance) the smaller restart
  diag --task T --table i --arm C|M   in-distribution exact match with the reads, bits and shift removed (selected
                   restart for C)
  report           per task and table: the selected student's bins, criteria (OOD bins 1 and 2 >= 0.90 and >= baseline
                   best - 0.01; total FLOPs = teacher (judgment FLOPs) + dependency extraction + both arm-C students
                   (judgment FLOPs) <= the protocol budget = the largest 20,000-step training FLOPs among the task's
                   baselines); task win = all three tables; answer yes if >= 4 of 5 tasks win
                   baselines: addition stage-1 (phaseA abacus / gru, phaseA2 looped_rr, phaseA4 rope; seed 0); copy,
                   mul1, prefix_sum G-0 (no BOS); reverse G-0 (no BOS) and H-0 (BOS) for the accuracy reference, H-0 (BOS,
                   same format) for the budget; 20,000-step FLOPs = the run's training FLOPs per step x 20,000
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
import c1a                       # noqa: E402

OUT = pathlib.Path(os.environ.get("C1_OUT", HERE / "results" / "c1"))
TASKS = c0a.TASKS
TOL_COUNT = 5
SRC = {"addition": [ROOT / ("stage1/results/c4/addition_compile_s%d" % s) for s in (6, 7, 8)],
       "copy": [HERE / ("results/g0p/copy_compile_s%d" % s) for s in (12, 13, 14)],
       "mul1": [HERE / ("results/g0p/mul1_compile_s%d" % s) for s in (12, 13, 14)],
       "prefix_sum": [HERE / ("results/g0p/prefix_sum_compile_s%d" % s) for s in (12, 13, 14)],
       "reverse": [HERE / ("results/h0/reverse_compile_s%d" % s) for s in (15, 16, 17)]}
BASE_ACC = {"addition": [ROOT / "stage1/results/phaseA/addition__abacus__1M__s0__N100000",
                         ROOT / "stage1/results/phaseA/addition__gru__1M__s0__N100000",
                         ROOT / "stage1/results/phaseA2/phaseA2_addition__looped_rr__1M__s0__N100000",
                         ROOT / "stage1/results/phaseA4/phaseA4_addition__rope__1M__s0__N100000"]}
for _t in ("copy", "mul1", "prefix_sum", "reverse"):
    BASE_ACC[_t] = [HERE / ("results/g0/g0_%s__%s__1M__s0__N100000" % (_t, k)) for k in ("abacus", "rope", "looped_rr", "gru")]
BASE_ACC["reverse"] += [HERE / ("results/h0/h0_reverse__%s__1M__s0__N100000" % k) for k in ("abacus", "rope", "looped_rr", "gru")]
BASE_BUDGET = {t: list(v) for t, v in BASE_ACC.items()}
BASE_BUDGET["reverse"] = BASE_ACC["reverse"][4:]                    # same format (BOS), 9.11


def compiled(task, i):
    cr = json.loads((SRC[task][i - 1] / "compile_result.json").read_text())
    return cr


def seed_of(i):
    return 30 + i


def run_dir(task, i, arm, restart):
    s = seed_of(i) + 100 * restart
    return OUT / ("c1_%s__%s__1M__s%d__N100000__table%d" % (task, c1a.ARMS[arm], s, i))


# ---------------------------------------------------------------- checks
def cmd_check(a):
    c0a.install(a.task)
    import tasks as T
    import run as R
    import h0a
    torch.set_num_threads(1)
    out = {}
    pool = [T.TOK[d] for d in T.DIGITS] + [T.TOK[s] for s in ("+", "=", "|", "-", "*", "^") if s in T.TOK] + [T.EOS]
    for i in (1, 2, 3):
        cr = compiled(a.task, i)
        table = cr["policy"]
        mv = c1a.moving(table)
        rng = random.Random("c1:causal:%s:%d" % (a.task, i))

        def keys(x, y, P, Bt):
            res = []
            for b in range(x.shape[0]):
                for t in (y[b] != -100).nonzero()[:, 0].tolist():
                    k = (int(x[b, t]),) + tuple((int(x[b, P[b, j, t]]), int(Bt[b, j, t])) for j in mv)
                    k += (int(x[b, t - 1]),) + tuple((int(x[b, P[b, j, t - 1]]), int(Bt[b, j, t - 1])) for j in mv)
                    res.append((b, k, int(y[b, t])))
            return res
        train = T.train_set(a.task, 100000, seed_of(i))
        tabk, conflicts = {}, 0
        for j in range(0, len(train), 256):
            x, y = R.make_batch(train[j:j + 256])
            P = c1a.read_paths(x, table)
            for _, k, v in keys(x, y, P, c1a.segment_bits(x, P)):
                if k in tabk and tabk[k] != v:
                    conflicts += 1
                tabk.setdefault(k, v)
        evs = T.eval_sets(a.task, 1000, 500)
        evs["train_first200"] = train[:200]
        sets = {}
        for lab, ex in evs.items():
            caus = pos_ok = bit_ok = bit_n = bit_strict_ok = 0
            n_keys = covered = cov_ok = 0
            for j in range(0, len(ex), 128):
                chunk = ex[j:j + 128]
                x, y = R.make_batch(chunk)
                P = c1a.read_paths(x, table)
                Bt = c1a.segment_bits(x, P)
                x2 = x.clone()
                ts = []
                for b, (p, ans) in enumerate(chunk):
                    n = len(p) + len(ans)
                    caus += bool((P[b, :, :n] <= torch.arange(n)[None, :]).all())
                    t = rng.randrange(n)
                    ts.append(t)
                    for q in range(t + 1, n):
                        x2[b, q] = rng.choice(pool)
                P2 = c1a.read_paths(x2, table)
                eq = (x2 == T.TOK["="]).any(1)
                for b, (p, ans) in enumerate(chunk):
                    t, t0 = ts[b], len(p) - 1
                    pos_ok += bool((P[b, :, :t + 1] == P2[b, :, :t + 1]).all())
                    if bool(eq[b]):
                        B2 = c1a.segment_bits(x2[b:b + 1], P2[b:b + 1])
                        same = bool((Bt[b, :, :t + 1] == B2[0, :, :t + 1]).all())
                    else:                                    # every '=' replaced away (t < t0): bits undefined there
                        same = False
                    bit_strict_ok += same
                    if t >= t0:
                        bit_n += 1
                        bit_ok += same
                for b, k, v in keys(x, y, P, Bt):
                    n_keys += 1
                    if k in tabk:
                        covered += 1
                        cov_ok += tabk[k] == v
            sets[lab] = {"examples": len(ex), "causal_p_le_t": caus / len(ex),
                         "causal_invariance_read_positions_any_t": pos_ok / len(ex),
                         "causal_invariance_bits_t_ge_t0": bit_ok / bit_n if bit_n else None,
                         "examples_with_t_ge_t0": bit_n,
                         "bits_unchanged_any_t_recorded_only": bit_strict_ok / len(ex),
                         "d_covered_steps_table_right_recorded": cov_ok / covered if covered else None,
                         "d_key_coverage_recorded": covered / n_keys}
            print(a.task, i, lab, sets[lab], flush=True)
        ok = all(s["causal_p_le_t"] == 1.0 and s["causal_invariance_read_positions_any_t"] == 1.0
                 and s["causal_invariance_bits_t_ge_t0"] == 1.0 for s in sets.values())
        out["table%d" % i] = {"source": str(SRC[a.task][i - 1].relative_to(ROOT)), "teacher_seed": cr["data_seed"],
                              "policy": table, "policy_named": cr["policy_named"], "moving_heads": mv,
                              "content_move_in_table": any(5 in col for col in table),
                              "d_conflicts_recorded": conflicts, "d_table_keys": len(tabk), "sets": sets,
                              "gate_b_cprime_1.000": ok}
    out["all_1.000"] = all(v["gate_b_cprime_1.000"] for v in out.values() if isinstance(v, dict))
    out["env"] = h0a.env(["stage2/c1.py", "stage2/c1a.py"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("pretraining_check_%s.json" % a.task)).write_text(json.dumps(out, indent=1))
    print(a.task, "gate (b), (c'):", out["all_1.000"])


# ---------------------------------------------------------------- train / select / diag
def cmd_train(a):
    c0a.install(a.task)
    table = compiled(a.task, a.table)["policy"]
    c1a.register(table, a.arm)
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in c1a.PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    assert a.arm == "C" or a.restart == 0
    s = seed_of(a.table) + 100 * a.restart
    argv = ["--task", a.task, "--kind", c1a.ARMS[a.arm], "--scale", "1M", "--seed", str(s), "--N", "100000",
            "--max-steps", os.environ.get("C1_MAX_STEPS", "20000"), "--phase", "c1", "--out-root", str(OUT),
            "--threads", "1", "--tag", "table%d" % a.table, "--keep-best"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    exec(compile(src, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


def load(task, i, arm, restart):
    import tasks as T
    import models as M
    d = run_dir(task, i, arm, restart)
    ck = torch.load(d / "teacher_best.pt", weights_only=False)
    fin = json.loads((d / "final.json").read_text())
    assert ck["step"] == fin["judgment"]["step"]
    m = M.build(c1a.ARMS[arm], len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
    m.load_state_dict(ck["model"])
    m.eval()
    return m, fin


def exact(model, exs, bs=128):
    import run as R
    ok = 0
    with torch.no_grad():
        for j in range(0, len(exs), bs):
            x, y = R.make_batch(exs[j:j + bs])
            pred = model(x).argmax(-1)
            m = y != -100
            ok += int(((pred == y) | ~m).all(1).sum())
    return ok


def cmd_select(a):
    c0a.install(a.task)
    c1a.register(compiled(a.task, a.table)["policy"], "C")
    import c4_select as CS
    import h0a
    torch.set_num_threads(1)
    sel = CS.selection_set(a.task)
    counts = {}
    for r in (0, 1):
        m, _ = load(a.task, a.table, "C", r)
        counts[r] = exact(m, sel)
    best = max(counts.values())
    pool = [r for r in (0, 1) if best - counts[r] <= TOL_COUNT]
    pick = min(pool)
    res = {"task": a.task, "table": a.table, "selection_set": {"generation_seed": "select:%s" % a.task, "size": len(sel)},
           "correct": counts, "accuracy": {r: c / len(sel) for r, c in counts.items()}, "tied_within_tolerance": pool,
           "selected_restart": pick, "selected_seed": seed_of(a.table) + 100 * pick,
           "rule": "highest selection accuracy; within 0.005 (<= 5 of 1,000) the smaller restart",
           "env": h0a.env(["stage2/c1.py", "stage2/c1a.py"])}
    (OUT / ("selection_%s_table%d.json" % (a.task, a.table))).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("accuracy", "selected_restart")}))


def cmd_diag(a):
    c0a.install(a.task)
    c1a.register(compiled(a.task, a.table)["policy"], a.arm)
    import tasks as T
    import h0a
    torch.set_num_threads(1)
    if a.arm == "C":
        r = json.loads((OUT / ("selection_%s_table%d.json" % (a.task, a.table))).read_text())["selected_restart"]
    else:
        r = 0
    m, fin = load(a.task, a.table, a.arm, r)
    ev = T.eval_sets(a.task, 1000, 500)
    lab = list(ev)[0]
    base = exact(m, ev[lab]) / len(ev[lab])
    m.ablate = True
    abl = exact(m, ev[lab]) / len(ev[lab])
    res = {"task": a.task, "table": a.table, "arm": a.arm, "restart": r,
           "in_distribution": {"unchanged": base, "run_judgment_acc": fin["judgment"]["acc"][lab],
                               "reads_bits_shift_removed": abl, "drop": base - abl},
           "env": h0a.env(["stage2/c1.py", "stage2/c1a.py"])}
    (OUT / ("diag_%s_table%d_%s.json" % (a.task, a.table, a.arm))).write_text(json.dumps(res, indent=1))
    print(json.dumps(res["in_distribution"]))


# ---------------------------------------------------------------- report
def fin_of(d):
    return json.loads((d / "final.json").read_text())


def baselines(task):
    import baseline_table                                          # Phase A runs (before the judgment rule): the
    accs = [baseline_table.judged(d)[1] for d in BASE_ACC[task]]   # same rule applied to log.jsonl (stage 1)
    labs = list(accs[0])
    best = {l: max(x[l] for x in accs) for l in labs}
    budget = {}
    for d in BASE_BUDGET[task]:
        f = fin_of(d)
        budget[d.name] = f["train_flops"] / f["steps"] * 20000
    return {"best": best, "best_runs": [d.name for d in BASE_ACC[task]], "budget": max(budget.values()),
            "budget_by_run": budget}


def cmd_report(a):
    import h0a
    out = {"design": "stage2/DESIGN.md 11.16, 11.17 (verdict 11.5 / 7.7 with the 9.12 definitions)", "tasks": {}}
    wins = 0
    md = []
    for t in TASKS:
        B = baselines(t)
        labs = list(B["best"])
        rows = []
        for i in (1, 2, 3):
            cr = compiled(t, i)
            sel = json.loads((OUT / ("selection_%s_table%d.json" % (t, i))).read_text())
            r = sel["selected_restart"]
            fC = [fin_of(run_dir(t, i, "C", k)) for k in (0, 1)]
            fM = fin_of(run_dir(t, i, "M", 0))
            acc = fC[r]["judgment"]["acc"]
            tpath = ROOT / cr["teacher"]["path"] if not os.path.isabs(cr["teacher"]["path"]) else pathlib.Path(cr["teacher"]["path"])
            teacher_flops = cr["teacher"]["train_flops_to_judgment"]
            total = teacher_flops + cr["extraction"]["flops"] + sum(f["judgment"]["train_flops_cum"] for f in fC)
            c1 = acc[labs[1]] >= 0.90 and acc[labs[2]] >= 0.90
            c2 = acc[labs[1]] >= B["best"][labs[1]] - 0.01 and acc[labs[2]] >= B["best"][labs[2]] - 0.01
            c3 = total <= B["budget"]
            dC = json.loads((OUT / ("diag_%s_table%d_C.json" % (t, i))).read_text())["in_distribution"]
            dM = json.loads((OUT / ("diag_%s_table%d_M.json" % (t, i))).read_text())["in_distribution"]
            rows.append({"table": i, "teacher_seed": cr["data_seed"], "teacher": str(tpath.parent.name),
                         "selected_restart": r, "selection_accuracy": sel["accuracy"],
                         "acc": acc, "restart_accs": [f["judgment"]["acc"] for f in fC],
                         "steps": [f["steps"] for f in fC], "judgment_steps": [f["judgment"]["step"] for f in fC],
                         "flops": {"teacher": teacher_flops, "extraction": cr["extraction"]["flops"],
                                   "students": [f["judgment"]["train_flops_cum"] for f in fC], "total": total,
                                   "budget": B["budget"], "fraction": total / B["budget"]},
                         "wall_s": [f["wall_train_s"] + f["wall_eval_s"] for f in fC],
                         "criteria": {"1_ood_first_two_ge_0.90": c1, "2_ge_baseline_best_minus_0.01": c2,
                                      "3_total_flops_le_budget": c3}, "win": c1 and c2 and c3,
                         "reads_removed_drop": {"C": dC["drop"], "M": dM["drop"]},
                         "M": {"acc": fM["judgment"]["acc"], "judgment_step": fM["judgment"]["step"],
                               "steps": fM["steps"], "train_flops": fM["train_flops"],
                               "wall_s": fM["wall_train_s"] + fM["wall_eval_s"],
                               "ood_first_two_ge_0.90": fM["judgment"]["acc"][labs[1]] >= 0.90
                               and fM["judgment"]["acc"][labs[2]] >= 0.90},
                         "curve_C": c1a.curve(run_dir(t, i, "C", r)), "curve_M": c1a.curve(run_dir(t, i, "M", 0))})
        win = all(x["win"] for x in rows)
        wins += win
        out["tasks"][t] = {"baselines": B, "tables": rows, "win": win}
        md.append("\n### %s: 이김 %s (기준선 최고 %s; 허용 예산 %.2e)" % (
            t, "예" if win else "아니오", " · ".join("%.3f" % B["best"][l] for l in labs), B["budget"]))
        md.append("| 표 (교사 시드) | 선택 (선택용 r0 · r1) | 분포 안 · 밖 1 · 2 · 3 | 합계 FLOPs (예산 대비) | 기준 1 · 2 · 3 | 읽기 제거 하락 C · M | M 분포 안 · 밖 1 · 2 · 3 |")
        md.append("|---|---|---|---|---|---|---|")
        YN = {True: "예", False: "아니오"}
        for x in rows:
            md.append("| %d (s%d) | r%d (%.3f · %.3f) | %s | %.2e (%.2f) | %s | %.3f · %.3f | %s |" % (
                x["table"], x["teacher_seed"], x["selected_restart"], x["selection_accuracy"]["0"] if "0" in x["selection_accuracy"] else x["selection_accuracy"][0],
                x["selection_accuracy"]["1"] if "1" in x["selection_accuracy"] else x["selection_accuracy"][1],
                " · ".join("%.3f" % v for v in x["acc"].values()), x["flops"]["total"], x["flops"]["fraction"],
                " · ".join(YN[v] for v in x["criteria"].values()), x["reads_removed_drop"]["C"],
                x["reads_removed_drop"]["M"], " · ".join("%.3f" % v for v in x["M"]["acc"].values())))
    out["tasks_won"] = wins
    out["answer"] = "yes" if wins >= 4 else "no"
    out["env"] = h0a.env(["stage2/c1.py", "stage2/c1a.py"])
    (OUT / "summary.json").write_text(json.dumps(out, indent=1))
    print("\n".join(md))
    print("tasks won: %d of 5 -> %s" % (wins, out["answer"]))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("check")
    q.add_argument("--task", choices=TASKS, required=True)
    q = sp.add_parser("train")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--table", type=int, choices=(1, 2, 3), required=True)
    q.add_argument("--arm", choices=tuple(c1a.ARMS), required=True)
    q.add_argument("--restart", type=int, choices=(0, 1), default=0)
    q.add_argument("--resume", action="store_true")
    q = sp.add_parser("select")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--table", type=int, choices=(1, 2, 3), required=True)
    q = sp.add_parser("diag")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--table", type=int, choices=(1, 2, 3), required=True)
    q.add_argument("--arm", choices=tuple(c1a.ARMS), required=True)
    sp.add_parser("report")
    a = p.parse_args()
    {"check": cmd_check, "train": cmd_train, "select": cmd_select, "diag": cmd_diag, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
