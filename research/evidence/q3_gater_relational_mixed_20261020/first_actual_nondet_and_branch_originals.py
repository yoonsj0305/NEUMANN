"""Gate R source semantics: preserve all nondet declared globals, mixed
Bool/Int function calls and nondeterministic OR transition branches.
POSTHOC on opened external source. No neural operator invention claim.
"""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
import z3
HERE=Path(__file__).resolve().parents[3]/"research/evidence/q3t-mixed-original-20261018"
sys.path.insert(0,str(HERE))
from mixed_sygus_original import UnsupportedOriginal,SORTS,parse_signature,compile_original,sexprs
COHORT=[
 ("lib/Inv_Track/xujie_code2inv/1.c.sl","859bae24a9f26044a40a3c97f1d2e5fc08504f06"),
 ("lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl","8490b3e25ff7d462a7405e68e742be1abb35b8f8")]
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
def sha(x):return hashlib.sha256(x).hexdigest()
def blob(x):return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def elapsed(t):return round((time.perf_counter_ns()-t)/1e6,3)
def render(x):
 return ("("+" ".join(map(render,x))+")") if isinstance(x,list) else str(x)
def dual(formula,expected,limit=8):
 t=time.perf_counter_ns()
 solver=z3.Solver();solver.set(timeout=limit*1000);solver.add(formula)
 zv=str(solver.check());res={"Z3":zv,"Z3_ms":elapsed(t),"expected":expected}
 if zv!=expected:return {**res,"dual_pass":False}
 try:
  p=subprocess.run(["cvc5","--lang=smt2",f"--tlimit-per={limit*1000}","-"],
    input=solver.to_smt2(),text=True,capture_output=True,timeout=limit+5)
  out=[z.strip() for z in p.stdout.splitlines() if z.strip()]
  cs=out[-1] if out else "EMPTY"
  return {**res,"cvc5":cs,"cvc5_exit":p.returncode,
    "cvc5_stderr":p.stderr[:130],"dual_pass":cs==expected and p.returncode==0,
    "wall_ms":elapsed(t)}
 except Exception as ex:
  return {**res,"cvc5":"ERROR:"+str(ex)[:140],"dual_pass":False}

def compile_typed_original(forms):
 defs={};globals_={}
 for x in forms:
  if not isinstance(x,list) or not x:continue
  if x[0]=="define-fun":
   if len(x)!=5 or x[1] in defs or x[3] not in SORTS:
    raise UnsupportedOriginal("MALFORMED_ORIGINAL_HELPER")
   defs[x[1]]={"args":parse_signature(x[2]),"output":x[3],"body":x[4]}
  if x[0]=="declare-var":
   if len(x)!=3 or x[1] in globals_ or x[2] not in SORTS:
    raise UnsupportedOriginal("UNSUPPORTED_DECLARED_NONDET")
   globals_[x[1]]=z3.Const(x[1],SORTS[x[2]])
 specs=[x for x in forms if isinstance(x,list) and x and x[0]=="synth-inv"]
 cs=[x for x in forms if isinstance(x,list) and x and x[0]=="inv-constraint"]
 if len(specs)!=1 or len(cs)!=1 or len(cs[0])!=5:
  raise UnsupportedOriginal("ORIGINAL_SYNTH_CONTRACT_SHAPE")
 spec=specs[0];c=cs[0]
 if spec[1]!=c[1]:raise UnsupportedOriginal("ORIGINAL_INVARIANT_NAMING")
 states=parse_signature(spec[2])
 pre_name,tr_name,post_name=c[2:]
 if any(k not in defs for k in (pre_name,tr_name,post_name)):
  raise UnsupportedOriginal("MISSING_ORIGINAL_PRE_TRANS_POST")
 if defs[pre_name]["args"]!=states or defs[post_name]["args"]!=states:
  raise UnsupportedOriginal("INVALID_ORIGINAL_STATE_ARGUMENTS")
 trargs=defs[tr_name]["args"]
 if len(trargs)!=2*len(states) or trargs[:len(states)]!=states or [s for _,s in trargs[len(states):]]!=[s for _,s in states]:
  raise UnsupportedOriginal("ORIGINAL_TRANS_SIGNATURE_DIFFERS")
 if len(states)>250 or len(globals_)>150 or len(defs)>100:
  raise UnsupportedOriginal("RESOURCE_CAP")
 now=[z3.Const("q3R_now_"+str(i),SORTS[s]) for i,(_,s) in enumerate(states)]
 nxt=[z3.Const("q3R_next_"+str(i),SORTS[s]) for i,(_,s) in enumerate(states)]
 preds={}
 for key,name,args in [
  ("pre",pre_name,now),("trans",tr_name,now+nxt),("post",post_name,now)]:
  arg_names=[n for n,_ in defs[name]["args"]]
  pred,_=compile_original(defs[name]["body"],
        {**globals_,**dict(zip(arg_names,args))},defs)
  if not z3.is_bool(pred):raise UnsupportedOriginal("NOT_BOOL_RELATION")
  preds[key]=pred
 return {"states":states,"now":now,"next":nxt,"globals":globals_,
  "names":{"pre":pre_name,"trans":tr_name,"post":post_name},**preds}

