#!/usr/bin/env python3
"""Separate POST-FIRST original gold grader for strictly frozen ownweight prior.

Does NOT train, tune, reselect, alter source proposals, or overwrite FIRST.
Uses exact pre-GOLD SHA of program selections and separately frozen training weights.
Strong C1 from native cvc5 uses one extra authentic original label per task.
"""
import hashlib,json,math,os,pathlib,re,subprocess,sys
from collections import Counter
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_active_oracle_v1 import (top_level_forms,get_cmd,io_form,source_without_forms,
    sha256,helpers_for,proposal_function,model_eval,bounded_cvc5)
from sgi_active_oracle_v1_postfirst_grade_fast import source_verified
from sgi_ownweight_prior_new12_first import ROOT,OUT,choose_paths,PIN

SEALED_FIRST=os.environ["SEALED_NEWPRIOR_FIRST_SHA256"]
SEALED_TRAIN=os.environ["SEALED_TRAIN_SHA256"]
WEIGHTS=pathlib.Path("training_weights/FROZEN_TRAINED_A_B_WEIGHTS.json")
SCORED=pathlib.Path("newprior_grade")

def grade_candidate(picked,arm_data,correct):
    if picked is None:return "HOLD"
    arm=arm_data[picked]
    if arm.get("status")!="VALID_UNGRADED" or not arm.get("source_valid"):
        return "HOLD"
    return "EXACT" if arm.get("future_prediction")==correct else "WRONG"

