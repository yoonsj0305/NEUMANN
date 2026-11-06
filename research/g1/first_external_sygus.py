"""G1 external author original SyGuS STRING first source evaluation.

Loads byte-pinned own-weight checkpoint trained only on generated synthetic
tasks. Opens exactly preregistered public SyGuS source files AFTER freeze.
Candidate selector sees (input,expected output) TRAIN only, and original
heldout last constraint INPUT; heldout GOLD is scored only after proposals
from learned and TWO equal-rights classical baselines have been committed
to in-memory records. The FIRST JSON must be immutable after execution.

Scoped constraints, not universally correct string functions or global Q3.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.request import Request,urlopen
from typing import Any
from research.g1.ownweight_string_ast import ATOMS, features, run_ast, topk, reserved_pair

ROOT=Path(__file__).resolve().parents[2]
PREREG=ROOT/"docs/experiments/G1_OWNWEIGHT_STRING_AST_EXTERNAL_FIRST_PREREG_2026_11_06.json"
FROZEN=ROOT/"docs/experiments/G1_OWNWEIGHT_AST_V2_FROZEN_BEFORE_EXTERNAL_FIRST_2026_11_06.json"


def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()


def smt_value(source:str)->str:
    if not source.startswith('"') or not source.endswith('"'):
        raise ValueError("BAD_SOURCE_STRING")
    inner=source[1:-1].replace('""','"')
    if "\\" in inner:
        # A backslash literal may have SMT-LIB version-dependent meaning.
        # Reject unknown escapes instead of silently misgrading.
        raise ValueError("UNSUPPORTED_ESCAPE_SOURCE")
    return inner


QSTR=r'"(?:[^"]|"")*"'
PAT=re.compile(
    r"\\(constraint\\s+\\(=\\s+\\(f\\s+("+QSTR+r")\\)\\s+("+QSTR+r")\\s*\\)\\s*\\)",
    re.DOTALL)


def parse_original(data:bytes)->tuple[list[tuple[str,str]]|None,str|None]:
    try:
        source=data.decode("utf-8").replace("\\r","\\n")
    except UnicodeError:
        return None,"NON_UTF8_SOURCE"
    if "(check-synth)" not in source or "(set-logic SLIA)" not in source:
        return None,"UNSUPPORTED_NOT_ORIGINAL_SLIA"
    all_constraints=len(re.findall(r"\\(constraint\\b",source))
    matches=PAT.findall(source)
    if len(matches)!=all_constraints or all_constraints<2:
        return None,"UNSUPPORTED_ARITY_OR_SOURCE_CONSTRAINT_PATTERN"
    try:
        pairs=[(smt_value(a),smt_value(b)) for a,b in matches]
    except ValueError as e:
        return None,str(e)
    if len(pairs)!=len(set(pairs)):
        # Reject duplicated source inputs rather than manufacture generalization.
        return None,"DUPLICATE_SOURCE_INPUT_OUTPUT"
    return pairs,None


def freeze_programs(train:list[tuple[str,str]],unseen_input:str,
                    ordered:list[tuple[int,int]],max_evals:int)->dict[str,Any]:
    fits=[]
    evaluated=0
    for pair in ordered[:max_evals]:
        evaluated+=1
        try:
            if all(run_ast(pair,x)==y for x,y in train):
                fits.append((pair,run_ast(pair,unseen_input)))
        except Exception:
            continue
    predictions={value for _,value in fits}
    answer=(next(iter(predictions)) if len(predictions)==1 else None)
    return {
        "candidate_program_executions":evaluated,
        "fitting_ASTs":[[int(a),int(b)] for (a,b),_ in fits],
        "source_fit_count":len(fits),
        "predictions_conflict":len(predictions)>1,
        "submitted":answer is not None,
        "prediction":answer,
        "prediction_sha256":(hashlib.sha256(answer.encode()).hexdigest()
               if answer is not None else None),
        "winner_is_heldout_composition":(answer is not None and
             any(reserved_pair(pair) for pair,pred in fits if pred==answer))
    }


def classical_order()->list[tuple[int,int]]:
    # Same 15 atomic rights and CONCAT syntax as the student.
    # No gold/source hidden input used; prefer single atom and shorter source.
    def complexity(pair):
        a,b=ATOMS[pair[0]],ATOMS[pair[1]]
        return (int(a!="EMPTY")+int(b!="EMPTY"),
                int(a not in ("INPUT","HEAD1","FIRST_WORD"))+
                int(b not in ("EMPTY","SPACE","DOT","DASH")),
                pair[0],pair[1])
    return sorted(
        ((i,j) for i in range(len(ATOMS)) for j in range(len(ATOMS))),
        key=complexity)


def external_first(weights_file:Path)->dict[str,Any]:
    pre=json.loads(PREREG.read_text())
    frozen=json.loads(FROZEN.read_text())
    wdata=weights_file.read_bytes()
    weights_sha=hashlib.sha256(wdata).hexdigest()
    if weights_sha!=frozen["source_free_V2"]["weights_sha256"]:
        raise ValueError("EXTERNAL_FIRST_UNFROZEN_OR_REPLACED_STUDENT_WEIGHTS")
    weights=json.loads(wdata)
    if weights["schema"]!="neumann.g1.ownweight-two-token-string-ast-checkpoint.v2" or \
       weights["reserved_pair_count"]!=45 or \
       weights["training_distinct_program_pairs"]!=180 or \
       weights["original_external_tasks_accessed"]!=0:
        raise ValueError("STUDENT_CHECKPOINT_NOT_ACTUAL_RESERVED_AST_TRAIN")
    programs=classical_order()
    if len(programs)!=225 or len(set(programs))!=225:
        raise ValueError("INCOMPLETE_EQUAL_RIGHTS_CLASSICAL_GRAMMAR")
    report=[]
    begin=time.perf_counter_ns()
    for target in pre["external_original"]["tasks"]:
        url="https://raw.githubusercontent.com/"+pre["external_original"]["repo"]+ \
            "/"+pre["external_original"]["commit"]+"/"+pre["external_original"]["subdir"]+ \
            "/"+target["name"]
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G1-first"}),timeout=40) as response:
            raw=response.read(50000)
        source_blob=gitblob(raw)
        if source_blob!=target["git_blob"]:
            raise ValueError("ORIGINAL_EXTERNAL_SYGUS_GIT_BLOB_CHANGED_"+target["name"])
        pairs,problem=parse_original(raw)
        row={"task_file":target["name"],"original_git_blob":source_blob,
             "original_source_bytes":len(raw),
             "constraint_count":len(pairs) if pairs else None,
             "scientific_scope":"PBE original last constraint held out only",
             "train_example_count":len(pairs)-1 if pairs else 0}
        if problem:
            row.update({"status":"UNSUPPORTED_ORIGINAL_COUNTED",
                        "error":problem,
                        "learned":None,"classical32":None,"classical225":None})
            report.append(row)
            continue
        train=pairs[:-1]
        test_input=pairs[-1][0]
        feat=features(train)
        start=time.perf_counter_ns()
        learned_order=topk(weights,feat,max_pairs=225)
        learned_compile_ns=time.perf_counter_ns()-start
        start=time.perf_counter_ns()
        learned=freeze_programs(train,test_input,learned_order,32)
        learned_ns=time.perf_counter_ns()-start
        start=time.perf_counter_ns()
        classic32=freeze_programs(train,test_input,programs,32)
        classic32_ns=time.perf_counter_ns()-start
        start=time.perf_counter_ns()
        full=freeze_programs(train,test_input,programs,225)
        full_ns=time.perf_counter_ns()-start
        # No gold was passed to learner or either classical enumerator.
        # Read target output ONLY AFTER source proposals are frozen.
        test_gold=pairs[-1][1]
        for result in (learned,classic32,full):
            result["correct_original_heldout"]=(result["submitted"] and
                result["prediction"]==test_gold)
            result["wrong_original_heldout"]=(result["submitted"] and
                result["prediction"]!=test_gold)
        row.update({
            "status":"ORIGINAL_SCORED",
            "student_source_programs_not_task_id":True,
            "learned":learned,
            "classical32":classic32,
            "classical225":full,
            "student_inference_ns":learned_compile_ns,
            "learned_candidate_runtime_ns":learned_ns,
            "classical_32_runtime_ns":classic32_ns,
            "classical_full_runtime_ns":full_ns,
            "test_source_input_sha256":hashlib.sha256(test_input.encode()).hexdigest(),
            "test_original_gold_sha256":hashlib.sha256(test_gold.encode()).hexdigest(),
            "source_gold_only_used_for_scoring":True
        })
        report.append(row)
    scored=[r for r in report if r["status"]=="ORIGINAL_SCORED"]
    count=lambda arm,key:sum(bool(r[arm][key]) for r in scored)
    extra=sum(r["learned"]["correct_original_heldout"] and
        not r["classical32"]["correct_original_heldout"] for r in scored)
    proof_train=sum(any(reserved_pair(tuple(p)) for p in r["learned"]["fitting_ASTs"])
       and r["learned"]["correct_original_heldout"] for r in scored)
    stats={
        "external_author_source_tasks_frozen":len(report),
        "original_supported":len(scored),
        "original_unsupported_counted":len(report)-len(scored),
        "learned_submitted":count("learned","submitted"),
        "learned_original_heldout_correct":count("learned","correct_original_heldout"),
        "learned_original_heldout_wrong":count("learned","wrong_original_heldout"),
        "classical32_submitted":count("classical32","submitted"),
        "classical32_correct":count("classical32","correct_original_heldout"),
        "classical32_wrong":count("classical32","wrong_original_heldout"),
        "classical225_submitted":count("classical225","submitted"),
        "classical225_correct":count("classical225","correct_original_heldout"),
        "classical225_wrong":count("classical225","wrong_original_heldout"),
        "learned_additional_verified_over_classical32":extra,
        "new_AST_pair_reserved_in_training_on_correct_original":proof_train,
        "external_original_fetch_model_inference_wall_ns":time.perf_counter_ns()-begin,
        "ownweight_checkpoint_sha256":weights_sha,
        "trained_pair_count":weights["training_distinct_program_pairs"],
        "synthetic_reserved_pairs":weights["reserved_pair_count"],
        "original_ARC_evaluation_IDs_consumed":0
    }
    passed=(stats["original_supported"]>=5 and
      stats["learned_original_heldout_correct"]>=2 and
      stats["learned_additional_verified_over_classical32"]>=1 and
      stats["learned_original_heldout_wrong"]==0 and
      stats["new_AST_pair_reserved_in_training_on_correct_original"]>=1)
    return {
      "schema":"neumann.g1.first-ownweight-ast-real-external-sygus.v1",
      "science_status":"SCOPED_LEARNED_CROSS_AUTHOR_AST_TRANSFER_PASS" if passed
          else "SCOPED_LEARNED_CROSS_AUTHOR_AST_TRANSFER_FAIL",
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "one_original_external_FIRST":True,
      "source_type":"2018 SyGuS public PBE-String; no full all-string equivalence proof",
      "model_training_token_and_energy_cost":"UNKNOWN",
      "model_was_trained_from_scratch":True,
      "script_policies_do_not_read_original_test_gold":True,
      "same_program_language_for_student_and_classical":True,
      "full_classical_225_versionspace_comparison":True,
      "stronger_external_sygus_specialist_run":"NOT_RUN",
      "equal_end_to_end_10x_cost":"NOT_ESTABLISHED",
      "stats":stats,"rows":report
    }


def main()->int:
    if len(sys.argv)!=2:
        print("usage: python -m research.g1.first_external_sygus AST_V2_WEIGHTS.json",file=sys.stderr)
        return 2
    try:
        out=external_first(Path(sys.argv[1]))
        print(json.dumps(out,indent=2,sort_keys=True))
        return 0 if out["science_status"]=="SCOPED_LEARNED_CROSS_AUTHOR_AST_TRANSFER_PASS" else 1
    except Exception as error:
        print(json.dumps({"schema":"neumann.g1.first-ownweight-ast-real-external-sygus.v1",
           "science_status":"INFRA_OR_SOURCE_FAIL_CLOSED",
           "error":type(error).__name__+": "+str(error)[:280]},indent=2))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
