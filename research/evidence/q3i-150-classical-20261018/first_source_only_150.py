"""Q3I first full 150-source LOOPY classical original C invariant discovery.

Input to proposer: original C source+original safety goal ONLY.
The workbook is used ONLY by the external identity selector for consistency
with the previous 150-license Q3H sample; its invariant text is NOT forwarded,
parsed, stored, or examined by the proposer or verifier.

This is a developer-corpus classical baseline, not learned Q3.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import io
import json
import sys
import time
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3h-real-source-proof-20261018"))
sys.path.insert(0,str(HERE.parent/"q3g-real-corpus-20261018"))
from source_only_houdini import candidate_proof
from link_real_invariants import run as pair_index
from license_body_audit import class_license
from inventory_real_corpus import git_blob, LOOPY_WORKBOOK_GIT_BLOB,LOOPY_DATASET_GIT_BLOB

PERMISSIVE={"BSD_3_CLAUSE","APACHE_2_0","MIT"}
EXPECTED_COUNT=150
PREVIOUSLY_OPENED_GROUPS={
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP",
 "dataset/loop_invariants/sv-benchmarks/loop-lit"
}
FIRST_THREE={
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP/TRACER-testabs7_VeriMAP_true.c",
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/invgen/simple.c",
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/sharma_splitter/popl.c",
}

def run(workbook:Path,dataset:Path):
    wb=workbook.read_bytes()
    ds=dataset.read_bytes()
    if git_blob(wb)!=LOOPY_WORKBOOK_GIT_BLOB or git_blob(ds)!=LOOPY_DATASET_GIT_BLOB:
        raise ValueError("PUBLIC_DATA_IDENTITY_CHANGED")
    # Q3H eligibility's prior 150 path+hash identity, NOT answers.
    # The published invariant workbook can be loaded by this identity-only
    # index, but NO formula/string/score is ever passed to candidate_proof.
    identity=pair_index(workbook,dataset)["per_pair_identity_only"]
    results=[]
    begun=time.perf_counter_ns()
    with zipfile.ZipFile(io.BytesIO(ds)) as z:
        license_types={
            path:class_license(z.read(path)) for path in
            {item["license_path_hint"] for item in identity if item["license_path_hint"]}
        }
        admitted=[
            item for item in identity
            if license_types.get(item["license_path_hint"],"NO_LICENSE") in PERMISSIVE
        ]
        if len(admitted)!=EXPECTED_COUNT:
            raise ValueError("SOURCE_SET_DID_NOT_MATCH_FIRST_150")
        if len({i["source_sha256"] for i in admitted})!=EXPECTED_COUNT:
            raise ValueError("NONINDEPENDENT_EXACT_DUPLICATES")
        for item in admitted:
            actual=z.read(item["program_path"])
            sh=hashlib.sha256(actual).hexdigest()
            if sh!=item["source_sha256"]:raise ValueError("ORIGINAL_SOURCE_MUTATED")
            tick=time.perf_counter_ns()
            try:
                proof=candidate_proof(actual.decode("utf-8",errors="strict"))
            except Exception as exc:
                proof={"status":"ABSTAIN_UNSUPPORTED_OR_ERROR",
                       "reason":f"{type(exc).__name__}: {str(exc)[:140]}"}
            if proof["status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED":
                obligations=proof["full_original_check"]
                if not all(obligations[x]=="unsat" for x in
                  ("initial","inductive","postcondition","signed_overflow")):
                    raise ValueError("FALSE_POSITIVE_MISSING_ORIGINAL_PROOF")
                if obligations["deliberately_false_goal"]!="sat" or obligations["empty_invariant_goal"]!="sat":
                    raise ValueError("FALSE_POSITIVE_MISSING_NEGATIVE_CONTROL")
            results.append({
              "source_path":item["program_path"],
              "source_sha256":sh,
              "group":item["source_group"],
              "license":license_types[item["license_path_hint"]],
              "proof":proof,
              "per_case_wall_ms":round((time.perf_counter_ns()-tick)/1e6,3),
              "is_q3g_neural_heldout_group":item["source_group"] in PREVIOUSLY_OPENED_GROUPS
            })
    counts=collections.Counter(x["proof"]["status"] for x in results)
    bygroup={}
    for group in sorted({x["group"] for x in results}):
        members=[x for x in results if x["group"]==group]
        bygroup[group]={
            "seen":len(members),
            "classically_proven":sum(x["proof"]["status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED" for x in members),
            "status_counts":dict(collections.Counter(x["proof"]["status"] for x in members)),
            "time_sum_ms":round(sum(x["per_case_wall_ms"] for x in members),3)}
    proven=[x for x in results if x["proof"]["status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED"]
    checksums={x["source_path"]:x["proof"]["status"] for x in results}
    if not FIRST_THREE.issubset(checksums):raise ValueError("THREE_PREVIOUSLY_FIXED_SOURCE_FILES_MISSING")
    if not all(checksums[x]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED" for x in FIRST_THREE):
        raise ValueError("THREE_PREVIOUS_POSITIVE_CLASSICAL_PROOFS_REGRESSED")
    held=[x for x in results if x["is_q3g_neural_heldout_group"]]
    return {
       "status":"SOURCE_ONLY_LICENSED_DEVELOPMENT_CORPUS_CLASSICAL_AUDIT_COMPLETE",
       "date":"2026-10-18",
       "frozen_algorithm":"Q3H2_CLASSICAL_HOUDINI_SOURCE_ONLY",
       "original_corpus_commit":"91fe89245a0894ec8ad3741d85ae91ce3b552b2e",
       "source_programs_seen":len(results),
       "exact_original_source_hashes_distinct":len({x["source_sha256"] for x in results}),
       "source_groups":len(bygroup),
       "full_original_certificates":len(proven),
       "certificates_from_groups":len({x["group"] for x in proven}),
       "outcomes":dict(counts),
       "by_group":bygroup,
       "q3g_group_holdout_population":len(held),
       "q3g_group_holdout_classical_proofs":sum(x["proof"]["status"]=="SOURCE_ONLY_AUTO_INVARIANT_CERTIFIED" for x in held),
       "aggregate_wall_ms":round((time.perf_counter_ns()-begun)/1e6,3),
       "classical_candidate_solver_calls_sum":sum(
           x["proof"].get("total_induction_solver_queries",0) for x in results),
       "source_selection_workbook_used_FOR_METADATA_ONLY":True,
       "invariant_strings_passed_to_solver":False,
       "published_invariant_strings_used_for_generation":False,
       "model_training_or_inference_calls":0,
       "q3f_original_bodies_read":False,
       "source_originals_modified":False,
       "q3_q4_q7":"OPEN","all_q1_q7":"OPEN",
       "first_originals":results,
       "scientific_boundary":"Published labels not used by model; same previously opened Loopy corpus; Houdini grammar and original-C parser only cover a restricted C subset; no neural generalization, Q3, Q4 speedup, or Q7 demonstrated."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",required=True,type=Path)
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    o=p.parse_args();result=run(o.workbook,o.dataset)
    o.output.parent.mkdir(parents=True,exist_ok=True)
    o.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3I_CLASSICAL_SOURCE_ONLY",result["source_programs_seen"],
          "CERTIFIED",result["full_original_certificates"],"GROUPS",result["certificates_from_groups"])
    print("Q3I_Q3G_HELDOUT_SOURCE_GROUPS",result["q3g_group_holdout_population"],
          "CERTIFIED",result["q3g_group_holdout_classical_proofs"])
    print("Q3I_FAILURES",result["outcomes"],"ALL_GLOBAL",result["all_q1_q7"])
