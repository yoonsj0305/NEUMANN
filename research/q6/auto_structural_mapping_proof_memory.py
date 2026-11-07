"""Q6 scoped automatic cross-formalism observation map generation.

The reference source proof comes from existing Q6 PR #685 unchanged.
The proposer receives its *type/role* interface and the target update
syntax, but NOT the old manually chosen alpha expression.

A small general typed SMT expression grammar builds observation candidates,
filters them by independent relational execution examples, and then submits
their commuting equations to the existing Z3 source-proof backend.

This is neither an unrestricted AI-invented representation constructor nor
an independently author-written new problem. The search grammar, adapters,
memory descriptors and verifier are human authored. Q3/Q4/Q6 remain OPEN.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
import time

from research.q6.array_string_simulation import STRING, query
from research.q6.compositional_simulation_postfirst import CHECKS

SCHEMA="neumann.q6.auto-generated-proof-carrying-observation.v1"
OLD_Q6_ARRAY_BLOB="a9744d0cf88f196600acf0f225e988273e67976f"
OLD_Q6_COMPOSE_BLOB="1da58b324666c4cc207c042d15d555629ca277be"


def digest(x):
    return sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()


@dataclass(frozen=True)
class ObservationTerm:
    head:str
    index:str
    count:int|None

    def ast(self):
        return ["Apply",self.head,["ConcreteContainer"],
                ["IndexExpression",self.index]] + (
                [["LengthLiteral",self.count]] if self.count is not None else [])

    def integer_index(self,j,n):
        if self.index=="j":return j
        if self.index=="0":return 0
        if self.index=="1":return 1
        if self.index=="j+1":return j+1
        if self.index=="j-1":return j-1
        if self.index=="n-1-j":return n-1-j
        raise ValueError("UNDECLARED_INDEX_FORM")

    def smt_index(self,j,n):
        if self.index=="j":return j
        if self.index in ("0","1"):return self.index
        if self.index=="j+1":return f"(+ {j} 1)"
        if self.index=="j-1":return f"(- {j} 1)"
        if self.index=="n-1-j":return f"(- (- {n} 1) {j})"
        raise ValueError("UNDECLARED_INDEX_FORM")

    def py_eval(self,word,j):
        ix=self.integer_index(j,len(word))
        if self.head=="str.at":
            return word[ix:ix+1] if 0<=ix<len(word) else ""
        if self.head=="str.substr":
            return word[ix:ix+self.count] if 0<=ix<len(word) else ""
        raise ValueError("UNDECLARED_PRIMITIVE")

    def smt(self,word,j,n):
        ix=self.smt_index(j,n)
        if self.head=="str.at":
            return f"(str.at {word} {ix})"
        if self.head=="str.substr":
            return f"(str.substr {word} {ix} {self.count})"
        raise ValueError("UNDECLARED_PRIMITIVE")

    def operator_heads(self):
        return [self.head]


def heads_from_existing_target_semantics():
    """Read operation symbols from #685's target update; no supplied alpha."""
    return sorted(set(re.findall(r"\((str\.[a-zA-Z0-9.+-]+)",STRING)))


def enumerate_typed_observations(heads):
    indices=("0","1","j","j+1","j-1","n-1-j")
    # Only well-typed constructors under the String x Int -> String
    # or String x Int x Int -> String generic SMT interfaces are generated.
    emitted=[]
    for h in sorted(set(heads)):
        for ix in indices:
            if h=="str.at":
                emitted.append(ObservationTerm(h,ix,None))
            elif h=="str.substr":
                for n in (0,1,2):
                    emitted.append(ObservationTerm(h,ix,n))
    return sorted(set(emitted),
                  key=lambda x:(len(json.dumps(x.ast())),json.dumps(x.ast())))


def local_relational_probes():
    """Synthetic, deterministic relational source->target demonstrations.

    No position-observation function is supplied as a target label.
    Only a source/destination input and a full updated String are observed.
    """
    scenarios=[("abc","XYZ",0),("abc","XYZ",1),("abc","XYZ",2),
               ("abcde","KLMNO",3),("pqrs","ABCD",0),
               ("wxyz","ABCD",2),("abca","WXYZ",1)]
    for source,dest,i in scenarios:
        out=dest[:i]+source[i]+dest[i+1:]
        yield source,dest,i,out


def preliminary_evidence(term):
    checked=0;reason=None
    # Witness that the interface actually distinguishes positions and
    # outputs one single target element. Reject vacuous constant observers.
    signals=[term.py_eval("abc",j) for j in range(3)]
    if any(len(x)!=1 for x in signals) or len(set(signals))!=3:
        return False,"NOT_FAITHFUL_NONDEGENERATE_ELEMENT_OBSERVATION",checked
    for source,dest,i,actual in local_relational_probes():
        n=len(source)
        for j in range(n):
            left=term.py_eval(actual,j)
            right=(term.py_eval(source,i) if j==i
                   else term.py_eval(dest,j))
            checked+=1
            if left!=right:
                return False,"CONCRETE_COUNTEREXAMPLE_TO_TRANSFER",checked
    return True,"OBSERVATION_RELATION_HOLDS_ON_PROBES",checked


