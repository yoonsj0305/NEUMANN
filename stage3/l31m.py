"""3-1 main run (stage3/DESIGN.md 6.7 with 6.9-6.13).  Raw data in results/3-1/main/.

  teacher_check --task T --seed S   in-distribution exact match of the rope teacher on select:<task> (>= 0.95)
  choose --task T --seed S          substitution dependency of the used teacher on the 400 examples (synthesis sample
                                    100 + length 8-10 set 300; FLOPs recorded), routing candidates Q 1-4 (6.10, 600 s),
                                    output-state candidates (6.12/6.13), selection 6.13-4 -> choice_<T>_t<S>.json
  train --task T --seed S --restart R   student s + 10 + 100 R on the chosen combined program (l1read, C-1 student + q)
  select --task T --seed S          C-1 rule on select:<task> (within 5 of 1,000: the smaller restart)
  report                            7.7 criteria with the 9.12 budget (3-0 C baselines)

Teacher training uses stage3/l_adapter.py run (driver stage3/l31m_run.sh).  Coverage figures labelled "all" in the
routing files are over the 400 extracted examples (the dependency exists only there); explanation rates "all" are
over the first 2,000 (no teacher cost).
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402

import l1                        # noqa: E402
import l31                       # noqa: E402
import l31b                      # noqa: E402
import l31c                      # noqa: E402

MAIN = HERE / "results" / "3-1" / "main"
l31.OUT = MAIN
l31c.GATE = l31c.ROUTE_DIR = MAIN
TEACHER_SEEDS = l31.TEACHER_SEEDS
GATE1 = HERE / "results" / "3-1" / "3-1a3"


def env_info():
    e = l31c.env_info()
    e["module"] = "stage3/l31m.py"
    import h0a
    e["code"] = h0a.env(["stage3/l31m.py", "stage3/l31c.py", "stage3/l31b.py", "stage3/l31.py", "stage3/l1.py"])
    return e


def cmd_choose(a):
    torch.set_num_threads(1)
    l31b.setup(a.task)
    MAIN.mkdir(parents=True, exist_ok=True)
    used = l31.used_teacher(a.task, a.seed)
    assert used is not None, "both teachers failed"
    run_dir = l31.teacher_dir(a.task, used)
    data_seed = json.loads((run_dir / "final.json").read_text())["seed"]
    exs, ns = l31.train_with_n(a.task, data_seed, l31.N_ALL)
    syn, sel = l31.pick_sets(a.task, ns)
    ids400 = syn + sel
    ids_all = list(range(l31.N_ALL))
    rows, tinfo = l31b.rows_teacher_sub(a.task, run_dir, exs, ids400, "main__%s" % run_dir.name)
    prefix = "teacher_%s_t%d" % (a.task, a.seed)
    routes = l31b.routing_candidates(exs, rows, syn, sel, ids400, ids400, prefix, MAIN)
    res = l31c.supply_candidates(exs, syn, sel, ids_all, routes, prefix)
    pick, tied = l31c.select(res)
    MUc, DELc, rec = res[pick]
    hp = l31b.paths_of(exs, ids400, l1.program_tensors(l1.PROGRAMS[a.task]))
    hand = {k: l31b.coverage(rows, ids, hp) for k, ids in (("synthesis_sample", syn), ("selection_8_10", sel),
                                                          ("all_400", ids400))}
    per_Q = {}
    for Q, (MU, DEL, rr) in routes.items():
        pa = l31b.paths_of(exs, ids_all, (MU, DEL))
        per_Q[Q] = {"candidate": rr["candidate"], "coverage": rr["coverage"], "coverage_without_free": rr["coverage_without_free"],
                    "solver": {k: rr["solver"][k] for k in ("status", "proved_optimal", "gap_relative", "cpu_s",
                                                            "exec_check_examples_equal")},
                    "program": rr["program"],
                    "supply_agreement_all_2000_without_eos": l31.supply_agreement(a.task, exs, ids_all, pa, False),
                    "supply_agreement_all_2000_with_eos": l31.supply_agreement(a.task, exs, ids_all, pa, True)}
    gate1 = json.loads((GATE1 / ("gate1_%s.json" % a.task)).read_text())
    out = {"task": a.task, "teacher_seed": a.seed, "teacher_run_seed": used, "teacher_run": str(run_dir.relative_to(ROOT)),
           "data": "tasks.train_set(%s, 100000, %d), first 2,000; synthesis sample and length 8-10 set as 6.9-1" % (a.task, data_seed),
           "extraction": tinfo, "selected": {"Q": pick[0], "Qp": pick[1], "states": pick[0] * pick[1]},
           "tied_after_explanation_and_coverage": ["Q%d_Qp%d" % k for k in tied],
           "rule": "6.13-4: explanation rate 8-10 (0.005) -> coverage 8-10 (0.005) -> Q x Q' -> Q",
           "candidates": l31c.cand_summary(res), "routing_per_Q": per_Q, "hand_coverage_same_dependency": hand,
           "explanation_selected": rec["explanation"], "coverage_selected": rec["coverage"],
           "explanation_8_10_below_0.99": bool(rec["explanation"]["selection_8_10"]["rate"] < 0.99),
           "table": rec["table"],
           "synthesis_cpu_s_total": sum(r[2]["solver"]["cpu_s"] for r in routes.values())
           + sum(r[2]["solver"].get("cpu_s", 0.0) for r in res.values()),
           "check1_failed_task_marker": None if gate1["pass"] else "check 1 failed (3-1a3): output state not recovered",
           "env": env_info()}
    l31.save_prog(l31.choice_path(a.task, a.seed), MUc, DELc, out)
    print(a.task, a.seed, "selected", pick, "expl", {k: round(v["rate"], 4) for k, v in rec["explanation"].items()},
          "cov sel %.4f" % rec["coverage"]["selection_8_10"], flush=True)


def cmd_report(a):
    jl = l31.jl
    out = {"design": "stage3/DESIGN.md 6.7 (verdict 7.7 with the 9.12 budget), 6.9-6.13", "tasks": {}}
    wins = 0
    for t in l1.VERDICT_TASKS:
        B = l31.baselines30(t)
        labs = list(B["best"])
        rows = []
        for s in TEACHER_SEEDS:
            r = {"teacher_seed": s}
            seeds = [x for x in (s, s + 200) if (MAIN / ("teacher_select_%s_s%d.json" % (t, x))).exists()]
            checks = [jl(MAIN / ("teacher_select_%s_s%d.json" % (t, x))) for x in seeds]
            r["teacher_checks"] = {c["run_seed"]: c["selection_accuracy"] for c in checks}
            used = l31.used_teacher(t, s)
            r["teacher_used"] = used
            if used is None:
                r["failure"] = "teacher"
                rows.append(r)
                continue
            ch = jl(l31.choice_path(t, s))
            sel = jl(MAIN / ("selection_%s_t%d.json" % (t, s)))
            fs = [jl(l31.student_dir(t, s, k) / "final.json") for k in (0, 1)]
            f = fs[sel["selected_restart"]]
            acc = f["judgment"]["acc"]
            teacher_fl = sum(c["judgment_train_flops"] for c in checks)
            extract_fl = ch["extraction"]["extraction_flops"]
            stud_fl = [x["judgment"]["train_flops_cum"] for x in fs]
            total = teacher_fl + extract_fl + sum(stud_fl)
            c1_ = acc[labs[1]] >= 0.90 and acc[labs[2]] >= 0.90
            c2_ = acc[labs[1]] >= B["best"][labs[1]] - 0.01 and acc[labs[2]] >= B["best"][labs[2]] - 0.01
            c3_ = total <= B["budget"]
            cpu = {"teacher_judgment_train_s": sum(c["judgment_wall_train_s"] for c in checks),
                   "extraction_cpu_s": ch["extraction"]["extraction_cpu_s"], "synthesis_cpu_s": ch["synthesis_cpu_s_total"],
                   "students_judgment_train_s": [x["judgment"]["wall_train_s_cum"] for x in fs]}
            cpu["total"] = (cpu["teacher_judgment_train_s"] + cpu["extraction_cpu_s"] + cpu["synthesis_cpu_s"]
                            + sum(cpu["students_judgment_train_s"]))
            r.update({"selected": ch["selected"], "explanation_selected": {k: v["rate"] for k, v in ch["explanation_selected"].items()},
                      "eos_explanation_selected": {k: v["eos_rate"] for k, v in ch["explanation_selected"].items()},
                      "coverage_selected": ch["coverage_selected"],
                      "supply_agreement_selected_routing": {k: ch["routing_per_Q"][str(ch["selected"]["Q"])][k] for k in
                                                            ("supply_agreement_all_2000_without_eos", "supply_agreement_all_2000_with_eos")},
                      "hand_coverage": ch["hand_coverage_same_dependency"], "program": ch["program"],
                      "check1_failed_task_marker": ch["check1_failed_task_marker"],
                      "selected_restart": sel["selected_restart"], "selection_accuracy": sel["accuracy"],
                      "acc": acc, "judgment_step": f["judgment"]["step"], "steps": f["steps"],
                      "flops": {"teacher": teacher_fl, "extraction": extract_fl, "students": stud_fl, "total": total,
                                "budget": B["budget"], "fraction": total / B["budget"]},
                      "cpu_s": cpu, "criteria": {"1_ood12_ge_0.90": c1_, "2_ge_baseline_best_minus_0.01": c2_,
                                                 "3_total_flops_le_budget": c3_}, "win": c1_ and c2_ and c3_,
                      "decisive": bool(c1_ and c2_ and c3_ and B["best"][labs[2]] <= 0.60)})
            rows.append(r)
        win = len(rows) == 3 and all(x.get("win") for x in rows)
        wins += win
        out["tasks"][t] = {"baselines": B, "tables": rows, "win": win}
    out["tasks_won"] = wins
    out["answer"] = "yes" if wins >= 3 else "no"
    out["env"] = env_info()
    (MAIN / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({t: [(x.get("selected"), x.get("acc"), x.get("win")) for x in v["tables"]] for t, v in out["tasks"].items()},
                     default=str))
    print("tasks won", wins)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for name in ("teacher_check", "choose", "train", "select"):
        q = sp.add_parser(name)
        q.add_argument("--task", required=True)
        q.add_argument("--seed", type=int, required=True)
        q.add_argument("--restart", type=int, default=0)
        q.add_argument("--resume", action="store_true")
    sp.add_parser("report")
    a = p.parse_args()
    {"teacher_check": l31.cmd_teacher_check, "choose": cmd_choose, "train": l31.cmd_train, "select": l31.cmd_select,
     "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
