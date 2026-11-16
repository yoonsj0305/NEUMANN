"""Structural state identification (PSI40) -- Q3 development core (opt-in through active.PSI40; default off).

Section 40: the hidden state is identified from observations FIRST, an executable representation is CONSTRUCTED for
it, and only then is the method synthesised.  Section 39 failed because (i) a state outside the fixed fold list could
not be found at all, (ii) two distinctions left thousands of fold programs admissible and a prior over program size
chose among them, and (iii) a failed attempt spent CPU and SOURCE queries the existing path needed.

  free_distinctions  -- distinctions already present in the observations (no query): two observed prefixes the
                        current state z merges whose answers to the SAME observed suffix differ.  Used as the
                        observation-based necessity check before any query is spent.
  discover           -- candidate-free experiments.  Pairs: merged observed prefixes, and constructed chains u, u.e,
                        u.e.e for an element e that left z unchanged (the merge is confirmed before any suffix test).
                        The next test is chosen by the EMPIRICAL informativeness of the suffix on this task (Laplace
                        rate of the distinctions it produced) and the history difference of the pair -- no latent
                        hypothesis and no prior over a grammar decide where to look.  A pair that answers every
                        tested suffix alike is kept as equal-future evidence; nothing is declared identified from it.
  construct_automata -- an executable finite-state latent built from the constraints, not chosen from a list: a guard
                        c = g(x) (a boolean program of the generic substrate over the element; constants are the
                        observed element values; enumerated in cost order and collapsed by the partition it induces
                        on the observed alphabet) and the smallest transition table delta(q, c) whose run from q = 0
                        separates every distinction, found by backtracking over the prefix tree of guard words
                        (k <= KMAX states).  The table is computable on any input; unseen (q, c) cells stay q.
  rank / disagreement-- representations (constructed automata and the existing fold candidates) collapse into classes
                        by the partition they induce on the observed prefixes (P0-C); a class must separate every
                        distinction; classes are ordered by the equal-future pairs they split, then description
                        length.  When the best classes disagree on a merged pair, `disagreement` names the pair so
                        that an experiment decides (refinement only where needed).
Every function returns its failure reason and its cost.  Nothing here names a task, a routine, a generator or an
answer.
"""
from __future__ import annotations
import time

KMAX = 4                     # largest automaton tried (states)
DFA_STEPS = 20000            # backtracking assignments per (guard, k) before "search time"


def _key(u):
    return (len(u), u)


def merged_groups(prefixes, state_of):
    groups = {}
    for u in prefixes:
        s = state_of(u)
        if s is not None:
            groups.setdefault(s, []).append(u)
    return {s: sorted(set(g), key=_key) for s, g in groups.items() if len(set(g)) > 1}


def free_distinctions(prefixes, state_of, futures, limit=60):
    """Distinctions in the observations alone.  futures(u) -> {w: F(u.w)} over the observed continuations of u
    (w non-empty).  Returns [(u, v, w, F(u.w), F(v.w))] -- no query."""
    out = []
    for g in merged_groups(prefixes, state_of).values():
        fu = {u: futures(u) for u in g}
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                u, v = g[i], g[j]
                for w in sorted(set(fu[u]) & set(fu[v]), key=_key):
                    if fu[u][w] != fu[v][w]:
                        out.append((u, v, w, fu[u][w], fu[v][w]))
                        break
                if len(out) >= limit:
                    return out
    return out


def residual(y_u, y_uw, direction="prefix"):
    """What the future w adds to the current answer: F(u.w) minus F(u) when F(u) is its beginning (prefix direction)
    or its end (suffix direction); None when the answer is not extended (no residual is defined)."""
    if not isinstance(y_u, tuple) or not isinstance(y_uw, tuple) or len(y_uw) < len(y_u):
        return None
    if direction == "prefix":
        return y_uw[len(y_u):] if y_uw[:len(y_u)] == y_u else None
    return y_uw[:len(y_uw) - len(y_u)] if y_uw[len(y_uw) - len(y_u):] == y_u else None


