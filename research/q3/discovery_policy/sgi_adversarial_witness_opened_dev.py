#!/usr/bin/env python3
"""Opened DEV: seek source-consistent original-SyGuS programs differing at
previously unlabeled inputs. Prevent source/future gold access in proposer.
No model learning; no global Q promotion. Two phases prepare/propose.
"""
import hashlib,json,os,pathlib,re,resource,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_active_oracle_v1 import (top_level_forms,get_cmd,sha256,source_without_forms,
    proposal_function,model_eval,helpers_for,io_form)
UPSTREAM="e7ae840e5546e9243ff94afb1a29064fc050011c"
FROZEN_SHA="a2713cee7e4a54506501927c07ff65f78d4ad110e4c9568892d937f3a0aa8185"
TARGET=(1,5,8,9,10,11)
SOURCE=pathlib.Path("upstream")
FIRST=pathlib.Path("previous_first")
PACK=pathlib.Path("adversarial_source_only.json")
OUT=pathlib.Path("adversarial_dev_first")

def prep():
    assert subprocess.check_output(["git","-C",str(SOURCE),"rev-parse","HEAD"],text=True).strip()==UPSTREAM
    f=FIRST/"FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json"
    assert sha256(f.read_bytes())==FROZEN_SHA
    previous=json.loads(f.read_text())
    rows=[]
    for i in TARGET:
        r=previous["rows"][i]
        assert r["index"]==i and r["query_decision"]=="SKIP_UNANIMOUS_THREE"
        path=SOURCE/r["path"];raw=path.read_bytes();original=raw.decode()
        assert sha256(raw)==r["original_sha256"]
        xs=top_level_forms(original)
        cs=[x for x in xs if get_cmd(x[2])=="constraint"]
        assert len(cs)==r["n_constraints"]
        inp=[io_form(x[2]) for x in cs]
        assert inp[-2][0]==r["probe_input"] and inp[-1][0]==r["future_input"]
        assert sha256(cs[-2][2].encode())==r["probe_constraint_sha256"]
        assert sha256(cs[-1][2].encode())==r["future_constraint_sha256"]
        src=source_without_forms(original,cs[-2:])
        assert sha256(src.encode())==r["source_only_sha256"]
        rows.append({"index":i,"name":r["path"],"source_original_sha256":sha256(raw),
                     "source_sha256":sha256(src.encode()),"source":src,
                     "probe_input":r["probe_input"],"future_input":r["future_input"],
                     "f0_stdout_sha256":r["proposals"][0]["stdout_sha256"],
                     "source_constraints":len(cs)-2})
    PACK.write_text(json.dumps({"root":UPSTREAM,"prior_first":FROZEN_SHA,"rows":rows},indent=2))
    print("PREPARED",[(r["index"],r["name"],r["source_constraints"]) for r in rows],flush=True)

def strict_source_check(helpers,candidate,source):
    import z3
    cs=[f[2] for f in top_level_forms(source) if get_cmd(f[2])=="constraint"]
    def body(f):
        m=re.match(r"\(\s*constraint\s+(.*)\s*\)$",f,re.S)
        if not m:raise ValueError("not ground")
        return m.group(1)
    script=helpers+"\n"+candidate+"\n(assert (not (and "+" ".join(body(c) for c in cs)+")))\n"
    slv=z3.Solver();slv.set(timeout=3500)
    slv.add(*z3.parse_smt2_string(script))
    return str(slv.check())

def run_solver(content,stem):
    infile=OUT/(stem+".sl")
    infile.write_text(content)
    def limit():resource.setrlimit(resource.RLIMIT_CPU,(5,6))
    t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    p=subprocess.Popen(["cvc5","--lang=sygus2",str(infile)],stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,text=True,errors="replace",preexec_fn=limit)
    peak=0;forced=None
    while p.poll() is None:
        try:
            txt=pathlib.Path(f"/proc/{p.pid}/status").read_text(errors="replace")
            m=re.search(r"^VmRSS:\s+(\d+)\s+kB",txt,re.M)
            if m:
                peak=max(peak,int(m.group(1)))
                if peak>524288:forced="RSS";p.kill()
        except (FileNotFoundError,ProcessLookupError):pass
        if time.monotonic()-t>6:
            forced="TIME";p.kill()
        time.sleep(.015)
    out,err=p.communicate(timeout=2)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    infile.unlink()
    (OUT/(stem+".stdout")).write_text(out)
    (OUT/(stem+".stderr")).write_text(err)
    return out,err,{"exit_code":p.returncode,"forced":forced,
        "wall_s":round(time.monotonic()-t,6),"cpu_user_s":round(after.ru_utime-before.ru_utime,6),
        "cpu_sys_s":round(after.ru_stime-before.ru_stime,6),
        "rss_sample_max_kib":peak or None,
        "stdout_sha256":sha256(out.encode()),"stderr_sha256":sha256(err.encode())}

