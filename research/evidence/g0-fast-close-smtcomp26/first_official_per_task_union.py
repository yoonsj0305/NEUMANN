"""G0 first immutable official SMT-COMP 2026 per-task classical-union audit.
No task files, labels for training, neural calls, model code or solver benchmarks.
Preregistered issue #218 comment id 6247450278 before downloading original gz.
"""
import collections,gzip,hashlib,json,os,sys,time,urllib.request
from pathlib import Path
try:
    import ijson
except ImportError:
    raise SystemExit("BLOCKED_IJSON_DEPENDENCY")

SOURCE_COMMIT="cd15cbedd4ef312d615448100797a80e922cf575"
BASE=f"https://raw.githubusercontent.com/SMT-COMP/smt-comp.github.io/{SOURCE_COMMIT}/data/"
EXPECTED_BLOB={
    "results-sq-2026.json.gz":"958998e703aa5f5b32b45c253f80e618440824b1",
    "benchmarks-2026.json.gz":"83afb4e0a83f651e8677caa99872acce843011cb",
}
TARGET=("QF_NIA","QF_NIRA")
OFFICIAL_TARGET_TOTAL=2857
GITHUB_ISSUE="https://github.com/yoonsj0305/NEUMANN/issues/218"
OUT=Path("/tmp/g0_2026_per_task_union_first_receipt.json")
MASK_LIMIT=12

def publish(obj):
    OUT.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("G0_OFFICIAL_PER_TASK_UNION_EVIDENCE",json.dumps({
        "status":obj.get("status"),"coverage":obj.get("coverage"),
        "decision":obj.get("decision"),"source":obj.get("source_identity")},sort_keys=True),flush=True)

def getfile(name):
    out=Path("/tmp")/name
    req=urllib.request.Request(BASE+name,headers={"User-Agent":"NEUMANN-G0-independent-2026-record-audit"})
    with urllib.request.urlopen(req,timeout=45) as r,out.open("wb") as fd:
        import shutil
        shutil.copyfileobj(r,fd)
    raw=out.read_bytes()
    if not raw.startswith(b"\x1f\x8b"):
        raise RuntimeError(f"NOT_GZIP_{name}")
    return out,{"upstream_git_blob_sha1":EXPECTED_BLOB[name],
                "computed_gzip_sha256":hashlib.sha256(raw).hexdigest(),
                "compressed_bytes":len(raw)}

def status_normalize(x):
    if not isinstance(x,str):return "unknown"
    return x.lower().strip()

def file_id(record):
    if not isinstance(record,dict):raise RuntimeError("UNSUPPORTED_FILENAME_STRUCTURE")
    family=record.get("family")
    name=record.get("name")
    logic=record.get("logic")
    if isinstance(family,str):family=family.split("/")
    if not isinstance(family,list) or not isinstance(name,str) or not isinstance(logic,str):
        raise RuntimeError("MALFORMED_ORIGINAL_SMT_FILE_ID")
    if logic not in TARGET:return None
    if record.get("incremental") is not False:
        raise RuntimeError("INCREMENTAL_FILE_IN_SINGLEQUERY_NIA")
    if "/" in name or any("/" in f for f in family):
        raise RuntimeError("INVALID_PATH_COMPONENT")
    return (logic,tuple(family),name)

def hid(key):
    return hashlib.sha256(json.dumps(key,separators=(",",":")).encode()).hexdigest()

