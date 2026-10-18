"""First source-original classical control; prereg issue #218, comment 6247675561.
A = Z3 4.15.4 Python; B = pinned qfn2l Python reference, NOT qfn2l C++.
Exact 18 2026 competition non-answer cases frozen before original sources opened.
No training, model calls, solution labels in solver, or original formula modifications.
"""
import collections,gzip,hashlib,ijson,json,os,re,subprocess,sys,time,urllib.request
from pathlib import Path

STAMP="G0_MATHPROBLEMS_18_FIRST_CLASSICAL_REPLAY"
INPUT_COMMIT="cd15cbedd4ef312d615448100797a80e922cf575"
SOURCE_COMMIT="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
QFN2L_COMMIT="ca83ce1a7b81aa78520c06360aaf4724f7f8c963"
GROUP="20220315-MathProblems"
RESULT_BASE=f"https://raw.githubusercontent.com/SMT-COMP/smt-comp.github.io/{INPUT_COMMIT}/data/"
SOURCE_BASE=f"https://raw.githubusercontent.com/SMT-LIB/benchmark-submission-2022/{SOURCE_COMMIT}/"
OUT=Path("/tmp/g0_mathproblems18_first_modern_classical_replay.json")
BASE="/tmp/g0_2026_mathproblems18_baseline"
WALL_PER_ARM_S=15
EXPECTED_COUNT=18
EXPECTED_LABELS={"sat":13,"unknown":5}
REF_FILE_SHA256={
"results-sq-2026.json.gz":"7abe5cadf800cc84db00506f85176378f714cdaa8c02a0e491059835f5039c58",
"benchmarks-2026.json.gz":"ba855e47e1ed88e2e6bb26272e84a20a0e8f0c320adc704b062f4c287e586a54"}
A_CODE=r"""
import json,sys,z3
p=sys.argv[1]
s=z3.Solver()
try:s.from_file(p)
except Exception as e:
 print(json.dumps({"status":"PARSE_ERROR","error":type(e).__name__}))
 sys.exit(0)
s.set(timeout=14500)
r=s.check()
if r==z3.sat:
 model=s.model()
 from z3.z3util import get_vars
 vars=get_vars(z3.And(*s.assertions()))
 pairs={v.decl().name():str(model.eval(v,model_completion=True)) for v in vars}
 print(json.dumps({"status":"sat","model":pairs}))
else:
 print(json.dumps({"status":str(r),"reason":s.reason_unknown() if r==z3.unknown else None}))
"""
def public_get(url,out):
    req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-G0-2026-original-frozen-comparison"})
    with urllib.request.urlopen(req,timeout=40) as r,open(out,"wb") as f:
        import shutil
        shutil.copyfileobj(r,f)
    return Path(out).read_bytes()
def get_official(name):
    p=Path("/tmp")/("verified_"+name)
    if p.exists():raw=p.read_bytes()
    else:raw=public_get(RESULT_BASE+name,p)
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=REF_FILE_SHA256[name]:raise RuntimeError("PINNED_COMPETITION_DATA_SHA256_MISMATCH "+name)
    return p
def case_key(record):
    f=record["file"]
    if f["logic"]!="QF_NIA" or not f["family"] or f["family"][0]!=GROUP:return None
    return ("QF_NIA",tuple(f["family"]),f["name"])
def original_sha(key):
    return hashlib.sha256(json.dumps(key,separators=(",",":")).encode()).hexdigest()
def frozen_original_keys():
    results=get_official("results-sq-2026.json.gz")
    index=get_official("benchmarks-2026.json.gz")
    observed=collections.defaultdict(dict)
    with gzip.open(results,"rb") as f:
        for row in ijson.items(f,"results.item"):
            if row["track"]!="SingleQuery":raise RuntimeError("TRACK_INPUT_MISMATCH")
            key=case_key(row)
            if key is None:continue
            assert row["solver"] not in observed[key],"RESULT_DUPLICATE"
            observed[key][row["solver"]]=row["result"].lower()
    meta={}
    with gzip.open(index,"rb") as f:
        for row in ijson.items(f,"non_incremental.item"):
            key=case_key(row)
            if key is None:continue
            assert key not in meta
            meta[key]=row["status"].lower()
    assert len(observed)==134 and set(observed).issubset(meta)
    keys=[k for k,v in sorted(observed.items()) if not any(
        ans in ("sat","unsat") for ans in v.values())]
    assert len(keys)==EXPECTED_COUNT
    assert dict(collections.Counter(meta[k] for k in keys))==EXPECTED_LABELS
    assert all(len(observed[k])==17 for k in keys)
    return [(key,meta[key]) for key in keys]
