"""3-E0: brute force over a 6-state program family for missing_duplicate_string (pure python simulation of the L1
moves stay / right / left: right clamped to t, left clamped to 0; transitions on the kind read, as stage3/l1.py).
Only head positions matter (the target is the token at the partner position), so every n in 1..40 and every hole
position p is checked, values are not needed.  State = (phase 1/2/3, parity); parity flips every step; the run starts
in (phase 3, parity 0).  Z, Y = heads 0, 1.  Family (variants enumerated in this order, the first one that is exact
everywhere is written to OUT_JSON):
  Z: phase 1 right on parity zr, phases 2-3 left on parity zl;  Y: phases 1-2 right, phase 3 right on parity yr;
  moves at '=' (eqZ, eqY) and at kind-other steps per phase (oZ1, oY1: the hole; oZ2, oY2, oZ3, oY3: the pad);
  supply: phase 1 -> s1 (n = 1 only), phase 2 -> Z, phase 3 -> Y.
  python stage3/e0_mds_search.py OUT_JSON
"""
import itertools, json, sys
MV = {"s": 0, "r": 1, "l": -1}
def run(n, p, v):
    # tape kinds: 0 BOS(other), 1..n input (hole at p: other; pad at n if odd: other), n+1 '='
    L = n // 2
    kind = ["other"] + ["digit"] * n + ["="]
    if n == 1:
        p = None
    else:
        kind[p] = "other"
        if n % 2: kind[n] = "other"
    ph, par = 3, 0                       # initial state (ph3, par0)
    Z = Y = 0
    for t in range(n + 2):
        k = kind[t]
        # moves
        if k == "=":
            mz, my = v["eqZ"][ph], v["eqY"][ph]
        elif k == "other" and t > 0:
            mz, my = v["oZ"][ph], v["oY"][ph]
        else:
            mz = v["Z"][(ph, par)]; my = v["Y"][(ph, par)]
        if t == 0: mz = my = "s"
        Z = min(max(Z + MV[mz], 0), t); Y = min(max(Y + MV[my], 0), t)
        if t == n + 1:
            return ph, Z, Y
        # transition
        if ph == 3 and k == "other" and kind[Y] == "other":        # step 0 only (Y reads BOS)
            nph = 1
        elif ph == 1 and k == "other":
            nph = 2
        elif ph == 2 and kind[Z] == "other":                        # Z reads BOS
            nph = 3
        else:
            nph = ph
        par = 1 - par if t > 0 else v["par0"]
        ph = nph
def ok(v):
    for n in range(1, 41):
        L = n // 2
        holes = [None] if n == 1 else range(1, 2 * L + 1)
        for p in holes:
            ph, Z, Y = run(n, p if p else 1, v)
            want = 1 if n == 1 else (p + L if p <= L else p - L)
            got = {"Z": Z, "Y": Y}[v["sup"][ph]]
            if got != want:
                return False
    return True
found, tried = [], 0
for zr, zl, yr, par0, s1 in itertools.product((0, 1), (0, 1), (0, 1), (0, 1), "ZY"):
    for eqZ, eqY, oZ2, oY2, oZ3, oY3, oZ1, oY1 in itertools.product("srl", repeat=8):
        v = {"Z": {(1, zr): "r", (1, 1 - zr): "s", (2, zl): "l", (2, 1 - zl): "s", (3, zl): "l", (3, 1 - zl): "s"},
             "Y": {(1, 0): "r", (1, 1): "r", (2, 0): "r", (2, 1): "r", (3, yr): "r", (3, 1 - yr): "s"},
             "eqZ": {1: eqZ, 2: eqZ, 3: eqZ}, "eqY": {1: eqY, 2: eqY, 3: eqY},
             "oZ": {1: oZ1, 2: oZ2, 3: oZ3}, "oY": {1: oY1, 2: oY2, 3: oY3},
             "par0": par0, "sup": {1: s1, 2: "Z", 3: "Y"}}
        tried += 1
        if ok(v):
            found.append({"zr": zr, "zl": zl, "yr": yr, "par0": par0, "s1": s1, "eqZ": eqZ, "eqY": eqY,
                          "oZ1": oZ1, "oY1": oY1, "oZ2": oZ2, "oY2": oY2, "oZ3": oZ3, "oY3": oY3})
            print("FOUND after", tried, found[-1], flush=True)
            json.dump({"family": __doc__, "variants_tried_until_first": tried, "first_exact": found[-1],
                       "checked": "n = 1..40, every hole position"}, open(sys.argv[1], "w"), indent=1)
            sys.exit()
print("none found after", tried)
