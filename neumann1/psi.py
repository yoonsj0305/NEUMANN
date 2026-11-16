"""Predictive State Invention (PSI) -- Q3 development core (opt-in through active.PSI; default off).

A state representation z is insufficient when two observed input prefixes u, v are merged by it (z(u) = z(v)) but
the black box answers the SAME future input w differently:  F(u.w) != F(v.w).  Such a pair is a *distinction*.
PSI turns distinctions into a new executable latent state:

  discover_distinctions  -- Bayesian experimental design: among the prefix pairs the current representation merges
                            (observed, or constructed from observed state-preserving transitions and confirmed by a
                            query), the (pair, suffix) whose outcome the competing latent hypotheses -- weighted by a
                            description-length prior -- are most uncertain about, per uncached query; SOURCE answers
                            F(u.w), F(v.w) for the same suffix w (charged to the run's budget).  A distinction
                            removes the hypotheses that merge the pair; a pair answering every tested suffix alike
                            down-weights the hypotheses that split it.
  invent_state           -- latent candidates are fold programs h' = G(h, x) of the generic substrate (with a start
                            value; single variables or pairs), computable on any new input.  A candidate is admissible
                            when it separates every distinction and makes every observed transition a function of
                            (state, latent, element).  Ranking: posterior weight (description-length prior x EPS per
                            apparently equivalent pair it splits), then the coarsest partition; or a learned policy.
  synthesize / verify    -- done by the caller (active.form_machine) with its existing Update synthesis and
                            verification; this module only classifies the outcome.
  update_discovery_policy-- a logistic model over candidate features fitted on verified outcomes of OTHER tasks.

Nothing here names a task, a routine or an answer; the candidate grammar is the substrate enumeration shared by
every task (active.accumulators()).
"""
from __future__ import annotations
import math
import time


def _sep(hv, u, v):
    return hv.get(u) != hv.get(v)


def merged_pairs(prefixes, state_of, limit=400):
    """Pairs of observed prefixes the current representation cannot tell apart (equal full state)."""
    groups = {}
    for u in prefixes:
        s = state_of(u)
        if s is not None:
            groups.setdefault(s, []).append(u)
    out = []
    for g in groups.values():
        g = sorted(set(g), key=lambda u: (len(u), u))
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                out.append((g[i], g[j]))
                if len(out) >= limit:
                    return out
    return out


EPS = 0.3          # weight kept by a hypothesis for each pair it splits that answered every tested future alike
PRIOR_SCALE = 6.0  # description-length prior: weight 2 ** (-size / PRIOR_SCALE)


def prior(c):
    return 2.0 ** (-c["size"] / PRIOR_SCALE)


