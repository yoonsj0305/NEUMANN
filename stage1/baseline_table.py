"""Stage 1 baseline table (CLAUDE.md "1단계 비교 기준선"): for every Stage 1 task and evaluation bin, the value of each
of the four baselines (abacus, rope, looped_rr, gru) at its judgment checkpoint and the highest of them (the
reference a Stage 1 candidate is compared with).

Values come from the run records only:
* runs that carry a judgment (Phase A', A''') -> final.json "judgment" (highest in-distribution evaluation,
  earliest if tied; out-of-distribution at that evaluation);
* Phase A runs (written before the judgment rule of 2026-11-17) -> the same rule applied to their log.jsonl rows.
Primary accuracy: sequence exact match (addition, parity); per-query accuracy (MQAR); looped_rr: the pre-declared
recurrence (4 x length ratio).

  python stage1/baseline_table.py            -> prints the RESULTS.md section (markdown)
"""
from __future__ import annotations
import json
import pathlib

R = pathlib.Path(__file__).resolve().parent / "results"
KINDS = ("abacus", "rope", "looped_rr", "gru")
SRC = {
    ("addition", "abacus"): "phaseA/addition__abacus__1M__s0__N100000",
    ("addition", "rope"): "phaseA4/phaseA4_addition__rope__1M__s0__N100000",
    ("addition", "looped_rr"): "phaseA2/phaseA2_addition__looped_rr__1M__s0__N100000",
    ("addition", "gru"): "phaseA/addition__gru__1M__s0__N100000",
    ("parity", "abacus"): "phaseA/parity__abacus__1M__s0__N100000",
    ("parity", "rope"): "phaseA4/phaseA4_parity__rope__1M__s0__N100000",
    ("parity", "looped_rr"): "phaseA2/phaseA2_parity__looped_rr__1M__s0__N100000",
    ("parity", "gru"): "phaseA/parity__gru__1M__s0__N100000",
    ("mqar", "abacus"): "phaseA4/phaseA4_mqar__abacus__1M__s0__N100000",
    ("mqar", "rope"): "phaseA4/phaseA4_mqar__rope__1M__s0__N100000",
    ("mqar", "looped_rr"): "phaseA4/phaseA4_mqar__looped_rr__1M__s0__N100000",
    ("mqar", "gru"): "phaseA4/phaseA4_mqar__gru__1M__s0__N100000",
}
NAME_T = {"addition": "덧셈", "parity": "패리티", "mqar": "MQAR (질의별)"}


def judged(d):
    f = json.loads((d / "final.json").read_text())
    if "judgment" in f:
        return f["judgment"]["step"], f["judgment"]["acc"], "final.json judgment"
    rows = [json.loads(l) for l in open(d / "log.jsonl") if l.strip()]
    rows = [r for r in rows if "step" in r]
    idl = [l for l in rows[-1]["acc"] if l.startswith("id")][0]
    best = max(rows, key=lambda r: (r["acc"][idl], -r["step"]))
    return best["step"], best["acc"], "log.jsonl (rule applied)"


def main():
    out = ["## 1단계 기준선 표 (Phase A‴ 종료 시점)",
           "- 값은 각 실행의 판정 체크포인트 값이다(분포 안 최고 시점, 동률이면 이른 시점). 분포 밖은 그 시점 값이다.",
           "- 주 정확도: 덧셈·패리티는 시퀀스 정답, MQAR은 질의별 정확도다. looped_rr은 사전 선언한 반복 횟수(4 × 길이 비율)를 쓴다.",
           "- **최고(기준값)** 열은 네 기준선 중 가장 높은 값이다. 분포 밖 행의 이 값이 1단계 후보와 비교할 기준값이다.",
           ""]
    srcs = []
    for task in ("addition", "parity", "mqar"):
        vals, labels = {}, None
        for k in KINDS:
            d = R / SRC[(task, k)]
            if not (d / "final.json").exists():
                vals[k] = None
                continue
            step, acc, how = judged(d)
            vals[k] = (step, acc)
            labels = labels or list(acc)
            srcs.append("`%s` (%s, step %d)" % (SRC[(task, k)], how, step))
        out.append("### %s" % NAME_T[task])
        out.append("")
        out.append("| 구간 | abacus | rope | looped_rr | gru | 최고 (기준값) |")
        out.append("|---|---|---|---|---|---|")
        for l in labels or []:
            cells, best = [], (-1, None)
            for k in KINDS:
                if vals[k] is None:
                    cells.append("미실행")
                    continue
                v = vals[k][1][l]
                cells.append("%.3f" % v)
                if v > best[0]:
                    best = (v, k)
            tied = [k for k in KINDS if vals[k] is not None and abs(vals[k][1][l] - best[0]) < 1e-12]
            name = ("분포 안 " if l.startswith("id") else "분포 밖 ") + l.split("_", 1)[1]
            out.append("| %s | %s | **%.3f** (%s) |" % (name, " | ".join(cells), best[0], ", ".join(tied)))
        out.append("")
    out.append("- 출처 (실행 디렉터리, `stage1/results/` 기준):")
    for s in srcs:
        out.append("  - " + s)
    print("\n".join(out))


if __name__ == "__main__":
    main()
