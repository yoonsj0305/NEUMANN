"""Q1/Q2/Q4/Q6 FIRST: exact redundancy elimination + zero-investment cascade.

Pre-registered in docs/research/Q1Q2Q4Q6_VERIFIED_CASCADE_CONCEPTARC_PREREG_2026_11_11.md
BEFORE any ConceptARC task byte is fetched.  Target = all 160
`corpus/*/*.json` originals of victorvikram/ConceptARC at a pinned commit
(Moskvichev, Odouard & Mitchell 2023), an author/benchmark never opened in
this repository.  No tuning after opening.

Modes
  register <blobless-clone-dir>       metadata only (names + git blob SHAs)
  evaluate <full-clone-dir>           the single FIRST evaluation
  dev <dataset-dir> <glob> <out>      same harness on ALREADY OPENED data

Only TRAIN pairs and test INPUTS are passed to any engine.  Test outputs are
read by the scorer after every candidate of that task is fixed.
"""
from __future__ import annotations
import functools, hashlib, json, pathlib, subprocess, sys, time
sys.path.insert(0, ".")
from neumann1 import arc2_meta_grid_reasoner as old
from neumann1 import relational_grid_inventor as rel_mod
from neumann1.relational_grid_inventor import grid
from neumann1.hybrid_arc_grid_inventor import HybridArcGridInventor
from neumann1.source_learned_grid_router import SourceLearnedGridRouter, _classical
from neumann1.classical_grid_fast import fit_all, classical_candidates
from neumann1.verified_cascade_grid_router import (
    VerifiedCascadeGridRouter, _relational)

REPO = "https://github.com/victorvikram/ConceptARC.git"
COMMIT = "0e67da6af879e4bad3d7cd3c196e8d551b445725"
REGISTRY = "docs/experiments/conceptarc_first_registry.json"
RESULT = "CONCEPTARC_VERIFIED_CASCADE_FIRST.json"
EXPECTED_TASKS = 160
CODE = ("neumann1/arc2_meta_grid_reasoner.py",
        "neumann1/relational_grid_inventor.py",
        "neumann1/hybrid_arc_grid_inventor.py",
        "neumann1/source_learned_grid_router.py",
        "neumann1/classical_grid_fast.py",
        "neumann1/verified_cascade_grid_router.py",
        "research/q4/conceptarc_verified_cascade_first.py")
# 1D-ARC family names: the frozen source-learned router only knows these.
ONED_FAMILIES = (
    "1d_denoising_1c", "1d_denoising_mc", "1d_fill", "1d_flip", "1d_hollow",
    "1d_mirror", "1d_move_1p", "1d_move_2p", "1d_move_2p_dp", "1d_move_3p",
    "1d_move_dp", "1d_padded_fill", "1d_pcopy_1c", "1d_pcopy_mc",
    "1d_recolor_cmp", "1d_recolor_cnt", "1d_recolor_oe", "1d_scale_dp")


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def git_blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def code_shas():
    return {p: sha256(pathlib.Path(p).read_bytes()) for p in CODE}


def clear_caches():
    for name in dir(rel_mod):
        fn = getattr(rel_mod, name)
        if isinstance(fn, functools._lru_cache_wrapper):
            fn.cache_clear()


def measure(fn):
    clear_caches()
    w, c = time.perf_counter_ns(), time.process_time_ns()
    out = fn()
    return out, (time.perf_counter_ns() - w) / 1e6, (time.process_time_ns() - c) / 1e6


def hybrid_compose(rel_cands, fits, inputs):
    """Hybrid candidate semantics (hybrid_arc_grid_inventor) from parts."""
    top = sorted(fits, key=lambda it: (it[1]["kind"] != "exact",
                                       len(old.PROGRAMS[it[0]]), it[0]))[:2]
    pool = list(rel_cands)
    for idx, ad in top:
        outs = []
        for g in inputs:
            o = old.predict(g, old.PROGRAMS[idx])
            if o is not None and ad["kind"] == "recolor":
                o = old.recolor(o, ad["mapping"])
            outs.append(o)
        pool.append(tuple(outs))
    seen, out = set(), []
    for p in pool:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
        if len(out) == 2:
            break
    return out


def score(preds, gold):
    joint = any(p == gold for p in preds)
    per = sum(any(p[i] == gold[i] for p in preds) for i in range(len(gold)))
    return joint, per