def main():
    t=time.perf_counter()
    artifact={"status":"INCOMPLETE_OR_BLOCKED","source_identity":{
        "repository":"SMT-COMP/smt-comp.github.io","commit":SOURCE_COMMIT,
        "blobs":EXPECTED_BLOB},
        "preregistration_issue":GITHUB_ISSUE,
        "no_source_program_bodies_opened":True,
        "no_neural_training_or_forwards":True,
        "no_paid_calls":True,
        "global_q1_q7":"OPEN",
        "decision":{"g0":"HOLD","g1":"HOLD_LEARNING","g2":"BLOCKED"}}
    publish(artifact)
    try:
        results_file,rf=getfile("results-sq-2026.json.gz")
        benchmarks_file,bf=getfile("benchmarks-2026.json.gz")
        artifact["downloaded_sources"]={"results":rf,"benchmarks":bf}
        bench={}
        with gzip.open(benchmarks_file,"rb") as raw:
            for rec in ijson.items(raw,"non_incremental.item"):
                key=file_id(rec["file"])
                if key is None:continue
                label=status_normalize(rec.get("status"))
                if key in bench and bench[key]!=label:
                    raise RuntimeError("INCONSISTENT_REFERENCE_EXPECTED_STATUS")
                bench[key]=label
        observed=collections.defaultdict(dict)
        duplicate=0
        solver_rows=collections.Counter()
        seen_tracks=collections.Counter()
        status_distribution=collections.Counter()
        with gzip.open(results_file,"rb") as raw:
            for rec in ijson.items(raw,"results.item"):
                track=rec.get("track")
                seen_tracks[str(track)]+=1
                if str(track)!="SingleQuery":raise RuntimeError("NOT_SINGLE_QUERY_FILE")
                key=file_id(rec["file"])
                if key is None:continue
                solver=rec.get("solver")
                ans=status_normalize(rec.get("result"))
                if not isinstance(solver,str) or not solver:raise RuntimeError("INVALID_SOLVER")
                solver_rows[solver]+=1
                status_distribution[ans]+=1
                current=observed[key]
                if solver in current:
                    duplicate+=1
                    if current[solver]!=ans:raise RuntimeError("DUPLICATE_SOLVER_CONTRADICTORY_RESULT")
                current[solver]=ans
        unknown_ref=collections.Counter()
        missing_bench=[key for key in observed if key not in bench]
        tasks=set(observed)
        official_match=len(tasks)==OFFICIAL_TARGET_TOTAL
        families=collections.defaultdict(lambda:collections.Counter())
        bylogic=collections.defaultdict(lambda:collections.Counter())
        solver_disagree=[]
        truly_no_claim=[]
        no_known_correct=[]
        z3_intersection=[]
        unknown_expected_with_solves=[]
        for key in sorted(tasks):
            vals=observed[key]
            true_solves={s for s,r in vals.items() if r in ("sat","unsat")}
            reported_statuses={r for r in vals.values() if r in ("sat","unsat")}
            ref=bench.get(key,"missing")
            approved={s for s,r in vals.items() if r in ("sat","unsat") and r==ref}
            contradictory={s for s,r in vals.items() if r in ("sat","unsat") and r!=ref and ref in ("sat","unsat")}
            grp=(key[0],key[1][0] if key[1] else "[root]")
            cnt=families[grp]; bc=bylogic[key[0]]
            for c in (cnt,bc):
                c["observed"]+=1
                if true_solves:c["any_sat_unsat_claim"]+=1
                if approved:c["expected_consistent_solution"]+=1
            if not true_solves:
                truly_no_claim.append(key)
                cnt["no_any_solver_sat_unsat_claim"]+=1
                bc["no_any_solver_sat_unsat_claim"]+=1
            if not approved:
                no_known_correct.append(key)
                cnt["no_reference_consistent_result"]+=1
                bc["no_reference_consistent_result"]+=1
            if contradictory or len(reported_statuses)>1:
                solver_disagree.append((key,sorted(contradictory),sorted(reported_statuses)))
            if ref not in ("sat","unsat"):
                unknown_ref[ref]+=1
                if true_solves:unknown_expected_with_solves.append(key)
            if not any(vals.get(s) in ("sat","unsat") for s in ("Z3-alpha2","Z3-Z3++")):
                z3_intersection.append(key)
        no_any_nia=[x for x in truly_no_claim if x[0]=="QF_NIA"]
        all_solvers_count=len(solver_rows)
        artifact["coverage"]={
            "official_division_benchmarks":OFFICIAL_TARGET_TOTAL,
            "observed_originals":len(tasks),
            "official_division_match":official_match,
            "per_logic":{k:dict(v) for k,v in sorted(bylogic.items())},
            "benchmark_index_matching_observed":len(tasks)-len(missing_bench),
            "missing_in_official_benchmark_index":len(missing_bench),
            "official_reference_unknown_distribution":dict(unknown_ref),
            "solvers_with_target_rows":all_solvers_count,
            "total_target_result_rows":sum(solver_rows.values()),
            "duplicate_solver_target_rows":duplicate,
            "target_status_distribution":dict(status_distribution),
            "originals_with_no_sat_or_unsat_claim_by_any_2026_participant":len(truly_no_claim),
            "originals_with_no_reference_consistent_sat_or_unsat":len(no_known_correct),
            "no_claim_QF_NIA_only":len(no_any_nia),
            "z3_alpha2_z3_plusplus_both_no_sat_unsat_claim":len(z3_intersection),
            "source_solver_status_conflicts_or_reference_mismatches":len(solver_disagree),
            "unknown_reference_cases_with_sat_or_unsat_claims":len(unknown_expected_with_solves),
            "top_solver_result_counts":dict(solver_rows.most_common(40)),
            "seen_tracks":dict(seen_tracks)}
        artifact["family_aggregate"]=[
            {"logic":log,"top_source_family":group,**dict(stats)}
            for (log,group),stats in sorted(families.items())
        ]
        artifact["file_sha256_only_samples"]={
            "all_solver_no_claim": [hid(v) for v in truly_no_claim[:MASK_LIMIT]],
            "no_reference_consistent": [hid(v) for v in no_known_correct[:MASK_LIMIT]],
            "status_conflict": [hid(v[0]) for v in solver_disagree[:MASK_LIMIT]],
            "missing_benchmark": [hid(v) for v in missing_bench[:MASK_LIMIT]]}
        if not official_match or missing_bench:
            artifact["status"]="AUDIT_INCOMPLETE_COVERAGE_MISMATCH"
            artifact["decision"]["g0"]="BLOCKED_UNRECONCILED_OFFICIAL_COHORT"
        else:
            artifact["status"]="FIRST_PER_TASK_CLASSICAL_COMPETITION_UNION_COMPLETE"
            artifact["decision"]["g0"]=(
                "CLASSICAL_UNRESOLVED_COHORT_EXISTS_BUT_NOT_NEURAL_HEADROOM"
                if truly_no_claim else "NO_COMPETITION_TIME_UNRESOLVED_COHORT")
        artifact["decision"]["oracle_total_cost_headroom"]="UNKNOWN_NOT_MEASURED"
        artifact["decision"]["iso_hardware_replay"]="NOT_EXECUTED"
        artifact["analysis_wall_seconds"]=round(time.perf_counter()-t,3)
        publish(artifact)
    except Exception as e:
        artifact["status"]="FIRST_PER_TASK_AUDIT_BLOCKED"
        artifact["error_type"]=type(e).__name__
        artifact["error_message"]=str(e)[:400]
        artifact["analysis_wall_seconds"]=round(time.perf_counter()-t,3)
        publish(artifact)
        raise
if __name__=="__main__":main()