def propose():
    import z3
    f=FIRST/"FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json"
    assert sha256(f.read_bytes())==FROZEN_SHA
    prev=json.loads(f.read_text())
    z=json.loads(PACK.read_text())
    assert z["prior_first"]==FROZEN_SHA
    OUT.mkdir(exist_ok=True)
    data=[]
    for r in z["rows"]:
        i=r["index"]
        p=prev["rows"][i]
        f0txt=(FIRST/f"{i:02d}_0.stdout").read_text()
        assert sha256(f0txt.encode())==r["f0_stdout_sha256"]
        f0=proposal_function(f0txt)
        h=helpers_for(r["source"])
        record={"index":i,"name":r["name"],"source_sha256":r["source_sha256"],
                "f0_stdout_sha256":r["f0_stdout_sha256"],"probe":[]}
        assert strict_source_check(h,f0,r["source"])=="unsat"
        for key in ("probe_input","future_input"):
            v0=model_eval(h,f0,r[key])
            # Must insert before check-synth; gold is unavailable, only source and unlabeled x/v0.
            assertion=f"(constraint (not (= (f {r[key]}) {v0})))"
            forms=top_level_forms(r["source"])
            check=[f for f in forms if get_cmd(f[2])=="check-synth"]
            assert len(check)==1
            insert=check[0][0]
            solver_input=r["source"][:insert]+assertion+"\n"+r["source"][insert:]
            base=f"i{i:02d}_{key}"
            a,b,cost=run_solver(solver_input,base)
            rec={"input_type":key,"x":r[key],"default_prediction":v0,
                 "adversarial_assertion_sha256":sha256(assertion.encode()),
                 "source_only_forced_script_sha256":sha256(solver_input.encode()),**cost}
            try:
                if cost["exit_code"]!=0 or cost["forced"]:raise ValueError("NO_TERMINATED_NATIVE_CANDIDATE")
                rival=proposal_function(a)
                rec["rival_program_sha256"]=sha256(rival.encode())
                rec["rival_source_check"]=strict_source_check(h,rival,r["source"])
                rec["rival_value"]=model_eval(h,rival,r[key])
                if rec["rival_source_check"]!="unsat" or rec["rival_value"]==v0:
                    raise ValueError("NOT_INDEPENDENTLY_VERIFIED_DISAGREEMENT")
                rec["status"]="SOURCE_CONSISTENT_SEMANTIC_DISAGREEMENT_WITNESS"
            except Exception as e:
                rec["status"]="HOLD_NO_WITNESS_WITHIN_BOUND"
                rec["reason"]=type(e).__name__+":"+str(e)[:130]
            record["probe"].append(rec)
            print("DEV_WITNESS",i,key,rec["status"],rec["wall_s"],flush=True)
        data.append(record)
    result={"intent":"OPENED_RETROSPECTIVE_DEVELOPMENT_NOT_UNSEEN_TRANSFER",
        "prior_original_first_sha256":FROZEN_SHA,"original_commit":UPSTREAM,
        "original_future_or_probe_gold_read":False,
        "neural_weights":False,"G1":"HOLD","Q1_Q7":"OPEN",
        "rows":data}
    p=OUT/"DEV_V2_SEMANTIC_ADVERSARIAL_WITNESS.json"
    p.write_text(json.dumps(result,sort_keys=True,indent=2))
    print("DEV_SHA256",sha256(p.read_bytes()))
if __name__=="__main__":
    if sys.argv[1]=="prepare":prep()
    elif sys.argv[1]=="propose":propose()
    else:raise SystemExit("use prepare/propose")
