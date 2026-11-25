"""H-0 report (stage2/DESIGN.md 7.7, 9.5, 9.6, 9.9, 9.10, 9.11): win table, failure stages and types, teacher restarts
and teacher FLOPs, selected students.  The G-0' report (stage2/g0p_report.py) with the BOS convention, T2 and the H-0
baselines.  Run after the selections are committed.

Baselines (9.6, 9.11), per task:
  accuracy reference per bin = the highest of the 4 BOS baselines (stage2/results/h0, seed 0) and, for the frozen five
    tasks, of the 4 G-0 baselines without BOS (stage2/results/g0); rev_xor has BOS baselines only
  FLOPs cap = the largest judgment-checkpoint training FLOPs of the 4 BOS baselines (9.11; the G-0 baselines are used
    for accuracy only)
Teacher (T2): the teacher of seed s (run seed s), then restarts s + 200, s + 300, s + 400 until one passes the
  selection-set sequence check (>= 0.95, stage2/h0_teacher_check.py); none passes: failure "teacher (restarts
  exhausted)".  The compile uses the teacher that passed.
  total FLOPs = every teacher trained for the seed (each to its judgment checkpoint) + dependency extraction + all
                four students (each to its judgment checkpoint); alt. = failed teachers counted for their whole run
Win, decisive win: 7.7.  Answer (9.6): yes iff all six tasks win; no if any task does not win; else undecided.
Loss confirmed (9.9): a seed whose teacher restarts are exhausted, whose selected student has an out-of-distribution
  first-two-bins value < 0.90, or whose total FLOPs exceed the cap (with the baselines of its task complete).
Failure type (9.10): "teacher dependence" = the teacher stage, or a FLOPs failure that the passing teacher alone would
  not cause (total - failed teachers <= cap); "mechanism" = compile, student in-distribution or out-of-distribution, or
  a FLOPs failure with the passing teacher alone.  Tasks of a bundle not run: "not run (answer determined)".

  python stage2/h0_report.py        # prints markdown tables, writes stage2/results/h0/summary.json
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "results" / "h0"
G0 = HERE / "results" / "g0"
sys.path.insert(0, str(HERE))
import h_tasks as HT           # noqa: E402
from g0_report import KINDS, MIN_OOD, TOL, DECISIVE, STUDENT_MIN, jl, f3   # noqa: E402

SEEDS = (15, 16, 17)
RESTARTS = (200, 300, 400)
TEACHER_MIN = 0.95
BUNDLES = {1: ("reverse", "rev_xor", "xor"), 2: ("copy", "mul1", "prefix_sum")}
NAME = {"copy": "복사", "reverse": "뒤집기", "xor": "자리별 XOR", "mul1": "N×1 곱셈", "prefix_sum": "누적합 mod 10",
        "rev_xor": "뒤집은 XOR"}
YN = {True: "예", False: "아니오", None: "—"}


def labels(task):
    sp = HT.SPEC[task]
    return ["id_%d-%d" % sp["id"]] + ["ood_%d-%d" % b for b in sp["ood"]]


def rd(res, phase, task, kind, seed, tag=""):
    return res / ("%s_%s__%s__1M__s%d__N100000%s" % (phase, task, kind, seed, ("__" + tag) if tag else ""))


def base_runs(res, phase, task):
    out = {}
    for k in KINDS:
        f = jl(rd(res, phase, task, k, 0) / "final.json")
        if f:
            out[k] = {"judgment_step": f["judgment"]["step"], "acc": f["judgment"]["acc"],
                      "judgment_flops": f["judgment"]["train_flops_cum"], "steps": f["steps"], "stopped": f["stopped"]}
    return out


def baselines(task, L):
    bos = base_runs(RES, "h0", task)
    nob = base_runs(G0, "g0", task) if task != "rev_xor" else {}
    complete = len(bos) == len(KINDS)
    pool = {("%s (BOS)" % k): v for k, v in bos.items()}
    pool.update({("%s (BOS 없음)" % k): v for k, v in nob.items()})
    best = {l: max(v["acc"][l] for v in pool.values()) for l in L} if complete else None
    best_by = {l: max(pool, key=lambda k: pool[k]["acc"][l]) for l in L} if complete else None
    cap = max(v["judgment_flops"] for v in bos.values()) if complete else None
    cap_by = max(bos, key=lambda k: bos[k]["judgment_flops"]) if complete else None
    return {"bos": bos, "no_bos": nob, "complete": complete, "best": best, "best_by": best_by, "cap": cap,
            "cap_by": cap_by}


def teachers(task, s, L):
    out, passed = [], None
    for k, ts in enumerate((s,) + tuple(s + r for r in RESTARTS)):
        f = jl(rd(RES, "h0", task, "rope", ts) / "final.json")
        if f is None:
            return out, passed, "teacher%s not finished" % (" restart %d" % k if k else "")
        c = jl(RES / ("teacher_select_%s_s%d.json" % (task, ts)))
        if c is None:
            return out, passed, "teacher%s check not finished" % (" restart %d" % k if k else "")
        assert c["judgment_step"] == f["judgment"]["step"]
        out.append({"run_seed": ts, "restart": k, "judgment_step": f["judgment"]["step"], "steps": f["steps"],
                    "stopped": f["stopped"], "id_at_judgment": f["judgment"]["acc"][L[0]],
                    "selection_accuracy": c["selection_accuracy"], "passed": c["passed"],
                    "judgment_flops": f["judgment"]["train_flops_cum"], "run_flops": f["train_flops"]})
        if c["passed"]:
            passed = ts
            break
    return out, passed, None


def seed_result(task, s, L, B):
    r = {"failure_stage": None, "failure_type": None, "loss_confirmed": False}
    ts, passed, st = teachers(task, s, L)
    r["teachers"] = ts
    r["teacher_restarts"] = max(0, len(ts) - 1)
    r["teacher_used"] = passed
    r["teacher_flops"] = sum(t["judgment_flops"] for t in ts)
    if st:
        r["status"] = st
        return r
    if passed is None:
        r.update(failure_stage="teacher (restarts exhausted)", failure_type="teacher dependence", win=False,
                 loss_confirmed=True)
        return r
    cr = jl(RES / ("%s_compile_s%d" % (task, s)) / "compile_result.json")
    if cr is None:
        r["status"] = "compile not finished"
        return r
    pc = cr["precheck"]
    r["precheck"] = {"ratio": pc["dependency"]["ratio"], "correct": pc["dependency"]["correct"],
                     "all_stay": pc["dependency"]["all_stay"], "passed": pc["passed"]}
    r["extraction_flops"] = cr["extraction"]["flops"]
    r["compile_data_seed"] = cr["data_seed"]
    if "policy" not in cr:
        r.update(failure_stage="precheck", failure_type="mechanism", win=False, loss_confirmed=True)
        return r
    corr = json.loads((HERE / "results/h0a/bos/tables.json").read_text())[task]["table"]
    moving = [j for j in range(3) if any(m != 0 for m in corr[j])]
    agree = cr["reference_agreement_with_correct_table"]
    ag = {j: agree["correct_head%d_position_read_by_some_compiled_head" % j] for j in moving}
    r["compile"] = {"policy": cr["policy"], "policy_named": cr["policy_named"], "agreement_moving_correct_heads": ag,
                    "reads_correct_positions": all(v >= 0.99 for v in ag.values()),
                    "compiled_all_stay": all(m == 0 for c in cr["policy"] for m in c)}
    sel = jl(RES / ("selection_%s_s%d.json" % (task, s)))
    if sel is None:
        r["status"] = "selection not committed"
        return r
    studs, s_flops = {}, 0
    for key, stu in sel["students"].items():
        f = jl(pathlib.Path(HERE.parent / stu["run"]) / "final.json")
        studs[key] = {"run": stu["run"], "selection_accuracy": stu["selection_accuracy"],
                      "moving_heads": stu["moving_heads"], "judgment_step": f["judgment"]["step"],
                      "acc": f["judgment"]["acc"], "judgment_flops": f["judgment"]["train_flops_cum"],
                      "steps": f["steps"], "stopped": f["stopped"]}
        s_flops += studs[key]["judgment_flops"]
    r["students"] = studs
    r["selected"] = sel["selected"]
    r["selection_reason"] = sel["reason"]
    t_alt = sum(t["run_flops"] if not t["passed"] else t["judgment_flops"] for t in ts)
    t_pass = sum(t["judgment_flops"] for t in ts if t["passed"])
    r["flops"] = {"teachers": r["teacher_flops"], "teachers_alt": t_alt, "passing_teacher": t_pass,
                  "extraction": r["extraction_flops"], "students": s_flops}
    r["total_flops"] = r["teacher_flops"] + r["extraction_flops"] + s_flops
    r["total_flops_alt"] = t_alt + r["extraction_flops"] + s_flops
    r["total_flops_passing_teacher_only"] = t_pass + r["extraction_flops"] + s_flops
    a = studs[sel["selected"]]["acc"]
    o1, o2 = a[L[1]], a[L[2]]
    c1 = o1 >= MIN_OOD and o2 >= MIN_OOD
    if not c1:
        r["loss_confirmed"] = True
    if not B["complete"]:
        r["criteria"] = {"1_ood_first_two_ge_0.90": c1, "2_ge_baseline_best_minus_0.01": None,
                         "3_total_flops_le_cap": None}
        r["win"] = False if not c1 else None
        r["status"] = "baselines not finished"
    else:
        best, cap = B["best"], B["cap"]
        c2 = o1 >= best[L[1]] - TOL and o2 >= best[L[2]] - TOL
        c3 = r["total_flops"] <= cap
        r["criteria"] = {"1_ood_first_two_ge_0.90": c1, "2_ge_baseline_best_minus_0.01": c2,
                         "3_total_flops_le_cap": c3, "total_flops_over_cap": r["total_flops"] / cap,
                         "3_alt_failed_teachers_whole_run": r["total_flops_alt"] <= cap,
                         "total_flops_alt_over_cap": r["total_flops_alt"] / cap,
                         "passing_teacher_only_over_cap": r["total_flops_passing_teacher_only"] / cap}
        r["win"] = bool(c1 and c2 and c3)
        if not c3:
            r["loss_confirmed"] = True
    if r["win"] is False:
        if not r["compile"]["reads_correct_positions"]:
            r["failure_stage"] = "compile"
        elif a[L[0]] < STUDENT_MIN:
            r["failure_stage"] = "student in-distribution"
        elif not (r["criteria"]["1_ood_first_two_ge_0.90"] and r["criteria"]["2_ge_baseline_best_minus_0.01"]):
            r["failure_stage"] = "student out-of-distribution"
        else:
            r["failure_stage"] = "flops"
        if r["failure_stage"] == "flops" and r["total_flops_passing_teacher_only"] <= B["cap"]:
            r["failure_type"] = "teacher dependence"
        else:
            r["failure_type"] = "mechanism"
    return r


def main():
    out = {"tasks": {}, "bundles": {b: list(v) for b, v in BUNDLES.items()}}
    for b, tasks in BUNDLES.items():
        for task in tasks:
            L = labels(task)
            B = baselines(task, L)
            seeds = {s: seed_result(task, s, L, B) for s in SEEDS}
            started = bool(B["bos"]) or any(rd(RES, "h0", task, "rope", s).exists() for s in SEEDS)
            wins = [seeds[s].get("win") for s in SEEDS]
            if not started:
                task_win, status = None, "not run"
            elif any(w is False for w in wins):
                task_win, status = False, "lost"
            elif all(w is True for w in wins):
                task_win, status = True, "won"
            else:
                task_win, status = None, "in progress"
            decisive = (task_win and B["best"][L[2]] <= DECISIVE) if task_win is not None else None
            out["tasks"][task] = {"bundle": b, "bins": L, "status": status, "baselines": B, "seeds": seeds,
                                  "win": task_win, "decisive_win": decisive,
                                  "loss_confirmed": any(seeds[s]["loss_confirmed"] for s in SEEDS)}
    ts = out["tasks"].values()
    out["wins"] = sum(1 for t in ts if t["win"])
    out["loss_confirmed_tasks"] = [k for k, t in out["tasks"].items() if t["loss_confirmed"] or t["win"] is False]
    out["answer"] = ("no" if out["loss_confirmed_tasks"] else ("yes" if all(t["win"] for t in ts) else None))
    out["not_run"] = [k for k, t in out["tasks"].items() if t["status"] == "not run"]
    (RES / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("| 과제 | 묶음 | 기준선 최고 분포 안 · 분포 밖 1 · 2 · 3 (최고인 기준선) | FLOPs 상한 (BOS 기준선) | 시드 15 · 16 · 17 이김 | 이김 | 결정적 |")
    print("|---|---|---|---|---|---|---|")
    for task, t in out["tasks"].items():
        L, B = t["bins"], t["baselines"]
        bb = " · ".join("%s (%s)" % (f3(B["best"][l]), B["best_by"][l]) for l in L) if B["best"] else "—"
        w = " · ".join(YN[t["seeds"][s].get("win")] for s in SEEDS)
        print("| %s | %d | %s | %s | %s | %s | %s |" % (NAME[task], t["bundle"], bb, "%.2e (%s)" % (B["cap"], B["cap_by"])
                                                       if B["cap"] else "—", w if t["status"] != "not run" else
                                                       "돌리지 않음", YN[t["win"]], YN[t["decisive_win"]]))
    print("\n| 과제 | 시드 | 교사 (실행 시드: 판정 step, 선택용) | 재시작 | 교사 FLOPs | 사전 확인 비 | 컴파일 (정답 위치) | 선택 | 선택 학생 분포 안 · 분포 밖 1 · 2 · 3 | 합계 FLOPs (상한 대비) | 기준 1 · 2 · 3 | 실패 단계 (유형) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for task, t in out["tasks"].items():
        if t["status"] == "not run":
            continue
        L = t["bins"]
        for s in SEEDS:
            r = t["seeds"][s]
            te = "; ".join("s%d: %d, %s" % (x["run_seed"], x["judgment_step"], f3(x["selection_accuracy"]))
                           for x in r["teachers"]) or "—"
            pr = r.get("precheck", {}).get("ratio")
            pr = ("%.2f" % pr) if isinstance(pr, float) else ("— (all-stay 0)" if "precheck" in r else "—")
            cp = YN[r["compile"]["reads_correct_positions"]] if "compile" in r else "—"
            if "selected" in r:
                st = r["students"][r["selected"]]
                se = "%s (%s)" % (r["selected"], f3(st["selection_accuracy"]))
                ac = " · ".join(f3(st["acc"][l]) for l in L)
                c = r["criteria"]
                fl = ("%.2e (%.2f)" % (r["total_flops"], c["total_flops_over_cap"]) if "total_flops_over_cap" in c
                      else "%.2e" % r["total_flops"])
                cr = " · ".join(YN[c[k]] for k in ("1_ood_first_two_ge_0.90", "2_ge_baseline_best_minus_0.01",
                                                   "3_total_flops_le_cap"))
            else:
                se = ac = fl = cr = "—"
            fs = r.get("failure_stage") or r.get("status") or "없음"
            if r.get("failure_type"):
                fs += " (%s)" % r["failure_type"]
            print("| %s | %d | %s | %d | %.2e | %s | %s | %s | %s | %s | %s | %s |" % (
                NAME[task], s, te, r["teacher_restarts"], r["teacher_flops"], pr, cp, se, ac, fl, cr, fs))
    print("\nwins %d, loss confirmed: %s, not run: %s -> answer %s" % (out["wins"], out["loss_confirmed_tasks"] or "none",
                                                                      out["not_run"] or "none", out["answer"]))


if __name__ == "__main__":
    main()
