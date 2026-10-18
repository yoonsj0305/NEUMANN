"""G0: 2026 competition official 3-case noanswer external Ultimate Automizer originals.
All three frozen prereg Issue #220 before result names read. No NN, no oracle yet.
Original SMT-LIB 2023 repo commit 7f993a0..., unchanged assertions verified.
"""
import collections,gzip,hashlib,ijson,json,os,re,subprocess,sys,time,urllib.request
from pathlib import Path

BENCH_COMMIT="cd15cbedd4ef312d615448100797a80e922cf575"
SOURCE_COMMIT="7f993a017850ba547c6ea19a1bf3b54adf54a449"
FAMILY="20230321-UltimateAutomizerSvcomp2023"
EXP_SHA={
    "results-sq-2026.json.gz":"7abe5cadf800cc84db00506f85176378f714cdaa8c02a0e491059835f5039c58",
    "benchmarks-2026.json.gz":"ba855e47e1ed88e2e6bb26272e84a20a0e8f0c320adc704b062f4c287e586a54"}
SOURCE_URL=f"https://raw.githubusercontent.com/SMT-LIB/benchmark-submission-2023/{SOURCE_COMMIT}/non-incremental/QF_NIA/{FAMILY}/"
DATA_URL=f"https://raw.githubusercontent.com/SMT-COMP/smt-comp.github.io/{BENCH_COMMIT}/data/"
OUT=Path("/tmp/g0_ultimate_first_original_classical.json")
WALL_S=15
Z3_CODE=r"""
import json,sys,z3
s=z3.Solver()
try:
 s.from_file(sys.argv[1])
 s.set(timeout=14200)
 ans=s.check()
 if ans==z3.sat:
  from z3.z3util import get_vars
  free=get_vars(z3.And(*s.assertions()))
  model=s.model()
  vals={v.decl().name():str(model.eval(v,model_completion=True)) for v in free}
  print(json.dumps({"result":"sat","model":vals}))
 elif ans==z3.unsat:print(json.dumps({"result":"unsat"}))
 else:print(json.dumps({"result":"unknown","reason":s.reason_unknown()}))
except Exception as e:print(json.dumps({"result":"error","exception":type(e).__name__+":"+str(e)[:150]}))
"""
def fetch(url,file):
    req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-G0-fastclose-original-2026"})
    with urllib.request.urlopen(req,timeout=60) as inp,file.open("wb") as out:
        import shutil
        shutil.copyfileobj(inp,out)
    return file.read_bytes()
def data(name):
    p=Path("/tmp")/("g0_ultimate_"+name)
    raw=fetch(DATA_URL+name,p)
    if hashlib.sha256(raw).hexdigest()!=EXP_SHA[name]:raise RuntimeError("OFFICIAL_INPUT_HASH_MISMATCH")
    return p
def fid(rec):
    f=rec["file"]
    if f.get("logic")!="QF_NIA" or f.get("incremental") is not False:return None
    a=f.get("family",[])
    if not a or a[0]!=FAMILY:return None
    if len(a)!=1 or not re.fullmatch(r"[A-Za-z0-9_.-]+\.smt2",f["name"]):raise ValueError("SOURCE_PATH_NOT_FROZEN_FLAT")
    return f["name"]
def select_three():
    f=data("results-sq-2026.json.gz"); idx=data("benchmarks-2026.json.gz")
    results=collections.defaultdict(dict)
    for item in ijson.items(gzip.open(f,"rb"),"results.item"):
        if item.get("track")!="SingleQuery":raise RuntimeError("NOT_SINGLE_QUERY")
        name=fid(item)
        if name is None:continue
        solver=item["solver"]
        if solver in results[name]:raise RuntimeError("DUPLICATE_SOLVER")
        results[name][solver]=item["result"].lower()
    statuses={}
    for item in ijson.items(gzip.open(idx,"rb"),"non_incremental.item"):
        name=fid(item)
        if name is None:continue
        if name in statuses:raise RuntimeError("DUPLICATE_SOURCE")
        statuses[name]=item["status"].lower()
    if not set(results).issubset(statuses):raise RuntimeError("BENCH_INDEX_MISMATCH")
    chosen=[name for name,v in sorted(results.items())
            if not any(ans in ("sat","unsat") for ans in v.values())]
    if len(chosen)!=3:raise RuntimeError("FROZEN_COHORT_NOT_EXACTLY_3")
    if any(len(results[name])!=17 for name in chosen):raise RuntimeError("INCOMPLETE_OFFICIAL_BASELINE")
    return chosen,statuses,len(results)
