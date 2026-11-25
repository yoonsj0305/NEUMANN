"""Stage 2-0a (stage2/DESIGN.md section 3): expressivity pre-check -- no search, no change to k_ext.py or s2_0.py,
no 2-0 rerun.

Hand-written correct machines (z0, U, V, C) for the seed-7 tables (parity: all stay; addition: the compiled table),
in k_ext's own machine form: h_0 = z0, h' = U(h, x), emit V(h, h', x) when C(h, h', x); U is an expression tree of
the factored core's operators (add, sub, min, max, mod by a constant; "c" leaves and mod divisors are constant holes),
V = term + constant, C = (term > / < / == constant) or true.  They are run with k_ext.run_factored on the 2-0
observations, code and scoring (stage2/s2_0.py to_io: answer digits and <eos>), first on the 200 training sequences
of 2-0, then on the existing evaluation sets (in-distribution and every out-of-distribution bin).

The grammar limits are measured on the machines (operators, depth, constant holes, mod divisors, constant range,
value range), and for each limit the number of candidate structures the factored core would enumerate is counted
with k_ext.skeletons / k_ext._hole_free_terms at the current limit and at the limit that admits the hand machine.

Reference only (the 2-0 format is not changed): the parity machine for one written format change (no <eos> in the
output pieces) is also executed, to check the written claim.

  python stage2/s2_0a.py
"""
from __future__ import annotations
import json
import math
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_0 as Z           # noqa: E402  (2-0's observation, code and scoring; unchanged)
import k_ext as K          # noqa: E402

T = Z.T
OUT = HERE / "results" / "s2_0a"


# ------------------------------------------------------------------ expression trees in k_ext's form
def v(i):
    return (("v", i), [])


def c(k):
    return (("c",), [k])


def _b(op, a, b):
    return ((op, a[0], b[0]), a[1] + b[1])


def add(a, b):
    return _b("add", a, b)


def sub(a, b):
    return _b("sub", a, b)


def mn(a, b):
    return _b("min", a, b)


def mx(a, b):
    return _b("max", a, b)


def mod(a, d):
    return (("mod", a[0]), a[1] + [d])


def band(x, off, d):
    """d * [x + off >= d] for 0 <= x + off < 2d: (x + off) - mod(x + off, d)"""
    t = add(x, c(off))
    return sub(t, mod(t, d))


def parity_machine():
    """inputs: (current token); U vars $0 = h, $1 = x; V, C vars $0 = h, $1 = h', $2 = x.
    bits: h' = (h + x) mod 2 (the parity so far); '=' (13): emit h (the parity), h' = 11; the parity digit step:
    emit h = 11 (<eos>).  Silent on bits: max(h, x) <= 1."""
    U = mx(mod(add(v(0), v(1)), 2), sub(v(1), c(2)))
    V = v(0)
    C = mx(v(0), v(2))
    return {"z0": 0, "U": U, "V": (V, 0), "C": ("cgt", C, 10)}


def addition_machine():
    """inputs: (current token, head 0 read = a_k, head 1 read = b_k, head 2 read = current position); U vars
    $0 = h, $1 = cur, $2 = ra, $3 = rb, $4 = rc; V, C vars $0 = h, $1 = h', $2.. the inputs.
    latent h = sf + 32 A + 64 B:  sf = 31 in the prompt (marker), else the step sum s = a_k + b_k + carry (0..19), or
    21 at the <eos> step;  A = 1 once head 0 has read a non-digit in the answer phase ('+', a exhausted);  B = 1 once
    head 1 has read '=' (b exhausted).  Exhausted reads are masked (x - min(x, mask)); carry_in = [10 <= sf <= 19];
    the prompt keeps sf = 31 until '='; <eos> when A, B and s = 0.  Emit when sf' < 22; value = sf' mod 10, or 11
    for sf' = 21."""
    h, cur, ra, rb = v(0), v(1), v(2), v(3)
    sf = mod(h, 32)
    A32 = sub(mod(h, 64), mod(h, 32))
    B64 = sub(h, mod(h, 64))
    A32n = mx(A32, band(ra, 20, 32))                  # 32 [ra >= 12]
    B64n = mx(B64, band(rb, 51, 64))                  # 64 [rb == 13]
    da = sub(ra, mn(ra, A32n))
    db = sub(rb, mn(rb, B64n))
    z = mod(add(sf, c(12)), 32)
    cin = mx(c(0), mn(c(1), sub(z, c(21))))           # [10 <= sf <= 19]
    s = add(add(da, db), cin)
    W = mn(sub(sf, c(19)), sub(c(13), cur))          # >= 1 exactly in the prompt (sf = 31, cur != '=')
    sg = mx(s, band(W, 30, 31))                       # 31 in the prompt
    y = sub(add(A32n, B64n), c(75))                   # 21 when both exhausted
    eosv = mx(c(0), sub(y, band(s, 20, 21)))          # 21 when both exhausted and s = 0
    U = add(add(mx(sg, eosv), A32n), B64n)
    sfp = mod(v(1), 32)
    tens = mx(c(0), sub(sub(sfp, c(10)), mod(sub(sfp, c(10)), 10)))
    V = add(mod(sfp, 10), tens)
    C = mod(v(1), 32)
    return {"z0": 31, "U": U, "V": (V, 0), "C": ("clt", C, 22)}


