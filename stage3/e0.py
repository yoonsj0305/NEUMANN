"""3-E0: external benchmark expressivity survey, no training (stage3/DESIGN.md 9.1).  Raw data: results/3-E0/.

Tasks: stage3/e_tasks.py (the 15 Deletang et al. tasks, ported; replay check: stage3/e0_replay.py).
Machine and checks: stage3/l1.py, unchanged (L1 = Q <= 4 control states, H = 3 heads; the 3-0 A1 checks):
  (b)  p_h(t) <= t;  (c') positions, segment bits and q up to t unchanged when the tokens after t are replaced
  (t >= t0); correct read (copy-type tasks): the supply head of q_t reads the target, scored steps without <eos>;
  (d)  local determinism, key = (x_t, reads + segment bits of the moving heads, q_t, the same at t - 1): no conflict
  in the 100,000 training examples (seed 30) nor in any bin, nor against the training table.
  Sets: tasks.eval_sets(task, 2000, 500) (in-distribution 1-10: 2,000; each out-of-distribution bin: 500).
Adapter (install): the H-0 adapter (stage2/h_adapter.py: '<bos>' "other"; '-', '*', '^' the "+" kind and PF
separators) plus the e_tasks vocabulary and the 15 tasks in tasks.TASKS / SPEC / draw.  Only tasks without a PENDING
format entry can be encoded.

  python stage3/e0.py a1 --task even_pairs|reverse_string|duplicate_string|missing_duplicate_string
  python stage3/e0.py l0 --task duplicate_string        L0 attempt: the 3-0 A2 exhaustive L0 compile on the oracle
                                                        dependency of the L1 program, then the same checks
  python stage3/e0.py binadd_end                        benchmark-encoded statistic (no format needed)
  python stage3/e0.py report
"""
from __future__ import annotations
import argparse
import itertools
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import torch                     # noqa: E402
import e_tasks as E              # noqa: E402
import l1                        # noqa: E402

OUT = HERE / "results" / "3-E0"
FILES = ["stage3/e0.py", "stage3/e_tasks.py", "stage3/l1.py"]


def install():
    import tasks as T
    import h_adapter as HA
    if getattr(T, "_e_adapter", False):
        return
    HA.install()
    for tok in E.NEW_TOKENS:
        if tok not in T.TOK:
            T.TOK[tok] = len(T.VOCAB)
            T.VOCAB.append(tok)
    # DESIGN 10.1-1 Q1: every op symbol is the one op kind (the L1 '+' kind) and a PF separator, as G-0's '-', '*', '^'
    import pf as PFM
    import c1a
    extra = sorted({tok for t in E.SUITE for tok, kd in E.SYMBOLS[t]["input"].values() if kd == "op"}
                   - {"+", "-", "*", "^"})
    ex_ids = torch.tensor([T.TOK[x] for x in extra])
    h0_classes, h0_candidates, c1a_separators = PFM.token_classes, PFM.candidates, c1a.separators

    def token_classes(tokens, digit_ids, plus_id, eq_id, bar_id, node_lo, node_hi):
        t = torch.where(torch.isin(tokens, ex_ids.to(tokens.device)), torch.full_like(tokens, plus_id), tokens)
        return h0_classes(t, digit_ids, plus_id, eq_id, bar_id, node_lo, node_hi)

    def candidates(tape, t, h, xt, issep):
        return h0_candidates(tape, t, h, xt, issep | torch.isin(tape, ex_ids.to(tape.device)))

    def separators(tokens):
        return c1a_separators(tokens) | torch.isin(tokens, ex_ids.to(tokens.device))
    PFM.token_classes, PFM.candidates, c1a.separators = token_classes, candidates, separators
    T.TASKS = tuple(T.TASKS) + tuple(t for t in E.SUITE if t not in T.TASKS)
    T.SPEC.update({t: E.SPEC[t] for t in E.SUITE})
    inner = T.draw

    def draw(task, rng, lo, hi, train_dist=False):
        if task in E.SUITE:
            return E.draw(task, rng, lo, hi, train_dist=train_dist)
        return inner(task, rng, lo, hi, train_dist=train_dist)
    T.draw = draw
    T._e_adapter = True


