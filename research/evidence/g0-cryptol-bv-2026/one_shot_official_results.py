"""One-shot 2026 What4/Cryptol BV competition non-answer screen.
Before-data prereg: https://github.com/yoonsj0305/NEUMANN/issues/219
Use official full per-task data and fail closed; do NOT cherry-pick original tasks.
No original task SAT solver, training, oracle or new benchmark harness.
"""
import collections,gzip,hashlib,ijson,json,time,urllib.request
from pathlib import Path
ISSUE="https://github.com/yoonsj0305/NEUMANN/issues/219"
COMMIT="cd15cbedd4ef312d615448100797a80e922cf575"
FAMILY="20260613-cryptol-bv-math"
SOURCE_GIT="bdae77b0a144895098f82b51a531bc2b566df9e6"
EXPECTED={
"results-sq-2026.json.gz":"7abe5cadf800cc84db00506f85176378f714cdaa8c02a0e491059835f5039c58",
"benchmarks-2026.json.gz":"ba855e47e1ed88e2e6bb26272e84a20a0e8f0c320adc704b062f4c287e586a54"}
OUT=Path("/tmp/g0_cryptol_bv_official_first_receipt.json")

def download(name):
    p=Path("/tmp")/("g0_bv_"+name)
    req=urllib.request.Request(
        f"https://raw.githubusercontent.com/SMT-COMP/smt-comp.github.io/{COMMIT}/data/{name}",
        headers={"User-Agent":"NEUMANN-fast-close-G0-frozen-source-2026"})
    with urllib.request.urlopen(req,timeout=65) as f,p.open("wb") as w:
        import shutil
        shutil.copyfileobj(f,w)
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    if sha!=EXPECTED[name]:raise RuntimeError("OFFICIAL_DATA_SHA256_MISMATCH:"+name)
    return p
def key(file):
    if file.get("logic")!="QF_BV" or file.get("incremental") is not False:return None
    fam=file.get("family",[])
    if not isinstance(fam,list) or not fam or fam[0]!=FAMILY:return None
    name=file.get("name","")
    if "/" in name or not name.endswith(".smt2"):raise ValueError("INVALID_BENCHMARK_ID")
    return (tuple(fam),name)
def hashed(k):
    return hashlib.sha256(json.dumps(k,separators=(",",":")).encode()).hexdigest()
def main():
    start=time.monotonic()
    receipt={"status":"FIRST_ATTEMPT_INCOMPLETE",
      "preregistration":ISSUE,"official_results_git_commit":COMMIT,
      "official_data_shas":EXPECTED,"source_original_git_commit":SOURCE_GIT,
      "family":FAMILY,"logic":"QF_BV","frozen_first_data":True,
      "no_original_source_body_downloaded":True,"no_new_solver_running":True,
      "no_model_training":True,"no_oracle_cost_proof":True,
      "G1":"HOLD_LEARNING","G2":"BLOCKED","Q1_to_Q7_global":"OPEN"}
    OUT.write_text(json.dumps(receipt,indent=2)+"\n")
    try:
        resultfile=download("results-sq-2026.json.gz")
        indexfile=download("benchmarks-2026.json.gz")
        status={}
        with gzip.open(indexfile,"rb") as f:
            for row in ijson.items(f,"non_incremental.item"):
                k=key(row["file"])
                if k is None:continue
                if k in status:raise RuntimeError("DUPLICATE_TASK")
                status[k]=row["status"].lower()
        outputs=collections.defaultdict(dict)
        for row in ijson.items(gzip.open(resultfile,"rb"),"results.item"):
            if row.get("track")!="SingleQuery":raise RuntimeError("NOT_SINGLE_QUERY")
            k=key(row["file"])
            if k is None:continue
            solver=row.get("solver")
            if solver in outputs[k]:raise RuntimeError("DUPLICATE_SOLVER_TASK")
            outputs[k][solver]=row["result"].lower()
        if not set(outputs).issubset(status):raise RuntimeError("MISSING_TASK_IN_OFFICIAL_INDEX")
        count=collections.Counter()
        groups=collections.defaultdict(collections.Counter)
        solver_count=collections.Counter()
        bad=[]
        for k,v in sorted(outputs.items()):
            family=k[0][1] if len(k[0])>1 else "root"
            gr=groups[family]
            gr["selected"]+=1
            count["selected"]+=1
            expected=status[k]
            gr["label_"+expected]+=1
            count["label_"+expected]+=1
            good=[s for s,ans in v.items() if ans in ("sat","unsat")]
            if good:
                gr["some_solver_sat_unsat"]+=1
                count["some_solver_sat_unsat"]+=1
            else:
                gr["no_solver_sat_unsat"]+=1
                count["no_solver_sat_unsat"]+=1
            consistent=[s for s,ans in v.items() if ans in ("sat","unsat") and ans==expected]
            if consistent:gr["known_label_consistent"]+=1
            for s,ans in v.items():
                solver_count[s]+=1
                if ans in ("sat","unsat") and expected in ("sat","unsat") and ans!=expected:
                    bad.append(hashed(k))
        receipt["status"]="FIRST_OFFICIAL_CRYPTO_BV_PER_TASK_SCREEN_COMPLETE"
        receipt["selected_source_family_records_in_index"]=len(status)
        receipt["selected_source_family_records_in_solvers"]=len(outputs)
        receipt["counts"]=dict(count)
        receipt["per_subfamily"]={k:dict(v) for k,v in sorted(groups.items())}
        receipt["solver_counts_by_participant"]=dict(solver_count)
        receipt["known_label_disagreement_sha256"]=bad[:20]
        receipt["known_label_disagreement_count"]=len(bad)
        receipt["G0_classical_gap_status"]=(
          "NO_COMPETITION_SELECTED_BENCHMARKS" if not outputs else
          "NO_UNANSWERED_TASKS_STOP_DOMAIN" if count["no_solver_sat_unsat"]==0 else
          "COMPETITION_TIME_NONANSWER_EXISTS_ORACLE_HEADROOM_STILL_UNKNOWN")
        receipt["G0_full"]="OPEN"
        receipt["wall_s"]=round(time.monotonic()-start,3)
        OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print("G0_CRYPTO_BV_FIRST_SCREEN",json.dumps({
          "cases":len(outputs),"groups":receipt["per_subfamily"],
          "status":receipt["G0_classical_gap_status"],
          "label_disagreements":len(bad)}),flush=True)
    except Exception as exc:
        receipt["status"]="FIRST_CRYPTO_BV_OFFICIAL_AUDIT_FAILED"
        receipt["exception"]=type(exc).__name__+":"+str(exc)[:300]
        OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print("G0_CRYPTO_BV_FIRST_FAILURE",receipt["exception"],flush=True)
        raise
if __name__=="__main__":main()
