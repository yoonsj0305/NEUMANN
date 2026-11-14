#!/usr/bin/env python3
"""SGI heldout twelve original source-only first proposer (NO eval gold).
Requires separately trained and GitHub-sealed weights. Prepare removes all
last two original constraints, leaving only their original input words.
"""
import hashlib,json,os,pathlib,subprocess,sys,math,re
from collections import Counter
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_active_oracle_v1 import (top_level_forms,get_cmd,io_form,source_without_forms,
    sha256,helpers_for,proposal_function,model_eval,bounded_cvc5)
from sgi_active_oracle_v1_postfirst_grade_fast import source_verified
from sgi_ownweight_prior_train import features,DIM

PIN="e7ae840e5546e9243ff94afb1a29064fc050011c"
PATHSEED="neumann1-ownweight-program-prior-v1/"
ROOT=pathlib.Path("upstream")
WEIGHTS=pathlib.Path("training_weights/FROZEN_TRAINED_A_B_WEIGHTS.json")
PACK=pathlib.Path("newprior_source_pack.json")
OUT=pathlib.Path("newprior_first")
OLD={"PRE_51_10","PRE_icfp_gen_6.12","PRE_76_10","PRE_105_100",
 "PRE_100_1000","PRE_126_100","PRE_55_1000","PRE_104_1000",
 "PRE_icfp_gen_11.20","PRE_icfp_gen_11.1","PRE_icfp_gen_10.7",
 "PRE_83_10","PRE_79_100","PRE_147_10","PRE_icfp_gen_6.15",
 "PRE_92_100","PRE_32_10","PRE_icfp_gen_10.10","PRE_100_10",
 "PRE_26_100","PRE_125_1000"}
ARMS=(("default",["--seed=0"]),("seed1",["--seed=1"]),
      ("random1",["--sygus-enum=random","--seed=1"]))

def choose_paths():
    base=ROOT/"data/benchmarks/hard"
    paths=[p for p in base.glob("*/*.sl") if p.parent.name not in OLD]
    paths.sort(key=lambda p:(sha256((PATHSEED+p.relative_to(ROOT).as_posix()).encode()),p.as_posix()))
    if len(paths)<12:raise RuntimeError("INSUFFICIENT_UNOPENED_ORIGINAL_HARD")
    return paths[:12]

def source_parts(b):
    original=b.decode("utf-8")
    fs=top_level_forms(original)
    cs=[x for x in fs if get_cmd(x[2])=="constraint"]
    if len(cs)<3 or len([x for x in fs if get_cmd(x[2])=="synth-fun"])!=1:
        raise ValueError("NOT_SINGLE_SYGUS_TARGET")
    pairs=[io_form(x[2]) for x in cs]
    src=source_without_forms(original,cs[-2:])
    assert len(top_level_forms(src))==len(fs)-2
    return src,cs,pairs

def prepare():
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    source=[]
    for idx,p in enumerate(choose_paths()):
        b=p.read_bytes();row={"index":idx,"name":p.relative_to(ROOT).as_posix(),
                            "original_sha256":sha256(b),"status":"ELIGIBLE"}
        try:
            src,cs,pairs=source_parts(b)
            row.update({"source_text":src,"source_sha256":sha256(src.encode()),
                "n_total_constraints":len(cs),
                "probe_input":pairs[-2][0],"future_input":pairs[-1][0],
                "probe_constraint_sha256":sha256(cs[-2][2].encode()),
                "future_constraint_sha256":sha256(cs[-1][2].encode())})
        except Exception as e:
            row["status"]="INELIGIBLE";row["reason"]=type(e).__name__+":"+str(e)[:140]
        source.append(row)
    PACK.write_text(json.dumps({"upstream":PIN,"filename_sort_seed":PATHSEED,"rows":source},indent=2))
    print("CHOSEN",[(r["index"],r["name"],r["status"]) for r in source],flush=True)

def weighted_score(w,x):
    return sum(float(a)*float(b) for a,b in zip(w["weights"],x))+float(w["bias"])

