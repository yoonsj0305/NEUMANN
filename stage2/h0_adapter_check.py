"""H-0 step 0: check of the BOS adapter (stage2/h_adapter.py) before the main run -- no training.

Through the adapter (124-token PF built by stage1 models.build, the adapted token kinds and separators):
  - data: the adapter's train (seeds 15, 16, 17, first 2,000), eval (1,000 / 500) and selection sets of the six H-0
    tasks equal stage2/h_tasks.py's (the sets of the H-0a check); stage-1 addition / parity data unchanged;
  - token kinds: the adapted pf.token_classes equals stage2/g0a.classes on those sets (BOS = "other");
  - hand tables: the H-0a BOS hand tables + controllers (stage2/h0a.py) are exact (1.000) on every bin with the
    adapter's own token kinds and separators;
  - compile head simulation (c3_compile.simulate) of each hand table reads the same positions as the PF move code
    (stage2/g0a.head_path);
  - pre-check correct tables (c3_compile.correct_table) are the H-0a tables.

  python stage2/h0_adapter_check.py        # writes stage2/results/h0/adapter_check.json
"""
from __future__ import annotations
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "stage1"))
import torch                     # noqa: E402
import tasks as T                # noqa: E402

OUT = HERE / "results" / "h0"


def main():
    torch.set_num_threads(1)
    t0 = time.time()
    before = {t: {"train": T.train_set(t, 2000, 6), "eval": T.eval_sets(t, 1000, 500)} for t in ("addition", "parity")}
    import h_adapter as A
    A.install()
    import h_tasks as HT
    import g0a
    import h0a
    import models as M
    import run as R
    import pf as PFM
    import c3_compile as CC
    import c4_select as CS
    res = {"vocab_size": len(T.VOCAB), "added_tokens": T.VOCAB[120:], "bos_id": T.TOK["<bos>"]}
    res["stage1_data_identical"] = {t: before[t] == {"train": T.train_set(t, 2000, 6), "eval": T.eval_sets(t, 1000, 500)}
                                    for t in before}
    cfg = dict(M.SCALES["pf_search"]["1M"], policy=[[0] * 7] * 3)
    torch.manual_seed(0)
    pf = M.build("pf_search", len(T.VOCAB), [T.TOK[d] for d in T.DIGITS], cfg)
    pf.eval()
    ci = CC.class_ids()

    def kinds(x):
        return PFM.token_classes(x, ci["digits"], ci["plus"], ci["eq"], ci["bar"], ci["node_lo"], ci["node_hi"])

    class AdaptedHand(torch.nn.Module):          # H-0a controller, token kinds from the adapted pf.token_classes
        def __init__(self, task):
            super().__init__()
            self.task = task

        def forward(self, tokens, offset=None, recur=None):
            ctl = h0a.Controller(self.task, h0a.TABLES[self.task], kinds(tokens), pf.V, pf.K)
            return PFM.PF.forward(pf, tokens, controller=ctl)

    acc, same, sim, kind_same, corr = {}, {}, {}, {}, {}
    for task in HT.SUITE:
        ev = T.eval_sets(task, 1000, 500)
        with torch.no_grad():
            acc[task] = {l: R.exact_match(AdaptedHand(task), e, "pf_search", cfg)[0] for l, e in ev.items()}
        trains = {s: T.train_set(task, 2000, s) for s in (15, 16, 17)}
        sel = CS.selection_set(task)
        same[task] = {"eval": ev == HT.eval_sets(task, 1000, 500),
                      "train_s15_s16_s17_first2000": all(trains[s] == HT.train_set(task, 2000, s) for s in trains),
                      "select": sel == HT.selection_set(task),
                      "bos_first_only": all(e[0][0] == HT.BOS_ID and HT.BOS_ID not in e[0][1:]
                                            for v in list(ev.values()) + list(trains.values()) + [sel] for e in v)}
        ok = True
        for e in sel[:300]:
            x = torch.tensor([e[0] + e[1]])
            ok &= bool((kinds(x) == g0a.classes(x)).all())
        kind_same[task] = ok
        exs = trains[15][:200]
        rows = []
        for i, e in enumerate(exs):
            x, y = R.make_batch([e])
            rows += [(i, t, None, None) for t in range(x.shape[1]) if int(y[0, t]) != -100]
        P, _ = CC.simulate(exs, rows, [list(c) for c in h0a.TABLES[task]])
        ok = True
        for r, (i, t, _, _) in enumerate(rows):
            p, a = exs[i]
            if [int(v) for v in P[:, r]] != g0a.head_path(p + a, h0a.TABLES[task])[t]:
                ok = False
                break
        sim[task] = {"output_steps": len(rows), "same_read_positions": ok}
        corr[task] = CC.correct_table(task) == h0a.TABLES[task]
    res.update({"hand_table_accuracy": acc, "data_identical_to_h_tasks": same, "token_kinds_equal_g0a": kind_same,
                "compile_simulation_vs_pf_head_path": sim, "precheck_correct_table_is_h0a": corr})
    res["all_exact"] = all(v == 1.0 for d in acc.values() for v in d.values())
    res["all_identical"] = (all(res["stage1_data_identical"].values()) and all(all(d.values()) for d in same.values())
                            and all(kind_same.values()) and all(d["same_read_positions"] for d in sim.values())
                            and all(corr.values()))
    res["wall_s"] = round(time.time() - t0, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter_check.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("all_exact", "all_identical", "wall_s")}))
    for k, v in acc.items():
        print(k, {l: round(x, 3) for l, x in v.items()})


if __name__ == "__main__":
    main()