def _h2(p):
    return 0.0 if p <= 0.0 or p >= 1.0 else -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def discover_distinctions(pairs, candidates, suffixes, cont, query, cached, budget, deadline,
                          prepare=None, prepare_cost=None, per_pair=2, max_tests=40):
    """Active search for distinctions: Bayesian experimental design over the competing latent hypotheses.

    pairs:      candidate prefix pairs (u, v); `prepare(u, v)` -> True when the current representation merges them
                (may query SOURCE to observe v's state; `prepare_cost(u, v)` = its uncached queries), None = observed.
    candidates: competing latent hypotheses [{"hv": {prefix: value}, "size"}], prior 2 ** (-size / PRIOR_SCALE).
    The next test is the (pair, suffix) with the largest entropy of P(the pair is split | hypotheses) per uncached
    query.  A distinguished pair removes every hypothesis that merges it; a pair that answers every tested suffix
    alike multiplies the weight of every hypothesis that splits it by EPS (weak, since an untested future may still
    differ).  Returns (evidence, equal_pairs, info), evidence = [(u, v, w, F(u.w), F(v.w))]."""
    t0, spent, tests = time.process_time(), 0, 0
    evidence, equal, tried, ready, trace, order = [], [], {}, {}, [], {}
    # hypotheses that agree on every prefix the experiments can involve are one class (summed prior): the design
    # needs only how a class splits pairs, and thousands of fold programs collapse to far fewer classes
    involved = sorted({y for pr in pairs for y in pr}, key=lambda y: (len(y), y))
    classes = {}
    for c in candidates:
        key = tuple(repr(c["hv"].get(y)) for y in involved)
        if key not in classes:
            classes[key] = {"hv": c["hv"], "w": 0.0}
        classes[key]["w"] += prior(c)
    alive = list(classes.values())
    weight = {id(c): c["w"] for c in alive}
    reason = None
    while True:
        if time.process_time() > deadline:
            reason = "deadline"
            break
        if spent >= budget:
            reason = "query budget"
            break
        if tests >= max_tests:
            reason = "test limit"
            break
        tot = sum(weight[id(c)] for c in alive) or 1.0
        best = None
        for u, v in pairs:
            done = tried.get((u, v), 0)
            if done >= per_pair or done >= len(suffixes) or ready.get((u, v)) is False:
                continue
            # suffixes rotate across pairs (the k-th newly tested pair starts at the k-th suffix), so extremes on
            # both sides of the observed range are tried early
            w = suffixes[(done + order.get((u, v), len(order))) % len(suffixes)]
            cost = sum(1 for x in (cont(u, w), cont(v, w)) if not cached(x))
            if prepare_cost is not None and (u, v) not in ready:
                cost += prepare_cost(u, v)
            if cost > budget - spent:
                continue
            ps = sum(weight[id(c)] for c in alive if _sep(c["hv"], u, v)) / tot
            gain = _h2(ps)
            if gain <= 1e-9:
                continue
            key = (gain / max(cost, 0.5), gain, -len(u) - len(v))
            if best is None or key > best[0]:
                best = (key, u, v, w)
        if best is None:
            reason = "no informative experiment within budget"
            break
        (ratio, gain, _), u, v, w = best
        step = {"u": list(u), "v": list(v), "w": list(w), "p_split_entropy": round(gain, 3)}
        trace.append(step)
        if prepare is not None and (u, v) not in ready:
            c0 = prepare_cost(u, v) if prepare_cost else 0
            ok = prepare(u, v)
            spent += c0
            ready[(u, v)] = bool(ok)
            if not ok:
                step["outcome"] = "not merged"
                continue
        order.setdefault((u, v), len(order))
        tried[(u, v)] = tried.get((u, v), 0) + 1
        tests += 1
        before = [cached(cont(u, w)), cached(cont(v, w))]
        yu, yv = query(cont(u, w)), query(cont(v, w))
        spent += sum(1 for b in before if not b)
        if yu is None or yv is None:
            step["outcome"] = "undefined"
            continue
        step["outcome"] = "distinct" if yu != yv else "equal"
        if yu != yv:
            evidence.append((u, v, w, yu, yv))
            tried[(u, v)] = per_pair
            kept = [c for c in alive if _sep(c["hv"], u, v)]
            alive = kept or alive
            if len(alive) <= 1:
                reason = "hypotheses narrowed to one"
                break
        else:
            for c in alive:                          # every equal answer is weak evidence against a split
                if _sep(c["hv"], u, v):
                    weight[id(c)] *= EPS
            if tried[(u, v)] >= min(per_pair, len(suffixes)):
                equal.append((u, v))
    return evidence, equal, {"queries": spent, "tests": tests, "distinctions": len(evidence),
                             "hypothesis_classes": len(classes),
                             "equal_pairs": len(equal), "alive": len(alive), "reason": reason,
                             "constructed_pairs_confirmed": sum(1 for k, v in ready.items() if v),
                             "constructed_pairs_rejected": sum(1 for k, v in ready.items() if not v),
                             "trace": trace[:30], "cpu": round(time.process_time() - t0, 4)}


