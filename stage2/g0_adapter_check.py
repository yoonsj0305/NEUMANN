"""G-0 step 2 (stage2/DESIGN.md 7.10, item 3): regression check of the token-only adapter (stage2/g_adapter.py).

  hand      Through the adapter (123-token PF built by stage1 models.build, the adapted token kinds and separators):
            - stage-1 hand-table checks reproduce 1.000 on every bin: addition with the C1-3 hand table and its hand
              update controller (stage1/pf_search_v2_check.TableRuleModel), addition and parity with the C1-1 hand
              rule controllers (stage1/pf_rules.RuleModel; parity's moves are all "stay");
            - the G-0 suite's G-0a hand tables + controllers are exact on every bin with the adapter's own token kinds
              (pf.token_classes) and separators (pf.candidates);
            - data: stage-1 train/eval sets of addition and parity are identical before and after install(); the
              adapter's train / eval / selection sets of the G-0 tasks are identical to stage2/g_tasks.py's;
            - compile head simulation (c3_compile.simulate) of each G-0 hand table reads the same positions as the PF
              move code in stage2/g0a.head_path.
  compile   One stage-1 addition teacher checkpoint (rope, vocabulary 120) through the adapter: content-substitution
            dependency extraction, pre-check and compile (stage1/c3_compile.py main, unchanged); the teacher is built
            with its checkpoint's vocabulary (120 tokens) -- the only deviation from the G-0 run, needed to load it.
            The result is compared with the stored stage-1 compile_result.json: the compiled table, the pre-check
            scores and the per-head scores must be identical (extraction FLOPs use len(VOCAB) and change slightly).

  python stage2/g0_adapter_check.py hand
  python stage2/g0_adapter_check.py compile --teacher stage1/results/c4/c4_addition__rope__1M__s6__N100000/teacher_best.pt \
      --seed 6 --ref stage1/results/c4/addition_compile_s6/compile_result.json --out stage2/results/g0/adapter_check/c4_addition_s6
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "stage1"))
import torch                     # noqa: E402
import tasks as T                # noqa: E402

OUT = HERE / "results" / "g0" / "adapter_check"


def stage1_data():
    return {t: {"train": T.train_set(t, 2000, 6), "eval": T.eval_sets(t, 1000, 500)} for t in ("addition", "parity")}


def hand():
    torch.set_num_threads(1)
    t0 = time.time()
    before = stage1_data()
    import g_adapter as A
    A.install()
    import g_tasks as G
    import g0a
    import models as M
    import run as R
    import pf as PFM
    import c3_compile as CC
    import c4_select as CS
    from pf_search_v2_check import HAND, TableRuleModel
    from pf_rules import RuleModel
    res = {"vocab_size": len(T.VOCAB), "added_tokens": T.VOCAB[120:]}
    after = stage1_data()
    res["stage1_data_identical"] = {t: before[t] == after[t] for t in before}
    cfg = dict(M.SCALES["pf_search"]["1M"], policy=HAND)
    torch.manual_seed(0)
    pf = M.build("pf_search", len(T.VOCAB), [T.TOK[d] for d in T.DIGITS], cfg)
    pf.eval()
    acc = {}
    with torch.no_grad():
        ev = T.eval_sets("addition", 1000, 500)
        acc["addition_c1_3_hand_table"] = {l: R.exact_match(TableRuleModel(pf, HAND), e, "pf_search", cfg)[0]
                                           for l, e in ev.items()}
        acc["addition_c1_1_rule_controller"] = {l: R.exact_match(RuleModel(pf, "addition"), e, "pf_search", cfg)[0]
                                                for l, e in ev.items()}
        ev = T.eval_sets("parity", 1000, 500)
        acc["parity_c1_1_rule_controller"] = {l: R.exact_match(RuleModel(pf, "parity"), e, "pf_search", cfg)[0]
                                              for l, e in ev.items()}
    ci = CC.class_ids()

    class AdaptedHand(torch.nn.Module):          # G-0a controller, token kinds from the adapted pf.token_classes
        def __init__(self, task):
            super().__init__()
            self.task = task

        def forward(self, tokens, offset=None, recur=None):
            cls = PFM.token_classes(tokens, ci["digits"], ci["plus"], ci["eq"], ci["bar"], ci["node_lo"], ci["node_hi"])
            ctl = g0a.Controller(self.task, g0a.TABLES[self.task], cls, pf.V, pf.K)
            return PFM.PF.forward(pf, tokens, controller=ctl)

    same, sim = {}, {}
    for task in G.SUITE:
        ev = T.eval_sets(task, 1000, 500)
        with torch.no_grad():
            acc["%s_g0a_hand_table" % task] = {l: R.exact_match(AdaptedHand(task), e, "pf_search", cfg)[0]
                                               for l, e in ev.items()}
        same[task] = {"eval": ev == G.eval_sets(task, 1000, 500),
                      "train_s9_s10_s11_first2000": all(T.train_set(task, 2000, s) == G.train_set(task, 2000, s)
                                                        for s in (9, 10, 11)),
                      "select": CS.selection_set(task) == G.selection_set(task)}
        exs = G.train_set(task, 200, 9)
        rows = []
        for i, e in enumerate(exs):
            x, y = R.make_batch([e])
            rows += [(i, t, None, None) for t in range(x.shape[1]) if int(y[0, t]) != -100]
        P, _ = CC.simulate(exs, rows, [list(c) for c in g0a.TABLES[task]])
        ok = True
        for r, (i, t, _, _) in enumerate(rows):
            p, a = exs[i]
            if [int(v) for v in P[:, r]] != g0a.head_path(p + a, g0a.TABLES[task])[t]:
                ok = False
                break
        sim[task] = {"output_steps": len(rows), "same_read_positions": ok}
    res.update({"accuracy": acc, "g0_data_identical_to_g_tasks": same, "compile_simulation_vs_pf_head_path": sim})
    res["all_exact"] = all(v == 1.0 for d in acc.values() for v in d.values())
    res["all_identical"] = (all(res["stage1_data_identical"].values())
                            and all(all(d.values()) for d in same.values())
                            and all(d["same_read_positions"] for d in sim.values()))
    res["wall_s"] = round(time.time() - t0, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hand.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("all_exact", "all_identical", "wall_s")}))
    for k, v in acc.items():
        print(k, {l: round(x, 3) for l, x in v.items()})


def compile_check(a):
    import g_adapter as A
    A.install()
    import models as M
    import c3_compile as CC
    ck = torch.load(a.teacher, weights_only=False)
    v0 = ck["model"]["tok.weight"].shape[0]
    build = M.build

    def build_ck_vocab(kind, vocab, digit_ids, cfg):     # load the stage-1 teacher with its own vocabulary
        return build(kind, v0 if kind == "rope" else vocab, digit_ids, cfg)
    M.build = build_ck_vocab
    os.environ.setdefault("THREADS", "1")
    sys.argv = ["c3_compile.py", "--task", "addition", "--seed", str(a.seed), "--teacher", a.teacher,
                "--dependency", "substitution", "--out", a.out]
    A.run_script("c3_compile", sys.argv[1:])
    new = json.loads((pathlib.Path(a.out) / "compile_result.json").read_text())
    ref = json.loads(pathlib.Path(a.ref).read_text())
    cmp_ = {"teacher": a.teacher, "teacher_vocab": v0, "reference": a.ref,
            "same_policy": new.get("policy") == ref.get("policy"),
            "policy": new.get("policy"), "reference_policy": ref.get("policy"),
            "precheck_dependency_new": new["precheck"]["dependency"],
            "precheck_dependency_reference": ref["precheck"]["dependency"],
            "same_precheck_scores": new["precheck"]["dependency"] == ref["precheck"]["dependency"],
            "same_per_head_scores": [h["score_after_cover"] for h in new["per_head"]] ==
                                    [h["score_after_cover"] for h in ref["per_head"]],
            "same_table_score": new["table_score_dependency"] == ref["table_score_dependency"],
            "same_class_symbols": new["extraction"]["substitution"]["class_symbols"] ==
                                  ref["extraction"]["substitution"]["class_symbols"],
            "extraction_flops_new_vocab123": new["extraction"]["flops"],
            "extraction_flops_reference_vocab120": ref["extraction"]["flops"]}
    cmp_["identical"] = all(cmp_[k] for k in ("same_policy", "same_precheck_scores", "same_per_head_scores",
                                               "same_table_score", "same_class_symbols"))
    (pathlib.Path(a.out) / "comparison.json").write_text(json.dumps(cmp_, indent=1))
    print("COMPARISON", json.dumps({k: cmp_[k] for k in ("identical", "same_policy", "same_precheck_scores")}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("hand", "compile"))
    p.add_argument("--teacher")
    p.add_argument("--seed", type=int)
    p.add_argument("--ref")
    p.add_argument("--out")
    a = p.parse_args()
    hand() if a.mode == "hand" else compile_check(a)
