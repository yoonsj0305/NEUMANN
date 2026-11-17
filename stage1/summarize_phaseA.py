"""Stage 1 / Phase A: the result table and the pass criteria of CLAUDE.md, from the run records only.

Criteria (CLAUDE.md, Phase A):
  addition: both transformer baselines (abacus, looped) in-distribution >= 95 %
  parity:   GRU in-distribution >= 95 %  (a GRU failure is treated as a pipeline bug)
  a transformer failing parity in-distribution is recorded as a result, not a bug
"In-distribution accuracy" is the value at the run's last evaluation (the model the run ends with); the best value
over the run is reported next to it.

  python stage1/summarize_phaseA.py   -> stage1/results/phaseA/SUMMARY.md, summary.json
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).parent / "results" / "phaseA"
TASKS = ("addition", "parity", "reachability")
KINDS = ("abacus", "looped", "gru")


def load(task, kind):
    d = ROOT / ("%s__%s__1M__s0__N100000" % (task, kind))
    if not (d / "final.json").exists():
        return None
    f = json.loads((d / "final.json").read_text())
    rows = [json.loads(l) for l in open(d / "log.jsonl") if l.strip()]
    f["evals"] = [r for r in rows if "step" in r]
    f["events"] = [r for r in rows if "event" in r]
    return f


def main():
    out, lines = {}, []
    lines.append("| task | baseline | params | N | steps (stop) | in-dist (last / best) | out-of-dist bins (last) "
                 "| looped fixed-4 bins | train FLOPs | train / eval wall-clock |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for t in TASKS:
        for k in KINDS:
            f = load(t, k)
            if f is None:
                lines.append("| %s | %s | — | — | not finished | | | | | |" % (t, k))
                continue
            idl = [l for l in f["final_acc"] if l.startswith("id")][0]
            best = max(e["acc"][idl] for e in f["evals"])
            ood = {l: v for l, v in f["final_acc"].items() if l.startswith("ood")}
            stop = "early" if f["stopped"].startswith("early") else "max"
            out["%s/%s" % (t, k)] = {"params": f["params"], "steps": f["steps"], "stopped": f["stopped"],
                                     "id_last": f["final_acc"][idl], "id_best": best, "ood_last": ood,
                                     "ood_fixed4_last": f.get("final_acc_fixed4"), "train_flops": f["train_flops"],
                                     "wall_train_s": f["wall_train_s"], "wall_eval_s": f["wall_eval_s"],
                                     "segments": len(f["segments"]),
                                     "curve": [[e["step"], e["train_flops_cum"], e["acc"][idl]] for e in f["evals"]]}
            fx = f.get("final_acc_fixed4")
            lines.append("| %s | %s | %d | %d | %d (%s) | %.3f / %.3f | %s | %s | %.2e | %.0f s / %.0f s |" % (
                t, k, f["params"], f["N"], f["steps"], stop, f["final_acc"][idl], best,
                " · ".join("%s %.3f" % (l[4:], v) for l, v in ood.items()),
                " · ".join("%s %.3f" % (l[4:], v) for l, v in fx.items()) if fx else "—",
                f["train_flops"], f["wall_train_s"], f["wall_eval_s"]))
    crit = []

    def get(t, k):
        return out.get("%s/%s" % (t, k), {}).get("id_last")
    a1, a2, g = get("addition", "abacus"), get("addition", "looped"), get("parity", "gru")
    crit.append({"criterion": "addition: abacus in-distribution >= 0.95", "value": a1,
                 "met": a1 is not None and a1 >= 0.95})
    crit.append({"criterion": "addition: looped in-distribution >= 0.95", "value": a2,
                 "met": a2 is not None and a2 >= 0.95})
    crit.append({"criterion": "parity: GRU in-distribution >= 0.95", "value": g, "met": g is not None and g >= 0.95})
    for k in ("abacus", "looped"):
        v = get("parity", k)
        crit.append({"criterion": "parity: %s in-distribution (recorded as a result, no threshold)" % k, "value": v,
                     "met": None})
    allmet = all(c["met"] for c in crit if c["met"] is not None)
    lines.append("")
    lines.append("Phase A criteria (CLAUDE.md), in-distribution accuracy at the last evaluation:")
    for c in crit:
        lines.append("* %s: %s%s" % (c["criterion"], "—" if c["value"] is None else "%.3f" % c["value"],
                                     "" if c["met"] is None else (" → met" if c["met"] else " → not met")))
    lines.append("* all thresholds met: %s" % ("yes" if allmet else "no"))
    lines.append("")
    lines.append("Interrupted by the session's 2-hour background limit and resumed from the last checkpoint (steps after "
                 "it were recomputed; recorded FLOPs and wall-clock count each step once; see QUEUE_LOG.txt):")
    for k, v in out.items():
        if v["segments"] > 1:
            lines.append("* %s: %d segments" % (k, v["segments"]))
    lines.append("")
    lines.append("Wall-clock: one CPU thread per run, up to 4 runs at once on a 4-core CPU (no GPU); times are not "
                 "corrected for contention.")
    (ROOT / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    (ROOT / "summary.json").write_text(json.dumps({"runs": out, "criteria": crit, "all_thresholds_met": allmet},
                                                  indent=1))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