def parity_machine_no_eos():
    """reference (format change F1: no <eos> in the output pieces): h' = (h + x) mod 2, emit h when x == '='"""
    return {"z0": 0, "U": mod(add(v(0), v(1)), 2), "V": (v(0), 0), "C": ("ceq", v(2), 13)}


def as_k(m):
    """the machine in k_ext.run_factored's dict form (terms = [V term, C term])"""
    (Vt, Vc), (ck, Ct, cc) = m["V"], m["C"]
    return {"U": m["U"][0], "ucs": tuple(m["U"][1]), "z0": m["z0"],
            "terms": [(Vt[0], tuple(Vt[1])), (Ct[0], tuple(Ct[1]))], "rule": ((ck, 1, cc), (0, Vc))}


def show(m):
    (Vt, Vc), (ck, Ct, cc) = m["V"], m["C"]
    return {"z0": m["z0"], "U": K.show_t(*m["U"]),
            "V": K.show_t(*Vt) + ("" if Vc == 0 else " + %d" % Vc),
            "C": "(%s %s %d)" % ({"cgt": ">", "clt": "<", "ceq": "=="}[ck], K.show_t(*Ct), cc)}


# ------------------------------------------------------------------ measurements
def ops(t):
    return 0 if t[0] in ("v", "c") else 1 + sum(ops(s) for s in t[1:] if isinstance(s, tuple))


def depth(t):
    return 0 if t[0] in ("v", "c") else 1 + max(depth(s) for s in t[1:] if isinstance(s, tuple))


def holes_split(t, cs):
    """(constant leaves, mod divisors) with their values"""
    it = iter(cs)
    leaves, divs = [], []

    def walk(t):
        if t[0] == "c":
            leaves.append(next(it))
        elif t[0] == "mod":
            walk(t[1])
            divs.append(next(it))
        elif t[0] != "v":
            walk(t[1])
            walk(t[2])
    walk(t)
    return leaves, divs


def ev_track(t, args, consts, acc):
    """k_ext.evaluate's semantics, recording the largest |value| of every node"""
    it = iter(consts)

    def ev(t):
        k = t[0]
        if k == "v":
            r = args[t[1]]
        elif k == "c":
            r = next(it)
        elif k == "mod":
            a = ev(t[1])
            r = a % next(it)
        else:
            a, b = ev(t[1]), ev(t[2])
            r = a + b if k == "add" else a - b if k == "sub" else min(a, b) if k == "min" else max(a, b)
        acc[0] = max(acc[0], abs(r))
        return r
    return ev(t)


def value_range(m, xs):
    acc, lat = [0], 0
    (Vt, _), (_, Ct, _) = m["V"], m["C"]
    for x in xs:
        h = m["z0"]
        for e in x:
            h2 = ev_track(m["U"][0], (h,) + e, m["U"][1], acc)
            ev_track(Vt[0], (h, h2) + e, Vt[1], acc)
            ev_track(Ct[0], (h, h2) + e, Ct[1], acc)
            lat = max(lat, abs(h2))
            h = h2
    return lat, acc[0]


