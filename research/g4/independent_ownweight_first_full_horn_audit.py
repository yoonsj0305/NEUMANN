"""G4 READONLY independent 10 synthetic own-weight first proof recheck.

Original FIRST model weights, exact 10 source split and predicted AST bytes
are SHA-pinned; this script NEVER imports the G4 learned policy, does NOT
retrain or rerun any model, and does not use the first bespoke array proof
engine. Instead it independently constructs a full original Horn clause
program for each synthetic source and applies the separate generic SMT
CHC witness checker to every generated invariant, proving ALL untouched
Horn clauses by UNSAT of each negation.

No CHC-COMP external original (including frozen reserved eight) is read.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from research.g4.generic_chc_independent_proof import independent_verify_original_chc_sat

FIRST_SHA="0b3f898e7f36cea5ae8011de74af57e3058322795a5ceb35c0aa37c16af5dbf2"
WEIGHTS_SHA="16bb17ba5715e60acad6bd1d672212bcc33342ff159afdd9aa65a8ee3d464d7a"
ARRS=("A","B","C")
KINDS=("FILL","COPY","ADD")
def sha(x:bytes):return hashlib.sha256(x).hexdigest()
def numeric(x:int)->str:
    return str(x) if x>=0 else "(- "+str(-x)+")"
def rhs(kind:str,src:str|None,constant:int,index:str)->str:
    if kind=="FILL":return numeric(constant)
    expression="(select "+src+" "+index+")"
    return expression if kind=="COPY" else "(+ "+expression+" "+numeric(constant)+")"

def make_original_source(kind:str,dst:str,src:str|None,constant:int)->str:
    if kind not in KINDS or dst not in ARRS:
        raise ValueError("NOT_REGISTERED_ORIGINAL_SYNTHETIC_CLASS")
    if kind!="FILL" and (src not in ARRS or src==dst):
        raise ValueError("WRONG_ORIGINAL_TYPED_SOURCE")
    rel="(declare-fun Inv (Int Int (Array Int Int) (Array Int Int) (Array Int Int)) Bool)"
    arrs=" ".join("( "+n+" (Array Int Int))" for n in ARRS)
    next_arrs=" ".join("( "+n+"2 (Array Int Int))" for n in ARRS)
    before=" ".join(ARRS)
    after=" ".join(n+"2" for n in ARRS)
    def call(i,n,registers):
        return "(Inv "+i+" "+n+" "+registers+")"
    init="(assert (forall ((n Int) "+arrs+") (=> (>= n 0) "+call("0","n",before)+")))"
    conditions=["(and",call("i","n",before),"(<= 0 i)","(< i n)"]
    for name in ARRS:
        value=("(store "+name+" i "+rhs(kind,src,constant,"i")+")"
               if name==dst else name)
        conditions.append("(= "+name+"2 "+value+")")
    conditions.append(")")
    trans="(assert (forall ((i Int) (n Int) "+arrs+" "+next_arrs+") "
    trans+="(=> "+" ".join(conditions)+" "+call("(+ i 1)","n",after)+")))"
    wanted="(= (select "+dst+" k) "+rhs(kind,src,constant,"k")+")"
    post="(forall ((k Int)) (=> (and (<= 0 k) (< k n)) "+wanted+"))"
    safe="(assert (forall ((i Int) (n Int) "+arrs+") "
    safe+="(=> (and "+call("i","n",before)+" (= i n)) "+post+")))"
    return "(set-logic HORN)\n"+rel+"\n"+init+"\n"+trans+"\n"+safe+"\n(check-sat)\n"

def independent_candidate(raw:list|None,constant:int):
    if not isinstance(raw,list) or len(raw)!=3:
        return None
    kind,dst,src=raw
    if kind not in KINDS or dst not in ARRS or (kind!="FILL" and src not in ARRS):
        return None
    term=rhs(kind,src,constant,"k")
    relation="(= (select "+dst+" k) "+term+")"
    formula="(and (>= n 0) (<= 0 i) (<= i n) "
    formula+="(forall ((k Int)) (=> (and (<= 0 k) (< k i)) "+relation+")))"
    return {"Inv":{"params":["i","n","A","B","C"],"body":formula}}

def audit(p:Path):
    data=p.read_bytes()
    if sha(data)!=FIRST_SHA:
        raise ValueError("G4_ORIGINAL_WEIGHT_FIRST_RECEIPT_CHANGED")
    first=json.loads(data)
    if first["model_weights_sha256"]!=WEIGHTS_SHA or first["total_synthetic_heldout_programs"]!=10:
        raise ValueError("G4_FIRST_PROGRAM_COUNT_OR_WEIGHT_HASH_DRIFT")
    if first["metrics"]["external_original_reserved_2025_array8_consumed"]!=0:
        raise ValueError("RESERVED_CHC_ORIGINAL_LEAK")
    result=[]
    for row in first["rows"]:
        kind,dst,src=row["source_class"]
        const=row["constant_pass_through_int"]
        original=make_original_source(kind,dst,src,const)
        candidate=independent_candidate(row["ownweight_output_roles"],const)
        if candidate is None:
            verified={"verified":False,"status":"ILL_TYPED_GENERATED_RELATION"}
        else:
            verified=independent_verify_original_chc_sat(original,candidate,3500)
        first_claim=row["ownweight_source_proof"]["verified"]
        if verified["verified"]!=first_claim:
            raise ValueError("INDEPENDENT_HORN_ORIGINAL_DISAGREES_WITH_FIRST_PROOF")
        # Mutation false is not an alternate syntactic solution: an always
        # false Inv cannot satisfy any nonempty original initial condition.
        wrong={"Inv":{"params":["i","n","A","B","C"],"body":"false"}}
        invalid=independent_verify_original_chc_sat(original,wrong,3500)
        if invalid["verified"]:
            raise ValueError("FALSE_INVARIANT_MUTATION_ACCEPTED")
        result.append({"original_synthetic_source_SHA256":sha(original.encode()),
          "first_generated_AST":row["ownweight_output_roles"],
          "original_training_tuple_held_out":row["heldout_unseen_whole_AST"],
          "original_model_output_claim":first_claim,
          "new_independent_full_HORN_3assertion_proof":verified,
          "mutation_explicit_false_rejected":not invalid["verified"],
          "model_or_training_reexecuted":False})
    certified=sum(r["new_independent_full_HORN_3assertion_proof"]["verified"] for r in result)
    return {
      "schema":"neumann.q3.g4.synthetic-FIRST-compositional-ownweight-full-HORN-independent-audit.v1",
      "original_first_SHA256":FIRST_SHA,
      "frozen_actual_train_weights_SHA256":WEIGHTS_SHA,
      "audit_pass":len(result)==10 and certified==10,
      "independent_original_HORN_clause_proven":certified,
      "synthetic_heldout_programs":len(result),
      "false_mutation_rejected":sum(r["mutation_explicit_false_rejected"] for r in result),
      "model_weights_retrained":False,
      "model_predictions_rerun":False,
      "original_generic_verifier_is_different_from_first_array_proof":True,
      "external_G3_unopened_array8_originals_accessed":0,
      "strong_classical_first_was_10_of_10":True,
      "NEUMANN_learned_exclusive_over_classical":0,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "original_cases":result
    }
if __name__=="__main__":
    try:
        result=audit(Path(sys.argv[1]))
        print(json.dumps(result,indent=2,sort_keys=True))
        if not result["audit_pass"]:raise SystemExit(1)
    except Exception as e:
        print("G4_INDEPENDENT_FULL_HORN_FIRST_AUDIT_FAIL_CLOSED",repr(e),file=sys.stderr)
        raise SystemExit(2)
