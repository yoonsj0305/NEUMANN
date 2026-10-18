"""G0 frozen July MathProblems 18 metadata-only reference-label screen.
No SMT2 task source body is read; no solvers, no model, no gold hints to learning.
Pre-register issue #218 comment 6247558084 before any additional file inspection.
"""
import collections,gzip,hashlib,ijson,json,time,urllib.request
from pathlib import Path
BASE="https://raw.githubusercontent.com/SMT-COMP/smt-comp.github.io/cd15cbedd4ef312d615448100797a80e922cf575/data/"
OUT=Path("/tmp/g0_mathproblems_18_reference_screen.json")
GROUP="20220315-MathProblems"
def get(name):
    dest=Path("/tmp")/name
    if not dest.exists():
        with urllib.request.urlopen(BASE+name, timeout=60) as inp,dest.open("wb") as o:
            import shutil
            shutil.copyfileobj(inp,o)
    return dest
def parse_id(rec):
    file=rec["file"]
    if file["logic"]!="QF_NIA":return None
    family=file["family"]
    if len(family)<1 or family[0]!=GROUP:return None
    return ("QF_NIA",tuple(family),file["name"])
def main():
    start=time.perf_counter()
    published=False
    try:
        result=get("results-sq-2026.json.gz")
        benchmark=get("benchmarks-2026.json.gz")
        reported=collections.defaultdict(dict)
        with gzip.open(result,"rb") as f:
            for rec in ijson.items(f,"results.item"):
                if rec["track"]!="SingleQuery":raise AssertionError("not single query")
                key=parse_id(rec)
                if key is not None:
                    assert rec["solver"] not in reported[key]
                    reported[key][rec["solver"]]=rec["result"].lower()
        statuses={}
        with gzip.open(benchmark,"rb") as f:
            for rec in ijson.items(f,"non_incremental.item"):
                key=parse_id(rec)
                if key is not None:
                    assert key not in statuses
                    statuses[key]=rec["status"].lower()
        assert len(reported)==134, 'FROZEN_COMPETITION_SELECTED_134_DRIFT'
        assert set(reported).issubset(set(statuses)), 'SELECTED_SOURCE_NOT_IN_FULL_INDEX'
        noanswers={key for key,solver in reported.items()
                   if not any(x in ("sat","unsat") for x in solver.values())}
        assert len(noanswers)==18
        status_breakdown=collections.Counter(statuses[key] for key in noanswers)
        accessible_baseline=[
          "MarekDanco/qfn2l Aug-2026 585/1100 MathProblems vs Z3 118/1100",
          "no overlap of 18 competition selected programs with new qfn2l file-level proof published"
        ]
        result={
            "status":"MATHPROBLEMS_18_OFFICIAL_METADATA_COMPLETE",
            "exact_pinned_2026_competition_git_commit":"cd15cbedd4ef312d615448100797a80e922cf575",
            "preregistration_issue_comment":6247558084,
            "selected_family":GROUP,
            "family_in_2026_benchmarks":134,
            "no_competitor_sat_or_unsat_count":18,
            "all_18_official_expected_label_distribution":dict(status_breakdown),
            "all_18_have_known_sat_or_unsat_label":all(
                statuses[k] in ("sat","unsat") for k in noanswers),
            "solver_result_rows_for_the_18":sum(len(reported[k]) for k in noanswers),
            "solver_outputs_any_sat_unsat_on_18":0,
            "selected_18_original_identity_hashes_sha256":[
                hashlib.sha256(json.dumps(k,sort_keys=True).encode()).hexdigest()
                for k in sorted(noanswers)],
            "no_original_smt2_task_source_bodies_read":True,
            "per_case_new_qfn2l_same_tasks":"NOT_CHECKED",
            "matching_cpu_gold_reframe":"NOT_EXECUTED",
            "q3_q4_q7_learning_claim":"NOT_ADMITTED",
            "g0_status":"HOLD_NEED_STRONG_NEW_SPECIALIST_AND_ORIGINAL_CHECKER",
            "g1":"HOLD_LEARNING",
            "global_q1_q7":"OPEN",
            "analysis_wall_s":round(time.perf_counter()-start,3)
        }
        OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print("G0_MATHPROBLEMS_18_METADATA_SCREEN",json.dumps({
            "count":len(noanswers),"official_labels":dict(status_breakdown),
            "g0":result["g0_status"]},sort_keys=True),flush=True)
    except Exception as exc:
        failure={"status":"FIRST_MATHPROBLEMS_INDEX_CHECK_BLOCKED",
                 "error":type(exc).__name__+": "+str(exc)[:300],
                 "preregistration_issue_comment":6247558084,
                 "g0_status":"BLOCKED","g1":"HOLD_LEARNING","global_q1_q7":"OPEN"}
        OUT.write_text(json.dumps(failure,indent=2)+"\n")
        print("G0_MATHPROBLEMS_18_FIRST_FAILURE",failure,flush=True)
        raise
if __name__=="__main__":main()
