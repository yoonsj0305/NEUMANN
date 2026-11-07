"""Q3: discover a previously absent operator *TYPE* and reuse it elsewhere.

Phase 1 (source only): Take two independently discovered, original-correct
nonconservative executable programs, not their problem names or target
outputs. Canonicalize each finite semantic function modulo arbitrary color
renaming. If and only if they are isomorphic, create a new content-addressed
reusable operator TYPE with a canonical symbol-role algebra. This is a
discovered definition, NOT hand-written task-specific input/color rules.

Phase 2 (target): After freezing that newly minted type, fit ONLY its palette
renaming and grid layout parameters using each different official original
TRAIN, compile and run the frozen canonical function on the original TEST.
Never run the original direct full semantic table inventor on target cases.

This is still classical program abstraction over a human-provided universal
finite-case language. It is an independently executable Q3 subgate, NOT a
proof that a trained neural network autonomously invents arbitrary semantics.
All external original tasks were previously project-opened. Q3 Global OPEN.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from research.q3.induce_binary_algebra_original import (
    PIN,EVAL32,grid_ok,enumerate_decompositions,subgrids,
)

SCHEMA="neumann.q3.new-semantic-type-isomorphism-reuse-original.v1"
PARENT_SCHEME="neumann.q3.failed-join-new-semantics-original.v1"
FROZEN_PARENT_RUN=42338077481
SOURCE_IDS=("94f9d214","f2829549")


def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,
                separators=(",",":")).encode()).hexdigest()


def find_one(ast,tag):
    """Find a typed AST node by syntax, never task-id-dependent code."""
    matches=[]
    def walk(obj):
        if isinstance(obj,list):
            if obj and obj[0]==tag:matches.append(obj)
            for x in obj:walk(x)
        elif isinstance(obj,dict):
            for x in obj.values():walk(x)
    walk(ast)
    if len(matches)!=1:raise ValueError("AMBIGUOUS_OR_MISSING_"+tag)
    return matches[0]


def source_semantic_contract(source_row):
    """Read only a real emitted executable AST, not target examples."""
    if not source_row["exact"] or source_row["status"]!=\
        "INVENTED_NONCONSERVATIVE_OPERATOR":
        raise ValueError("SOURCE_NOT_ORIGINAL_SOLVED")
    programs=source_row["frozen_operator_AST"]
    if len(programs)!=1:raise ValueError("AMBIGUOUS_SOURCE_OPERATOR")
    ast=programs[0]
    split=find_one(ast,"Split")
    case=find_one(ast,"Case")
    encoding=case[1]
    lam=find_one(ast,"Lambda")
    if encoding[:1]!=["EncodeArguments"] or encoding[2]!="args" \
       or case[3]!=["Abstain","UNKNOWN_SIGNATURE"]:
        raise ValueError("NONSTANDARD_OUTPUT_SEMANTICS")
    if len(lam)<4 or lam[2]!="Color":
        raise ValueError("BAD_LAMBDA_TYPE")
    arity=len(lam[1])
    if not 2<=arity<=9 or split[4]!=arity:
        raise ValueError("ARITY_MISMATCH")
    mode=encoding[1]
    clauses=case[2]
    signature_set=set()
    rows=[]
    for key,value in clauses:
        if any(not isinstance(a,int) for a in key) or not isinstance(value,int):
            raise ValueError("NON_COLOR_SOURCE_CASE")
        key_tuple=tuple(key)
        if key_tuple in signature_set:raise ValueError("REPEATED_SOURCE_CASE")
        signature_set.add(key_tuple)
        rows.append((key_tuple,value))
    if not any(y not in inp for inp,y in rows):
        raise ValueError("NO_SOURCE_NONCONSERVATIVITY")
    return {"arity":arity,"mode":mode,
            "clauses":tuple(sorted(rows)),"source_ast_sha256":sha(ast)}


def canonical_type(contract):
    """Entirely generic graph isomorphism over typed finite function facts.

    The arbitrary numeric colors are alpha-renamed; no meaningful symbols,
    palette colors, specific outcomes or human function-name are supplied.
    """
    if contract["mode"] not in ("set","multiset","ordered"):
        raise ValueError("UNSUPPORTED_FUNCTION_INPUT_TYPE")
    colors=sorted({v for sig,out in contract["clauses"] for v in (*sig,out)})
    if len(colors)>6:raise ValueError("PALETTE_CANONICALIZATION_CAP")
    possibilities=[]
    for perm in itertools.permutations(range(len(colors))):
        rename=dict(zip(colors,perm))
        clauses=tuple(sorted(
           ((tuple(sorted(rename[v] for v in sig))
             if contract["mode"]!="ordered" else tuple(rename[v] for v in sig)),
            rename[out]) for sig,out in contract["clauses"]))
        possibilities.append(clauses)
    return min(possibilities),len(colors)


@dataclass(frozen=True)
class NewSemanticType:
    mode:str
    arity:int
    roles:int
    canonical_facts:tuple
    source_hashes:tuple

    def ast(self):
        body=["Lambda",["role"+str(i) for i in range(self.arity)],
           ["Case",["EncodeArguments",self.mode,"roles"],
           [[list(key),out] for key,out in self.canonical_facts],
           ["Abstain","UNKNOWN_SEMANTIC_PAIR"]]]
        return ["DefineNewReusableSemanticType",
                "learned_type_"+sha(body)[:16],
                ["Product",["ColorRole"]*self.arity],"ColorRole",
                body]

    def to_json(self):
        return {"function_AST":self.ast(),
                "frozen_library_sha256":sha(self.ast()),
                "learned_input_type":self.mode,
                "arity":self.arity,
                "num_abstract_color_roles":self.roles,
                "source_program_sha256":list(self.source_hashes)}


def discover_operator_type(source_a,source_b):
    a,b=source_semantic_contract(source_a),source_semantic_contract(source_b)
    canon_a,roles_a=canonical_type(a)
    canon_b,roles_b=canonical_type(b)
    if a["arity"]!=b["arity"] or a["mode"]!=b["mode"] \
       or roles_a!=roles_b or canon_a!=canon_b:
        return None
    if a["source_ast_sha256"]==b["source_ast_sha256"]:
        raise ValueError("TRIVIAL_EXACT_PROGRAM_REUSE")
    return NewSemanticType(a["mode"],a["arity"],roles_a,canon_a,
            (a["source_ast_sha256"],b["source_ast_sha256"]))


def source_original_counterexample_to_old_join(train,decomp):
    """Only existence proof, NOT repeated GP speed comparison."""
    for row in train:
        panels=subgrids(row["input"],decomp)
        if panels is None:return False
        h,w=len(row["output"]),len(row["output"][0])
        for y in range(h):
            for x in range(w):
                args={p[y][x] for p in panels}
                if row["output"][y][x] not in args:return True
    return False


def derive_target_roles(train,decomp,library):
    """Learn bindings for a frozen type, no standalone new-table inference.

    All candidate role assignments must match the already-generated schema
    on every target TRAIN example. Unknown results never infer missing source
    color/output rules. The source type is fixed prior to target exposure.
    """
    observation=[]
    colors=set()
    for item in train:
        parts=subgrids(item["input"],decomp)
        if parts is None:return []
        expected=item["output"]
        h,w=len(expected),len(expected[0])
        if any(len(p)!=h or len(p[0])!=w for p in parts):return []
        for y in range(h):
            for x in range(w):
                args=tuple(part[y][x] for part in parts)
                result=expected[y][x]
                observation.append((args,result))
                colors.update(args);colors.add(result)
    if len(colors)!=library.roles:return []
    if not source_original_counterexample_to_old_join(train,decomp):
        return []
    ordered_colors=sorted(colors)
    facts=dict(library.canonical_facts)
    valid=[]
    for perm in itertools.permutations(ordered_colors):
        role_to_color=tuple(perm)
        color_to_role={col:role for role,col in enumerate(perm)}
        def apply(args):
            signature=tuple(color_to_role[x] for x in args)
            if library.mode=="set":
                signature=tuple(sorted(set(signature)))
            elif library.mode=="multiset":
                signature=tuple(sorted(signature))
            outcome=facts.get(signature,None)
            return role_to_color[outcome] if outcome is not None else None
        if all(apply(args)==result for args,result in observation):
            valid.append(role_to_color)
    return valid


def apply_frozen_type(library,decomp,color_roles,grid):
    parts=subgrids(grid,decomp)
    if parts is None:return None
    role_for_color={v:i for i,v in enumerate(color_roles)}
    facts=dict(library.canonical_facts)
    h,w=len(parts[0]),len(parts[0][0])
    result=[]
    for y in range(h):
        row=[]
        for x in range(w):
            args=tuple(part[y][x] for part in parts)
            if not all(col in role_for_color for col in args):
                return None
            signature=tuple(role_for_color[col] for col in args)
            if library.mode=="set":
                signature=tuple(sorted(set(signature)))
            elif library.mode=="multiset":
                signature=tuple(sorted(signature))
            outcome=facts.get(signature,None)
            if outcome is None:return None
            row.append(color_roles[outcome])
        result.append(row)
    return result


def fit_frozen_library_to_original(library,task,identifier,cohort):
    train=task["train"]
    candidates=[]
    if not all(grid_ok(p["input"]) and grid_ok(p["output"]) for p in train):
        return {"id":identifier,"cohort":cohort,"status":"INVALID_ORIGINAL_GRID",
                "submitted":False,"exact":False}
    for decomp in enumerate_decompositions(train):
        if decomp.count!=library.arity:continue
        bindings=derive_target_roles(train,decomp,library)
        for role_to_color in bindings:
            candidates.append((decomp,role_to_color))
    if not candidates:
        return {"id":identifier,"cohort":cohort,"status":"NO_REUSABLE_TYPE_INSTANCE",
                "submitted":False,"exact":False}
    frozen_spec=sha({"library":library.to_json(),
        "bindings":[[list(d),list(c)] for d,c in candidates]})
    outputs=[]
    for test in task["test"]:
        candidates_output=[
            apply_frozen_type(library,d,palette,test["input"])
            for d,palette in candidates]
        if not candidates_output or any(p is None for p in candidates_output) \
           or any(p!=candidates_output[0] for p in candidates_output[1:]):
            outputs.append(None)
        else:outputs.append(candidates_output[0])
    submitted=all(out is not None for out in outputs)
    exact=submitted and all(out==test["output"]
                            for out,test in zip(outputs,task["test"]))
    return {"id":identifier,"cohort":cohort,
            "status":"REUSED_SELF_DISCOVERED_SEMANTIC_TYPE",
            "submitted":submitted,"exact":exact,
            "wrong_submission":submitted and not exact,
            "ambiguous_train_bindings":len(candidates),
            "unseen_source_operator_type_reused":True,
            "frozen_library_sha256":sha(library.ast()),
            "frozen_binding_sha256":frozen_spec,
            "test_prediction_sha256":[sha(p) if p is not None else None
                                      for p in outputs],
            "no_direct_semantics_inventor_on_target":True}


def run(parent_report:Path,arc_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_REUSE_FIRST")
    previous=json.loads(parent_report.read_text())
    if previous["schema"]!=PARENT_SCHEME or previous["pin"]!=PIN:
        raise ValueError("SOURCE_FIRST_DRIFT")
    if previous["summary"]["public_TRAIN_400"]["tasks"]!=400 or \
       previous["summary"]["previously_opened_EVAL_32"]["tasks"]!=32:
        raise ValueError("SOURCE_COHORT_MISMATCH")
    rows={row["id"]:row for row in previous["rows"]}
    if len(rows)!=432:raise ValueError("SOURCE_IDS_NOT_DISTINCT")
    source_a,source_b=rows[SOURCE_IDS[0]],rows[SOURCE_IDS[1]]
    if not all(s["cohort"]=="public_TRAIN_400" for s in (source_a,source_b)):
        raise ValueError("SOURCE_ORIGINAL_GROUP_WRONG")
    learned=discover_operator_type(source_a,source_b)
    if learned is None:raise ValueError("NO_COMMON_TYPE_AUTOMATICALLY_DISCOVERED")
    # New operator type is created and frozen now, before ANY target task
    # is read from disk. Previous source first had targets in the artifact,
    # but this function never reads their program definitions.
    out.mkdir(parents=True)
    (out/"FROZEN_AUTONOMOUS_OPERATOR_TYPE.json").write_text(
            json.dumps(learned.to_json(),sort_keys=True,indent=2)+"\n")
    type_sha=sha(learned.ast())
    tested=[]
    for cohort,folder,ids in (
        ("public_TRAIN_400","training",None),
        ("previously_opened_EVAL_32","evaluation",EVAL32)
    ):
        base=arc_root/"data"/folder
        paths=(sorted(base.glob("*.json")) if ids is None
               else [base/(i+".json") for i in ids])
        if len(paths)!=(400 if ids is None else 32):
            raise ValueError("ORIGINAL_COHORT_CHANGED")
        for filepath in paths:
            if filepath.stem in SOURCE_IDS:continue
            task=json.loads(filepath.read_text())
            row=fit_frozen_library_to_original(
                learned,task,filepath.stem,cohort)
            tested.append(row)
            if row["status"]=="REUSED_SELF_DISCOVERED_SEMANTIC_TYPE":
                print("REUSE",cohort,filepath.stem,
                      "correct",row["exact"],
                      "submitted",row["submitted"],flush=True)
    if sha(learned.ast())!=type_sha:
        raise RuntimeError("LIBRARY_CHANGED_AFTER_TARGET_EXPOSURE")
    stats={}
    for cohort in ("public_TRAIN_400","previously_opened_EVAL_32"):
        subset=[r for r in tested if r["cohort"]==cohort]
        stats[cohort]={
            "original_targets":len(subset),
            "type_instantiations":sum(r["status"]=="REUSED_SELF_DISCOVERED_SEMANTIC_TYPE"
                                      for r in subset),
            "submitted":sum(r["submitted"] for r in subset),
            "test_exact":sum(r["exact"] for r in subset),
            "wrong":sum(r.get("wrong_submission",False) for r in subset)
        }
    report={"schema":SCHEMA,
        "source_preregistered_original_ids":list(SOURCE_IDS),
        "source_external_original_first_run":FROZEN_PARENT_RUN,
        "newly_discovered_operator_type":learned.to_json(),
        "new_type_frozen_before_target_data":True,
        "all_remaining_originals_evaluated_not_cherrypicked":True,
        "previously_project_opened_originals_only":True,
        "direct_target_program_or_semantic_table_inventor_called":False,
        "human_implemented_generic_color_role_isomorphism":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "summary":stats,"rows":tested}
    (out/"FIRST.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("RESULTS",json.dumps({k:v for k,v in report.items() if k!="rows"},
                               sort_keys=True))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent-first",type=Path,required=True)
    p.add_argument("--arc-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.parent_first,args.arc_root,args.out)
