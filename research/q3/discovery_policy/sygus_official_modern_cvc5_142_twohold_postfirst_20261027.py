#!/usr/bin/env python3
"""POSTFIRST two original official CVC5 1.1.2 budget-holds with newest CVC5 1.4.2.

No new tasks, no relabel, no model training, no oracle data. Same original full
SyGuS source, same 12 CPU/15 wall/800 MiB as frozen original FIRST.
"""
import hashlib,json,os,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sygus_official_multifamily_classical_first_20261027 import ROOT,PIN,run_solver,hash_data

OLD_FIRST="a648346b162b3c76d4c60283f339c1a3c54016ad374128c1b4135453c27a5ba5"
OLD=pathlib.Path("official_old_cvc5_first/OFFICIAL_C16_FIRST_UNGRADED_CLASSICAL_HEADROOM.json")
NEW=pathlib.Path("official_cvc5_142_retest")
EXACT_PATHS=[
  "lib/General_Track/cegist-cav18/inv/danger-loop21.sl",
  "lib/Inv_Track/xujie_code2inv/95.c.sl",
]
ASSET_SHA="0af677313c8277dc558d3049b192389db4d975d31c968fbd6f31cf0849ee411d"

def main():
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert hash_data(OLD.read_bytes())==OLD_FIRST
    old=json.loads(OLD.read_text())
    originals={r["path"]:r for r in old["results"]}
    assert sorted(r["path"] for r in old["results"] if r["status"]=="C_BUDGET_HOLD")==sorted(EXACT_PATHS)
    version=subprocess.check_output(["cvc5","--version"],text=True,stderr=subprocess.STDOUT).strip()
    print("MODERN_SOLVER_VERSION",version.splitlines()[0],flush=True)
    assert version.splitlines()[0].startswith("cvc5 1.4.2 "), "WRONG_SOLVER_VERSION"
    NEW.mkdir(exist_ok=True)
    rows=[]
    for rel in EXACT_PATHS:
        orig=originals[rel];b=(ROOT/rel).read_bytes()
        assert hash_data(b)==orig["original_source_sha256"]
        stdout,stderr,cost=run_solver(ROOT/rel)
        tag=rel.replace("/","__")
        (NEW/(tag+".stdout")).write_text(stdout)
        (NEW/(tag+".stderr")).write_text(stderr)
        n=stdout.count("(define-fun")
        errors=stdout.lower()+"\n"+stderr.lower()
        if cost["forced"] or cost["returncode"] in (-6,-9,-24):
            status="MODERN_C_BUDGET_HOLD"
        elif cost["returncode"]!=0 or "(error" in errors or "unsupported" in errors or "exception" in errors:
            status="HOLD_MODERN_SOLVER_ERROR_OR_UNSUPPORTED"
        elif n:
            status="MODERN_C_PROGRAM_UNVERIFIED"
        else:status="HOLD_MODERN_NO_EXECUTABLE_PROGRAM"
        record={"path":rel,"original_file_sha256":orig["original_source_sha256"],
                "historical_cvc5_112_wall":orig["wall_seconds"],
                "historical_cvc5_112_status":orig["status"],
                "modern_solver_version_first_line":version.splitlines()[0],
                "modern_release_asset_zip_sha256":ASSET_SHA,
                "define_fun_count":n,"status":status,
                "candidate_independent_verification":"NOT_RUN",
                **cost}
        rows.append(record)
        print("MODERN_CVC5_MATCHED",rel,status,cost["wall_seconds"],flush=True)
    receipt={"original_upstream_commit":PIN,"original_first_json_sha256":OLD_FIRST,
        "official_newest_solver_version":version.splitlines()[0],
        "official_release_asset_sha256":ASSET_SHA,
        "scope":"POSTFIRST_TWO_BUDGET_HOLD_CLASSICAL_VERSION_PARITY_NO_NEURAL",
        "denominator":2,"global_Q1_Q7":"OPEN","G1":"HOLD","rows":rows}
    p=NEW/"POSTFIRST_OFFICIAL_TWO_HOLDS_CVC5_142_MATCHED.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print("RESULT_SHA256",hash_data(p.read_bytes()),flush=True)
if __name__=="__main__":main()
