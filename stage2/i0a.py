"""I-0a diagnostic (stage2/DESIGN.md 10.4 and 10.7, 10.7 first): when does a teacher know "where"?  No student or
baseline training; the compile rule is unchanged (stage1/c3_compile.py is executed as is, only timed).

Tasks, one teacher each, unseen seed 20: addition (stage-1 format, no BOS), mul1 (G-0 format, no BOS, through
stage2/g_adapter.py), xor and rev_xor (BOS, through stage2/h_adapter.py).

  time                 time estimate (results/i0a/time_estimate.json); stop if > 48 h
  teacher --task T     rope 1M, the stage-1 protocol (stage1/run.py: 20,000 steps, cosine, N = 100,000, seed 20) trained
                       to the end.  stage1/run.py is executed from its own source with three textual changes (asserted
                       to apply exactly once each; the file is not edited): (1) the early stop (in-distribution >= 99 %
                       at two consecutive evaluations) is not applied -- the diagnostic trains to 20,000 steps (10.4,
                       10.7-4; the schedule is the 20,000-step cosine either way); (2) the process CPU seconds of the
                       training segments are accumulated next to the wall seconds (time.process_time, 1 thread);
                       (3) every 1,000 steps the model is also saved as teacher_step<step>.pt (the teacher_best.pt
                       format: model, step, acc, kind, cfg, train_flops_cum; plus the cumulative training CPU / wall
                       seconds).  Checkpoints are local only (*.pt is gitignored).
  compile --task T --step S
                       stage1/c3_compile.py --dependency substitution on teacher_step<S>.pt, data seed 20 (the teacher's
                       training data, as in H-0), executed unchanged with --no-gate: the pre-check is computed and
                       recorded (compile_result.json precheck.passed) but does not stop the search, so a table exists at
                       every timepoint; the stop rules below do not use the pre-check (it needs the hand-written correct
                       table).  Timing (cpu.json): the process CPU / wall seconds of the dependency extraction
                       (c3_compile.extract_substitution, wrapped with a timer) and of the whole compile; search and the
                       rest = total - extraction.
  measure --task T     per timepoint (1k 2k 3k 4k 6k 8k 12k 16k 20k): on "select:<task>" (1,000) the teacher's answer
                       token accuracy (answer tokens without <eos>, and all exact-match targets with <eos>) and sequence
                       accuracy; the compiled table's columns and per-head share of the table's dependency score
                       (per_head score_after_cover / table_score_dependency); the self ratio = table_score_dependency /
                       score of all heads staying on position 1 (the first content position: index 1 with BOS, index 0
                       without; from the local dependency_rows.pt with c3_compile.dense / table_score); correct
                       position = every moving head of the correct table (c3_compile.correct_table) has its position
                       read by some compiled head on >= 0.99 of the output steps (compile_result
                       reference_agreement_with_correct_table, the G-0 / H-0 report rule); also table_reads on the
                       selection set (addition: stage1/c1_3_table_reads.reads_share; xor, rev_xor: stage2/h0b.bit_reads);
                       the costs (teacher training FLOPs / CPU s to the step, extraction FLOPs, compile CPU s).
  report               the stop rules (10.7, fixed before the data):
                       R1 = two consecutive timepoints with the same set of columns (head numbers ignored; compared as
                            the sorted list of the three columns) and self ratio >= 2 at both;
                       R2 = the same for the columns of the heads with >= 10 % of the table's dependency score;
                       the rule stops at the second of the two timepoints and uses that table.  Per task and rule: stop
                       timepoint, correct position, cumulative teacher + compile FLOPs (teacher training + extraction of
                       every compile up to the stop) and CPU s (teacher training + every compile up to the stop), as
                       fractions of the 20,000-step teacher; the first timepoint from which the table is a correct
                       position table at every later timepoint.  Adoption (10.7): in all four tasks the rule stops at a
                       correct position table with FLOPs <= 50 % and CPU <= 50 %; R1 first, then R2.

  python stage2/i0a.py time
  python stage2/i0a.py teacher --task xor
  python stage2/i0a.py compile --task xor --step 4000
  python stage2/i0a.py measure --task xor
  python stage2/i0a.py report
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

OUT = pathlib.Path(os.environ.get("I0A_OUT", HERE / "results" / "i0a"))   # I0A_OUT / I0A_MAX_STEPS: smoke tests only
SEED = 20
TASKS = ("addition", "mul1", "xor", "rev_xor")
ADAPTER = {"addition": None, "mul1": "g_adapter", "xor": "h_adapter", "rev_xor": "h_adapter"}
BOS_TASK = {"addition": False, "mul1": False, "xor": True, "rev_xor": True}
TIMEPOINTS = tuple(int(x) for x in os.environ.get("I0A_TIMEPOINTS", "1000,2000,3000,4000,6000,8000,12000,16000,20000").split(","))
MAX_STEPS = int(os.environ.get("I0A_MAX_STEPS", "20000"))
_MAX_UNUSED, LIMIT_H, SHARE_MIN, RATIO_MIN, FRAC_MAX = 20000, 48, 0.10, 2.0, 0.5


def install(task):
    if ADAPTER[task]:
        __import__(ADAPTER[task]).install()


def teacher_dir(task):
    return OUT / ("i0a_%s__rope__1M__s%d__N100000" % (task, SEED))


def compile_dir(task, step):
    return OUT / ("%s_compile_s%d_step%05d" % (task, SEED, step))


# ---------------------------------------------------------------- time estimate
def cmd_time(a):
    def rate(pat):
        r = []
        for p in glob.glob(str(HERE.parent / pat)):
            f = json.loads(open(p).read())
            r.append((f["wall_train_s"] + f["wall_eval_s"]) / f["steps"])
        return max(r), len(r)
    src = {"addition": ("stage1/results/c3*/*addition__rope__1M*/final.json",
                        "stage1/results/c4/*addition__rope__1M*/final.json", "stage1/results/c4/addition_compile_s*"),
           "mul1": ("stage2/results/g0/*mul1__rope__1M*/final.json", "stage2/results/g0p/*mul1__rope__1M*/final.json",
                    "stage2/results/g0*/mul1_compile_s*"),
           "xor": ("stage2/results/h0/h0_xor__rope__1M*/final.json", None, "stage2/results/h0*/xor_compile_s*"),
           "rev_xor": ("stage2/results/h0/h0_rev_xor__rope__1M*/final.json", None,
                       "stage2/results/h0*/rev_xor_compile_s*")}
    per, cpu = {}, 0.0
    for t, (p1, p2, pc) in src.items():
        rates = [rate(p1)[0]] + ([rate(p2)[0]] if p2 else [])
        sps = max(rates)
        comp = [json.loads(open(p + "/compile_result.json").read())["wall_s"] for p in glob.glob(str(ROOT / pc))
                if os.path.exists(p + "/compile_result.json")]
        c = max(comp)
        per[t] = {"teacher_s_per_step_max": sps, "teacher_20000_h": sps * MAX_STEPS / 3600, "compile_s_max": c,
                  "compiles": len(TIMEPOINTS), "compiles_h": c * len(TIMEPOINTS) / 3600}
        cpu += sps * MAX_STEPS + c * len(TIMEPOINTS)
    longest_teacher = max(v["teacher_20000_h"] for v in per.values())
    comp_cpu = sum(v["compiles_h"] for v in per.values())
    longest_compile = max(v["compile_s_max"] for v in per.values()) / 3600
    wall = longest_teacher + comp_cpu / 4 + longest_compile
    res = {"per_task": per, "cpu_hours": cpu / 3600,
           "wall_hours_teachers_in_parallel_then_compiles_4_workers_plus_longest_compile": wall,
           "limit_hours": LIMIT_H,
           "note": "rates: the largest measured (wall train + eval) / step of rope 1M teachers of the task (1 thread, "
                   "4 jobs at a time, same machine) and the largest measured compile wall; measuring adds < 1 min per "
                   "task"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "time_estimate.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


# ---------------------------------------------------------------- teacher
PATCHES = [
    ('            if st["hits"] >= 2:\n',
     '            if False and st["hits"] >= 2:          # I-0a: trained to the end (no early stop)\n'),
    ('            t_seg = time.time()\n',
     '            t_seg = time.time(); c_seg = time.process_time()\n'),
    ('    t_seg = time.time()\n',
     '    t_seg = time.time(); c_seg = time.process_time()\n'),
    ('            st["wall_train_s"] += time.time() - t_seg\n',
     '            st["wall_train_s"] += time.time() - t_seg\n'
     '            st["cpu_train_s"] = st.get("cpu_train_s", 0.0) + time.process_time() - c_seg\n'),
    ('"eval_flops_cum": st["eval_flops"], "segment": seg["segment"]})\n',
     '"eval_flops_cum": st["eval_flops"], "segment": seg["segment"],\n'
     '                        "cpu_train_s_cum": round(st["cpu_train_s"], 2)})\n'),
    ('            os.replace(str(ck) + ".tmp", ck)\n',
     '            os.replace(str(ck) + ".tmp", ck)\n'
     '            torch.save({"model": model.state_dict(), "step": st["step"], "acc": rec["acc"], "kind": a.kind,\n'
     '                        "cfg": cfg, "train_flops_cum": st["train_flops"], "cpu_train_s_cum": st["cpu_train_s"],\n'
     '                        "wall_train_s_cum": st["wall_train_s"]}, str(out / ("teacher_step%05d.pt" % st["step"])) + ".tmp")\n'
     '            os.replace(str(out / ("teacher_step%05d.pt" % st["step"])) + ".tmp", out / ("teacher_step%05d.pt" % st["step"]))\n'),
]


def cmd_teacher(a):
    install(a.task)
    path = ROOT / "stage1" / "run.py"
    src = path.read_text()
    for old, new in PATCHES:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    argv = ["--task", a.task, "--kind", "rope", "--scale", "1M", "--seed", str(SEED), "--N", "100000",
            "--max-steps", str(MAX_STEPS), "--phase", "i0a", "--out-root", str(OUT), "--threads", "1"]
    if a.resume:
        argv.append("--resume")
    sys.argv = [str(path)] + argv
    g = {"__name__": "__main__", "__file__": str(path)}
    exec(compile(src, str(path), "exec"), g)


# ---------------------------------------------------------------- compile
def cmd_compile(a):
    install(a.task)
    import c3_compile as CC
    ext = {"cpu": 0.0, "wall": 0.0}
    inner = CC.extract_substitution

    def timed(*args, **kw):
        c0, w0 = time.process_time(), time.time()
        r = inner(*args, **kw)
        ext["cpu"] += time.process_time() - c0
        ext["wall"] += time.time() - w0
        return r
    CC.extract_substitution = timed
    out = compile_dir(a.task, a.step)
    ck = teacher_dir(a.task) / ("teacher_step%05d.pt" % a.step)
    assert ck.exists(), ck
    assert not (out / "compile_result.json").exists(), "refusing to overwrite %s (rule 5)" % out
    path = ROOT / "stage1" / "c3_compile.py"
    src = path.read_text()
    key = 'if __name__ == "__main__":'
    block = src[src.index(key):].replace(key, "if True:", 1)
    sys.argv = [str(path), "--task", a.task, "--seed", str(SEED), "--teacher", str(ck), "--dependency",
                "substitution", "--out", str(out), "--no-gate"]
    c0, w0 = time.process_time(), time.time()
    exec(compile(block, str(path), "exec"), CC.__dict__)
    tot_c, tot_w = time.process_time() - c0, time.time() - w0
    (out / "cpu.json").write_text(json.dumps({
        "extraction_cpu_s": ext["cpu"], "extraction_wall_s": ext["wall"], "total_cpu_s": tot_c, "total_wall_s": tot_w,
        "search_and_rest_cpu_s": tot_c - ext["cpu"], "search_and_rest_wall_s": tot_w - ext["wall"],
        "threads": {"torch": int(os.environ.get("THREADS", "1")), "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS")},
        "note": "process CPU seconds (time.process_time) of c3_compile.extract_substitution and of the whole compile "
                "(loading, training data, extraction, pre-check, search, writing); search and the rest = total - "
                "extraction"}, indent=1))


# ---------------------------------------------------------------- measure
def cmd_measure(a):
    install(a.task)
    import numpy as np
    import torch
    import tasks as T
    import models as M
    import run as R
    import c4_select as CS
    import c3_compile as CC
    torch.set_num_threads(1)
    sel = CS.selection_set(a.task)
    corr = CC.correct_table(a.task)
    moving = [j for j in range(3) if any(m != 0 for m in corr[j])]
    p1 = 1 if BOS_TASK[a.task] else 0
    if BOS_TASK[a.task]:
        assert all(e[0][0] == T.TOK["<bos>"] for e in sel)
    reads = None
    if a.task == "addition":
        import c1_3_table_reads as TR
        reads = lambda pol: TR.reads_share(pol, sel)                          # noqa: E731
    elif a.task in ("xor", "rev_xor"):
        import g0a
        import h0b
        reads = lambda pol: h0b.bit_reads(a.task, pol, sel, T, g0a)           # noqa: E731
    rows = {}
    for step in TIMEPOINTS:
        ckp = teacher_dir(a.task) / ("teacher_step%05d.pt" % step)
        ck = torch.load(ckp, weights_only=False)
        assert ck["step"] == step
        m = M.build("rope", len(T.VOCAB), [T.TOK[x] for x in T.DIGITS], ck["cfg"])
        m.load_state_dict(ck["model"])
        m.eval()
        ok_tok = ok_ans = n_tok = n_ans = ok_seq = 0
        with torch.no_grad():
            for i in range(0, len(sel), 128):
                x, y = R.make_batch(sel[i:i + 128])
                pred = m(x).argmax(-1)
                msk = y != -100
                ans = msk & (y != T.EOS)
                hit = pred == y
                ok_tok += int((hit & msk).sum())
                n_tok += int(msk.sum())
                ok_ans += int((hit & ans).sum())
                n_ans += int(ans.sum())
                ok_seq += int((hit | ~msk).all(1).sum())
        r = {"step": step, "teacher": {"train_flops_cum": ck["train_flops_cum"], "cpu_train_s_cum": ck["cpu_train_s_cum"],
                                       "wall_train_s_cum": ck["wall_train_s_cum"], "acc_eval": ck["acc"]},
             "selection": {"token_accuracy_answer": ok_ans / n_ans, "token_accuracy_answer_and_eos": ok_tok / n_tok,
                           "sequence_accuracy": ok_seq / len(sel)}}
        cd = compile_dir(a.task, step)
        cr = json.loads((cd / "compile_result.json").read_text())
        cpu = json.loads((cd / "cpu.json").read_text())
        S = CC.dense(torch.load(cd / "dependency_rows.pt", weights_only=False)["rows"], 2)
        s1 = CC.table_score(S, [np.full(S.shape[0], p1, dtype=int)])[0]
        tot = cr["table_score_dependency"]
        ag = cr["reference_agreement_with_correct_table"]
        heads = [{"column": cr["policy"][j], "column_named": cr["per_head"][j]["column"],
                  "score": cr["per_head"][j]["score_after_cover"],
                  "share": cr["per_head"][j]["score_after_cover"] / tot if tot > 0 else None} for j in range(3)]
        r["compile"] = {"policy": cr["policy"], "heads": heads, "table_score": tot,
                        "stay_on_first_content_position_score": s1, "first_content_position": p1,
                        "self_ratio": tot / s1 if s1 > 0 else None,
                        "precheck_existing_rule": {"correct": cr["precheck"]["dependency"]["correct"],
                                                   "all_stay": cr["precheck"]["dependency"]["all_stay"],
                                                   "ratio": cr["precheck"]["dependency"]["ratio"],
                                                   "passed": cr["precheck"]["passed"]},
                        "agreement_moving_correct_heads": {j: ag["correct_head%d_position_read_by_some_compiled_head" % j]
                                                           for j in moving},
                        "correct_position": all(ag["correct_head%d_position_read_by_some_compiled_head" % j] >= 0.99
                                                for j in moving),
                        "table_reads_selection": reads(cr["policy"]) if reads else None,
                        "extraction_flops": cr["extraction"]["flops"], "cpu": cpu, "wall_s": cr["wall_s"]}
        rows[step] = r
        print(a.task, step, json.dumps({"tok": round(r["selection"]["token_accuracy_answer"], 3),
                                        "seq": round(r["selection"]["sequence_accuracy"], 3),
                                        "ratio": r["compile"]["self_ratio"] and round(r["compile"]["self_ratio"], 2),
                                        "correct": r["compile"]["correct_position"]}), flush=True)
    import h0a
    (OUT / ("measure_%s.json" % a.task)).write_text(json.dumps(
        {"task": a.task, "seed": SEED, "bos": BOS_TASK[a.task], "moving_correct_heads": moving,
         "timepoints": rows, "env": h0a.env(["stage2/i0a.py"])}, indent=1))


# ---------------------------------------------------------------- report
def colset(heads, share_min=None):
    return sorted(tuple(h["column"]) for h in heads if share_min is None or (h["share"] or 0) >= share_min)


def stop(rows, rule):
    tps = [rows[str(t)] for t in TIMEPOINTS]
    for i in range(1, len(tps)):
        a, b = tps[i - 1]["compile"], tps[i]["compile"]
        sm = SHARE_MIN if rule == "R2" else None
        if (colset(a["heads"], sm) == colset(b["heads"], sm) and (a["self_ratio"] or 0) >= RATIO_MIN
                and (b["self_ratio"] or 0) >= RATIO_MIN):
            return i
    return None


def cmd_report(a):
    res, md = {}, []
    for t in TASKS:
        mj = json.loads((OUT / ("measure_%s.json" % t)).read_text())
        rows = mj["timepoints"]
        tps = [rows[str(s)] for s in TIMEPOINTS]
        full_f = tps[-1]["teacher"]["train_flops_cum"]
        full_c = tps[-1]["teacher"]["cpu_train_s_cum"]
        assert tps[-1]["step"] == MAX_STEPS
        per = []
        for i, r in enumerate(tps):
            c = r["compile"]
            per.append({"step": r["step"], "token_answer": r["selection"]["token_accuracy_answer"],
                        "token_answer_eos": r["selection"]["token_accuracy_answer_and_eos"],
                        "sequence": r["selection"]["sequence_accuracy"], "self_ratio": c["self_ratio"],
                        "correct_position": c["correct_position"],
                        "precheck_existing_rule_passed": c["precheck_existing_rule"]["passed"],
                        "same_as_previous_exact": i > 0 and c["policy"] == tps[i - 1]["compile"]["policy"],
                        "same_as_previous_R1": i > 0 and colset(c["heads"]) == colset(tps[i - 1]["compile"]["heads"]),
                        "same_as_previous_R2": i > 0 and colset(c["heads"], SHARE_MIN) ==
                        colset(tps[i - 1]["compile"]["heads"], SHARE_MIN),
                        "shares": [h["share"] for h in c["heads"]],
                        "teacher_flops": r["teacher"]["train_flops_cum"], "teacher_cpu_s": r["teacher"]["cpu_train_s_cum"],
                        "extraction_flops": c["extraction_flops"], "compile_cpu_s": c["cpu"]["total_cpu_s"],
                        "extraction_cpu_s": c["cpu"]["extraction_cpu_s"],
                        "search_and_rest_cpu_s": c["cpu"]["search_and_rest_cpu_s"]})
        first_persistent = None
        for i in range(len(per)):
            if all(p["correct_position"] for p in per[i:]):
                first_persistent = per[i]["step"]
                break
        rules = {}
        for rule in ("R1", "R2"):
            i = stop(rows, rule)
            if i is None:
                rules[rule] = {"stops": False}
                continue
            f = per[i]["teacher_flops"] + sum(p["extraction_flops"] for p in per[:i + 1])
            cpu = per[i]["teacher_cpu_s"] + sum(p["compile_cpu_s"] for p in per[:i + 1])
            rules[rule] = {"stops": True, "stop_step": per[i]["step"], "correct_position": per[i]["correct_position"],
                           "flops": f, "flops_fraction": f / full_f, "cpu_s": cpu, "cpu_fraction": cpu / full_c,
                           "teacher_flops_fraction": per[i]["teacher_flops"] / full_f,
                           "teacher_cpu_fraction": per[i]["teacher_cpu_s"] / full_c,
                           "compiles": i + 1, "precheck_existing_rule_passed_at_stop": per[i]["precheck_existing_rule_passed"],
                           "token_answer": per[i]["token_answer"], "sequence": per[i]["sequence"]}
            rules[rule]["meets"] = (rules[rule]["correct_position"] and rules[rule]["flops_fraction"] <= FRAC_MAX
                                    and rules[rule]["cpu_fraction"] <= FRAC_MAX)
        res[t] = {"timepoints": per, "first_persistent_correct_position": first_persistent, "rules": rules,
                  "teacher_20000": {"flops": full_f, "cpu_s": full_c}}
    adopt = {r: all(res[t]["rules"][r].get("meets", False) for t in TASKS) for r in ("R1", "R2")}
    out = {"design": "stage2/DESIGN.md 10.4, 10.7", "tasks": res, "adoption_condition_met": adopt,
           "adopted_rule": "R1" if adopt["R1"] else ("R2" if adopt["R2"] else None)}
    (OUT / "summary.json").write_text(json.dumps(out, indent=1))
    YN = {True: "예", False: "아니오", None: "—"}
    for t in TASKS:
        md.append("\n### %s\n| step | 답 토큰 · +eos | 시퀀스 | 자기 대비 비율 | 정답 위치 | 기존 사전 확인 | 직전과 같음 (번호 포함 · R1 · R2) | 헤드 점수 비중 | 교사 CPU s | 추출 · 탐색 CPU s |" % t)
        md.append("|---|---|---|---|---|---|---|---|---|---|")
        for p in res[t]["timepoints"]:
            md.append("| %d | %.3f · %.3f | %.3f | %s | %s | %s | %s · %s · %s | %s | %.0f | %.0f · %.0f |" % (
                p["step"], p["token_answer"], p["token_answer_eos"], p["sequence"],
                "%.2f" % p["self_ratio"] if p["self_ratio"] else "—", YN[p["correct_position"]],
                YN[p["precheck_existing_rule_passed"]], YN[p["same_as_previous_exact"]], YN[p["same_as_previous_R1"]],
                YN[p["same_as_previous_R2"]], " · ".join("%.2f" % s for s in p["shares"]), p["teacher_cpu_s"],
                p["extraction_cpu_s"], p["search_and_rest_cpu_s"]))
    md.append("\n| 과제 | 규칙 | 멈춘 step | 정답 위치 | FLOPs (20,000 step 교사 대비) | CPU s (대비) | 조건 충족 | 정답 위치가 처음 나타나 유지되는 step |")
    md.append("|---|---|---|---|---|---|---|---|")
    for t in TASKS:
        for rule in ("R1", "R2"):
            r = res[t]["rules"][rule]
            if not r["stops"]:
                md.append("| %s | %s | 멈추지 않음 | — | — | — | 아니오 | %s |" % (t, rule, res[t]["first_persistent_correct_position"]))
            else:
                md.append("| %s | %s | %d | %s | %.3e (%.2f) | %.0f (%.2f) | %s | %s |" % (
                    t, rule, r["stop_step"], YN[r["correct_position"]], r["flops"], r["flops_fraction"], r["cpu_s"],
                    r["cpu_fraction"], YN[r["meets"]], res[t]["first_persistent_correct_position"]))
    md.append("\nadoption: R1 %s, R2 %s -> %s" % (YN[adopt["R1"]], YN[adopt["R2"]], out["adopted_rule"]))
    print("\n".join(md))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("time")
    q = sp.add_parser("teacher")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--resume", action="store_true")
    q = sp.add_parser("compile")
    q.add_argument("--task", choices=TASKS, required=True)
    q.add_argument("--step", type=int, choices=TIMEPOINTS, required=True)
    q = sp.add_parser("measure")
    q.add_argument("--task", choices=TASKS, required=True)
    sp.add_parser("report")
    a = p.parse_args()
    {"time": cmd_time, "teacher": cmd_teacher, "compile": cmd_compile, "measure": cmd_measure,
     "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