def run(cmd,token):
    f=Path("/tmp")/("g0_ultimate_rss_"+token)
    start=time.perf_counter()
    try:
        x=subprocess.run(["/usr/bin/time","-f","%M","-o",str(f)]+cmd,
                         capture_output=True,text=True,timeout=WALL_S)
        return {"rc":x.returncode,"output":x.stdout,"stderr_digest":hashlib.sha256(x.stderr.encode()).hexdigest(),
                "stderr_tail":x.stderr[-180:] if x.returncode else "",
                "wall_s":round(time.perf_counter()-start,3),
                "rss_kib":int(f.read_text().strip()) if f.exists() and f.read_text().strip().isdigit() else None,
                "external_timeout":False}
    except subprocess.TimeoutExpired:
        return {"rc":None,"output":"","stderr_digest":None,"stderr_tail":"",
                "wall_s":round(time.perf_counter()-start,3),"rss_kib":None,
                "external_timeout":True}
def intval(s):
    s=s.strip()
    if re.fullmatch(r"-?\d+",s):return int(s)
    m=re.fullmatch(r"\(-\s+(\d+)\)",s)
    return -int(m.group(1)) if m else None
def validate_src(path,assign):
    import z3
    from z3.z3util import get_vars
    s=z3.Solver();s.from_file(str(path))
    fs=z3.And(*s.assertions())
    symbols=get_vars(fs)
    keys={v.decl().name() for v in symbols}
    if set(assign)!=keys:return "MISSING_OR_EXTRA_ORIGINAL_VARIABLES"
    pairs=[]
    for v in symbols:
        if not z3.is_int(v):return "NON_INTEGER_SYMBOL"
        val=intval(str(assign[v.decl().name()]))
        if val is None:return "INVALID_NUMERIC_MODEL"
        pairs.append((v,z3.IntVal(val)))
    ground=z3.simplify(z3.substitute(fs,*pairs)) if pairs else z3.simplify(fs)
    if z3.is_true(ground):return "ORIGINAL_SOURCE_SAT_WITNESS_VERIFIED"
    if z3.is_false(ground):return "ORIGINAL_SOURCE_SAT_WITNESS_FALSE"
    ck=z3.Solver();ck.set(timeout=2500);ck.add(z3.Not(ground))
    return "ORIGINAL_SOURCE_SAT_WITNESS_VERIFIED" if ck.check()==z3.unsat else "NOT_VERIFIED"
def cvc5_model(out):
    # cvc5's (get-model) uses define-fun, supporting only exact ground integer
    result={}
    for m in re.finditer(r"\(define-fun\s+(\|[^|]+\||[^\s()]+)\s+\(\s*\)\s+Int\s+(\(-\s*\d+\)|-?\d+)\s*\)",out):
        name=m.group(1)
        if name.startswith("|") and name.endswith("|"):name=name[1:-1]
        if name in result:return {}
        result[name]=m.group(2)
    return result