def residual_signatures(prefixes, answer, futures, direction="prefix", max_seps=4000):
    """Future-behaviour signatures comparable ACROSS different current states: for an answer that the future only
    extends, two prefixes whose residuals for the same observed suffix w differ are in different hidden states
    (Myhill-Nerode for the residual function); prefixes with the same residual for w form an equal-evidence group.
    answer(u) -> F(u) or None; futures(u) -> {w: F(u.w)}.  No query.
    Returns (separations, equal_groups, info)."""
    byw = {}
    for u in prefixes:
        y = answer(u)
        if y is None:
            continue
        for w, yw in futures(u).items():
            r = residual(y, yw, direction)
            if r is not None:
                byw.setdefault(w, {}).setdefault(r, []).append(u)
    seps, hist = [], 0
    for w, rg in sorted(byw.items(), key=lambda kv: _key(kv[0])):
        cls = [sorted(g, key=_key) for g in rg.values()]
        if len(cls) > 1:
            hist += 1
        for i in range(len(cls)):
            for j in range(i + 1, len(cls)):
                for u in cls[i][:6]:
                    for v in cls[j][:6]:
                        if len(seps) < max_seps:
                            seps.append((u, v) if _key(u) < _key(v) else (v, u))
    # equal-future evidence: two prefixes whose residuals agree on at least two history-dependent suffixes (a
    # suffix that extends every answer alike tells nothing) and differ on none
    informative = {w for w, rg in byw.items() if len(rg) > 1}
    sig = {}
    for w in informative:
        for r, g in byw[w].items():
            for u in g:
                sig.setdefault(u, {})[w] = r
    us = sorted(sig, key=_key)
    groups = []
    for i in range(len(us)):
        for j in range(i + 1, len(us)):
            a, b = sig[us[i]], sig[us[j]]
            common = set(a) & set(b)
            if len(common) >= 2 and all(a[w] == b[w] for w in common):
                groups.append([us[i], us[j]])
    best = sorted(byw, key=lambda w: (-len(byw[w]), -sum(len(g) for g in byw[w].values()), _key(w)))
    info = {"suffixes_with_residuals": len(byw), "history_dependent_suffixes": hist, "separations": len(seps),
            "equal_groups": len(groups), "best_suffixes": best[:6]}
    return list(dict.fromkeys(seps)), groups, info


def _diversity(u, v):
    a, b = list(u), list(v)
    for x in list(a):
        if x in b:
            b.remove(x)
            a.remove(x)
    return 1 + abs(len(u) - len(v)) + len(a) + len(b)


def discover(pairs, suffixes, cont, query, cached, budget, deadline, prepare=None, prepare_cost=None, per_pair=3,
             known=()):
    """Candidate-free distinction experiments (see module doc).  `known`: distinctions already observed (free).
    Returns (evidence, equal_pairs, info); evidence = [(u, v, w, F(u.w), F(v.w))]."""
    t0, spent = time.process_time(), 0
    evidence, equal_n, trace = list(known), {}, []
    done = {(u, v) for u, v, _, _, _ in known}
    rate = {w: [0, 0] for w in suffixes}                 # [distinctions, tests] per suffix on THIS task
    for u, v, w, _, _ in known:
        if w in rate:
            rate[w][0] += 1
            rate[w][1] += 1
    tested, ready, reason = {}, {}, None
    rejected = confirmed = 0
    while True:
        if time.process_time() > deadline:
            reason = "deadline"
            break
        best = None
        for pr in pairs:
            if pr in done or ready.get(pr) is False or tested.get(pr, 0) >= per_pair:
                continue
            u, v = pr
            pc = 0 if ready.get(pr) or prepare_cost is None else prepare_cost(u, v)
            for i, w in enumerate(suffixes):
                if (pr, w) in tested:
                    continue
                cost = pc + sum(1 for y in (cont(u, w), cont(v, w)) if not cached(y))
                if spent + cost > budget:
                    continue
                s, n = rate[w]
                sc = ((s + 1.0) / (n + 2.0), _diversity(u, v), -cost, -i)
                if best is None or sc > best[0]:
                    best = (sc, pr, w, pc)
                break                                  # the next untested suffix of this pair only
        if best is None:
            reason = "query budget" if spent >= budget else "no untested experiment within budget"
            break
        _, pr, w, pc = best
        u, v = pr
        if pr not in ready:
            if prepare is not None:
                q0 = spent
                ok = prepare(u, v)
                spent += pc
                ready[pr] = bool(ok)
                if not ok:
                    rejected += 1
                    trace.append(("rejected", list(u), list(v), spent - q0))
                    continue
                confirmed += 1
            else:
                ready[pr] = True
        tested[(pr, w)] = True
        tested[pr] = tested.get(pr, 0) + 1
        miss = sum(1 for y in (cont(u, w), cont(v, w)) if not cached(y))
        yu, yv = query(cont(u, w)), query(cont(v, w))
        spent += miss
        rate[w][1] += 1
        if yu is None or yv is None:
            continue
        if yu != yv:
            rate[w][0] += 1
            evidence.append((u, v, w, yu, yv))
            done.add(pr)
            trace.append(("distinct", list(u), list(v), list(w)))
        else:
            equal_n[pr] = equal_n.get(pr, 0) + 1
    equal = [pr for pr, n in equal_n.items() if pr not in done]
    info = {"queries": spent, "distinctions": len(evidence), "free_distinctions": len(known),
            "equal_pairs": len(equal), "reason": reason, "constructed_confirmed": confirmed,
            "constructed_rejected": rejected, "suffix_rates": {repr(list(w)): r for w, r in rate.items() if r[1]},
            "trace": trace[:30], "cpu": round(time.process_time() - t0, 4)}
    return evidence, equal, info


