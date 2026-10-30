#!/usr/bin/env python3
"""POST-FIRST independent original semantic check of five immutable native CVC5
program-list outputs. No new synthesis. Keep 3 timeouts and 8 template H0.

Native CVC5 1.4.2 returns outer wrapped list of 2/3 function defs:
( (define-fun D ...) (define-fun R ...) ... )
Original FIRST incorrectly expected exactly 3 direct top-level defs.
"""
import collections,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_dangerloop_unseen8_classical_template_transfer_20261027 import (
 ROOT,PIN,FROZEN_ORDER,FROZEN_ORDER_SHA,split_source,only_symbol,z3_all_actual
)

FIRST_SHA="57df20f0c54f2c22965e3a6b104def1a529ccf58bbc645fedd4695aa041b4c3d"
FIRST=pathlib.Path("official_danger8_frozen_first")
OUT=pathlib.Path("official_danger8_independent_z3_grade")
def unwrap_sygus_output(stdout):
    content=stdout.strip()
    if not content:raise ValueError("EMPTY_OUTPUT")
    forms=top_level_forms(content)
    if len(forms)==1 and get_cmd(forms[0][2])=="(":
        inner=content[1:-1].strip()
        forms=top_level_forms(inner)
    elif len(forms)==1 and content.startswith("(") and re.match(r"^\(\s*\(",content):
        forms=top_level_forms(content[1:-1])
    defs=[f[2] for f in forms if get_cmd(f[2])=="define-fun"]
    if len(defs)!=len(forms):raise ValueError("NON_FUNCTION_OUTPUT")
    if not defs:raise ValueError("NO_FUNCTIONS_FOUND")
    names=[only_symbol(x,"define-fun") for x in defs]
    if len(names)!=len(set(names)):raise ValueError("DUPLICATE_SYMBOL")
    return defs,names

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    original=(FIRST/"DANGERLOOP_SAME_AUTHOR_PROSPECTIVE_EIGHT_TEMPLATE_VS_CVC5_142.json").read_bytes()
    assert sha256(original)==FIRST_SHA
    data=json.loads(original)
    assert [x["original_path"] for x in data["rows"]]==FROZEN_ORDER
    assert data["filename_selection_sha256"]==FROZEN_ORDER_SHA
    OUT.mkdir(exist_ok=True)
    rows=[]
    for r in data["rows"]:
        ix=r["index"];path=r["original_path"];entry={
            "index":ix,"path":path,"original_sha256":r["original_sha256"],
            "native_first_status":r["native_classical_status"],
            "template_first_status":r["template_status"],
            "postfirst_independent_status":"HOLD"}
        source=(ROOT/path).read_bytes()
        assert sha256(source)==r["original_sha256"]
        if r["native_classical_status"]=="C_BUDGET_HOLD":
            entry["postfirst_independent_status"]="NATIVE_C_BUDGET_HOLD_UNCHANGED"
            rows.append(entry)
            print("Z3_ORIGINAL_CLASSICAL_RECHECK",path,entry["postfirst_independent_status"],flush=True)
            continue
        b=(FIRST/f"{ix:02d}_native.stdout").read_bytes()
        assert sha256(b)==r["native_cost"]["stdout_sha256"]
        try:
            f,help,synth,con,dec=split_source(source.decode())
            if "synth-inv" in [cmd for cmd,_ in f] or "inv-constraint" in [cmd for cmd,_ in f]:
                raise ValueError("ORIGINAL_INVARIANT_SYNTAX_NEEDS_PROPER_VC")
            defs,names=unwrap_sygus_output(b.decode("utf8","replace"))
            assert len(names)==len(synth),("NUMBER_ORIGINAL_SYNTH_FUNCTIONS",names,list(synth))
            assert set(names)==set(synth),("UNEXPECTED_SYNTH_NAMES",names,list(synth))
            entry["candidate_names"]=names
            entry["candidate_definition_sha256"]=sha256("\n".join(defs).encode())
            outcomes=z3_all_actual(f,con,defs)
            entry["z3_obligations"]=outcomes
            if all(x["z3"]=="unsat" for x in outcomes):
                entry["postfirst_independent_status"]="C_PROGRAM_Z3_PROVED_ALL_ORIGINAL_CONSTRAINTS"
            elif any(x["z3"]=="sat" for x in outcomes):
                entry["postfirst_independent_status"]="C_PROGRAM_COUNTEREXAMPLE_FOUND"
            else:entry["postfirst_independent_status"]="HOLD_Z3_UNKNOWN"
        except Exception as e:
            entry["postfirst_independent_status"]="HOLD_Z3_PARSER_OR_SPEC_UNSUPPORTED"
            entry["error"]=type(e).__name__+":"+str(e)[:200]
        rows.append(entry)
        print("Z3_ORIGINAL_CLASSICAL_RECHECK",path,entry["postfirst_independent_status"],flush=True)
    assert len(rows)==8
    result={
      "study":"POSTFIRST_INDEPENDENT_NATIVE_C_WRAPPED_LIST_VERIFICATION_NO_REEXECUTION",
      "original_upstream":PIN,"first_json_sha256":FIRST_SHA,
      "exact_eight_rows":8,"matched_full_original_source_sha256":True,
      "z3_version":z3.get_version_string(),
      "native_cpu_first_not_modified":True,
      "template_prospective_napplicable":8,
      "summary":dict(collections.Counter(x["postfirst_independent_status"] for x in rows)),
      "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
      "rows":rows}
    p=OUT/"POSTFIRST_DANGER8_ORIGINAL_CVC5_142_Z3_VERIFIED.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True))
    print("GRADE_SHA256",sha256(p.read_bytes()))
    print("SUMMARY",json.dumps(result["summary"],sort_keys=True))
if __name__=="__main__":main()
