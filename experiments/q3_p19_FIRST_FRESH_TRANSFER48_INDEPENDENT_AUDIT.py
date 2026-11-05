"""NEUMANN P1.9 first-original48 independent Python audit.
No new proposal, inference, model training or search. Replays only existing first
proposed executable certificates with a different interpreter and original
upstream checker. Existing baseline solver internals are not reimplemented.
"""
from __future__ import annotations
import hashlib,itertools,json,sys
from pathlib import Path
FIRST_HASH="fc55628f4cd1627a0f17f52a66ced0cec66830b58ed0658b74c113dae61ebfeb"
ROOT_SHA="399030444e0ab0cc8b4e199870fb20b863846f34"
def blob(p):
 b=Path(p).read_bytes()
 return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def good(g):
 return (type(g)==list and 1<=len(g)<=30 and type(g[0])==list and
  1<=len(g[0])<=30 and all(type(row)==list and len(row)==len(g[0]) and
  all(type(x)==int and 0<=x<=9 for x in row)for row in g))
def transpose(g):return [list(row)for row in zip(*g)]
def rotate(g):return [list(row)for row in zip(*g[::-1])]
def mode(g):
 counts={}
 for row in g:
  for x in row:counts[x]=counts.get(x,0)+1
 ranked=sorted(counts,key=lambda x:(-counts[x],x))
 if len(ranked)>1 and counts[ranked[0]]==counts[ranked[1]]:return None
 return ranked[0] if ranked else None
def crop_non_bg(g):
 bg=mode(g)
 if bg is None:return None
 pts=[(r,c)for r,row in enumerate(g)for c,x in enumerate(row)if x!=bg]
 if not pts:return None
 lo_r,hi_r=min(r for r,c in pts),max(r for r,c in pts)
 lo_c,hi_c=min(c for r,c in pts),max(c for r,c in pts)
 return [row[lo_c:hi_c+1]for row in g[lo_r:hi_r+1]]
def orient(g,o):
 if o=="id":return [r[:]for r in g]
 if o=="flipH":return [r[::-1]for r in g]
 if o=="flipV":return g[::-1]
 if o=="rot90":return rotate(g)
 if o=="rot180":return rotate(rotate(g))
 if o=="rot270":return rotate(rotate(rotate(g)))
 if o=="transpose":return transpose(g)
 if o=="antiTranspose":return rotate(rotate(transpose(g)))
 raise ValueError("UNSUPPORTED_ORIENTATION")
def panels(g,orientation):
 h,w=len(g),len(g[0])
 if orientation=="horizontal":
  if h<3 or h%2!=1:return None
  mid=h//2;row=g[mid]
  if len(set(row))!=1:return None
  return g[:mid],g[mid+1:]
 if orientation=="vertical":
  if w<3 or w%2!=1:return None
  mid=w//2
  if len({row[mid]for row in g})!=1:return None
  return [r[:mid]for r in g],[r[mid+1:]for r in g]
 return None
def pred(a,b,op):
 rules={"bothZero":a==0 and b==0,
 "eitherZero":a==0 or b==0,
 "oneZero":(a==0)!=(b==0),
 "bothNonzero":a!=0 and b!=0,
 "same":a==b,"different":a!=b,
 "sameNonzero":a==b and a!=0,
 "aZero":a==0,"bZero":b==0,
 "aNonzero":a!=0,"bNonzero":b!=0}
 if op not in rules:raise ValueError("INVALID_PREDICATE")
 return rules[op]
def expr(a,b,op):
 if op=="a":return a
 if op=="b":return b
 if op=="min":return min(a,b)
 if op=="max":return max(a,b)
 raise ValueError("INVALID_EXPR")
def execute(g,program):
 if not good(g):return None
 a=program["ast"]
 if a["type"]=="affine":
  t=crop_non_bg(g)if a["crop"]else g
  if t is None:return None
  t=orient(t,a["orientation"])
  bg=0 if a["fill"]=="zero"else mode(g)
  if bg is None:return None
  h,w=len(t),len(t[0])
  raw=[[t[r-a["dy"]][c-a["dx"]]if 0<=r-a["dy"]<h and 0<=c-a["dx"]<w
         else bg for c in range(w)]for r in range(h)]
 elif a["type"]=="split":
  pair=panels(g,a["orientation"])
  if pair is None:return None
  a1,a2=pair
  raw=[[int(pred(a1[r][c],a2[r][c],a["op"]))if a["mode"]=="predicate"
         else expr(a1[r][c],a2[r][c],a["op"])
         for c in range(len(a1[r]))]for r in range(len(a1))]
 else:return None
 palette=dict(program["palette"])
 if not good(raw)or any(x not in palette for row in raw for x in row):return None
 out=[[palette[x]for x in row]for row in raw]
 return out if good(out)else None