def get_original(key,folder):
    rel=Path("non-incremental")/key[0]/Path(*key[1])/key[2]
    if ".." in rel.parts or key[1][0]!=GROUP or not key[2].endswith(".smt2"):
        raise RuntimeError("FROZEN_INPUT_OUTSIDE_ORIGINAL_DIR")
    local=folder/key[2]
    data=public_get(SOURCE_BASE+rel.as_posix(),local)
    if not 30<len(data)<2_000_000:raise RuntimeError("ORIGINAL_SOURCE_SIZE_OR_DOWNLOAD")
    # SMT original contents are NEVER changed. Status names are not fed to solver.
    import z3
    original=z3.Solver()
    original.from_file(str(local))
    if not original.assertions():raise RuntimeError("NO_ORIGINAL_ASSERTIONS")
    if b"QF_NIA" not in data[:250]:raise RuntimeError("MISMATCH_ORIGINAL_LOGIC")
    return local,hashlib.sha256(data).hexdigest(),len(data)
def parse_model_string(value):
    if re.fullmatch(r"-?\d+",value.strip()):return int(value.strip())
    m=re.fullmatch(r"\(-\s+(\d+)\)",value.strip())
    if m:return -int(m.group(1))
    return None
def verify_independently(original,values):
    # A fresh source parse and *ground* verification, never append hints to originals.
    import z3
    s=z3.Solver()
    s.from_file(str(original))
    from z3.z3util import get_vars
    original_formula=z3.And(*s.assertions())
    free=get_vars(original_formula)
    names=[v.decl().name() for v in free]
    if set(names)!=set(values):
        return {"status":"FAILED_INCOMPLETE_OR_EXTRANEOUS_ASSIGNMENT",
                "expected_var_count":len(names),"reported_var_count":len(values)}
    if any(not z3.is_int(v) for v in free):
        return {"status":"FAILED_NON_INTEGER_VARIABLE"}
    parsed={k:parse_model_string(v) for k,v in values.items()}
    if any(v is None for v in parsed.values()):
        return {"status":"FAILED_MODEL_NONINTEGER"}
    subst=[(v,z3.IntVal(parsed[v.decl().name()])) for v in free]
    ground=z3.substitute(original_formula,*subst) if subst else original_formula
    ground_simple=z3.simplify(ground)
    if z3.is_true(ground_simple):return {"status":"SOURCE_ORIGINAL_MODEL_VERIFIED","original_free_vars":len(free)}
    if z3.is_false(ground_simple):return {"status":"ORIGINAL_MODEL_REFUTED","original_free_vars":len(free)}
    check=z3.Solver();check.set(timeout=3000)
    check.add(z3.Not(ground_simple))
    r=check.check()
    return {"status":"SOURCE_ORIGINAL_MODEL_VERIFIED" if r==z3.unsat else
            "ORIGINAL_MODEL_NOT_VERIFIED","original_free_vars":len(free),
            "ground_check":str(r)}
