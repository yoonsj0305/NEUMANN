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


def c12_ref(task):
    """C1-2 values of the same task, read from the C1-2 runs' final.json (judgment checkpoint)"""
    out = []
    for k in ("pf2", "pf_search"):
        d = HERE / "results" / "c1_2" / ("c1_2_%s__%s__1M__s0__N100000" % (task, k))
        if not (d / "final.json").exists():
            continue
        f = json.loads((d / "final.json").read_text())
        j = f["judgment"]
        txt = "%s 분포 안 %.3f · 분포 밖 %s; 판정 시점까지 학습 FLOPs %.2e" % (
            NAME_K[k], idv(f), " · ".join("%.3f" % v for l, v in j["acc"].items() if l.startswith("ood")),
            j["train_flops_cum"])
        if k == "pf_search":
            c = json.loads((d / "config.json").read_text())
            txt += " (+ 탐색 %.2e)" % c["pf_search"]["search"]["search_flops"]
        out.append(txt)
    return " / ".join(out)


# C1 best values of the same task (RESULTS.md C1-1 / C1-2 / C1-3 summaries): judgment checkpoint
C1_BEST = {
    "addition": "PF-cont (C1-1) 분포 안 0.393 · 분포 밖 0.132 · 0.084 · 0.038; 판정 시점까지 학습 FLOPs 1.06e+14 "
                "(그 밖의 C1: PF-search v2 (C1-3) 0.121, PF (C1-2) 0.018, PF (C1-1) 0.005)",
    "parity": "PF (C1-1) 분포 안 1.000 · 분포 밖 1.000 · 1.000 · 1.000; 판정 시점까지 학습 FLOPs 6.34e+12",
    "mqar": "PF (C1-1) 질의별 분포 안 0.989 · 분포 밖 0.993 · 0.997 · 0.998, 시퀀스 전체 0.922 · 0.876 · 0.904 · "
            "0.910; 판정 시점까지 학습 FLOPs 4.41e+13",
}


def c3_lines(d, f, cfg):
    """C3-1 student: the compiled table, the pre-check and the FLOPs of every stage (13.3)"""
    t = f["task"]
    cr = cfg["pf_search"]["search"]
    tf = cr["teacher"]["train_flops_to_judgment"]       # 0 for the C3-2 control (teacher before training)
    ef = cr["extraction"]["flops"]
    sf = f["judgment"]["train_flops_cum"]
    pc = cr["precheck"]["dependency"]
    src = ("- 교사: 학습 전 rope (무작위 초기화, 시드 %d; C3-2 대조군), 의존도 데이터 시드 %d" % (
               cr["teacher"]["untrained_seed"], cr.get("data_seed", 0)) if cr["teacher"].get("untrained_seed") is not None
           else "- 교사: `%s` (step %d), 의존도 데이터 시드 %d" % (cr["teacher"]["path"], cr["teacher"]["step"],
                                                               cr.get("data_seed", 0)))
    return [src, "- 표 파일: `%s`%s" % (cfg["pf_search"]["policy_file"],
                                       "; 사전 확인은 기록만 하고 적용하지 않음 (C3-1 판정)"
                                       if cr["precheck"].get("gate_applied") is False else ""),
        "- 사전 확인 (13.2): 의존도 점수 정답 표 %.4f · 전부 정지 표 %.4f (비 %.2f, 기준 ≥2); 주의 가중치(보조) %.4f · %.4f"
        % (pc["correct"], pc["all_stay"], pc["ratio"], cr["precheck"]["attention_aux"]["correct"],
           cr["precheck"]["attention_aux"]["all_stay"]),
        "- 컴파일된 표 (stay가 아닌 칸): %s; 헤드별 덮은 의존도 %s" % (
            "; ".join("%s: %s" % (h, ", ".join("%s→%s" % (c, mv) for c, mv in row.items() if mv != "stay") or "모두 stay")
                      for h, row in cr["policy_named"].items()),
            " · ".join("%.4f" % ph["score_after_cover"] for ph in cr["per_head"])),
        "- 참고 (판정 무관): 정답 표 헤드가 읽는 자리를 컴파일된 표의 어느 헤드가 읽는 비율 %s" % " · ".join(
            "%.3f" % v for v in cr["reference_agreement_with_correct_table"].values()),
        "- 단계별 FLOPs (13.3): 교사(판정 시점까지) %.2e + 의존도 추출 %.2e + 학생(판정 시점까지) %.2e = **%.2e**; "
        "표 탐색은 헤드 시뮬레이션 연산 %.2e회 (FLOPs와 별도; 서로 다른 경로 %d개로 열 %d개 전부의 점수를 얻음)"
        % (tf, ef, sf, tf + ef + sf, cr["search"]["head_simulation_operations"],
           cr["search"]["distinct_paths_simulated"], cr["search"]["columns"]),
    ]


