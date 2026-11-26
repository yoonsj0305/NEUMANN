"""3-1 repeat diagnosis (stage3/DESIGN.md 7.5-1; evaluation only).  Raw data in results/3-1/diag_repeat/.

For each repeat student (the selected student of teachers 41, 42, 43 and teacher 43 restart 1), the judgment checkpoint
(teacher_best.pt) is evaluated on the same eval sets and batching as stage1/run.py exact_match.  Every failed
out-of-distribution example is classified by its first wrong scored step (the earliest answer position whose argmax
differs from the target):
  (a) eos timing: the target is <eos> and the prediction is not, or the prediction is <eos> and the target is not
  (b) digit value: target and prediction are both digits (different)
  other: anything else (recorded separately if it occurs)
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402

import l31                       # noqa: E402
import l31m                      # noqa: E402,F401  (sets l31.OUT to results/3-1/main)

OUT = HERE / "results" / "3-1" / "diag_repeat"
TASK = "repeat"
N_EXAMPLES = 5


def students():
    out = []
    for s in l31.TEACHER_SEEDS:
        sel = json.loads((l31.OUT / ("selection_%s_t%d.json" % (TASK, s))).read_text())
        out.append((s, sel["selected_restart"], "selected"))
    out.append((43, 1, "teacher 43 restart 1 (not selected)"))
    return out


def main():
    torch.set_num_threads(1)
    l31.setup(TASK)
    import tasks as T
    import models as M
    import run as R
    OUT.mkdir(parents=True, exist_ok=True)
    digits = {T.TOK[x] for x in T.DIGITS}
    inv = {v: k for k, v in T.TOK.items()}
    cfg0 = json.loads((l31.student_dir(TASK, 41, 0) / "config.json").read_text())
    evals = T.eval_sets(TASK, cfg0["id_size"], cfg0["ood_size"])
    summary = {"design": "stage3/DESIGN.md 7.5-1", "task": TASK,
               "classes": {"a_eos_timing": "first wrong step: target <eos> and prediction not <eos>, or prediction <eos> and target not <eos>",
                           "b_digit_value": "first wrong step: target and prediction both digits",
                           "other": "first wrong step of any other kind"},
               "eval_sets": "tasks.eval_sets(repeat, %d, %d), batching as stage1/run.py exact_match" % (cfg0["id_size"], cfg0["ood_size"]),
               "students": []}
    for s, r, role in students():
        l31.register_choice(TASK, s)
        d = l31.student_dir(TASK, s, r)
        ck = torch.load(d / "teacher_best.pt", weights_only=False)
        fin = json.loads((d / "final.json").read_text())
        assert ck["step"] == fin["judgment"]["step"]
        m = M.build("l1read", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
        m.load_state_dict(ck["model"])
        m.eval()
        rec = {"teacher_seed": s, "restart": r, "student_seed": l31.student_seed(s, r), "role": role,
               "run": str(d.relative_to(ROOT)), "judgment_step": ck["step"], "bins": {}}
        rows = []
        for label, exs in evals.items():
            order = sorted(range(len(exs)), key=lambda i: len(exs[i][0]) + len(exs[i][1]))
            ok = 0
            cnt = {"a_eos_timing": 0, "a_target_eos_pred_digit": 0, "a_pred_eos_target_digit": 0, "b_digit_value": 0, "other": 0}
            pos = {"a_eos_timing": [], "b_digit_value": []}
            ex_out = {"a_eos_timing": [], "b_digit_value": [], "other": []}
            with torch.no_grad():
                for i in range(0, len(order), 128):
                    idx = order[i:i + 128]
                    x, y = R.make_batch([exs[j] for j in idx])
                    pred = m(x).argmax(-1)
                    msk = y != -100
                    for b, j in enumerate(idx):
                        cols = msk[b].nonzero().flatten().tolist()
                        wrong = [c for c in cols if int(pred[b, c]) != int(y[b, c])]
                        if not wrong:
                            ok += 1
                            continue
                        c = wrong[0]
                        tgt, pr = int(y[b, c]), int(pred[b, c])
                        k = cols.index(c)                       # answer index of the first wrong step (0-based)
                        if tgt == T.EOS and pr != T.EOS:
                            cls = "a_eos_timing"
                            cnt["a_target_eos_pred_digit"] += 1
                        elif pr == T.EOS and tgt != T.EOS:
                            cls = "a_eos_timing"
                            cnt["a_pred_eos_target_digit"] += 1
                        elif tgt in digits and pr in digits:
                            cls = "b_digit_value"
                        else:
                            cls = "other"
                        cnt[cls] += 1
                        if cls in pos:
                            pos[cls].append({"answer_index": k, "answer_len_with_eos": len(cols)})
                        if len(ex_out[cls]) < N_EXAMPLES:
                            p, a = exs[j][0], exs[j][1]
                            ex_out[cls].append({"prompt": " ".join(inv[t] for t in p),
                                                "target": " ".join(inv[t] for t in a),
                                                "prediction_on_answer_steps": " ".join(inv[int(pred[b, cc])] for cc in cols),
                                                "first_wrong_answer_index": k, "target_token": inv[tgt],
                                                "predicted_token": inv[pr], "n_wrong_steps": len(wrong)})
            acc = ok / len(exs)
            nf = len(exs) - ok
            b_ = {"n": len(exs), "acc": acc, "final_json_acc": fin["judgment"]["acc"][label], "failures": nf, "counts": cnt,
                  "fraction_of_failures": {k: (cnt[k] / nf if nf else None) for k in ("a_eos_timing", "b_digit_value", "other")},
                  "first_wrong_position": {k: {"mean_answer_index": (sum(v["answer_index"] for v in pos[k]) / len(pos[k]) if pos[k] else None),
                                              "mean_answer_len_with_eos": (sum(v["answer_len_with_eos"] for v in pos[k]) / len(pos[k]) if pos[k] else None),
                                              "fraction_in_second_half": (sum(v["answer_index"] >= v["answer_len_with_eos"] / 2 for v in pos[k]) / len(pos[k]) if pos[k] else None)}
                                          for k in pos},
                  "examples": ex_out}
            rec["bins"][label] = b_
            rows.append((label, round(acc, 3), nf, cnt["a_eos_timing"], cnt["a_target_eos_pred_digit"],
                         cnt["a_pred_eos_target_digit"], cnt["b_digit_value"], cnt["other"]))
        (OUT / ("diag_repeat_t%d_r%d.json" % (s, r))).write_text(json.dumps(rec, indent=1))
        summary["students"].append({k: rec[k] for k in ("teacher_seed", "restart", "student_seed", "role", "judgment_step")}
                                   | {"bins": {lb: {k: v[k] for k in ("acc", "final_json_acc", "failures", "counts", "fraction_of_failures")}
                                               for lb, v in rec["bins"].items()}})
        print("t%d r%d" % (s, r), rows, flush=True)
    summary["env"] = l31m.env_info() | {"module": "stage3/l31diag.py"}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
