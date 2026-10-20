"""Certified ONE-STEP published-original UNSAFE counterexample for prod4br.
No source edits or gold invariant. Positive independent SAT in Z3+cvc5 and
negative source successor uniqueness UNSAT in both. CLASSICAL falsification.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import z3
from experiments.q3_source_prove import (
 sexprs,extract_mixed_original,native_original_relations,check_parity,
 check_formula)

REL="benchmarks/NIA/other/prod4br.sl"
BLOB="81b9f72de2b2ee569a2f395fac2fd67164f0a10f"
BEFORE=(1,1,1,1,1,0)
AFTER=(1,1,0,0,1,-1)
UPSTREAM="6ac90265b11431c9477dfbd33e3e3380234c0499"

def blob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def ms(start):return round((time.perf_counter_ns()-start)/1e6,3)

def independently_check(name,formula,desired,timeout=7):
 start=time.perf_counter_ns()
 s=z3.Solver();s.set(timeout=timeout*1000);s.add(formula)
 ze=str(s.check())
 if ze!=desired:
  return {"name":name,"native_Z3":ze,"expected":desired,
   "dual_certified":False,"total_wall_ms":ms(start)}
 try:
  proc=subprocess.run(["cvc5","--lang=smt2","--tlimit-per="+str(timeout*1000),"-"],
       input=s.to_smt2(),text=True,capture_output=True,timeout=timeout+4)
  lines=[t.strip() for t in proc.stdout.splitlines() if t.strip()]
  ce=lines[-1] if lines else "NO_RESULT"
  return {"name":name,"native_Z3":ze,"independent_cvc5":ce,
     "cvc5_exit":proc.returncode,
     "dual_certified":ce==desired and proc.returncode==0,
     "total_wall_ms":ms(start),"stderr_excerpt":proc.stderr[:130]}
 except Exception as ex:
  return {"name":name,"native_Z3":ze,
          "independent_cvc5":"ERROR:"+type(ex).__name__,
          "dual_certified":False,"total_wall_ms":ms(start)}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--root",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 a=ap.parse_args()
 t=time.perf_counter_ns()
 raw=(a.root/REL).read_bytes()
 if blob(raw)!=BLOB:raise ValueError("PINNED_SOURCE_GIT_BLOB_MISMATCH")
 forms=sexprs(raw);src=extract_mixed_original(forms)
 native=native_original_relations(forms,src)
 now,nxt=src["now"],src["next"]
 if len(now)!=6 or len(nxt)!=6:raise RuntimeError("SOURCE_STATE_ARITY_MISMATCH")
 parity=check_parity(src,native)
 if set(parity)!={"pre","trans","post"} or any(x!="unsat" for x in parity.values()):
  raise RuntimeError("NATIVE_CUSTOM_ORIGINAL_SEMANTICS_DIFFERENT")
 orig_next_post=z3.substitute(native["post"],*list(zip(now,nxt)))
 now_match=z3.And(*[v==int(z) for v,z in zip(now,BEFORE)])
 nxt_match=z3.And(*[v==int(z) for v,z in zip(nxt,AFTER)])
 source_one_step=z3.And(native["pre"],now_match,native["trans"],
                        nxt_match,z3.Not(orig_next_post))
 obligations=[
  independently_check("ORIGINAL_SOURCE_PRE_SAT",native["pre"],"sat"),
  independently_check("ORIGINAL_SOURCE_NONVACUOUS_NOTPOST",z3.Not(native["post"]),"sat"),
  independently_check("EXPLICIT_REAL_ORIGINAL_PRE_WITNESS",
      z3.And(native["pre"],now_match),"sat"),
  independently_check("CURRENT_INITIAL_STATE_IS_NOT_ALREADY_UNSAFE",
      z3.And(native["pre"],now_match,z3.Not(native["post"])),"unsat"),
  independently_check("EXACT_ORIGINAL_TRANS_ONE_STEP_REACHABLE",
      z3.And(native["pre"],now_match,native["trans"],nxt_match),"sat"),
  independently_check("ACTUAL_SOURCE_NEXT_UNIQUE_UNDER_THIS_PRE",
      z3.And(native["pre"],now_match,native["trans"],z3.Not(nxt_match)),"unsat"),
  independently_check("NEXT_ORIGINAL_PUBLISHED_POST_IS_FALSE",
      z3.And(nxt_match,orig_next_post),"unsat"),
  independently_check("TRUE_PUBLISHED_ORIGINAL_ONE_STEP_BAD_EXECUTION",
      source_one_step,"sat"),
  independently_check("EXISTS_UNCONSTRAINED_ONE_STEP_BAD_SOURCE_PATH",
      z3.And(native["pre"],native["trans"],z3.Not(orig_next_post)),"sat"),
 ]
 all_pass=all(x["dual_certified"] for x in obligations)
 report={"schema":"neumann.q3.real_original.prod4br.unsafe.one_step.v1",
    "source":REL,"git_blob":BLOB,
    "source_content_sha256":hashlib.sha256(raw).hexdigest(),
    "upstream_revision":UPSTREAM,"original_semantic_parser_parity":parity,
    "source_current_state_from_original_Pre":list(BEFORE),
    "source_next_state_from_original_Trans":list(AFTER),
    "witness_branch":"BOTH_ORIGINAL_INPUTS_ODD",
    "witness_source_is_unmodified_published_original":True,
    "actual_reachable_bad_step_dual_solver_evidence":obligations,
    "proof_obligation_count":len(obligations),
    "independently_dual_verified_obligations":sum(x["dual_certified"] for x in obligations),
    "original_unmodified_program_UNSAFE":all_pass,
    "sound_inductive_invariant_for_same_original_Post_exists":False if all_pass else None,
    "earlier_first_G0_result_preserved":"UNRESOLVED_NOT_RETROACTIVELY_RELABELED",
    "classical_counterexample_no_neural_training":True,
    "global_Q3":"OPEN","global_Q1_Q7":"OPEN",
    "wall_ms":ms(t),"gpu_calls":0,"paid_API_calls":0}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("REAL_ORIGINAL_UNSAFE",all_pass,"DUAL",report["independently_dual_verified_obligations"],"/",len(obligations))
 print("COUNTEREXAMPLE",list(BEFORE),"->",list(AFTER))
 for x in obligations:
  print("ORIGINAL_PROOF_STEP",x["name"],x["native_Z3"],x.get("independent_cvc5"),x["dual_certified"])
 print("Q3_GLOBAL",report["global_Q3"])

if __name__=="__main__":main()