def solve_task(path, family):
    data = json.loads(path.read_text())
    demo = [(grid(x["input"]), grid(x["output"])) for x in data["train"]]
    inputs = [grid(x["input"]) for x in data["test"]]
    rec = {"tests": len(inputs)}
    # Timed: complete candidate construction (each includes its own fit).
    cand_o, w, c = measure(lambda: _classical(demo, inputs, 2))
    rec["classical_original"] = {"ms": w, "cpu_ms": c}
    cand_f, w, c = measure(lambda: classical_candidates(demo, inputs, 2))
    rec["classical_fast"] = {"ms": w, "cpu_ms": c}
    # Untimed exactness audit of the full fit list (indices, kinds, maps).
    fits_o = old.fit_task(demo, range(len(old.PROGRAMS)), len(old.PROGRAMS),
                          max_hits=len(old.PROGRAMS))[0]
    fits_f = fit_all(demo)[0]
    rec["exact_equivalent"] = (fits_o == fits_f and cand_o[0] == cand_f[0])
    (rel_c, rel_fit), w, c = measure(lambda: _relational(demo, inputs))
    rec["relational"] = {"ms": w, "cpu_ms": c, "fit": rel_fit,
                         "candidate": bool(rel_c)}
    hyb, w, c = measure(lambda: HybridArcGridInventor(2).solve(demo, inputs))
    rec["hybrid_original_run"] = {"ms": w, "cpu_ms": c,
                                  "preds": [p.outputs for p in hyb.candidates]}
    cas, w, c = measure(lambda: VerifiedCascadeGridRouter().solve(demo, inputs))
    rec["cascade_run"] = {"ms": w, "cpu_ms": c,
                          "engines_run": list(cas.engines_run),
                          "preds": [p.outputs for p in cas.candidates]}
    try:
        SourceLearnedGridRouter({f: "relational_only" for f in ONED_FAMILIES}
                                ).solve(family, demo, inputs)
        rec["family_router"] = "ANSWERED"
    except ValueError:
        rec["family_router"] = "REFUSED_UNSEEN_FAMILY"
    # Composite arms from single measured engine runs (no warm caches).
    rel_preds = [p.outputs for p in rel_c]
    cls_preds = [p.outputs for p in cand_f[0]]
    arms = {
        "classical_only": (cls_preds, rec["classical_fast"]["ms"]),
        "relational_only": (rel_preds, rec["relational"]["ms"]),
        "hybrid_fast": (hybrid_compose(rel_preds, fits_f, inputs),
                        rec["relational"]["ms"] + rec["classical_fast"]["ms"]),
        "cascade_composed": ((cls_preds, rec["classical_fast"]["ms"]) if cls_preds
                             else (rel_preds, rec["classical_fast"]["ms"]
                                   + rec["relational"]["ms"])),
    }
    gold = tuple(grid(x["output"]) for x in data["test"])   # scorer only
    out = {}
    for name, (preds, ms) in arms.items():
        j, p = score(preds, gold)
        out[name] = {"joint": j, "per_output": p, "ms": round(ms, 4),
                     "attempts": len(preds)}
    for name in ("hybrid_original_run", "cascade_run"):
        j, p = score(rec[name]["preds"], gold)
        out[name] = {"joint": j, "per_output": p, "ms": round(rec[name]["ms"], 4),
                     "cpu_ms": round(rec[name]["cpu_ms"], 4),
                     "attempts": len(rec[name]["preds"])}
    out["cascade_run"]["engines_run"] = rec["cascade_run"]["engines_run"]
    for k in ("classical_original", "classical_fast", "relational"):
        out[k] = {kk: (round(v, 4) if isinstance(v, float) else v)
                  for kk, v in rec[k].items()}
    out["exact_equivalent"] = rec["exact_equivalent"]
    out["family_router"] = rec["family_router"]
    out["tests"] = rec["tests"]
    return out


def summarize(rows):
    valid = [r for r in rows if "error" not in r]
    s = {"tasks": len(rows), "valid": len(valid), "errors": len(rows) - len(valid),
         "test_outputs": sum(r["tests"] for r in valid)}
    for a in ("classical_only", "relational_only", "hybrid_fast",
              "cascade_composed", "hybrid_original_run", "cascade_run"):
        s[a] = {"joint": sum(r[a]["joint"] for r in valid),
                "per_output": sum(r[a]["per_output"] for r in valid),
                "seconds": round(sum(r[a]["ms"] for r in valid) / 1000, 4)}
    for a in ("classical_original", "classical_fast", "relational"):
        s[a + "_seconds"] = round(sum(r[a]["ms"] for r in valid) / 1000, 4)
    s["exact_equivalent"] = sum(r["exact_equivalent"] for r in valid)
    s["family_router_refused"] = sum(
        r["family_router"] == "REFUSED_UNSEEN_FAMILY" for r in valid)
    s["cascade_escalated"] = sum(len(r["cascade_run"]["engines_run"]) > 1 for r in valid)
    s["cascade_lost_vs_hybrid"] = sum(
        r["hybrid_original_run"]["joint"] and not r["cascade_run"]["joint"] for r in valid)
    s["cascade_gained_vs_hybrid"] = sum(
        r["cascade_run"]["joint"] and not r["hybrid_original_run"]["joint"] for r in valid)
    return s