def check_kinds(task):
    """the machine's kind of every input token of the task equals e_tasks' kind table (op = the "+" kind)"""
    import tasks as T
    name = {"digit": "digit", "op": "+", "=": "=", "other": "other"}
    toks = E.kind_of_token(task)
    toks = dict([(t, k) for t, k in toks.items() if t != "="] + [("=", toks["="])])    # '=' last: answer phase after it
    ids = torch.tensor([[T.TOK[t] for t in toks]])
    got = l1.kinds_of(ids)[0].tolist()
    return {t: {"e_tasks": k, "machine": l1.KINDS[g], "same": name[k] == l1.KINDS[g]} for (t, k), g in zip(toks.items(), got)}


# ---------------------------------------------------------------- hand programs (l1.PROGRAMS format)
# mu: {head: {(q, kind): move}} (default stay); delta: first-match rules (q, kind of x_t, {head: kind read}, next).
def _mds_program():
    """missing_duplicate_string, Q = 6 (OUTSIDE L1: Q <= 4).  Found by brute force over a 6-state family
    (raw data: mds_search.json).  State = (phase, parity); parity flips every step.
      Z = head 0, Y = head 1.  Hole at p (kind other), |s| = L, partner p + L (p <= L) or p - L (p > L).
      phase 1 (before the hole): Z right on parity 0 (half speed), Y right (full speed); both right at the hole step
      phase 2 (after the hole):  Z left on parity 0 (half speed), Y right (full speed)
      phase 3 (Z back on <bos>, only when p <= L, at about 2p): Y right on parity 0 (half speed)
      The run starts in a phase-3 state; at step 0 Y reads <bos> -> phase 1.
      At '=' (t0) q is phase 2 iff p > L (supply Z = p - L), phase 3 iff p <= L (supply Y = 2p + (2L - 2p)/2 = p + L).
    """
    st = {(3, 0): 0, (3, 1): 1, (1, 0): 2, (1, 1): 3, (2, 0): 4, (2, 1): 5}
    mu = {0: {}, 1: {}}
    for (ph, par), q in st.items():
        if ph == 1:
            if par == 0:
                mu[0][(q, "digit")] = "right"
            mu[1][(q, "digit")] = "right"
            mu[0][(q, "other")] = "right"
            mu[1][(q, "other")] = "right"
        elif ph == 2:
            if par == 0:
                mu[0][(q, "digit")] = "left"
            mu[1][(q, "digit")] = "right"
        else:
            if par == 0:
                mu[0][(q, "digit")] = "left"
                mu[1][(q, "digit")] = "right"
    delta = []
    for (ph, par), q in st.items():
        flip = st[(ph, 1 - par)]
        if ph == 3:
            delta.append((q, "other", {1: "other"}, st[(1, 1 - par)]))
        elif ph == 1:
            delta.append((q, "other", {}, st[(2, 1 - par)]))
        else:
            delta.append((q, "*", {0: "other"}, st[(3, 1 - par)]))
        delta.append((q, "*", {}, flip))
    supply = {q: (0 if ph == 2 else 1) for (ph, par), q in st.items()}
    return {"Q": 6, "mu": mu, "delta": delta, "supply": supply, "outside_l1": "Q = 6 > 4",
            "note": _mds_program.__doc__.strip()}


PROGRAMS = {
    "even_pairs": {
        "Q": 1, "copy_type": False,
        "mu": {0: {(0, "="): "right"}, 1: {(0, "digit"): "right"}},
        "delta": [("*", "*", {}, "same")], "supply": {},
        "note": "class = (number of unequal adjacent pairs) mod 2 = [s_1 != s_n].  Head 0 moves from <bos> to s_1 at "
                "'=', head 1 follows the input (right on every digit) and reads s_n at '='; the class is a function "
                "of the two reads (d).  Not copy type (no correct-read check)."},
    "reverse_string": {
        "Q": 1, "copy_type": True,
        "mu": {0: {(0, "digit"): "right", (0, "answer_phase"): "left"}},
        "delta": [("*", "*", {}, "same")], "supply": {0: 0},
        "note": "the H-0 BOS table: head 0 follows the input, reads s_n at '=', then moves left; it reads <bos> at the "
                "<eos> step"},
    "duplicate_string": {
        "Q": 3, "copy_type": True,
        "mu": {0: {(1, "="): "right", (1, "answer_phase"): "right"},
               1: {(0, "digit"): "right", (1, "="): "right", (1, "answer_phase"): "right"},
               2: {(2, "answer_phase"): "right"}},
        "delta": [(0, "digit", {}, 1), (1, "*", {1: "="}, 2), ("*", "*", {}, "same")],
        "supply": {1: 0, 2: 2},
        "note": "the 3-0 repeat program with <bos>: q = 0 until the first digit (head 1 steps onto s_0 there), q = 1 "
                "copies s with head 0 (from s_0 at '='); head 1 runs one position ahead of head 0 and reads '=' at "
                "answer step n - 1, so q = 2 from step n: head 2 leaves <bos> and copies s again; it reads '=' at "
                "the <eos> step"},
    "missing_duplicate_string": dict(_mds_program(), copy_type=True),
}


