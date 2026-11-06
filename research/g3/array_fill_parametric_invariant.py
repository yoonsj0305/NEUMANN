"""One-rule executable structural transfer for CHC array-store initialization.

From ONE source family, infer a stage-indexed prefix/suffix array invariant
without reading expected verdicts or heldout source. A universal inductive
proof over EVERY untouched original Horn implication is mandatory.

This is a HUMAN-DESIGNED deterministic rule, not a trained Q3 model.
Never equate the generated invariant with a successful theorem until a
fresh SMT instance proves UNSAT of negated source implication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"docs/experiments/G3_ARRAY_FILL_ONE_RULE_UNSEEN_N5_N8_N9_FIRST_PREREG_2026_11_06.json"
COMMIT="ddd279cab0717db6effe69baad451a8eb04ffd86"
REPO="chc-comp/chc-comp25-benchmarks"
FOLDER="quic3/data"

KNOWN_SOURCE={
 "standard_init4_true-unreach-call_ground_000.smt2":"174d192924d11f0863bbb28466613b72f825a962",
 "standard_init6_true-unreach-call_ground_000.smt2":"c00fbed8d20b3b724fb71fb6aebd9c8b443fad13",
 "standard_init7_true-unreach-call_ground_000.smt2":"b603b46cb0b6e9e9c6ae9cb2af6615c8e3a5813c",
}

def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def blob(x:bytes)->str:return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def top_forms(source:str)->list[str]:
    out=[];depth=0;begin=None;quote=False;comment=False;i=0
    while i<len(source):
        c=source[i]
        if comment:
            if c in "\r\n":comment=False
            i+=1;continue
        if quote:
            if c=="|":quote=False
            i+=1;continue
        if c==';':comment=True
        elif c=='|':quote=True
        elif c=='(':
            if depth==0:begin=i
            depth+=1
        elif c==')':
            depth-=1
            if depth<0:raise ValueError("UNBALANCED_ORIGINAL_CHC")
            if depth==0:
                out.append(source[begin:i+1])
                begin=None
        i+=1
    if depth or quote:raise ValueError("UNTERMINATED_SOURCE")
    return out

def source_role_info(source:str)->dict:
    forms=top_forms(source)
    predicates=[]
    declarations=[]
    for form in forms:
        m=re.fullmatch(r"\(\s*declare-fun\s+\|main@bb(\d+)\.i\|\s+\(\s*(.*?)\s*\)\s+Bool\s*\)",form,re.S)
        if m:
            sorts=re.findall(r"\(Array\s+Int\s+Int\)|Int|Bool",m.group(2))
            if len(sorts)!=4 or sorts.count("(Array Int Int)")!=1 or sorts.count("Int")!=3:
                raise ValueError("INCOMPATIBLE_LOOP_PREDICATE_TYPED_INTERFACE")
            predicates.append((int(m.group(1)),form,sorts))
        elif re.match(r"^\(\s*declare-fun",form):
            declarations.append(form)
    predicates.sort(key=lambda p:p[0])
    writes=[int(s) for s in re.findall(
        r"\(\s*store\s+[A-Za-z0-9_!]+\s+[A-Za-z0-9_!]+\s+(\d+)\s*\)",source)]
    if not writes or len(writes)<2 or len(writes)>20:
        raise ValueError("SOURCE_IS_NOT_MULTI_PHASE_CONSTANT_STORE")
    if writes!=list(range(writes[0],writes[0]+len(writes))):
        raise ValueError("SOURCE_HAS_INTERLEAVED_OR_REPEATED_STORE_CONSTANTS")
    if len(predicates)!=len(writes)+1:
        raise ValueError("WRITTEN_PHASE_COUNT_NOT_EQUAL_TO_LOOP_PREDICATES_MINUS_ONE")
    # Qualifier: all intermediate original CHC loop predicates have four
    # arguments with Array[Int,Int] at slot 2. Last is verification read
    # cursor and Array appears at slot 1. This is an observed interface
    # structure, not a source-file-name switch.
    for i,(n,decl,sorts) in enumerate(predicates):
        expected=2 if i<len(writes) else 1
        if sorts.index("(Array Int Int)")!=expected:
            raise ValueError("INCOMPATIBLE_ARRAY_POSITION")
    rest=[p for p in declarations if p not in {x[1] for x in predicates}]
    if not any(re.search(r"\|\s*main@entry\s*\|",x) for x in rest):
        raise ValueError("SOURCE_NO_ENTRY_PREDICATE")
    if not any(re.search(r"\|\s*main@verifier\.error\.split\s*\|",x) for x in rest):
        raise ValueError("SOURCE_NO_UNSAFE_PREDICATE")
    orig_asserts=[f for f in forms if re.match(r"^\(\s*assert\s+",f)]
    if len(orig_asserts)<len(writes)+3:
        raise ValueError("SOURCE_ASSERTIONS_INCOMPLETE")
    return {"source_forms":forms,"predicates":predicates,"values":writes,
       "num_stages":len(writes),"n_source_assertions":len(orig_asserts)}

def template(stage:int,values:list[int],arrslot:int,name:str)->str:
    # Construct position from *typed source signature*, no target-specific
    # hand-coded variable assignments.
    par=[("n","Int"),("i","Int"),("arr","(Array Int Int)"),("limit","Int")]
    if arrslot==1:
        par=[par[0],par[2],par[1],par[3]]
    elif arrslot!=2:raise ValueError("INVALID_ARRAY_SLOT")
    conditions=["(> n 0)","(> limit 0)","(<= 0 i)","(<= i limit)"]
    def q_range(lo:str,hi:str,v:int):
        return ("(forall ((j Int)) (=> (and (<= "+lo+" j) (< j "+hi+")) "
           "(= (select arr (+ n j)) "+str(v)+")))")
    if stage==len(values):
        conditions.append(q_range("0","limit",values[-1]))
    else:
        conditions.append(q_range("0","i",values[stage]))
        if stage>0:
            conditions.append(q_range("i","limit",values[stage-1]))
    return ("(define-fun |"+name+"| ("+
        " ".join("("+p+" "+s+")" for p,s in par)+
        ") Bool (and "+" ".join(conditions)+"))")

def solution_from_original(source:str,stage_mutant:int|None=None)->dict:
    x=source_role_info(source)
    stages=x["predicates"]
    values=list(x["values"])
    definitions={}
    for stage,(n,declare,sorts) in enumerate(stages):
        vv=list(values)
        if stage_mutant==stage and stage<len(values):
            # Deliberately corrupt exactly one learned-family stage value.
            vv[stage]+=17
        rel="main@bb"+str(n)+".i"
        definitions[declare]=template(stage,vv,sorts.index("(Array Int Int)"),rel)
    forms=x["source_forms"]
    for form in forms:
        if re.fullmatch(r"\(\s*declare-fun\s+\|main@verifier\.error\.split\|\s+\(\s*\)\s+Bool\s*\)",form):
            definitions[form]="(define-fun |main@verifier.error.split| () Bool false)"
        if re.fullmatch(r"\(\s*declare-fun\s+\|main@entry\|\s+\(\s*Int\s*\)\s+Bool\s*\)",form):
            definitions[form]="(define-fun |main@entry| ((n Int)) Bool true)"
        if re.fullmatch(r"\(\s*declare-fun\s+\|main@entry\|\s+\(\s*\)\s+Bool\s*\)",form):
            definitions[form]="(define-fun |main@entry| () Bool true)"
    for form in forms:
        if form.startswith("(declare-fun") and form not in definitions:
            raise ValueError("UNSUPPORTED_UNINTERPRETED_RELATION_"+form[:75])
    if len(definitions)!=len(stages)+2:
        raise ValueError("UNSUPPORTED_ENTRY_OR_ERROR_SYMBOL")
    declarations=[definitions[f] for f in forms if f in definitions]
    requirements=[f for f in forms if re.match(r"^\(\s*assert\s+",f)]
    # All original assertions remain untouched. Each assertion is turned
    # into an independent refutation obligation. Asking SAT of the original
    # CHC system would be insufficient to prove the guessed invariant.
    return {
      "prefix":"(set-logic ALL)\n"+"\n".join(declarations)+"\n",
      "source_assertions":requirements,
      "predicates":[{"name":"main@bb"+str(z[0])+".i",
           "array_index":z[2].index("(Array Int Int)")}
           for z in stages],
      "num_stages":len(values),
      "store_constants":values,
      "generated_interpretations":declarations,
      "original_clause_count":len(requirements),
    }

def prove_each(solution:dict,budget_per_clause_s:float=12)->dict:
    outcomes=[]
    for idx,assertion in enumerate(solution["source_assertions"]):
        # assert form is "(assert <phi>)"; original clauses unchanged.
        if not assertion.startswith("(assert") or not assertion.endswith(")"):
            raise ValueError("NOT_ORIGINAL_ASSERT")
        phi=assertion[len("(assert"):-1].strip()
        script=solution["prefix"]+"(assert (not "+phi+"))\n(check-sat)\n"
        with tempfile.NamedTemporaryFile("w",suffix=".smt2",encoding="utf8") as f:
            f.write(script);f.flush()
            start=time.perf_counter_ns()
            try:
                p=subprocess.run(["z3","-smt2","-T:"+str(int(budget_per_clause_s)),f.name],
                    capture_output=True,text=True,timeout=budget_per_clause_s+2)
                result=[v.strip() for v in p.stdout.splitlines() if v.strip()]
                verdict=("UNSAT_PROVED" if p.returncode==0 and result==["unsat"]
                   else "SAT_COUNTEREXAMPLE" if p.returncode==0 and result==["sat"]
                   else "UNKNOWN_OR_CHECKER_ERROR")
                detail={"status":verdict,"stdout_head":result[:3],
                   "solver_exit":p.returncode,"stderr_tail":p.stderr[-200:]}
            except subprocess.TimeoutExpired:
                detail={"status":"TIMEOUT_NOT_PROOF"}
            detail.update({"original_clause_index":idx,
                "independent_obligation_SHA256":sha(script.encode()),
                "wall_ms":round((time.perf_counter_ns()-start)/1e6,3)})
        outcomes.append(detail)
        if detail["status"]!="UNSAT_PROVED":
            # Fail closed at first non-proven original clause. No favorable
            # skipping or later interpretation as a proof.
            break
    return {"all_original_clauses_proven":len(outcomes)==solution["original_clause_count"] and
                all(o["status"]=="UNSAT_PROVED" for o in outcomes),
        "total_original_clauses":solution["original_clause_count"],
        "original_clauses_examined":len(outcomes),
        "original_clauses_independently_proven":sum(o["status"]=="UNSAT_PROVED" for o in outcomes),
        "first_nonproof":next((o for o in outcomes if o["status"]!="UNSAT_PROVED"),None),
        "clause_checks":outcomes}

def source(name:str,expected:str)->bytes:
    url="https://raw.githubusercontent.com/"+REPO+"/"+COMMIT+"/"+FOLDER+"/"+name
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G3-structural-array-invariant"}),timeout=45) as r:
        raw=r.read(25000)
    if blob(raw)!=expected:
        raise ValueError("PINNED_ORIGINAL_ARRAY_SOURCE_BLOB_DRIFT_"+name)
    return raw

def run_one(name:str,expected_blob:str,mode:str,budget:float)->dict:
    raw=source(name,expected_blob)
    orig=raw.decode("utf8")
    start=time.perf_counter_ns()
    model=solution_from_original(orig)
    proof=prove_each(model,budget)
    return {"source":name,"original_git_blob":expected_blob,
        "mode":mode,"source_sha256":sha(raw),
        "num_store_stages":model["num_stages"],
        "detected_values":model["store_constants"],
        "typed_relations":model["predicates"],
        "generated_reusable_relation_source_sha256":sha("\n".join(model["generated_interpretations"]).encode()),
        "source_model_not_trained":True,
        "independent_original_all_chc_proof":proof,
        "total_wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
        "certified_original":proof["all_original_clauses_proven"],
        "Q3_autonomous_learned_discovery":"NOT_PROVEN"}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["DEVELOPMENT","SOURCE_FREE_SYNTHETIC","UNSEEN_FIRST"],required=True)
    ap.add_argument("--per-clause-cap",type=int,default=12)
    args=ap.parse_args()
    if args.per_clause_cap<1 or args.per_clause_cap>30:raise ValueError("OUT_OF_REGISTERED_CHECKER_BUDGET")
    if args.mode=="SOURCE_FREE_SYNTHETIC":
        good=solution_from_original("""(set-logic HORN)
