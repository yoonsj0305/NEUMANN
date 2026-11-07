"""Q3: automatically INVENT a named reusable function from discovered programs.

This is library learning, NOT another hand-added ARC primitive or model ranker:
1. Read TWO executable solved-program ASTs emitted by a previous separate Q3
   source-only induction run, without a provided abstraction or target program.
2. Compute their least-general generalization structurally, introducing
   fresh typed holes exactly where the observed executable definitions differ.
3. Name and freeze that new higher-order library function BEFORE target-task
   training data or heldout gold is opened.
4. Bind the NEW function's formal parameters from another original task's
   TRAIN examples only, compile and execute it on its TEST input, ABSTAIN on
   unspecified/ambiguous colors.
5. Check that the frozen library function really carries over different
   source layouts, operand orderings, numbers of panels and learned laws.

The meta-abstraction algorithm is classical (appropriate when cheaper).
Its primitives and operator family are not self-discovered from nothing.
Proving scoped library invention/reuse does NOT prove a frontier-trained NN
invented a new fundamental type system. It does supply executable evidence
of autonomous function *definition and reuse*, rather than a static macro.

All original IDs here are PROJECT-OPENED development problems; true Q3
global, Q4 and Q6 stay OPEN. No new reserved EVAL ids are consumed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from research.q3.induce_binary_algebra_original import (
    Decomposition, InventedJoin, enumerate_decompositions,
    subgrids, closure_relations, predict_single, grid_ok,
)

SOURCE_IDS=("281123b4","6a11f6da")
FROZEN_REUSE_TARGET="cf98881b"
FROZEN_PARENT_FIRST_RUN=42331791321
FROZEN_PARENT_ARTIFACT_SHA256="6c9616b9f70e33675c0b4e7835bfecd5ad4c4e64030fda76d979379fe04488a3"
SCHEMA="neumann.q3.learn-and-reuse-program-library-from-original-source-asts.v1"


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,
                   separators=(",",":")).encode()).hexdigest()


def full_program_ast(source_row):
    """Reify prior independently invented executable operator into a term.

    A generic program AST, not a program ID, a trained output lookup, or a
    generated answer taken from the transfer target. No target lookup table.
    """
    programs=source_row["model"]["programs"]
    if len(programs)!=1:raise ValueError("SOURCE_PROGRAM_AMBIGUOUS")
    item=programs[0]
    d=item["decomposition"]
    return ["MapZipFold",["DivideIntoPanels",
                          d["axis"],d["panel"],d["gutter"],d["count"]],
            item["learned_binary_operator_AST"]]


class AntiUnifier:
    """Generic structure-only most-specific abstraction of two arbitrary ASTs.

    It has NO knowledge of ARC operators, colors, joins, paths or originals.
    Fresh parameters are invented by recursively unifying two syntax trees,
    with higher-level mismatched subexpressions becoming whole holes.
    """
    def __init__(self):
        self.holes=[]
        self.correspondence={}
    def unify(self,left:Any,right:Any):
        if left==right:
            return left
        if isinstance(left,list) and isinstance(right,list) \
           and len(left)==len(right):
            return [self.unify(a,b) for a,b in zip(left,right)]
        if isinstance(left,dict) and isinstance(right,dict) \
           and set(left)==set(right):
            return {k:self.unify(left[k],right[k]) for k in sorted(left)}
        key=(json.dumps(left,sort_keys=True),json.dumps(right,sort_keys=True))
        if key in self.correspondence:
            return {"$param":self.correspondence[key]}
        label="p"+str(len(self.holes))
        self.correspondence[key]=label
        self.holes.append(label)
        return {"$param":label}


def bind_pattern(pattern,term,values=None):
    """Structural type-safe fit; never return guessed values for missing holes."""
    if values is None:values={}
    if isinstance(pattern,dict) and list(pattern)==["$param"]:
        key=pattern["$param"]
        if key in values and values[key]!=term:return None
        values[key]=term
        return values
    if type(pattern)!=type(term):return None
    if isinstance(pattern,list):
        if len(pattern)!=len(term):return None
        for a,b in zip(pattern,term):
            if bind_pattern(a,b,values) is None:return None
        return values
    if isinstance(pattern,dict):
        if set(pattern)!=set(term):return None
        for key in pattern:
            if bind_pattern(pattern[key],term[key],values) is None:return None
        return values
    return values if pattern==term else None


def substitute(pattern,bindings):
    if isinstance(pattern,dict) and list(pattern)==["$param"]:
        return bindings[pattern["$param"]]
    if isinstance(pattern,list):
        return [substitute(v,bindings) for v in pattern]
    if isinstance(pattern,dict):
        return {k:substitute(v,bindings) for k,v in pattern.items()}
    return pattern


def compile_as_executable(program_ast):
    """Strict compiler for the learned higher-order MapZipFold operator.

    Any program with unresolved holes, unsupported node or cyclic color
    relations must fail closed. Execution never examines original test gold.
    """
    if not isinstance(program_ast,list) or len(program_ast)!=3 \
       or program_ast[0]!="MapZipFold":
        raise ValueError("NOT_COMPILED_REUSABLE_OPERATOR")
    split,joinast=program_ast[1:]
    if not (isinstance(split,list) and len(split)==5
            and split[0]=="DivideIntoPanels"):
        raise ValueError("BAD_SPLIT_OPERATOR")
    d=Decomposition(split[1],split[2],split[3],split[4])
    if d.axis not in ("columns","rows") \
       or type(d.panel)!=int or type(d.gutter)!=int or type(d.count)!=int:
        raise ValueError("BAD_SPLIT_TYPES")
    if not(isinstance(joinast,list) and len(joinast)==4
           and joinast[0]=="DefineOperator"
           and joinast[2][0]=="lambda"):
        raise ValueError("BAD_INVENTED_LAMBDA")
    rule=joinast[2][2]
    if rule[0]!="ChooseUniqueMaxUnder" \
       or rule[1][0]!="Identity" or rule[2][0]!="LearnedStrictOrder":
        raise ValueError("UNSUPPORTED_INVENTED_BINARY_OPERATOR")
    identity=rule[1][1]
    edges=tuple((int(a),int(b)) for a,b in rule[2][1])
    colors=tuple(sorted({identity}|{v for edge in edges for v in edge}))
    learned=InventedJoin(identity,edges,colors)
    if not learned.all_laws_hold():
        raise ValueError("LEARNED_LAW_VIOLATES_CONTRACT")
    def function(input_grid):
        if not grid_ok(input_grid):return None
        return predict_single(learned,d,input_grid)
    return function


@dataclass(frozen=True)
class LearnedLibrary:
    name:str
    body:Any
    parameters:tuple[str,...]
    training_source_hashes:tuple[str,...]

    def to_ast(self):
        return ["DefineReusableOperator",self.name,
                ["lambda",[{"name":p,"type":"StructuralTerm"} for p in self.parameters],
                 self.body]]
    def to_data(self):
        return {"name":self.name,"function_ast":self.to_ast(),
                "parameters":list(self.parameters),
                "source_program_hashes":list(self.training_source_hashes),
                "library_sha256":digest(self.to_ast())}


def invent_library_from_programs(a,b):
    anti=AntiUnifier()
    body=anti.unify(a,b)
    left=bind_pattern(body,a)
    right=bind_pattern(body,b)
    if left is None or right is None or not anti.holes:
        raise RuntimeError("NO_MEANINGFUL_REUSABLE_ABSTRACTION")
    if substitute(body,left)!=a or substitute(body,right)!=b:
        raise RuntimeError("ABSTRACTION_CANNOT_RECONSTRUCT_SOURCES")
    # Only the repeated executable structure is factored; the algorithm
    # cannot get novelty by replacing the entire program with one hole.
    if isinstance(body,dict) and "$param" in body:
        raise RuntimeError("TRIVIAL_WHOLE_PROGRAM_ABSTRACTION")
    h=digest(["semantic_program_abstraction",body])[:16]
    name="invented_library_"+h
    return LearnedLibrary(name,body,tuple(anti.holes),
          (digest(a),digest(b))),left,right


def semantic_interface_of_frozen_library(lib):
    """Extract only what the *previously learned library function* permits.

    The entire target inference is driven by the frozen program structure.
    No previous full-task program synthesis solver is called; no new target
    function template can be created on the fly. Unknown library syntax must
    return an empty admissible hypothesis space, not a favorable fallback.
    """
    body=lib.body
    try:
        if body[0]!="MapZipFold" or body[1][0]!="DivideIntoPanels":
            return None
        op=body[2]
        if op[0]!="DefineOperator" or op[2][0]!="lambda":
            return None
        rule=op[2][2]
        if rule[0]!="ChooseUniqueMaxUnder" or rule[1][0]!="Identity" \
           or rule[2][0]!="LearnedStrictOrder":
            return None
        # The two original source ASTs agreed about the identity. It stays
        # a frozen literal, never secretly re-learned by a direct solver.
        identity=rule[1][1]
        hole=rule[2][1]
        if type(identity) is not int or not (
            isinstance(hole,dict) and set(hole)=={"$param"} and
            hole["$param"] in lib.parameters):
            return None
        if rule[3]!=["Vars","a","b"] or rule[4]!=["Unknown","ABSTAIN"]:
            return None
        return identity
    except (IndexError,KeyError,TypeError,AttributeError):
        return None


def infer_binary_law_parameters_from_observations(train,decomposition,identity):
    """Infer the UNKNOWN slot of a frozen invented operator from I/O equations.

    This is NOT the old direct program synthesis path. A code interpreter
    already told us via the reusable function that its free slot is a
    strict ordering on same-cell operands. Training examples now constrain
    only that slot's pairwise relation, never the function's operator kind,
    workflow topology, identity or control flow.
    """
    edges=set()
    used={identity}
    competitive_observations=0
    source_constraints=0
    for row in train:
        panels=subgrids(row["input"],decomposition)
        target=row["output"]
        if panels is None:return None
        h=len(target);w=len(target[0])
        if any(len(panel)!=h or len(panel[0])!=w for panel in panels):
            return None
        for y in range(h):
            for x in range(w):
                inputs={p[y][x] for p in panels if p[y][x]!=identity}
                observed=target[y][x]
                used.update(inputs)
                if not inputs:
                    if observed!=identity:return None
                    continue
                if observed not in inputs:return None
                if len(inputs)>1:competitive_observations+=1
                for loser in inputs-{observed}:
                    edges.add((loser,observed))
                    source_constraints+=1
    # No trivial one-equation relabeling is called a new law.
    if competitive_observations<2 or source_constraints<3 or \
       len(edges)<2 or len(used)<4:
        return None
    try:
        closure_relations(used,edges)
    except Exception:
        return None
    op=InventedJoin(identity,tuple(sorted(edges)),tuple(sorted(used)))
    if not op.all_laws_hold():return None
    return op


def infer_bindings_using_only_target_train(lib,target_train):
    """Instantiate *only* the frozen new library's typed holes.

    In particular, DO NOT call the original source program resolver:
    it could solve the target independently, falsely making library reuse
    appear causally necessary. This procedure cannot synthesize anything
    unless a specific frozen reusable library describes the semantics.
    """
    identity=semantic_interface_of_frozen_library(lib)
    if identity is None:return []
    candidates=[]
    for decomposition in enumerate_decompositions(target_train):
        learned_relation=infer_binary_law_parameters_from_observations(
            target_train,decomposition,identity)
        if learned_relation is None:continue
        candidate_ast=["MapZipFold",
             ["DivideIntoPanels",
              decomposition.axis,decomposition.panel,
              decomposition.gutter,decomposition.count],
             learned_relation.to_ast()]
        binding=bind_pattern(lib.body,candidate_ast)
        if binding is None or set(binding)!=set(lib.parameters):
            continue  # The new frozen library actually constrains programs.
        if substitute(lib.body,binding)!=candidate_ast:
            raise RuntimeError("PARAMETER_BINDING_INVALID")
        function=compile_as_executable(candidate_ast)
        if not all(function(row["input"])==row["output"]
                   for row in target_train):
            raise RuntimeError("FALSE_PROGRAM_TRAIN_FIT")
        candidates.append((binding,candidate_ast,function))
    found={}
    for vals,ast,fn in candidates:
        found[digest(ast)]=(vals,ast,fn)
    return list(found.values())


def ablate_learned_parameter(lib,parameter,source_binding):
    """Restore one formerly constant source-site and remove its learned hole.

    Any loss of capacity on the same target TRAIN is a scoped causal
    witness that source-program abstraction, not just direct memorization,
    enabled this particular kind of reuse.
    """
    if parameter not in lib.parameters:raise ValueError("UNKNOWN_LEARNED_HOLE")
    def fixed(term):
        if isinstance(term,dict) and set(term)=={"$param"}:
            if term["$param"]==parameter:return source_binding
            return term
        if isinstance(term,list):return [fixed(x) for x in term]
        if isinstance(term,dict):return {k:fixed(v) for k,v in term.items()}
        return term
    new_body=fixed(lib.body)
    return LearnedLibrary("ABLATION_"+lib.name,new_body,
                tuple(p for p in lib.parameters if p!=parameter),
                lib.training_source_hashes)


def transfer_to_new_original(lib,target,task_id):
    """Frozen library first. Only then load unseen target TRAIN observations."""
    candidates=infer_bindings_using_only_target_train(lib,target["train"])
    if not candidates:
        return {"target":task_id,"status":"ABSTAIN_NO_LIBRARY_INSTANCE",
                "train_fit":False,"test_exact":False}
    # All train-consistent library instances must predict the SAME test
    # input; any ambiguity abstains without inspecting test output.
    predicted=[]
    for case in target["test"]:
        outputs=[fn(case["input"]) for _,_,fn in candidates]
        if any(out is None for out in outputs) or \
           any(out!=outputs[0] for out in outputs[1:]):
            return {"target":task_id,"status":"ABSTAIN_AMBIGUOUS_LIBRARY_INSTANCE",
                    "number_programs":len(candidates),
                    "train_fit":True,"test_exact":False}
        predicted.append(outputs[0])
    success=all(pred==case["output"]
                for pred,case in zip(predicted,target["test"]))
    return {"target":task_id,"status":"REUSED_COMPILED_FUNCTION",
            "library_name":lib.name,"library_sha256":digest(lib.to_ast()),
            "number_programs":len(candidates),
            "generated_ast_hashes":[digest(ast) for vals,ast,fn in candidates],
            "parameter_bindings":[vals for vals,ast,fn in candidates],
            "train_fit":True,"test_exact":success,
            "test_count":len(target["test"]),
            "test_pred_hashes":[digest(pred) for pred in predicted]}


def run(first:Path,arc_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_AUTONOMOUS_LIBRARY_FIRST")
    parent=json.loads(first.read_text())
    if parent["schema"]!="neumann.q3.induced-binary-algebra-from-external-originals.v1":
        raise ValueError("UNTRUSTED_PARENT_ORIGINAL_SOURCE")
    if parent["groups"]["official_public_TRAIN_400"]["original_tasks"]!=400 \
       or parent["groups"]["previously_opened_eval_P25_32"]["original_tasks"]!=32:
        raise ValueError("PARENT_COHORT_DRIFT")
    by_id={p["original_id"]:p for p in parent["rows"]}
    if FROZEN_REUSE_TARGET in SOURCE_IDS:
        raise ValueError("TARGET_LEAKED_INTO_LIBRARY_SOURCES")
    sources=[by_id[x] for x in SOURCE_IDS]
    if not all(s["original_TEST_exact"] for s in sources):
        raise ValueError("SOURCE_ORIGINAL_PROGRAM_NOT_PROVEN")
    source_asts=[full_program_ast(s) for s in sources]
    lib, bind_a,bind_b=invent_library_from_programs(*source_asts)
    frozen_library_sha=digest(lib.to_ast())
    # Source code+program abstraction FROZEN NOW. Neither the input nor the
    # output of the transfer task is used for operator invention.
    out.mkdir(parents=True)
    (out/"FROZEN_INVENTED_LIBRARY.json").write_text(
            json.dumps(lib.to_data(),indent=2,sort_keys=True)+"\n")
    # Reuse program on the original from *different source cohort*. This
    # original is held out from schema invention, but previously project opened.
    file=arc_root/"data"/"training"/(FROZEN_REUSE_TARGET+".json")
    if not file.is_file():
        raise ValueError("FROZEN_TRANSFER_SOURCE_MISSING")
    task=json.loads(file.read_text())
    result=transfer_to_new_original(lib,task,FROZEN_REUSE_TARGET)
    # No full direct-program solver is used. Remove each abstraction slot in
    # turn and test whether the formerly frozen source parameter can still
    # explain the target TRAIN. This identifies which invention was useful.
    ablations={}
    for slot in lib.parameters:
        constrained=ablate_learned_parameter(lib,slot,bind_a[slot])
        surviving=infer_bindings_using_only_target_train(
            constrained,task["train"])
        ablations[slot]={
          "source_literal_forced":bind_a[slot],
          "target_train_programs_without_slot":len(surviving),
          "target_train_reuse_requires_this_slot":len(surviving)==0
        }
    if frozen_library_sha!=digest(lib.to_ast()):
        raise RuntimeError("LIBRARY_MUTATED_AFTER_TARGET_EXPOSURE")
    report={
      "schema":"neumann.q3.learned-named-reusable-library-first.v1",
      "frozen_external_parent_run":FROZEN_PARENT_FIRST_RUN,
      "source_program_ids":list(SOURCE_IDS),
      "target_heldout_only_from_library_induction":FROZEN_REUSE_TARGET,
      "source_programs_correct_in_prior_originals":True,
      "source_program_ast_sha256":list(lib.training_source_hashes),
      "generated_new_library_definition":lib.to_data(),
      "full_library_frozen_before_target_training":True,
      "symbolic_antiunification_used":True,
      "human_defined_primitive_semantic_vocabulary":True,
      "target_program_source_seen_during_library_training":False,
      "learned_library_covers_axis_and_layout_count_variation":(
        len(lib.parameters)>=4),
      "source_a_full_reconstruction":substitute(lib.body,bind_a)==source_asts[0],
      "source_b_full_reconstruction":substitute(lib.body,bind_b)==source_asts[1],
      "original_target":result,
      "automatic_parameter_ablation_causal_results":ablations,
      "learned_slots_necessary_for_target":sum(
          v["target_train_reuse_requires_this_slot"] for v in ablations.values()),
      "old_full_task_resolver_reused_for_target":False,
      "no_globally_new_public_eval_ids_consumed":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
    }
    (out/"FIRST_REPORT.json").write_text(
             json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items()
                      if k not in ("generated_new_library_definition",)},
                     indent=2,sort_keys=True))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent-first",type=Path,required=True)
    p.add_argument("--arc-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    run(a.parent_first,a.arc_root,a.out)
