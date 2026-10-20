"""Q3 source-only modular congruence Houdini for genuine published lcm.sl.
NO neural inference, NO manually supplied four formula candidates.
All candidate atoms enumerated from original mutable terms and static moduli;
original Post only used in final independent three VC test.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,subprocess,time
from pathlib import Path
import z3
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,
 check_formula,source_proof)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

REL="benchmarks/NIA/other/lcm.sl"
BLOB="6c0cbaafc0c8b960d6047014dc5670554aacbc85"
SRC_SHA="c488e8b87d96e48916ffd95c656c3ef712f3d8f327128a461814f3d424936667"
EXPECTED={"initial":"unsat","consecution":"unsat","post":"unsat"}
def now_ms(t):return round((time.perf_counter_ns()-t)/1e6,3)
def exact_git_blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def source_bad_vcs(candidate,source,native):
 # Unmodified original trusted ASTs exactly.
 now,nxt=source["now"],source["next"]
 new=z3.substitute(candidate,*list(zip(now,nxt)))
 return {"initial":z3.And(native["pre"],z3.Not(candidate)),
 "consecution":z3.And(candidate,native["trans"],z3.Not(new)),
 "post":z3.And(candidate,z3.Not(native["post"]))}
def cvc5_on_vc(bad,timeout=15):
 t=time.perf_counter_ns()
 s=z3.Solver();s.add(bad)
 script=s.to_smt2()
 try:
  p=subprocess.run(["cvc5","--lang=smt2","--decision=internal",
      "--tlimit-per="+str(timeout*1000),"-"],
      input=script,capture_output=True,text=True,timeout=timeout+4,check=False)
  lines=[q.strip() for q in p.stdout.splitlines() if q.strip()]
  return {"result":lines[-1] if lines else "EMPTY",
    "exit_code":p.returncode,"wall_ms":now_ms(t),
    "stderr_excerpt":p.stderr[:160]}
 except Exception as ex:
  return {"result":"NO_RESULT","error":str(ex)[:180],"wall_ms":now_ms(t)}
def query(*constraints,timeout=5000):
 s=z3.Solver();s.set(timeout=timeout)
 s.add(*constraints)
 result=s.check()
 return str(result), s.model() if result==z3.sat else None

def generate_candidates(source,native):
 now,nxt=source["now"],source["next"]
 statics=[];changes=[]
 for idx,(v,vp) in enumerate(zip(now,nxt)):
  status,_=query(native["trans"],v!=vp)
  if status=="unsat":
   if query(native["pre"],z3.Not(v>0))[0]=="unsat":
    statics.append(idx)
  elif status=="sat":changes.append(idx)
  else:raise RuntimeError("ORIGINAL_SOURCE_CONSTANCY_UNPROVEN_"+str(idx))
 if not statics or not changes:raise RuntimeError("ORIGINAL_SOURCE_STATIC_OR_MUTABLE_EMPTY")
 candidates=[]
 for modulus_idx in statics:
  m=now[modulus_idx]
  for i in changes:
   expr=now[i]
   candidates.append((f"{expr} mod {m} = 0", expr%m==0,modulus_idx))
  for i,j in itertools.combinations(changes,2):
   for sign in (1,-1):
    expr=now[i]+sign*now[j]
    candidates.append((f"({now[i]} {'+' if sign==1 else '-'} {now[j]}) mod {m} = 0",
                        expr%m==0,modulus_idx))
 positives=[]
 for i,v in enumerate(now):
  if query(native["pre"],z3.Not(v>0))[0]=="unsat":
   positives.append((f"{v}>0",v>0,None))
  elif query(native["pre"],z3.Not(v>0))[0]=="unknown":
   raise RuntimeError("POSITIVE_SOURCE_UNKNOWN")
 return statics,changes,candidates,positives

def source_only_houdini(source,native,atoms):
 now,nxt=source["now"],source["next"]
 pre_valid=[];not_pre=[];statuses=[]
 for (label,f,m) in atoms:
  status,_=query(native["pre"],z3.Not(f))
  statuses.append((label,status))
  if status=="unsat":pre_valid.append((label,f,m))
  else:not_pre.append((label,status))
 work=pre_valid.copy();rounds=[];smt_checks=0
 for iteration in range(len(work)+1):
  inv=z3.And(*[f for _,f,_ in work])
  # Check *every* candidate under conjunction, with no target Post.
  rejected=[]
  for label,formula,mod in work:
   fp=z3.substitute(formula,*list(zip(now,nxt)))
   status,_=query(inv,native["trans"],z3.Not(fp),timeout=5000)
   smt_checks+=1
   if status!="unsat":rejected.append((label,status))
  rounds.append({"iteration":iteration,"candidate_count_before":len(work),
    "rejected":rejected})
  if not rejected:break
  bad={label for label,status in rejected}
  work=[v for v in work if v[0] not in bad]
 else:raise RuntimeError("HOUDINI_UNTERMINATED")
 inv=z3.And(*[f for _,f,_ in work])
 if query(native["pre"],inv)[0]!="sat":
  raise RuntimeError("VACUOUS_FINAL_INVARIANT")
 return {"pre_valid_candidates":[label for label,f,m in pre_valid],
  "pre_rejected":not_pre,"selection_rounds":rounds,
  "final_atom_names":[label for label,f,m in work],
  "final_atom_count":len(work),"candidate_prechecks":len(atoms),
  "inductiveness_checks":smt_checks},inv

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source-root",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 a=p.parse_args()
 whole=time.perf_counter_ns()
 raw=(a.source_root/REL).read_bytes()
 if exact_git_blob(raw)!=BLOB or hashlib.sha256(raw).hexdigest()!=SRC_SHA:
  raise RuntimeError("PINNED_ORIGINAL_SOURCE_IDENTITY_MISMATCH")
 parsed=sexprs(raw);src=extract_mixed_original(parsed)
 native=native_original_relations(parsed,src)
 native.update({"now":src["now"],"next":src["next"]})
 parity=check_parity(src,native)
 if set(parity)!={"pre","trans","post"} or any(x!="unsat" for x in parity.values()):
  raise RuntimeError("ORIGINAL_NATIVE_PRE_TRANS_POST_PARITY_FAIL")
 if query(native["pre"])[0]!="sat" or query(z3.Not(native["post"]))[0]!="sat":
  raise RuntimeError("VACUOUS_ORIGINAL_SOURCE_PRE_OR_POST")
 static,mutables,mods,positive=generate_candidates(src,native)
 t=time.perf_counter_ns()
 ledger,inv=source_only_houdini(src,native,mods+positive)
 discovery_wall=now_ms(t)
 # HAPPENS ONLY AFTER SOURCE-ONLY CANDIDATES ARE FROZEN.
 proof=source_proof(inv,native)
 full_vcs=source_bad_vcs(inv,src,native)
 original_z3={k:query(v,timeout=7000)[0] for k,v in full_vcs.items()}
 old_post_only=source_proof(native["post"],native)
 positive_only=source_proof(z3.And(*[p for label,p,m in positive]),native)
 unchanged=check_original_candidate(a.source_root/REL,inv.sexpr(),
                    expected_source_sha256=SRC_SHA) if proof["accepted"] else {}
 old3=unchanged.get("cvc5_original_three_vc") or {}
 oldpass=unchanged.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
 cvc5_15s={}
 if proof["accepted"] and not oldpass:
  # Prespecified 15 second ORIGINAL verification under independent cvc5 1.4.2.
  for name,obligation in full_vcs.items():
   cvc5_15s[name]=cvc5_on_vc(obligation,timeout=15)
 independent_pass=oldpass or (
    set(cvc5_15s)==set(EXPECTED) and
    all(v["result"]=="unsat" and v["exit_code"]==0 for v in cvc5_15s.values()))
 out={"schema":"neumann.q3.opened_lcm.classical_modular_lattice_original.v1",
   "SCIENCE_SCOPE":"POSTHOC SOURCE-ONLY CLASSICAL NO NEURAL GRADIENT TRAINING",
   "original_source":REL,"pinned_git_blob":BLOB,"original_source_sha256":SRC_SHA,
   "source_3_parity":parity,
   "static_positive_moduli":[str(src["now"][i]) for i in static],
   "mutable_state_variables":[str(src["now"][i]) for i in mutables],
   "generated_modular_atoms_before_precheck":len(mods),
   "preproved_positive_helper_atoms":[v[0] for v in positive],
   "source_only_discovery":ledger,
   "source_only_discovery_wall_ms":discovery_wall,
   "source_only_final_invariant_sexpr":inv.sexpr(),
   "source_only_no_gold_post_during_candidate_selection":True,
   "native_original_Z3_3VC":original_z3,
   "original_Z3_algorithm_accepts":proof["accepted"],
   "original_post_only_negative_control":old_post_only["vcs"],
   "source_positivity_only_negative_control":positive_only["vcs"],
   "frozen_3s_cvc5_original_3VC":old3,
   "frozen_3s_cvc5_full_pass":oldpass,
   "extra_15s_internal_cvc5_original_3VC":cvc5_15s,
   "independent_cvc5_3VC_full_pass":independent_pass,
   "posthoc_classical_scoped_pass":proof["accepted"] and independent_pass and
        original_z3==EXPECTED and not old_post_only["accepted"] and
        not positive_only["accepted"],
   "learned_neural_new_operator":False,
   "unique_neural_over_strong_classical":False,
   "genuinely_blind_source":False,"GPU_calls":0,"paid_API_calls":0,
   "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
   "whole_study_wall_ms":now_ms(whole)}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
 print("MOD_CANDIDATES",len(mods),"PRE_OK",len(ledger["pre_valid_candidates"]),
       "FINAL",ledger["final_atom_count"])
 print("CONGRUENCES_FINAL",ledger["final_atom_names"])
 print("ORIGINAL_Z3",original_z3)
 print("INDEPENDENT_CVC5",independent_pass,"original3s",old3,"extra15s",cvc5_15s)
 print("SCOPED_CLASSICAL_SOURCE_PASS",out["posthoc_classical_scoped_pass"])
 print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":main()