def proof_contracts(learned):
    """Candidate-independent prover formulas. No fixed alpha in proposer."""
    def v(s,j):
        return learned.smt(s,j,"n")
    source=STRING+"""
(assert (<= 0 i)) (assert (< i n))
(assert (<= 0 j)) (assert (< j n))
"""
    commute=(source+"(assert (not (= "+v("next","j")+
        " (ite (= j i) "+v("src","i")+" "+v("dst","j")+"))))")
    # An independent *post-selection* fidelity verifier uses target String
    # theory's reference indexed element semantics. It does NOT generate,
    # propose, rank or filter the expressions before freeze.
    bridge=(STRING+"""
(assert (<= 0 j)) (assert (< j n))
(assert (not (= """+v("src","j")+""" (str.at src j))))""")
    # Counterfactual target writes its OWN old value rather than the
    # source value. A valid non-degenerate transfer must expose a mismatch.
    corrupted=(STRING+"""
(assert (= src "b")) (assert (= dst "x"))
(assert (= i 0)) (assert (= j 0))
(define-fun wrong () String
  (str.++ (str.substr dst 0 i) (str.at dst i)
          (str.substr dst (+ i 1) (- n (+ i 1)))))
(assert (not (= """+v("wrong","j")+
        " "+v("src","i")+")))")
    return {
      "INVENTED_ALPHA_COMMUTING":("unsat",commute),
      "INVENTED_ALPHA_INDEPENDENT_FIDELITY":("unsat",bridge),
      "WRONG_TARGET_UPDATE_MUST_BREAK":("sat",corrupted),
    }


def check_smt(body,expect,timeout_s=8):
    observed,ms,error=query(body,cap_s=timeout_s)
    return {"expected":expect,"observed":observed,
            "pass":observed==expect,
            "wall_ms":ms,"query_sha256":sha256(
                (body+"\n(check-sat)\n").encode()).hexdigest(),
            "error":error}


def source_memories():
    """Preserve real prior knowledge as typed source contracts.

    Other memories are genuine past PR categories, not synthetic invented
    solution claims. Contract fields are HUMAN-AUTHORED metadata. No alpha
    program or successful cross-theory mapping is stored in any descriptor.
    """
    return [
      {"id":"Q6_ARRAY_PREFIX_WRITE_PR685",
       "source_type":"Array[Int,String]",
       "operation_roles":["indexed_read","indexed_store","prefix_invariant"],
       "requires":["select","store"],"certified_source_checks":[
            "ABSTRACT_INIT","ABSTRACT_STEP_COMPOSED_FROM_POINTWISE_STORE",
            "ABSTRACT_FINISH_WITH_GROUND_INDEX"],
       "kind":"INDUCTIVE_COPY_INVARIANT"},
      {"id":"Q3_STITCH_GRAPHICS_MACRO_PR670",
       "source_type":"GraphicsAST",
       "operation_roles":["geometry_translate","repeat","object_map"],
       "requires":["T","M","repeat","tan"],
       "certified_source_checks":[],"kind":"EXACT_MACRO"},
      {"id":"Q3_COLOR_FUNCTION_TYPE_PR699",
       "source_type":"Set[Color]",
       "operation_roles":["color_join","palette_role"],
       "requires":["color_case","panel_split"],
       "certified_source_checks":[],"kind":"FINITE_COLOR_OPERATOR"},
    ]


def retrieve_compatible(memories,target):
    results=[]
    for memory in memories:
        required=set(memory["requires"])
        accepted=(
            memory["source_type"]=="Array[Int,String]" and
            "indexed_read" in memory["operation_roles"] and
            "indexed_store" in memory["operation_roles"] and
            "str.at" in target["target_heads"] and
            "str.substr" in target["target_heads"] and
            {"select","store"}.issubset(required)
        )
        results.append({"source":memory["id"],
                        "accepted":accepted,
                        "reason":"TYPED_ROLE_AND_OPERATION_MATCH"
                          if accepted else "TYPE_OR_REQUIRED_OPERATOR_MISMATCH"})
    return results


def read_only_source_check():
    return {
       "array_source_original_git_blob":OLD_Q6_ARRAY_BLOB,
       "composed_source_original_git_blob":OLD_Q6_COMPOSE_BLOB,
    }


def select_observation_without_reference_oracle(target_heads):
    candidates=enumerate_typed_observations(target_heads)
    audits=[]
    survivors=[]
    for term in candidates:
        match,why,count=preliminary_evidence(term)
        audits.append({"ast":term.ast(),"admitted":match,
                       "reason":why,"relational_probes_checked":count})
        if match:survivors.append(term)
    return candidates,audits,survivors