def u_structures(nv, max_ops, max_holes, cache={}):
    """candidate update structures of the factored core (factored_synthesis's filter): canonical skeletons over nv
    variables with <= max_ops operators and <= max_holes constant holes, not a bare constant, not h itself"""
    key = (nv, max_ops)
    if key not in cache:
        cache[key] = K.skeletons(nv, max_ops)
    sk = cache[key]
    n = 0
    for k in range(max_ops + 1):
        for U in sk[k]:
            if U[0] == "c" or U == ("v", 0) or K.holes(U) > max_holes:
                continue
            n += 1
    return n


def per_op_counts(nv, upto, max_holes):
    sk = K.skeletons(nv, upto)
    return [sum(1 for U in sk[k] if not (U[0] == "c" or U == ("v", 0) or K.holes(U) > max_holes))
            for k in range(upto + 1)]


def u_cost(m):
    """the factored core's description length of a machine's update: OP_BITS per operator + HOLE_BITS per hole +
    cbits of every hole value and of z0 (factored_synthesis's order)"""
    t, cs = m["U"]
    return K.OP_BITS * ops(t) + K.HOLE_BITS * len(cs) + sum(K.cbits(v) for v in cs) + K.cbits(m["z0"])


def candidates_up_to(nv, max_ops, max_holes, budget, crange=range(-20, 41), z0range=range(-20, 41)):
    """number of (update structure, hole values, z0) candidates with description length <= budget (each is one
    latent trace of factored_synthesis before equivalence skipping) -- the work before a machine of that length"""
    from collections import Counter
    dist = {"c": Counter(K.cbits(v) for v in crange), "d": Counter(K.cbits(v) for v in range(2, 11)),
            "z": Counter(K.cbits(v) for v in z0range)}
    memo = {}

    def combos_le(kinds, b):
        key = (kinds, b)
        if key not in memo:
            cur = Counter({0: 1})
            for kd in list(kinds) + ["z"]:
                nxt = Counter()
                for c0, n0 in cur.items():
                    for c1, n1 in dist[kd].items():
                        if c0 + c1 <= b:
                            nxt[c0 + c1] += n0 * n1
                cur = nxt
            memo[key] = sum(cur.values())
        return memo[key]
    sk = K.skeletons(nv, max_ops)
    total = 0
    for k in range(max_ops + 1):
        for U in sk[k]:
            if U[0] == "c" or U == ("v", 0) or K.holes(U) > max_holes:
                continue
            kinds = K._hole_kinds(U)
            b = budget - (K.OP_BITS * k + K.HOLE_BITS * len(kinds))
            if b >= 0:
                total += combos_le(kinds, b)
    return total


def evaluate_machine(m, task, policy, strip_eos=False):
    km = as_k(m)
    exs_train = T.train_set(task, 100000, 7)[:Z.N_SEQ]
    res = {}
    xs_all = []
    for label, exs in [("training_200 (2-0 observations)", exs_train)] + list(T.eval_sets(task, 1000, 500).items()):
        ok = 0
        for e in exs:
            xs, ys, _ = Z.to_io(e, policy)
            if strip_eos:
                ys = ys[:-1]
            ok += K.run_factored(km, xs) == ys
            xs_all.append(xs)
        res[label] = ok / len(exs)
    return res, xs_all


def measure(m):
    out = {}
    for part, (t, cs) in (("U", m["U"]), ("V", m["V"][0]), ("C", m["C"][1])):
        leaves, divs = holes_split(t, cs)
        out[part] = {"operators": ops(t), "depth": depth(t), "constant_holes": len(leaves) + len(divs),
                     "constant_leaves": leaves, "mod_divisors": divs,
                     "operator_set": sorted(set(_opset(t)))}
    out["V"]["additive_constant"] = m["V"][1]
    out["C"]["comparison"], out["C"]["comparison_constant"] = m["C"][0], m["C"][2]
    return out


def _opset(t):
    if t[0] in ("v", "c"):
        return []
    return [t[0]] + sum((_opset(s) for s in t[1:] if isinstance(s, tuple)), [])


