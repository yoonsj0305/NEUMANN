"""Append one finished Phase A' / A'' run to stage1/RESULTS.md (CLAUDE.md "결과 기록" format) and commit + push its raw
records with the entry.  Values are copied from the run's final.json / config.json / env.json; nothing is
recomputed.  The answer line applies the Phase A' pass criterion (CLAUDE.md) to the runs finished so far.

  python stage1/record_run.py stage1/results/phaseA2/<run name> [--no-git]
"""
from __future__ import annotations
import argparse
import json
import pathlib
import subprocess
import time

HERE = pathlib.Path(__file__).resolve().parent
PH = HERE / "results" / "phaseA2"
NAME_T = {"addition": "덧셈", "parity": "패리티", "assoc": "연관 기억", "assoc_n4": "연관 기억 (n=4 고정)",
          "mqar": "MQAR", "mqar_n4": "MQAR (n=4 고정)"}
NAME_K = {"abacus": "Abacus", "looped": "looped", "gru": "GRU", "looped_rr": "looped_rr", "rope": "rope",
          "pf": "PF", "pf_cont": "PF-cont", "pf2": "PF (C1-2)", "pf_search": "PF-search"}
# C1-1 values of the same task (RESULTS.md "C1-1 요약", commit faa9181): judgment checkpoint
C11_REF = {
    "addition": "PF 분포 안 0.005 · 분포 밖 0.000 · 0.000 · 0.000 (PF-cont 0.393 · 0.132 · 0.084 · 0.038); "
                "판정 시점까지 학습 FLOPs 4.90e+13",
    "parity": "PF 분포 안 1.000 · 분포 밖 1.000 · 1.000 · 1.000; 판정 시점까지 학습 FLOPs 6.34e+12",
    "mqar": "PF 질의별 분포 안 0.989 · 분포 밖 0.993 · 0.997 · 0.998, 시퀀스 전체 0.922 · 0.876 · 0.904 · 0.910; "
            "판정 시점까지 학습 FLOPs 4.41e+13",
}
# frozen baseline reference (CANDIDATE_DESIGN.md 7, from RESULTS.md 1단계 기준선 표, commit 29559d3)
BASE_REF = {
    "addition": "분포 안 최고 0.998 (abacus) · 분포 밖 11-20: 0.278 (looped_rr) · 21-30: 0.000 · 31-40: 0.000; "
                "판정 시점까지 학습 FLOPs 5.18e+14 (looped_rr)",
    "parity": "분포 안 최고 1.000 (gru) · 분포 밖 17-32: 1.000 · 33-48: 1.000 · 49-64: 1.000 (gru); "
              "판정 시점까지 학습 FLOPs 1.19e+13 (gru)",
    "mqar": "질의별 분포 안 최고 1.000 (rope) · 분포 밖 17-32: 0.978 · 33-48: 0.932 · 49-64: 0.844 (looped_rr); "
            "판정 시점까지 학습 FLOPs 2.68e+14 (looped_rr)",
}
PH3 = HERE / "results" / "phaseA3"
Q3 = "Phase A″ — `rope`가 연관 기억 분포 안 ≥95%인가? (실패하면 하네스 문제로 보고 디버그 허용)"
Q3C = ("Phase A″ 실행 전 점검 — `rope`가 연관 기억 n=4 고정, 2,000 step에서 분포 안 ≥95%인가? "
       "(안 되면 본실행 전에 멈추고 보고)")


PH4 = HERE / "results" / "phaseA4"
Q4C = "Phase A‴ 작업 1 점검 — `rope`가 MQAR n=4 고정, 2,000 step에서 질의별 분포 안 ≥95%인가? (아니면 MQAR 본실행 없이 중단)"
Q4 = ("Phase A‴ 작업 1 — 표준 MQAR에서 트랜스포머 기준선(rope, abacus, looped_rr)이 학습되는가? "
      "(질의별 분포 안 ≥95%를 기준으로 답함)")
Q4B = "Phase A‴ 작업 2 — `rope`가 %s 분포 안을 학습하는가? (1단계 기준선 표용; ≥95%%를 기준으로 답함)"