def first():
    import z3
    w_bytes=WEIGHTS.read_bytes()
    w=json.loads(w_bytes)
    assert len(w["weights"])==6 and w["test_source_accessed"] is False
    if os.environ.get("SEALED_TRAIN_SHA256") and sha256(w_bytes)!=os.environ["SEALED_TRAIN_SHA256"]:
        raise RuntimeError("TRAIN_WEIGHTS_SHA_MISMATCH")
    pack=json.loads(PACK.read_text())
    assert pack["upstream"]==PIN and len(pack["rows"])==12
    assert not ROOT.exists(),"Original GOLD repository must be DELETED before first proposals"
    OUT.mkdir(exist_ok=True)
    full=[]
    for r in pack["rows"]:
        rr={k:v for k,v in r.items() if k!="source_text"}
        rr["arms"]=[]
        rr["selected"]={}
        if r["status"]!="ELIGIBLE":
            full.append(rr);continue
        src=r["source_text"]
        path=OUT/f"input_{r['index']:02d}.sl"
        path.write_text(src)
        helpers=helpers_for(src)
        fs=top_level_forms(src)
        cs=[f[2] for f in fs if get_cmd(f[2])=="constraint"]
        source_goals=[]
        for s in cs:
            m=re.fullmatch(r"\(\s*constraint\s+(.*)\s*\)",s,re.S)
            if m is None:raise RuntimeError("NON_STANDARD_PBE")
            source_goals.append(m.group(1))
        for j,(name,flags) in enumerate(ARMS):
            stdout,stderr,cost=bounded_cvc5(path,flags)
            (OUT/f"{r['index']:02d}_{j}.stdout").write_text(stdout)
            (OUT/f"{r['index']:02d}_{j}.stderr").write_text(stderr)
            arm={"index":j,"config":name,"flags":flags,**cost,"status":"HOLD"}
            try:
                if cost["exit_code"]!=0 or cost["forced"]:raise ValueError("CVC5_LIMIT_OR_ERROR")
                program=proposal_function(stdout)
                if not source_verified(z3,helpers,program,source_goals):
                    raise ValueError("F0_NOT_SOURCE_FIT")
                probe_pred=model_eval(helpers,program,r["probe_input"])
                future_pred=model_eval(helpers,program,r["future_input"])
                x=features(program,len(cs),len(src),probe_pred,future_pred,j)
                arm.update({"program_sha256":sha256(program.encode()),"program_chars":len(program),
                    "source_valid":True,"probe_prediction":probe_pred,
                    "future_prediction":future_pred,"feature_vector":x,"status":"VALID_UNGRADED"})
            except Exception as e:
                arm["reason"]=type(e).__name__+":"+str(e)[:160]
            rr["arms"].append(arm)
        path.unlink()
        available=[a for a in rr["arms"] if a["status"]=="VALID_UNGRADED"]
        for key in sorted(w["weights"]):
            choice=max(available,key=lambda a:(weighted_score(w["weights"][key],a["feature_vector"]),-a["index"])) if available else None
            rr["selected"][key]=choice["index"] if choice else None
        mdl=min(available,key=lambda a:(a["program_chars"],a["index"])) if available else None
        rr["selected"]["MDL"]=mdl["index"] if mdl else None
        rr["selected"]["C0"]=0 if rr["arms"][0]["status"]=="VALID_UNGRADED" else None
        full.append(rr)
        print("UNGRADED_NEW",r["index"],r["name"],[a["status"] for a in rr["arms"]],
              rr["selected"],flush=True)
    output={"intent":"NEW ORIGINAL UNGRADED test candidate and selector choices; no new original future/probe OUTPUTS available",
       "upstream":PIN,"filename_seed":PATHSEED,
       "training_weight_sha256":sha256(w_bytes),
       "num_original_tasks":12,"gold_used_for_policy":False,
       "trained_policy_weights_six":list(sorted(w["weights"])),
       "source_only_cvc5_configs":ARMS,
       "global_Q1_Q7":"OPEN","G1":"HOLD","rows":full}
    fname=OUT/"UNSEEN12_FIRST_PROGRAM_SELECTIONS_BEFORE_GOLD.json"
    fname.write_text(json.dumps(output,sort_keys=True,indent=2))
    print("NEW_UNGRADED_SHA256",sha256(fname.read_bytes()),flush=True)
    print("SELECTED_SUMMARY",dict(Counter(str(r.get("selected",{}).get("C0")) for r in full)))
if __name__=="__main__":
    if sys.argv[1]=="prepare":prepare()
    elif sys.argv[1]=="propose":first()
    else:raise SystemExit("usage prepare|propose")