(declare-fun |main@entry| (Int) Bool)
(declare-fun |main@bb9.i| (Int Int (Array Int Int) Int) Bool)
(declare-fun |main@bb19.i| (Int Int (Array Int Int) Int) Bool)
(declare-fun |main@bb29.i| (Int (Array Int Int) Int Int) Bool)
(declare-fun |main@verifier.error.split| () Bool)
(assert (forall ((n Int) (i Int) (a (Array Int Int)) (l Int)) (=> (and (main@bb9.i n i a l) (< i l) (= a (store a i 42))) (main@bb9.i n i a l))))
(assert (forall ((n Int) (i Int) (a (Array Int Int)) (l Int)) (=> (and (main@bb19.i n i a l) (< i l) (= a (store a i 43))) (main@bb19.i n i a l))))
(assert (=> main@verifier.error.split false))
(check-sat)
""")
        assert good["num_stages"]==2
        print(json.dumps({"sourcefree_parser_and_typed_rule_pass":True,
            "detected_stages":good["num_stages"],
            "number_generated":len(good["generated_interpretations"])},sort_keys=True))
        return 0
    if args.mode=="DEVELOPMENT":
        files=[(name,hash) for name,hash in KNOWN_SOURCE.items()]
    else:
        manifest=json.loads(MANIFEST.read_text())
        targets=manifest["unopened_heldout_transfer"]["selected_file_metadata_before_body"]
        if len(targets)!=3 or not manifest["unopened_heldout_transfer"]["source_body_unopened_before_this_manifest"]:
            raise ValueError("UNSEEN_FIRST_PREREG_BROKEN")
        files=[(t["file"],t["git_blob"]) for t in targets]
    result={
      "schema":"neumann.g3.array-init-parametric-typed-invariant-inductive-all-clauses.v1",
      "mode":args.mode,
      "science_claim":"REUSABLE_DETERMINISTIC_HUMAN_DERIVED_RULE_NOT_NEURAL_Q3",
      "original_transfer_blind_claim":args.mode=="UNSEEN_FIRST",
      "no_learned_policy":True,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "cases":[]
    }
    for name,expected in files:
        try:
            outcome=run_one(name,expected,args.mode,float(args.per_clause_cap))
        except Exception as e:
            outcome={"source":name,"original_git_blob":expected,"certified_original":False,
                     "status":"INFRA_OR_PATTERN_FAIL_CLOSED",
                     "error":type(e).__name__+":"+str(e)[:250]}
        result["cases"].append(outcome)
    result["stats"]={
       "original_denominator":len(result["cases"]),
       "independent_full_original_clause_proofs":sum(x["certified_original"] for x in result["cases"]),
       "infrastructure_or_pattern_error":sum(x.get("status")=="INFRA_OR_PATTERN_FAIL_CLOSED" for x in result["cases"]),
       "new_ARC_public_eval_IDs_consumed":0,
       "neural_model_trained":False
    }
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"scientific_status":"SOURCE_INVARIANT_GENERATOR_FATAL_FAIL_CLOSED",
            "error":type(e).__name__+":"+str(e)[:250]}))
        raise SystemExit(2)
