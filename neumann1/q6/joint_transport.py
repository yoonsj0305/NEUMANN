"""Joint SOURCE-role correspondence using the unchanged Q3 enumerator.

Unlike v1, all roles may be composed, every kernel receives turns, and the
preimage domain consists of executable target expressions (no integer window).
The join is exact within the recorded finite expression pool. It is not a
proof of target semantics or a second learned discovery policy.
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
import heapq
import itertools
import time

from neumann1 import discovery_core as dc, invention_core as ic, spec_core as sc
from .contracts import digest, result
from .transport import (LIB, I, B, L, _columns, _eval, _fit_method, _stages,
                        checked_type, substitute, tup)

POOL_LIMIT = 96
POOL_LEVEL = 6
POOL_CANDIDATES = 6000
SAMPLE_LIMIT = 16


@dataclass(frozen=True)
class Expression:
    ast: tuple
    vector: tuple

    @property
    def compound(self):
        return self.ast[0] not in ("v", "k")


def _sample(points, limit=SAMPLE_LIMIT):
    # Round-robin over original examples; both output labels are represented
    # before taking more instances of a frequent label. No task IDs are used.
    buckets = {}
    for p in points:
        buckets.setdefault((p[0], digest(p[3])), deque()).append(p)
    out = []
    while buckets and len(out) < limit:
        for key in list(buckets):
            out.append(buckets[key].popleft())
            if not buckets[key]:
                del buckets[key]
            if len(out) == limit:
                break
    return out


def expression_pool(types, points, consts, end, stats):
    """Collect Q3's public FSearch.offer results; never replace its internals."""
    pools = {t: {} for t in (I, B, L)}

    def add(ast, typ, vec):
        if None in vec:
            return
        prior = pools[typ].get(vec)
        if prior is None and len(pools[typ]) >= POOL_LIMIT:
            return
        if prior is None or (ic.size(ast), repr(ast)) < (ic.size(prior.ast), repr(prior.ast)):
            pools[typ][vec] = Expression(ast, tuple(vec))

    for typ, asts in _columns(types, consts).items():
        for ast in asts:
            add(ast, typ, tuple(_eval(ast, p[2]) for p in points))
    # Small scopes keep independent features discoverable when the full state
    # has many columns. This schedule is based only on position and type.
    scopes = [(j,) for j in range(len(types))]
    scopes.append(tuple(range(len(types))))
    scopes = list(dict.fromkeys(scopes))
    for index, scope in enumerate(scopes):
        now = time.process_time()
        if now >= end:
            break
        scope_end = now + (end - now) / (len(scopes) - index)
        mapping = {j: ("v", old) for j, old in enumerate(scope)}

        def offer(entry, typ):
            ast = substitute(entry.ast(), len(scope), len(types), mapping)
            add(ast, typ, entry.vec)

        search = dc.FSearch(LIB, tuple(types[j] for j in scope),
                            [tuple(p[2][j] for j in scope) for p in points],
                            scope_end, consts, ic.uniform_costs(), (I, B, L), offer)
        search.max_level = POOL_LEVEL
        search.budget = POOL_CANDIDATES
        search.run()
        stats["q3_expression_candidates"] += search.n
    return {t: sorted(pool.values(), key=lambda e: (ic.size(e.ast), repr(e.ast)))
            for t, pool in pools.items()}


def _products(options):
    """Lazy Cartesian product ordered by total expression size."""
    if not options:
        yield ()
        return
    if any(not o for o in options):
        return
    zero = (0,) * len(options)
    weight = lambda ix: sum(ic.size(options[j][k].ast) for j, k in enumerate(ix))
    heap, seen = [(weight(zero), zero)], {zero}
    while heap:
        _, ix = heapq.heappop(heap)
        yield tuple(options[j][k] for j, k in enumerate(ix))
        for j in range(len(ix)):
            nxt = ix[:j] + (ix[j] + 1,) + ix[j + 1:]
            if nxt[j] < len(options[j]) and nxt not in seen:
                seen.add(nxt)
                heapq.heappush(heap, (weight(nxt), nxt))