def c32_labels(f):
    """C3-2 runs (the control, the parity student, seeds 1 and 2): (heading, question, commit label), else None"""
    t, k, sd = f["task"], f["kind"], f["seed"]
    ctrl = "ctrl" in f["name"].split("__")[-1]
    if not (sd != 0 or ctrl or (t == "parity" and k == "pf_search")):
        return None
    if k == "rope":
        return ("C3-2 교사 (시드 %d)" % sd,
                "C3-2 4단계 — 시드 %d 교사 `rope` 학습 (기준선 규약; 판정 체크포인트를 교사로 로컬 보관)" % sd,
                "C3-2 교사 s%d" % sd)
    if ctrl:
        return ("C3-2 대조군",
                "C3-2 대조군 — 학습 전(무작위 초기화, 시드 %d) 교사에서 같은 방법으로 컴파일한 표의 학생이 %s를 분포 안에서 "
                "배우는가? 분포 밖에서는? (결과가 교사의 학습에서 왔는지 확인; 판정은 설계 채팅)" % (sd, NAME_T[t]),
                "C3-2 대조군")
    return ("C3-2 학생 (시드 %d)" % sd,
            "C3-2 — 시드 %d에서 교사부터 새로 돌린 C3 파이프라인의 학생이 %s를 분포 안에서 배우는가? 분포 밖에서는? "
            "(유효성 기준 ≥0.95; 1단계 신호 기준은 7절)" % (sd, NAME_T[t]),
            "C3-2 학생 s%d" % sd)


def c33_labels(f):
    """C3-3 runs: (heading, question, commit label)"""
    t, k, sd = f["task"], f["kind"], f["seed"]
    tag = f["name"].split("__")[-1] if f["name"].count("__") > 4 else ""
    if k == "rope":
        return ("C3-3 교사 (시드 %d)" % sd,
                "C3-3 확인 실행 — 시드 %d 교사 `rope` 학습 (기준선 규약; 판정 체크포인트를 교사로 로컬 보관)" % sd,
                "C3-3 교사 s%d" % sd)
    if tag == "allstay":
        return ("C3-3 패리티 진단",
                "C3-3 변경 2 — 전부 정지 표의 학생이 패리티를 분포 안 ≥0.95로 배우는가? (아니면 학생 경로 결함으로 보고 고친다)",
                "C3-3 패리티 진단")
    if tag.startswith("dev"):
        return ("C3-3 개발 확인 (시드 %d)" % sd,
                "C3-3 개발 확인 — 내용 치환 의존도로 시드 %d 기존 교사에서 컴파일한 표의 학생이 %s를 배우는가? "
                "(개발용, 판정에 쓰지 않음)" % (sd, NAME_T[t]), "C3-3 개발 s%d" % sd)
    return ("C3-3 학생 (시드 %d, 판정용)" % sd,
            "C3-3 확인 실행 — 내용 치환 의존도 C3 학생이 시드 %d에서 %s 1단계 기준을 충족하는가? (7절)" % (sd, NAME_T[t]),
            "C3-3 학생 s%d" % sd)


def stage1_signal_line(f, total_flops):
    """7절 thresholds for one seed (C3-3 decision seeds 3-5)"""
    a = f["judgment"]["acc"]
    if f["task"] == "addition":
        ok = (a["ood_11-20"] >= 0.778, a["ood_21-30"] >= 0.500, total_flops <= 5.18e14)
        return ("- 7절 기준 (이 시드): 11–20 %.3f ≥0.778 %s · 21–30 %.3f ≥0.500 %s · 합계 FLOPs %.2e ≤5.18e14 %s"
                % (a["ood_11-20"], "예" if ok[0] else "아니오", a["ood_21-30"], "예" if ok[1] else "아니오",
                   total_flops, "예" if ok[2] else "아니오"))
    if f["task"] == "parity":
        oo = [v for l, v in a.items() if l.startswith("ood")]
        return "- 7절 기준 (이 시드): 패리티 세 구간 %s ≥0.99 %s" % (
            " · ".join("%.3f" % v for v in oo), "예" if all(v >= 0.99 for v in oo) else "아니오")
    return None


