"""Q3G real source<->invariant joining with contamination & license diagnostics.

Do not distribute 3rd party benchmark bodies or benchmark model labels.
This stage counts and hashes them; no learned forward or proof claim.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,posixpath,re,zipfile
from pathlib import Path
from inventory_real_corpus import workbook_tables,git_blob,LOOPY_WORKBOOK_GIT_BLOB,LOOPY_DATASET_GIT_BLOB

SOURCE_GROUP_EXCLUSIONS=("tip-adt-lia","ringen-adt-benchmarks/isaplanner")

def basename(p):
    return posixpath.basename(p.replace("\\","/")).lower()

def identify(rows, archive):
    files=[n for n in archive.namelist() if not n.endswith("/")]
    index=collections.defaultdict(list)
    for p in files:index[basename(p)].append(p)
    licenses=[n for n in files if re.search(r"(?i)(^|/)(license|copying|notice)(\..*)?$",basename(n))]
    out=[];issues=collections.Counter()
    for row in rows[1:]:
        file_ref=row.get("A","").strip()
        inv=row.get("B","").strip()
        if not file_ref or not inv:
            issues["MISSING_SOURCE_OR_INVARIANT"]+=1;continue
        refs=index.get(basename(file_ref),[])
        if not refs:
            issues["NOT_IN_ARCHIVE"]+=1;continue
        # Refuse ambiguous candidate source identity unless entire tail resolves.
        if len(refs)>1:
            parts=[s.lower() for s in file_ref.split("/")]
            score=lambda p: sum(a==b for a,b in zip(reversed(p.lower().split("/")),reversed(parts)))
            mx=max(map(score,refs));refs=[p for p in refs if score(p)==mx]
        if len(refs)!=1:
            issues["AMBIGUOUS_SOURCE_IDENTITY"]+=1;continue
        matched=refs[0]
        if any(g in matched.lower() or g in file_ref.lower() for g in SOURCE_GROUP_EXCLUSIONS):
            issues["Q3F_HOLDOUT_SOURCE_EXCLUSION"]+=1;continue
        raw=archive.read(matched)
        # Best effort license discovery: this is advisory, not a legal permission decision.
        ancestors=matched.split("/")[:-1]
        license_candidates=[lic for lic in licenses
            if posixpath.dirname(lic) in ("/".join(ancestors[:i])
                for i in range(1,len(ancestors)+1))]
        best_license=max(license_candidates,key=len,default=None)
        path_parts=matched.split("/")
        group="/".join(path_parts[:4]) if len(path_parts)>4 else "/".join(path_parts[:-1])
        out.append({
            "program_path":matched,
            "published_row_source":file_ref,
            "source_group":group,
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "invariant_sha256":hashlib.sha256(inv.encode()).hexdigest(),
            "source_bytes":len(raw),
            "invariant_chars":len(inv),
            "invariant_lines":len(inv.splitlines()),
            "license_path_hint":best_license,
            "license_requires_review":True
        })
    unique=collections.Counter(x["source_sha256"] for x in out)
    return out,{
        "metadata_rows":len(rows)-1,
        "matched_rows":len(out),
        "distinct_original_source_hashes":len(unique),
        "exact_duplicate_rows":sum(n-1 for n in unique.values() if n>1),
        "unmatched_or_excluded":dict(issues),
        "license_hint_count":sum(x["license_path_hint"] is not None for x in out),
        "unique_license_hints":sorted({x["license_path_hint"] for x in out if x["license_path_hint"]})[:100],
        "source_groups":dict(collections.Counter(x["source_group"] for x in out)),
        "invariant_structure":{
            "multiline":sum(x["invariant_lines"]>1 for x in out),
            "max_chars":max([x["invariant_chars"] for x in out],default=0),
            "median_chars":sorted([x["invariant_chars"] for x in out])[len(out)//2] if out else 0
        },
        "first_5_source_paths":[x["program_path"] for x in out[:5]]
    }

def run(workbook,dataset):
    xl=workbook.read_bytes();raw=dataset.read_bytes()
    if git_blob(xl)!=LOOPY_WORKBOOK_GIT_BLOB or git_blob(raw)!=LOOPY_DATASET_GIT_BLOB:
        raise ValueError("MISMATCH_PINNED_DATASET_IDENTITY")
    tables=workbook_tables(xl)
    if "Sheet1" not in tables:raise ValueError("MISSING_PUBLISHED_LABEL_SHEET")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        joined,metrics=identify(tables["Sheet1"],archive)
    return {
      "study":"Q3G_AUTHENTIC_SOURCE_LABEL_LINK",
      "status":"SOURCE_INVARIANT_IDENTITY_LINKED_NOT_TRAINED" if metrics["matched_rows"]>0 else "BLOCKED_NO_MATCHES",
      "loopy_workbook_git_blob":LOOPY_WORKBOOK_GIT_BLOB,
      "loopy_dataset_git_blob":LOOPY_DATASET_GIT_BLOB,
      "external_repo":"microsoft/loop-invariant-gen-experiments",
      "external_commit":"91fe89245a0894ec8ad3741d85ae91ce3b552b2e",
      "metrics":metrics,
      "per_pair_identity_only":joined,
      "licensed_training_admitted":False,
      "source_invariant_independently_reproven":False,
      "q3f_competition_targets_read":False,
      "model_trained":False,
      "global_q1_q7":"OPEN"}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--workbook",type=Path,required=True)
    ap.add_argument("--dataset",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    result=run(args.workbook,args.dataset)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print("MATCHED_SOURCE_INVARIANTS",result["metrics"]["matched_rows"],
          "UNMATCHED",result["metrics"]["unmatched_or_excluded"])
    print("SOURCE_GROUPS",result["metrics"]["source_groups"])
    print("LICENSE_HINTS",result["metrics"]["license_hint_count"])
    if result["status"]!="SOURCE_INVARIANT_IDENTITY_LINKED_NOT_TRAINED":raise SystemExit(2)
