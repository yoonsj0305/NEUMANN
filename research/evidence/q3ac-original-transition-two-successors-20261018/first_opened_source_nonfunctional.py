"""Q3AC: SOURCE-OPENED semantic diagnostic, not a blind result, not an invariant proof.
Check whether original transition relation has TWO different next-state tuples
for the SAME previous tuple. If yes, no exact single affine update graph can
describe its full original transition relation. No theorem generator re-run.
Preregistered as auxiliary diagnostic in Q3AB Issue #235 after first FAIL.
"""
import argparse,hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path
import z3

HERE=Path(__file__).resolve().parent
ROOT_CODE=HERE.parent/"q3z-polynomial-20261018"/"first_polynomial_original.py"
BLOB="869271c35fad857ebd7889291bfe1c74e0ca59fc"
ORIGINALS=["benchmarks/LIA/others/gcnr_tacas08.sl",
           "benchmarks/LIA/others/inria-00615623_4.sl"]

def q3z_pinned():
    b=subprocess.run(["git","hash-object",str(ROOT_CODE)],
        capture_output=True,text=True,check=True,timeout=8).stdout.strip()
    if b!=BLOB:raise RuntimeError("FROZEN_ORIGINAL_PARSER_CHANGED")
    spec=importlib.util.spec_from_file_location("frozen_q3ac_q3z",str(ROOT_CODE))
    a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a
    spec.loader.exec_module(a)
    return a

def sat_status(q,timeout=8000):
    s=z3.Solver();s.set(timeout=timeout);s.add(q)
    r=str(s.check());return r,s

def analyze(root,filename,q3z):
    source_file=root/filename
    raw=source_file.read_bytes()
    forms=q3z.core.sexprs(raw)
    src=q3z.core.extract_mixed_original(forms)
    native=q3z.core.native_original_relations(forms,src)
    parity={}
    for key in ("pre","trans","post"):
        status,_=sat_status(z3.Xor(src[key],native[key]))
        parity[key]=status
    if any(v!="unsat" for v in parity.values()):
        raise RuntimeError("AUTHENTIC_ORIGINAL_NATIVE_FORMULA_PARITY_NOT_UNSAT")
    now=src["now"];nxt=src["next"]
    if len(nxt)!=len(now) or len(nxt)>16:
        raise RuntimeError("INVALID_OR_TOO_LARGE_STATE_ARITY")
    independently_next=[
        z3.Const("q3ac_second_successor_"+str(i),v.sort()) for i,v in enumerate(nxt)]
    independent_second=z3.substitute(native["trans"],*list(zip(nxt,independently_next)))
    different=z3.Or(*(a!=b for a,b in zip(nxt,independently_next)))
    transition_twice=z3.And(native["trans"],independent_second,different)
    t=time.perf_counter()
    status,solver=sat_status(transition_twice,8000)
    row={"original_path":filename,
      "original_sha256":hashlib.sha256(raw).hexdigest(),
      "original_git_blob":q3z.core.blobhash(raw),
      "original_source_parity":parity,
      "now_state_arity":len(now),"now_int_count":src["num_int"],
      "now_bool_count":src["num_bool"],
      "same_source_two_distinct_successors_formula":"T(s,s1) AND T(s,s2) AND s1!=s2",
      "original_is_nonfunctional":status=="sat",
      "two_successor_query_status":status,
      "z3_wall_s":round(time.perf_counter()-t,6),
      "inductive_safety_proven":False,
      "this_diagnostic_changes_first_q3ab_score":False}
    if status=="sat":
        m=solver.model()
        row["witness"]={"old":[str(m.eval(v,model_completion=True)) for v in now],
                        "next_one":[str(m.eval(v,model_completion=True)) for v in nxt],
                        "next_two":[str(m.eval(v,model_completion=True)) for v in independently_next]}
        if row["witness"]["next_one"]==row["witness"]["next_two"]:
            raise RuntimeError("FALSE_NONFUNCTIONAL_WITNESS")
    elif status=="unknown":
        row["reason_unknown"]=solver.reason_unknown()[:120]
    return row

def main(root,out):
    t0=time.perf_counter()
    receipt={"study":"Q3AC_SOURCE_OPENED_TWO_SUCCESSOR_SEMANTIC_DIAGNOSTIC",
      "status":"Q3AC_FIRST_NOT_COMPLETE",
      "preregistered_after_q3ab_fail_comment":"https://github.com/yoonsj0305/NEUMANN/issues/235#issuecomment-6251090226",
      "source_git":"6ac90265b11431c9477dfbd33e3e3380234c0499",
      "first_q3ab_result":"FAIL / 0 OF 2 ORIGIN GROUPS",
      "no_new_original_safety_proof":True,
      "Q3_GLOBAL":"OPEN","Q1_Q7_GLOBAL":"OPEN",
      "originals":[]}
    def save():
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    save()
    try:
        q3z=q3z_pinned()
        for path in ORIGINALS:
            receipt["originals"].append(analyze(root,path,q3z));save()
        receipt["nonfunctional_originals_count"]=sum(x["original_is_nonfunctional"] for x in receipt["originals"])
        receipt["status"]="Q3AC_OPENED_SOURCE_TRANSITION_FUNCTIONALITY_AUDIT_COMPLETE"
        receipt["wall_s"]=round(time.perf_counter()-t0,6)
        save()
        print("Q3AC_AUTHENTIC_SOURCE_NONFUNCTIONAL_TRANSITION_AUDIT",json.dumps({
          "count":len(receipt["originals"]),
          "nonfunctional":receipt["nonfunctional_originals_count"],
          "statuses":{x["original_path"]:x["two_successor_query_status"] for x in receipt["originals"]}},sort_keys=True),flush=True)
    except Exception as exc:
        receipt["status"]="Q3AC_FIRST_SEMANTIC_AUDIT_FAILURE"
        receipt["error"]=type(exc).__name__+":"+str(exc)[:300]
        save();raise

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();main(a.root,a.out)