def answer4(f):
    v = idv(f)
    if f["task"] == "mqar_n4":
        return "%s (질의별 분포 안 %.3f)" % ("예" if v >= 0.95 else "아니오 — MQAR 본실행 없이 중단", v)
    if f["task"] == "mqar":
        done = {}
        for k in ("rope", "abacus", "looped_rr"):
            d = PH4 / ("phaseA4_mqar__%s__1M__s0__N100000" % k)
            if (d / "final.json").exists():
                done[k] = idv(json.loads((d / "final.json").read_text()))
        txt = ", ".join("%s %.3f" % (NAME_K[k], x) for k, x in done.items())
        if any(x >= 0.95 for x in done.values()):
            return "예 (질의별 분포 안: %s)" % txt
        if len(done) == 3:
            return "아니오 (질의별 분포 안: %s)" % txt
        return "미정 (끝난 트랜스포머 기준선: %s)" % (txt or "없음")
    return "%s (분포 안 %.3f)" % ("예" if v >= 0.95 else "아니오", v)


def answer_c1(f):
    v = idv(f)
    if f["task"] == "mqar":
        return "미정 — MQAR은 판정 기준 없음, 숫자만 보고 (질의별 분포 안 %.3f)" % v
    return "%s (분포 안 %.3f; 유효성 기준 ≥0.95)" % ("예" if v >= 0.95 else "아니오", v)


def labels(phase, task, kind="pf"):
    """(heading label, question, commit label) for a run"""
    if phase == "c1_2" and kind == "pf_search":
        return ("C1-2 분기 2단계 (PF-search)",
                "C1-2 분기 2단계 — PF-search(설계서 11절)로 찾은 이동 정책 표와 경사하강 갱신 제어기가 %s를 학습 분포 "
                "안에서 배우는가? (유효성 기준 ≥0.95; 판정 FLOPs = 탐색 + 최종 학습)" % NAME_T[task], "C1-2 PF-search")
    if phase == "c1_2":
        q = ("C1-2 — 이동 학습 추정기를 바꾼 PF가 %s를 학습 분포 안에서 배우는가? (유효성 기준: 분포 안 ≥0.95, 시드 0)"
             % NAME_T[task] if task != "mqar" else "C1-2 — PF(C1-2)의 MQAR 결과 (판정 기준 없음; 질의별·시퀀스 전체 보고)")
        return "C1-2", q, "C1-2"
    if phase == "c1":
        if kind == "pf_cont":
            return ("C1-1 분기 2단계 (PF-cont)",
                    "C1-1 분기 2단계 — 이산화를 뺀 PF-cont가 %s를 학습 분포 안에서 배우는가? (유효성 기준 ≥0.95; "
                    "PF가 실패하고 버그 점검에서 구현 결함이 없을 때 1회)" % NAME_T[task], "C1-1 PF-cont")
        q = ("C1-1 — PF가 %s를 학습 분포 안에서 배우는가? (유효성 기준: 분포 안 ≥0.95, 시드 0)" % NAME_T[task]
             if task != "mqar" else "C1-1 — PF의 MQAR 결과 (판정 기준 없음; 질의별·시퀀스 전체 보고)")
        return "C1-1", q, "C1-1"
    if phase == "phaseA4":
        if task == "mqar_n4":
            return "Phase A‴ 작업 1 점검", Q4C, "Phase A‴ 점검"
        if task == "mqar":
            return "Phase A‴ 작업 1", Q4, "Phase A‴ 작업 1"
        return "Phase A‴ 작업 2", Q4B % NAME_T[task], "Phase A‴ 작업 2"
    if phase == "phaseA3":
        if task == "assoc_n4":
            return "Phase A″ 실행 전 점검", Q3C, "Phase A″ 점검"
        return "Phase A″ 작업", Q3, "Phase A″"
    work = "작업 1" if task == "assoc" else "작업 2"
    return "Phase A′ %s" % work, (Q1 if task == "assoc" else Q2), "Phase A′ %s" % work


def answer3(f):
    if f["task"] == "assoc_n4":
        v = idv(f)
        return "%s (분포 안 %.3f)" % ("예" if v >= 0.95 else "아니오 — 본실행 전에 멈추고 보고", v)
    d = PH3 / "phaseA3_assoc__rope__1M__s0__N100000"
    if not (d / "final.json").exists():
        return "미정 (연관 기억 rope 실행이 아직 끝나지 않음)"
    v = idv(json.loads((d / "final.json").read_text()))
    return "%s (연관 기억 rope 분포 안 %.3f)" % ("예" if v >= 0.95 else "아니오 — 하네스 문제로 보고 디버그", v)