def tensors(prog):
    """l1.program_tensors without its Q <= 4 assertion (the Q = 6 program is checked as outside L1)"""
    Q = prog["Q"]
    H = l1.H
    MU = torch.zeros(H, Q, len(l1.KINDS), dtype=torch.long)
    for h, m in prog["mu"].items():
        for (q, k), mv in m.items():
            MU[h, q, l1.KINDS.index(k)] = l1.MOVES.index(mv)
    DEL = torch.full((Q, 7, 7, 7, 7), -1, dtype=torch.long)
    for q in range(Q):
        for kx in range(7):
            for r in itertools.product(range(7), repeat=H):
                for (rq, rk, rr, nxt) in prog["delta"]:
                    if rq != "*" and rq != q:
                        continue
                    if rk != "*" and l1.KINDS.index(rk) != kx:
                        continue
                    if any(l1.KINDS.index(v) != r[h] for h, v in rr.items()):
                        continue
                    DEL[(q, kx) + r] = q if nxt == "same" else nxt
                    break
    assert int(DEL.min()) >= 0 and int(DEL.max()) < Q
    if Q <= 4:
        a, b = l1.program_tensors(prog)
        assert torch.equal(a, MU) and torch.equal(b, DEL)
    return MU, DEL


def a1_checks(task, prog):
    """l1.cmd_a1 with a given program and tensors (copy-type flag for the correct-read check)"""
    import tasks as T
    import run as R
    tens = tensors(prog)
    mv = l1.moving(prog)
    rng = random.Random("e0:causal:%s" % task)
    toks = set(E.kind_of_token(task)) - {"<bos>"}
    toks |= {E.SYMBOLS[task]["output"][v] for v in E.SYMBOLS[task]["output"]}
    pool = sorted({T.TOK[t] for t in toks} | {T.EOS})
    evs = T.eval_sets(task, 2000, 500)
    sets = {}
    for lab, ex in evs.items():
        caus = inv = n_sc = n_ok = 0
        for j in range(0, len(ex), 128):
            chunk = ex[j:j + 128]
            x, y = R.make_batch(chunk)
            P, Qt = l1.l1_paths(x, prog, tens)
            Bt = l1.segment_bits(x, P)
            t0 = l1.first_scored(x)
            x2 = x.clone()
            ts = []
            for b, e in enumerate(chunk):
                n = len(e[0]) + len(e[1])
                caus += bool((P[b, :, :n] <= torch.arange(n)[None, :]).all())
                t = rng.randint(int(t0[b]), n - 1)
                ts.append(t)
                for p in range(t + 1, n):
                    x2[b, p] = rng.choice(pool)
            P2, Q2 = l1.l1_paths(x2, prog, tens)
            B2 = l1.segment_bits(x2, P2)
            for b, t in enumerate(ts):
                inv += (bool((P[b, :, :t + 1] == P2[b, :, :t + 1]).all()) and bool((Bt[b, :, :t + 1] == B2[b, :, :t + 1]).all())
                        and bool((Qt[b, :t + 1] == Q2[b, :t + 1]).all()))
            if prog["copy_type"]:
                for b in range(x.shape[0]):
                    for t in (y[b] != -100).nonzero()[:, 0].tolist():
                        if int(y[b, t]) == T.EOS:
                            continue
                        h = prog["supply"].get(int(Qt[b, t]))
                        n_sc += 1
                        n_ok += h is not None and int(x[b, P[b, h, t]]) == int(y[b, t])
        sets[lab] = {"examples": len(ex), "b_causal_p_le_t": caus / len(ex),
                     "c_prime_invariance_t_ge_t0_positions_bits_q": inv / len(ex)}
        if prog["copy_type"]:
            sets[lab].update({"correct_read_scored_steps_without_eos": n_ok / n_sc, "scored_steps_without_eos": n_sc})
        print(task, lab, sets[lab], flush=True)
    d = l1.d_check(task, lambda x: l1.l1_paths(x, prog, tens), mv, evs, use_q=True)
    print(task, "(d)", json.dumps({k: v for k, v in d.items() if k != "sets"}), flush=True)
    for lab, s in d["sets"].items():
        print("   ", lab, s, flush=True)
    ok = all(s["b_causal_p_le_t"] == 1.0 and s["c_prime_invariance_t_ge_t0_positions_bits_q"] == 1.0
             and s.get("correct_read_scored_steps_without_eos", 1.0) == 1.0 for s in sets.values()) \
        and d["conflicts_0_everywhere"]
    return {"sets": sets, "d": d, "all_checks_1.000_and_d_0": ok, "moving_heads": mv}


