#!/usr/bin/env python3
"""Prospective SGI v1, exact original source split, three-arm classical uncertainty.
Usage: prepare | propose | grade. Only 'prepare' and 'grade' access upstream;
'propose' runs after upstream is deleted and sees sanitized source-only IO.
No NEUMANN neural model here.
"""
import hashlib,json,pathlib,re,resource,subprocess,sys,time,os
from collections import Counter
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

PIN="e7ae840e5546e9243ff94afb1a29064fc050011c"
PREREG="68d11bac161b08b1fdbda47a146c616478157fdb"
FIRST_SEED="neumann1-sgi-active-oracle-v1/"
ROOT=pathlib.Path("upstream")
PACK=pathlib.Path("private_input_pack.json")
FIRST=pathlib.Path("new12_first")
SCORED=pathlib.Path("new12_score")
OLD={"PRE_51_10","PRE_icfp_gen_6.12","PRE_76_10","PRE_105_100","PRE_100_1000","PRE_126_100","PRE_55_1000","PRE_104_1000","PRE_icfp_gen_11.20"}
CONFIGS=(("default",["--seed=0"]),("seed1",["--seed=1"]),("random1",["--sygus-enum=random","--seed=1"]))

def source_pick():
    base=ROOT/"data/benchmarks/hard"
    paths=[p for p in base.glob("*/*.sl") if p.parent.name not in OLD]
    paths.sort(key=lambda p:(sha256((FIRST_SEED+p.relative_to(ROOT).as_posix()).encode()),p.as_posix()))
    if len(paths)<12:raise RuntimeError("too_few_originals")
    return paths[:12]

def io_form(form):
    # Restrict to original single-input and single-output ground PBE-BV constraints.
    m=re.fullmatch(r"\(\s*constraint\s+\(\s*=\s+\(\s*f\s+(#x[0-9a-fA-F]+)\s*\)\s+(#x[0-9a-fA-F]+)\s*\)\s*\)",form.strip())
    if not m:raise ValueError("NON_STANDARD_PBE_GROUND")
    return m.group(1).lower(),m.group(2).lower()

def source_without_forms(original,remove):
    for a,b,_ in sorted(remove,reverse=True):
        original=original[:a]+original[b:]
    return original

def proposal_function(stdout):
    m=list(re.finditer(r"\(\s*define-fun\s+f(?=\s)",stdout))
    if len(m)!=1:raise ValueError("Candidate count "+str(len(m)))
    start=m[0].start()
    d=0;in_s=False;in_bar=False
    for i in range(start,len(stdout)):
        ch=stdout[i]
        if in_s:
            if ch=='"':in_s=False
        elif in_bar:
            if ch=='|':in_bar=False
        elif ch=='"':in_s=True
        elif ch=='|':in_bar=True
        elif ch=='(':d+=1
        elif ch==')':
            d-=1
            if d==0:return stdout[start:i+1]
    raise ValueError("UNBALANCED_PROPOSAL")