def compile_independent_native(forms,src):
 # Only SyGuS declare-var command becomes equivalent SMT-LIB declaration.
 # Every ORIGINAL definition body is parsed by Z3 itself, independent
 # from the custom helper-expanding Python compiler.
 native=[]
 for form in forms:
  if not isinstance(form,list) or not form:continue
  if form[0] in ("set-logic","define-fun"):native.append(render(form))
  elif form[0]=="declare-var":
   native.append("(declare-const "+form[1]+" "+form[2]+")")
  elif form[0] not in ("synth-inv","inv-constraint","check-synth"):
   raise UnsupportedOriginal("UNEXPECTED_SYGUS_COMMAND_"+form[0])
 for var in src["now"]+src["next"]:
  sort="Bool" if var.sort().kind()==z3.Z3_BOOL_SORT else "Int"
  native.append("(declare-const "+str(var)+" "+sort+")")
 result={}
 for kind,args in (("pre",src["now"]),("trans",src["now"]+src["next"]),("post",src["now"])):
  program="\n".join(native)+"\n(assert ("+src["names"][kind]+" "+" ".join(map(str,args))+"))\n"
  expressions=z3.parse_smt2_string(program)
  if len(expressions)!=1:raise UnsupportedOriginal("NATIVE_PARSE_NOT_ONE_ASSERT")
  result[kind]=expressions[0]
 return result

def branch_original(src,native):
 branches=list(src["trans"].children()) if z3.is_or(src["trans"]) else [src["trans"]]
 if len(branches)<2:return {"branch_count":len(branches),"status":"NO_MULTIBRANCH"}
 if len(branches)>16:return {"branch_count":len(branches),"status":"BRANCH_CAP"}
 exact=dual(z3.Xor(native["trans"],z3.Or(*branches)),"unsat")
 # Losing a branch is a real semantics violation, intentionally rejected.
 drop=dual(z3.And(native["trans"],z3.Not(z3.Or(*branches[1:]))),"sat")
 checks=[]
 for i,b in enumerate(branches):
  checks.append({"index":i,"branch_sha256":sha(b.sexpr().encode()),
   "original_Pre_and_branch":dual(z3.And(src["pre"],b),"sat")})
 return {"branch_count":len(branches),
   "exact_original_DNF":exact,
   "drop_first_branch_negative_control":drop,
   "branches":checks,
   "branch_original_semantics_dual_proved":exact["dual_pass"],
   "negative_branch_drop_dual_proved":drop["dual_pass"]}

def case(root,path,githash):
 t=time.perf_counter_ns()
 out={"source":path,"git_blob":githash,"status":"NOT_EVALUATED"}
 try:
  raw=(root/path).read_bytes()
  if blob(raw)!=githash:raise ValueError("PINNED_SOURCE_BLOB_MISMATCH")
  out["real_source_sha256"]=sha(raw)
  forms=sexprs(raw)
  parsed=compile_typed_original(forms)
  out["original_nondet_declared_globals"]=len(parsed["globals"])
  out["original_state_ints"]=sum(s=="Int" for _,s in parsed["states"])
  out["original_state_bools"]=sum(s=="Bool" for _,s in parsed["states"])
  independent=compile_independent_native(forms,parsed)
  out["source_native_typed_XOR"]={name:dual(z3.Xor(parsed[name],independent[name]),"unsat",limit=12)
    for name in ("pre","trans","post")}
  out["all_three_original_semantics_dual_certified"]=all(
    row["dual_pass"] for row in out["source_native_typed_XOR"].values())
  out["nonvacuity"]={
   "original_Pre_SAT":dual(parsed["pre"],"sat"),
   "original_NotPost_SAT":dual(z3.Not(parsed["post"]),"sat"),
   "original_Trans_SAT":dual(parsed["trans"],"sat")}
  out["source_branches"]=branch_original(parsed,independent)
  out["status"]=("DUAL_NATIVE_ORIGINAL_FRONTEND_PASS"
    if out["all_three_original_semantics_dual_certified"]
    else "UNVERIFIED_ORIGINAL_FRONTEND")
 except Exception as exc:
  out["status"]="ABSTAIN_SOURCE_PARSER"
  out["error"]=type(exc).__name__+":"+str(exc)[:260]
 out["wall_ms"]=elapsed(t)
 print("REAL_GATE_R",path,out["status"],
   "NONDET",out.get("original_nondet_declared_globals"),
   "BOOL",out.get("original_state_bools"),
   "ERROR",out.get("error"),flush=True)
 return out
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 t=time.perf_counter_ns()
 cases=[case(a.root,*z) for z in COHORT]
 out={"schema":"neumann.q3.gate_R.original_source_preserving_semantic_frontend.v1",
  "two_existing_opened_sources_POSTHOC":True,
  "upstream_revision":UPSTREAM,
  "all_two_source_git_blobs_verified":all("real_source_sha256" in c for c in cases),
  "exact_three_predicate_dual_source_count":sum(c.get("all_three_original_semantics_dual_certified",False) for c in cases),
  "xujie_original_disjunctive_transition_dual_proved":cases[0].get("source_branches",{}).get("branch_original_semantics_dual_proved",False),
  "andrew_original_mixed_Bool_Int_nondet_dual_proved":cases[1].get("all_three_original_semantics_dual_certified",False),
  "new_learned_nonpolynomial_operator":"NOT_DEMONSTRATED",
  "gate_R_complete":"OPEN",
  "gate_V":"OPEN","global_Q3":"OPEN","global_Q1_Q7":"OPEN",
  "GPU_calls":0,"paid_API_calls":0,"elapsed_ms":elapsed(t),
  "sources":cases}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
 print("GATE_R_ORIGINAL_SEMANTIC_DUAL",out["exact_three_predicate_dual_source_count"],"/2")
 print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":main()