def verify(root,arc,first_file):
 root,arc=Path(root),Path(arc)
 raw=Path(first_file).read_bytes()
 report=json.loads(raw)
 cohort_path=root/"docs/experiments/q3_p19_FIRST_FRESH_TRANSFER48_COHORT_FROZEN.json"
 lock=json.loads((root/"docs/experiments/q3_p19_FIRST_FRESH_TRANSFER48_SOURCE_LOCK.json").read_text())
 cohort=json.loads(cohort_path.read_text())
 errors=[]
 def check(cond,why):
  if not cond:errors.append(why)
 check(hashlib.sha256(raw).hexdigest()==FIRST_HASH,"IMMUTABLE_FIRST_RAW_HASH_CHANGED")
 check(blob(cohort_path)==lock["cohort_blob"],"SOURCE_COHORT_DRIFT")
 for name,sha in lock["source_blobs"].items():
  check(blob(root/name)==sha,"SOURCE_CHANGED:"+name)
 prior=set()
 for m in cohort["prior_manifests"]:
  f=root/m["path"]
  check(blob(f)==m["blob"],"PRIOR_SOURCE_DRIFT:"+m["path"])
  names=json.loads(f.read_text())["ids"]
  check(len(names)==m["length"],"PRIOR_IDS_DRIFT")
  prior.update(names)
 check(len(prior)==280,"PREVIOUS_COHORT_INCOMPLETE")
 filenames=[p.name for p in (arc/"data/evaluation").glob("*.json")]
 check(len(filenames)==400,"UPSTREAM_COUNT")
 remaining=[x for x in filenames if x not in prior]
 seed="neumann-q3-p19-first-fresh-transfer-20261105|"
 def fnv(s):
  h=2166136261
  for c in s:h=((h^ord(c))*16777619)&0xffffffff
  return h
 selected=sorted(remaining,key=lambda x:(fnv(seed+x),x))[:48]
 check(selected==cohort["ids"],"CANDIDATE_IDS_DRIFT")
 check([x["id"]+".json"for x in report["rows"]]==selected,"FIRST_RESULTS_REORDERED")
 independent_proofs=0
 independently_original_correct=0
 proposed_ids=[]
 for name,row in zip(selected,report["rows"]):
  task_bytes=(arc/"data/evaluation"/name).read_bytes()
  check(hashlib.sha256(task_bytes).hexdigest()==row["original_file_sha256"],"UPSTREAM_FILE_CHANGED:"+name)
  task=json.loads(task_bytes)
  cert=row["P19_certificate"]
  if cert is None:
   check(not row["P19_submitted"],"NONEXISTENT_P19_PROGRAM:"+name)
   continue
  proposed_ids.append(name)
  check(row["P19_submitted"],"HIDDEN_P19_PROGRAM:"+name)
  if cert["schema"]!="neumann.q3.p19.public-execution-certificate.v1":
   errors.append("CERT_SCHEMA:"+name);continue
  # No original TEST output is accessed until certificate execution is replayed.
  train=cert["train"];inputs=cert["test_inputs"];proposed=cert["predicted_test"]
  check(train==task["train"],"PUBLIC_TRAIN_DIFFERENT:"+name)
  check(inputs==[z["input"]for z in task["test"]],"TEST_INPUT_CHANGED:"+name)
  independent_replay=any(
   all(execute(p["input"],rep)==p["output"]for p in train)and
   [execute(x,rep)for x in inputs]==proposed
   for rep in cert["representative_ASTs"])
  check(independent_replay,"INDEPENDENT_PYTHON_EXECUTION_FAIL:"+name)
  if independent_replay:independent_proofs+=1
  # Open original TEST gold only after the frozen program was evaluated above.
  true_answer=[z["output"]for z in task["test"]]
  original_correct=proposed==true_answer
  if original_correct:independently_original_correct+=1
  check(original_correct==row["P19_correct"],"FIRST_ORIGINAL_VERIFIER_DISAGREES:"+name)
 totals=report["totals"]
 check(totals["n"]==48,"SCORE_N")
 check(totals["P19_submitted"]==len(proposed_ids),"P19_SUBMITTED_AGGREGATE")
 check(totals["P19"]==independently_original_correct,"P19_ORIGINAL_CORRECT_AGGREGATE")
 check(totals["gained"]==sum(bool(z["gained"])for z in report["rows"]),"GAIN_SUM_DRIFT")
 check(totals["combined"]==sum(bool(z["combined_correct"])for z in report["rows"]),"BASELINE_COMBINED_DRIFT")
 check(totals["baseline"]==sum(bool(z["base_correct"])for z in report["rows"]),"BASELINE_SUM_DRIFT")
 check(totals["P19_total_ASTs"]==sum(z["P19_candidate_ASTs"]for z in report["rows"]),"AST_SUM_DRIFT")
 check(totals["P19_train_pair_checks"]==sum(z["P19_train_replays"]for z in report["rows"]),"TRAIN_CALL_SUM_DRIFT")
 check(totals["gained"]==0 and totals["P19"]==1 and totals["baseline"]==2,"SCIENTIFIC_STOP_RESULT_CHANGED")
 check(report["scientific_status"]=="P19_FRESH_TRANSFER_FAIL_STOP","FIRST_NEGATIVE_GATE_RELABELED")
 return{"schema":"neumann.q3.p19.first-fresh48-independent-python.v1",
 "audit_pass":not errors,"errors":errors,
 "first_sha256":hashlib.sha256(raw).hexdigest(),
 "n":len(selected),"matched_baseline_original_exact_from_hashlocked_flags":totals["baseline"],
 "matching_classical_solver_internals_independently_reimplemented":False,
 "P19_submitted_programs":len(proposed_ids),"P19_submitted_original_ids":proposed_ids,
 "independent_python_replayed_certificate_count":independent_proofs,
 "independent_original_exact":independently_original_correct,
 "additional_original_exact":totals["gained"],
 "previously_unevaluated_original_reserve":72,
 "source_hypothesis":"human-designed bounded program DSL; not new autonomous opcode",
 "scientific_status":"P19_FRESH_TRANSFER_FAIL_STOP",
 "Q3":"OPEN","Q6":"OPEN"}
if __name__=="__main__":
 if len(sys.argv)!=4:raise SystemExit("Usage: script ROOT ARC_ROOT ORIGINAL_FIRST_RECEIPT")
 out=verify(sys.argv[1],sys.argv[2],sys.argv[3])
 print(json.dumps(out,indent=2,sort_keys=True))
 if not out["audit_pass"]:raise SystemExit(1)
