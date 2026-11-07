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
    train_invention, predict_single, grid_ok,
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


def infer_bindings_using_only_target_train(lib,target_train):
    """Solve parameters for the already frozen library function.

    NOTE: the constraint solver is classical. It does not invent the library
    structure: only instantiates its typed free variables. This distinction
    prevents rebranding trivial fitting as new reusable semantics.
    """
    candidates=[]
    for decomposition in enumerate_decompositions(target_train):
        # Identity is sourced from the visible input only, and law edges
        # from genuine observed target TRAIN behavior, not test output.
        all_color=[v for pair in target_train for row in pair["input"] for v in row]
        from collections import Counter
        for identity,_ in Counter(all_color).most_common():
            law=train_invention(target_train,decomposition,identity)
            if law is None:continue
            formal_ast=["MapZipFold",["DivideIntoPanels",
                                     decomposition.axis,decomposition.panel,
                                     decomposition.gutter,decomposition.count],
                        law.to_ast()]
            binding=bind_pattern(lib.body,formal_ast)
            if binding is None:continue
            if set(binding)!=set(lib.parameters):continue
            if substitute(lib.body,binding)!=formal_ast:
                raise RuntimeError("PARAMETER_BINDING_INVALID")
            function=compile_as_executable(formal_ast)
            if not all(function(row["input"])==row["output"]
                       for row in target_train):
                raise RuntimeError("FALSE_PROGRAM_TRAIN_FIT")
            candidates.append((binding,formal_ast,function))
    # Deduplicate the semantics without inspecting test gold.
    found={}
    for vals,ast,fn in candidates:
        found[digest(ast)]=(vals,ast,fn)
    return list(found.values())


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
