"""Q3/Q6 FIRST: one invention core, mixed SOURCE, three independent TARGETs.

Pre-registration: docs/research/Q3Q6_INVENTION_CORE_PREREG_2026_11_11.md

  register <bigbench> <ec> <oeis>   metadata only (blobless clones)
  train    <bigbench> <oeis>        opens SOURCE files only, freezes the core
  evaluate <bigbench> <ec> <oeis>   opens TARGET files, single FIRST run

Families (independent authors, pinned commits):
  rule  google/BIG-bench list_functions c001..c250 (Rule, Piantadosi, Tenenbaum)
  dc    ellisk42/ec data/list_tasks.json           (DreamCoder list tasks)
  oeis  oeis/oeisdata seq/A000/*.seq                (OEIS contributors)

No task content is written to the repository (BIG-bench canary policy);
only ids, git blob hashes, outcomes and the system's own programs.
"""
from __future__ import annotations
import hashlib, json, math, pathlib, re, subprocess, sys, time
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
from multiprocessing import Pool
from neumann1 import invention_core as ic
import sequence_specialist

SALT = "neumann-invention-first-v1"
PINS = {"bigbench": "092b196c1f8f14a54bbc62f24759d43bde46dd3b",
        "ec": "cb0e63f5c33cd2de360b791038b0f5272750270e",
        "oeis": "2066359a24c83163fd067fc54d1d20d143c5be69"}
RULE_DIR = "bigbench/benchmark_tasks/list_functions"
DC_FILE = "data/list_tasks.json"
OEIS_DIR = "seq/A000"
REGISTRY = "docs/experiments/invention_first_registry.json"
FROZEN = "docs/experiments/results/invention_core_frozen.json"
RESULT = "docs/experiments/results/invention_first_result.json"
CODE = ("neumann1/invention_core.py", "research/q3/invention_first.py",
        "research/q3/sequence_specialist.py")
N_TARGET = 200000            # candidate budget per TARGET task per arm
N_STRONG = 4 * N_TARGET      # classical baseline given 4x compute
N_SOURCE = 600000            # SOURCE wake budget per task per round
ROUNDS = 3
OEIS_SOURCE, OEIS_TARGET = 250, 250
SEQ_TRAIN, SEQ_TEST = 14, 6
WORKERS = 4


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"))


def order(ids, family):
    return sorted(ids, key=lambda i: sha256(("%s:%s:%s" % (SALT, family, i)).encode()))


def git(clone, *args):
    return subprocess.run(["git", "-C", str(clone)] + list(args), check=True,
                          capture_output=True, text=True).stdout


def tree(clone, prefix):
    out = {}
    for line in git(clone, "ls-tree", "-r", "FETCH_HEAD", prefix).splitlines():
        meta, path = line.split("\t", 1)
        out[path] = meta.split()[2]
    return out


def code_shas():
    return {p: sha256(pathlib.Path(p).read_bytes()) for p in CODE}


def blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def read_blobs(clone, paths, registry_blobs):
    """Fetch exactly these files from the pinned commit and verify them."""
    out = {}
    for i in range(0, len(paths), 100):
        chunk = paths[i:i + 100]
        git(clone, "checkout", "FETCH_HEAD", "--", *chunk)
    for p in paths:
        b = (pathlib.Path(clone) / p).read_bytes()
        if blob_sha(b) != registry_blobs[p]:
            raise SystemExit("BLOB_MISMATCH " + p)
        out[p] = b
    return out


