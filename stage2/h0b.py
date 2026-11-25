"""H-0b diagnostic (stage2/DESIGN.md 9.13-5) -- no teacher, student or baseline training; no change to the pipeline
code (stage1/*.py, stage2/h_adapter.py are imported, not edited).  Results are not used for any verdict (C design
evidence only).

The H-0 teachers discarded by the T2 threshold (selection sequence accuracy < 0.95): XOR s15, s16, s17, s215, s315 and
rev_xor s15, s215, s315, s415, s16, s216, s316, s416 -- their kept judgment checkpoints (teacher_best.pt, checked to be
the final.json judgment step), BOS format, through the H-0 adapter (stage2/h_adapter.py).  Per checkpoint:
  - token accuracy on "select:<task>" (1,000, BOS): teacher-forced argmax over the answer tokens -- the bits alone and
    the bits + <eos> (every exact-match target) -- and the sequence accuracy (cross-check with
    results/h0/teacher_select_<task>_s<seed>.json);
  - table_reads of the table compiled by the existing rule (stage1/c3_compile.py --dependency substitution through
    h_adapter.py, as in H-0: data seed = the teacher's run seed; run separately into
    results/h0b/<task>_s<seed>_compile): at the step that outputs the bit c_i = x_i ^ y_i, the share of (example,
    answer step) in which head j reads x_i / y_i (stage2/h0a.xor_reads with the BOS offset; rev_xor outputs i = n-1 ..
    0), on "select:<task>"; also per head the share of examples in which it reads BOS at the <eos> step (h0a.end_reads),
    reported for the x / y content heads (a head that stays on BOS reads it trivially);
  - the pre-check ratio with the all-"stay" reference on position 1 (the first operand token; with BOS the all-"stay"
    heads on position 0 score 0 by definition): correct / score(heads staying on position 1), from the compile's local
    dependency_rows.pt with stage1/c3_compile.dense / table_score (as stage2/h0_precheck_alt.py).  The compile's own
    recorded ratio (null under BOS) is kept too.
"aligned" = some head reads x_i and some head reads y_i at every answer bit step (both maxima 1.000), the H-0a
definition.  The compiled table is also compared with the H-0 compiled tables of the same task (passing teachers).

  python stage2/h0b.py        # writes stage2/results/h0b/diagnosis.json   (after the 13 compiles)
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import h_adapter as A           # noqa: E402

OUT = HERE / "results" / "h0b"
H0 = HERE / "results" / "h0"
FAILED = [("xor", s) for s in (15, 16, 17, 215, 315)] + [("rev_xor", s) for s in (15, 215, 315, 415, 16, 216, 316, 416)]
PASSING_COMPILES = {"xor": (15, 16, 17), "rev_xor": (17,)}


def bit_reads(task, table, exs, T, g0a):
    """at the step that outputs c_i (x_i ^ y_i): the share of (example, step) in which head j reads x_i / y_i"""
    cnt = {"x": [0, 0, 0], "y": [0, 0, 0]}
    n_all = 0
    for p, a in exs:
        assert p[0] == T.TOK["<bos>"]
        m = p.index(T.TOK["^"])
        n = m - 1
        path = g0a.head_path(p + a, table)
        eq = len(p) - 1
        for k in range(n):
            i = k if task == "xor" else n - 1 - k
            n_all += 1
            for j in range(3):
                cnt["x"][j] += path[eq + k][j] == 1 + i
                cnt["y"][j] += path[eq + k][j] == m + 1 + i
    return {"head%d" % j: {"reads_x_i": cnt["x"][j] / n_all, "reads_y_i": cnt["y"][j] / n_all} for j in range(3)}


def end_reads(table, exs, bos, g0a):
    at_eos = [0, 0, 0]
    for p, a in exs:
        s = p + a
        path = g0a.head_path(s, table)
        last = len(s) - 2
        for j in range(3):
            at_eos[j] += s[path[last][j]] == bos
    return {"head%d" % j: at_eos[j] / len(exs) for j in range(3)}


def main():
    A.install()
    import numpy as np
    import torch
    import tasks as T
    import models as M
    import run as R
    import c4_select as CS
    import c3_compile as CC
    import g0a
    import h0a
    torch.set_num_threads(1)
    sels = {t: CS.selection_set(t) for t in ("xor", "rev_xor")}
    passing = {}
    for t, seeds in PASSING_COMPILES.items():
        for s in seeds:
            passing["%s_s%d" % (t, s)] = json.loads((H0 / ("%s_compile_s%d" % (t, s)) / "compile_result.json").read_text())["policy"]
    rows = {}
    for task, seed in FAILED:
        sel = sels[task]
        label = "%s_s%d" % (task, seed)
        d = H0 / ("h0_%s__rope__1M__s%d__N100000" % (task, seed))
        row = {"task": task, "run": str(d.relative_to(ROOT)), "run_seed": seed}
        ckp = d / "teacher_best.pt"
        if not ckp.exists():
            rows[label] = dict(row, checkpoint="없음")
            continue
        ck = torch.load(ckp, weights_only=False)
        fin = json.loads((d / "final.json").read_text())
        assert ck["step"] == fin["judgment"]["step"]
        m = M.build("rope", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
        m.load_state_dict(ck["model"])
        m.eval()
        ok_tok = ok_bit = n_tok = n_bit = ok_seq = 0
        with torch.no_grad():
            for i in range(0, len(sel), 128):
                x, y = R.make_batch(sel[i:i + 128])
                pred = m(x).argmax(-1)
                msk = y != -100
                bit = msk & (y != T.EOS)
                hit = pred == y
                ok_tok += int((hit & msk).sum())
                n_tok += int(msk.sum())
                ok_bit += int((hit & bit).sum())
                n_bit += int(bit.sum())
                ok_seq += int((hit | ~msk).all(1).sum())
        chk = json.loads((H0 / ("teacher_select_%s_s%d.json" % (task, seed))).read_text())
        row.update({"checkpoint": str(ckp.relative_to(ROOT)), "judgment_step": ck["step"], "run_steps": fin["steps"],
                    "selection_set": {"generation_seed": "select:%s" % task, "size": len(sel)},
                    "token_accuracy_bits": ok_bit / n_bit, "token_accuracy_bits_and_eos": ok_tok / n_tok,
                    "sequence_accuracy": ok_seq / len(sel), "h0_teacher_check_sequence_accuracy": chk["selection_accuracy"],
                    "answer_bits": n_bit, "answer_tokens": n_tok})
        cd = OUT / ("%s_compile" % label)
        cr_p, rows_p = cd / "compile_result.json", cd / "dependency_rows.pt"
        if not cr_p.exists():
            row["compile"] = "없음 (compile not run)"
            rows[label] = row
            continue
        cr = json.loads(cr_p.read_text())
        dep = cr["precheck"]["dependency"]
        row["compile_data_seed"] = cr["data_seed"]
        row["precheck_recorded"] = {"correct": dep["correct"], "all_stay_on_bos": dep["all_stay"], "ratio": dep["ratio"],
                                    "passed": cr["precheck"]["passed"]}
        if rows_p.exists():
            S = CC.dense(torch.load(rows_p, weights_only=False)["rows"], 2)
            s1 = CC.table_score(S, [np.ones(S.shape[0], dtype=int)])[0]
            row["precheck_position_1"] = {"correct": dep["correct"], "stay_on_position_1": s1,
                                          "ratio": dep["correct"] / s1 if s1 > 0 else None,
                                          "ge_2": dep["correct"] >= 2 * s1}
        else:
            row["precheck_position_1"] = "없음 (dependency_rows.pt missing)"
        if "policy" in cr:
            tr = bit_reads(task, cr["policy"], sel, T, g0a)
            er = end_reads(cr["policy"], sel, T.TOK["<bos>"], g0a)
            row["compiled"] = {"policy": cr["policy"], "policy_named": cr["policy_named"], "table_reads": tr,
                               "reads_x_i_max": max(v["reads_x_i"] for v in tr.values()),
                               "reads_y_i_max": max(v["reads_y_i"] for v in tr.values()),
                               "reads_bos_at_eos_step": er,
                               "x_head": max(tr, key=lambda h: tr[h]["reads_x_i"]),
                               "y_head": max(tr, key=lambda h: tr[h]["reads_y_i"]),
                               "same_as_h0_passing_compile": [k for k, v in passing.items()
                                                              if k.startswith(task + "_s") and v == cr["policy"]]}
            c = row["compiled"]
            c["x_head_reads_bos_at_eos_step"] = er[c["x_head"]]
            c["y_head_reads_bos_at_eos_step"] = er[c["y_head"]]
            row["compiled"]["aligned"] = row["compiled"]["reads_x_i_max"] == 1.0 and row["compiled"]["reads_y_i_max"] == 1.0
        else:
            row["compiled"] = "없음 (pre-check gate: no table)"
        rows[label] = row
        print(label, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()
                                 if k in ("judgment_step", "token_accuracy_bits", "token_accuracy_bits_and_eos",
                                          "sequence_accuracy")}),
              row["compiled"]["aligned"] if isinstance(row.get("compiled"), dict) else row.get("compiled"),
              flush=True)
    ref = {}
    for t in ("xor", "rev_xor"):
        ref[t] = {"table_reads": bit_reads(t, h0a.TABLES[t], sels[t], T, g0a),
                  "reads_bos_at_eos_step": end_reads(h0a.TABLES[t], sels[t], T.TOK["<bos>"], g0a)}
        for k, pol in passing.items():
            if k.startswith(t + "_s"):
                ref[t]["h0_passing_compile_" + k] = {"table_reads": bit_reads(t, pol, sels[t], T, g0a),
                                                     "reads_bos_at_eos_step": end_reads(pol, sels[t], T.TOK["<bos>"], g0a)}
    out = {"design": "stage2/DESIGN.md 9.13-5 (H-0b; not used for any verdict)", "teachers": rows,
           "reference_reads": ref, "env": h0a.env(["stage2/h0b.py"])}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagnosis.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
