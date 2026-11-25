"""E-0 curves: accuracy against cumulative training FLOPs, one panel per run (bins 1–10, 11–20, 21–30), plus the
abacus_looped 1M vs stage-1 looped_rr panel (11–20, same FLOPs, up to 5.18e14).  Reads the logs only.

  python stage2/e0_plot.py      # writes stage2/results/e0/curves.png
"""
from __future__ import annotations
import json
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "e0"
ROOT = HERE.parent
LOOPED_RR = ROOT / "stage1/results/phaseA2/phaseA2_addition__looped_rr__1M__s0__N100000/log.jsonl"
C3 = 1.79e14
RUNS = [("abacus_ii_1M", "abacus + input injection · 1M"), ("abacus_looped_1M", "abacus_looped · 1M"),
        ("abacus_looped_10M", "abacus_looped · 10M"), ("position_coupling_1M", "position coupling · 1M"),
        ("position_coupling_pad_1M", "position coupling, zero-padded · 1M")]
BINS = [("id_1-10", "1–10 (in distribution)"), ("ood_11-20", "11–20"), ("ood_21-30", "21–30")]
# reference categorical palette, first three slots (validated all-pairs, light surface)
COL = {"id_1-10": "#2a78d6", "ood_11-20": "#eb6834", "ood_21-30": "#1baf7a"}
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"


def rows(p):
    return [r for r in (json.loads(l) for l in open(p)) if "step" in r]


def style(ax, xmax):
    ax.set_facecolor(SURFACE)
    ax.set_xscale("log")
    ax.set_xlim(1e13, xmax)
    ax.set_ylim(-0.02, 1.02)
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.axhline(0.95, color=MUTED, linewidth=0.8, zorder=1)
    for m in (1, 10, 30):
        if C3 * m <= xmax * 1.01:
            ax.axvline(C3 * m, color=MUTED, linewidth=0.8, zorder=1)


def main():
    data = {r: rows(OUT / ("e0_" + r) / "log.jsonl") for r, _ in RUNS if (OUT / ("e0_" + r) / "log.jsonl").exists()}
    xmax = max([1.9e15] + [rs[-1]["train_flops_cum"] * 1.1 for rs in data.values() if rs])
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.4), sharey=True, facecolor=SURFACE)
    for ax, (run, title) in zip(axes.flat, RUNS):
        style(ax, xmax)
        ax.set_title(title, color=INK, fontsize=10, loc="left")
        rs = data.get(run, [])
        if not rs:
            continue
        x = [r["train_flops_cum"] for r in rs]
        for b, _ in BINS:
            ax.plot(x, [r["acc"][b] for r in rs], color=COL[b], linewidth=1.6, solid_capstyle="round")
        if "acc_scaled" in rs[-1]:
            for b, _ in BINS[1:]:
                ax.plot(x, [r["acc_scaled"][b] for r in rs], color=COL[b], linewidth=1.2, linestyle=(0, (3, 2)))
    # 5.1 item 6: abacus_looped 1M (acc_scaled, the stage-1 looped rule) vs stage-1 looped_rr, 11–20
    ax = axes.flat[5]
    lr = rows(LOOPED_RR)
    lim = lr[-1]["train_flops_cum"]
    style(ax, lim * 1.15)
    ax.set_title("11–20 up to 5.18e14: abacus_looped 1M vs stage-1 looped_rr", color=INK, fontsize=10, loc="left")
    al = [r for r in data.get("abacus_looped_1M", []) if r["train_flops_cum"] <= lim * 1.0001]
    ax.plot([r["train_flops_cum"] for r in lr], [r["acc"]["ood_11-20"] for r in lr], color=INK2, linewidth=1.6,
            label="looped_rr 1M (stage 1, N = 1e5)")
    if al:
        ax.plot([r["train_flops_cum"] for r in al], [r["acc_scaled"]["ood_11-20"] for r in al],
                color=COL["ood_11-20"], linewidth=1.6, linestyle=(0, (3, 2)), label="abacus_looped 1M (stage-1 rule)")
    ax.legend(loc="upper left", frameon=False, fontsize=8, labelcolor=INK)
    for ax in axes[1]:
        ax.set_xlabel("cumulative training FLOPs", color=INK2, fontsize=8)
    for ax in axes[:, 0]:
        ax.set_ylabel("sequence accuracy", color=INK2, fontsize=8)
    handles = [plt.Line2D([], [], color=COL[b], linewidth=1.6, label=lab) for b, lab in BINS]
    handles.append(plt.Line2D([], [], color=INK2, linewidth=1.2, linestyle=(0, (3, 2)),
                              label="dashed: abacus_looped, stage-1 recurrence rule (acc_scaled)"))
    handles.append(plt.Line2D([], [], color=MUTED, linewidth=0.8,
                              label="gray: 0.95 target · C3 total FLOPs 1.79e14 · 10× · 30×"))
    fig.suptitle("E-0 · addition · sequence accuracy vs cumulative training FLOPs (seed 0, fresh data every batch, "
                 "evaluated every 1,000 steps)", x=0.01, y=0.985, ha="left", color=INK, fontsize=11)
    fig.legend(handles=handles, loc="upper left", ncol=5, frameon=False, fontsize=8, labelcolor=INK,
               bbox_to_anchor=(0.005, 0.955))
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(OUT / "curves.png", dpi=150, facecolor=SURFACE)
    print(OUT / "curves.png")


if __name__ == "__main__":
    main()