Q1 = ("Phase A′ 작업 1 — 트랜스포머 기준선(Abacus, looped) 중 하나 이상이 연관 기억 분포 안 ≥95%인가? "
      "(못 하면 과제 형식 버그로 보고 멈춘다)")
Q2 = "Phase A′ 작업 2 — looped_rr이 덧셈 분포 안 ≥95%를 유지하는가? (분포 밖은 숫자만, 기준 없음)"


def load(name):
    d = PH / name
    if not (d / "final.json").exists():
        return None
    return json.loads((d / "final.json").read_text())


def idv(f):
    return [v for l, v in f["judgment"]["acc"].items() if l.startswith("id")][0]


def answer(task, kind):
    if task == "assoc":
        runs = {k: load("phaseA2_assoc__%s__1M__s0__N100000" % k) for k in ("abacus", "looped")}
        done = {k: idv(f) for k, f in runs.items() if f}
        if any(v >= 0.95 for v in done.values()):
            return "예 (%s)" % ", ".join("%s %.3f" % (NAME_K[k], v) for k, v in done.items())
        if len(done) == 2:
            return "아니오 (%s) — CLAUDE.md에 따라 과제 형식 버그로 보고 멈춤" % ", ".join(
                "%s %.3f" % (NAME_K[k], v) for k, v in done.items())
        return "미정 (끝난 트랜스포머: %s)" % (", ".join("%s %.3f" % (NAME_K[k], v) for k, v in done.items()) or "없음")
    f = load("phaseA2_addition__looped_rr__1M__s0__N100000")
    if f is None:
        return "미정 (덧셈 looped_rr 실행이 아직 끝나지 않음)"
    v = idv(f)
    return "%s (덧셈 looped_rr 분포 안 %.3f)" % ("예" if v >= 0.95 else "아니오", v)


