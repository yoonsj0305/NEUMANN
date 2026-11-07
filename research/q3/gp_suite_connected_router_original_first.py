"""Q3 genuinely different-source author benchmark: Helmuth/Spector GP-Suite.

The full 29-family General Program Synthesis Benchmark Suite has independently
authored edge/random I/O. Discovery uses ONLY source training cases.
Program AST freezes before withheld random cases are scored. The target
algorithm receives no task name, specification, generator source, or target
reference implementation.

Source memory is restored VERBATIM from the prior #717 artifact, where the
coordinate representation was generated from a now-exposed HumanEval/48
development problem. It is NOT manually inserted in this experiment.

This measures ONE scientific missing link: proof-carrying reuse of a learned
relational constructor with COLD SAME-CORE controls and cross-domain routing.

The generator algorithms and their VM primitives are human-authored. Even a
positive FIRST cannot establish unrestricted Q3 or 10x improvements.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import gzip
import hashlib
import heapq
import json
from pathlib import Path
import time

from research.q3.connected_constructor_router import (
    ConnectedConstructorRouter,validate_memory,score_source_frozen,
    program_id,run_canonical,canon,result_equal
)

SCHEMA="neumann.q3.gp-suite-independent-original-29-family-first.v1"
SOURCE_ARTIFACT_RUN=42363017165
PREFLIGHT_EXPECTED_SOURCE="research/q3/discover_index_relation_constructor.py"


def load_prior_learned_representation(artifact:Path):
    first=json.loads(artifact.read_text())
    if first.get("schema")!="neumann.q3.generic-pairwise-coordinate-repr-postfirst.v1":
        raise ValueError("PRIOR_ARTIFACT_SCHEMA_CHANGED")
    if first.get("original_first_source_actions_run")!=42361601013:
        raise ValueError("NO_SOURCE_PROVENANCE")
    source=next((row for row in first.get("rows",[])
                 if row.get("id")=="HumanEval/48"),None)
    if not source or not source.get("original_heldout_exact"):
        raise ValueError("PRIOR_OPERATOR_NOT_ACTUALLY_VERIFIED")
    program=source.get("invented_representation_ast")
    if not validate_memory(program):
        raise ValueError("PRIOR_PROGRAM_FAILS_GENERIC_AFFINE_BOUNDS_PROOF")
    cert=first.get("symbolic_certificate") or {}
    if not cert.get("certifies_value_equality_to_reverse_for_any_sequence"):
        raise ValueError("SOURCE_PROOF_CERTIFICATE_MISSING")
    # Prior post-first source has already been inspected; preserve truth.
    return {"program":program,"sha256":program_id(program),
            "source_original":"HumanEval/48",
            "source_proof_status":"POSTFIRST_DEVELOPMENT_VERIFIED",
            "source_artifact":SOURCE_ARTIFACT_RUN}


def iterator(path:Path):
    if path.name.endswith(".gz"):
        opening=lambda: gzip.open(path,"rt",encoding="utf-8")
    else:
        opening=lambda: path.open("rt",encoding="utf-8")
    with opening() as f:
        for line in f:
            if not line.strip():continue
            try:
                obj=json.loads(line)
            except (ValueError,json.JSONDecodeError):
                continue
            if isinstance(obj,dict):
                yield obj


def parse_pair(row):
    """Generic inputN/outputN interface, known from corpus documentation."""
    ins=sorted((k for k in row if k.startswith("input") and
                k[5:].isdigit()),key=lambda k:int(k[5:]))
    outs=sorted((k for k in row if k.startswith("output") and
                 k[6:].isdigit()),key=lambda k:int(k[6:]))
    if len(ins) not in (1,2) or len(outs)!=1:
        raise ValueError("UNSUPPORTED_INPUT_OUTPUT_ARITY")
    if ins!=[f"input{i+1}" for i in range(len(ins))]:
        raise ValueError("NONCONTIGUOUS_INPUT_INDEX")
    if outs!=["output1"]:
        raise ValueError("UNSUPPORTED_OUTPUT_INDEX")
    xs=[row[k] for k in ins]
    y=row[outs[0]]
    allowed=(str,int,float,bool,list,tuple)
    if any(type(v) not in allowed for v in xs+[y]):
        raise ValueError("UNSUPPORTED_PRIMITIVE_IO")
    for value in xs+[y]:
        if type(value) in (str,list,tuple) and len(value)>1024:
            raise ValueError("OVERLONG_IO")
        if type(value) in (list,tuple) and any(
                type(element) not in (str,int,float,bool)
                for element in value):
            raise ValueError("NESTED_TREES_NOT_YET_SUPPORTED")
    return xs,y


def load_training(edge:Path,random:Path):
    """Train from edge and hash-sampled random; hold out distinct random.

    We choose the train/test SHARD by SHA256(INPUTS) alone, without using
    gold outputs for selection. Public random results are consumed only
    AFTER all candidate ASTs are frozen by the evaluation below.
    """
    edge_seen=set();edge_rows=[];edge_errors=0
    for obj in iterator(edge):
        try:pair=parse_pair(obj)
        except (ValueError,TypeError):
            edge_errors+=1;continue
        key=canon(pair[0])
        if key not in edge_seen:
            edge_seen.add(key);edge_rows.append(pair)
            if len(edge_rows)>=12:break
    # Keep deterministic bottom-64 input-hash sample from up to 50k
    # original independent random cases (bounded CPU / memory).
    heap=[];seen=set();invalid=0;raw=0
    for obj in iterator(random):
        raw+=1
        if raw>50000:break
        try:pair=parse_pair(obj)
        except (ValueError,TypeError):
            invalid+=1;continue
        key=canon(pair[0])
        if key in seen or key in edge_seen:continue
        seen.add(key)
        sig=int(hashlib.sha256(
                ("NEUMANN_Q3_GP_SOURCE_20261107/"+key).encode()
               ).hexdigest(),16)
        # Exclude total duplicates; only original distinct input values.
        current=(-sig,key,pair)
        if len(heap)<64:
            heapq.heappush(heap,current)
        elif current>heap[0]:
            heapq.heapreplace(heap,current)
    original=[(-priority,key,pair) for priority,key,pair in heap]
    original.sort(key=lambda x:(x[0],x[1]))
    # 12 + 8 source observations, 32 original heldout random I/O, with
    # untouched extra 24 observations discarded rather than cherry-picked.
    train=edge_rows+ [entry[2] for entry in original[:8]]
    heldout=[entry[2] for entry in original[8:40]]
    return train,heldout,{
        "source_edge_train_examples":len(edge_rows),
        "source_random_train_examples":min(8,len(original)),
        "heldout_original_independent_random_examples":len(heldout),
        "random_rows_scanned":min(raw,50000),
        "random_schema_or_type_rejected":invalid,
        "edge_type_rejected":edge_errors,
        "input_hash_selection_only":True,
        "source_IO_original_test_disjoint":True
    }


def evaluate(dataset:Path,manifest_path:Path,source_artifact:Path,out:Path,
             fold_budget:int=1000,relation_budget:int=1200):
    if out.exists():raise ValueError("NO_OVERWRITE_PUBLIC_FIRST")
    out.mkdir(parents=True)
    source=load_prior_learned_representation(source_artifact)
    manifest=json.loads(manifest_path.read_text())
    if not isinstance(manifest,list) or len(manifest)<20:
        raise ValueError("EXTERNAL_DATASET_MANIFEST_IS_INCOMPLETE")
    hasher=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    memory_router=ConnectedConstructorRouter(source["program"])
    cold_router=ConnectedConstructorRouter()
    receipts=[]
    started=time.perf_counter_ns()
    for entry in manifest:
        task=entry["task"]
        record={
            "source_task":task,
            "original_author":"Thomas Helmuth / Lee Spector",
            "source_input_output_names_NOT_used_to_choose_program":True,
            "source_reference_implementation_NOT_READ":True,
            "status":"UNSET",
            "source_file_paths":entry.get("paths",{}),
            "source_file_sizes_B":entry.get("size_B",{}),
        }
        try:
            if not entry.get("downloaded",False):
                raise ValueError("DATA_NOT_DOWNLOADED_OR_SIZE_LIMIT")
            edge=dataset/entry["paths"]["edge"]
            random=dataset/entry["paths"]["random"]
            if not edge.is_file() or not random.is_file():
                raise ValueError("DATA_PAIR_INCOMPLETE")
            train,heldout,meta=load_training(edge,random)
            record.update(meta)
            if len(train)<6 or len(heldout)<16:
                raise ValueError("TOO_FEW_SOURCE_OR_UNSEEN_ORIGINALS")
            sigs={(tuple(type(v).__name__ for v in x),
                   type(y).__name__) for x,y in train}
            if len(sigs)!=1:raise ValueError("MIXED_TRAINING_IO_SCHEMA")
            # **ALL candidate programs are frozen first, then test cases
            # are scored.** Source/heldout were loaded independently by
            # input-hash but heldout labels not passed to ANY generator.
            warm=memory_router.discover(train,use_memory=True,
                    relation_budget=relation_budget,fold_budget=fold_budget)
            cold=cold_router.discover(train,use_memory=False,
                    relation_budget=relation_budget,fold_budget=fold_budget)
            no_relation=next((x for x in (
                cold, ) if x.get("program") and
                x["program"]["origin"]!="fresh_relational_invention"),None)
            pred_w=score_source_frozen(warm,heldout)
            pred_c=score_source_frozen(cold,heldout)
            record.update({
                "status":"EVALUATED",
                "source_train_total":len(train),
                "source_heldout_total":len(heldout),
                "typed_signature":list(next(iter(sigs))),
                "warm":warm,"cold":cold,
                "warm_heldout":pred_w,"cold_heldout":pred_c,
                "source_memory_used":bool(
                    warm.get("program") is not None and
                    warm["program"]["origin"]=="prior_verified_relation_memory"),
                "memory_accuracy_lift_exact":bool(
                    pred_w["exact"] and not pred_c["exact"]),
                "cold_exact_and_memory_wrong":bool(
                    pred_c["exact"] and not pred_w["exact"]),
                "all_32_or_more_heldout_exact_warm":pred_w["exact"],
                "all_32_or_more_heldout_exact_cold":pred_c["exact"],
            })
            if pred_w["exact"] or pred_c["exact"]:
                print("Q3_GP_INDEPENDENT_EXTERNAL_EXACT",task,
                      "memory",pred_w["exact"],"cold",pred_c["exact"],
                      "source_memory_used",record["source_memory_used"],
                      "source_AST",warm.get("selected_ast_sha256"),flush=True)
        except (ValueError,TypeError,KeyError,IndexError,
                OverflowError,MemoryError,RecursionError,
                OSError,EOFError,UnicodeError) as e:
            record["status"]="UNSUPPORTED_OR_INCOMPLETE"
            record["reason"]=f"{type(e).__name__}:{e}"[:180]
            record["source_heldout_total"]=0
        receipts.append(record)
    eligible=[x for x in receipts if x["status"]=="EVALUATED"]
    summary={
        "all_source_family_directories":len(manifest),
        "eligible_full_32_holdout_families":len(eligible),
        "unsupported_or_missing_families":len(manifest)-len(eligible),
        "memory_full_original_exact_families":sum(
            x["warm_heldout"]["exact"] for x in eligible),
        "cold_same_core_full_original_exact_families":sum(
            x["cold_heldout"]["exact"] for x in eligible),
        "memory_additional_full_exact_families":sum(
            x["memory_accuracy_lift_exact"] for x in eligible),
        "memory_negative_transfer_full_exact_families":sum(
            x["cold_exact_and_memory_wrong"] for x in eligible),
        "memory_executable_reuse_trials":sum(
            x["source_memory_used"] for x in eligible),
        "warm_heldout_examples_exact":sum(
            x["warm_heldout"]["original_heldout_correct"]
            for x in eligible),
        "cold_heldout_examples_exact":sum(
            x["cold_heldout"]["original_heldout_correct"]
            for x in eligible),
        "total_original_heldout_examples":sum(
            x["source_heldout_total"] for x in eligible),
        "total_warm_discovery_ms":round(sum(
            x["warm"].get("elapsed_ms",0) for x in eligible),4),
        "total_cold_discovery_ms":round(sum(
            x["cold"].get("elapsed_ms",0) for x in eligible),4),
        "original_external_first_pre_registered_data_file_manifest_sha256":hasher,
    }
    report={
        "schema":SCHEMA,
        "external_corpus":"Helmuth/Spector General Program Synthesis Benchmark Suite",
        "external_author_distinct_from_Google_MBPP_and_HumanEval":True,
        "original_training_edge_and_random_sources_separated_from_original_random_heldout":True,
        "previously_generated_relational_representation_artifact_loaded_NOT_literal_inserted":True,
        "source_memory":source,
        "program_source_human_coded_three_generic_constructor_families":True,
        "no_global_Q3_guarantee":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "summary":summary,"rows":receipts}
    (out/"FIRST.json").write_text(
        json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("Q3_GP_FULL_29_EXTERNAL_ORIGINAL_FIRST",
          json.dumps(summary,sort_keys=True),flush=True)
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--source-artifact",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--fold-budget",type=int,default=1000)
    p.add_argument("--relation-budget",type=int,default=1200)
    a=p.parse_args()
    evaluate(a.data,a.manifest,a.source_artifact,a.out,
             a.fold_budget,a.relation_budget)
