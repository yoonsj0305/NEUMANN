"""G3 full 24 immutable FIRST independent competition-metadata/track audit.

No original first scorer, no native solver, no learned proposer imports.
After first 24 source bodies were already opened, re-download pinned official
CHC-COMP 2025 original Git blobs, official per-file YAML verdict metadata
and actual .set membership. Compare to original byte-pinned Z3/cvc5 receipts.
Official README: missing expected_verdict = nobody solved in 2025.
NOT proof of universal unprovability; tournament labels not a proof object.
"""
from __future__ import annotations
import hashlib,json,re,sys
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json"
ERRATUM=ROOT/"docs/experiments/G3_SOURCEFREE_PREOPEN_ONE_GIT_BLOB_ERRATUM_2026_11_06.json"
FIRST_SHA={
 "LIA_MULTIPHASE":"c4529472973dc7e102e3b755ff866ccac5f285a9d7206488d65dd054f5b41535",
 "ARRAY_CHC":"47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8",
 "ADT_CHC":"84e35263eb08153776ccb1fb6ae97a1a76b82b8ca8959fd8b6502987474c6376",
}
OFFICIAL_TRACK={
 "LIA_MULTIPHASE":"LIA-Lin.set",
 "ARRAY_CHC":"LIA-Lin-Arrays.set",
 "ADT_CHC":"ADT-LIA.set",
}
def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def gitblob(x:bytes)->str:return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def read_original(repo:str,rev:str,path:str)->bytes:
  url="https://raw.githubusercontent.com/"+repo+"/"+rev+"/"+path
  with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G3-official-first-readonly-audit"}),timeout=50) as r:
    return r.read(200000)

def label_from_yml(raw:bytes,original:str)->str:
  text=raw.decode("utf8")
  if "format_version:" not in text or "property_file:" not in text:
    raise ValueError("UNSUPPORTED_OR_MISSING_PUBLISHED_YAML_SOURCE")
  specified=re.findall(r"^\s*expected_verdict:\s*(\S+)\s*$",text,re.MULTILINE)
  listed=re.findall(r"^\s*input_files:\s*(\S+)\s*$",text,re.MULTILINE)
  if listed!=[original]:raise ValueError("OFFICIAL_METADATA_TASK_NAME_NOT_MATCHING_SOURCE")
  if len(specified)>1:raise ValueError("DUPLICATE_ORIGINAL_EXPECTED_VERDICT")
  x=specified[0].lower() if specified else "ABSENT_NO_SOLVER_SUCCESS_REPORTED_IN_2025"
  if x not in ("true","false","inconsistent","ABSENT_NO_SOLVER_SUCCESS_REPORTED_IN_2025".lower()):
     raise ValueError("UNKNOWN_PUBLISHED_EXPECTED_VERDICT")
  return x

def official_yml_name(cohort:str,name:str)->str:
  base=name[:-len(".smt2")]
  return base+("_000.yml" if cohort=="LIA_MULTIPHASE" else ".yml")

