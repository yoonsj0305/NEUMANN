"""Independent, post-primary analysis of actual recorded transport witnesses.

No discovery/repair or new hidden evaluation. Exhaust the declared finite
replay/type-only class and audit the already frozen correspondence.
"""
from __future__ import annotations
import itertools
import json
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q6"))
from source_study import OUT, fold, inventory_for
from reference import execute
from neumann1 import invention_core as ic
from neumann1.q6.transport import substitute, checked_type, tup
from neumann1.q6.contracts import digest


def exact(sol, pairs):
    return all(execute(sol, tup(i)) == tup(o) for i, o in pairs)


def nodes(ast, path=()):
    yield path, ast
    if ast[0] not in ("v", "k"):
        for i, c in enumerate(ast[1:]):
            yield from nodes(c, path + (i,))


def replace(ast, path, replacement):
    if not path:
        return replacement
    out = list(ast)
    out[path[0] + 1] = replace(out[path[0] + 1], path[1:], replacement)
    return tuple(out)


def main():
    path = OUT / "witness_audit.json"
    if path.exists():
        raise SystemExit("preserve first witness audit")
    result = json.loads((OUT / "result.json").read_text())
    visible = {t["id"]: t for t in json.loads((ROOT.parent / "q6_source_v1_train_cache.json").read_text())}
    artifacts = {a["artifact_id"]: a for a in json.loads((OUT / "source_artifacts.json").read_text())}
    reports = []
    for row in result["grades"]:
        if row["arm"] != "C" or row["id"] not in result["compound_attributed_exclusive"]:
            continue
        c0 = time.process_time()
        t = visible[row["id"]]
        train = [(tup(i), tup(o)) for i, o in t["train"]]
        c = row["candidate_correspondence"]
        k = tup(c["kernel"])
        bindings = {int(j): tup(a) for j, a in c["bindings"].items()}
        n = len(c["target_state_types"])
        body = substitute(k, len(c["source_role_types"]), n, bindings)
        assert body == tup(row["sol"][1])
        source = artifacts[row["source_artifact_id"]]
        assert fold(source["provenance"]["source_id"]) != fold(row["id"])
        inv = inventory_for(fold(row["id"]))
        replay_fits = []
        for aid, m in inv["methods"]:
            if exact((m["kind"], tup(m["ast"])), train):
                replay_fits.append(aid)
        # Exhaust this witness's applicable type-only fragment class without
        # the original runtime cutoff. No hidden TEST values are read.
        types = tuple(c["target_state_types"])
        cols = {typ: [("v", j) for j, q in enumerate(types) if q == typ] for typ in ("I", "B", "L")}
        cols["I"] += [("k", j) for j in sorted(set(range(-2, 10)) | set(ic.data_constants(train)))]
        tested, type_fits = 0, []
        for kernel in inv["kernels"]:
            if kernel.out_type != "B":
                continue
            for args in itertools.product(*(cols[typ] for typ in kernel.in_types)):
                candidate = substitute(kernel.ast, len(kernel.in_types), n, dict(enumerate(args)))
                tested += 1
                if exact((row["sol"][0], candidate), train):
                    type_fits.append({"kernel_key": kernel.key, "bindings": args})
        # Check source-kernel execution composed with the learned map against
        # the transformed AST using only the independent literal interpreter.
        rng = random.Random(745)
        commute, undefined = 0, 0
        for _ in range(4096):
            state = tuple(tuple(rng.randint(-4, 20) for _ in range(rng.randint(0, 8))) if typ == "L"
                          else bool(rng.getrandbits(1)) if typ == "B" else rng.randint(-4, 20) for typ in types)
            values = tuple(execute(("ast", bindings[j]), state) for j in range(len(bindings)))
            if any(v is None for v in values):
                undefined += 1
                continue
            expected = execute(("ast", k), values)
            observed = execute(("ast", body), state)
            assert expected == observed
            commute += 1
        knockouts = []
        for j, bound in bindings.items():
            if bound[0] in ("v", "k"):
                continue
            for child in bound[1:]:
                if checked_type(child, types) != c["source_role_types"][j]:
                    continue
                bs = {**bindings, j: child}
                candidate = substitute(k, len(bs), n, bs)
                knockouts.append({"kind": "composed_binding_operator_removed", "role": j,
                                   "replacement": child, "TRAIN_rejected": not exact((row["sol"][0], candidate), train)})
        mutations = []
        for at, node in nodes(k):
            if node[0] in ("v", "k"):
                continue
            old = ic.base_library()[node[0]]
            for primitive in ic.base_library().values():
                if primitive.name == old.name or primitive.ret != old.ret or primitive.params != old.params:
                    continue
                mutated = replace(k, at, (primitive.name,) + node[1:])
                candidate = substitute(mutated, len(bindings), n, bindings)
                mutations.append({"source_path": at, "old": old.name, "replacement": primitive.name,
                                  "TRAIN_rejected": not exact((row["sol"][0], candidate), train)})
        reports.append({"receiver": row["id"], "source": source["provenance"]["source_id"],
                        "source_artifact_id": row["source_artifact_id"], "source_kernel": k,
                        "recorded_correspondence": bindings, "frozen_AST_reconstruction_identical": True,
                        "donor_fold_excludes_receiver": True,
                        "whole_program_replay_TRAIN_fits": replay_fits,
                        "type_only_applications_exhaustively_tested": tested, "type_only_TRAIN_fits": type_fits,
                        "commuting_relation_samples_passed": commute, "undefined_mapping_samples_skipped": undefined,
                        "binding_removal_controls": knockouts, "type_preserving_source_operator_controls": mutations,
                        "cpu_seconds": time.process_time() - c0,
                        "scope": "post-primary finite replay/type-class audit and reconstruction checks; TRAIN only, not fresh capability or universal TARGET equivalence"})
    path.write_text(json.dumps({"witnesses": reports, "receiver_TEST_read": False}, indent=2) + "\n")
    print(json.dumps({"witnesses": [{k: v for k, v in r.items() if k not in ("recorded_correspondence", "source_kernel")} for r in reports]}, indent=2))


if __name__ == "__main__":
    main()
