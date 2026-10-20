"""NEUMANN 1 Q3: generic first bounded original bad-path detector.
Three public source SHA identities frozen BEFORE source bodies inspected.
A *sound UNSAFE certifier*, not a SAFE verifier, neural model, or global Q3.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import z3
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity)

REV="6ac90265b11431c9477dfbd33e3e3380234c0499"
COHORT=[
 ("BLIND_NEW","benchmarks/NIA/other/pottsumm3.sl","e0734e4358956b3ca66d280c9d4f8282b18d29b4"),
 ("BLIND_NEW","benchmarks/NIA/2018.CHI_InvGame/s9.desugared.sl","36234fd712b21a9111f834058e8371b10e3de191"),
 ("BLIND_NEW","benchmarks/NIA/2018.CHI_InvGame/non-lin-ineq-3.desugared.sl","728ee7e03686db111e47b429e3d584ad3ed668db"),
 ("KNOWN_UNSAFE_POSITIVE_CONTROL","benchmarks/NIA/other/prod4br.sl","81b9f72de2b2ee569a2f395fac2fd67164f0a10f"),
 ("KNOWN_SAFE_NEGATIVE_CONTROL","benchmarks/NIA/other/mul.sl","f6291a03edee61b5624bd5b394913988d4c5af9a"),
 ("KNOWN_SAFE_NEGATIVE_CONTROL","benchmarks/NIA/2018.CHI_InvGame/sorin04.desugared.sl","565795c4792ead110b65aad27fa5657bbbee074e"),
]
DEPTHS=range(4)
Z3_TIMEOUT_MS=3000
CVC5_TIMEOUT_SECONDS=7
def sha(b):return hashlib.sha256(b).hexdigest()
def gitblob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def wall(t):return round((time.perf_counter_ns()-t)/1e6,3)
def z3check(formula):
 t=time.perf_counter_ns()
 s=z3.Solver();s.set(timeout=Z3_TIMEOUT_MS);s.add(formula)
 verdict=str(s.check())
 return verdict,(s.model() if verdict=="sat" else None),wall(t)
def external(formula):
 t=time.perf_counter_ns()
 s=z3.Solver();s.add(formula)
 try:
  proc=subprocess.run(["cvc5","--lang=smt2",f"--tlimit-per={CVC5_TIMEOUT_SECONDS*1000}","-"],
    input=s.to_smt2(),capture_output=True,text=True,timeout=CVC5_TIMEOUT_SECONDS+4)
  lines=[x.strip() for x in proc.stdout.splitlines() if x.strip()]
  status=lines[-1] if lines else "NO_RESULT"
  return {"status":status,"exit_code":proc.returncode,
   "wall_ms":wall(t),"stderr_excerpt":proc.stderr[:120]}
 except Exception as exc:
  return {"status":"EXTERNAL_ERROR","error":str(exc)[:160],"wall_ms":wall(t)}
def substitute_pre(expr,old,new):
 return z3.substitute(expr,*list(zip(old,new)))
def build_chain(native,src,depth):
 physical=list(src["now"])
 next_names=list(src["next"])
 if len(physical)!=len(next_names):raise ValueError("WRONG_STATE_ARITY")
 sorts=[v.sort() for v in physical]
 if any(s.kind()!=z3.Z3_INT_SORT for s in sorts):raise ValueError("UNSUPPORTED_NONINTEGER_ORIGINAL")
 states=[
  [z3.Const(f"q3_bmc_t{k}_{j}",sorts[j]) for j in range(len(physical))]
  for k in range(depth+1)]
 pre=substitute_pre(native["pre"],physical,states[0])
 trans=[z3.substitute(native["trans"],
         *list(zip(physical,states[k])),
         *list(zip(next_names,states[k+1])))
         for k in range(depth)]
 bad=z3.Not(substitute_pre(native["post"],physical,states[-1]))
 return states,pre,trans,bad

def one(root,kind,path,expected):
 t=time.perf_counter_ns()
 row={"role":kind,"source":path,"pinned_git_blob":expected,
      "depth_rows":[],"first_proven_bad_depth":None,
      "classification":"UNKNOWN_OR_NOT_YET_ANALYZED"}
 try:
  raw=(root/path).read_bytes()
  if gitblob(raw)!=expected:raise ValueError("ORIGINAL_GIT_BLOB_MISMATCH")
  row["source_sha256"]=sha(raw)
  s=sexprs(raw);src=extract_mixed_original(s)
  nat=native_original_relations(s,src)
  nat.update({"now":src["now"],"next":src["next"]})
  parity=check_parity(src,nat)
  row["native_original_custom_semantic_parity"]=parity
  if set(parity)!={"pre","trans","post"} or any(v!="unsat" for v in parity.values()):
   row["classification"]="ABSTAIN_PARSER_SEMANTICS_MISMATCH"
   return row
  if len(src["now"])!=len(src["next"]):raise ValueError("STATE_SHAPE_MISMATCH")
  if any(v.sort().kind()!=z3.Z3_INT_SORT for v in src["now"]):
   row["classification"]="ABSTAIN_NON_INTEGER_STATE"
   return row
  pre_verdict,_,_=z3check(nat["pre"])
  row["original_pre_sat"]=pre_verdict
  if pre_verdict!="sat":
   row["classification"]="ABSTAIN_PRE_VACUOUS_OR_UNKNOWN"
   return row
  for depth in DEPTHS:
   states,pre,trans,bad=build_chain(nat,src,depth)
   formula=z3.And(pre,*trans,bad)
   status,model,z3wall=z3check(formula)
   audit={"depth":depth,"original_bound_pre_trans_negpost_Z3":status,
      "original_Z3_wall_ms":z3wall,
      "interpretation":"SAT_UNSAFE_WITNESS_REQUIRED" if status=="sat" else
       "UNSAT_BOUNDED_ONLY_NOT_SAFE" if status=="unsat" else "UNKNOWN_NOT_SAFE"}
   if status=="sat":
    witness=[[int(model.eval(x,model_completion=True).as_long())
       for x in state] for state in states]
    audit["model_physical_original_states"]=witness
    # The full ground chain is the actual original Pre/Trans/Post formula,
    # not a hand-built simulator or a mutated source contract.
    allfixed=z3.And(*[
      x==z3.IntVal(n) for state,values in zip(states,witness)
      for x,n in zip(state,values)])
    ground=z3.And(formula,allfixed)
    grounded,_,_=z3check(ground)
    external_full=external(ground) if grounded=="sat" else {"status":"NOT_RUN"}
    audit["exact_ground_original_chain_Z3"]=grounded
    audit["exact_ground_original_chain_cvc5"]=external_full
    local=[]
    for phase,claim in (
      [("source_PRE",pre)]+
      [(f"source_TRANS_{j}",c) for j,c in enumerate(trans)]+
      [("source_NOT_POST",bad)]):
     fixedclaim=z3.And(claim,allfixed)
     res,_,_=z3check(fixedclaim)
     ce=external(fixedclaim) if res=="sat" else {"status":"NOT_RUN"}
     local.append({"phase":phase,"Z3":res,"cvc5":ce,
                   "dual_grounded":res=="sat" and ce.get("status")=="sat"
                     and ce.get("exit_code")==0})
    audit["source_phase_ground_dual"] = local
    dual=(grounded=="sat" and external_full.get("status")=="sat"
        and external_full.get("exit_code")==0
        and all(c["dual_grounded"] for c in local))
    audit["dual_authentic_original_bad_execution"]=dual
    row["depth_rows"].append(audit)
    if dual:
     row["classification"]="PROVEN_UNSAFE_REAL_ORIGINAL"
     row["first_proven_bad_depth"]=depth
     row["independent_cvc5_actual_witness"]=True
     break
    row["classification"]="ABSTAIN_SAT_UNCONFIRMED_INDEPENDENT_CVC5"
    break
   row["depth_rows"].append(audit)
  else:
   row["classification"]="NO_BAD_WITNESS_WITHIN_DEPTH_0_TO_3_NOT_SAFE_PROOF"
 except Exception as exc:
  row["classification"]="ABSTAIN_EXCEPTION_FAIL_CLOSED"
  row["error"]=type(exc).__name__+":"+str(exc)[:280]
 row["total_source_wall_ms"]=wall(t)
 return row

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",required=True,type=Path)
 parser.add_argument("--out",required=True,type=Path)
 args=parser.parse_args()
 t=time.perf_counter_ns()
 rows=[]
 for kind,path,blob in COHORT:
  r=one(args.root,kind,path,blob)
  rows.append(r)
  print("REAL_SOURCE",path,"ROLE",kind,"RESULT",r["classification"],
     "BOUND",r["first_proven_bad_depth"],flush=True)
 known_unsafe=[r for r in rows if r["role"]=="KNOWN_UNSAFE_POSITIVE_CONTROL"]
 known_safe=[r for r in rows if r["role"]=="KNOWN_SAFE_NEGATIVE_CONTROL"]
 blind=[r for r in rows if r["role"]=="BLIND_NEW"]
 quality=(len(rows)==6 and
    known_unsafe[0]["classification"]=="PROVEN_UNSAFE_REAL_ORIGINAL" and
    known_unsafe[0]["first_proven_bad_depth"]==1 and
    all(r["classification"]!="PROVEN_UNSAFE_REAL_ORIGINAL" for r in known_safe) and
    all(r.get("source_sha256") and
        r.get("native_original_custom_semantic_parity")==
           {"pre":"unsat","trans":"unsat","post":"unsat"}
        for r in rows))
 report={
 "schema":"neumann.q3.source_preflight.generic_BMC_0_3.first_six_originals.v1",
 "upstream_git_rev":REV,
 "all_six_exact_blob_hashes_and_semantic_parity":all(
    r.get("source_sha256") and
    r.get("native_original_custom_semantic_parity")==
       {"pre":"unsat","trans":"unsat","post":"unsat"}
     for r in rows),
 "generic_detector_uses_no_manual_witness":True,
 "BMC_depths_fixed_before_source_inspection":list(DEPTHS),
 "Z3_timeout_per_source_per_depth_ms":Z3_TIMEOUT_MS,
 "three_new_sources_metadata_frozen_before_original_contents":True,
 "all_six_rows_retained":len(rows)==6,
 "previously_known_unsafe_positive_control_detected":(
  known_unsafe[0]["classification"]=="PROVEN_UNSAFE_REAL_ORIGINAL" and
  known_unsafe[0]["first_proven_bad_depth"]==1),
 "false_unsafe_positive_on_known_safe_controls":sum(
  r["classification"]=="PROVEN_UNSAFE_REAL_ORIGINAL" for r in known_safe),
 "new_blind_sources_proven_unsafe":sum(
  r["classification"]=="PROVEN_UNSAFE_REAL_ORIGINAL" for r in blind),
 "new_blind_sources_neither_safe_nor_proven_unsafe":sum(
  r["classification"]!="PROVEN_UNSAFE_REAL_ORIGINAL" for r in blind),
 "scoped_generic_automated_safety_triage_pass":bool(quality),
 "original_full_unbounded_SAFE_from_BMC":False,
 "learned_neural_first_new_structure":False,
 "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
 "paid_API_calls":0,"GPU_calls":0,"whole_study_wall_ms":wall(t),
 "sources":rows}
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("AUTOMATED_ORIGINAL_SOURCE_TRIAGE_PASS",quality,
    "NEW_UNSAFE_BLIND",report["new_blind_sources_proven_unsafe"],
    "GLOBAL_Q3",report["global_Q3"],flush=True)
if __name__=="__main__":main()