def prog_json(prog):
    j = l1.prog_json(prog)
    j["copy_type"] = prog["copy_type"]
    if "outside_l1" in prog:
        j["outside_l1"] = prog["outside_l1"]
    return j


def cmd_a1(a):
    install()
    import h0a
    torch.set_num_threads(1)
    prog = PROGRAMS[a.task]
    res = {"task": a.task, "program": prog_json(prog), "kinds": check_kinds(a.task), "bos": True,
           "format": "<bos> input = output <eos> (DESIGN 9.1)"}
    res.update(a1_checks(a.task, prog))
    res["in_l1"] = bool(res["all_checks_1.000_and_d_0"] and prog["Q"] <= 4)
    res["in_l0"] = bool(res["in_l1"] and prog["Q"] == 1)
    res["env"] = h0a.env(FILES)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("a1_%s.json" % a.task)).write_text(json.dumps(res, indent=1))
    print(a.task, "A1 all:", res["all_checks_1.000_and_d_0"], "Q", prog["Q"], "in L1:", res["in_l1"], "in L0:", res["in_l0"])


def cmd_l0(a):
    """3-0 A2 on the oracle dependency of the L1 hand program (l1.oracle_rows / l0_compile, both variants of the
    <eos> step), then (d) without q on the best L0 table, and the correct read of its best head"""
    install()
    import tasks as T
    import c1a
    import h0a
    import run as R
    torch.set_num_threads(1)
    prog = PROGRAMS[a.task]
    assert prog["Q"] <= 4
    l1.PROGRAMS[a.task] = prog
    exs = T.train_set(a.task, 100000, l1.SEED_DATA_A2)[:2000]
    evs = T.eval_sets(a.task, 2000, 500)
    res = {"task": a.task, "method": "stage3/l1.py cmd_a2 (3-0 A2): oracle dependency = the supply head's read "
                                     "position of the L1 hand program; exhaustive L0 compile, 3 heads, greedy cover",
           "data": "train_set(seed %d)[:2000]" % l1.SEED_DATA_A2, "variants": {}}
    for with_eos in (False, True):
        rows = l1.oracle_rows(a.task, exs, prog, with_eos)
        table, per, cover, info = l1.l0_compile(exs, rows)
        mv = c1a.moving(table)
        d = l1.d_check(a.task, lambda x: (c1a.read_paths(x, table), torch.zeros(x.shape[0], x.shape[1], dtype=torch.long)),
                       mv, evs, use_q=False)
        best_read = {}
        for lab, ex in evs.items():
            ok = n = 0
            for j in range(0, len(ex), 128):
                x, y = R.make_batch(ex[j:j + 128])
                P = c1a.read_paths(x, table)
                for b in range(x.shape[0]):
                    for t in (y[b] != -100).nonzero()[:, 0].tolist():
                        if int(y[b, t]) == T.EOS:
                            continue
                        n += 1
                        ok += any(int(x[b, P[b, h, t]]) == int(y[b, t]) for h in range(l1.H))
            best_read[lab] = ok / n
        lab = "with_eos_step" if with_eos else "without_eos_step"
        res["variants"][lab] = {"output_steps": len(rows), "best_l0_table": table, "per_head": per,
                                "coverage": cover, "moving_heads": mv, "d_without_q": d,
                                "any_head_reads_target_scored_without_eos": best_read,
                                "l0_outside": bool(cover < 0.99 or not d["conflicts_0_everywhere"]),
                                "why": {"coverage_lt_0.99": bool(cover < 0.99),
                                        "d_conflict_gt_0": not d["conflicts_0_everywhere"]}, **info}
        print(a.task, lab, "coverage %.4f" % cover, "d conflicts any:", not d["conflicts_0_everywhere"], "table",
              table, "any-head read", best_read, flush=True)
    v = [x["l0_outside"] for x in res["variants"].values()]
    res["l0_outside"] = v[0] if v[0] == v[1] else None
    res["env"] = h0a.env(FILES)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("l0_%s.json" % a.task)).write_text(json.dumps(res, indent=1))
    print(a.task, "L0 outside:", res["l0_outside"])