def main():
    import z3
    raw=(OUT/"UNSEEN12_FIRST_PROGRAM_SELECTIONS_BEFORE_GOLD.json").read_bytes()
    assert sha256(raw)==SEALED_FIRST,"UNSEALED_OR_CHANGED_FIRST"
    first=json.loads(raw)
    assert first["upstream"]==PIN and len(first["rows"])==12
    w_bytes=WEIGHTS.read_bytes()
    assert sha256(w_bytes)==SEALED_TRAIN==first["training_weight_sha256"]
    weight=json.loads(w_bytes)
    assert weight["test_gold_accessed"] is False and len(weight["weights"])==6
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    expected=[p.relative_to(ROOT).as_posix() for p in choose_paths()]
    assert expected==[r["name"] for r in first["rows"]]
    SCORED.mkdir(exist_ok=True)
    rows=[]
    for r in first["rows"]:
        o={"index":r["index"],"name":r["name"],"original_sha256":r["original_sha256"]}
        try:
            rawtask=(ROOT/r["name"]).read_bytes()
            assert sha256(rawtask)==r["original_sha256"]
            original=rawtask.decode("utf8")
            fs=top_level_forms(original)
            cs=[p for p in fs if get_cmd(p[2])=="constraint"]
            pairs=[io_form(p[2]) for p in cs]
            assert len(cs)==r["n_total_constraints"]
            assert sha256(cs[-2][2].encode())==r["probe_constraint_sha256"]
            assert sha256(cs[-1][2].encode())==r["future_constraint_sha256"]
            assert r["probe_input"]==pairs[-2][0] and r["future_input"]==pairs[-1][0]
            src=source_without_forms(original,cs[-2:])
            assert sha256(src.encode())==r["source_sha256"]
            source_set={x for x,y in pairs[:-2]}
            o["probe_input_new"]=pairs[-2][0] not in source_set
            o["future_input_new"]=pairs[-1][0] not in source_set
            if r["status"]!="ELIGIBLE":
                o["status"]="INELIGIBLE"
                rows.append(o)
                continue
            # Independently read raw FIRST stdout and verify program identity/grade.
            for j,arm in enumerate(r["arms"]):
                stdout=(OUT/f"{r['index']:02d}_{j}.stdout").read_bytes()
                assert sha256(stdout)==arm["stdout_sha256"]
                if arm["status"]=="VALID_UNGRADED":
                    program=proposal_function(stdout.decode("utf8","replace"))
                    assert sha256(program.encode())==arm["program_sha256"]
            policy={}
            for name,idx in r["selected"].items():
                policy[name]=grade_candidate(idx,r["arms"],pairs[-1][1])
            o["policy_grades"]=policy
            # Stronger native C1 uses the extra authentic penultimate label for all twelve.
            with_probe=source_without_forms(original,[cs[-1]])
            srcfile=SCORED/f"c1_{r['index']:02d}.sl"
            srcfile.write_text(with_probe)
            try:
                stdout,stderr,cost=bounded_cvc5(srcfile,["--seed=0"])
            finally:
                srcfile.unlink()
            o["c1_cost"]=cost
            o["c1_stdout_sha256"]=sha256(stdout.encode())
            try:
                if cost["exit_code"]!=0 or cost["forced"]:
                    raise ValueError("C1_RUNTIME_LIMIT")
                candidate=proposal_function(stdout)
                helper=helpers_for(with_probe)
                bodies=[]
                for p in cs[:-1]:
                    m=re.fullmatch(r"\(\s*constraint\s+(.*)\s*\)",p[2],re.S)
                    assert m
                    bodies.append(m.group(1))
                if not source_verified(z3,helper,candidate,bodies):
                    raise ValueError("C1_SOURCE_VIOLATION")
                pred=model_eval(helper,candidate,pairs[-1][0])
                o["c1"]="EXACT" if pred==pairs[-1][1] else "WRONG"
            except Exception as exc:
                o["c1"]="HOLD"
                o["c1_error"]=type(exc).__name__+":"+str(exc)[:150]
            o["status"]="GRADED"
        except Exception as exc:
            o["status"]="HOLD_GRADE_ERROR"
            o["error"]=type(exc).__name__+":"+str(exc)[:180]
        rows.append(o)
        print("MODEL_GRADE",o["index"],o["name"],o.get("policy_grades"),"C1",o.get("c1"),o["status"],flush=True)
    names=[f"{c}_{seed}" for c in ("A","B") for seed in (5,13,29)]+["MDL","C0","C1"]
    scores={}
    for name in names:
        scores[name]=dict(Counter((r.get("c1","HOLD") if name=="C1" else r.get("policy_grades",{}).get(name,"HOLD")) for r in rows))
    cpu_source_cvc5=sum(sum(a.get("cpu_user_s",0)+a.get("cpu_sys_s",0) for a in r["arms"]) for r in first["rows"])
    cpu_c0=sum(sum(a.get("cpu_user_s",0)+a.get("cpu_sys_s",0) for a in r["arms"][:1]) for r in first["rows"])
    cpu_c1=sum(r.get("c1_cost",{}).get("cpu_user_s",0)+r.get("c1_cost",{}).get("cpu_sys_s",0) for r in rows)
    report={"description":"real separate sealed-weight ownweight program selector A/B and matched classical original heldout twelve",
            "upstream":PIN,"sealed_original_first_sha256":SEALED_FIRST,
            "sealed_training_weights_sha256":SEALED_TRAIN,
            "n_original":12,"original_test_author_independence":"NOT_ESTABLISHED",
            "scores":scores,"cpu_source_three_program_portfolio_s":round(cpu_source_cvc5,6),
            "cpu_c0_s":round(cpu_c0,6),"cpu_c1_s":round(cpu_c1,6),
            "training_cpu_s":weight["training_cpu_seconds"],
            "whole_system_energy_and_total_cost":"UNKNOWN",
            "weights_cannot_invent_new_operators":True,
            "Q1_Q7":"OPEN","G1":"HOLD","rows":rows}
    file=SCORED/"POSTFIRST_NEW12_ORIGINAL_SGI_OWNWEIGHT_VS_CLASSICAL_GRADE.json"
    file.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("GRADED_SHA256",sha256(file.read_bytes()))
    print("SUMMARY",json.dumps({k:report[k] for k in
         ("scores","cpu_source_three_program_portfolio_s","cpu_c0_s","cpu_c1_s","training_cpu_s")},sort_keys=True),flush=True)
if __name__=="__main__":main()