# ------------------------------------------------------------------ splits
def splits(reg):
    rule_ids = sorted(reg["rule_blobs"])
    rule = order(rule_ids, "rule")
    oeis = order(sorted(reg["oeis_blobs"]), "oeis")
    return {"rule_source": sorted(rule[:len(rule) // 2]),
            "rule_target": sorted(rule[len(rule) // 2:]),
            "oeis_source": sorted(oeis[:OEIS_SOURCE]),
            "oeis_target": sorted(oeis[OEIS_SOURCE:OEIS_SOURCE + OEIS_TARGET]),
            "oeis_reserved_unopened": len(oeis) - OEIS_SOURCE - OEIS_TARGET}


# ----------------------------------------------------------------- loaders
def _val(x):
    if isinstance(x, str):
        x = json.loads(x)
    if isinstance(x, bool):
        return x
    if isinstance(x, list):
        return tuple(int(v) for v in x)
    return int(x)


def split_examples(ex):
    n = len(ex)
    k = 8 if n >= 12 else math.ceil(2 * n / 3)
    return ex[:k], ex[k:]


def load_rule(path, raw):
    d = json.loads(raw)
    ex = []
    for e in d["examples"]:
        tgt = e["target"]
        if isinstance(tgt, list) and tgt and isinstance(tgt[0], str):
            tgt = tgt[0]
        ex.append(((_val(e["input"]),), _val(tgt)))
    tr, te = split_examples(ex)
    return {"id": "rule/" + path.split("/")[-2], "in_types": ["L"],
            "out_type": "L", "train": tr, "test": te}


TP = {"int": "I", "bool": "B", "list-of-int": "L"}


def load_dc(raw):
    out = []
    for i, item in enumerate(json.loads(raw)):
        tid = "dc/%03d" % i
        ti, to = item["type"]["input"], item["type"]["output"]
        if ti not in ("int", "list-of-int") or to not in TP:
            out.append({"id": tid, "unsupported": "%s->%s" % (ti, to)})
            continue
        ex = []
        for e in item["examples"]:
            i_, o_ = e["i"], e["o"]
            ex.append(((tuple(i_) if isinstance(i_, list) else int(i_),),
                       bool(o_) if to == "bool" else
                       tuple(o_) if isinstance(o_, list) else int(o_)))
        tr, te = split_examples(ex)
        out.append({"id": tid, "in_types": [TP[ti]], "out_type": TP[to],
                    "train": tr, "test": te})
    return out


def load_oeis(path, raw):
    aid = path.split("/")[-1].split(".")[0]
    terms, offset = [], 0
    for line in raw.decode("utf-8", "replace").splitlines():
        if line[:2] in ("%S", "%T", "%U"):
            terms += [t for t in line.split(None, 2)[2].replace(" ", "").split(",") if t]
        elif line[:2] == "%O":
            m = re.match(r"\s*(-?\d+)", line.split(None, 2)[2])
            offset = int(m.group(1)) if m else 0
    try:
        vals = [int(t) for t in terms]
    except ValueError:
        return {"id": "oeis/" + aid, "unsupported": "non-integer terms"}
    if len(vals) < SEQ_TRAIN + SEQ_TEST:
        return {"id": "oeis/" + aid, "unsupported": "fewer than 20 terms"}
    ex = [((offset + i,), vals[i]) for i in range(SEQ_TRAIN + SEQ_TEST)]
    return {"id": "oeis/" + aid, "in_types": ["I"], "out_type": "I",
            "train": ex[:SEQ_TRAIN], "test": ex[SEQ_TRAIN:]}


# ---------------------------------------------------------------- register
def register(bigbench, ec, oeis):
    rule = {p: s for p, s in tree(bigbench, RULE_DIR).items()
            if re.search(r"/c\d{3}/task\.json$", p)}
    dc = tree(ec, DC_FILE)
    seq = {p: s for p, s in tree(oeis, OEIS_DIR).items() if p.endswith(".seq")}
    if len(rule) != 250 or len(dc) != 1:
        raise SystemExit("unexpected registry size")
    reg = {"schema": "neumann.q3q6.invention-first-registry.v1", "salt": SALT,
           "pins": PINS, "rule_blobs": rule, "dc_blob": dc, "oeis_blobs": seq,
           "budgets": {"target": N_TARGET, "strong_classical": N_STRONG,
                       "source_wake": N_SOURCE, "rounds": ROUNDS},
           "target_bytes_opened": False}
    reg["splits"] = splits(reg)
    reg["registry_sha256"] = sha256(canon(reg).encode())
    pathlib.Path(REGISTRY).write_text(json.dumps(reg, indent=0, sort_keys=True))
    s = reg["splits"]
    print("REGISTERED rule %d/%d  oeis %d/%d (+%d reserved)  dc 1 file  sha %s" % (
        len(s["rule_source"]), len(s["rule_target"]), len(s["oeis_source"]),
        len(s["oeis_target"]), s["oeis_reserved_unopened"], reg["registry_sha256"]))


def load_registry():
    reg = json.loads(pathlib.Path(REGISTRY).read_text())
    sig = reg.pop("registry_sha256")
    if sha256(canon(reg).encode()) != sig:
        raise SystemExit("REGISTRY_MUTATED")
    return reg, sig


# ------------------------------------------------------------------- train
def train(bigbench, oeis):
    reg, sig = load_registry()
    s = reg["splits"]
    rb = read_blobs(bigbench, s["rule_source"], reg["rule_blobs"])
    ob = read_blobs(oeis, s["oeis_source"], reg["oeis_blobs"])
    tasks = [load_rule(p, rb[p]) for p in s["rule_source"]]
    tasks += [load_oeis(p, ob[p]) for p in s["oeis_source"]]
    usable = [t for t in tasks if "unsupported" not in t]
    print("SOURCE tasks %d usable %d" % (len(tasks), len(usable)), flush=True)
    t0 = time.perf_counter()
    with Pool(WORKERS) as pool:
        core = ic.train(usable, rounds=ROUNDS, budget=N_SOURCE, pool=pool,
                        log=lambda m: print(m, flush=True))
    # ablation prior: same experience, but no invented symbols
    base = ic.base_library()
    groups = {}
    by_id = {t["id"]: t for t in usable}
    flat = []
    for tid, (ast, in_types, out_type) in zip(sorted(core["solved"]), core["memory"]):
        flat.append((ast, in_types))
        groups.setdefault(ic.sig_key(by_id[tid]), []).append((ast, in_types))
    costs_base = {"*": ic.learn_costs(flat, base)}
    for k, progs in groups.items():
        if len(progs) >= 8:
            costs_base[k] = ic.learn_costs(progs, base)
    for c in costs_base.values():
        c["$mem"] = 3
    frozen = {"schema": "neumann.q3q6.invention-core-frozen.v1",
              "registry_sha256": sig, "code_sha256": code_shas(),
              "spec": core["spec"], "costs": core["costs"],
              "costs_base_only": costs_base, "memory": core["memory"],
              "source_solved": {k: ic.show(v) for k, v in core["solved"].items()},
              "source_tasks": len(tasks), "source_usable": len(usable),
              "history": core["history"],
              "train_wall_s": round(time.perf_counter() - t0, 1),
              "target_bytes_opened": False}
    frozen["core_sha256"] = sha256(canon(frozen).encode())
    pathlib.Path(FROZEN).write_text(json.dumps(frozen, indent=0, sort_keys=True))
    print("FROZEN core %s : %d inventions, %d/%d source solved, %.0fs" % (
        frozen["core_sha256"], len(core["spec"]), len(core["solved"]),
        len(usable), frozen["train_wall_s"]))
    for name, ret, params, body in core["spec"]:
        print("  %s : %s" % (name, ic.show(ic._tup(body))))


# ---------------------------------------------------------------- evaluate
def mcnemar(b, c):
    """Exact two-sided p for b = C-only wins, c = other-only wins."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def used_inventions(ast, acc):
    if isinstance(ast, (list, tuple)) and ast and isinstance(ast[0], str):
        if re.fullmatch(r"f\d+", ast[0]):
            acc.add(ast[0])
        for c in ast[1:]:
            used_inventions(c, acc)
    return acc


def evaluate(bigbench, ec, oeis):
    reg, sig = load_registry()
    frozen = json.loads(pathlib.Path(FROZEN).read_text())
    csig = frozen.pop("core_sha256")
    if sha256(canon(frozen).encode()) != csig or frozen["registry_sha256"] != sig:
        raise SystemExit("FROZEN_CORE_MUTATED")
    if frozen["code_sha256"] != code_shas():
        raise SystemExit("CODE_CHANGED_AFTER_FREEZE")
    s = reg["splits"]
    rb = read_blobs(bigbench, s["rule_target"], reg["rule_blobs"])
    db = read_blobs(ec, [DC_FILE], reg["dc_blob"])
    ob = read_blobs(oeis, s["oeis_target"], reg["oeis_blobs"])
    fams = {"rule": [load_rule(p, rb[p]) for p in s["rule_target"]],
            "dc": load_dc(db[DC_FILE]),
            "oeis": [load_oeis(p, ob[p]) for p in s["oeis_target"]]}
    spec = [tuple(x) for x in frozen["spec"]]
    memory = [(ic._tup(a), tuple(i), o) for a, i, o in frozen["memory"]]
    un = ic.untrained_costs()
    lib_inv = ic.library_from_spec(spec)
    un_inv = {"*": ic.learn_costs([], lib_inv)}
    un_inv["*"]["$mem"] = 3
    arms = {"A": ((), un, None, N_TARGET),
            "A4": ((), un, None, N_STRONG),
            "B": ((), un, memory, N_TARGET),
            "C": (spec, frozen["costs"], memory, N_TARGET)}
    secondary = {"C_no_inventions": ((), frozen["costs_base_only"], memory, N_TARGET),
                 "C_no_learned_prior": (spec, un_inv, memory, N_TARGET)}
    report = {"schema": "neumann.q3q6.invention-FIRST.v1", "registry_sha256": sig,
              "core_sha256": csig, "families": {}}
    t_all = time.perf_counter()
    with Pool(WORKERS) as pool:
        for fam, tasks in fams.items():
            usable = [t for t in tasks if "unsupported" not in t]
            rows = {t["id"]: ({"unsupported": t["unsupported"]} if "unsupported" in t
                              else {}) for t in tasks}
            todo = dict(arms)
            if fam == "rule":
                todo.update(secondary)
            wall = {}
            for arm, (sp, costs, mem, budget) in todo.items():
                t0 = time.perf_counter()
                for r in ic.run_arm(usable, sp, costs, budget, mem, pool):
                    rows[r["id"]][arm] = {
                        "fit": r["fit"], "solved": r["solved"], "via": r["via"],
                        "candidates": r["candidates"], "seconds": r["seconds"],
                        "program": ic.show(ic._tup(r["ast"])) if r["ast"] else None,
                        "inventions": sorted(used_inventions(r["ast"], set())) if r["ast"] else []}
                wall[arm] = round(time.perf_counter() - t0, 1)
                print(fam, arm, "solved", sum(rows[t["id"]][arm]["solved"] for t in usable),
                      "/", len(tasks), "wall", wall[arm], flush=True)
            if fam == "oeis":
                for t in usable:
                    pred = sequence_specialist.predict([o for _, o in t["train"]], SEQ_TEST)
                    rows[t["id"]]["D"] = {"solved": pred == [o for _, o in t["test"]],
                                          "fit": pred is not None}
            report["families"][fam] = {"tasks": len(tasks), "usable": len(usable),
                                       "wall_s": wall, "rows": rows}
    report["summary"], report["verdict"] = summarize(report, frozen)
    report["wall_s"] = round(time.perf_counter() - t_all, 1)
    pathlib.Path(RESULT).write_text(json.dumps(report, indent=0, sort_keys=True))
    print(json.dumps({"summary": report["summary"], "verdict": report["verdict"]}, indent=1))


def summarize(report, frozen):
    summary, verdict = {}, {}
    excl_inv = set()
    for fam, data in report["families"].items():
        rows = [r for r in data["rows"].values() if "unsupported" not in r]
        arms = [a for a in ("A", "A4", "B", "C", "C_no_inventions",
                            "C_no_learned_prior", "D") if rows and a in rows[0]]
        s = {"tasks": data["tasks"], "usable": data["usable"]}
        for a in arms:
            s[a] = {"solved": sum(r[a]["solved"] for r in rows),
                    "fit": sum(r[a]["fit"] for r in rows)}
            if "candidates" in rows[0][a]:
                s[a]["candidates"] = sum(r[a]["candidates"] for r in rows)
                s[a]["cpu_seconds"] = round(sum(r[a]["seconds"] for r in rows), 1)
        rivals = [a for a in ("A", "A4", "B", "D") if a in arms]
        excl = [r for r in rows if r["C"]["solved"] and not any(r[a]["solved"] for a in rivals)]
        s["C_exclusive_vs_" + "_".join(rivals)] = len(excl)
        s["lost_by_C_but_solved_by_A_or_B"] = sum(
            (r["A"]["solved"] or r["B"]["solved"]) and not r["C"]["solved"] for r in rows)
        for r in excl:
            excl_inv.update(r["C"]["inventions"])
        for other in ("A", "B", "A4"):
            b = sum(r["C"]["solved"] and not r[other]["solved"] for r in rows)
            c = sum(r[other]["solved"] and not r["C"]["solved"] for r in rows)
            s["C_vs_" + other] = {"C_only": b, other + "_only": c,
                                  "mcnemar_p": round(mcnemar(b, c), 6)}
        both = [r for r in rows if r["A"]["solved"] and r["C"]["solved"]]
        if both:
            s["search_cost_on_tasks_both_solve"] = {
                "tasks": len(both),
                "A_candidates": sum(r["A"]["candidates"] for r in both),
                "C_candidates": sum(r["C"]["candidates"] for r in both)}
        summary[fam] = s
        ok = (s["C"]["solved"] > s["A"]["solved"] and s["C"]["solved"] > s["B"]["solved"]
              and s["C_vs_A"]["mcnemar_p"] < 0.05 and s["C_vs_B"]["mcnemar_p"] < 0.05
              and len(excl) >= 5)
        verdict["P2_" + fam] = "PASS" if ok else "FAIL"
        verdict["P3_iso_capability_4x_" + fam] = (
            "C_BEATS_CLASSICAL_AT_4X_COMPUTE" if s["C"]["solved"] > s["A4"]["solved"]
            else "NOT_SHOWN")
    summary["inventions_in_frozen_core"] = len(frozen["spec"])
    summary["inventions_used_in_exclusive_wins"] = sorted(excl_inv)
    verdict["P1_invention"] = ("PASS" if len(frozen["spec"]) >= 5 and len(excl_inv) >= 3
                               else "FAIL")
    verdict["Q3_scoped"] = ("PASS" if verdict["P1_invention"] == "PASS"
                            and verdict["P2_rule"] == "PASS" else "FAIL")
    verdict["Q6a_cross_author_zero_shot"] = verdict["P2_dc"]
    verdict["Q6b_cross_semantic_one_core"] = verdict["P2_oeis"]
    verdict["issue_745_gate"] = ("PASS" if verdict["Q3_scoped"] == "PASS"
                                 and verdict["P2_dc"] == "PASS"
                                 and verdict["P2_oeis"] == "PASS" else "FAIL")
    verdict["global_Q1_Q7"] = "OPEN"
    return summary, verdict


if __name__ == "__main__":
    mode = sys.argv[1:2]
    if mode == ["register"]:
        register(*sys.argv[2:5])
    elif mode == ["train"]:
        train(*sys.argv[2:4])
    elif mode == ["evaluate"]:
        evaluate(*sys.argv[2:5])
    else:
        raise SystemExit(__doc__)
