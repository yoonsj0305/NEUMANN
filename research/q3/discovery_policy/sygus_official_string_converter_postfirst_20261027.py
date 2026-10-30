#!/usr/bin/env python3
"""Official independent SyGuS version converter POST-FIRST ONLY.

Exactly four original EUPHONY SyGuS1-vs2 parser failures, untouched source
identities. Preserves immutable original 16 task first SHA. No learned AI.
"""
import hashlib,json,os,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sygus_official_multifamily_classical_first_20261027 import (
    ROOT,PIN,run_solver,hash_data
)
TOOLS=pathlib.Path("official_tools")
ORIGINAL_FIRST="a648346b162b3c76d4c60283f339c1a3c54016ad374128c1b4135453c27a5ba5"
PATHS=[
"lib/PBE_SLIA_Track/euphony/convert-text-to-numbers.sl",
"lib/PBE_SLIA_Track/euphony/find-nth-occurrence-of-character.sl",
"lib/PBE_SLIA_Track/euphony/phone-5-short.sl",
"lib/PBE_SLIA_Track/euphony/35744094.sl",
]
OUT=pathlib.Path("official_string_converter")

def gitsha(p):
    return subprocess.check_output(["git","-C",str(p),"rev-parse","HEAD"],text=True).strip()

def count_forms(s,op):
    return len(re.findall(r"\(\s*"+op+r"(?=\s|\))",s))

def main():
    assert gitsha(ROOT)==PIN
    tools_sha=gitsha(TOOLS)
    OUT.mkdir(exist_ok=True)
    rows=[]
    for rel in PATHS:
        p=ROOT/rel;original=p.read_bytes()
        result={"path":rel,"original_source_sha256":hash_data(original),
                "official_converter_sha":tools_sha,
                "native_first_sha256":ORIGINAL_FIRST,
                "first_failure":"NATIVE_CVC5_SYGUS2_PARSE_ERROR",
                "independent_solution_grade":"NOT_RUN",
                "stage":"POSTFIRST_CONVERSION","status":"HOLD"}
        env=os.environ.copy()
        env["PYTHONPATH"]=str(TOOLS.resolve())
        cp=subprocess.run([sys.executable,"-m","sygus.bin.convert","-s","1","-t","2",str(p.resolve())],
                          cwd=".",env=env,text=True,stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,timeout=45)
        s=cp.stdout
        tag=rel.replace("/","__")
        (OUT/(tag+".convert.stderr")).write_text(cp.stderr)
        (OUT/(tag+".convert.stdout")).write_text(s)
        result.update(converter_exit_code=cp.returncode,
              converted_source_sha256=hash_data(s.encode()),
              conversion_stdout_size=len(s.encode()),
              conversion_stderr_sha256=hash_data(cp.stderr.encode()))
        expected_constraint=count_forms(original.decode("utf8"),"constraint")
        actual_constraint=count_forms(s,"constraint")
        result.update(original_constraints=expected_constraint,
                      converted_constraints=actual_constraint,
                      original_checksynth=count_forms(original.decode("utf8"),"check-synth"),
                      converted_checksynth=count_forms(s,"check-synth"))
        if cp.returncode!=0:
            result["status"]="HOLD_OFFICIAL_CONVERTER_ERROR"
        elif expected_constraint!=actual_constraint or result["original_checksynth"]!=1 or result["converted_checksynth"]!=1:
            result["status"]="HOLD_CONVERSION_CONSTRAINT_COUNT_CHANGE"
        elif len(s)<50:
            result["status"]="HOLD_CONVERTED_EMPTY"
        else:
            temp=OUT/(tag+".sl")
            temp.write_text(s)
            stdout,stderr,cost=run_solver(temp)
            temp.unlink()
            (OUT/(tag+".cvc5.stdout")).write_text(stdout)
            (OUT/(tag+".cvc5.stderr")).write_text(stderr)
            result.update(cost)
            count=len(re.findall(r"\(\s*define-fun\s+",stdout))
            result["native_synth_candidates"]=count
            error=(stdout+"\n"+stderr).lower()
            if cost["forced"] or cost["returncode"] in (-6,-9,-24):
                result["status"]="C_CONVERTED_BUDGET_HOLD"
            elif cost["returncode"]!=0 or re.search(r"\(error|error:|exception|unsupported",error):
                result["status"]="HOLD_CONVERTED_NATIVE_ERROR"
            elif count:
                result["status"]="C_CONVERTED_PROGRAM_UNVERIFIED"
            else:
                result["status"]="HOLD_CONVERTED_NO_PROGRAM"
        rows.append(result)
        print("CONVERTED_C_FIRST",rel,result["status"],result.get("wall_seconds"),flush=True)
    output={
        "source":"SyGuS-Org/benchmarks","upstream_benchmark_sha":PIN,
        "upstream_converter_source":"SyGuS-Org/tools",
        "upstream_converter_sha":tools_sha,
        "original_C16_first_json_sha256":ORIGINAL_FIRST,
        "experiment":"POST_FIRST_FIXED_FOUR_PARSE_ERRORS_WITH_OFFICIAL_V1_TO_V2",
        "all_original_tasks_reported":True,
        "neural_training":"NOT_RUN","global_Q1_Q7":"OPEN","G1":"HOLD",
        "rows":rows,
    }
    p=OUT/"OFFICIAL_PBE_SLIA_V1_TO_V2_POSTFIRST_NATIVE_C_GRADE.json"
    p.write_text(json.dumps(output,indent=2,sort_keys=True))
    print("RESULT_SHA256",hash_data(p.read_bytes()),flush=True)
if __name__=="__main__":main()
