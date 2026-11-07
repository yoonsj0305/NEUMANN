"""Q3 second-order role transfer: REUSE prior generated index mapping unchanged.

Instead of manually coding a new vector-mirror algorithm, this compiler
instantiates a PREVIOUSLY DISCOVERED coordinate relation AST across an
arbitrary pair of input roles. Generic source-I/O constraints pick which
roles, comparison and quantifier are correct. No source task-name,
reference code or source domain label is provided.

The first original 29-family GP-Suite task corpus was already accessed by
#718, so this is explicitly POST-FIRST DEVELOPMENT, not a pristine
independent heldout/general Q3 PASS.

HUMAN CODED: typed two-input interface, index-role binder grammar, simple
Boolean reductions, base VM, source-validity and search ordering.
MACHINE-DERIVED: source prior affine expression, target input roles,
new executable AST and its application to independent author originals.
"""
from __future__ import annotations
from hashlib import sha256
import json,time
from research.q3.discover_index_relation_constructor import (
    affine_value,coeffs,generated_coordinates
)
from research.q3.connected_constructor_router import (
    canon,validate_memory,program_id,result_equal
)

SCHEMA="neumann.q3.generic-index-relation-argument-role-generalization.v1"

def run_role_program(prog,args):
    if prog is None or not isinstance(prog,dict) or len(args)!=2:
        return None
    if prog.get("kind")!="DefineRoleAbstraction":
        return None
    try:
        l=prog["left_argument_role"];r=prog["right_argument_role"]
        left=args[l];right=args[r]
        if type(left) not in (list,tuple,str) or \
           type(right) not in (list,tuple,str):
            return None
        if len(left)>1024 or len(right)>1024:return None
        if prog["length_guard"]=="equal" and len(left)!=len(right):
            return False
        if prog["length_guard"]!="equal":return None
        n=len(left)
        index=prog["learned_coordinate_expression"]
        op=prog["value_relation"];reduce=prog["quantifier"]
        observations=[]
        for i in range(n):
            j=affine_value(index,i,n)
            if not isinstance(j,int) or not 0<=j<len(right):
                return None
            match=left[i]==right[j]
            if op=="neq":match=not match
            elif op!="eq":return None
            observations.append(match)
        if reduce=="all":return all(observations)
        if reduce=="any":return any(observations)
    except (ValueError,TypeError,IndexError,KeyError,OverflowError):
        return None
    return None

def acceptable(train):
    if len(train)<6:return False
    signatures=set()
    output_kinds=set()
    for args,y in train:
        if len(args)!=2 or type(y) is not bool:return False
        if any(type(v) not in (list,tuple,str) or len(v)>1024 for v in args):
            return False
        signatures.add((type(args[0]),type(args[1])))
        output_kinds.add(y)
    return len(signatures)==1 and output_kinds=={True,False}

def construct(index,left,right,comp,quant,origin):
    ast={
        "kind":"DefineRoleAbstraction",
        "left_argument_role":left,
        "right_argument_role":right,
        "learned_coordinate_expression":index,
        "length_guard":"equal",
        "value_relation":comp,
        "quantifier":quant,
        "coordinate_provenance":origin,
        "human_supplied_generic_role_VM":True,
    }
    ast["symbol"]="invented_arg_relation_"+program_id(ast)[:18]
    return ast

def structural_programs(coordinates,origin):
    for expr in coordinates:
        # Prioritize comparing two different input roles, but this is a
        # generic fixed search policy and not target-specific semantics.
        for left,right in ((0,1),(1,0),(0,0),(1,1)):
            for op in ("eq","neq"):
                for quant in ("all","any"):
                    yield construct(expr,left,right,op,quant,origin)

def train_matches(prog,train):
    return all(run_role_program(prog,args) is y for args,y in train)

def search(train,*,prior_program=None,budget=1000):
    begin=time.perf_counter_ns();trials=0
    if not acceptable(train):
        return {"status":"ABSTAIN_TYPE_OR_INSUFFICIENT_EVIDENCE",
                "attempts":0,"program":None,
                "ms":round((time.perf_counter_ns()-begin)/1e6,4)}
    if prior_program is not None:
        if not validate_memory(prior_program):
            raise ValueError("PRIOR_MEMORY_PROOF_INVALID")
        frozen_index=prior_program["representation_constructor"]["second_index"]
        for program in structural_programs([frozen_index],"VERIFIED_PREVIOUS_OPERATOR"):
            trials+=1
            if train_matches(program,train):
                return {"status":"TRANSFERRED_NEW_INPUT_ROLE_BINDING",
                        "attempts":trials,"program":program,
                        "learned_affine_coefficients":coeffs(frozen_index),
                        "ms":round((time.perf_counter_ns()-begin)/1e6,4)}
            if trials>=budget:
                return {"status":"ABSTAIN_BUDGET","attempts":trials,
                        "program":None}
    # SAME universal index/value VM in cold arm, but not prioritized
    # by any old memory AST. Count all cold hypothesis evaluations.
    for program in structural_programs(
            generated_coordinates(),"GENERIC_COLD_COORDINATE_GRAMMAR"):
        trials+=1
        if train_matches(program,train):
            return {"status":"COLD_INVENTED_COORDINATE_RELATION",
                    "attempts":trials,"program":program,
                    "learned_affine_coefficients":coeffs(
                        program["learned_coordinate_expression"]),
                    "ms":round((time.perf_counter_ns()-begin)/1e6,4)}
        if trials>=budget:
            return {"status":"ABSTAIN_BUDGET","attempts":trials,
                    "program":None,
                    "ms":round((time.perf_counter_ns()-begin)/1e6,4)}
    return {"status":"ABSTAIN_NO_RELATIONAL_HYPOTHESIS",
            "attempts":trials,"program":None,
            "ms":round((time.perf_counter_ns()-begin)/1e6,4)}

def score(program,heldout):
    matches=[program is not None and
             run_role_program(program,args) is y
             for args,y in heldout]
    return {"exact":all(matches),"correct":sum(matches),
            "tested":len(matches)}