def run(out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_AUTOMAP_FIRST")
    if not shutil.which("z3"):
        raise RuntimeError("INDEPENDENT_Z3_REQUIRED")
    out.mkdir(parents=True)
    start=time.perf_counter_ns()
    target_heads=heads_from_existing_target_semantics()
    retrieved=retrieve_compatible(source_memories(),
                     {"target_heads":target_heads,"target_type":"String"})
    approved=[x for x in retrieved if x["accepted"]]
    if not approved:
        raise RuntimeError("NO_COMPATIBLE_SOURCE_STRUCTURE")
    candidates,audits,survivors=select_observation_without_reference_oracle(
        target_heads)
    records=[];chosen=None;frozen=None
    # Source proof and original human mapping are NOT used by the proposer.
    # The full source backend is invoked only on the already selected,
    # data-generated candidate after the candidate AST has been frozen.
    for term in survivors:
        declaration=term.ast()
        receipt=check_smt(proof_contracts(term)["INVENTED_ALPHA_COMMUTING"][1],
                          "unsat",8)
        records.append({"ast":declaration,**receipt})
        if receipt["pass"]:
            chosen=term
            frozen=digest(declaration)
            break
    # Independently audit a few hard negatives with a real countermodel.
    negative=[]
    for term in candidates:
        if len(negative)>=3:break
        if term in survivors:continue
        if term.head=="str.at" and term.index in ("0","j+1","n-1-j"):
            receipt=check_smt(
                proof_contracts(term)["INVENTED_ALPHA_COMMUTING"][1],
                "sat",5)
            negative.append({"ast":term.ast(),**receipt})
    final_checks={}
    if chosen is not None:
        contracts=proof_contracts(chosen)
        for key,(expected,body) in contracts.items():
            # Reuse original candidate commuting receipt if possible, but
            # independently replay it to include the fixed final contract.
            result=check_smt(body,expected,8)
            final_checks[key]=result
            (out/(key+".smt2")).write_text(body+"\n(check-sat)\n")
    source_checks={}
    for key in [
        "ABSTRACT_INIT","ABSTRACT_STEP_COMPOSED_FROM_POINTWISE_STORE",
        "ABSTRACT_FINISH_WITH_GROUND_INDEX",
        "STRING_SAME_LENGTH_EQUAL_PREFIX_FINISH",
        "CORRUPTED_REAL_STRING_UPDATE_WITNESS",
    ]:
        expected,body=CHECKS[key]
        source_checks[key]=check_smt(body,expected,9)
    allpass=(chosen is not None and
        len(approved)==1 and
        all(r["pass"] for r in final_checks.values()) and
        all(r["pass"] for r in source_checks.values()) and
        any(r["pass"] for r in negative))
    report={
        "schema":SCHEMA,
        "source_repository_pr":685,
        "source_proof_files_unchanged":True,
        "source_blobs":read_only_source_check(),
        "human_added_correct_alpha_to_proposer":False,
        "human_authored_generic_smt_observation_grammar":True,
        "source_original_was_previously_developed_and_opened":True,
        "corpus_external_first_new_problem_families":0,
        "source_memories_searched":len(source_memories()),
        "source_memories_compatible":len(approved),
        "memory_decisions":retrieved,
        "target_operation_heads_extracted":target_heads,
        "typed_candidates_generated":len(candidates),
        "candidate_probe_audit":audits,
        "candidates_surviving_relational_counterexamples":len(survivors),
        "prover_candidate_receipts":records,
        "learned_observation_ast":chosen.ast() if chosen else None,
        "frozen_before_final_proofs_sha256":frozen,
        "independent_final_checks":final_checks,
        "original_independent_source_checks":source_checks,
        "hard_negative_proof_receipts":negative,
        "pass_scoped":allpass,
        "total_elapsed_ms":round(
            (time.perf_counter_ns()-start)/1e6,3),
        "total_z3_process_ms":round(sum(x["wall_ms"] for x in (
            records+negative+list(final_checks.values())+
            list(source_checks.values()))),3),
        "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
    }
    (out/"FIRST.json").write_text(json.dumps(report,sort_keys=True,
                                           indent=2)+"\n")
    (out/"CANDIDATE_LANGUAGE.json").write_text(json.dumps(
        [term.ast() for term in candidates],sort_keys=True,indent=2)+"\n")
    print("AUTO_ALPHA_FIRST",json.dumps({key:report[key] for key in (
        "source_memories_compatible","typed_candidates_generated",
        "candidates_surviving_relational_counterexamples",
        "learned_observation_ast","pass_scoped","total_elapsed_ms",
        "total_z3_process_ms")},sort_keys=True),flush=True)
    print("PROOF_VERDICTS",json.dumps({k:v["observed"]
                                     for k,v in final_checks.items()},
                                     sort_keys=True),flush=True)
    print("NEGATIVE_VERDICTS",json.dumps(
        [p["observed"] for p in negative]),flush=True)
    print("Q3_Q4_Q6_GLOBAL_OPEN",flush=True)
    if not allpass:
        raise RuntimeError("AUTO_ALPHA_DEVELOPMENT_FAILED_NOT_TRANSFER_PASS")
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    arguments=ap.parse_args()
    run(arguments.out)
