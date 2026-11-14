"""SOURCE-anchored, typed state correspondence transport.

Keeps source operator/binder structure; discovers expressions for its state
roles. Existing Q3 enumerator constructs ONLY a correspondence expression.
This is not a replacement learned discovery core or per-task answer generator.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import itertools
import time

from neumann1 import invention_core as ic, spec_core as sc
from .contracts import Artifact, digest, result

LIB = ic.base_library()
I, B, L = ic.T_I, ic.T_B, ic.T_L
MAX_KERNELS = 48
MAX_RULES = 64
_INVERSE = None


def tup(x):
    return tuple(tup(y) for y in x) if isinstance(x, (tuple, list)) else x


def checked_type(ast, scope):
    h = ast[0]
    if h == "v":
        if len(ast) != 2 or type(ast[1]) is not int or not 0 <= ast[1] < len(scope):
            raise ValueError("invalid free/bound variable")
        return scope[ast[1]]
    if h == "k":
        if len(ast) != 2 or type(ast[1]) is not int:
            raise ValueError("invalid constant")
        return I
    if h not in LIB:
        raise ValueError("unsupported source vocabulary")
    p = LIB[h]
    if len(ast) != p.arity + 1:
        raise ValueError("invalid primitive arity")
    for c, (t, bt) in zip(ast[1:], p.params):
        if checked_type(c, tuple(scope) + bt) != t:
            raise ValueError("type mismatch")
    return p.ret


def dependencies(ast, base):
    if ast[0] == "v":
        return {ast[1]} if ast[1] < base else set()
    if ast[0] == "k":
        return set()
    return set().union(*(dependencies(c, base) for c in ast[1:]))


def _lift(ast, base, extra):
    if ast[0] == "v":
        return ("v", ast[1] + extra) if ast[1] >= base else ast
    if ast[0] == "k":
        return ast
    return (ast[0],) + tuple(_lift(c, base, extra) for c in ast[1:])


def substitute(ast, source_arity, target_arity, bindings, depth=0):
    """Capture-avoiding substitution of source roles by arbitrary target ASTs."""
    h = ast[0]
    if h == "v":
        j = ast[1]
        return _lift(bindings[j], target_arity, depth) if j < source_arity else ("v", target_arity + j - source_arity)
    if h == "k":
        return ast
    return (h,) + tuple(substitute(c, source_arity, target_arity, bindings, depth + len(bt))
                        for c, (_, bt) in zip(ast[1:], LIB[h].params))


@dataclass(frozen=True)
class Kernel:
    artifact_id: str
    path: tuple
    ast: tuple
    in_types: tuple
    out_type: str

    @property
    def key(self):
        return digest([self.ast, self.in_types, self.out_type])


def extract(artifacts):
    """A typed subtree is retained with its certified SOURCE context path."""
    c0 = time.process_time()
    kernels, methods, counts = {}, [], Counter()
    for a in artifacts:
        d = a.data
        m = d["executable_method"]
        if m.get("kind") not in ("ast", "zmap", "zfilter"):
            continue
        ast, scope = tup(m["ast"]), tuple(m["state_types"])
        expected = m["output_type"] if m["kind"] == "ast" else I if m["kind"] == "zmap" else B
        if checked_type(ast, scope) != expected:
            raise ValueError("source method/result type mismatch")
        methods.append((a.identity, m))

        def walk(node, types, path):
            if node[0] in ("v", "k"):
                return
            ds = sorted(dependencies(node, len(types)))
            # Closed literal trees and identity-only fragments are not principles.
            if ds and 3 <= ic.size(node) <= 28 and len(ds) <= 3:
                mapping = {old: ("v", new) for new, old in enumerate(ds)}
                norm = substitute(node, len(types), len(ds), mapping)
                ts = tuple(types[j] for j in ds)
                k = Kernel(a.identity, path, norm, ts, checked_type(norm, ts))
                kernels.setdefault(k.key, k)
                counts[k.key] += 1
            for j, (child, (_, bt)) in enumerate(zip(node[1:], LIB[node[0]].params)):
                walk(child, types + bt, path + (j,))
        walk(ast, scope, ())
    # Representation-only ordering; no receiver task labels/IDs or per-family routes.
    ordered = sorted(kernels.values(), key=lambda k: (-any(n in str(k.ast) for n in ("fold", "filter", "map")),
                                                      -counts[k.key], -ic.size(k.ast), k.key))
    return {"kernels": ordered[:MAX_KERNELS], "methods": methods,
            "extraction_cpu_seconds": time.process_time() - c0, "all_kernel_count": len(kernels)}


class Meter:
    def __init__(self):
        self.start = self.last = time.process_time()
        self.phase = "memory"
        self.costs = {k: 0.0 for k in ("memory", "match", "reconstruct", "verify", "failed")}

    def switch(self, phase):
        now = time.process_time()
        self.costs[self.phase] += now - self.last
        self.last, self.phase = now, phase

    def finish(self):
        self.switch(self.phase)
        return {"phase_cpu_seconds": self.costs, "total_cpu_seconds": time.process_time() - self.start,
                "execute_cpu_seconds": None, "independent_verify_cpu_seconds": None,
                "energy_joules": None, "monetary_cost": None}


def _eval(ast, inputs):
    try:
        return ic.compile_ast(ast, len(inputs), LIB)(tuple(inputs))
    except ic.Fail:
        return None


def _columns(types, consts):
    out = {t: [("v", j) for j, v in enumerate(types) if v == t] for t in (I, B, L)}
    out[I] += [("k", k) for k in sorted(set(range(-2, 10)) | set(consts))]
    return out


def _universe(typ, state, goal):
    if typ == I:
        values = set(range(-2, 13))
        for x in (*state, goal):
            if type(x) is int:
                values.add(x)
            elif isinstance(x, tuple):
                values.update(x)
                values.add(len(x))
        return tuple(sorted(values))[:128]
    if typ == B:
        return (False, True)
    lists = [x for x in (*state, goal) if isinstance(x, tuple)]
    values = {(), *lists, *(x[::-1] for x in lists)}
    for a, b in itertools.product(lists, repeat=2):
        if len(a) + len(b) <= ic.LEN_CAP:
            values.add(a + b)
    for x in lists:
        for i in range(len(x) + 1):
            for j in range(i, len(x) + 1):
                values.add(x[i:j])
    preferred = sorted(values, key=lambda x: (x not in lists, len(x), x))
    return tuple(preferred[:128])


def _inverse_hint(ast, active, args, goal, inverse):
    """Reuse Q3's derived inverse operators along a source-structure path.
    This is only a candidate preimage, always rechecked by source execution.
    """
    if ast == ("v", active):
        return goal
    if ast[0] in ("v", "k"):
        return None
    p = LIB[ast[0]]
    if p.kind != "fo" or p.arity != 2:
        return None
    dep = [active in dependencies(child, len(args)) for child in ast[1:]]
    if sum(dep) != 1:
        return None
    unknown = dep.index(True)
    alone = inverse.get(p.name, {}).get("alone")
    if alone is not None:
        recovered = _eval(tup(alone[unknown]), (goal,))
        if recovered is not None:
            return _inverse_hint(ast[1 + unknown], active, args, recovered, inverse)
    if p.ret != I:
        return None
    known = _eval(ast[2 - unknown], args)
    if known is None:
        return None
    for name, k, q in inverse.get("_given_I", []):
        if name != p.name or k != unknown:
            continue
        try:
            value = q((goal, known))
        except ic.Fail:
            continue
        return _inverse_hint(ast[1 + unknown], active, args, value, inverse)
    return None


def _stages(task):
    return sc.subtasks(task) + [{"kind": "ast", "in_types": tuple(task["in_types"]), "out_type": task["out_type"],
             "points": [(j, 0, tuple(i), o) for j, (i, o) in enumerate(task["train"])]}]


def _fit_method(sol, task):
    return all(sc.run_solution(sol, LIB, i, task["train"]) == o for i, o in task["train"])


def _role_options(kernel, stage, consts):
    cols = _columns(stage["in_types"], consts)
    return [cols[t] for t in kernel.in_types]


class FoundTransport(Exception):
    def __init__(self, kernel, stage, bindings, body):
        self.kernel, self.stage, self.bindings, self.body = kernel, stage, bindings, body


def transport(task, inventory, *, cap_s=3, mode="C", fallback=None):
    """TRAIN-only Q6; unsupported correspondences return UNKNOWN to Q3.

    inventory must originate from admitted artifacts. fallback is injected by
    the SAME Q3 core, never a new Q6 target-specific solver.
    """
    if task.get("test"):
        raise ValueError("Q6 inference refuses hidden TEST observations")
    meter = Meter()
    end = meter.start + cap_s
    od = digest({k: task[k] for k in ("in_types", "out_type", "train")})
    consts = ic.data_constants(task["train"])
    stages = _stages(task)
    counterexamples, stats = [], Counter()
    failures = []
    sol, source, correspondence, via = None, None, None, None

    def check(kernel, stage, bindings):
        checked_at = time.process_time()
        before = {p: meter.costs[p] for p in ("reconstruct", "verify")}
        meter.switch("reconstruct")
        body = substitute(kernel.ast, len(kernel.in_types), len(stage["in_types"]), bindings)
        checked_type(body, tuple(stage["in_types"]))
        stats["reconstructed_candidates"] += 1
        meter.switch("verify")
        if _fit_method((stage["kind"], body), task):
            raise FoundTransport(kernel, stage, bindings, body)
        stats["rejected_candidates"] += 1
        failures.append({"source_artifact_id": kernel.artifact_id, "kernel_key": kernel.key,
                         "bindings": bindings, "cpu_seconds": time.process_time() - checked_at,
                         "reason": "authorized_TRAIN_mismatch"})
        meter.switch("match")
        for phase in before:
            failed = meter.costs[phase] - before[phase]
            meter.costs[phase] -= failed
            meter.costs["failed"] += failed

    try:
        # B: whole certified methods. Source/target original types must agree.
        replay_end = min(end, meter.start + .1 * cap_s)
        meter.switch("verify")
        for aid, method in inventory["methods"]:
            if time.process_time() >= replay_end:
                break
            if list(method["input_types"]) == list(task["in_types"]) and method["output_type"] == task["out_type"]:
                candidate = (method["kind"], tup(method["ast"]))
                stats["whole_program_replays"] += 1
                if _fit_method(candidate, task):
                    sol, source, via = candidate, aid, "replay"
                    break
        if sol is None and mode not in ("B",):
            meter.switch("match")
            type_end = min(end, meter.start + .35 * cap_s)
            seen = set()
            for stage in stages:
                for k in inventory["kernels"]:
                    if k.out_type != stage["out_type"]:
                        continue
                    for bs in itertools.product(*_role_options(k, stage, consts)):
                        if time.process_time() >= type_end:
                            break
                        key = (stage["kind"], k.key, bs)
                        if key in seen:
                            continue
                        seen.add(key)
                        stats["type_only_candidates"] += 1
                        check(k, stage, dict(enumerate(bs)))
                    if time.process_time() >= type_end:
                        break
                if time.process_time() >= type_end:
                    break
        if sol is None and mode == "C":
            match_end = min(end, meter.start + .9 * cap_s)
            for stage_index, stage in enumerate(stages):
                if time.process_time() >= match_end:
                    break
                stage_end = time.process_time() + (match_end - time.process_time()) / (len(stages) - stage_index)
                _match_stage(task, stage, inventory["kernels"], consts, stage_end, check,
                             stats, counterexamples, meter)
    except FoundTransport as found:
        sol, source = (found.stage["kind"], found.body), found.kernel.artifact_id
        bs = found.bindings
        compound = any(ast[0] not in ("v", "k") for ast in bs.values())
        via = "compound_transport" if compound else "type_only"
        correspondence = {"kernel": found.kernel.ast, "source_fragment_path": found.kernel.path,
                          "source_role_types": found.kernel.in_types,
                          "target_state_types": found.stage["in_types"],
                          "bindings": {str(j): a for j, a in sorted(bs.items())}, "compound": compound}
    if sol is None and fallback is not None and time.process_time() < end:
        meter.switch("match")
        r = fallback(max(.001, end - time.process_time()))
        sol = r.get("sol")
        via = "q3_fallback" if sol is not None else None
        stats["fallback_candidates"] += r.get("candidates", 0)
    cost = meter.finish()
    return result(od, status="TRAIN_CONSISTENT" if sol is not None else "UNKNOWN", source=source,
                  correspondence=correspondence, representation={"kind": sol[0]} if sol else None,
                  method={"kind": sol[0], "ast": sol[1]} if sol else None,
                  counterexamples=counterexamples[:32], cost={**cost, "counts": dict(stats)},
                  reason=None if sol else "no_supported_verified_correspondence",
                  obligations=["finite SOURCE proof and role type binding", "runtime definedness on receiver TRAIN",
                               "independent original receiver TEST still required"]) | {"via": via, "rejected_candidate_ledger": failures}


def _match_stage(task, stage, kernels, consts, end, check, stats, counterexamples, meter):
    global _INVERSE
    if _INVERSE is None:
        _INVERSE = sc.load_inverses()
    points = list(stage["points"][:8])
    if not points:
        return
    types = tuple(stage["in_types"])
    # A correspondence may join target columns. Small scopes precede the full
    # state; the scope enumeration is type/position-based, never family-named.
    scopes = [(j,) for j in range(len(types))]
    scopes += list(itertools.combinations(range(len(types)), 2))
    scopes += [tuple(range(len(types)))]
    for _round in range(3):
        if time.process_time() >= end:
            return
        rules = []
        universes = {}
        for k in kernels:
            if k.out_type != stage["out_type"] or len(k.in_types) > 3:
                continue
            options = _role_options(k, stage, consts)
            fn = ic.compile_ast(k.ast, len(k.in_types), LIB)
            for active in range(len(k.in_types)):
                other = [j for j in range(len(k.in_types)) if j != active]
                # Constant-independent columns first. Bounded hypothesis count
                # keeps expensive noninjective inverse fibres from taking over.
                for vals in itertools.product(*(options[j] for j in other)):
                    if len(rules) >= MAX_RULES or time.process_time() >= end:
                        break
                    fixed = dict(zip(other, vals))
                    fibres = []
                    for p in points:
                        args = [None] * len(k.in_types)
                        for j, ast in fixed.items():
                            args[j] = _eval(ast, p[2])
                        if any(args[j] is None for j in other):
                            break
                        fibre = set()
                        ukey = (k.in_types[active], p[0], p[1])
                        if ukey not in universes:
                            universes[ukey] = _universe(k.in_types[active], p[2], p[3])
                        candidates = list(universes[ukey])
                        hint = _inverse_hint(k.ast, active, args, p[3], _INVERSE)
                        if hint is not None and hint not in candidates:
                            candidates.append(hint)
                        for ui, u in enumerate(candidates):
                            if not (ui & 7) and time.process_time() >= end:
                                return
                            args[active] = u
                            stats["source_relation_evaluations"] += 1
                            try:
                                v = fn(tuple(args))
                            except ic.Fail:
                                continue
                            if type(v) is type(p[3]) and v == p[3]:
                                fibre.add(u)
                        if not fibre:
                            break
                        fibres.append(frozenset(fibre))
                    if len(fibres) == len(points):
                        rules.append((k, active, fixed, tuple(fibres)))
                if len(rules) >= MAX_RULES or time.process_time() >= end:
                    break
            if len(rules) >= MAX_RULES or time.process_time() >= end:
                break
        stats["correspondence_constraint_rules"] += len(rules)
        if not rules:
            return
        refuted = []
        for nscope, scope in enumerate(scopes):
            now = time.process_time()
            if now >= end:
                return
            scope_end = min(end, now + (end - now) / max(1, len(scopes) - nscope))
            wanted = {k.in_types[a] for k, a, _, _ in rules}
            sample_inputs = [tuple(p[2][j] for j in scope) for p in points]

            restart = False
            ordered_types = [t for t in (B, I, L) if t in wanted]
            for type_index, out_type in enumerate(ordered_types):
                matches = []

                def accept(vector):
                    stats["correspondence_functions"] += 1
                    if None in vector:
                        return False
                    matches[:] = [(k, a, fixed) for k, a, fixed, fibres in rules
                                  if k.in_types[a] == out_type and all(v in fs for v, fs in zip(vector, fibres))]
                    return bool(matches)

                # Public accept callback: no Q3 _keep/_pool/private-policy override.
                type_end = min(scope_end, time.process_time() + max(0, scope_end - time.process_time()) /
                               (len(ordered_types) - type_index))
                search = sc.GSearch(LIB, tuple(types[j] for j in scope), out_type,
                                    [(x, 0) for x in sample_inputs], type_end,
                                    consts=consts, accept=accept)
                answer, _ = search.run()
                stats["mapping_search_candidates"] += search.n
                if answer is None:
                    continue
                ast = answer[1]
                mapping = {j: ("v", old) for j, old in enumerate(scope)}
                bound = substitute(ast, len(scope), len(types), mapping)
                for kernel, active, fixed in matches:
                    bindings = {**fixed, active: bound}
                    body = substitute(kernel.ast, len(kernel.in_types), len(types), bindings)
                    check(kernel, stage, bindings)
                    bad = [p for p in stage["points"] if p not in points and _eval(body, p[2]) != p[3]]
                    if bad:
                        refuted.extend(bad[:8])
                        counterexamples.append({"kernel_key": kernel.key, "source_role": active,
                                                "target_state_digest": digest(bad[0][2]),
                                                "reason": "correspondence_refuted_by_authorized_TRAIN"})
                        restart = True
                if restart:
                    break
            if restart:
                break

        fresh = [p for p in refuted if p not in points]
        if not fresh:
            return
        points += fresh[:8]
