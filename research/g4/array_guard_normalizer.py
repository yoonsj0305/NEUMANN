"""G4 original array CHC: ONE reusable semantics-preserving guard canonicalizer.

This uses an established local Z3 formula simplifier, NOT a learned policy,
and must never be credited as autonomous Q3. All original G3 expert timeouts
remain immutable. The key experiment is whether simple non-model preprocessing
changes solvability of the complete ORIGINAL CHC property across one
frozen primary source and two previously frozen transfer sources.
"""
from __future__ import annotations

import argparse,hashlib,json,re,sys,time
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/"docs/experiments/G4_ONE_ARRAY_FRAME_OPERATOR_POSTFIRST_SOURCE_SELECTION_2026_11_06.json"
CON=ROOT/"docs/experiments/G4_ONE_ARRAY_GUARD_CANONICALIZER_SOURCE_FREE_FIRST_2026_11_06.json"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

SYNTHETIC=b"""(set-logic HORN)
(declare-fun Inv (Int) Bool)
(assert (forall ((x Int)) (=> (= x 0) (Inv x))))
(assert (forall ((x Int) (y Int)) (=> (and (Inv x) (= y (+ x 1))) (Inv y))))
(assert (forall ((x Int)) (=> (and (Inv x) (< x 0)) false)))
(check-sat)
"""

def collect_uninterpreted_predicates(ast):
    import z3
    found=set()
    stack=[ast]
    while stack:
        expr=stack.pop()
        if z3.is_quantifier(expr):
            stack.append(expr.body())
        elif z3.is_app(expr):
            if expr.decl().kind()==z3.Z3_OP_UNINTERPRETED:
                found.add((str(expr.decl().name()),expr.num_args(),str(expr.sort())))
            stack.extend(expr.children())
    return found

def canonicalize(data:bytes)->dict:
    import z3
    begin=time.perf_counter_ns()
    original=z3.SolverFor("HORN")
    original.from_string(data.decode("utf8"))
    before=list(original.assertions())
    if not before:
        raise ValueError("ORIGINAL_HORN_SOURCE_HAS_NO_ASSERTIONS")
    original_signatures=set()
    for x in before:
        original_signatures|=collect_uninterpreted_predicates(x)
    # Only Z3's local Boolean and select/store algebraic simplifier.
    # No hand-injected predicate, guessed invariant, or new source formula.
    reduced=[z3.simplify(x,elim_and=True,pull_cheap_ite=True) for x in before]
    after_signatures=set()
    for x in reduced:
        after_signatures|=collect_uninterpreted_predicates(x)
    # A logically valid simplifier may eliminate dead uninterpreted symbols,
    # but must not introduce ANY new predicate kinds or arities.
    if after_signatures-original_signatures:
        raise ValueError("CANONICALIZER_ADDED_UNKNOWN_PREDICATES")
    if len(reduced)!=len(before):
        raise ValueError("CANONICALIZER_DROPPED_HORN_CONSTRAINT")
    solver=z3.SolverFor("HORN")
    solver.add(*reduced)
    output=solver.to_smt2()
    if "(set-logic HORN)" not in output:
        output="(set-logic HORN)\n"+output
    output_bytes=output.encode("utf8")
    # Syntactic validity of transformed benchmark, no original query here.
    reread=z3.SolverFor("HORN")
    reread.from_string(output)
    if len(reread.assertions())!=len(before):
        raise ValueError("NORMALIZED_ORIGINAL_ASSERTION_LOSS")
    normalization_ms=round((time.perf_counter_ns()-begin)/1e6,3)
    return {
      "normalization":"z3.simplify local source formulas only",
      "original_raw_sha256":sha(data),
      "normalized_sha256":sha(output_bytes),
      "original_bytes":len(data),
      "normalized_bytes":len(output_bytes),
      "original_assertions":len(before),
      "normalized_assertions":len(reread.assertions()),
      "original_uninterpreted_signatures":len(original_signatures),
      "normalized_uninterpreted_signatures":len(after_signatures),
      "no_new_predicate_signatures":True,
      "native_Z3_version":z3.get_version_string(),
      "normalization_wall_ms":normalization_ms,
      "normalized_source":output
    }

def solve_transformed(source:str,cap_ms:int=15000)->dict:
    import z3
    solver=z3.SolverFor("HORN")
    solver.set(timeout=cap_ms)
    solver.from_string(source)
    begin=time.perf_counter_ns()
    answer=solver.check()
    elapsed=round((time.perf_counter_ns()-begin)/1e6,3)
    result=str(answer)
    reason=None
    if result=="unknown":
        try: reason=solver.reason_unknown()
        except Exception:reason="UNKNOWN_REASON"
    return {"outcome":result if result in ("sat","unsat","unknown") else "NO_GROUNDED",
      "solver_wall_ms":elapsed,
      "reason_unknown":reason,
      "verified_original_CHC_semantics":False,
      "independent_original_witness_available":False}

