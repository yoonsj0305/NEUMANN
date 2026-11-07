"""POST-FIRST infrastructure repair: stream every GP-Suite family, no solver change.

The initial external FIRST #42365072610 downloaded only 17/29 full
edge/random file pairs due to a predeclared 20MB raw file size cap.
That is not a solver failure. Here the *same frozen inventor* and
*same original scorer* run on bounded first 50k source random cases,
decompressing gzip incrementally from a pinned previous Git commit.

This is POST-FIRST DEVELOPMENT on the exact same public original corpus,
not a new independent-first Q3 proof. Scientific reports MUST keep the
prior 13-eligible / 2-exact / 0-memory-gain original first unchanged.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import gzip
import hashlib
import json
import urllib.request
import time

from research.q3.gp_suite_connected_router_original_first import (
    evaluate as existing_frozen_evaluator
)

SCHEMA="neumann.q3.gp-suite-streaming-infrastructure-postfirst.v1"
FIRST_ACTIONS=42365072610
MAX_RANDOM_ROWS=50000


def stream_original(url:str,output:Path,rows:int|None):
    output.parent.mkdir(parents=True,exist_ok=True)
    request=urllib.request.Request(url,headers={
        "User-Agent":"NEUMANN-Q3-source-frozen-research"})
    start=time.monotonic()
    count=0
    with urllib.request.urlopen(request,timeout=90) as response:
        if rows is None:
            # Edge originals are normally tiny compressed gzip files.
            # Read entire original compressed bytes, preserve suffix.
            with output.open("wb") as f:
                while True:
                    chunk=response.read(1<<20)
                    if not chunk:break
                    f.write(chunk)
                    if output.stat().st_size>20000000:
                        raise ValueError("ORIGINAL_EDGE_EXCEEDS_20MB")
            with gzip.open(output,"rt",encoding="utf8") as reader:
                count=sum(1 for line in reader if line.strip())
        else:
            # Random original gzip is sometimes >100MB compressed.
            # Decompress ONLY the FIRST N original lines, as BOTH first
            # and post-first algorithms cap reader at 50k original rows.
            with gzip.GzipFile(fileobj=response,mode="rb") as reader:
                with output.open("w",encoding="utf8") as f:
                    for line in reader:
                        if not line.strip():continue
                        f.write(line.decode("utf8"))
                        count+=1
                        if count>=rows:break
    return {"rows_streamed":count,
            "bytes_saved":output.stat().st_size,
            "elapsed_s":round(time.monotonic()-start,4)}


def acquire_first_pinned_inventory(first_artifact:Path,
                                   output_dataset:Path,output:Path):
    if output.exists():raise ValueError("NO_OVERWRITE_POSTFIRST")
    output.mkdir(parents=True)
    prior_inventory=json.loads(
        (first_artifact/"ORIGINAL_FILE_INVENTORY.json").read_text())
    original_manifest=json.loads(
        (first_artifact/"MANIFEST.json").read_text())
    rev=(first_artifact/"GP_SOURCE_GIT_SHA.txt").read_text().strip()
    if len(rev)!=40 or len(original_manifest)!=29:
        raise ValueError("EARLIER_SOURCE_REVISION_OR_DENOMINATOR_INVALID")
    provenance=[]
    for entry in original_manifest:
        row={**entry}
        task=row["task"]
        paths=row.get("paths",{})
        if not paths.get("edge") or not paths.get("random"):
            row["downloaded"]=False
            row["download_reason"]="ORIGINAL_MISSING_FILE_PAIR"
            provenance.append(row);continue
        obtained={};new_paths={}
        try:
            for part in ("edge","random"):
                src=paths[part]
                if not src.startswith(f"datasets/{task}/") or ".." in src:
                    raise ValueError("DISALLOWED_ORIGINAL_SOURCE_PATH")
                url=("https://raw.githubusercontent.com/thelmuth/"
                     "program-synthesis-benchmark-datasets/"+rev+"/"+src)
                dst=(output_dataset/src if part=="edge" else
                     output_dataset/(src+".first50000.jsonl"))
                obtained[part]=stream_original(url,dst,
                    rows=None if part=="edge" else MAX_RANDOM_ROWS)
                new_paths[part]=str(dst.relative_to(output_dataset))
            row.update({
                "downloaded":True,
                "paths":new_paths,
                "download_reason":"POSTFIRST_BOUND_STREAMING_ACQUISITION",
                "postfirst_original_partial_random_stream":True,
                "postfirst_data_acquisition_stats":obtained,
            })
        except (OSError,ValueError,TimeoutError,UnicodeError,
                gzip.BadGzipFile) as error:
            row.update({"downloaded":False,
                        "download_reason":(type(error).__name__+":"+str(error))[:160]})
        provenance.append(row)
        print("GP_ALL_29_STREAMED",task,row["downloaded"],
              row["download_reason"],flush=True)
    (output/"POSTFIRST_MANIFEST.json").write_text(
        json.dumps(provenance,indent=2,sort_keys=True)+"\n")
    source_report={
        "schema":SCHEMA,
        "original_immutable_FIRST_run":FIRST_ACTIONS,
        "original_first_source_git_sha":rev,
        "original_original_family_count":len(original_manifest),
        "original_first_downloaded":sum(x["downloaded"] for x in original_manifest),
        "new_postfirst_downloaded":sum(x["downloaded"] for x in provenance),
        "same_original_sha256_input_selection":True,
        "partial_random_streamed_first_50000_lines_per_family":True,
        "original_FIRST_unmodified":True,
        "post_first_not_new_blind":True,
    }
    (output/"ACQUISITION_DIAGNOSIS.json").write_text(
        json.dumps(source_report,indent=2,sort_keys=True)+"\n")
    return source_report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--first-artifact",required=True,type=Path)
    p.add_argument("--prior-memory",required=True,type=Path)
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    # Source evaluator's original entrypoint is reused byte-for-byte.
    # Do not run() with misordered params; script below invokes the
    # frozen evaluator explicitly after acquisition.
    info=acquire_first_pinned_inventory(
        a.first_artifact,a.dataset,a.out)
    original=a.out/"POSTFIRST_MANIFEST.json"
    scored=a.out/"SCORER_AS_FROZEN"
    x=existing_frozen_evaluator(
        a.dataset,original,a.prior_memory,scored,
        fold_budget=1000,relation_budget=1200)
    old=json.loads((a.first_artifact/"RESULTS/FIRST.json").read_text())
    previous={q["source_task"]:q for q in old["rows"]}
    new={q["source_task"]:q for q in x["rows"]}
    comparisons=[]
    for k,q in previous.items():
        if q["status"]!="EVALUATED":continue
        now=new[k]
        comparisons.append({
            "task":k,
            "previous_first_full_exact_memory":q["warm_heldout"]["exact"],
            "postfirst_full_exact_memory":now.get(
                "warm_heldout",{}).get("exact"),
            "previous_first_full_exact_cold":q["cold_heldout"]["exact"],
            "postfirst_full_exact_cold":now.get(
                "cold_heldout",{}).get("exact"),
            "previous_first_heldout_n":q["source_heldout_total"],
            "postfirst_heldout_n":now.get("source_heldout_total",0),
            "same_original_first_metrics_reproduced":
                (now.get("warm_heldout",{}).get("exact")==
                 q["warm_heldout"]["exact"] and
                 now.get("cold_heldout",{}).get("exact")==
                 q["cold_heldout"]["exact"] and
                 now.get("source_heldout_total")==q["source_heldout_total"]),
        })
    report={
        "schema":SCHEMA,
        "original_first_run":FIRST_ACTIONS,
        "evaluation_postfirst_not_independent_original":True,
        "same_frozen_existing_evaluator_and_inventor":True,
        "unchanged_original_first_receipts":True,
        "acquisition":info,
        "postfirst_extended_coverage":x["summary"],
        "previous_eligible_reproduction":comparisons,
        "reproduced_previous_first_eligible":sum(
            q["same_original_first_metrics_reproduced"] for q in comparisons),
        "previous_first_eligible_count":len(comparisons),
        "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
    }
    (a.out/"POSTFIRST_DIAGNOSIS.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_GP_POSTFIRST_INFRASTRUCTURE_EXTENDED_COVERAGE",
          json.dumps({
              "available":info["new_postfirst_downloaded"],
              "evaluated":x["summary"]["eligible_full_32_holdout_families"],
              "exact":x["summary"]["memory_full_original_exact_families"],
              "memory_gain":x["summary"]["memory_additional_full_exact_families"],
              "previous_reproduced":report["reproduced_previous_first_eligible"],
              "previous_total":len(comparisons),
              "postfirst_not_blind":True,
          },sort_keys=True),flush=True)
