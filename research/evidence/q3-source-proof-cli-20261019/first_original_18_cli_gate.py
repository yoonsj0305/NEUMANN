"""One frozen Q3 deployability regression: same 18 previously opened originals.
Not fresh unseen-family proof and not a global Q3 closure.
Preregd issue #245 BEFORE implementation.
"""
import argparse
import hashlib
import json
import tempfile
import subprocess
import sys
from collections import Counter
from pathlib import Path
from experiments.q3_source_prove import prove_source,replay_exported_queries
from first_original_branch_nullspace import sample
from first_proof_gated_lazy_fallback import FIXED_EIGHT

def run(root):
    original_paths=list(sample(root))+[root/name for name in FIXED_EIGHT]
    if len(original_paths)!=18 or len({str(x) for x in original_paths})!=18:
        raise ValueError("NOT_EXACT_18_HISTORICAL_OPENED_ORIGINALS")
    cases=[]
    for path in original_paths:
        outcome=prove_source(path)
        if outcome.get("source_sha256")!=hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError("SOURCE_HASH_MISMATCH")
        row={"path":path.relative_to(root).as_posix(),
            "source_sha256":outcome["source_sha256"],
            "status":outcome["status"],
            "selected_route":outcome.get("selected_route"),
            "replay_of_explicit_three_vc":replay_exported_queries(outcome),
            "certificate_scope":outcome.get("certificate_scope"),
            "source_native_custom_xor":outcome.get("independent_native_custom_parser_xor"),
            "all_three_smt2_sha256":{
                k:v["sha256"] for k,v in
                (outcome.get("original_bad_condition_smt2") or {}).items()},
            "original_3vc":outcome.get("original_three_vc"),
            "rejected_reason":outcome.get("reason")}
        if outcome["status"]=="ORIGINAL_SOURCE_THREE_VC_CERTIFIED":
            assert row["replay_of_explicit_three_vc"]
            assert set(row["all_three_smt2_sha256"])=={"initial","consecution","post"}
            assert all(s=="unsat" for s in row["original_3vc"].values())
        elif outcome["status"]=="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT":
            assert row["replay_of_explicit_three_vc"] is False
            assert not row["all_three_smt2_sha256"]
            assert outcome.get("original_three_vc") is None
        cases.append(row)
    # CLI through actual -m entrypoint on one historical source path.
    with tempfile.TemporaryDirectory() as temp:
        t=Path(temp)
        output=t/"example_receipt.json"
        sample_src=original_paths[0]
        proc=subprocess.run([sys.executable,"-m","experiments.q3_source_prove",
            "--source",str(sample_src),"--out",str(output)],
            capture_output=True,text=True,timeout=40)
        if proc.returncode!=0 or not output.is_file():
            raise AssertionError("ACTUAL_STANDALONE_CLI_FAIL:"+proc.stderr[-300:])
        cli_result=json.loads(output.read_text())
        if cli_result.get("status") not in (
            "ORIGINAL_SOURCE_THREE_VC_CERTIFIED","ORIGINAL_SOURCE_ONLY_SPACER_UNSAT"):
            raise AssertionError("ACTUAL_STANDALONE_ORIGINAL_SOURCE_NOT_PROVEN")
        # Negative controls, no proof string injected.
        malformed=t/"malformed.sl"
        malformed.write_text("(synth-inv inv badSyntax")
        bad=prove_source(malformed)
        if bad.get("status")!="ABSTAIN":
            raise AssertionError("MALFORMED_SOURCE_FALSE_ACCEPTED")
        wrong_suffix=t/"bad.py"
        wrong_suffix.write_text("print('untrusted')")
        if prove_source(wrong_suffix)["status"]!="ABSTAIN":
            raise AssertionError("WRONG_EXTENSION_FALSE_ACCEPTED")
        # An altered query is never allowed to pass replay, even if hash is recomputed.
        certified=prove_source(original_paths[0])
        if certified["status"]!="ORIGINAL_SOURCE_THREE_VC_CERTIFIED":
            raise AssertionError("MISSING_NEGATIVE_CONTROL_CERTIFIED_SOURCE")
        wrong_cert=json.loads(json.dumps(certified))
        one=wrong_cert["original_bad_condition_smt2"]["initial"]
        one["query"]="(set-logic QF_LIA)\n(assert true)\n(check-sat)\n"
        one["sha256"]=hashlib.sha256(one["query"].encode()).hexdigest()
        if replay_exported_queries(wrong_cert):
            raise AssertionError("WRONG_SMT_QUERY_ACCEPTED")
        missing_cert=json.loads(json.dumps(certified))
        del missing_cert["original_bad_condition_smt2"]["post"]
        if replay_exported_queries(missing_cert):
            raise AssertionError("MISSING_VC_ACCEPTED")
    hist=Counter(x["status"] for x in cases)
    safe=sum(v for k,v in hist.items() if k in (
        "ORIGINAL_SOURCE_THREE_VC_CERTIFIED","ORIGINAL_SOURCE_ONLY_SPACER_UNSAT"))
    nontrivial=sum(c["selected_route"] in (
        "OCTAGON_HOUDINI","BRANCH_AFFINE_NULLSPACE") for c in cases)
    all_sources_parity=all(
        set(c["source_native_custom_xor"])=={"pre","trans","post"} and
        all(x=="unsat" for x in c["source_native_custom_xor"].values()) for c in cases)
    return {"study":"Q3_SOURCE_INPUT_PROOF_CLI_18_OPENED_REGRESSION_FIRST",
        "preregistration_issue":245,"status":"FIRST_REGRESSION_RECORDED",
        "source_originals":18,"input_source_git_revision":
            "6ac90265b11431c9477dfbd33e3e3380234c0499",
        "cases":cases,"counts":dict(hist),
        "safe_source_decisions":safe,
        "explicit_replayable_inductive_three_vc":hist.get(
            "ORIGINAL_SOURCE_THREE_VC_CERTIFIED",0),
        "source_only_spacer_without_inductive_certificate":hist.get(
            "ORIGINAL_SOURCE_ONLY_SPACER_UNSAT",0),
        "non_postonly_source_3vc":nontrivial,
        "three_semantic_XOR_all_originals":all_sources_parity,
        "all_sources_unique":len({c["source_sha256"] for c in cases})==18,
        "negative_controls":{"malformed_input":"ABSTAIN",
            "unsupported_suffix":"ABSTAIN","rewritten_bad_smt_query":"REJECTED",
            "missing_smt_obligation":"REJECTED"},
        "first_gate_pass":safe==18 and
            hist.get("ORIGINAL_SOURCE_THREE_VC_CERTIFIED",0)==16 and
            hist.get("ORIGINAL_SOURCE_ONLY_SPACER_UNSAT",0)==2 and
            all_sources_parity and
            len({c["source_sha256"] for c in cases})==18,
        "learned_new_math":False,"model_calls":0,
        "no_fresh_unseen_family":True,"global_Q3":"OPEN","global_Q1_Q7":"OPEN"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=run(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("Q3_DEPLOYABLE_CLI_FIRST",r["counts"],"gate",r["first_gate_pass"])
    print("Q3_DEPLOYABLE_CLI_GLOBAL",r["global_Q3"])
    for c in r["cases"]:
        print("Q3_SOURCE_PROOF_RESULT",c["path"],c["selected_route"],c["status"])
if __name__=="__main__":main()
