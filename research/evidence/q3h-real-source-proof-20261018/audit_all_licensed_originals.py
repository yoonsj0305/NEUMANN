"""Q3H second non-blind real-source proof coverage audit.

Audit every permissively-licensed program/invariant pair from pinned Loopy.
Strict no-guesses compiler; unsupported and undecidable results are not proofs.
No neural training, no heldout Q3F problem access, no third-party source export.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3g-real-corpus-20261018"))
from inventory_real_corpus import workbook_tables
from license_body_audit import class_license
from link_real_invariants import run as pair_index
from replay_real_c_loop_invariants import verify

PERMISSIVE={"APACHE_2_0","BSD_3_CLAUSE","MIT"}
SOURCE_REV="91fe89245a0894ec8ad3741d85ae91ce3b552b2e"
PREVIOUS_DEVELOPMENT_PROVEN={
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP/TRACER-testabs7_VeriMAP_true.c",
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/invgen/simple.c",
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/sharma_splitter/popl.c",
}

def audit(workbook,archive):
    corpus=pair_index(workbook,archive)["per_pair_identity_only"]
    labels=workbook_tables(workbook.read_bytes())["Sheet1"]
    lookup=collections.defaultdict(list)
    for r in labels[1:]:
        lookup[r.get("A","").strip()].append(r.get("B","").strip())
    records=[]
    with zipfile.ZipFile(io.BytesIO(archive.read_bytes())) as z:
        lic_types={
            name:class_license(z.read(name)) for name in
            {r["license_path_hint"] for r in corpus if r["license_path_hint"]}
        }
        for r in corpus:
            typ=lic_types.get(r["license_path_hint"],"NO_ANCESTOR_LICENSE")
            if typ not in PERMISSIVE:continue
            originals=lookup.get(r["published_row_source"],[])
            if len(originals)!=1 or not originals[0]:
                status="ABSTAIN_NO_UNIQUE_PUBLISHED_INVARIANT"
                result={"status":status}
            else:
                raw=z.read(r["program_path"])
                if hashlib.sha256(raw).hexdigest()!=r["source_sha256"]:
                    raise ValueError("RAW_ORIGINAL_SOURCE_IDENTITY_INVALID")
                if hashlib.sha256(originals[0].encode()).hexdigest()!=r["invariant_sha256"]:
                    raise ValueError("PUBLISHED_INVARIANT_IDENTITY_INVALID")
                try:
                    result=verify(raw.decode("utf-8",errors="strict"),originals[0])
                    status=result["status"]
                except Exception as exc:
                    result={"status":"ABSTAIN_UNSUPPORTED_OR_ERROR",
                            "reason":f"{type(exc).__name__}: {str(exc)[:110]}"}
                    status=result["status"]
            records.append({
                "source_path":r["program_path"],
                "source_sha256":r["source_sha256"],
                "published_invariant_sha256":r["invariant_sha256"],
                "source_group":r["source_group"],
                "license":typ,
                "supported_original_C_proof":status=="ALL_ORIGINAL_LOOP_OBLIGATIONS_UNSAT",
                "proof":result
            })
    cats=collections.Counter(r["proof"]["status"] for r in records)
    groups=collections.defaultdict(lambda:collections.Counter())
    for r in records:
        groups[r["source_group"]][r["proof"]["status"]]+=1
    proven=[r for r in records if r["supported_original_C_proof"]]
    # Require the fixed three *previously* independently certified cases still prove.
    path_status={r["source_path"]:r["supported_original_C_proof"] for r in records}
    if not all(path_status.get(k,False) for k in PREVIOUS_DEVELOPMENT_PROVEN):
        raise ValueError("KNOWN_THREE_GENUINE_ORIGINAL_PROOFS_REGRESSED")
    return {
        "scope":"postopened authentic Loopy source/invariant proof eligibility within supported single-loop C",
        "status":"COMPLETE_BOUNDARY_AUDIT_NO_Q3_PROMOTION",
        "source_repository":"microsoft/loop-invariant-gen-experiments",
        "source_commit":SOURCE_REV,
        "source_groups_audited":len(groups),
        "permissive_programs_checked":len(records),
        "actual_original_full_proofs":len(proven),
        "proofs_from_distinct_source_groups":len({r["source_group"] for r in proven}),
        "unsupported_or_failed_proof_counts":dict(cats),
        "group_verdict_counts":{k:dict(v) for k,v in sorted(groups.items())},
        "third_party_C_and_invariant_text_retained":False,
        "q3f_sealed_benchmarks_read":False,
        "actual_learned_model_proof_calls":0,
        "original_proof_status":"ONLY_PROOF_PASS_IF_INDUCTION_EXIT_OVERFLOW_AND_NEGATIVES",
        "global_q1_q7":"OPEN",
        "records":records
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",required=True,type=Path)
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    r=audit(a.workbook,a.dataset)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+"\n")
    print("Q3H_ALL_LICENSED_PROOF_COVERAGE",r["permissive_programs_checked"],
          "PROVEN",r["actual_original_full_proofs"],
          "SOURCE_GROUPS",r["proofs_from_distinct_source_groups"])
    print("NONPROOFS",r["unsupported_or_failed_proof_counts"])
    print("GLOBAL",r["global_q1_q7"])