C4_TAG = {"compiled": "컴파일된 표", "allstay": "전부 정지 표"}


def c4_tag(f):
    return f["name"].split("__")[-1] if f["name"].count("__") > 4 else ""


def c4_answer(f):
    sp = HERE / "results" / "c4" / ("selection_%s_s%d.json" % (f["task"], f["seed"]))
    if not sp.exists():
        return "미정 (선택 전)"
    sel = json.loads(sp.read_text())
    return "%s (분포 안 %.3f; 선택용 검증 %.3f)" % (
        "선택됨" if sel["selected"] == c4_tag(f) else "선택 안 됨", idv(f),
        sel["students"][c4_tag(f)]["selection_accuracy"])


def c4_labels(f):
    t, k, sd, tag = f["task"], f["kind"], f["seed"], c4_tag(f)
    if k == "rope":
        return ("C4 교사 (시드 %d)" % sd,
                "C4 — 시드 %d 교사 `rope` 학습 (기준선 규약; 판정 체크포인트를 교사로 로컬 보관)" % sd, "C4 교사 s%d" % sd)
    return ("C4 학생 (시드 %d, %s)" % (sd, C4_TAG.get(tag, tag)),
            "C4 — 시드 %d의 %s 학생 (%s; 두 학생 중 선택 전용 분포 안 검증으로 하나를 고르고, 선택된 학생만 7절로 판정)"
            % (sd, C4_TAG.get(tag, tag), NAME_T[t]), "C4 학생 s%d %s" % (sd, tag))


def c4_student_lines(f):
    """C4 student: its table, the selection (design 15) and, if selected, the 7절 check with the total FLOPs"""
    t, sd, tag = f["task"], f["seed"], c4_tag(f)
    R4 = HERE / "results" / "c4"
    lines = []
    cr = json.loads((R4 / ("%s_compile_s%d" % (t, sd)) / "compile_result.json").read_text())
    if tag == "compiled":
        lines.append("- 컴파일된 표 (stay가 아닌 칸): %s; 사전 확인 비 %.2f%s" % (
            "; ".join("%s: %s" % (h, ", ".join("%s→%s" % (c, mv) for c, mv in row.items() if mv != "stay") or "모두 stay")
                      for h, row in cr["policy_named"].items()), cr["precheck"]["dependency"]["ratio"],
            " (기록만, 적용 안 함)" if cr["precheck"].get("gate_applied") is False else ""))
    else:
        lines.append("- 표: 전부 정지 (`stage1/results/c4/allstay_policy.json`)")
    sp = R4 / ("selection_%s_s%d.json" % (t, sd))
    if sp.exists():
        sel = json.loads(sp.read_text())
        st = sel["students"]
        lines.append("- 선택 (15절, 선택 전용 검증 %d개, 생성 시드 `%s`): %s; 규칙 — %s; 결과 — **%s** (%s)" % (
            sel["selection_set"]["size"], sel["selection_set"]["generation_seed"],
            " · ".join("%s %.3f (움직이는 헤드 %d)" % (C4_TAG[k], v["selection_accuracy"], v["moving_heads"])
                       for k, v in st.items()), sel["rule"], C4_TAG[sel["selected"]], sel["reason"]))
        if sel["selected"] == tag:
            tf = cr["teacher"]["train_flops_to_judgment"]
            ef = cr["extraction"]["flops"]
            sf = {k: json.loads((HERE.parent / v["run"] / "final.json").read_text())["judgment"]["train_flops_cum"]
                  for k, v in st.items()}
            total = tf + ef + sum(sf.values())
            lines.append("- 합계 FLOPs (15절): 교사 %.2e + 의존도 추출 %.2e + %s = **%.2e** (학생은 판정 시점까지)" % (
                tf, ef, " + ".join("학생 %s %.2e" % (C4_TAG[k], v) for k, v in sf.items()), total))
            sl = stage1_signal_line(f, total)
            if sl:
                lines.append(sl)
    return lines