def main():
    receipt={"status":"INCOMPLETE","prereg_issue":220,"original_source_commit":SOURCE_COMMIT,
             "official_record_commit":BENCH_COMMIT,"official_gzip_sha256":EXP_SHA,
             "scope":"all3_unanswered_QF_NIA_UltimateAutomizerSvcomp2023",
             "max_wall_per_original_per_solver":WALL_S,
             "g0_oracle_all_in_cost":"NOT_MEASURED",
             "g1":"HOLD_LEARNING","g2":"BLOCKED","global_q1_q7":"OPEN",
             "zero_training":True,"cases":[]}
    def persist():OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    persist()
    try:
        chosen,all_status,selected_count=select_three()
        receipt["official_selected_family_count"]=selected_count
        receipt["frozen_three_count"]=len(chosen)
        receipt["status_distribution_of_original_three"]=dict(collections.Counter(all_status[n] for n in chosen))
        import z3
        receipt["z3_version"]=z3.get_version_string()
        try:
            package=subprocess.run(["cvc5","--version"],capture_output=True,text=True,timeout=10)
            receipt["cvc5_version"]=package.stdout.strip().splitlines()[0][:160]
            cvc5_available=package.returncode==0
        except FileNotFoundError:
            cvc5_available=False
            receipt["cvc5_version"]="NOT_INSTALLED"
        if not cvc5_available:raise RuntimeError("SPECIALIST_CVC5_NOT_AVAILABLE")
        for i,name in enumerate(chosen):
            path=Path("/tmp")/name
            raw=fetch(SOURCE_URL+name,path)
            txt=raw.decode("utf-8")
            if "(set-logic QF_NIA)" not in txt or "(set-info :license " not in txt or "(check-sat)" not in txt:
                raise RuntimeError("ORIGINAL_HEADER_OR_LOGIC_MISMATCH:"+name)
            ss=z3.Solver();ss.from_file(str(path))
            if not ss.assertions():raise RuntimeError("SOURCE_ASSERTIONS_EMPTY")
            case={"original_filename":name,"source_sha256":hashlib.sha256(raw).hexdigest(),
                  "source_bytes":len(raw),"original_asserts":len(ss.assertions()),
                  "metadata_status_NOT_USED_IN_SOLVING":all_status[name],"arms":{}}
            a=run([sys.executable,"-c",Z3_CODE,str(path)],f"{i}_z3")
            if not a["external_timeout"]:
                try:
                    j=json.loads(a.pop("output").strip().splitlines()[-1])
                    a["answer"]=j.get("result","error")
                    a["source_validation"]=validate_src(path,j.get("model",{})) if a["answer"]=="sat" else "NO_SAT_WITNESS"
                except Exception as e:
                    a["answer"]="OUTPUT_PARSE_ERROR"
                    a["source_validation"]=type(e).__name__
            else:a["answer"]="TIMEOUT";a["source_validation"]="NO_SAT_WITNESS"
            case["arms"]["z3"]=a
            # Preserve original assertions, but replace final (exit) with model-request
            # instrumentation to retrieve witnesses. No formula/edit allowed.
            if "(exit)" not in txt:raise RuntimeError("MISSING_ORIGINAL_EXIT")
            probe=Path("/tmp")/("g0_ultimate_cvc5_"+str(i)+".smt2")
            probe.write_text(txt[:txt.rfind("(exit)")]+
                             "\n(get-model)\n(exit)\n",encoding="utf-8")
            b=run(["cvc5","--lang=smt2","--produce-models","--tlimit=14000",str(probe)],f"{i}_cvc5")
            if not b["external_timeout"]:
                rawoutput=b.pop("output")
                lines=[z.strip().lower() for z in rawoutput.splitlines()]
                b["answer"]=next((z for z in lines if z in ("sat","unsat","unknown")),"OUTPUT_PARSE_ERROR")
                b["source_validation"]=(validate_src(path,cvc5_model(rawoutput))
                                        if b["answer"]=="sat" else "NO_SAT_WITNESS")
                b["model_values_not_saved"]=True
            else:b["answer"]="TIMEOUT";b["source_validation"]="NO_SAT_WITNESS"
            case["arms"]["cvc5"]=b
            receipt["cases"].append(case);persist()
        summary={}
        for solver in ("z3","cvc5"):
            arms=[c["arms"][solver] for c in receipt["cases"]]
            summary[solver]={
                "sat_claim":sum(x["answer"]=="sat" for x in arms),
                "original_validated_sat":sum(x["source_validation"]=="ORIGINAL_SOURCE_SAT_WITNESS_VERIFIED" for x in arms),
                "unsat_claim_NOT_CERTIFIED":sum(x["answer"]=="unsat" for x in arms),
                "timeouts_unknown_errors":sum(x["answer"] not in ("sat","unsat") for x in arms),
                "total_wall_sec":round(sum(x["wall_s"] for x in arms),3)}
        receipt["summary"]=summary
        receipt["status"]="COMPLETE_FROZEN_THREE_ORIGINAL_SPECIALIST_REPLAY"
        receipt["g0_decision"]="STILL_OPEN_NO_ORACLE_COST_OR_FULL_SPECIALIST_UNION"
        persist()
        print("G0_ULTIMATE_FIRST_EVIDENCE",json.dumps({"status":receipt["status"],"summary":summary,
                   "original_cases":len(chosen),"label_dist":receipt["status_distribution_of_original_three"]}),flush=True)
    except Exception as e:
        receipt["status"]="FIRST_ORIGINAL_THREE_REPLAY_FAILED"
        receipt["first_error"]=type(e).__name__+":"+str(e)[:300]
        persist()
        print("G0_ULTIMATE_FIRST_FAILURE",receipt["first_error"],flush=True)
        raise
if __name__=="__main__":main()
