#!/usr/bin/env python3
"""Read-only fault taxonomy for FOUR frozen original PBE-SLIA CVC5 stderr files.

No new synthesis, no tampering with original first. Distinguish parser source
support errors from candidate-generation failure and original task infeasible.
"""
import collections,json,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import sha256
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_new16_frozen_FIRST")
OUT=pathlib.Path("external_slIA_original_error_diagnosis")
def main():
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    frozen=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(frozen)==FIRST_SHA
    rows=json.loads(frozen)["rows"]
    assert [r["original"] for r in rows]==list(FIXED)
    audited=[]
    for i in range(12,16):
        row=rows[i]
        assert row["status"]=="HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED"
        raw=(ROOT/row["original"]).read_bytes()
        assert sha256(raw)==row["source_sha256"]
        stderr=(FIRST/f"{i:02d}_cvc5.stderr").read_bytes()
        stdout=(FIRST/f"{i:02d}_cvc5.stdout").read_bytes()
        assert sha256(stderr)==row["native_cost"]["stderr_sha256"]
        assert sha256(stdout)==row["native_cost"]["stdout_sha256"]
        detail=stderr.decode("utf8","replace").strip()
        if not detail:
            classification="NATIVE_UNKNOWN_NO_STDERR"
        elif "parse" in detail.lower() or "unexpected" in detail.lower() or "parser" in detail.lower():
            classification="NATIVE_ORIGINAL_PARSER_ERROR"
        elif "unsupported" in detail.lower() or "not supported" in detail.lower():
            classification="NATIVE_SOURCE_FEATURE_UNSUPPORTED"
        else:
            classification="NATIVE_ERROR_OTHER_UNPROVEN"
        audited.append({
            "index":i,"original":row["original"],"source_sha256":row["source_sha256"],
            "classification":classification,
            "native_stderr":detail[:1600],
            "native_returncode":row["native_cost"]["returncode"],
            "no_claim_task_unsatisfiable":True,
        })
        print("EXTERNAL_SLIA_FIRST_DIAG",i,classification,repr(detail[:380]),flush=True)
    OUT.mkdir(exist_ok=True)
    out={"scope":"READ_ONLY_NATIVE_ORIGINAL_FROZEN_ERRORS",
         "first_sha256":FIRST_SHA,"original_commit":PIN,
         "complete_4_slIA_rows":4,
         "original_native_first_untouched":True,
         "interpretation":"No semantic solver capability or proof conclusions from parser errors",
         "G1":"HOLD","Q1_Q7":"OPEN","cases":audited}
    p=OUT/"EXTERNAL16_SLIA_FOUR_NATIVE_ERROR_CAUSES.json"
    p.write_text(json.dumps(out,sort_keys=True,indent=2))
    print("SLIA_NATIVE_ERROR_CAUSE_SHA256",sha256(p.read_bytes()))
if __name__=="__main__":main()
