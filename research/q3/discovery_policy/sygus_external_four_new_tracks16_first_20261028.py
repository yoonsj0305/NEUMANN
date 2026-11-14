#!/usr/bin/env python3
"""Preregistered NEW four-track 16 originals: full native CVC5 1.4.2 FIRST.

No candidate returned is claimed valid until independent original semantics
are proved. Audit source feedback: PBE original *listed examples* != arbitrary
oracle target outputs; inductive proofs != unknown invariant target oracle.
"""
import collections,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_multifamily_classical_first_20261027 import run_solver

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
PREFIX="NEUMANN1_G1_EXTERNAL_NEW4TRACKS_20261028_v1/"
GROUPS=(
"lib/CLIA_Track/from_2018/",
"lib/Inv_Track/xujie_code2inv/",
"lib/PBE_BV_Track/from_2018/",
"lib/PBE_SLIA_Track/euphony/",
)
FIXED=(
"lib/CLIA_Track/from_2018/arraysearch20.sl",
"lib/CLIA_Track/from_2018/jmbl_fg_polynomial1.sl",
"lib/CLIA_Track/from_2018/jmbl_fg_mpg_example3.sl",
"lib/CLIA_Track/from_2018/jmbl_fg_array_sum_7_5.sl",
"lib/Inv_Track/xujie_code2inv/106.c.sl",
"lib/Inv_Track/xujie_code2inv/36_conf1.sl",
"lib/Inv_Track/xujie_code2inv/85_conf1.sl",
"lib/Inv_Track/xujie_code2inv/64.c.sl",
"lib/PBE_BV_Track/from_2018/PRE_20_10.sl",
"lib/PBE_BV_Track/from_2018/PRE_10_100.sl",
"lib/PBE_BV_Track/from_2018/PRE_27_1000.sl",
"lib/PBE_BV_Track/from_2018/PRE_icfp_gen_1.5.sl",
"lib/PBE_SLIA_Track/euphony/get-last-name-from-name-with-comma.sl",
"lib/PBE_SLIA_Track/euphony/count-consecutive-monthly-orders.sl",
"lib/PBE_SLIA_Track/euphony/get-first-word.sl",
"lib/PBE_SLIA_Track/euphony/25239569.sl",
)
FIXED_SHA="a24acb1fed0d195b48e08bcffbc27f5af2d06eefcd98937f326236798f4b1295"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_4track16_FIRST")
CVC5_ZIP_SHA="0af677313c8277dc558d3049b192389db4d975d31c968fbd6f31cf0849ee411d"

def choose():
    names=subprocess.check_output(
        ["git","-C",str(ROOT),"ls-tree","-r","--name-only","HEAD"],text=True).splitlines()
    picked=[]
    for group in GROUPS:
        candidates=[p for p in names if p.startswith(group) and p.endswith(".sl")]
        candidates.sort(key=lambda p:(sha256((PREFIX+p).encode()),p))
        picked.extend(candidates[:4])
    assert tuple(picked)==FIXED,(picked,FIXED)
    assert sha256("\n".join(FIXED).encode())==FIXED_SHA
    return picked

def classify_source(raw):
    forms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(raw.decode("utf8"))]
    cnt=collections.Counter(c for c,_ in forms)
    names=[m.group(1) for c,f in forms if c in ("synth-inv","synth-fun")
           for m in [re.match(r"^\(\s*(?:synth-inv|synth-fun)\s+([^\s()]+)",f)] if m]
    cs=[f for c,f in forms if c=="constraint"]
    pbe=0
    for constraint in cs:
        if any(re.search(r"^\(\s*constraint\s+\(=\s+\(\s*"+re.escape(n)+r"(?:\s|\))",
                          constraint) for n in names):
            pbe+=1
    return {
      "original_top_level_form_counts":{k:cnt[k] for k in sorted(cnt)},
      "original_synth_symbols":names,
      "source_ground_direct_f_examples_count":pbe,
      "source_other_constraints":len(cs)-pbe,
      "original_declared_vars":cnt["declare-var"],
      "original_invariant_constraints":cnt["inv-constraint"],
      "arbitrary_target_output_oracle_provided":False,
      "source_feedback_contract":(
        "LISTED_PBE_EXAMPLES_ONLY__NO_ARBITRARY_TARGET_LABEL"
        if pbe and pbe==len(cs) and cnt["inv-constraint"]==0 else
        "FORMAL_SPEC_COUNTEREXAMPLE_VERIFIER__NO_ARBITRARY_TARGET_LABEL"
      ),
      "classification_caution":"A published example may be a hard constraint, not a callable oracle"}
