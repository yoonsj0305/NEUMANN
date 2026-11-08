"""Q4 FIRST identical DSL common-subexpression elimination on 180 untouched 1D originals.

Both interpreters have the SAME operators, grammar, input 1D/2D type,
original two-attempt scoring, source-derived object rule mechanism,
and executable semantics. Only difference: reusing exact immutable
(g, primitive-op) results shared by the 626 expression trees.

Pre-register 180 new originals (10 of each of 18 concepts) after
EXCLUDING all three previously opened 180-task 1D cohorts.
Use A-B-B-A two runs per variant on SAME GITHUB worker to avoid
confounding second-arm warm filesystem/CPU effects. All four arm
implementations are frozen before the FIRST original bytes are read.
"""
from __future__ import annotations
import hashlib,json,pathlib,sys,time
sys.path.insert(0,'.')
sys.path.insert(0,'research/q3')
import q6_independent_author_1d_arc_transfer_first as original

ROOT=pathlib.Path("independent_1d_arc/dataset")
FIRST="prior_first/Q6_1D_ARC_180_DIFFERENT_AUTHOR_ORIGINAL_FIRST.json"
SECOND="prior_second/Q4_SECOND_1D_180_FILENAMES_FROZEN.json"
THIRD="prior_third/Q6_LONG_1D_NEW_180_THIRD_AUTHORIGINAL_FIRST.json"
REGISTRY="Q4_FOURTH_180_UNOPENED_1D_ORIGINALS_FROZEN.json"
UPSTREAM=original.UPSTREAM

def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(x):return hashlib.sha256(canonical(x).encode()).hexdigest()

def registry():
    a=json.loads(pathlib.Path(FIRST).read_text())
    b=json.loads(pathlib.Path(SECOND).read_text())
    c=json.loads(pathlib.Path(THIRD).read_text())
    if (a["official_1d_author_commit"]!=UPSTREAM or
        b["official_1d_author_commit"]!=UPSTREAM or
        c["official_1d_arc_commit"]!=UPSTREAM):
        raise ValueError("UPSTREAM_MISMATCH")
    first=set(a["original_task_names"])
    second=set(b["original_names"])
    third={r["id"] for r in c["records"]}
    if not (len(first)==len(second)==len(third)==180):
        raise ValueError("PRIOR_COHORT_SIZE")
    if first&second or first&third or second&third:
        raise ValueError("PREVIOUS_COHORTS_OVERLAP")
    exposed=first|second|third
    groups=sorted(x for x in ROOT.iterdir() if x.is_dir())
    if len(groups)!=18:raise ValueError("EXPECTED_18_CONCEPTS")
    out=[]
    for kind in groups:
        candidates=[
            p for p in kind.glob("*.json")
            if str(p.relative_to(ROOT)) not in exposed]
        candidates.sort(key=lambda p:sha(("q4-first-fourth-180-clean-same-language-ABBA-v1",p.name)))
        if len(candidates)<10:raise ValueError("INSUFFICIENT_UNOPENED_TASKS")
        out.extend(candidates[:10])
    ids=[str(x.relative_to(ROOT)) for x in out]
    if len(out)!=180 or len(set(ids))!=180 or set(ids)&exposed:
        raise ValueError("FOURTH_COHORT_NOT_NEW")
    return out,ids

def freeze():
    paths,names=registry()
    p={"schema":"neumann.q4.common-subexpression-1d-180-pre-registered.v1",
       "upstream_original_repo_sha":UPSTREAM,
       "first_three_opened_originals":540,
       "new_originals":180,
       "new_original_ids":names,
       "previous_normalizer_patched_commit":"f3a266882580541e7b43d9d906ec3eb2a77436de",
       "source_policy":"No task-specific 1D gold is used to choose operations or memo policy; immutable exact grid algebra, identical AST language",
       "programs":626,
       "candidate_attempts":2,
       "schedule":"uncached_A, cached_A, cached_B, uncached_B on same runner",
       "meta_source_only":True,
       "source_files_pre_registered_before_originals":True}
    p["sha256"]=sha(p)
    pathlib.Path(REGISTRY).write_text(json.dumps(p,indent=2))
    print("FROZEN_180_FOURTH_1D_AUTHOR_ORIGINALS_BEFORE_ANY_TARGET",p["sha256"],flush=True)
    return p

def target(variant,rep):
    pinned=json.loads(pathlib.Path(REGISTRY).read_text())
    digest=pinned.pop("sha256")
    if sha(pinned)!=digest or pinned["upstream_original_repo_sha"]!=UPSTREAM:
        raise ValueError("FROZEN_FOURTH_REGISTRY_INVALID")
    paths,names=registry()
    if names!=pinned["new_original_ids"]:raise ValueError("TASK_IDS_DRIFT")
    if variant not in ("uncached","cached") or rep not in ("A","B"):
        raise ValueError("INVALID_PAIRED_ARM")
    print("Q4_ABBA_FOURTH_180_PINNED",digest,variant,rep,flush=True)
    start=time.perf_counter()
    records=[original.solve_one(p) for p in paths]
    summary=original.summarize(records)
    result={"schema":"neumann.q4.repeated-cross-over-fourth-180-original-FIRST.v1",
        "source_program_code_sha256":original.file_sha("neumann1/arc2_meta_grid_reasoner.py"),
        "relational_program_code_sha256":original.file_sha("neumann1/relational_grid_inventor.py"),
        "new_180_registry_sha256":digest,
        "official_1d_author_sha":UPSTREAM,
        "paired_variant":variant,
        "repeat":rep,
        "originals":len(records),
        "summary":summary,
        "paired_process_wall_s":round(time.perf_counter()-start,5),
        "rows":records,
        "read_only_evaluator":"Neither arm sees test labels before its two source-fitted outputs are frozen.",
        "scope":"Identical DSL, original cases, two-attempt cap and input contract; only exact (input_grid,primitive) common-subexpression memo differs. No prior human R&D effort, CI startup, electricity or frontier provider FLOP accounting."}
    path=f"Q4_CSE_FOURTH_180_{variant.upper()}_{rep}.json"
    pathlib.Path(path).write_text(json.dumps(result,indent=2))
    print(json.dumps({
        "variant":variant,"rep":rep,
        "original_count":summary["originals"],"errors":summary["errors"],
        "hybrid_correct":summary["hybrid_exact_orig"],
        "classical_correct":summary["cold_exact_orig"],
        "hybrid_search_s":summary["hybrid_search_s"],
        "cold_search_s":summary["cold_search_s"],
        "full_wall_s":result["paired_process_wall_s"]},indent=2),flush=True)
    return result

if __name__=="__main__":
    if sys.argv[1:]==["prefreeze"]:freeze()
    elif len(sys.argv)==4 and sys.argv[1]=="target":target(sys.argv[2],sys.argv[3])
    else:raise SystemExit("prefreeze | target [uncached|cached] [A|B]")