def relational_bindings(kernel, pools, points, end, stats, max_compound=3):
    """Semijoin source execution fibres against all target-role expressions.

    Other roles are expressions too. Bitset intersection retains one consistent
    expression for the active role across every observation, including repeated
    uses inside the SOURCE method. Relation evaluations are memoized by actual
    argument values. Partial/undefined SOURCE execution never matches.
    """
    opts = [pools[t] for t in kernel.in_types]
    if any(not x for x in opts):
        return
    active = max(range(len(opts)), key=lambda j: len(opts[j]))
    other = [j for j in range(len(opts)) if j != active]
    active_opts = opts[active]
    compound_mask = sum((1 << j) for j, e in enumerate(active_opts) if e.compound)
    all_mask = (1 << len(active_opts)) - 1
    groups = []
    for pindex in range(len(points)):
        group = {}
        for j, entry in enumerate(active_opts):
            group[entry.vector[pindex]] = group.get(entry.vector[pindex], 0) | (1 << j)
        groups.append(group)
    goal_counts = Counter(digest(p[3]) for p in points)
    order = sorted(range(len(points)), key=lambda j: (goal_counts[digest(points[j][3])], j))
    fn = ic.compile_ast(kernel.ast, len(kernel.in_types), LIB)
    cache = {}
    for fixed in _products([opts[j] for j in other]):
        if time.process_time() >= end:
            return
        stats["joint_fixed_role_tuples"] += 1
        ncompound = sum(e.compound for e in fixed)
        if ncompound > max_compound:
            continue
        mask = all_mask
        # Type-only mappings are separately enumerated by the same schedule.
        if ncompound == 0:
            mask &= compound_mask
        if ncompound == max_compound:
            mask &= all_mask ^ compound_mask
        for point_index in order:
            if not mask:
                break
            args = [None] * len(opts)
            for j, entry in zip(other, fixed):
                args[j] = entry.vector[point_index]
            good = 0
            for value, ids in groups[point_index].items():
                if not (mask & ids):
                    continue
                args[active] = value
                key = tuple(args)
                if key not in cache:
                    if not (stats["source_relation_evaluations"] & 63) and time.process_time() >= end:
                        return
                    try:
                        cache[key] = fn(key)
                    except ic.Fail:
                        cache[key] = None
                    stats["source_relation_evaluations"] += 1
                observed = cache[key]
                goal = points[point_index][3]
                if type(observed) is type(goal) and observed == goal:
                    good |= ids
            mask &= good
        while mask:
            bit = mask & -mask
            mask ^= bit
            j = bit.bit_length() - 1
            bindings = {role: e.ast for role, e in zip(other, fixed)}
            bindings[active] = active_opts[j].ast
            yield bindings
        # Round-robin fairness: a failed tuple also yields control to the caller.
        yield None


def typed_bindings(kernel, pools, points, end, stats, max_compound=3):
    """Equal-rights control: same pools and full multi-role Cartesian language.

    No relation-table pruning; this is strictly stronger than v1 type-only T.
    """
    options = [pools[t] for t in kernel.in_types]
    for entries in _products(options):
        if time.process_time() >= end:
            return
        if 0 < sum(e.compound for e in entries) <= max_compound:
            stats["typed_composition_tuples"] += 1
            yield {j: e.ast for j, e in enumerate(entries)}
        else:
            yield None