def main():
    assert subprocess.check_output(
        ["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(
        ["cvc5","--version"],text=True).strip().splitlines()[0].startswith("cvc5 1.4.2 ")
    paths=choose()
    OUT.mkdir(exist_ok=True)
    rows=[]
    for i,rel in enumerate(paths):
        raw=(ROOT/rel).read_bytes()
        row={"index":i,"family":next(g for g in GROUPS if rel.startswith(g)),
             "original":rel,"source_sha256":sha256(raw),"source_bytes":len(raw),
             "strong_full_original_given":True,"returned_program_independent_grade":"NOT_RUN"}
        try:
            row.update(classify_source(raw))
        except Exception as e:
            row["source_classification_error"]=type(e).__name__+":"+str(e)[:240]
        try:
            stdout,stderr,cost=run_solver(ROOT/rel)
            (OUT/(f"{i:02d}_cvc5.stdout")).write_text(stdout)
            (OUT/(f"{i:02d}_cvc5.stderr")).write_text(stderr)
            row["native_cost"]=cost
            row["native_define_fun_count"]=len(re.findall(r"\(\s*define-fun\b",stdout))
            if cost["forced"] or cost["returncode"] in (-9,-6,-24):
                row["status"]="STRONG_C_BUDGET_HOLD"
            elif cost["returncode"]!=0 or re.search(r"\(error|parse error|unsupported|exception",
                     stdout+"\n"+stderr,re.I):
                row["status"]="HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED"
            elif row["native_define_fun_count"]>0:
                row["status"]="STRONG_C_CANDIDATE_UNVERIFIED"
            elif "infeasible" in stdout.lower():
                row["status"]="HOLD_NATIVE_INFEASIBLE_CLAIM_UNPROVED"
            else:
                row["status"]="HOLD_NATIVE_NO_PROGRAM"
        except Exception as e:
            row["status"]="HOLD_EXECUTOR"
            row["error"]=type(e).__name__+":"+str(e)[:240]
        print("EXTERNAL4TRACK_FIRST",i,rel,row["status"],flush=True)
        rows.append(row)
    counts=dict(collections.Counter(x["status"] for x in rows))
    by_group={}
    for group in GROUPS:
        by_group[group]=dict(collections.Counter(
            r["status"] for r in rows if r["family"]==group))
    receipt={
       "status":"STRONG_CLASSICAL_FIRST_UNGRADED_ORIGINAL16",
       "source":"SyGuS-Org/benchmarks","original_git_commit":PIN,
       "prereg_order_sha256":FIXED_SHA,"prereg_paths":list(FIXED),
       "official_native_cvc5_release_zip_sha256":CVC5_ZIP_SHA,
       "task_denominator":16,"native_status_counts":counts,"group_counts":by_group,
       "proposed_neural_training":"NOT_RUN",
       "classical_candidate_proof":"NOT_RUN",
       "source_oracle_rights":"NEVER_INFER_ARBITRARY_TARGET_ORACLE",
       "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
       "rows":rows}
    p=OUT/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json"
    p.write_text(json.dumps(receipt,sort_keys=True,indent=2))
    print("FIRST_RESULT_SHA256",sha256(p.read_bytes()))
    print("FIRST_COUNTS",json.dumps(counts,sort_keys=True))
    print("FIRST_CPU_SECONDS",round(sum(r.get("native_cost",{}).get("cpu_user_seconds",0)+
              r.get("native_cost",{}).get("cpu_system_seconds",0) for r in rows),6))
if __name__=="__main__":main()
