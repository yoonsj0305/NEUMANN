"""E-0 report: accuracy-versus-training-FLOPs curves per run and bin, reach points, and the abacus_looped 1M versus
stage-1 looped_rr comparison at the same FLOPs (5.1 item 3).  Reads stage2/results/e0/*/log.jsonl only.

  python stage2/e0_report.py            # prints markdown tables, writes stage2/results/e0/summary.json
"""
from __future__ import annotations
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "results" / "e0"
C3 = 1.79e14
BINS = ["id_1-10", "ood_11-20", "ood_21-30", "ood_31-40"]
RUNS = ["abacus_ii_1M", "abacus_looped_1M", "abacus_looped_10M", "position_coupling_1M"]
POINTS = [2.5e13, 5e13, 1e14, 1.79e14, 2.5e14, 5.18e14, 1e15, 1.79e15, 3e15, 5.37e15]
LOOPED_RR = ROOT / "stage1/results/phaseA2/phaseA2_addition__looped_rr__1M__s0__N100000/log.jsonl"


def rows(path):
    return [r for r in (json.loads(l) for l in open(path)) if "step" in r]


def at(rs, f):
    """the last evaluation at or before training FLOPs f"""
    c = [r for r in rs if r["train_flops_cum"] <= f * 1.0001]
    return c[-1] if c else None


def fmt(x):
    return "—" if x is None else "%.3f" % x