def joint_transport(task, inventory, *, cap_s=3, mode="Joint", fallback=None):
    """TRAIN-only bounded transport; all original-semantic tests remain due.

    Joint: relational join; OneRole: <=1 compound; TypeCompose: equal synthesis
    rights without relational pruning. No mode accepts receiver TEST labels.
    """
    if task.get("test"):
        raise ValueError("Q6 inference refuses hidden TEST observations")
    if mode not in ("Joint", "OneRole", "TypeCompose"):
        raise ValueError("unsupported joint correspondence mode")
    start = time.process_time()
    end = start + max(0, cap_s)
    stats, rejected, counterexamples = Counter(), [], []
    phases = Counter()
    od = digest({k: task[k] for k in ("in_types", "out_type", "train")})
    consts = ic.data_constants(task["train"])
    stages = _stages(task)
    answer, source, correspondence, via = None, None, None, None

    def check(kernel, stage, bindings):
        nonlocal answer, source, correspondence, via
        c0 = time.process_time()
        body = substitute(kernel.ast, len(kernel.in_types), len(stage["in_types"]), bindings)
        checked_type(body, tuple(stage["in_types"]))
        stats["reconstructed_candidates"] += 1
        if _fit_method((stage["kind"], body), task):
            answer, source = (stage["kind"], body), kernel.artifact_id
            count = sum(ast[0] not in ("v", "k") for ast in bindings.values())
            via = "joint_transport" if count > 1 else "compound_transport" if count else "type_only"
            correspondence = {"kernel": kernel.ast, "source_fragment_path": kernel.path,
                              "source_role_types": kernel.in_types, "target_state_types": stage["in_types"],
                              "bindings": {str(j): a for j, a in sorted(bindings.items())},
                              "compound": bool(count), "compound_role_count": count}
        else:
            stats["rejected_candidates"] += 1
            rejected.append({"source_artifact_id": kernel.artifact_id, "kernel_key": kernel.key,
                             "bindings": bindings, "reason": "authorized_TRAIN_mismatch"})
        phases["reconstruct_and_train_verify"] += time.process_time() - c0
        return answer is not None

    c0 = time.process_time()
    replay_end = start + .08 * cap_s
    for aid, method in inventory["methods"]:
        if time.process_time() >= replay_end:
            break
        if tuple(method["input_types"]) == tuple(task["in_types"]) and method["output_type"] == task["out_type"]:
            candidate = method["kind"], tup(method["ast"])
            stats["whole_program_replays"] += 1
            if _fit_method(candidate, task):
                answer, source, via = candidate, aid, "replay"
                break
    phases["whole_program_memory"] += time.process_time() - c0
    for sindex, stage in enumerate(stages):
        if answer is not None or time.process_time() >= start + .90 * cap_s:
            break
        stage_end = time.process_time() + (start + .90 * cap_s - time.process_time()) / (len(stages) - sindex)
        kernels = [k for k in inventory["kernels"] if k.out_type == stage["out_type"]]
        if not kernels:
            continue
        # First, the unchanged finite direct-role language, fairly interleaved.
        cols = _columns(stage["in_types"], consts)
        direct = deque((k, iter(itertools.product(*(cols[t] for t in k.in_types)))) for k in kernels)
        direct_end = time.process_time() + .10 * (stage_end - time.process_time())
        while direct and time.process_time() < direct_end and answer is None:
            k, iterator = direct.popleft()
            bs = next(iterator, None)
            if bs is None:
                continue
            stats["direct_role_candidates"] += 1
            check(k, stage, dict(enumerate(bs)))
            direct.append((k, iterator))
        if answer is not None:
            break
        points = _sample(stage["points"])
        for round_index in range(2):
            if not points or time.process_time() >= stage_end:
                break
            c0 = time.process_time()
            pool_end = time.process_time() + .30 * (stage_end - time.process_time())
            pools = expression_pool(tuple(stage["in_types"]), points, consts, pool_end, stats)
            phases["expression_pool"] += time.process_time() - c0
            stats["expression_pools"] += 1
            stats["distinct_expressions"] += sum(map(len, pools.values()))
            fn = typed_bindings if mode == "TypeCompose" else relational_bindings
            active = deque((k, fn(k, pools, points, stage_end, stats,
                                 max_compound=1 if mode == "OneRole" else 3)) for k in kernels)
            refuted = []
            c0 = time.process_time()
            verification_before = phases["reconstruct_and_train_verify"]
            while active and time.process_time() < stage_end and answer is None:
                k, iterator = active.popleft()
                stats["kernel_scheduling_turns"] += 1
                bindings = next(iterator, "exhausted")
                if bindings == "exhausted":
                    continue
                active.append((k, iterator))
                if bindings is None:
                    continue
                if check(k, stage, bindings):
                    break
                body = substitute(k.ast, len(k.in_types), len(stage["in_types"]), bindings)
                bad = [p for p in stage["points"] if p not in points and _eval(body, p[2]) != p[3]]
                if bad:
                    refuted.extend(bad[:8])
                    counterexamples.append({"kernel_key": k.key, "target_state_digest": digest(bad[0][2]),
                                            "reason": "joint_correspondence_refuted_by_authorized_TRAIN"})
            phases["joint_matching"] += time.process_time() - c0 - (phases["reconstruct_and_train_verify"] - verification_before)
            if answer is not None:
                break
            fresh = [p for p in refuted if p not in points]
            if not fresh:
                break
            points += fresh[:8]
            stats["counterexample_restarts"] += 1
    if answer is None and fallback is not None and time.process_time() < end:
        c0 = time.process_time()
        raw = fallback(max(.001, end - time.process_time()))
        answer = raw.get("sol")
        via = "q3_fallback" if answer else None
        stats["fallback_candidates"] += raw.get("candidates", 0)
        phases["q3_fallback"] += time.process_time() - c0
    elapsed = time.process_time() - start
    # Timer nesting is removed above. Everything not in a named interval is
    # charged as controller/loop overhead, never silently counted as zero.
    phases["controller_and_direct_schedule"] = max(0.0, elapsed - sum(phases.values()))
    return result(od, status="TRAIN_CONSISTENT" if answer else "UNKNOWN", source=source,
                  correspondence=correspondence, representation={"kind": answer[0]} if answer else None,
                  method={"kind": answer[0], "ast": answer[1]} if answer else None,
                  obligations=["finite admitted SOURCE evidence, not universal source validity",
                               "joint state correspondence checked on authorized TRAIN",
                               "independent original receiver TEST remains required"],
                  counterexamples=counterexamples, reason=None if answer else "no_joint_verified_correspondence",
                  cost={"total_cpu_seconds": elapsed, "phase_cpu_seconds": dict(phases),
                        "counts": dict(stats), "energy_joules": None, "monetary_cost": None}) | {
                      "via": via, "rejected_candidate_ledger": rejected}