def invent_state(evidence_pairs, equal_pairs, candidates, transitions, pair_cost=6, max_pairs=60, policy=None):
    """Admissible latent candidates, best first.

    evidence_pairs: [(u, v)] that must be separated (distinctions and one-step transition conflicts).
    transitions:    [(state, element, successor, prefix)] observed; with the latent they must be functional.
    candidates:     [{"show", "size", "hv": {prefix: value}, ...}] single fold variables (value tables).
    Returns (ranked [{"vars": [cand, ...], "size", "false_splits", "ns", "feat"}], info)."""
    def functional(hvs):
        seen = {}
        for a, e, b, u in transitions:
            hs = tuple(h.get(u) for h in hvs)
            if None in hs:
                return False
            k = (a, hs, e)
            if k in seen and seen[k] != b:
                return False
            seen.setdefault(k, b)
        return True

    def separates(hvs, u, v):
        return any(h.get(u) != h.get(v) for h in hvs)

    def item(cs):
        hvs = [c["hv"] for c in cs]
        prefixes = {u for c in cs for u in c["hv"]}
        ns = len({tuple(h.get(u) for h in hvs) for u in prefixes})
        fs = sum(1 for u, v in equal_pairs if separates(hvs, u, v))
        return {"vars": cs, "size": sum(c["size"] for c in cs) + pair_cost * (len(cs) - 1), "false_splits": fs,
                "ns": ns, "n_prefixes": len(prefixes)}
    singles, partial = [], []
    for c in candidates:
        miss = [p for p in evidence_pairs if not _sep(c["hv"], *p)]
        if not miss:
            if functional([c["hv"]]):
                singles.append(item([c]))
        elif len(miss) < len(evidence_pairs):
            partial.append((c, frozenset(miss)))
    pairs = []
    if not singles and partial:
        partial.sort(key=lambda t: (len(t[1]), t[0]["size"]))
        partial = partial[:max_pairs]
        for i in range(len(partial)):
            for j in range(i + 1, len(partial)):
                if partial[i][1] & partial[j][1]:
                    continue
                cs = [partial[i][0], partial[j][0]]
                if functional([c["hv"] for c in cs]):
                    pairs.append(item(cs))
    ranked = singles + pairs
    for it in ranked:
        it["feat"] = features(it, len(evidence_pairs), len(equal_pairs))
    for it in ranked:
        it["posterior"] = 2.0 ** (-it["size"] / PRIOR_SCALE) * EPS ** it["false_splits"]
    if policy is not None:
        ranked.sort(key=lambda it: (-score(policy, it["feat"]), -it["posterior"], it["ns"]))
    else:
        # the most probable sufficient latent given the experiments: description-length prior, down-weighted for every
        # pair it splits that answered every tested future alike; then the coarsest partition
        ranked.sort(key=lambda it: (-it["posterior"], it["ns"]))
    # collapse candidates that induce the same partition of the observed prefixes AND have the same size
    out, seen = [], set()
    for it in ranked:
        sig = (tuple(sorted((u, tuple(c["hv"].get(u) for c in it["vars"])) for u in it["vars"][0]["hv"])), it["size"])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(it)
    return out, {"singles": len(singles), "pairs": len(pairs), "evidence": len(evidence_pairs),
                 "equal_pairs": len(equal_pairs), "candidates": len(candidates)}


def features(it, n_evidence, n_equal):
    """Evidence about ONE candidate latent on the CURRENT task (no identity of the variable, no task name)."""
    f = {"bias": 1.0, "size": it["size"] / 40.0, "n_vars2": float(len(it["vars"]) >= 2),
         "granularity": it["ns"] / max(1, it["n_prefixes"]),
         "false_split_frac": it["false_splits"] / max(1, n_equal), "evidence": min(n_evidence, 20) / 20.0}
    for c in it["vars"]:
        sh = c["show"]
        for k, v in (("reads_e", "$1" in sh), ("keeps_h", "$0" in sh), ("case", sh.startswith("(if")),
                     ("list", c.get("t") == "L"), ("start_" + c.get("zkind", "const"), True)):
            f[k] = f.get(k, 0.0) + float(v) / len(it["vars"])
    return {k: round(v, 4) for k, v in f.items()}


def score(w, f):
    z = sum(w.get(k, 0.0) * v for k, v in f.items())
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


def update_discovery_policy(experience, epochs=400, lr=0.2, l2=0.01):
    """experience: [(features, label)] with label 1 iff the adopted latent led to an independently verified machine
    (challenge passed) on a task OTHER than the ones it will be applied to.  Class-balanced logistic regression."""
    keys = sorted({k for f, _ in experience for k in f})
    w = {k: 0.0 for k in keys}
    n = max(1, len(experience))
    pos = sum(y for _, y in experience)
    cw = {1: n / (2.0 * max(1, pos)), 0: n / (2.0 * max(1, n - pos))}
    for _ in range(epochs):
        g = {k: l2 * w[k] for k in keys}
        for f, y in experience:
            p_ = score(w, f)
            for k, v in f.items():
                g[k] += cw[y] * (p_ - y) * v / n
        for k in keys:
            w[k] -= lr * g[k]
    return {k: round(v, 5) for k, v in w.items()}


def classify_outcome(found_update, fold_failures, tolerance, conflict_with_latent=False):
    """Failure reason of one synthesis attempt with a latent (P0-C)."""
    if conflict_with_latent:
        return "representation insufficient (transitions not functional with the latent)"
    if not found_update:
        return "no Update within the synthesis budget"
    if fold_failures > tolerance:
        return "Update found but %d initial examples fold wrongly" % fold_failures
    return "ok"