def labels(phase, task, kind="pf"):
    """(heading label, question, commit label) for a run"""
    if phase == "c3" and kind == "rope":
        return ("C3-1 교사",
                "C3-1 1단계 — 교사 `rope` 학습 (기준선 rope와 같은 규약, 시드 0; 판정 체크포인트를 교사로 로컬 보관)",
                "C3-1 교사")
    if phase == "c3":
        q = ("C3-1 — rope에서 배운 의존 구조를 PF 이동 표로 컴파일한 학생 모델이 %s를 분포 안에서 배우는가? 분포 밖에서는? "
             "(유효성 기준 ≥0.95, 시드 0)" % NAME_T[task] if task != "mqar" else
             "C3-1 — 컴파일된 PF 학생의 MQAR 결과 (판정 기준 없음; 질의별·시퀀스 전체 보고)")
        return "C3-1 학생", q, "C3-1 학생"
    if phase == "c1_3" and kind == "pf_search":
        return ("C1-3 (PF-search v2)",
                "C1-3 — 점수를 손실로 고친 PF-search(설계서 12절)가 찾은 이동 정책 표와 경사하강 갱신 제어기가 %s를 "
                "학습 분포 안에서 배우는가? (유효성 기준 ≥0.95, 시드 0; 판정 FLOPs = 탐색 + 최종 학습)" % NAME_T[task],
                "C1-3 PF-search v2")
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
    head, question, _ = (c4_labels(f) if phase == "c4" else c33_labels(f) if phase == "c3_3" else
                         c32_labels(f) if phase == "c3" and c32_labels(f) else labels(phase, t, k))
    kname = "PF 학생 (C3)" if phase == "c3" and k == "pf_search" else NAME_K[k]
    if phase == "c3":
        kname += (" 대조군: 학습 전 교사" if "ctrl" in (f["name"].split("__")[-1]) else "") + " · 시드 %d" % f["seed"]
    if phase == "c3_3":
        kname = ("PF 학생 (C3-3)" if k == "pf_search" else NAME_K[k]) + " · 시드 %d" % f["seed"]
    if phase == "c4":
        kname = (("PF 학생 (C4, %s)" % C4_TAG.get(c4_tag(f), c4_tag(f))) if k == "pf_search" else NAME_K[k]) + \
            " · 시드 %d" % f["seed"]
    date = time.strftime("%Y-%m-%d", time.gmtime())
    lines = [
        "## %s · %s · %s / %s" % (date, head, NAME_T[t], kname),
        "- 질문: %s" % question,
        "- 질문에 대한 답: %s" % (("참고 — 교사 (판정 기준 없음; 분포 안 %.3f)" % idv(f))
                                  if phase in ("c3", "c3_3", "c4") and k == "rope"
                                  else c4_answer(f) if phase == "c4"
                                  else answer_c1(f) if phase in ("c1", "c1_2", "c1_3", "c3", "c3_3") else answer4(f) if phase == "phaseA4" else
                                  answer3(f) if phase == "phaseA3" else answer(t, k)),
        "- 코드 커밋: `%s`%s · 원자료: `%s/`" % (
            (env.get("code_commit") or "?")[:7], " (작업 트리 수정 있음)" if env.get("code_dirty") else "",
            d.relative_to(HERE.parent) if HERE.parent in d.parents else d),
        "- 결과 표 (판정 체크포인트 = 분포 안 최고 시점, 동률이면 이른 시점; 분포 밖은 그 시점 값):",
        "",
        "| 과제 | 기준선 | 규모 | 데이터 수 | 분포 안 정확도 | 분포 밖 정확도(구간별) | 학습 FLOPs | 시간 (학습 / 평가) |",
        "|---|---|---|---|---|---|---|---|",
        "| %s | %s | %s | %s | %.3f (step %d) | %s | %.2e (판정 시점까지) / %.2e (전체) | %.0f s / %.0f s |" % (
            NAME_T[t], kname, format(f["params"], ","), format(f["N"], ","), idv(f), j["step"], oods,
            j["train_flops_cum"], f["train_flops"], f["wall_train_s"], f["wall_eval_s"]),
        "",
        "- 마지막 시점 (step %d): 분포 안 %.3f · 분포 밖 %s" % (
            last["step"], [v for l, v in last["acc"].items() if l.startswith("id")][0], oods_last),
    ]
    if phase in ("c1", "c1_2", "c1_3", "c3", "c3_3", "c4") and t in BASE_REF:
        lines.append("- 같은 과제의 기준선 최고값 (동결, 설계서 7절): %s" % BASE_REF[t])
    if phase == "c4" and k == "rope":
        lines.append("- 교사 체크포인트: `teacher_best.pt` (판정 시점 가중치)와 `ckpt.pt`를 로컬에만 보관 (git 제외)")
    if phase == "c4" and k == "pf_search":
        lines.extend(c4_student_lines(f))
        if t in C1_BEST:
            lines.append("- 같은 과제의 C1 최고값: %s" % C1_BEST[t])
    if phase == "c3_3" and k == "rope":
        lines.append("- 교사 체크포인트: `teacher_best.pt` (판정 시점 가중치)와 `ckpt.pt`를 로컬에만 보관 (git 제외)")
    if phase == "c3_3" and k == "pf_search":
        if "precheck" in cfg["pf_search"]["search"]:
            cl = c3_lines(d, f, cfg)
            lines.extend(cl)
            cr = cfg["pf_search"]["search"]
            total = cr["teacher"]["train_flops_to_judgment"] + cr["extraction"]["flops"] + j["train_flops_cum"]
            if f["seed"] >= 3 and stage1_signal_line(f, total):
                lines.append(stage1_signal_line(f, total))
        else:
            lines.append("- 표: 전부 정지 (컴파일 없음, 교사 없음; `%s`)" % cfg["pf_search"]["policy_file"])
        if t in C1_BEST:
            lines.append("- 같은 과제의 C1 최고값: %s" % C1_BEST[t])
    if phase == "c3" and k == "rope":
        b = HERE / "results" / "phaseA4" / ("phaseA4_%s__rope__1M__s0__N100000" % t) / "final.json"
        if b.exists() and f["seed"] == 0:
            bf = json.loads(b.read_text())
            lines.append("- 같은 규약의 기준선 rope (Phase A‴, 같은 시드): 분포 안 %.3f (step %d) · 분포 밖 %s; 판정 시점까지 "
                         "학습 FLOPs %.2e" % (idv(bf), bf["judgment"]["step"], " · ".join(
                             "%.3f" % v for l, v in bf["judgment"]["acc"].items() if l.startswith("ood")),
                                               bf["judgment"]["train_flops_cum"]))
        lines.append("- 교사 체크포인트: `teacher_best.pt` (판정 시점 가중치)와 `ckpt.pt`를 로컬에만 보관 (git 제외)")
    if phase == "c3" and k == "pf_search":
        lines.extend(c3_lines(d, f, cfg))
        if t in C1_BEST:
            lines.append("- 같은 과제의 C1 최고값: %s" % C1_BEST[t])
    elif k == "pf_search" and cfg.get("pf_search") and phase not in ("c3_3", "c4"):
        sr = cfg["pf_search"]["search"]
        sc = ("탐색 점수(분포 안 검증 답 토큰 교차 엔트로피) %.4f" % sr["best_score_in_distribution_validation_loss"]
              if "best_score_in_distribution_validation_loss" in sr else
              "탐색 점수(분포 안 검증) %.3f" % sr["best_score_in_distribution_validation"])
        lines.append("- PF-search 탐색: 평가 %d회, 탐색 FLOPs %.2e, 정지 사유 — %s, %s; 찾은 표: %s"
                     % (sr["evaluations"], sr["search_flops"], sr["stopped"], sc,
                        "; ".join("%s: %s" % (h, ", ".join("%s→%s" % (c, mv) for c, mv in row.items() if mv != "stay")
                                                  or "모두 stay") for h, row in sr["policy_named"].items())))
        lines.append("- 판정 FLOPs (탐색 + 최종 학습 판정 시점까지): %.2e + %.2e = %.2e" % (
            sr["search_flops"], j["train_flops_cum"], sr["search_flops"] + j["train_flops_cum"]))
    if phase in ("c1_2", "c1_3") and t in C11_REF:
        lines.append("- 같은 과제의 C1-1 값: %s" % C11_REF[t])
    if phase == "c1_3" and c12_ref(t):
        lines.append("- 같은 과제의 C1-2 값: %s" % c12_ref(t))
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
              (c4_labels(f) if cfg.get("phase") == "c4" else c33_labels(f) if cfg.get("phase") == "c3_3" else
               c32_labels(f) if cfg.get("phase") == "c3" and c32_labels(f) else
               labels(cfg.get("phase", "phaseA2"), f["task"], f["kind"]))[2], f["task"], f["kind"], idv(f), j["step"])
    files = [str(res.relative_to(root)), str(d.relative_to(root))]
    if (d.parent / "QUEUE_LOG.txt").exists():
        files.append(str((d.parent / "QUEUE_LOG.txt").relative_to(root)))
    subprocess.check_call(["git", "add"] + files, cwd=root)
    subprocess.check_call(["git", "commit", "-q", "-m", msg], cwd=root)
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
    for i in range(4):
        if subprocess.call(["git", "push", "-u", "origin", branch], cwd=root) == 0:
            break
        time.sleep(2 ** (i + 1))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run_dir")
    p.add_argument("--no-git", action="store_true")
    main(p.parse_args())