def controls():
    good=canonicalize(SYNTHETIC)
    bad=canonicalize(SYNTHETIC.replace(b"(< x 0)",b"(> x 0)"))
    sg=solve_transformed(good["normalized_source"],6000)
    sb=solve_transformed(bad["normalized_source"],6000)
    return {"schema":"neumann.g4.array-guard-sourcefree-safe-unsafe.v1",
       "control_safe":sg,"control_unsafe":sb,
       "pass":sg["outcome"]=="sat" and sb["outcome"]=="unsat" and
             good["no_new_predicate_signatures"] and bad["no_new_predicate_signatures"],
       "original_benchmark_bytes_read":0,
       "normalization_ms":[good["normalization_wall_ms"],bad["normalization_wall_ms"]]}

def original3():
    doc=json.loads(PRE.read_text())
    c=json.loads(CON.read_text())
    if c["unchanged_target3"]!=[
       "array_swap_000.smt2","array_swap_twice_000.smt2",
       "standard_copy2_true-unreach-call_ground_000.smt2"]:
        raise ValueError("G4_SOURCE_TRANSFER_TARGETS_CHANGED")
    targets=[doc["pre_source_inspection_selection"]["main"]]+doc["pre_source_inspection_selection"]["transfer_without_rewrite"]
    if [x["name"] for x in targets]!=c["unchanged_target3"]:
        raise ValueError("G4_PRE_COMMITTED_SOURCE_ORDER_CHANGED")
    results=[]
    for target in targets:
        url="https://raw.githubusercontent.com/chc-comp/chc-comp25-benchmarks/ddd279cab0717db6effe69baad451a8eb04ffd86/"+target["folder"]+"/"+target["name"]
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G4-SINGLE-ARRAY-EFFECT-STRUCTURE"}),timeout=40) as r:
            data=r.read(25000)
        if gitblob(data)!=target["git_blob"]:
            raise ValueError("G4_EXTERNAL_SOURCE_GIT_BLOB_CHANGED_"+target["name"])
        row={"name":target["name"],"original_git_blob":target["git_blob"],
          "postfirst_original_not_blind":True}
        try:
            norm=canonicalize(data)
            src=norm.pop("normalized_source")
            row["canonicalization"]=norm
            row["native"]=solve_transformed(src,15000)
            row["status"]=(
              "PROVISIONAL_NATIVE_CLAIM_REQUIRES_ORIGINAL_SOURCE_PROOF"
              if row["native"]["outcome"] in ("sat","unsat")
              else "CANONICALIZATION_DID_NOT_CLOSE_ORIGINAL_WITHIN_BUDGET"
            )
        except Exception as ex:
            row["status"]="CANONICALIZATION_INFRASTRUCTURE_FAIL"
            row["error"]=type(ex).__name__+":"+str(ex)[:350]
        results.append(row)
    counts={
     "original_exact":len(results),
     "new_transformed_grounded_native_claims":sum(x["status"]=="PROVISIONAL_NATIVE_CLAIM_REQUIRES_ORIGINAL_SOURCE_PROOF" for x in results),
     "unchanged_hard_originals_with_no_verified_solution":sum(x["status"]!="PROVISIONAL_NATIVE_CLAIM_REQUIRES_ORIGINAL_SOURCE_PROOF" for x in results),
     "independently_verified_originals_solved":0,
     "student_trained_weights":False,
     "ARC_eval_used":0
    }
    return {"schema":"neumann.g4.one-array-guard-canonicalizer-three-frozen-originals.v1",
      "scientific_status":"CANONICALIZATION_ONLY_NO_LEARNED_NEW_SEMANTICS",
      "original_3_already_opened_by_G3_first":True,
      "operator_source_freeze_before_transfer":True,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "stats":counts,"rows":results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--synthetic",action="store_true")
    p.add_argument("--original3",action="store_true")
    args=p.parse_args()
    if args.synthetic:
        x=controls()
        print(json.dumps(x,indent=2,sort_keys=True))
        return 0 if x["pass"] else 1
    if args.original3:
        print(json.dumps(original3(),indent=2,sort_keys=True))
        return 0
    raise ValueError("MISSING_ONE_FROZEN_MECHANISM_EXPERIMENT_MODE")

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as ex:
        print(json.dumps({"status":"G4_SOURCE_COMPILER_INFRA_FAILURE_NOT_Q3",
          "exception":type(ex).__name__,"message":str(ex)[:250]}))
        raise SystemExit(2)
