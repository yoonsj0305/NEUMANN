"""ONE prospective independent published-source oracle-free invariant transfer.

This is a FIRST prospective read of official SyGuS 2018/2019 competition
Inv_Track sources, NOT new-family learned-model evidence and NOT a model
comparison. Strictly preregistered in GitHub Issue #257 before code/inspection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from experiments.q3_source_prove import prove_source,replay_exported_queries

EXPECTED_UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
DIRS=("comp/2018/Inv_Track","comp/2019/Inv_Track")
HISTORICAL_SOURCE_SHA256=set(["39b5bfe6b6836e81769d2f3cb17118a531c1196b4b06300487b8e711bfb6f7e7","d85acb615d1c83661f11d24f0eaa1ffa95064fdb35353866a3d2277a0948f649","a77f10f201ae26213b5af1147d1e0f33227aa146856e578cdbe4a7ec976a57ba","38294b6c836c3179130e5a454637e0669255a20d4a03a2086ec1f780e8ef5217","de2050be08d24b8cac8848805a96a1096b7182037b7aa15171214315530f4eca","e86979fe06e9075e6ac4510f86def43f67acaad0eab044264705ade32eb43b7c","3ab799bf66632a1a3a8b104ea78bce1d9d205571a63c5adcc7dc9adb6c91e983","4dd10ec778c3ee88ef6d17a98554e1ac3795a286f92b4d570699cb329271fbd1","1b9aafb712b40cdf17e5d09e8f75c02927785a6f46d84fa4cd26b1f5ace997f5","4d5b2cbeaf6ced53535796bf40d7800da31cd84e99c80a410896f7c28e9d51b5","426061c81169efaa0465521bb6d0e4b672ab83945a36a575b8c4c3d5abd4dc9d","1010e228b0ce7210adb86b8054cc90d3e46acce57ec6a098404d18fb7f49dfe5","111f12c0ec1af065543d806ff6dd8a03c05f276649818a14ca0bde155652d599","d2b70242effee34730a81a79d4b88d119059022dcaa2e57a4b0b015d6b4ae13a","9097e00bf0c5bcc8fc2b8439374af5675cc4ef31500724f5a1b21c3492e8742d","8250e5cf660024a70f8c45dd5c06866a62834202e09c4b2005e4f47d54aaff70","00f2e8159b876f1eda72f1850a0855d3753bfea1d9018e442905f3d267906d5c","09e8cf296a29610e4e86c5a6f3c78658c48c8735c8641d2da0ec59706c1755aa"])
FROZEN_SAMPLES_PER_DIR=6
NON_POST_ROUTES={"OCTAGON_HOUDINI","BRANCH_AFFINE_NULLSPACE"}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def cvc5_check(script):
    try:
        p=subprocess.run(
            ["cvc5","--lang=smt2","--tlimit-per=3000","-"],
            input=script,text=True,capture_output=True,timeout=7,check=False)
        lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
        last=[x for x in lines if x in ("sat","unsat","unknown")]
        verdict=last[-1] if last else "NO_DECISION"
        return {"result":verdict,"returncode":p.returncode,
                "stderr":p.stderr[:300],"stdout_excerpt":p.stdout[:240]}
    except Exception as e:
        return {"result":"EXCEPTION","exception":type(e).__name__+":"+str(e)[:120]}

def run(root):
    root=Path(root).resolve()
    first=[]
    for folder in DIRS:
        d=root/folder
        if not d.is_dir():
            raise RuntimeError("REGISTERED_SOURCE_DIRECTORY_MISSING:"+folder)
        names=sorted(x for x in d.glob("*.sl") if x.is_file() and not x.is_symlink())
        if len(names)<FROZEN_SAMPLES_PER_DIR:
            raise RuntimeError("FROZEN_FIRST_SIX_UNAVAILABLE:"+folder)
        first += names[:FROZEN_SAMPLES_PER_DIR]
    if len(first)!=12:
        raise RuntimeError("FROZEN_SELECTION_NOT_EXACT_12")
    # This first-only selection is made using filename metadata, BEFORE
    # reading any original source body, original proof or solver result.
    selected=[p.relative_to(root).as_posix() for p in first]
    print("FROZEN_METADATA_ONLY_SELECTED_SOURCE_LIST",json.dumps(selected))
    cases=[]
    for p in first:
        rel=p.relative_to(root).as_posix()
        raw=p.read_bytes()
        digest=sha(raw)
        historical_dup=digest in HISTORICAL_SOURCE_SHA256
        r=prove_source(p)
        row={"source_path":rel,"raw_source_sha256":digest,
             "source_bytes":len(raw),
             "duplicate_prior_18_raw_source":historical_dup,
             "status":r["status"],"route":r.get("selected_route"),
             "reason":r.get("reason"),
             "original_source_parser_parity":r.get(
                 "independent_native_custom_parser_xor"),
             "original_three_vc":r.get("original_three_vc"),
             "z3_original_three_vc_replay":replay_exported_queries(r),
             "smt2_crosschecks":{},
             "forged_query_negative_probe":None,
             "certificate_kind":r.get("certificate_scope"),
             "solver_wall_ms":r.get("total_wall_ms"),
        }
        if r["status"]=="ORIGINAL_SOURCE_THREE_VC_CERTIFIED":
            scripts=r["original_bad_condition_smt2"]
            for name in ("initial","consecution","post"):
                entry=scripts[name]
                assert sha(entry["query"].encode())==entry["sha256"]
                row["smt2_crosschecks"][name]=cvc5_check(entry["query"])
            # Must be tested with a CHANGED SMT QUERY AND CHANGED SHA.
            forged="(set-logic QF_LIA)\n(assert true)\n(check-sat)\n"
            row["forged_query_negative_probe"]=cvc5_check(forged)
            row["independent_cvc5_valid"]=(
                all(x["result"]=="unsat" and x.get("returncode")==0
                    for x in row["smt2_crosschecks"].values())
                and row["forged_query_negative_probe"]["result"]=="sat"
                and row["z3_original_three_vc_replay"]
            )
        else:
            row["independent_cvc5_valid"]=False
        cases.append(row)
        print("ORIGINAL_EXTERNAL_SOURCE_RESULT",rel,row["status"],row["route"],
              "cvc5",row["independent_cvc5_valid"])
    unique=len({c["raw_source_sha256"] for c in cases})==12
    new=sum(not c["duplicate_prior_18_raw_source"] for c in cases)
    vcs=[c for c in cases if c["status"]=="ORIGINAL_SOURCE_THREE_VC_CERTIFIED"]
    non_post=[c for c in vcs if c["route"] in NON_POST_ROUTES]
    good_cross=sum(bool(c["independent_cvc5_valid"]) for c in vcs)
    statuses=dict(Counter(x["status"] for x in cases))
    gate=(unique and new==12 and len(vcs)>=3 and len(non_post)>=1
          and good_cross==len(vcs))
    return {"schema":"neumann.q3.external-official-sygus-first.v1",
        "preregistered_issue":257,"status":"FIRST_OUTCOME_RECORDED",
        "scientific_transfer_gate_pass":gate,
        "external_repo":"SyGuS-Org/benchmarks",
        "external_git_commit":EXPECTED_UPSTREAM,
        "original_source_dirs":DIRS,
        "selection":"FIRST_SIX_LEXICOGRAPHIC_SL_PER_YEAR_NO_SUBSTITUTION",
        "selected":selected,"cases":cases,"counts":statuses,
        "all_12_sources_distinct_raw_sha":unique,
        "new_raw_sha_vs_prior_18":new,
        "total_sources":12,"explicit_original_3vc":len(vcs),
        "non_post_structural_3vc":len(non_post),
        "cvc5_crosschecked_3vc":good_cross,
        "original_proof_backend":"Z3_AND_INDEPENDENT_CVC5_IF_SUPPORTED",
        "prior_18_raw_source_sha_reference_count":len(HISTORICAL_SOURCE_SHA256),
        "independent_original_origin_proved":False,
        "published_sources_may_be_related_or_duplicated":True,
        "learned_new_operators":False,
        "model_calls":0,"GPU_calls":0,"frontier_calls":0,
        "global_Q1_Q7":"OPEN","global_Q6":"OPEN"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    v=run(args.source_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
    print("FIRST_OFFICIAL_SOURCE_SCIENTIFIC_GATE",v["scientific_transfer_gate_pass"])
    print("FIRST_OFFICIAL_SOURCE_SUMMARY",
          json.dumps({k:v[k] for k in (
              "counts","explicit_original_3vc","non_post_structural_3vc",
              "cvc5_crosschecked_3vc","new_raw_sha_vs_prior_18")},sort_keys=True))
    print("GLOBAL_Q1_Q7",v["global_Q1_Q7"])
if __name__=="__main__":
    main()
