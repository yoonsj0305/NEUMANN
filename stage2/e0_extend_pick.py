"""E-0 30 x extension target (DESIGN 5.1, tie-break 5.3).  Reads the general-method logs only.

5.1: if no general method reached by 10 x (1.79e15), extend the one with the highest 21–30 at 10 x to 5.37e15.
5.3 (pre-registered tie-break), compared in order:
  1. 21–30 at 10 x (the last evaluation at or before 1.79e15)
  2. best 21–30 during the run (the higher of the two test rules)
  3. best 11–20 during the run
For criterion 1 a looped run's value is also the higher of the two test rules (5.2 counts either rule); both rules
are written out so the choice can be checked.  The extension continues from the run's last checkpoint.

  python stage2/e0_extend_pick.py      # writes stage2/results/e0/extension_pick.json
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "e0"
GENERAL = ["abacus_ii_1M", "abacus_looped_1M", "abacus_looped_10M"]
TEN_X, THIRTY_X = 1.79e15, 5.37e15


def rows(p):
    return [r for r in (json.loads(l) for l in open(p)) if "step" in r]


def both(r, b):
    """(primary, acc_scaled or None)"""
    return r["acc"][b], (r.get("acc_scaled") or {}).get(b)


def hi(r, b):
    return max(v for v in both(r, b) if v is not None)


def main():
    cand = {}
    for run in GENERAL:
        d = OUT / ("e0_" + run)
        if not (d / "final.json").exists():
            sys.exit("%s has not finished its 10 x budget" % run)
        fin = json.loads((d / "final.json").read_text())
        if fin.get("reached"):
            print("%s reached within 10 x: no extension (5.1)" % run)
            (OUT / "extension_pick.json").write_text(json.dumps({"extend": None, "reason": "%s reached" % run}, indent=1))
            return
        rs = rows(d / "log.jsonl")
        at10 = [r for r in rs if r["train_flops_cum"] <= TEN_X * 1.0001][-1]
        b2130 = max(rs, key=lambda r: hi(r, "ood_21-30"))
        b1120 = max(rs, key=lambda r: hi(r, "ood_11-20"))
        cand[run] = {
            "c1_at_10x_21_30": hi(at10, "ood_21-30"),
            "c1_detail": {"step": at10["step"], "train_flops_cum": at10["train_flops_cum"],
                          "primary": both(at10, "ood_21-30")[0], "acc_scaled": both(at10, "ood_21-30")[1]},
            "c2_best_21_30": hi(b2130, "ood_21-30"),
            "c2_detail": {"step": b2130["step"], "train_flops_cum": b2130["train_flops_cum"],
                          "primary_best": max(r["acc"]["ood_21-30"] for r in rs),
                          "acc_scaled_best": max(((r.get("acc_scaled") or {}).get("ood_21-30", -1) for r in rs))},
            "c3_best_11_20": hi(b1120, "ood_11-20"),
            "c3_detail": {"step": b1120["step"], "train_flops_cum": b1120["train_flops_cum"],
                          "primary_best": max(r["acc"]["ood_11-20"] for r in rs),
                          "acc_scaled_best": max(((r.get("acc_scaled") or {}).get("ood_11-20", -1) for r in rs))},
            "last_checkpoint_step": fin["steps"], "last_checkpoint_flops": fin["train_flops"]}
    keys = ["c1_at_10x_21_30", "c2_best_21_30", "c3_best_11_20"]
    pool, decided_by = list(cand), None
    for k in keys:
        top = max(cand[r][k] for r in pool)
        pool = [r for r in pool if cand[r][k] == top]
        if len(pool) == 1:
            decided_by = k
            break
    pick = {"rule": "DESIGN 5.1 + 5.3 tie-break (1. 21-30 at 10x, 2. best 21-30 either test rule, 3. best 11-20)",
            "candidates": cand, "extend": pool[0] if len(pool) == 1 else None, "decided_by": decided_by,
            "tied_after_all_criteria": pool if len(pool) > 1 else None, "budget": THIRTY_X}
    (OUT / "extension_pick.json").write_text(json.dumps(pick, indent=1))
    for r in GENERAL:
        c = cand[r]
        print("%-18s  1) 21-30 at 10x %.3f (primary %.3f, scaled %s)  2) best 21-30 %.3f  3) best 11-20 %.3f" % (
            r, c["c1_at_10x_21_30"], c["c1_detail"]["primary"], c["c1_detail"]["acc_scaled"], c["c2_best_21_30"],
            c["c3_best_11_20"]))
    print("extend: %s (decided by %s)" % (pick["extend"], decided_by) if pick["extend"] else
          "still tied after all 5.3 criteria: %s" % pool)


if __name__ == "__main__":
    main()