def cmd_binadd_end(a):
    """binary_addition (benchmark encoding, no format): how often the end of the sum is NOT given by the operand
    lengths and the final carry (the 'natural' end = max(|n|, |m|) + carry out), per bin; the same seeds as the eval
    sets ('eval:binary_addition:...') and the training set (seed 30, 100,000)"""
    import h0a
    task = "binary_addition"
    out = {"task": task, "rule": "natural end = max(|n|, |m|) + carry out of the top position (operands zero-padded "
                                 "to the longer length); actual end = len(sum without leading zeros) (benchmark)",
           "sets": {}}
    sets = {"train_seed30": (random.Random("train:%s:%d" % (task, 30)), (1, 10), 100000),
            "id_1-10": (random.Random("eval:%s:id" % task), (1, 10), 2000)}
    for lo, hi in E.SPEC[task]["ood"]:
        sets["ood_%d-%d" % (lo, hi)] = (random.Random("eval:%s:%d-%d" % (task, lo, hi)), (lo, hi), 500)
    for lab, (rng, (lo, hi), size) in sets.items():
        shorter = two = 0
        ex = []
        for _ in range(size):
            inp, outp, n = E.raw_draw(task, rng, lo, hi)
            res_len = outp.index(2)                                   # the termination token
            if 2 in inp:
                k = inp.index(2)
                a_, b_ = inp[:k], inp[k + 1:]
                two += 1
                L = max(len(a_), len(b_))
                va = sum(v << i for i, v in enumerate(a_))
                vb = sum(v << i for i, v in enumerate(b_))
                natural = L + (1 if va + vb >= (1 << L) else 0)
            else:
                natural = len(inp)                                    # n <= 2: one number of n digits
            if res_len < natural:
                shorter += 1
                if len(ex) < 3:
                    ex.append({"input": inp, "output": outp, "sum_len": res_len, "natural_end": natural})
        out["sets"][lab] = {"examples": size, "with_two_operands": two, "sum_shorter_than_natural_end": shorter,
                            "fraction": shorter / size, "examples_shorter": ex}
        print(lab, out["sets"][lab]["fraction"], flush=True)
    out["env"] = h0a.env(FILES)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "binadd_end.json").write_text(json.dumps(out, indent=1))


# ---------------------------------------------------------------- report: the 15-row table
CAUSES = ("값 상태", "한 step 두 칸 이상", "출력당 읽기 증가", "값 조건 제어", "그 밖")
KEY = ("출력 step의 키는 x_t, x_{t-1}과 헤드 셋의 두 step 읽기(토큰 6개)와 q뿐이고, q는 종류로만 바뀐다(값을 보지 않는다). "
       "content를 쓰지 않으면 읽는 위치도 값과 무관하므로, 읽지 않는 자리 하나를 바꿔 답만 바뀌는 두 입력이 생긴다(n ≥ 7). "
       "content 이동(현재 토큰과 같은 값의 다음 칸으로 건너뜀)은 위치를 값에 따라 바꾸지만, 그 경로가 답을 위치로 담을 "
       "가능성까지 배제한 증명은 아니다.")