def main():
    summary = {"runs": {}}
    for run in RUNS:
        p = OUT / ("e0_" + run) / "log.jsonl"
        if not p.exists():
            continue
        rs = rows(p)
        if not rs:
            continue
        reach = next((r for r in rs if r["acc"]["ood_11-20"] >= 0.95 and r["acc"]["ood_21-30"] >= 0.95), None)
        reach_s = next((r for r in rs if "acc_scaled" in r and r["acc_scaled"]["ood_11-20"] >= 0.95
                        and r["acc_scaled"]["ood_21-30"] >= 0.95), None)
        first = {b: next((r["train_flops_cum"] for r in rs if r["acc"][b] >= 0.95), None) for b in BINS}
        best = {b: max(r["acc"][b] for r in rs) for b in BINS}
        summary["runs"][run] = {
            "evaluations": len(rs), "last_step": rs[-1]["step"], "last_flops": rs[-1]["train_flops_cum"],
            "last_acc": rs[-1]["acc"],
            "reached": None if reach is None else {"step": reach["step"], "train_flops_cum": reach["train_flops_cum"],
                                                   "multiple_of_C3": reach["train_flops_cum"] / C3, "acc": reach["acc"]},
            "reached_secondary_scaled_recurrence": None if reach_s is None else {
                "step": reach_s["step"], "train_flops_cum": reach_s["train_flops_cum"],
                "multiple_of_C3": reach_s["train_flops_cum"] / C3, "acc_scaled": reach_s["acc_scaled"]},
            "first_flops_bin_ge_0.95": first, "best_acc": best,
            "at_points": {"%.3g" % f: (None if at(rs, f) is None else
                                       {"step": at(rs, f)["step"], "train_flops_cum": at(rs, f)["train_flops_cum"],
                                        "acc": at(rs, f)["acc"], "acc_scaled": at(rs, f).get("acc_scaled")})
                          for f in POINTS}}
        print("\n### %s  (evaluations %d, last step %d, %.3e FLOPs)" % (run, len(rs), rs[-1]["step"], rs[-1]["train_flops_cum"]))
        print("| FLOPs ≤ | × C3 | step | " + " | ".join(BINS) + (" | 11–20 / 21–30 / 31–40 (scaled recurrence)" if "looped" in run else "") + " |")
        print("|---|---|---|" + "---|" * len(BINS) + ("---|" if "looped" in run else ""))
        for f in POINTS:
            r = at(rs, f)
            if r is None or (f > rs[-1]["train_flops_cum"] * 1.5 and f != POINTS[0]):
                continue
            line = "| %.3g | %.2f | %d | " % (f, f / C3, r["step"]) + " | ".join(fmt(r["acc"][b]) for b in BINS)
            if "looped" in run:
                s = r.get("acc_scaled", {})
                line += " | " + " / ".join(fmt(s.get(b)) for b in BINS[1:])
            print(line + " |")
        print("reach (primary): %s" % ("not reached" if reach is None else "step %d, %.3e FLOPs = %.2f x C3"
                                         % (reach["step"], reach["train_flops_cum"], reach["train_flops_cum"] / C3)))
        if "looped" in run:
            print("reach (secondary, scaled recurrence): %s" % ("not reached" if reach_s is None else
                  "step %d, %.3e FLOPs = %.2f x C3" % (reach_s["step"], reach_s["train_flops_cum"], reach_s["train_flops_cum"] / C3)))
    # 5.1 item 3: abacus_looped 1M against the stage-1 looped_rr log at the same FLOPs (up to 5.18e14)
    p = OUT / "e0_abacus_looped_1M" / "log.jsonl"
    if p.exists() and rows(p):
        al, lr = rows(p), rows(LOOPED_RR)
        cmp_ = []
        print("\n### abacus_looped 1M vs stage-1 looped_rr 1M (N = 1e5), same training FLOPs")
        print("| looped_rr step | FLOPs | abacus_looped step | looped_rr (stage-1 rule) id / 11–20 / 21–30 | "
              "looped_rr fixed 4: 11–20 / 21–30 | abacus_looped primary id / 11–20 / 21–30 | abacus_looped scaled 11–20 / 21–30 |")
        print("|---|---|---|---|---|---|---|")
        for r in lr:
            a = at(al, r["train_flops_cum"])
            if a is None or al[-1]["train_flops_cum"] < r["train_flops_cum"] * 0.999 - 2e13:
                continue
            c = {"flops": r["train_flops_cum"], "looped_rr_step": r["step"], "looped_rr_acc": r["acc"],
                 "looped_rr_acc_fixed4": r.get("acc_fixed4"), "abacus_looped_step": a["step"],
                 "abacus_looped_flops": a["train_flops_cum"], "abacus_looped_acc": a["acc"],
                 "abacus_looped_acc_scaled": a.get("acc_scaled")}
            cmp_.append(c)
            s = a.get("acc_scaled", {})
            print("| %d | %.3e | %d | %s / %s / %s | %s / %s | %s / %s / %s | %s / %s |" % (
                r["step"], r["train_flops_cum"], a["step"], fmt(r["acc"]["id_1-10"]), fmt(r["acc"]["ood_11-20"]),
                fmt(r["acc"]["ood_21-30"]), fmt(r["acc_fixed4"]["ood_11-20"]), fmt(r["acc_fixed4"]["ood_21-30"]),
                fmt(a["acc"]["id_1-10"]), fmt(a["acc"]["ood_11-20"]), fmt(a["acc"]["ood_21-30"]),
                fmt(s.get("ood_11-20")), fmt(s.get("ood_21-30"))))
        lower = [c for c in cmp_ if any(c["abacus_looped_acc"][b] < c["looped_rr_acc"][b] for b in BINS)]
        summary["looped_rr_comparison"] = {
            "rule": "for every stage-1 looped_rr evaluation (FLOPs f <= 5.18e14), the last abacus_looped 1M evaluation "
                    "at or before f; 'lower' = any bin of abacus_looped (primary) below looped_rr (stage-1 rule)",
            "points": cmp_, "points_where_abacus_looped_lower": [
                {"flops": c["flops"], "bins": [b for b in BINS if c["abacus_looped_acc"][b] < c["looped_rr_acc"][b]]}
                for c in lower]}
        print("points where abacus_looped 1M is lower in some bin: %d of %d" % (len(lower), len(cmp_)))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
