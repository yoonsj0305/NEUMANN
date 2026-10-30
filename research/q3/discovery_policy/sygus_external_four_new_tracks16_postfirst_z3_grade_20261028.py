#!/usr/bin/env python3
"""POST-FIRST full original semantic verification of frozen external16 CVC5 outputs.

Original first was selected and recorded BEFORE this checker. Never re-synthesizes
a candidate. Checks all original source SHA and all same-right constraints.
For ordinary CLIA/PBE, one Z3 negated conjunction checks ALL source constraints;
for synth-inv, original three genuine induction VCs are independently checked.
"""
import collections,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import (
    unwrap_native,form_name,parameter_signature,source_prefix,check_z3,independent_grade)
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED

FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_4track16_FROZEN_FIRST")
OUT=pathlib.Path("external_4track16_postfirst_semantic")

def verify_ordinary(original,output):
    forms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(original)]
    defs=unwrap_native(output)
    synt=[f for c,f in forms if c=="synth-fun"]
    src_names={form_name(f,"synth-fun"):parameter_signature(
        f,"synth-fun",form_name(f,"synth-fun")) for f in synt}
    assert len(defs)==len(synt) and len(defs)>0,"SYGUS_FUNCTION_COUNT_MISMATCH"
    assert {form_name(f,"define-fun") for f in defs}==set(src_names),"WRONG_FUNCTION_NAMES"
    for d in defs:
        n=form_name(d,"define-fun")
        assert [t for _,t in parameter_signature(d,"define-fun",n)]==[
            t for _,t in src_names[n]],"SORT_ARITY_MISMATCH"
    clauses=[]
    for c,form in forms:
        if c=="constraint":
            m=re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",form,re.S)
            assert m,"MALFORMED_ORIGINAL_CONSTRAINT"
            clauses.append(m.group(1))
    assert clauses and not [1 for c,_ in forms if c=="inv-constraint"]
    assertion=clauses[0] if len(clauses)==1 else "(and "+" ".join(clauses)+")"
    script="\n".join(source_prefix(forms)+defs)+"\n(assert (not "+assertion+"))\n"
    OUT.mkdir(exist_ok=True)
    return clauses,script,check_z3(script)

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    raw=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(raw)==FIRST_SHA,("FIRST_JSON_NOT_IMMUTABLE",sha256(raw))
    doc=json.loads(raw)
    assert len(doc["rows"])==16
    assert tuple(x["original"] for x in doc["rows"])==FIXED
    OUT.mkdir(exist_ok=True)
    result=[]
    for row in doc["rows"]:
        i=row["index"];rel=row["original"]
        original=(ROOT/rel).read_bytes()
        assert sha256(original)==row["source_sha256"]
        line={"index":i,"source":rel,"original_source_sha256":row["source_sha256"],
              "first_status_unchanged":row["status"],"postfirst_grade":"HOLD"}
        if row["status"]=="STRONG_C_CANDIDATE_UNVERIFIED":
            b=(FIRST/(f"{i:02d}_cvc5.stdout")).read_bytes()
            assert sha256(b)==row["native_cost"]["stdout_sha256"]
            try:
                commands=[get_cmd(f[2]) for f in top_level_forms(original.decode())]
                if "inv-constraint" in commands:
                    checked=independent_grade(row,original.decode(),b.decode("utf8","replace"))
                    line["source_constraint_count"]=0
                    line["inductive_vc_results"]=checked["original_formal_proof_obligations"]
                    line["postfirst_grade"]=(
                      "ORIGINAL_FULL_3VC_Z3_PROVED"
                      if checked["grade"]=="VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS"
                      and len(line["inductive_vc_results"])==3
                      else "HOLD_INDUCTIVE_CEX_OR_UNKNOWN")
                else:
                    clauses,script,outcome=verify_ordinary(original.decode(),b.decode("utf8","replace"))
                    path=OUT/(f"{i:02d}_original_all_constraints_negated_Z3.smt2")
                    path.write_text(script)
                    line["source_constraint_count"]=len(clauses)
                    line["single_full_source_conjunction_Z3"]=outcome
                    line["full_proof_query_sha256"]=sha256(script.encode())
                    line["postfirst_grade"]=(
                       "ORIGINAL_FULL_SOURCE_Z3_PROVED" if outcome["z3_answer"]=="unsat"
                       else "HOLD_COUNTEREXAMPLE_OR_UNKNOWN")
            except Exception as ex:
                line["postfirst_grade"]="HOLD_CHECKER_OR_SOURCE_NOT_SUPPORTED"
                line["error"]=type(ex).__name__+":"+str(ex)[:250]
        elif row["status"]=="STRONG_C_BUDGET_HOLD":
            line["postfirst_grade"]="ORIGINAL_BUDGET_HOLD_UNCHANGED"
        elif row["status"]=="HOLD_NATIVE_INFEASIBLE_CLAIM_UNPROVED":
            line["postfirst_grade"]="ORIGINAL_INFEASIBILITY_UNPROVED"
        else:
            line["postfirst_grade"]="ORIGINAL_NATIVE_PARSE_OR_EXECUTOR_HOLD"
        result.append(line)
        print("EXTERNAL16_ORIGINAL_FULL_PROOF",i,line["postfirst_grade"],flush=True)
    stats=dict(collections.Counter(x["postfirst_grade"] for x in result))
    result_doc={
       "status":"POSTFIRST_INDEPENDENT_FULL_SOURCE_ORIGINAL_PROOF",
       "actual_pinned_original":PIN,
       "first_original_source_C_receipt_sha256":FIRST_SHA,
       "total_originals":16,"z3_version":z3.get_version_string(),
       "no_original_re_synthesis":True,
       "inductive_requires_three_real_VCs":True,
       "ordinary_all_original_conditions_conjoined":True,
       "original_grammar_membership_independently_proven":False,
       "per_status":stats,"G1":"HOLD","global_Q1_Q7":"OPEN","G2":"NOT_RUN",
       "rows":result}
    p=OUT/"NEUMANN_G1_EXTERNAL_NEW16_CVC5_POSTFIRST_INDEPENDENT_Z3.json"
    p.write_text(json.dumps(result_doc,indent=2,sort_keys=True))
    print("FULL_PROOF_REPORT_SHA256",sha256(p.read_bytes()),flush=True)
    print("FULL_PROOF_RESULTS",json.dumps(stats,sort_keys=True),flush=True)
if __name__=="__main__":main()