def main():
    t0 = time.process_time()
    OUT.mkdir(parents=True, exist_ok=True)
    cs = Z.cases()
    jobs = {"parity_s7": (parity_machine(), cs["parity_s7"]), "addition_s7": (addition_machine(), cs["addition_s7"])}
    res = {"cases": {}, "reference_format_F1_parity_no_eos": None}
    for name, (m, case) in jobs.items():
        acc, xs_all = evaluate_machine(m, case["task"], case["policy"])
        lat, val = value_range(m, xs_all)
        res["cases"][name] = {"table": case["table"], "policy": case["policy"], "n_in": 1 + len(Z.moving(case["policy"])),
                              "machine": show(m), "measures": measure(m), "accuracy": acc,
                              "max_abs_latent": lat, "max_abs_any_node_value": val,
                              "tree": {"U": m["U"], "V": m["V"], "C": m["C"]}}
    mF1 = parity_machine_no_eos()
    accF1, xsF1 = evaluate_machine(mF1, "parity", cs["parity_s7"]["policy"], strip_eos=True)
    res["reference_format_F1_parity_no_eos"] = {"change": "output pieces without <eos> (answer digit only)",
                                               "machine": show(mF1), "measures": measure(mF1), "accuracy": accF1}
    # candidate-structure counts (factored core filter) at the current and relaxed limits
    cnt = {}
    cnt["parity_U_nv2"] = {"current_ops2_holes1": u_structures(2, 2, 1), "ops4_holes1": u_structures(2, 4, 1),
                           "ops2_holes2": u_structures(2, 2, 2), "ops4_holes2": u_structures(2, 4, 2),
                           "per_operator_count_holes2": per_op_counts(2, 4, 2)}
    cnt["addition_U_nv5"] = {"current_ops2_holes1": u_structures(5, 2, 1),
                             "per_operator_count_holes1": per_op_counts(5, 3, 1),
                             "per_operator_count_holes3": per_op_counts(5, 3, 3)}
    cnt["output_terms"] = {"nv3_ops1 (parity V/C, current)": len(K._hole_free_terms(3, 1)),
                           "nv6_ops1 (addition V/C, current)": len(K._hole_free_terms(6, 1)),
                           "nv6_ops2": len(K._hole_free_terms(6, 2))}
    res["structure_counts"] = cnt
    # work before the hand machine in the factored core's order (2-0 parity seed 7 measured 560,224 traces in
    # 27.67 CPU s on 12 sequences); [estimate]
    pm, fm = parity_machine(), parity_machine_no_eos()
    rate = 560224 / 27.67
    est = {"trace_rate_per_cpu_s_measured_in_2_0_parity_s7": round(rate),
           "parity_hand_U_description_length": u_cost(pm),
           "parity_candidates_up_to_hand_length_relaxed_ops4_holes2": candidates_up_to(2, 4, 2, u_cost(pm)),
           "parity_F1_hand_U_description_length": u_cost(fm),
           "parity_F1_candidates_up_to_hand_length_current_grammar": candidates_up_to(2, 2, 1, u_cost(fm)),
           "addition_hand_U_description_length": u_cost(addition_machine())}
    est["parity_estimated_cpu_s_relaxed"] = round(est["parity_candidates_up_to_hand_length_relaxed_ops4_holes2"] / rate, 1)
    est["parity_F1_estimated_cpu_s_current"] = round(est["parity_F1_candidates_up_to_hand_length_current_grammar"] / rate, 2)
    res["search_work_estimate"] = est
    res["cpu_s"] = round(time.process_time() - t0, 1)
    (OUT / "final.json").write_text(json.dumps(res, indent=1, default=list))
    (OUT / "env.json").write_text(json.dumps(Z.env(), indent=1))
    (OUT / "config.json").write_text(json.dumps({
        "design": "stage2/DESIGN.md section 3 (2-0a)", "observations": "stage2/s2_0.py to_io (2-0 code and scoring)",
        "run": "k_ext.run_factored", "training_sequences": "T.train_set(task, 100000, 7)[:200]",
        "evaluation": "T.eval_sets(task, 1000, 500)", "no_search": True,
        "grammar_limits_measured": ["U operators/depth/holes", "V operators", "C operators", "operator set",
                                    "value range (8-bit / latent +-200)", "constant range (-20..40, z0 -20..40, mod 2..10)"]},
        indent=1))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("tree", "policy")} for k, v in res["cases"].items()},
                     indent=1, default=list))
    print(json.dumps(res["reference_format_F1_parity_no_eos"], indent=1, default=list))
    print(json.dumps(cnt, indent=1))
    print(json.dumps(res["search_work_estimate"], indent=1))
    print("cpu", res["cpu_s"])


if __name__ == "__main__":
    main()