ROWS = [
    ("even_pairs", "분류", None, "클래스 = [s_1 != s_n] (인접 불일치 쌍 수의 홀짝). L0 손 프로그램(Q = 1)이 (b)·(c′) 1.000, "
                             "(d) 충돌 0이다."),
    ("parity_check", "분류", "값 상태", "클래스 = 1의 개수 mod 2로, 모든 입력 값에 달린다. 입력은 모두 digit 종류다. " + KEY),
    ("modular_arithmetic", "분류", "값 상태", "답 = 식의 값 mod 5(곱셈 먼저)로, 모든 항의 값에 달린다. 연산 기호는 op 종류라 q가 "
                                       "구조는 볼 수 있지만 누적값(0–4)은 담지 못한다. " + KEY),
    ("cycle_navigation", "분류", "값 상태", "답 = Σ(a − 1) mod 5. 행동 기호를 digit로 보면 값 상태다(위 논증). 기호마다 다른 op "
                                     "종류로 보면 상태 5개(원 위의 위치)가 필요해 Q ≤ 4를 넘는다(Q2 답에 따라 분류가 '그 밖: Q 한도'로 "
                                     "바뀐다. 표현 밖이라는 결론은 같다)."),
    ("modular_arithmetic_brackets", "분류", "값 상태", "답 = 괄호 식의 값 mod 5로, 부분식 값을 중첩 깊이만큼 들고 있어야 한다. "
                                                "값은 q에 들어가지 않는다. " + KEY),
    ("reverse_string", "열", None, "H-0 BOS 표와 같다(Q = 1): 헤드가 입력을 따라가 '='에서 s_n을 읽고 왼쪽으로 간다. "
                                  "<eos> step에서 <bos>를 읽는다."),
    ("solve_equation", "분류", "값 상태", "x = (우변 − 나머지 부분식의 값)을 풀어야 하므로, 괄호 식 전체의 값에 달린다. " + KEY),
    ("stack_manipulation", "열", "한 step 두 칸 이상",
     "k번째 출력은 위에서 k번째로 남은 원소다. 그 사이에 POP으로 지워진 원소가 길이에 따라 늘어나는 만큼 있어서, 출력 한 step에 "
     "건너뛸 칸 수에 상한이 없다(POP 수를 세는 일도 필요하다). 이것은 명령 기호가 종류로 구분될 때의 원인이다. "
     "Q1 답이 'op 하나'이면 POP·PUSH0·PUSH1이 같은 종류라 상태·이동이 명령을 구분하지 못하므로 '값 조건 제어'다."),
    ("binary_addition", "열", "그 밖",
     "끝 시점이 아직 읽지 않은 값에 달린다(G-0a 뺄셈과 같은 유형). 피연산자는 앞자리 0을 포함한 고정 길이로 쓰고(zfill), 합은 "
     "앞자리 0 없이 쓴다. 그래서 k자리 뒤에서 끝낼지가 '두 수의 남은 윗자리가 모두 0이고 올림이 없는가'에 달리는데, 남은 자리 수는 "
     "길이에 따라 늘어난다. 자리 값과 올림은 x_t와 앞 step 읽기로 국소적으로 정해진다(1단계 덧셈과 같다). Q4(끝 토큰·채움)를 "
     "어느 쪽으로 정해도 끝 토큰의 위치가 같은 문제다."),
    ("binary_multiplication", "열", "출력당 읽기 증가", "곱의 k번째 자리는 Σ_i a_i b_{k−i}와 올림으로, k + 1쌍을 읽어야 한다. "
                                                  "(끝 시점 문제도 덧셈과 같이 있다.)"),
    ("compute_sqrt", "열", "출력당 읽기 증가", "floor(√x)의 i번째 비트(윗자리부터)는 입력 윗자리 2i + 2개 전체(나머지 x_top − y²)에 "
                                         "달린다. 출력 step마다 읽어야 할 자리가 늘어난다."),
    ("duplicate_string", "열", None, "3-0 repeat 프로그램에 <bos>를 넣은 판(Q = 3)이다. L0는 3-0 A2 방식(전수 L0 컴파일)으로 시도했다."),
    ("missing_duplicate_string", "분류", "그 밖",
     "상태 수 한도다. 답은 구멍 p의 짝 위치(p + L 또는 p − L, L = n/2)의 토큰이다. 실시간으로 그 위치에 헤드를 두는 6상태 프로그램이 "
     "A1을 모두 통과한다(Q = 6 > 4). 4상태로는 찾지 못했다. 논증(속도 분해): 2L은 입력 끝에만 나타나므로 마지막 구간의 속도가 "
     "±1/2여야 하고(번갈이 상태 2개), p > L이면 공급 헤드가 p 앞뒤로 +1/2·−1/2(서로 다른 번갈이 쌍 2개), p ≤ L이면 다른 헤드가 "
     "2p까지 전속 뒤 1/2(세 번째 쌍)이어야 한다. 그래서 2 + 2 + 2 = 6개다. 다른 길(보이는 1의 개수 홀짝)은 값 상태다."),
    ("odds_first", "열", "한 step 두 칸 이상", "출력 k는 s[2k+1](뒤 절반은 s[2k])라 읽을 위치가 출력마다 2칸씩 나아간다. 헤드는 step당 "
                                         "한 칸이라 한 헤드의 경로는 기울기 2인 목표 경로를 되돌아가지 않는 한 한 번만 만나고, 헤드 "
                                         "셋으로는 출력 몇 개만 공급한다(입력에 구분자가 없어 next_sep도 쓸 수 없다)."),
    ("bucket_sort", "열", "값 조건 제어", "출력은 값 v를 개수(v)번 쓰는 것이다. 다음 출력이 v인지 다음 값인지는 남은 v가 있는가와 "
                                      "다음에 있는 값이 무엇인가(값에 따른 횟수)에 달린다. 모든 값이 digit 종류라 q와 이동은 값을 보지 "
                                      "않는다. content 이동으로 '같은 값이 더 있는가'는 일부 볼 수 있지만, 다음 값 u를 고를 수는 없다."),
]
assert [r[0] for r in ROWS] and set(r[0] for r in ROWS) == set(E.SUITE) and all(r[2] in CAUSES + (None,) for r in ROWS)