def child_run(argv,source,token):
    started=time.perf_counter()
    timepath=Path(BASE)/("peak_"+token+".txt")
    rawstdout=""
    err=""
    try:
        p=subprocess.run(
            ["/usr/bin/time","-f","%M","-o",str(timepath)]+argv,
            capture_output=True,text=True,timeout=WALL_PER_ARM_S,
            cwd=str(Path.cwd()),env={**os.environ,"PYTHONHASHSEED":"0"})
        rawstdout=p.stdout
        err=p.stderr
        rc=p.returncode
        if rc:
            status="ERROR_EXIT"
        else:
            status="OUTPUT_NOT_RECOGNIZED"
    except subprocess.TimeoutExpired as e:
        rc=None
        status="EXTERNAL_WALL_TIMEOUT"
        rawstdout=(e.stdout or b"").decode("utf-8","replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
        err=(e.stderr or b"").decode("utf-8","replace") if isinstance(e.stderr,bytes) else (e.stderr or "")
    except Exception as e:
        rc=None;status="EXEC_LAUNCH_FAILED";err=type(e).__name__+": "+str(e)[:120]
    wall=round(time.perf_counter()-started,3)
    rss=int(timepath.read_text().strip()) if timepath.exists() and timepath.read_text().strip().isdigit() else None
    return {"returncode":rc,"raw_output":rawstdout,
            "status":status,"wall_s":wall,"peak_rss_kib":rss,
            "stderr_digest_sha256":hashlib.sha256(err.encode()).hexdigest(),
            "stderr_type_excerpt":err[-180:].replace("\n"," ") if status in ("ERROR_EXIT","EXEC_LAUNCH_FAILED") else None}
def model_from_qfn(stdout):
    b=stdout.find(";; model-start")
    e=stdout.find(";; model-end")
    if b<0 or e<b:return {}
    middle=stdout[b:e]
    d={}
    for name,value in re.findall(
        r"\(define-fun\s+([^\s()]+)\s+\(\)\s+Int\s+(-?\d+|\(-\s+\d+\))\s*\)",middle):
        if name in d:raise RuntimeError("DUPLICATE_MODEL_VAR")
        d[name]=value
    return d
def extract_answer(run,arm):
    out=run.pop("raw_output")
    lines=[x.strip().lower() for x in out.splitlines()]
    if arm=="z3":
        try:
            js=json.loads(out.splitlines()[-1])
            answer=js.get("status","PARSE_ERROR")
            if answer=="sat":return answer,js.get("model",{})
            return answer,{}
        except (ValueError,IndexError):
            return "UNPARSEABLE_Z3",{}
    for x in reversed(lines):
        if x in ("sat","unsat","unknown"):
            return x,model_from_qfn(out) if x=="sat" else {}
    return "UNPARSEABLE_QFN2L",{}
def main():
    folder=Path(BASE);folder.mkdir(exist_ok=True,parents=True)
    receipt={"status":"INCOMPLETE_OR_FAILED","registered_issue_comment":6247675561,
        "input_competition_commit":INPUT_COMMIT,
        "original_smt2_source_commit":SOURCE_COMMIT,
        "qfn2l_source_commit":QFN2L_COMMIT,
        "exact_original_18_selector":"QF_NIA/20220315-MathProblems no sat nor unsat among 17 2026 participants",
        "target_count":18,"expected_label_metadata_not_supplied_to_solving_arms":True,
        "solver_arms":["z3-python-4.15.4","qfn2l-python-reference-ca83ce1a"],
        "paper_qfn2l_cpp_replication":False,
        "wall_limit_per_case_per_arm_s":WALL_PER_ARM_S,
        "source_corpus_unchanged":True,"zero_neural_forwards":True,
        "global_Q1_Q7":"OPEN","g1":"HOLD_LEARNING","g2":"BLOCKED",
        "cases":[]}
    try:
        keys=frozen_original_keys()
        receipt["exact_original_metadata_counts"]=dict(collections.Counter(label for _,label in keys))
        for i,(key,expected) in enumerate(keys):
            original,sha,size=get_original(key,folder)
            item={"original_identity_sha256":original_sha(key),
                  "original_source_sha256":sha,"source_bytes":size,
                  "reference_status_2026":expected,"arms":{}}
            for arm in ("z3","qfn2l"):
                token=f"{i}_{arm}"
                argv=(
                   [sys.executable,"-c",A_CODE,str(original)]
                   if arm=="z3" else
                   [sys.executable,"external_qfn2l/src/qfn2l/qf_solver.py",
                    str(original),"--bounds","--seed","7","--print-model",
                    "--timeout",str(WALL_PER_ARM_S-0.5)])
                outcome=child_run(argv,original,token)
                answer,model=extract_answer(outcome,arm)
                outcome["solver_reported_answer"]=answer
                if answer=="sat":
                    outcome["source_model_validation"]=verify_independently(original,model)
                elif answer=="unsat":
                    outcome["source_model_validation"]={"status":"UNSAT_NEEDS_INDEPENDENT_PROOF_CERTIFICATE"}
                else:
                    outcome["source_model_validation"]={"status":"NO_ORIGINAL_PROOF"}
                outcome["model_values_not_exported"]=True
                del model
                item["arms"][arm]=outcome
            receipt["cases"].append(item)
            # Save latest valid partial evidence even if later reference/download fails.
            Path("/tmp/g0_mathproblems18_first_modern_classical_replay.json").write_text(
                json.dumps(receipt,indent=2)+"\n")
        counter={}
        for arm in ("z3","qfn2l"):
            outcomes=[x["arms"][arm] for x in receipt["cases"]]
            counter[arm]={
                "solver_reported_sat":sum(x["solver_reported_answer"]=="sat" for x in outcomes),
                "source_verified_sat_models":sum(x["source_model_validation"]["status"]=="SOURCE_ORIGINAL_MODEL_VERIFIED" for x in outcomes),
                "solver_reported_unsat_without_cert":sum(x["solver_reported_answer"]=="unsat" for x in outcomes),
                "unknown_or_error":sum(x["solver_reported_answer"] not in ("sat","unsat") for x in outcomes),
                "total_wall_s":round(sum(x["wall_s"] for x in outcomes),3),
                "max_observed_peak_rss_kib":max((x["peak_rss_kib"] or 0) for x in outcomes)}
        receipt["score"]=counter
        receipt["status"]="FIRST_18_MODERN_CLASSICAL_SOURCE_CASES_ATTEMPTED"
        receipt["g0_admission"]="UNKNOWN_NO_FREE_ORACLE_COST_OR_CPP_SPECIALIST_REPLAY"
        receipt["all_solver_output_statuses_retained"]=True
        Path("/tmp/g0_mathproblems18_first_modern_classical_replay.json").write_text(
            json.dumps(receipt,indent=2)+"\n")
        print(STAMP,json.dumps({"status":receipt["status"],"score":counter,
              "g0":receipt["g0_admission"],"global":receipt["global_Q1_Q7"]}),flush=True)
    except Exception as e:
        receipt["status"]="FIRST_18_CLASSICAL_REPLAY_BLOCKED"
        receipt["first_failure_type"]=type(e).__name__
        receipt["first_failure_message"]=str(e)[:200]
        Path("/tmp/g0_mathproblems18_first_modern_classical_replay.json").write_text(
            json.dumps(receipt,indent=2)+"\n")
        print(STAMP,json.dumps({"status":receipt["status"],"failure":receipt["first_failure_message"]}),flush=True)
        raise
if __name__=="__main__":main()
