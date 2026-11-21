"""G-0' report (stage2/DESIGN.md 7.7, 7.12): win / decisive-win table, failure stages, teacher restarts, selected
students.  The G-0 report (stage2/g0_report.py) with the teacher restart; seeds 12, 13, 14 from stage2/results/g0p;
the baselines are the G-0 ones (stage2/results/g0, seed 0, reused unchanged: the same reference per bin and the same
FLOPs cap).  Run after the selections are committed.

Teacher (7.12): the teacher of seed s (run seed s) is checked on "select:<task>" at its judgment checkpoint
(stage2/g0p_teacher_check.py); < 0.95: the restart teacher (run seed s + 200), checked the same way; still < 0.95:
pipeline failure "teacher (after restart)" (the seed does not win).  The compile uses the teacher that passed.
  total FLOPs        = every teacher trained for the seed (s, and s + 200 when restarted), each to its judgment
                       checkpoint (the C4 rule) + dependency extraction + all four students (each to its judgment
                       checkpoint)
  total FLOPs (alt.) = the same, with a failed teacher counted for its whole run (final.json train_flops); reported
                       with whether criterion 3 would change
  (the teacher checks' and the students' selection evaluations are not training FLOPs and are not counted, as G-0)
Win, decisive win, answer, and the failure stages after the teacher: as stage2/g0_report.py (7.7).

  python stage2/g0p_report.py       # prints markdown tables, writes stage2/results/g0p/summary.json
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "results" / "g0p"
BASE = HERE / "results" / "g0"
sys.path.insert(0, str(HERE))
import g_tasks as G            # noqa: E402
from g0_report import KINDS, MIN_OOD, TOL, DECISIVE, STUDENT_MIN, DIFFERENT, NAME, jl, labels, f3   # noqa: E402

SEEDS = (12, 13, 14)
TEACHER_RESTART = 200
TEACHER_MIN = 0.95
YN = {True: "예", False: "아니오", None: "—"}


def rd(res, phase, task, kind, seed, tag=""):
    return res / ("%s_%s__%s__1M__s%d__N100000%s" % (phase, task, kind, seed, ("__" + tag) if tag else ""))


def baselines(task, L):
    base = {}
    for k in KINDS:
        f = jl(rd(BASE, "g0", task, k, 0) / "final.json")
        if f:
            base[k] = {"judgment_step": f["judgment"]["step"], "acc": f["judgment"]["acc"],
                       "judgment_flops": f["judgment"]["train_flops_cum"], "steps": f["steps"],
                       "stopped": f["stopped"]}
    assert len(base) == len(KINDS), "G-0 baselines incomplete for %s" % task
    best = {l: max(b["acc"][l] for b in base.values()) for l in L}
    best_by = {l: max(base, key=lambda k: base[k]["acc"][l]) for l in L}
    cap = max(b["judgment_flops"] for b in base.values())
    return base, best, best_by, cap


def teachers(task, s, L):
    """the teacher(s) of seed s in order; each with its run, check and FLOPs; and the run seed of the one that passed"""
    out, passed = [], None
    for k, ts in enumerate((s, s + TEACHER_RESTART)):
        f = jl(rd(RES, "g0p", task, "rope", ts) / "final.json")
        if f is None:
            return out, passed, "teacher%s not finished" % (" restart" if k else "")
        c = jl(RES / ("teacher_select_%s_s%d.json" % (task, ts)))
        if c is None:
            return out, passed, "teacher%s check not finished" % (" restart" if k else "")
        assert c["judgment_step"] == f["judgment"]["step"]
        out.append({"run_seed": ts, "restart": k, "judgment_step": f["judgment"]["step"], "steps": f["steps"],
                    "stopped": f["stopped"], "id_at_judgment": f["judgment"]["acc"][L[0]],
                    "selection_accuracy": c["selection_accuracy"], "passed": c["passed"],
                    "judgment_flops": f["judgment"]["train_flops_cum"], "run_flops": f["train_flops"],
                    "check_eval_flops": c["selection_eval_flops"]})
        if c["passed"]:
            passed = ts
            break
    return out, passed, None


def main():
    out = {"tasks": {}, "baselines_from": str(BASE.relative_to(HERE.parent))}
    for task in G.SUITE:
        L = labels(task)
        base, best, best_by, cap = baselines(task, L)
        seeds = {}
        for s in SEEDS:
            r = {"failure_stage": None}
            ts, passed, st = teachers(task, s, L)
            r["teachers"] = ts
            r["teacher_restarted"] = len(ts) > 1 or (st is not None and "restart" in st)
            r["teacher_used"] = passed
            if st:
                r["status"] = st
                seeds[s] = r
                continue
            t_flops = sum(t["judgment_flops"] for t in ts)
            t_flops_alt = sum(t["run_flops"] if not t["passed"] else t["judgment_flops"] for t in ts)
            if passed is None:                           # 7.12: still < 0.95 after the restart: failure
                r["failure_stage"] = "teacher (after restart)"
                r["win"] = False
                seeds[s] = r
                continue
            cr = jl(RES / ("%s_compile_s%d" % (task, s)) / "compile_result.json")
            if cr is None:
                r["status"] = "compile not finished"
                seeds[s] = r
                continue
            pc = cr["precheck"]
            r["precheck"] = {"ratio": pc["dependency"]["ratio"], "correct": pc["dependency"]["correct"],
                             "all_stay": pc["dependency"]["all_stay"], "passed": pc["passed"]}
            r["extraction_flops"] = cr["extraction"]["flops"]
            r["compile_data_seed"] = cr["data_seed"]
            if "policy" not in cr:                        # 7.4: counted as a failure
                r["failure_stage"] = "precheck"
                r["win"] = False
                seeds[s] = r
                continue
            corr = jl(HERE / ("results/g0a/tables.json" if task != "prefix_sum" else
                              "results/g0/a_prefix_sum/tables.json"))[task]["table"]
            moving = [j for j in range(3) if any(m != 0 for m in corr[j])]
            agree = cr["reference_agreement_with_correct_table"]
            ag = {j: agree["correct_head%d_position_read_by_some_compiled_head" % j] for j in moving}
            r["compile"] = {"policy": cr["policy"], "policy_named": cr["policy_named"],
                            "agreement_moving_correct_heads": ag,
                            "reads_correct_positions": all(v >= 0.99 for v in ag.values()),
                            "compiled_all_stay": all(m == 0 for c in cr["policy"] for m in c)}
            sel = jl(RES / ("selection_%s_s%d.json" % (task, s)))
            if sel is None:
                r["status"] = "selection not committed"
                seeds[s] = r
                continue
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
            r["flops"] = {"teachers": t_flops, "teachers_alt": t_flops_alt, "extraction": r["extraction_flops"],
                          "students": s_flops}
            r["total_flops"] = t_flops + r["extraction_flops"] + s_flops
            r["total_flops_alt"] = t_flops_alt + r["extraction_flops"] + s_flops
            a = studs[sel["selected"]]["acc"]
            o1, o2 = a[L[1]], a[L[2]]
            c1 = o1 >= MIN_OOD and o2 >= MIN_OOD
            c2 = o1 >= best[L[1]] - TOL and o2 >= best[L[2]] - TOL
            c3 = r["total_flops"] <= cap
            c3_alt = r["total_flops_alt"] <= cap
            r["criteria"] = {"1_ood_first_two_ge_0.90": c1, "2_ge_baseline_best_minus_0.01": c2,
                             "3_total_flops_le_cap": c3, "total_flops_over_cap": r["total_flops"] / cap,
                             "3_alt_failed_teacher_whole_run": c3_alt,
                             "total_flops_alt_over_cap": r["total_flops_alt"] / cap,
                             "criterion_3_changes_with_alt": c3 != c3_alt}
            r["win"] = bool(c1 and c2 and c3)
            if not r["win"]:
                if not r["compile"]["reads_correct_positions"]:
                    r["failure_stage"] = "compile"
                elif a[L[0]] < STUDENT_MIN:
                    r["failure_stage"] = "student in-distribution"
                elif not (c1 and c2):
                    r["failure_stage"] = "student out-of-distribution"
                else:
                    r["failure_stage"] = "flops"
            seeds[s] = r
        wins = [seeds[s].get("win") for s in SEEDS]
        task_win = all(w is True for w in wins) if all(w is not None for w in wins) else None
        if task_win is None and any(w is False for w in wins):
            task_win = False
        decisive = (task_win and best[L[2]] <= DECISIVE) if task_win is not None else None
        out["tasks"][task] = {"bins": L, "baselines": base, "baseline_best": best, "baseline_best_by": best_by,
                              "flops_cap": cap, "seeds": seeds, "win": task_win, "decisive_win": decisive,
                              "different_structure_from_addition": task in DIFFERENT}
    ws = [t["win"] for t in out["tasks"].values()]
    n = sum(1 for w in ws if w)
    out["wins"] = n
    out["answer"] = (None if any(w is None for w in ws) else ("yes" if n >= 4 else ("no" if n <= 2 else "undecided")))
    out["teacher_restarts"] = ["%s s%d" % (task, s) for task, t in out["tasks"].items() for s in SEEDS
                               if t["seeds"][s]["teacher_restarted"]]
    (RES / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    # tables
    print("| 과제 | 기준선 최고 분포 안 · 분포 밖 1 · 2 · 3 (최고인 기준선, G-0) | FLOPs 상한 | 시드 12 · 13 · 14 이김 | 이김 | 결정적 이김 |")
    print("|---|---|---|---|---|---|")
    for task, t in out["tasks"].items():
        L = t["bins"]
        bb = " · ".join("%s (%s)" % (f3(t["baseline_best"][l]), t["baseline_best_by"][l]) for l in L)
        w = " · ".join(YN[t["seeds"][s].get("win")] for s in SEEDS)
        print("| %s%s | %s | %.2e | %s | %s | %s |" % (NAME[task], " *" if t["different_structure_from_addition"]
                                                     else "", bb, t["flops_cap"], w, YN[t["win"]],
                                                     YN[t["decisive_win"]]))
    print("\n| 과제 | 시드 | 교사 (실행 시드: 판정 step, 선택용 분포 안) | 재시작 | 사전 확인 비 | 컴파일 표 (정답 위치 읽음) | 선택 (선택용 검증) | 선택 학생 분포 안 · 분포 밖 1 · 2 · 3 | 합계 FLOPs (상한 대비; 실패 교사 전체 실행) | 기준 1 · 2 · 3 | 실패 단계 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for task, t in out["tasks"].items():
        L = t["bins"]
        for s in SEEDS:
            r = t["seeds"][s]
            te = "; ".join("s%d: %d, %s" % (x["run_seed"], x["judgment_step"], f3(x["selection_accuracy"]))
                           for x in r["teachers"]) or "—"
            pr = "%.2f" % r["precheck"]["ratio"] if r.get("precheck") and r["precheck"]["ratio"] else "—"
            cp = YN[r["compile"]["reads_correct_positions"]] if "compile" in r else "—"
            if "selected" in r:
                st = r["students"][r["selected"]]
                se = "%s (%s)" % (r["selected"], f3(st["selection_accuracy"]))
                ac = " · ".join(f3(st["acc"][l]) for l in L)
                c = r["criteria"]
                fl = "%.2e (%.2f%s)" % (r["total_flops"], c["total_flops_over_cap"],
                                        "; %.2f" % c["total_flops_alt_over_cap"] if r["teacher_restarted"] else "")
                cr = " · ".join(YN[c[k]] for k in ("1_ood_first_two_ge_0.90", "2_ge_baseline_best_minus_0.01",
                                                   "3_total_flops_le_cap"))
            else:
                se = ac = fl = cr = "—"
            print("| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                NAME[task], s, te, YN[r["teacher_restarted"]], pr, cp, se, ac, fl, cr,
                r.get("failure_stage") or r.get("status") or "없음"))
    print("\nteacher restarts: %s" % (", ".join(out["teacher_restarts"]) or "none"))
    print("wins %d -> answer %s" % (n, out["answer"]))


if __name__ == "__main__":
    main()
