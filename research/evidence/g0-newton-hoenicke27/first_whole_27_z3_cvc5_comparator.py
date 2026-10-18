"""Matched CPU control on ALL existing 27 source-opened Hoenicke originals.
Preregistered NEUMANN Issue #222 comment 6248594040 before runtime.
Development-only; no blinded generalization or relative gain from timeout scores.
"""
import collections,hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path

FROZEN_SCRIPT=Path(__file__).parent/"one_shot_integer_polynomial_proof.py"
SPEC=importlib.util.spec_from_file_location("g0_original_newton",FROZEN_SCRIPT)
M=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=M;SPEC.loader.exec_module(M)
OUT=Path("/tmp/g0_newton27_classical_three_sec_first.json")
LIMIT=3.0
Z3=r"""
import json,sys,z3,time
s=z3.Solver()
try:
 s.from_file(sys.argv[1]);s.set(timeout=2700)
 result=s.check()
 print(json.dumps({"status":str(result),
                   "reason":s.reason_unknown() if result==z3.unknown else ""}))
except Exception as e:print(json.dumps({"status":"ERROR","exception":type(e).__name__}))
"""
ALREADY_PROVEN={"modInvStep.smt2","modInvVar1.smt2",
                "modInvStepSimplified.smt2","modSimpleTest.smt2"}

def run(command,i,who):
    started=time.perf_counter()
    peak=Path("/tmp")/("g0_newton_rss_"+str(i)+"_"+who+".txt")
    try:
        p=subprocess.run(["/usr/bin/time","-f","%M","-o",str(peak)]+command,
            text=True,capture_output=True,timeout=LIMIT)
        result={"exit_code":p.returncode,"external_wall_timeout":False,
                "stderr_sha256":hashlib.sha256(p.stderr.encode()).hexdigest()}
        if who=="z3":
            try:parsed=json.loads(p.stdout.splitlines()[-1]);answer=parsed.get("status","OUTPUT_ERROR")
            except (IndexError,ValueError):answer="OUTPUT_ERROR"
        else:
            lines=[x.strip() for x in p.stdout.splitlines()]
            answer=next((x for x in lines if x in ("sat","unsat","unknown")),"OUTPUT_ERROR")
        result["answer"]=answer
    except subprocess.TimeoutExpired:
        result={"exit_code":None,"external_wall_timeout":True,"answer":"EXTERNAL_WALL_TIMEOUT",
                "stderr_sha256":None}
    result["wall_s"]=round(time.perf_counter()-started,4)
    result["peak_rss_kib"]=(int(peak.read_text().strip())
         if peak.exists() and peak.read_text().strip().isdigit() else None)
    return result

def main():
    start=time.perf_counter()
    receipt={"status":"FIRST_CONTROL_NOT_COMPLETE",
        "registered_issue_comment":6248594040,
        "source_sha":M.SOURCE_COMMIT,
        "source_origin":M.SOURCE_FAMILY,
        "frozen_total_originals":27,
        "external_wall_limit_per_case_s":LIMIT,
        "solver_arms":["z3_4_15_4_python","cvc5_installed_binary"],
        "proof_already_registered_cases_sorted":sorted(ALREADY_PROVEN),
        "original_sat_unsat_reference_labels_NOT_used_as_inputs":True,
        "no_training_or_neural_inference":True,"G1":"HOLD_LEARNING",
        "Q1_Q7_global":"OPEN","cases":[]}
    def save():OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    save()
    try:
        import z3
        receipt["z3_version"]=z3.get_version_string()
        p=subprocess.run(["cvc5","--version"],capture_output=True,text=True,timeout=8)
        receipt["cvc5_version"]=p.stdout.strip().splitlines()[0] if p.returncode==0 else "NOT_EXECUTABLE"
        if p.returncode:raise RuntimeError("CVC5_UNAVAILABLE")
        for i,name in enumerate(M.NAMES):
            path,raw=M.fetch(name)
            case={"source_filename":name,"original_sha256":hashlib.sha256(raw).hexdigest(),
                  "previously_proved_by_source_algorithm":name in ALREADY_PROVEN,
                  "z3":run([sys.executable,"-c",Z3,str(path)],i,"z3"),
                  "cvc5":run(["cvc5","--lang=smt2","--tlimit=2700",str(path)],i,"cvc5")}
            receipt["cases"].append(case);save()
        receipt["status"]="COMPLETE_ALL_27_TWOSOLVER_DEVELOPMENT_CONTROL"
        counts={}
        for name in ("z3","cvc5"):
            results=[x[name] for x in receipt["cases"]]
            counts[name]={"answers":dict(collections.Counter(x["answer"] for x in results)),
                "whole_27_return_unsat":sum(x["answer"]=="unsat" for x in results),
                "already_math_certified_4_solver_unsat":sum(
                     x["previously_proved_by_source_algorithm"] and x[name]["answer"]=="unsat"
                     for x in receipt["cases"]),
                "already_math_certified_4_unsolved_or_timeout":sum(
                     x["previously_proved_by_source_algorithm"] and x[name]["answer"]!="unsat"
                     for x in receipt["cases"]),
                "total_solver_wall_sec":round(sum(x["wall_s"] for x in results),3)}
        receipt["summary"]=counts
        receipt["total_job_inner_wall_s_including_downloads"]=round(time.perf_counter()-start,3)
        receipt["admission"]="NOT_A_MATCHED_STRONGEST_SPECIALIST_OR_BLIND_NEURAL_NET_COST_PROOF"
        save()
        print("G0_NEWTON_27_TWO_CLASSICAL_SOURCE_CONTROL",json.dumps({
           "status":receipt["status"],"summary":counts,
           "inner_job_wall":receipt["total_job_inner_wall_s_including_downloads"]}),flush=True)
    except Exception as e:
        receipt["status"]="FIRST_CLASSICAL_CONTROL_FAILED"
        receipt["first_error"]=type(e).__name__+":"+str(e)[:240]
        receipt["total_job_inner_wall_s_including_downloads"]=round(time.perf_counter()-start,3)
        save()
        print("G0_NEWTON_CONTROL_FIRST_FAILURE",receipt["first_error"],flush=True)
        raise

if __name__=="__main__":main()