# ------------------------------------------------------------------ constructed finite-state latents
def guard_partitions(alphabet, enumerate_bool, deadline, limit=200):
    """Boolean guards over one element, in cost order, one per partition of the observed alphabet (a guard and its
    negation are the same partition).  enumerate_bool(alphabet, deadline, limit) -> [(ast, fn, size)].
    The trivial guard (no dependence on the element) comes first."""
    out, seen = [{"ast": None, "fn": lambda e: 0, "size": 0, "show": "-"}], {tuple(0 for _ in alphabet)}
    for ast, fn, size, show in enumerate_bool(alphabet, deadline, limit):
        try:
            part = tuple(int(bool(fn(e))) for e in alphabet)
        except Exception:
            continue
        if part[0] == 1:
            part = tuple(1 - p for p in part)
        if part in seen:
            continue
        seen.add(part)
        out.append({"ast": ast, "fn": (lambda e, fn=fn: _guard_class(fn, e)), "size": size, "show": show})
    return out


def _guard_class(fn, e):
    """the class of an element under a guard; -1 (a class of its own, constrained only by evidence) when the guard
    program fails on it (post-freeze crash fix in section 41: a failing guard used to raise and abort the run)"""
    try:
        return int(bool(fn(e)))
    except Exception:
        return -1


def dfa_search(words, seps, k, steps=DFA_STEPS):
    """Smallest-table search: delta over states 0..k-1 and letters of the words, run from 0, such that every pair in
    seps ends in different states.  words: {prefix: tuple of letters}.  Returns (delta, status)."""
    wp = []
    for u, v in seps:
        a, b = words[u], words[v]
        if a == b:
            return None, "guard merges a distinction"
        wp.append((a, b))
    nodes = sorted({w[:i] for a, b in wp for w in (a, b) for i in range(len(w) + 1)}, key=lambda w: (len(w), w))
    partners = {}
    for a, b in wp:
        partners.setdefault(a, []).append(b)
        partners.setdefault(b, []).append(a)
    state, delta, used, cnt = {(): 0}, {}, [1], [0]

    def ok(n):
        s = state[n]
        return all(state.get(p, -1) != s for p in partners.get(n, ()))

    def go(i):
        cnt[0] += 1
        if cnt[0] > steps:
            raise TimeoutError
        if i == len(nodes):
            return True
        n = nodes[i]
        if not n:
            return ok(n) and go(i + 1)
        s, c = state[n[:-1]], n[-1]
        if (s, c) in delta:
            state[n] = delta[(s, c)]
            r = ok(n) and go(i + 1)
            del state[n]
            return r
        for t in range(min(k, used[0] + 1)):
            delta[(s, c)] = t
            state[n] = t
            grew = t == used[0]
            if grew:
                used[0] += 1
            if ok(n) and go(i + 1):
                return True
            if grew:
                used[0] -= 1
            del state[n]
            del delta[(s, c)]
        return False
    try:
        return (dict(delta), "found") if go(0) else (None, "no %d-state table" % k)
    except TimeoutError:
        return None, "search time"


def construct_automata(seps, prefixes, seq, guards, deadline, kmax=KMAX):
    """Executable finite-state latents from the separation constraints: for the smallest k that admits any guard, every
    guard whose table exists.  seq(u) = the elements of u in fold order.  Returns (reps, info)."""
    t0 = time.process_time()
    info = {"guards": len(guards), "k": None, "status": {}}
    if not seps:
        info["reason"] = "no distinction"
        return [], info
    for k in range(2, kmax + 1):
        reps = []
        for g in guards:
            if time.process_time() > deadline:
                info["reason"] = "deadline"
                break
            words = {u: tuple(g["fn"](e) for e in seq(u)) for u in set(prefixes) | {y for pr in seps for y in pr}}
            delta, st = dfa_search(words, seps, k)
            info["status"][st] = info["status"].get(st, 0) + 1
            if delta is None:
                continue
            letters = sorted({c for (_, c) in delta})
            reps.append(make_automaton(k, g, delta, len(letters)))
        if reps:
            info["k"] = k
            info["found"] = len(reps)
            break
    else:
        info["reason"] = "not representable: no automaton with <= %d states and one guard" % kmax
    info["cpu"] = round(time.process_time() - t0, 4)
    return (reps if info.get("k") else []), info


