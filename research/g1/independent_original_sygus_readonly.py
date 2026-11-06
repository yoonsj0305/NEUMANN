"""G1 independent read-only audit of already frozen external source FIRST.

Never imports the student network, original first source scorer, its parser,
or its programs. Reimplements atom semantics and original-constraint parser.
Re-downloads the exact same eight published originals, independently checks
accepted executable ASTs and gold, and rejects favorable forged metrics.
This is SOURCE correctness/provenance, not learned-advantage certification.
"""
from __future__ import annotations

import hashlib,json,re,sys
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
FIRST_SHA="6d9940cefc43d9b8ccb93b375bcaf4ba02690481ca432637e54de28a09bfe8cc"
TRAINED_SHA="ae5e291d525098b05ade6eaaf5be76c5fc432fb20a39306be8b782377e4c1641"
ATOM_NAMES=(
 "INPUT","FIRST_WORD","LAST_WORD","HEAD1","HEAD2","TAIL1","TAIL2",
 "BEFORE_DIGIT","DIGIT_SUFFIX","LOWER","UPPER","SPACE","DOT","DASH","EMPTY"
)


def sha(x:bytes)->str:
 return hashlib.sha256(x).hexdigest()


def blob(x:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\\0"+x).hexdigest()


def atom(i:int,src:str)->str:
 name=ATOM_NAMES[i]
 if name=="INPUT":return src
 if name=="FIRST_WORD":return src[:src.find(" ")] if " " in src else src
 if name=="LAST_WORD":return src.rsplit(" ",1)[-1]
 if name=="HEAD1":return src[0:1]
 if name=="HEAD2":return src[0:2]
 if name=="TAIL1":return src[len(src)-1:] if src else ""
 if name=="TAIL2":return src[len(src)-2:] if src else ""
 if name=="BEFORE_DIGIT":
  for j,ch in enumerate(src):
   if ch in "0123456789":return src[:j]
  return src
 if name=="DIGIT_SUFFIX":
  k=len(src)
  while k>0 and src[k-1] in "0123456789":k-=1
  return src[k:]
 if name=="LOWER":return src.lower()
 if name=="UPPER":return src.upper()
 if name=="SPACE":return " "
 if name=="DOT":return "."
 if name=="DASH":return "-"
 if name=="EMPTY":return ""
 raise ValueError("UNKNOWN_ATOM")


def direct_ast(p:list[int],src:str)->str:
 if len(p)!=2 or not all(type(x) is int and 0<=x<15 for x in p):
  raise ValueError("INVALID_OPERATOR_SEQUENCE")
 return atom(p[0],src)+atom(p[1],src)


def parse_constraints(x:bytes):
 source=x.decode("utf-8").replace("\\r","\\n")
 # Independently validate each simple unary original PBE constraint.
 q=r'"(?:[^"]|"")*"'
 rexp=r"\\(constraint\\s+\\(=\\s+\\(f\\s+("+q+r")\\)\\s+("+q+r")\\s*\\)\\s*\\)"
 matches=re.findall(rexp,source,re.DOTALL)
 n=len(re.findall(r"\\(constraint\\b",source))
 if len(matches)!=n or n<2:
  return None,"UNSUPPORTED_ARITY_OR_SOURCE_CONSTRAINT_PATTERN"
 rows=[]
 for lhs,rhs in matches:
  if "\\" in lhs or "\\" in rhs:
   return None,"UNSUPPORTED_ESCAPE_SOURCE"
  rows.append((lhs[1:-1].replace('""','"'),rhs[1:-1].replace('""','"')))
 if len(rows)!=len(set(rows)):
  return None,"DUPLICATE_SOURCE_INPUT_OUTPUT"
 return rows,None


def audit(first_file:Path)->dict:
 first_raw=first_file.read_bytes()
 first=json.loads(first_raw)
 errors=[]
 if sha(first_raw)!=FIRST_SHA:errors.append("FROZEN_FIRST_JSON_SHA_MISMATCH")
 if first.get("science_status")!="SCOPED_LEARNED_CROSS_AUTHOR_AST_TRANSFER_FAIL":
  errors.append("UNAUTHORIZED_FIRST_SCIENCE_PROMOTION")
 if first.get("stats",{}).get("ownweight_checkpoint_sha256")!=TRAINED_SHA:
  errors.append("FROZEN_ACTUAL_STUDENT_WEIGHT_SHA_CHANGED")
 contract=json.loads((ROOT/"docs/experiments/G1_OWNWEIGHT_STRING_AST_EXTERNAL_FIRST_PREREG_2026_11_06.json").read_text())
 fix=json.loads((ROOT/"docs/experiments/G1_EXTERNAL_SYGUS_FIRST_METADATA_SHA_ERRATUM_2026_11_06.json").read_text())
 corrected=fix["actual_source_error"]["correct_original_github_blob_40_hex"]
 if len(first.get("rows",[]))!=8 or len(contract["external_original"]["tasks"])!=8:
  errors.append("EXTERNAL_ORIGINAL_DENOMINATOR_CHANGED")
 audit_rows=[]
 verified={"learned":0,"classical32":0,"classical225":0}
 wrong={"learned":0,"classical32":0,"classical225":0}
 for index,target in enumerate(contract["external_original"]["tasks"]):
  url=("https://raw.githubusercontent.com/"+contract["external_original"]["repo"]+
       "/"+contract["external_original"]["commit"]+"/"+contract["external_original"]["subdir"]+
       "/"+target["name"])
  with urlopen(Request(url,headers={"User-Agent":"NEUMANN-independent-G1"}),timeout=40) as response:
   data=response.read(50000)
  actual_blob=blob(data)
  expect=corrected if target["name"]=="reverse-name.sl" else target["git_blob"]
  if actual_blob!=expect:errors.append("INDEPENDENT_SOURCE_GIT_BLOB_FAIL_"+target["name"])
  row=first["rows"][index]
  if row["task_file"]!=target["name"] or row["original_git_blob"]!=actual_blob:
   errors.append("FIRST_SOURCE_ROW_CHANGED_"+target["name"])
  samples,unsupported=parse_constraints(data)
  if unsupported:
   if row["status"]!="UNSUPPORTED_ORIGINAL_COUNTED" or row.get("error")!=unsupported:
    errors.append("UNSUPPORTED_SOURCE_NOT_PRESERVED_"+target["name"])
   audit_rows.append({"name":target["name"],"status":"UNSUPPORTED","reason":unsupported})
   continue
  train=samples[:-1]
  heldout=samples[-1]
  if row["status"]!="ORIGINAL_SCORED":
   errors.append("SUPPORTED_SOURCE_NOT_SCORED_"+target["name"]);continue
  auditarm={}
  for name in verified:
   original=row[name]
   fits=original["fitting_ASTs"]
   if not all(all(direct_ast(p,x)==y for x,y in train) for p in fits):
    errors.append("FIRST_FALSE_TRAIN_FIT_"+target["name"]+"_"+name)
   all_preds={direct_ast(p,heldout[0]) for p in fits}
   predicted=next(iter(all_preds)) if len(all_preds)==1 else None
   if original["prediction"]!=predicted or original["submitted"]!=(predicted is not None):
    errors.append("FIRST_FALSE_PREDICTION_"+target["name"]+"_"+name)
   exact=predicted is not None and predicted==heldout[1]
   inaccurate=predicted is not None and predicted!=heldout[1]
   if exact!=original["correct_original_heldout"] or inaccurate!=original["wrong_original_heldout"]:
    errors.append("FIRST_GOLD_MISLABEL_"+target["name"]+"_"+name)
   verified[name]+=int(exact);wrong[name]+=int(inaccurate)
   auditarm[name]={"correct_original":exact,"wrong_original":inaccurate,
                   "source_fit_programs":len(fits)}
  audit_rows.append({"name":target["name"],"status":"SCORED","proof":auditarm})
 stats=first.get("stats",{})
 if any(stats.get(name+"_original_heldout_correct" if name=="learned" else name+"_correct")!=value
        for name,value in verified.items()):
  errors.append("FROZEN_AGGREGATE_CORRECTNESS_DRIFT")
 if wrong["learned"]!=stats.get("learned_original_heldout_wrong"):
  errors.append("FROZEN_LEARNED_WRONG_AGGREGATE_DRIFT")
 if stats.get("learned_additional_verified_over_classical32")!=0:
  errors.append("FALSE_LEARNED_EXCLUSIVE_GAIN_PROMOTION")
 return {
  "schema":"neumann.g1.external-sygus-original-independent-readonly-audit.v1",
  "audit_pass":len(errors)==0,
  "errors":errors,
  "original_source_FIRST_sha256":sha(first_raw),
  "frozen_ownweight_sha256":stats.get("ownweight_checkpoint_sha256"),
  "original_eight_task_denominator":len(audit_rows),
  "independent_source_verified_exact_counts":verified,
  "independent_wrong_counts":wrong,
  "source_cases":audit_rows,
  "student_weights_retrained":False,
  "student_original_first_runner_imported":False,
  "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN"
 }


if __name__=="__main__":
 try:
  result=audit(Path(sys.argv[1]))
  print(json.dumps(result,indent=2,sort_keys=True))
  if not result["audit_pass"]:raise SystemExit(1)
 except Exception as err:
  print("INDEPENDENT_AUDIT_ERROR",repr(err),file=sys.stderr)
  raise
