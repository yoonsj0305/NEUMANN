"""CHC-COMP 2025+2026 unresolved metadata audit + SHA-only source escrow.

No target SMT text, AST, claim label or answer is emitted, parsed, or shared
with any model. This program does not invoke a solver or claim a theorem.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

REVISIONS={
    "2025":("chc-comp25-benchmarks","ddd279cab0717db6effe69baad451a8eb04ffd86"),
    "2026":("chc-comp26-benchmarks","b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"),
}
PREREG="ea2c5290ff8649cbbd86cf96a887ceca595dafa4"
SELECTED=(
  ("tip-adt-lia","tip-adt-lia/tip2015_sort_StoogeSortIsSort_000.yml"),
  ("ringen-adt-benchmarks/isaplanner","ringen-adt-benchmarks/isaplanner/prop_63_000.yml"),
)
MAX_SOURCE_BYTES=10_000_000

def fetch(repo,rev,path):
    if not re.fullmatch(r"[0-9a-f]{40}",rev):raise ValueError("UNPINNED_REVISION")
    if ".." in path or path.startswith("/") or not re.fullmatch(r"[a-zA-Z0-9_./-]+",path):
        raise ValueError("INVALID_UNPINNED_PATH")
    url=f"https://raw.githubusercontent.com/chc-comp/{repo}/{rev}/{path}"
    with urlopen(url,timeout=35) as stream:
        data=stream.read(MAX_SOURCE_BYTES+1)
    if not data or len(data)>MAX_SOURCE_BYTES:raise ValueError("MISSING_OR_OVERSIZED_SOURCE")
    return data

def digest(raw):
    blob=b"blob "+str(len(raw)).encode()+bytes([0])+raw
    return {"sha256":hashlib.sha256(raw).hexdigest(),
            "git_blob_sha1":hashlib.sha1(blob).hexdigest(),
            "bytes":len(raw)}

def parse_metadata(raw,year):
    text=raw.decode("utf-8",errors="strict")
    files=re.findall(r"(?m)^input_files:\s*([a-zA-Z0-9_.-]+\.smt2)\s*$",text)
    if len(files)!=1:raise ValueError(f"{year}_EXACT_ONE_INPUT_REQUIRED")
    if "majority_vote_verdict:" in text:
        raise ValueError(f"{year}_HAS_REPORTED_SOLVER_VERDICT")
    if re.search(r"(?m)^\s*(sat|unsat|inconsistent)\s*:",text):
        raise ValueError(f"{year}_HAS_REPORTED_SOLVER_OUTPUT")
    verdict=re.findall(r"(?m)^\s*expected_verdict:\s*(\w+)\s*$",text)
    if year=="2025":
        if verdict:raise ValueError("2025_NOT_COMPETITION_UNRESOLVED")
    else:
        if verdict!=["true"] or "placeholder verdict (auto-added)" not in text:
            raise ValueError("2026_EXPECTED_PLACEHOLDER_NOT_CONFIRMED")
    if re.search(r"(?m)^-\s*property_file:",text) is None:
        raise ValueError("MISSING_CHECKSAT_METADATA")
    return files[0]

def run():
    receipt={
        "experiment":"NEUMANN_Q3F_METADATA_ONLY_COMPETITION_HEADROOM_CANDIDATE_ESCROW",
        "selection_preregistered_commit":PREREG,
        "source_body_inspection":False,
        "source_text_persisted_or_printed":False,
        "solver_invocations":0,"learned_model_calls":0,
        "frontier_model_calls":0,
        "global_q1_q7":"OPEN",
        "status":"INCOMPLETE",
        "records":[],
        "scope":"Official competition metadata only: no 2025 verdict, 2026 placeholder true with no majority vote. This does NOT prove current unsolvability, model gap, ground truth or novel Q3."
    }
    for group,path in SELECTED:
        try:
            # Metadata-only access to 2025 and 2026, separately hash each.
            rows={}
            filenames=[]
            for year,(repo,rev) in REVISIONS.items():
                meta=fetch(repo,rev,path)
                fname=parse_metadata(meta,year)
                filenames.append(fname)
                rows[year]={
                    "repository":"chc-comp/"+repo,
                    "revision":rev,
                    "metadata_path":path,
                    "metadata_identity":digest(meta),
                    "documented_competition_outcome":"NO_TOOL_VERDICT_RECORDED"
                }
            if filenames[0]!=filenames[1]:
                raise ValueError("CROSS_YEAR_BENCHMARK_FILENAME_CHANGED")
            # No SMT syntax analysis or content emission. ONLY content hashes.
            repo,rev=REVISIONS["2026"]
            source_path=path.rsplit("/",1)[0]+"/"+filenames[0]
            raw=fetch(repo,rev,source_path)
            source_hash=digest(raw)
            del raw
            record={
                "status":"HOLDOUT_IDENTITY_ESCROWED",
                "family_group":group,
                "metadata":rows,
                "source_repo":"chc-comp/"+repo,
                "source_revision":rev,
                "source_path":source_path,
                "raw_source_byte_identity_ONLY":source_hash,
                "training_exclusion":True,
                "source_text_exposed_to_model":False
            }
        except Exception as exc:
            record={
                "status":"BLOCKED_QUESTIONS_OPEN",
                "family_group":group,
                "metadata_path":path,
                "exception":f"{type(exc).__name__}: {str(exc)[:220]}"
            }
        receipt["records"].append(record)
    if all(r["status"]=="HOLDOUT_IDENTITY_ESCROWED" for r in receipt["records"]):
        if len({r["family_group"] for r in receipt["records"]})!=len(SELECTED):
            raise ValueError("SOURCE_GROUP_COLLISION")
        receipt["status"]="TWO_COMPETITION_HEADROOM_CANDIDATES_SEALED_NOT_EVALUATED"
    else:receipt["status"]="BLOCKED_METADATA_OR_SOURCE"
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    receipt=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(receipt,indent=2)+"\n")
    print("SCIENCE_STATUS",receipt["status"])
    print("SOURCE_GROUP_COUNT",len(receipt["records"]))
    print("PER_GROUP",[(r["family_group"],r["status"],
          r.get("raw_source_byte_identity_ONLY",{}).get("sha256"))
          for r in receipt["records"]])
    print("Q1_Q7",receipt["global_q1_q7"])
    if receipt["status"]!="TWO_COMPETITION_HEADROOM_CANDIDATES_SEALED_NOT_EVALUATED":
        raise SystemExit(2)

if __name__=="__main__":
    main()
