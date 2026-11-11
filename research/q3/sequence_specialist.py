"""Classical integer-sequence specialist (strong cheap baseline, frozen).

predict(train_terms, k) -> next k terms or None (abstain).
1. polynomial: lowest-order finite difference that vanishes on >= 3 entries;
2. C-finite: minimal linear recurrence with rational coefficients
   (Berlekamp-Massey over Fractions) of order <= 6 that is over-determined
   by at least 2 extra train equations and yields integer continuations.
No NEUMANN component is used.
"""
from __future__ import annotations
from fractions import Fraction


def _poly(a, k):
    rows = [list(a)]
    while len(rows[-1]) > 3 and any(rows[-1]):
        r = rows[-1]
        rows.append([r[i + 1] - r[i] for i in range(len(r) - 1)])
    if any(rows[-1]) or len(rows[-1]) < 3:
        return None
    out = []
    for _ in range(k):
        rows[-1].append(0)
        for d in range(len(rows) - 2, -1, -1):
            rows[d].append(rows[d][-1] + rows[d + 1][-1])
        out.append(rows[0][-1])
    return out


def _berlekamp_massey(s):
    c, b = [Fraction(1)], [Fraction(1)]
    l, m, bb = 0, 1, Fraction(1)
    for n in range(len(s)):
        d = s[n] + sum(c[i] * s[n - i] for i in range(1, l + 1))
        if d == 0:
            m += 1
            continue
        t = c[:]
        coef = d / bb
        c = c + [Fraction(0)] * (len(b) + m - len(c))
        for i, v in enumerate(b):
            c[i + m] -= coef * v
        if 2 * l <= n:
            l, b, bb, m = n + 1 - l, t, d, 1
        else:
            m += 1
    return c[:l + 1], l


def _cfinite(a, k, max_order=6):
    s = [Fraction(v) for v in a]
    c, l = _berlekamp_massey(s)
    if l == 0 or l > max_order or 2 * l + 2 > len(a):
        return None
    out = list(s)
    for _ in range(k):
        out.append(-sum(c[i] * out[-i] for i in range(1, l + 1)))
    tail = out[len(a):]
    if any(v.denominator != 1 for v in tail):
        return None
    return [int(v) for v in tail]


def predict(train_terms, k):
    return _poly(train_terms, k) or _cfinite(train_terms, k)