def make_automaton(k, g, delta, nletters):
    gf = g["fn"]

    def step(args, delta=dict(delta), gf=gf):
        h, e = args
        return delta.get((h, gf(e)), h)
    table = sorted((list(kv[0]), kv[1]) for kv in delta.items())
    letters = (0, 1) if g["ast"] is not None else (0,)
    return {"family": "automaton", "fn": step, "z": 0, "t": "I", "k": k, "guard": g["show"], "gfn": gf,
            "delta": dict(delta), "unseen": [(q, c) for q in range(k) for c in letters if (q, c) not in delta],
            "size": g["size"] + len(delta), "show": "automaton(k=%d; guard=%s; delta=%s)" % (k, g["show"], table)}


# ------------------------------------------------------------------ equivalence classes, ranking, refinement
def partition_key(values, prefixes):
    lab, out = {}, []
    for u in prefixes:
        v = values.get(u)
        if v not in lab:
            lab[v] = len(lab)
        out.append(lab[v])
    return tuple(out)


def rank(reps, seps, equal, prefixes):
    """reps: [{"values": {prefix: latent value}, "size", ...}].  Keep those separating every distinction, one per
    induced partition (smallest description), ordered by (equal-evidence splits, size, classes).  `equal`: groups
    of prefixes observed to have the same future (a group of size n split into m values costs m - 1)."""
    cls = {}
    for r in reps:
        hv = r["values"]
        if any(hv.get(u) == hv.get(v) or hv.get(u) is None or hv.get(v) is None for u, v in seps):
            continue
        key = partition_key(hv, prefixes)
        r["equal_split"] = sum(len({hv.get(u) for u in g}) - 1 for g in equal)
        r["classes"] = len(set(key))
        # one representative per class: the smallest description, then the smallest magnitude of its values
        # (len before 2 ** len: the same partition, but a value an Update can use directly)
        r["magnitude"] = max((abs(v) for v in hv.values() if isinstance(v, int) and not isinstance(v, bool)), default=0)
        if key not in cls or (r["size"], r["magnitude"]) < (cls[key]["size"], cls[key]["magnitude"]):
            cls[key] = r
    out = sorted(cls.values(), key=lambda r: (r["equal_split"], r["size"], r["classes"]))
    return out, {"admissible_classes": len(out)}


def disagreement(a, b, merged_pairs, skip):
    """A merged prefix pair on which representations a and b disagree (one splits it, the other does not)."""
    for u, v in merged_pairs:
        if (u, v) in skip:
            continue
        vals_ = (a["values"].get(u), a["values"].get(v), b["values"].get(u), b["values"].get(v))
        if None in vals_:
            continue
        if (vals_[0] == vals_[1]) != (vals_[2] == vals_[3]):
            return (u, v)
    return None


def classify_failure(n_distinctions, n_reps, attempts):
    """P0-C failure classes: not representable / insufficient information / search time."""
    if n_distinctions == 0:
        return "insufficient information: no distinction observed"
    if n_reps == 0:
        return "not representable: no constructed automaton or fold separates the distinctions"
    if attempts and all(a == "no Update within the synthesis budget" for a in attempts):
        return "search time: representation found, Update synthesis did not finish"
    return "insufficient information: representation(s) found but the Update folds the examples wrongly"


