"""G-0 report (stage2/DESIGN.md 7.7, 7.10): win / decisive-win table, failure stages, selected students.  Reads the
result files of stage2/results/g0 only (run after the selections are committed).

Per task, baselines (abacus, rope, looped_rr, gru; seed 0; stage-1 protocol): the value of each at its judgment
checkpoint (highest in-distribution, earliest if tied; looped_rr with its stage-1 primary rule); the reference per
bin = the highest of the four; the FLOPs cap = the largest judgment-checkpoint training FLOPs of the four.
Per task and seed (9, 10, 11): teacher, pre-check, compile, the four students, the selected one.
  total FLOPs = teacher (to its judgment checkpoint) + dependency extraction + all students (each to its judgment
                checkpoint) -- the C4 rule with all four students (7.4)
  win (7.7)   the selected student at its judgment checkpoint: 1. the first two out-of-distribution bins >= 0.90;
              2. both >= baseline best - 0.01; 3. total FLOPs <= the cap; a task wins iff all three seeds win
  decisive    a winning task whose baseline best on the second out-of-distribution bin is <= 0.60
  answer      >= 4 tasks win: yes; <= 2: no; 3: undecided
Failure stage of a task and seed (the first in pipeline order): teacher (in-distribution < 0.95), pre-check (ratio <
2), compile (the compiled table does not read the correct table's positions: a moving head of the correct table
whose read position is read by no compiled head at >= 1 % of output steps), student in-distribution (selected
student < 0.95, the stage-1 validity level), student out-of-distribution (criterion 1 or 2), FLOPs (criterion 3).
The compile stage is reported for a seed that does not win, the agreement value is recorded for every seed.

  python stage2/g0_report.py        # prints markdown tables, writes stage2/results/g0/summary.json
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "results" / "g0"
sys.path.insert(0, str(HERE))
import g_tasks as G            # noqa: E402

SEEDS = (9, 10, 11)
KINDS = ("abacus", "rope", "looped_rr", "gru")
MIN_OOD, TOL, DECISIVE, TEACHER_MIN, STUDENT_MIN = 0.90, 0.01, 0.60, 0.95, 0.95
DIFFERENT = {"copy", "reverse", "mul1", "prefix_sum"}          # 7.10: "different structure from addition"
NAME = {"copy": "복사", "reverse": "뒤집기", "xor": "자리별 XOR", "mul1": "N×1 곱셈", "prefix_sum": "누적합 mod 10"}


def jl(p):
    p = pathlib.Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def rd(task, kind, seed, tag=""):
    return RES / ("g0_%s__%s__1M__s%d__N100000%s" % (task, kind, seed, ("__" + tag) if tag else ""))


def labels(task):
    sp = G.SPEC[task]
    return ["id_%d-%d" % sp["id"]] + ["ood_%d-%d" % b for b in sp["ood"]]


def f3(x):
    return "—" if x is None else "%.3f" % x


def main():
    out = {"tasks": {}}
    for task in G.SUITE:
        L = labels(task)
        base = {}
        for k in KINDS:
            f = jl(rd(task, k, 0) / "final.json")
            if f:
                base[k] = {"judgment_step": f["judgment"]["step"], "acc": f["judgment"]["acc"],
                           "judgment_flops": f["judgment"]["train_flops_cum"], "steps": f["steps"],
                           "stopped": f["stopped"], "wall_s": f["wall_train_s"] + f["wall_eval_s"]}
        complete = len(base) == len(KINDS)
        best = {l: max(b["acc"][l] for b in base.values()) for l in L} if base else None
        best_by = {l: max(base, key=lambda k: base[k]["acc"][l]) for l in L} if base else None
        cap = max(b["judgment_flops"] for b in base.values()) if base else None
        seeds = {}
        for s in SEEDS:
            r = {"failure_stage": None}
            tf = jl(rd(task, "rope", s) / "final.json")
            if tf is None:
                r["status"] = "teacher not finished"
                seeds[s] = r
                continue
            r["teacher"] = {"judgment_step": tf["judgment"]["step"], "id": tf["judgment"]["acc"][L[0]],
                            "judgment_flops": tf["judgment"]["train_flops_cum"], "steps": tf["steps"],
                            "stopped": tf["stopped"]}
            if r["teacher"]["id"] < TEACHER_MIN:
                r["failure_stage"] = "teacher"
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
            if "policy" not in cr:
                r["failure_stage"] = "precheck"
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
            studs = {}
            total = r["teacher"]["judgment_flops"] + r["extraction_flops"]
            for key, st in sel["students"].items():
                f = jl(pathlib.Path(HERE.parent / st["run"]) / "final.json")
                studs[key] = {"run": st["run"], "selection_accuracy": st["selection_accuracy"],
                              "moving_heads": st["moving_heads"], "judgment_step": f["judgment"]["step"],
                              "acc": f["judgment"]["acc"], "judgment_flops": f["judgment"]["train_flops_cum"],
                              "steps": f["steps"], "stopped": f["stopped"]}
                total += studs[key]["judgment_flops"]
            r["students"] = studs
            r["selected"] = sel["selected"]
            r["selection_reason"] = sel["reason"]
            r["total_flops"] = total
            a = studs[sel["selected"]]["acc"]
            o1, o2 = a[L[1]], a[L[2]]
            c1 = o1 >= MIN_OOD and o2 >= MIN_OOD
            c2 = (best is not None and o1 >= best[L[1]] - TOL and o2 >= best[L[2]] - TOL) if complete else None
            c3 = (total <= cap) if complete else None
            r["criteria"] = {"1_ood_first_two_ge_0.90": c1, "2_ge_baseline_best_minus_0.01": c2,
                             "3_total_flops_le_cap": c3, "total_flops_over_cap": (total / cap) if complete else None}
            r["win"] = bool(c1 and c2 and c3) if complete else None
            if r["win"] is False:
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
        decisive = (task_win and best[L[2]] <= DECISIVE) if (task_win is not None and best) else None
        out["tasks"][task] = {"bins": L, "baselines": base, "baseline_best": best, "baseline_best_by": best_by,
                              "flops_cap": cap, "seeds": seeds, "win": task_win, "decisive_win": decisive,
                              "different_structure_from_addition": task in DIFFERENT}
    ws = [t["win"] for t in out["tasks"].values()]
    n = sum(1 for w in ws if w)
    out["wins"] = n
    out["answer"] = (None if any(w is None for w in ws) else ("yes" if n >= 4 else ("no" if n <= 2 else "undecided")))
    (RES / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    # tables
    print("| 과제 | 기준선 최고 분포 안 · 분포 밖 1 · 2 · 3 (최고인 기준선) | FLOPs 상한 (가장 큰 판정 시점) | 시드 9 · 10 · 11 이김 | 이김 | 결정적 이김 |")
    print("|---|---|---|---|---|---|")
    for task, t in out["tasks"].items():
        L = t["bins"]
        bb = (" · ".join("%s (%s)" % (f3(t["baseline_best"][l]), t["baseline_best_by"][l]) for l in L)
              if t["baseline_best"] else "—")
        w = " · ".join({True: "예", False: "아니오", None: "—"}[t["seeds"][s].get("win")] for s in SEEDS)
        print("| %s%s | %s | %s | %s | %s | %s |" % (NAME[task], " *" if t["different_structure_from_addition"] else "",
                                                bb, "%.2e" % t["flops_cap"] if t["flops_cap"] else "—", w,
                                                {True: "예", False: "아니오", None: "—"}[t["win"]],
                                                {True: "예", False: "아니오", None: "—"}[t["decisive_win"]]))
    print("\n| 과제 | 시드 | 교사 분포 안 | 사전 확인 비 | 컴파일 표 (정답 위치 읽음) | 선택 (선택용 검증) | 선택 학생 분포 안 · 분포 밖 1 · 2 · 3 | 합계 FLOPs (상한 대비) | 기준 1 · 2 · 3 | 실패 단계 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for task, t in out["tasks"].items():
        L = t["bins"]
        for s in SEEDS:
            r = t["seeds"][s]
            te = f3(r["teacher"]["id"]) if "teacher" in r else "—"
            pr = "%.2f" % r["precheck"]["ratio"] if r.get("precheck") and r["precheck"]["ratio"] else "—"
            cp = ("예" if r["compile"]["reads_correct_positions"] else "아니오") if "compile" in r else "—"
            if "selected" in r:
                st = r["students"][r["selected"]]
                se = "%s (%s)" % (r["selected"], f3(st["selection_accuracy"]))
                ac = " · ".join(f3(st["acc"][l]) for l in L)
                fl = "%.2e (%s)" % (r["total_flops"], "%.2f" % r["criteria"]["total_flops_over_cap"]
                                    if r["criteria"]["total_flops_over_cap"] else "—")
                cr = " · ".join({True: "예", False: "아니오", None: "—"}[r["criteria"][k]] for k in
                                ("1_ood_first_two_ge_0.90", "2_ge_baseline_best_minus_0.01", "3_total_flops_le_cap"))
            else:
                se = ac = fl = cr = "—"
            print("| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (NAME[task], s, te, pr, cp, se, ac, fl, cr,
                                                                          r.get("failure_stage") or r.get("status") or "없음"))
    print("\nwins %d -> answer %s" % (n, out["answer"]))


if __name__ == "__main__":
    main()
