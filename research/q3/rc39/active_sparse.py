"""NEUMANN RC39 | Active source-only sparse causal opcode discovery.

A human provided the HOST GRAMMAR (one conjunction of relative exact symbol
reads). The learner does not receive hidden offsets, target colors, target
syntax labels, reference formulas or an independent grader. It DOES receive
one genuine positive witness and black-box membership queries. This is
CLASSICAL active group testing, NOT autonomous new foundational ISA creation.

Execution is fail-closed under budget, malformed input, source contradiction.
"""
from __future__ import annotations
from dataclasses import dataclass
from time import process_time_ns
from typing import Callable

ALPHABET="ABC"
SCHEMA="neumann.q3.rc39.sparse-causal-program.v1"
SOURCE_RIGHTS="POSITIVE_WITNESS_PLUS_ACTIVE_MEMBERSHIP_QUERIES"
class BudgetExceeded(Exception):pass

def validate_word(w):
    return type(w) is str and 3<=len(w)<=4097 and all(c in ALPHABET for c in w)

def perturb(witness: str, offsets, center: int):
    if not validate_word(witness) or not isinstance(center,int) or not 0<=center<len(witness):
        raise ValueError("BAD_WITNESS_OR_CENTER")
    letters=list(witness)
    for offset in offsets:
        if type(offset) is not int or offset==0 or not 0<=center+offset<len(letters):
            raise ValueError("INVALID_RELATIVE_OFFSET")
        i=center+offset
        letters[i]=ALPHABET[(ALPHABET.index(letters[i])+1)%len(ALPHABET)]
    return "".join(letters)

def run_program(ast,word,center):
    """Pure source language, missing relative positions cannot satisfy a test."""
    if not validate_word(word) or type(center) is not int or not 0<=center<len(word):
        return None
    if (type(ast) is not dict or ast.get("schema")!=SCHEMA or
        ast.get("kind")!="RELATIVE_EXACT_CONJUNCTION"): 
        return None
    reads=ast.get("reads")
    if type(reads) not in (list,tuple) or len(reads)>2048:
        return None
    seen=set()
    for item in reads:
        if type(item) not in (list,tuple) or len(item)!=2:
            return None
        offset,char=item
        if type(offset) is not int or offset==0 or offset in seen or char not in ALPHABET:
            return None
        seen.add(offset)
        j=center+offset
        if j<0 or j>=len(word) or word[j]!=char:
            return word[center]
    return "A" if word[center]=="B" else word[center]

@dataclass
class OracleMeter:
    oracle: Callable[[str,int],str]
    max_calls:int
    calls:int=0
    def ask(self,word,center):
        if self.calls>=self.max_calls:raise BudgetExceeded
        self.calls+=1
        answer=self.oracle(word,center)
        if answer not in ALPHABET or type(answer) is not str:raise ValueError("MALFORMED_ORACLE_ANSWER")
        return answer

def discover(witness,center,oracle,*,max_queries=256,source_rights=SOURCE_RIGHTS):
    """Infer only missing position/symbol pairs via recursive group intervention.

    Assumption: a positive witness is provided. Under exactly the known sparse
    conjunction grammar, a group intervention preserves positivity iff no
    required coordinate was modified. Thus a binary recursion reveals every
    causal dependency without a task-specific gold opcode or reference label.
    """
    started=process_time_ns()
    calls=OracleMeter(oracle,max_queries)
    def abstain(reason):
        return {"schema":"neumann.q3.rc39.discovery-receipt.v1",
            "status":"ABSTAIN","reason":reason,"oracle_calls":calls.calls,
            "cpu_us":(process_time_ns()-started)/1000,
            "input_rights":source_rights,"neural_model_calls":0}
    if (source_rights!=SOURCE_RIGHTS or not validate_word(witness) or
        type(center) is not int or not 0<=center<len(witness) or witness[center]!="B"):
        return abstain("INVALID_POSITIVE_SOURCE")
    if max_queries<0 or max_queries>5000:return abstain("INVALID_QUERY_BUDGET")
    try:
        if calls.ask(witness,center)!="A":return abstain("NOT_AN_ACTUAL_POSITIVE")
        positions=tuple(i-center for i in range(len(witness)) if i!=center)
        found=[]
        def traverse(subset):
            if not subset:return
            result=calls.ask(perturb(witness,subset,center),center)
            if result=="A":return
            if result!="B":raise ValueError("NOT_SPARSE_EXACT_CONJUNCTION")
            if len(subset)==1:
                found.append(subset[0])
                return
            mid=len(subset)//2
            traverse(subset[:mid])
            traverse(subset[mid:])
        traverse(positions)
        found.sort()
        ast={"schema":SCHEMA,"kind":"RELATIVE_EXACT_CONJUNCTION",
             "reads":[[d,witness[center+d]] for d in found]}
        # Additional deterministic source-consistency perturbations, not a
        # proof for ANY arbitrary oracle. The declared grammar is essential.
        required=set(found)
        checks=[positions,tuple(d for d in positions if d not in required),tuple(found)]
        # Target adversarial XOR/OR behavior close to center without retuning.
        for d in [*range(-5,0),*range(1,6)]:
            if d in positions:checks.append((d,))
        for subset in checks:
            probe=perturb(witness,subset,center)
            if run_program(ast,probe,center)!=calls.ask(probe,center):
                return abstain("INCONSISTENT_WITH_DECLARED_CAUSAL_GRAMMAR")
        return {"schema":"neumann.q3.rc39.discovery-receipt.v1",
            "status":"SOURCE_CONSISTENT_EXECUTABLE","program":ast,
            "oracle_calls":calls.calls,"cpu_us":(process_time_ns()-started)/1000,
            "candidate_offsets":len(positions),"found_offsets":len(found),
            "input_rights":source_rights,"neural_model_calls":0,
            "runtime_all_domain_proof":"CONDITIONAL_ON_INDEPENDENT_AUTHOR_MAPPING_EQUALITY"}
    except BudgetExceeded:
        return abstain("QUERY_BUDGET_EXHAUSTED")
    except Exception as exc:
        return abstain("SOURCE_OR_ORACLE_CONTRACT_ERROR:"+type(exc).__name__)

def classical_single_site(witness,center,oracle):
    """Exactly same member-query rights, no hidden mapping, no trained model."""
    started=process_time_ns()
    meter=OracleMeter(oracle,5000)
    if not validate_word(witness) or witness[center]!="B" or meter.ask(witness,center)!="A":
        return {"status":"ABSTAIN","oracle_calls":meter.calls}
    pairs=[]
    for i in range(len(witness)):
        if i==center:continue
        offset=i-center
        answer=meter.ask(perturb(witness,(offset,),center),center)
        if answer=="B":pairs.append([offset,witness[i]])
        elif answer!="A":return {"status":"ABSTAIN","oracle_calls":meter.calls}
    return {"status":"SOURCE_CONSISTENT_EXECUTABLE",
        "program":{"schema":SCHEMA,"kind":"RELATIVE_EXACT_CONJUNCTION","reads":pairs},
        "oracle_calls":meter.calls,"cpu_us":(process_time_ns()-started)/1000,
        "input_rights":SOURCE_RIGHTS,"neural_model_calls":0}