def run(paths:dict[str,Path])->dict:
  contract=json.loads(MANIFEST.read_text())
  err=json.loads(ERRATUM.read_text())["exact_single_metadata_transcription_error"]
  original_repo=contract["upstream"]["repo"];commit=contract["upstream"]["commit"]
  cases=[];errors=[];cohort_counts={}
  for cohort in contract["cohorts"]:
    cname=cohort["id"];p=paths[cname]
    original_data=p.read_bytes()
    if sha(original_data)!=FIRST_SHA[cname]:
      errors.append("IMMUTABLE_FIRST_SHA256_CHANGED_"+cname)
    data=json.loads(original_data)
    if data.get("cohort")!=cname or len(data.get("rows",[]))!=8:
      errors.append("FIRST_DENOMINATOR_CHANGED_"+cname);continue
    original_target=cohort["targets"]
    member=read_original(original_repo,commit,OFFICIAL_TRACK[cname]).decode("utf8").splitlines()
    nlabel={"true":0,"false":0,"inconsistent":0,"ABSENT_NO_SOLVER_SUCCESS_REPORTED_IN_2025":0}
    nmatch=0;nmissing=0
    for idx,target in enumerate(original_target):
      row=data["rows"][idx]
      if row["file"]!=target["file"] or row["cohort"]!=cname:
        errors.append("ORIGINAL_TASK_ORDER_CHANGED_"+cname+"_"+target["file"]);continue
      path=cohort["folder"]+"/"+target["file"]
      got=read_original(original_repo,commit,path)
      expected=target["git_blob"]
      if path==err["folder"]+"/"+err["file"]:
        if expected!=err["original_38hex"]:
          errors.append("ORIGINAL_METADATA_ERRATUM_MISMATCH_"+target["file"])
        expected=err["publisher_verified_40hex"]
      if gitblob(got)!=expected or row.get("git_blob")!=expected:
        errors.append("IMMUTABLE_ORIGINAL_SOURCE_GIT_BLOB_CHANGED_"+target["file"])
      if row.get("original_source_sha256")!=sha(got):
        errors.append("FIRST_ORIGINAL_BODY_SHA256_CHANGED_"+target["file"])
      yml=official_yml_name(cname,target["file"])
      relative=cohort["folder"]+"/"+yml
      metadata=read_original(original_repo,commit,relative)
      if relative not in member:
        errors.append("NOT_REGISTERED_2025_COMPETITION_TASK_"+relative)
      label=label_from_yml(metadata,target["file"])
      nlabel[label]+=1
      records={x["engine"]:x for x in row.get("native",[])}
      if set(records)!={"Z3","CVC5"}:
        errors.append("MISSING_ORIGINAL_TWO_ENGINE_EVIDENCE_"+target["file"])
      z=records.get("Z3",{}).get("status")
      known={"true":"SAT_CLAIM_UNVERIFIED","false":"UNSAT_CLAIM_UNVERIFIED"}
      match=(z==known[label]) if label in known else None
      if match is False:
        errors.append("FIRST_Z3_OUTCOME_CONTRADICTS_OFFICIAL_METADATA_"+target["file"])
      if match is True:nmatch+=1
      if label=="ABSENT_NO_SOLVER_SUCCESS_REPORTED_IN_2025":nmissing+=1
      cases.append({"cohort":cname,"original":target["file"],
        "published_task_original_blob":expected,
        "official_2025_track":OFFICIAL_TRACK[cname],
        "original_in_2025_competition_task_set":relative in member,
        "official_verdict_metadata_git_blob":gitblob(metadata),
        "official_2025_expected_verdict":label,
        "frozen_original_first_Z3":z,
        "frozen_original_first_CVC5":records.get("CVC5",{}).get("status"),
        "Z3_matches_published_labeled_verdict":match,
        "original_native_Z3_wall_ms":records.get("Z3",{}).get("wall_ms"),
        "unknown_not_proof_of_unsolvability":True})
    cohort_counts[cname]={"original_count":8,"label_count":nlabel,
      "matched_labeled_native_z3":nmatch,
      "official_no_2025_solver_succeeded_label_count":nmissing}
  if len(cases)!=24:errors.append("ORIGINAL_24_AUDIT_DENOMINATOR_CHANGED")
  if cohort_counts.get("LIA_MULTIPHASE",{}).get("label_count",{}).get("true")!=8:
    errors.append("LIA_SOURCE_EXPECTED_EIGHT_PUBLISHED_SAT_LABELS")
  if cohort_counts.get("ARRAY_CHC",{}).get("label_count",{}).get("ABSENT_NO_SOLVER_SUCCESS_REPORTED_IN_2025")!=8:
    errors.append("ARRAY_SOURCE_EXPECTED_EIGHT_UNLABELED_RESULTS")
  if cohort_counts.get("ADT_CHC",{}).get("label_count",{}).get("true")!=2:
    errors.append("ADT_SOURCE_EXPECTED_TWO_SAT")
  if cohort_counts.get("ADT_CHC",{}).get("label_count",{}).get("false")!=6:
    errors.append("ADT_SOURCE_EXPECTED_SIX_UNSAT")
  return {
   "schema":"neumann.g3.original24-2025-competition-metadata-independent-audit.v1",
   "audit_pass":len(errors)==0,"errors":errors,
   "original_2025_benchmark_commit":commit,
   "native_first_run_id":42174775254,
   "frozen_original_first_SHA256":FIRST_SHA,
   "official_readme_interpretation":"ABSENT EXPECTED_VERDICT: NO TOOL SOLVED DURING CHC-COMP 2025; this is archived outcome, NOT mathematical impossibility; some competition inconsistencies omitted.",
   "original_native_synthesis_reruns":0,"NEUMANN_learned_model_training_or_inference":0,
   "known_original_count":len(cases),"cohort_counts":cohort_counts,
   "labeled_first_z3_verdict_agreement_count":sum(r["Z3_matches_published_labeled_verdict"] is True for r in cases),
   "labeled_original_count":sum(r["Z3_matches_published_labeled_verdict"] is not None for r in cases),
   "verified_unsolved_by_all_algorithms":False,
   "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
   "cases":cases}
if __name__=="__main__":
  try:
    mapping={"LIA_MULTIPHASE":Path(sys.argv[1]),
             "ARRAY_CHC":Path(sys.argv[2]),
             "ADT_CHC":Path(sys.argv[3])}
    result=run(mapping)
    print(json.dumps(result,sort_keys=True,indent=2))
    if not result["audit_pass"]:raise SystemExit(1)
  except Exception as e:
    print("G3_ORIGINAL_COMPETITION_READONLY_AUDIT_ERROR",type(e).__name__,str(e),file=sys.stderr)
    raise SystemExit(2)