def entry(d):
    f = json.loads((d / "final.json").read_text())
    cfg = json.loads((d / "config.json").read_text())
    env = json.loads((d / "env.json").read_text())
    t, k = f["task"], f["kind"]
    j, last = f["judgment"], f["last"]
    lab = lambda l: l.split("_", 1)[1]
    oods = " · ".join("%s: %.3f" % (lab(l), v) for l, v in j["acc"].items() if l.startswith("ood"))
    oods_last = " · ".join("%s: %.3f" % (lab(l), v) for l, v in last["acc"].items() if l.startswith("ood"))
    phase = cfg.get("phase", "phaseA2")
    head, question, _ = labels(phase, t, k)
    date = time.strftime("%Y-%m-%d", time.gmtime())
    lines = [
        "## %s · %s · %s / %s" % (date, head, NAME_T[t], NAME_K[k]),
        "- 질문: %s" % question,
        "- 질문에 대한 답: %s" % (answer_c1(f) if phase in ("c1", "c1_2") else answer4(f) if phase == "phaseA4" else
                                  answer3(f) if phase == "phaseA3" else answer(t, k)),
        "- 코드 커밋: `%s`%s · 원자료: `%s/`" % (
            (env.get("code_commit") or "?")[:7], " (작업 트리 수정 있음)" if env.get("code_dirty") else "",
            d.relative_to(HERE.parent) if HERE.parent in d.parents else d),
        "- 결과 표 (판정 체크포인트 = 분포 안 최고 시점, 동률이면 이른 시점; 분포 밖은 그 시점 값):",
        "",
        "| 과제 | 기준선 | 규모 | 데이터 수 | 분포 안 정확도 | 분포 밖 정확도(구간별) | 학습 FLOPs | 시간 (학습 / 평가) |",
        "|---|---|---|---|---|---|---|---|",
        "| %s | %s | %s | %s | %.3f (step %d) | %s | %.2e (판정 시점까지) / %.2e (전체) | %.0f s / %.0f s |" % (
            NAME_T[t], NAME_K[k], format(f["params"], ","), format(f["N"], ","), idv(f), j["step"], oods,
            j["train_flops_cum"], f["train_flops"], f["wall_train_s"], f["wall_eval_s"]),
        "",
        "- 마지막 시점 (step %d): 분포 안 %.3f · 분포 밖 %s" % (
            last["step"], [v for l, v in last["acc"].items() if l.startswith("id")][0], oods_last),
    ]
    if phase in ("c1", "c1_2") and t in BASE_REF:
        lines.append("- 같은 과제의 기준선 최고값 (동결, 설계서 7절): %s" % BASE_REF[t])
    if k == "pf_search" and cfg.get("pf_search"):
        sr = cfg["pf_search"]["search"]
        lines.append("- PF-search 탐색: 평가 %d회, 탐색 FLOPs %.2e, 정지 사유 — %s, 탐색 점수(분포 안 검증) %.3f; 찾은 표: %s"
                     % (sr["evaluations"], sr["search_flops"], sr["stopped"], sr["best_score_in_distribution_validation"],
                        "; ".join("%s: %s" % (h, ", ".join("%s→%s" % (c, mv) for c, mv in row.items() if mv != "stay")
                                                  or "모두 stay") for h, row in sr["policy_named"].items())))
        lines.append("- 판정 FLOPs (탐색 + 최종 학습 판정 시점까지): %.2e + %.2e = %.2e" % (
            sr["search_flops"], j["train_flops_cum"], sr["search_flops"] + j["train_flops_cum"]))
    if phase == "c1_2" and t in C11_REF:
        lines.append("- 같은 과제의 C1-1 값: %s" % C11_REF[t])
    if f.get("judgment", {}).get("train_move_signal_mean") is not None:
        pass
    if j.get("acc_seq"):
        lines.append("- 시퀀스 전체 정답률 (보조, 판정 시점): %s" % " · ".join(
            "%s: %.3f" % (lab(l), v) for l, v in j["acc_seq"].items()))
    if j.get("acc_fixed4"):
        lines.append("- looped 보조 (고정 4회, 판정 시점): %s" % " · ".join(
            "%s: %.3f" % (lab(l), v) for l, v in j["acc_fixed4"].items()))
        lines.append("- looped 주 결과의 반복 횟수: %s" % ", ".join("%s → %d" % (lab(l), r) for l, r in f["recur"].items()))
    if k == "looped_rr":
        lines.append("- looped_rr 학습: 반복 %s 균등, progressive loss α = %s (%s)" % (
            cfg["looped_rr"]["iterations"], cfg["looped_rr"]["progressive_alpha"], cfg["looped_rr"]["progressive"]))
    segs = f["segments"]
    lines.append("- 이상 사항 / 중단·재개 기록: 종료 사유 — %s; 실행 구간 %d개%s. 실행 환경 %s, %d코어, 1스레드, torch %s, "
                 "GPU 없음." % (
                     f["stopped"], len(segs),
                     "" if len(segs) == 1 else " (세션 백그라운드 2시간 한도로 중단 후 마지막 체크포인트에서 재개: %s)" %
                     ", ".join("구간 %d step %d부터" % (s["segment"], s["start_step"]) for s in segs[1:]),
                     env["cpu"], env["cores"], env["torch"]))
    return "\n".join(lines) + "\n", f, j


def main(a):
    d = pathlib.Path(a.run_dir).resolve()
    text, f, j = entry(d)
    res = HERE / "RESULTS.md"
    with open(res, "a") as fh:
        fh.write("\n" + text)
    print(text)
    if a.no_git:
        return
    root = HERE.parent
    cfg = json.loads((d / "config.json").read_text())
    msg = "stage1 %s: %s %s (분포 안 %.3f @ step %d)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n" \
          "Claude-Session: https://claude.ai/code/session_01VSWBvg7gXA6QqLM5pig7M5\n" % (
              labels(cfg.get("phase", "phaseA2"), f["task"], f["kind"])[2], f["task"], f["kind"], idv(f), j["step"])
    files = [str(res.relative_to(root)), str(d.relative_to(root))]
    if (d.parent / "QUEUE_LOG.txt").exists():
        files.append(str((d.parent / "QUEUE_LOG.txt").relative_to(root)))
    subprocess.check_call(["git", "add"] + files, cwd=root)
    subprocess.check_call(["git", "commit", "-q", "-m", msg], cwd=root)
    for i in range(4):
        if subprocess.call(["git", "push", "-u", "origin", "stage1/baselines"], cwd=root) == 0:
            break
        time.sleep(2 ** (i + 1))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run_dir")
    p.add_argument("--no-git", action="store_true")
    main(p.parse_args())