def cmd_kinds(a):
    """the kind check of every task whose format is fixed (results/3-E0/kinds.json).  The a1_<task>.json "kinds"
    field of the first runs put '=' first in the probe, so every later token read as answer_phase there (a bug of the
    probe only: the checks use the real tapes)"""
    install()
    out = {t: check_kinds(t) for t in E.SUITE if not E.SYMBOLS[t]["pending"]}
    out = {"tasks": out, "all_same": all(v["same"] for k in out.values() for v in k.values()),
           "format_answers": E.ANSWERS}
    name = "kinds.json" if not (OUT / "kinds.json").exists() else "kinds_10.1.json"     # rule 5: keep the first file
    (OUT / name).write_text(json.dumps(out, indent=1))
    print("written", name)
    print("all same:", out["all_same"])


def cmd_report(a):
    import h0a
    rows = []
    l1n = l0n = 0
    for task, otype, cause, why in ROWS:
        r = {"task": task, "level": E.LEVEL[task], "output_type": otype, "cause": cause, "argument": why,
             "format_pending": E.SYMBOLS[task]["pending"]}
        f = OUT / ("a1_%s.json" % task)
        if f.exists():
            j = json.loads(f.read_text())
            r.update({"Q": j["program"]["Q"], "a1_all": j["all_checks_1.000_and_d_0"], "in_l1": j["in_l1"],
                      "in_l0": j["in_l0"]})
        else:
            r.update({"Q": None, "in_l1": False, "in_l0": False})
        if task == "duplicate_string":
            j = json.loads((OUT / "l0_duplicate_string.json").read_text())
            r["in_l0"] = not j["l0_outside"]
            r["l0_attempt"] = {k: {"coverage": v["coverage"], "d_conflict": not v["d_without_q"]["conflicts_0_everywhere"]}
                               for k, v in j["variants"].items()}
        if task == "binary_addition":
            j = json.loads((OUT / "binadd_end.json").read_text())
            r["sum_shorter_than_natural_end"] = {k: v["fraction"] for k, v in j["sets"].items()}
        l1n += bool(r["in_l1"])
        l0n += bool(r["in_l0"])
        rows.append(r)
    out = {"design": "stage3/DESIGN.md 9.1", "source": E.SOURCE, "rows": rows, "in_l1": l1n, "in_l0": l0n,
           "causes": {c: [r["task"] for r in rows if r["cause"] == c] for c in CAUSES},
           "questions": E.QUESTIONS,
           "replay": json.loads((OUT / "replay.json").read_text()), "env": h0a.env(FILES)}
    (OUT / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for r in rows:
        print("%-28s %-3s L0 %-5s L1 %-5s Q %-4s %s" % (r["task"], r["output_type"], r["in_l0"], r["in_l1"], r["Q"], r["cause"]))
    print("L1:", l1n, "L0:", l0n)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("a1", "l0"):
        p = sub.add_parser(c)
        p.add_argument("--task", required=True, choices=sorted(PROGRAMS))
    sub.add_parser("binadd_end")
    sub.add_parser("report")
    sub.add_parser("kinds")
    a = ap.parse_args()
    {"a1": cmd_a1, "l0": cmd_l0, "binadd_end": cmd_binadd_end, "report": cmd_report, "kinds": cmd_kinds}[a.cmd](a)


if __name__ == "__main__":
    main()