def bounded_cvc5(path,flags):
    def limits():resource.setrlimit(resource.RLIMIT_CPU,(8,9))
    t=time.monotonic();r1=resource.getrusage(resource.RUSAGE_CHILDREN)
    p=subprocess.Popen(["cvc5","--lang=sygus2"]+flags+[str(path)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,errors="replace",preexec_fn=limits)
    peak=0;forced=None
    while p.poll() is None:
        try:
            z=pathlib.Path(f"/proc/{p.pid}/status").read_text(errors="replace")
            m=re.search(r"^VmRSS:\s+(\d+)\s+kB",z,re.M)
            if m:
                peak=max(peak,int(m.group(1)))
                if peak>512*1024:forced="RSS";p.kill()
        except (FileNotFoundError,ProcessLookupError):pass
        if time.monotonic()-t>10:forced="WALL";p.kill()
        time.sleep(.012)
    a,b=p.communicate(timeout=2)
    r2=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a,b,{"exit_code":p.returncode,"forced":forced,
        "wall_s":round(time.monotonic()-t,6),
        "cpu_user_s":round(r2.ru_utime-r1.ru_utime,6),
        "cpu_sys_s":round(r2.ru_stime-r1.ru_stime,6),
        "peak_rss_sample_kib":peak or None,
        "stdout_sha256":sha256(a.encode()),"stderr_sha256":sha256(b.encode())}

def model_eval(helpers,candidate,inp):
    import z3
    s=z3.Solver();s.set(timeout=4000)
    f=helpers+"\n"+candidate+"\n(declare-const neumann_val (_ BitVec 64))\n(assert (= neumann_val (f "+inp+")))\n"
    s.add(*z3.parse_smt2_string(f))
    if s.check()!=z3.sat:raise ValueError("Z3_CANNOT_EVALUATE")
    v=s.model().eval(z3.BitVec("neumann_val",64),model_completion=True).as_long()
    return f"#x{v:016x}"

def helpers_for(source):
    arr=top_level_forms(source)
    return "\n".join(p[2] for p in arr if get_cmd(p[2]) in ("define-fun","declare-fun","declare-const","declare-sort"))

def prepare():
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    rows=[]
    for idx,p in enumerate(source_pick()):
        name=p.relative_to(ROOT).as_posix()
        raw=p.read_bytes()
        r={"index":idx,"path":name,"original_sha256":sha256(raw),
           "original_git_blob_sha1":hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest(),
           "status":"ELIGIBLE"}
        try:
            text=raw.decode("utf-8")
            forms=top_level_forms(text)
            constraints=[f for f in forms if get_cmd(f[2])=="constraint"]
            if len(constraints)<3 or len([f for f in forms if get_cmd(f[2])=="synth-fun"])!=1:
                raise ValueError("INADEQUATE_ORIGINAL_STRUCTURE")
            ios=[io_form(f[2]) for f in constraints]
            probe, future=constraints[-2:]
            r["n_constraints"]=len(ios)
            r["probe_input"]=ios[-2][0];r["future_input"]=ios[-1][0]
            r["probe_constraint_sha256"]=sha256(probe[2].encode())
            r["future_constraint_sha256"]=sha256(future[2].encode())
            stripped=source_without_forms(text,[probe,future])
            assert len(top_level_forms(stripped))==len(forms)-2
            r["source_only_sha256"]=sha256(stripped.encode())
            r["source_only_text"]=stripped
        except Exception as e:
            r["status"]="INELIGIBLE"
            r["error_type"]=type(e).__name__
            r["error_detail"]=str(e)[:100]
        rows.append(r)
    PACK.write_text(json.dumps({"source":PIN,"prereg":PREREG,"rows":rows},indent=2))
    print("PACK_SOURCE_COUNTS",dict(Counter(r["status"] for r in rows)),flush=True)
    print("PACK_ROWS",[(r["index"],r["path"],r["status"]) for r in rows],flush=True)

def propose():
    import z3
    frozen=json.loads(PACK.read_text())
    assert frozen["source"]==PIN and frozen["prereg"]==PREREG
    FIRST.mkdir(exist_ok=True)
    rows=[]
    for r in frozen["rows"]:
        out={k:v for k,v in r.items() if k!="source_only_text"}
        out.update(proposals=[],query_decision="HOLD")
        if r["status"]!="ELIGIBLE":
            rows.append(out);continue
        src=FIRST/(f"source_{r['index']:02d}.sl")
        src.write_text(r["source_only_text"])
        helpers=helpers_for(r["source_only_text"])
        pred=[]
        for j,(name,flags) in enumerate(CONFIGS):
            a,b,t=bounded_cvc5(src,flags)
            (FIRST/f"{r['index']:02d}_{j}.stdout").write_text(a)
            (FIRST/f"{r['index']:02d}_{j}.stderr").write_text(b)
            rec={"name":name,"flags":flags,"arm":j,**t}
            try:
                if t["exit_code"]!=0 or t["forced"]:raise ValueError("CVC5_NONZERO_OR_LIMIT")
                candidate=proposal_function(a)
                rec["candidate_sha256"]=sha256(candidate.encode())
                rec["probe_pred"]=model_eval(helpers,candidate,r["probe_input"])
                if j==0:rec["future_pred"]=model_eval(helpers,candidate,r["future_input"])
                rec["status"]="CANDIDATE_EVALUATED_NO_GOLD"
                pred.append(rec["probe_pred"])
            except Exception as e:
                rec["status"]="HOLD_CANDIDATE_OR_Z3"
                rec["error_type"]=type(e).__name__
                rec["error_detail"]=str(e)[:160]
            out["proposals"].append(rec)
        src.unlink()
        if len(pred)==3 and len(set(pred))==1:
            out["query_decision"]="SKIP_UNANIMOUS_THREE"
        else:
            out["query_decision"]="REQUEST_ONE_DIVERGENCE_OR_UNCERTAIN"
        out["distinct_probe_candidate_outputs"]=len(set(pred))
        rows.append(out)
        print("UN_GRADED",out["index"],out["path"],out["query_decision"],len(pred),out["distinct_probe_candidate_outputs"],flush=True)
    receipt={
        "origin":"SGI external hard 64 bit; filename-rank 12 sealed, original N-2 source only",
        "upstream":PIN,"prereg":PREREG,
        "model_calls":0,"ownweight_training":False,
        "c0":"first three-arm arm0 default only; no extra labels",
        "active":"request one original penultimate label iff disagreement/uncertainty",
        "source_gold_or_probe_future_target_in_first":False,
        "graded_final":"NOT_RUN","graded_probe":"NOT_RUN",
        "global_questions":"OPEN","g1":"HOLD","rows":rows,
    }
    p=FIRST/"FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json"
    p.write_text(json.dumps(receipt,sort_keys=True,indent=2))
    (FIRST/"FIRST_SHA256.txt").write_text(sha256(p.read_bytes())+"  FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json\n")
    print("FIRST_SHA256",sha256(p.read_bytes()),flush=True)
    print("DECISIONS",dict(Counter(r["query_decision"] for r in rows)),flush=True)

def grade():
    import z3
    expected=os.environ["SEALED_FIRST_SHA256"]
    b=(FIRST/"FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json").read_bytes()
    assert sha256(b)==expected, "First immutable output is not the previously GitHub-sealed hash"
    first=json.loads(b)
    assert first["upstream"]==PIN
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    SCORED.mkdir(exist_ok=True)
    rows=[]
    for r in first["rows"]:
        o={"index":r["index"],"path":r["path"],"query_decision":r["query_decision"],"original_sha256":r["original_sha256"]}
        if r["status"]!="ELIGIBLE":
            o["status"]="INELIGIBLE";rows.append(o);continue
        text=(ROOT/r["path"]).read_text()
        assert sha256(text.encode())==r["original_sha256"]
        forms=top_level_forms(text)
        cs=[f for f in forms if get_cmd(f[2])=="constraint"]
        assert len(cs)==r["n_constraints"]
        ios=[io_form(f[2]) for f in cs]
        assert ios[-1][0]==r["future_input"] and ios[-2][0]==r["probe_input"]
        assert sha256(cs[-1][2].encode())==r["future_constraint_sha256"]
        assert sha256(cs[-2][2].encode())==r["probe_constraint_sha256"]
        src=source_without_forms(text,cs[-2:])
        assert sha256(src.encode())==r["source_only_sha256"]
        # No oracle targets from last two constraints provided in source-only arm.
        helpers=helpers_for(src)
        f0_stdout=(FIRST/f"{r['index']:02d}_0.stdout").read_text()
        assert sha256(f0_stdout.encode())==r["proposals"][0]["stdout_sha256"]
        try:
            candidate0=proposal_function(f0_stdout)
            src_preds=[model_eval(helpers,candidate0,ex[0]) for ex in ios[:-2]]
            o["c0_source_valid"]=src_preds==[ex[1] for ex in ios[:-2]]
            f0_prediction=model_eval(helpers,candidate0,ios[-1][0])
            o["c0"]= "EXACT" if o["c0_source_valid"] and f0_prediction==ios[-1][1] else "WRONG"
        except Exception as e:
            o["c0"]="HOLD";o["c0_error"]=type(e).__name__
        # C1 always purchases the authentic original penultimate label, even when active skips.
        fullsrc=source_without_forms(text,[cs[-1]])
        path=SCORED/(f"sourceplusprobe_{r['index']:02d}.sl")
        path.write_text(fullsrc)
        a,b,z=bounded_cvc5(path,["--seed=0"])
        path.unlink()
        z["arm"]="c1_full_label";o["c1_cost"]=z
        try:
            if z["exit_code"]!=0 or z["forced"]:raise ValueError("CVC5_REFIT_FAILED")
            candidate1=proposal_function(a)
            h=helpers_for(fullsrc)
            source_preds=[model_eval(h,candidate1,ex[0]) for ex in ios[:-1]]
            o["c1_source_valid"]=source_preds==[ex[1] for ex in ios[:-1]]
            future=model_eval(h,candidate1,ios[-1][0])
            o["c1"]="EXACT" if o["c1_source_valid"] and future==ios[-1][1] else "WRONG"
        except Exception as e:
            o["c1"]="HOLD";o["c1_error"]=type(e).__name__
        # Deterministic source-only conditional oracle policy frozen in FIRST.
        if r["query_decision"]=="SKIP_UNANIMOUS_THREE":
            o["active"]=o["c0"];o["active_label_requests"]=0
            o["active_refit_cpu_s"]=0
        else:
            o["active"]=o["c1"];o["active_label_requests"]=1
            o["active_refit_cpu_s"]=z["cpu_user_s"]+z["cpu_sys_s"]
        o["status"]="GRADED"
        rows.append(o)
        print("GRADE",r["index"],r["path"],"C0",o["c0"],"C1",o["c1"],"ACTIVE",o["active"],"Q",o["active_label_requests"],flush=True)
    def counts(k):return dict(Counter(r.get(k,"INELIGIBLE") for r in rows))
    report={"original_source_commit":PIN,"first_sha256":expected,
        "study":"Original previously unopened filename-rank hard 12, prior-first-source-only candidate freeze",
        "denominator":12,"model_ownweight_calls":0,"global_q1_q7":"OPEN","g1":"HOLD",
        "c0_counts":counts("c0"),"c1_counts":counts("c1"),"active_counts":counts("active"),
        "active_total_oracle_requests":sum(r.get("active_label_requests",0) for r in rows),
        "full_oracle_requests":sum(r.get("status")=="GRADED" for r in rows),
        "results":rows}
    dest=SCORED/"POSTFIRST_ORIGINAL_GRADE.json"
    dest.write_text(json.dumps(report,indent=2,sort_keys=True))
    print("GRADE_SHA256",sha256(dest.read_bytes()))
    print("SUMMARY",json.dumps({k:report[k] for k in ("c0_counts","c1_counts","active_counts","active_total_oracle_requests","full_oracle_requests")},sort_keys=True),flush=True)

if __name__=="__main__":
    command=sys.argv[1]
    if command=="prepare":prepare()
    elif command=="propose":propose()
    elif command=="grade":grade()
    else:raise SystemExit("command must be prepare/propose/grade")