# ------------------------------------------------------------------ section 41: evidence-driven structural invention
def dfa_enumerate(words, seps, merges, k, cap=30, steps=DFA_STEPS):
    """Every table (up to `cap`, symmetry broken: new states in order) over states 0..k-1 whose run from 0 puts every
    pair in seps in different states and every pair in merges in the same state.  Cells reached only by unconstrained
    words are enumerated too (their alternatives are competing hypotheses, never a default).  Returns (list of delta,
    status)."""
    for u, v in seps:
        if words[u] == words[v]:
            return [], "guard merges a distinction"
    wp = [(words[u], words[v], 0) for u, v in seps] + [(words[u], words[v], 1) for u, v in merges if words[u] != words[v]]
    nodes = sorted({w[:i] for w in words.values() for i in range(len(w) + 1)}, key=lambda w: (len(w), w))
    partners = {}
    for a, b, same in wp:
        partners.setdefault(a, []).append((b, same))
        partners.setdefault(b, []).append((a, same))
    state, delta, used, cnt, out = {(): 0}, {}, [1], [0], []

    def ok(n):
        s = state[n]
        for p, same in partners.get(n, ()):
            t = state.get(p)
            if t is not None and (t == s) != bool(same):
                return False
        return True

    def go(i):
        cnt[0] += 1
        if cnt[0] > steps or len(out) >= cap:
            raise TimeoutError
        if i == len(nodes):
            out.append(dict(delta))
            return
        n = nodes[i]
        if not n:
            if ok(n):
                go(i + 1)
            return
        s, c = state[n[:-1]], n[-1]
        if (s, c) in delta:
            state[n] = delta[(s, c)]
            if ok(n):
                go(i + 1)
            del state[n]
            return
        for t in range(min(k, used[0] + 1)):
            delta[(s, c)] = t
            state[n] = t
            grew = t == used[0]
            if grew:
                used[0] += 1
            if ok(n):
                go(i + 1)
            if grew:
                used[0] -= 1
            del state[n]
            del delta[(s, c)]
    status = "complete"
    try:
        go(0)
    except TimeoutError:
        status = "capped"
    return out, status


def automaton_values(delta, gf, seq, prefixes):
    """States of the prefixes under a partial table; None where the run meets a cell no evidence fixed."""
    out = {}
    for u in prefixes:
        s = 0
        for e in seq(u):
            try:
                s = delta.get((s, gf(e)))
            except Exception:
                s = None
            if s is None:
                break
        out[u] = s
    return out


def make_partial_automaton(k, g, delta):
    """An executable automaton whose unobserved cells stay UNKNOWN: a run that meets one has no value (no answer is
    produced from an unidentified transition)."""
    gf = g["fn"]

    def step(args, delta=dict(delta), gf=gf):
        h, e = args
        return delta.get((h, gf(e)))
    letters = (0, 1) if g["ast"] is not None else (0,)
    table = sorted((list(kv[0]), kv[1]) for kv in delta.items())
    return {"family": "automaton", "fn": step, "z": 0, "t": "I", "k": k, "guard": g["show"], "gfn": gf,
            "delta": dict(delta), "unseen": [(q, c) for q in range(k) for c in letters if (q, c) not in delta],
            "size": g["size"] + len(delta), "show": "automaton(k=%d; guard=%s; delta=%s)" % (k, g["show"], table)}


def version_space(seps, merges, constrained, pool, seq, guards, deadline, cap=30, kmax=KMAX):
    """Executable structures consistent with the evidence: for the smallest k that admits any (guard, table) and for
    k + 1, every table (enumerated, capped) of every guard.  Hypotheses are collapsed by the partition they induce on
    constrained + pool prefixes (structures that predict the same are one hypothesis).  Returns (hyps, info)."""
    t0 = time.process_time()
    info = {"guards": len(guards), "status": {}, "kmin": None}
    allp = list(dict.fromkeys(list(constrained) + list(pool) + [y for pr in list(seps) + list(merges) for y in pr]))
    hyps, seen, kmin = [], set(), None
    for k in range(2, kmax + 1):
        if kmin is not None and k > kmin + 1:
            break
        found = False
        for g in guards:
            if time.process_time() > deadline:
                info["reason"] = "deadline"
                break
            words = {u: tuple(g["fn"](e) for e in seq(u)) for u in allp}
            tables, st = dfa_enumerate(words, seps, merges, k, cap)
            info["status"][st] = info["status"].get(st, 0) + 1
            for d in tables:
                found = True
                vals = automaton_values(d, g["fn"], seq, allp)
                key = (k,) + partition_key(vals, allp)
                if key in seen:
                    continue
                seen.add(key)
                r = make_partial_automaton(k, g, d)
                r["values"] = vals
                hyps.append(r)
        if found and kmin is None:
            kmin = k
    info["kmin"] = kmin
    info["hypotheses"] = len(hyps)
    info["cpu"] = round(time.process_time() - t0, 3)
    return hyps, info


def disagreement_count(top, hyps, u, v):
    a, b = top["values"].get(u), top["values"].get(v)
    if a is None or b is None:
        return 0
    same = a == b
    n = 0
    for h in hyps:
        x, y = h["values"].get(u), h["values"].get(v)
        if x is not None and y is not None and (x == y) != same:
            n += 1
    return n


def consistent(h, seps, merges):
    hv = h["values"]
    for u, v in seps:
        if hv.get(u) is not None and hv.get(v) is not None and hv[u] == hv[v]:
            return False
    for u, v in merges:
        if hv.get(u) is not None and hv.get(v) is not None and hv[u] != hv[v]:
            return False
    return True