def verdict(s):
    """Decision rules frozen in the pre-registration (section 4)."""
    v = {}
    v["H1_exactness"] = ("PASS" if s["errors"] == 0 and
                         s["exact_equivalent"] == s["valid"] else "FAIL")
    sp = s["classical_original_seconds"] / max(s["classical_fast_seconds"], 1e-9)
    v["H2_classical_speedup"] = round(sp, 4)
    v["H2_elimination"] = "PASS" if sp >= 2.0 else "FAIL"
    hyb, cas = s["hybrid_original_run"], s["cascade_run"]
    hf, cc = s["hybrid_fast"], s["cascade_composed"]
    # Secondary, timing-noisy (relational 450 ms wall deadline): actual runs.
    v["H3b_actual_runs_joint"] = [cas["joint"], hyb["joint"]]
    if hf["joint"] < 5:
        v["H3_iso_capability"] = "NOT_EVALUABLE_CAPABILITY_FLOOR"
        v["H4_cost"] = "NOT_EVALUABLE_CAPABILITY_FLOOR"
    else:
        # Primary: SAME engine runs, only the routing decision differs.
        v["H3_iso_capability"] = ("PASS" if cc["joint"] >= hf["joint"]
                                  and cc["per_output"] >= hf["per_output"]
                                  else "FAIL")
        ratio = cas["seconds"] / max(hyb["seconds"], 1e-9)
        v["H4_cost_ratio_vs_hybrid_original"] = round(ratio, 4)
        v["H4_cost_ratio_vs_hybrid_fast"] = round(
            cas["seconds"] / max(s["hybrid_fast"]["seconds"], 1e-9), 4)
        v["H4_cost"] = ("PASS" if ratio <= 0.6 and cas["seconds"]
                        <= s["hybrid_fast"]["seconds"] else "FAIL")
    v["H5_open_set_routing"] = ("PASS" if s["family_router_refused"] == s["valid"]
                                else "UNEXPECTED")
    v["global_Q1_Q7"] = "OPEN"
    return v


def run_rows(paths, root, family_of):
    rows = []
    for p in paths:
        rid = str(p.relative_to(root))
        try:
            r = solve_task(p, family_of(p))
        except Exception as exc:          # recorded, never dropped
            r = {"error": type(exc).__name__ + ": " + str(exc)[:200]}
        r["id"] = rid
        rows.append(r)
        print(rid, "ERR" if "error" in r else
              (r["hybrid_original_run"]["joint"], r["cascade_run"]["joint"]),
              flush=True)
    return rows


def register(clone):
    clone = pathlib.Path(clone)
    out = subprocess.run(["git", "-C", str(clone), "ls-tree", "-r", "FETCH_HEAD"],
                         check=True, capture_output=True, text=True).stdout
    files = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        if path.startswith("corpus/") and path.endswith(".json"):
            files[path] = meta.split()[2]
    if len(files) != EXPECTED_TASKS:
        raise SystemExit("unexpected corpus size %d" % len(files))
    reg = {"schema": "neumann.q4.conceptarc-first-registry.v1",
           "repo": REPO, "commit": COMMIT, "target_files_git_blob_sha1": files,
           "target_bytes_opened": False, "code_sha256": code_shas()}
    reg["registry_sha256"] = sha256(canon(reg).encode())
    pathlib.Path(REGISTRY).write_text(json.dumps(reg, indent=1, sort_keys=True))
    print("REGISTERED", len(files), reg["registry_sha256"])


def evaluate(clone):
    clone = pathlib.Path(clone)
    reg = json.loads(pathlib.Path(REGISTRY).read_text())
    sig = reg.pop("registry_sha256")
    if sha256(canon(reg).encode()) != sig:
        raise SystemExit("REGISTRY_MUTATED")
    if reg["code_sha256"] != code_shas():
        raise SystemExit("CODE_CHANGED_AFTER_REGISTRATION")
    head = subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if head != COMMIT:
        raise SystemExit("WRONG_COMMIT")
    paths = []
    for rel, blob in sorted(reg["target_files_git_blob_sha1"].items()):
        p = clone / rel
        if git_blob_sha(p.read_bytes()) != blob:
            raise SystemExit("TARGET_BLOB_MISMATCH " + rel)
        paths.append(p)
    t = time.perf_counter()
    rows = run_rows(paths, clone, lambda p: p.parent.name)
    s = summarize(rows)
    report = {"schema": "neumann.q4.conceptarc-verified-cascade-FIRST.v1",
              "registry_sha256": sig, "commit": COMMIT, "summary": s,
              "verdict": verdict(s), "wall_s": round(time.perf_counter() - t, 3),
              "rows": rows}
    pathlib.Path(RESULT).write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps({"summary": s, "verdict": report["verdict"]}, indent=1))


def dev(root, pattern, out):
    root = pathlib.Path(root)
    paths = sorted(root.glob(pattern))
    rows = run_rows(paths, root, lambda p: p.parent.name)
    s = summarize(rows)
    report = {"status": "DEVELOPMENT_ON_OPENED_DATA_NOT_EVIDENCE",
              "summary": s, "verdict_if_rules_applied": verdict(s), "rows": rows}
    pathlib.Path(out).write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps({"summary": s, "verdict_if_rules_applied": report[
        "verdict_if_rules_applied"]}, indent=1))


if __name__ == "__main__":
    mode = sys.argv[1:2]
    if mode == ["register"]:
        register(sys.argv[2])
    elif mode == ["evaluate"]:
        evaluate(sys.argv[2])
    elif mode == ["dev"]:
        dev(*sys.argv[2:5])
    else:
        raise SystemExit(__doc__)
