"""Q3 meta-grammar causal original-author transfer FIRST: OpenAI HumanEval.

Evaluation contract:
- BEFORE downloading the external HumanEval corpus, learn a reusable
  grammar production from all previously independently verified #714
  source programs. Source candidates selected automatically by program
  structure, NOT by hard-coded source ID.
- The only HumanEval field read is 'test'. Never read 'prompt' or
  'canonical_solution'; never execute untrusted benchmark Python code.
- Parse only direct literal assert candidate(literal) == literal inside
  check(candidate). Reject entire task if any assert is unsupported.
- First N-2 executable original tests are source TRAIN; final TWO original
  tests are heldout and decoded AFTER code freeze.
- All eligible original tasks, wrong, abstain and unsupported preserved.
- Same base VM/candidate language in learned and COLD, same 16-candidate
  budget. Also report cold 256-candidate eventual success for expressivity.
- No claim of unrestricted Q3, Q4 or Q6 from a limited public corpus.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time
from research.q3.causal_learned_grammar_inventor import (
    SCHEMA as GRAMMAR_SCHEMA,canonical,digest,
    learn_production,solve,scorable,run_operator
)

SCHEMA="neumann.q3.source_generated_grammar_humaneval_external_first.v1"
VERIFIED_FIRST=42354198810
VERIFIED_SEMANTIC=42354597895

def freeze_from_original_sources(original_first:Path,
                                 original_semantic:Path,
                                 out:Path):
    if out.exists():raise ValueError("IMMUTABLE_GRAMMAR_FROZEN_NO_OVERWRITE")
    out.mkdir(parents=True)
    original=json.loads(original_first.read_text())
    semantic=json.loads(original_semantic.read_text())
    if original["schema"]!="neumann.q3.source-frozen-feature-predicate-new-mbpp-cohort.v1":
        raise ValueError("SOURCE_FIRST_SCHEMA_WRONG")
    if original["summary"]["source_learned_constructor_frozen_sha256"]!=\
       "2cd85f1712ef91dbcab4a3bc85c583dfd235dd9ef451ae13282c25aef1cfa332":
        raise ValueError("SOURCE_FIRST_FINGERPRINT_WRONG")
    if semantic["original_FIRST_actions_run"]!=VERIFIED_FIRST or \
       not semantic["stronger_semantic_proof_pass"]:
        raise ValueError("POSTFIRST_INDEPENDENT_PROOF_NOT_VALID")
    candidates=[]
    audits={x["original_MBPP_task_id"]:x for x in semantic["programs"]}
    for row in original["rows"]:
        pid=row["id"]
        cert=audits.get(pid)
        if (cert is not None and cert["semantic_agreement_on_new_probe"]
                and row.get("new_generated_exact") and
                row.get("source_generated_ast") is not None):
            candidates.append({"task_id":pid,
                               "original_heldout_exact":True,
                               "program":row["source_generated_ast"]})
    candidates.sort(key=lambda x:x["task_id"])
    found=[];failures=[]
    started=time.perf_counter_ns()
    for a,b in combinations(candidates,2):
        try:
            rule=learn_production([a,b])
            found.append(rule)
        except (ValueError,KeyError,IndexError,TypeError) as e:
            failures.append({"source_pair":[a["task_id"],b["task_id"]],
                             "reason":str(e)})
    if not found:raise ValueError("NO_NEW_MACHINE_GENERATED_GRAMMAR")
    # Ranking is source-independent: most structure, then canonical AST
    found.sort(key=lambda r:(
        -len(canonical(r["pattern_ast"])),
        canonical(r["pattern_ast"])))
    chosen=found[0]
    freeze={
        "schema":SCHEMA,
        "original_first_source_run":VERIFIED_FIRST,
        "independent_source_semantic_run":VERIFIED_SEMANTIC,
        "source_candidate_count":len(candidates),
        "source_candidate_ids":[x["task_id"] for x in candidates],
        "source_pairs_considered":len(failures)+len(found),
        "source_pairs_rejected":failures,
        "learned_grammar_candidates":found,
        "machine_selected_production":chosen,
        "frozen_production_sha256":digest(chosen),
        "source_only_learning_ms":round(
            (time.perf_counter_ns()-started)/1e6,5),
        "base_vm_modified":False,
        "human_supplied_meta_unifier":True,
        "human_supplied_source_AST_lowering":True,
        "independent_author_target_NOT_DOWNLOADED":True,
        "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
    }
    (out/"SOURCE_FIRST_FROZEN_GRAMMAR.json").write_text(
        json.dumps(freeze,sort_keys=True,indent=2)+"\n")
    print("Q3_INVENTED_GRAMMAR_FROZEN_BEFORE_HUMANEVAL",
          json.dumps({
          "candidate_source_program_ids":freeze["source_candidate_ids"],
          "pairs_examined":freeze["source_pairs_considered"],
          "generated_new_production":chosen["name"],
          "source_training_programs_selected_by_structural_novelty":
               chosen["source_operator_programs"],
          "pattern":chosen["pattern_ast"],
          "frozen_sha256":freeze["frozen_production_sha256"],
          "learn_ms":freeze["source_only_learning_ms"]},
          sort_keys=True),flush=True)
    return freeze

def parse_humaneval_assert(statement):
    # The expected output is a literal, never generated with exec/eval.
    if type(statement) is not ast.Assert:
        raise ValueError("UNSUPPORTED_NON_ASSERT_TEST")
    compare=statement.test
    if (not isinstance(compare,ast.Compare) or
        len(compare.ops)!=1 or type(compare.ops[0]) is not ast.Eq or
        len(compare.comparators)!=1):
        raise ValueError("NON_LITERAL_COMPARISON")
    call=compare.left
    if (not isinstance(call,ast.Call) or
        not isinstance(call.func,ast.Name) or
        call.func.id!="candidate" or
        len(call.args)!=1 or len(call.keywords)):
        raise ValueError("UNSUPPORTED_OR_WRAPPED_CANDIDATE_CALL")
    try:
        inp=ast.literal_eval(call.args[0])
        expected=ast.literal_eval(compare.comparators[0])
    except (TypeError,ValueError,SyntaxError,MemoryError):
        raise ValueError("UNSAFE_OR_NONLITERAL_VALUE")
    if (type(inp) not in (list,tuple,str) or type(inp) is not type(expected)):
        raise ValueError("NOT_SEQUENCE_TO_SAME_SEQUENCE")
    if len(inp)>1024 or len(expected)>1024:
        raise ValueError("BOUND_EXCEEDED")
    try:
        sequence=inp if type(inp) is not str else list(inp)
        target=expected if type(expected) is not str else list(expected)
        if any(type(x) not in (str,int,float,bool) for x in sequence+target):
            raise ValueError("INVALID_TOKEN_TYPE")
    except TypeError:
        raise ValueError("UNHASHABLE_OR_NONSEQUENCE")
    return [inp],expected

def extract_original_assertions(test_source):
    parsed=ast.parse(test_source)
    checker=[x for x in parsed.body if isinstance(x,
             (ast.FunctionDef,ast.AsyncFunctionDef)) and x.name=="check"]
    if len(checker)!=1:raise ValueError("NO_SINGLE_CHECK_FUNCTION")
    node=checker[0]
    if len(node.args.args)!=1 or node.args.args[0].arg!="candidate":
        raise ValueError("NONSTANDARD_CHECKER_INTERFACE")
    if not 4<=len(node.body)<=200:
        raise ValueError("INSUFFICIENT_OR_TOO_MANY_CHECKER_STATEMENTS")
    return [parse_humaneval_assert(stmt) for stmt in node.body]

def evaluate_humaneval(gz_path:Path,source_freeze:Path,out:Path,
                       budget:int=16):
    if out.exists():raise ValueError("IMMUTABLE_EXTERNAL_FIRST_NO_OVERWRITE")
    out.mkdir(parents=True)
    source=json.loads(source_freeze.read_text())
    if source["schema"]!=SCHEMA:raise ValueError("SOURCE_GRAMMAR_SCHEMA_WRONG")
    learned=source["machine_selected_production"]
    if digest(learned)!=source["frozen_production_sha256"]:
        raise ValueError("GRAMMAR_CHANGED_AFTER_FREEZE")
    start=time.perf_counter_ns()
    sha=hashlib.sha256(gz_path.read_bytes()).hexdigest()
    with gzip.open(gz_path,"rt",encoding="utf8") as handle:
        lines=[json.loads(line) for line in handle if line.strip()]
    if len(lines)!=164:
        raise ValueError("HUMANEVAL_OFFICIAL_TASK_COUNT_CHANGED")
    receipts=[]
    for task in lines:
        ident=task.get("task_id")
        record={"original_task_id":ident,
                "reference_solution_NOT_READ":True,
                "prompt_NOT_READ":True,
                "human_eval_source_file_sha256":sha,
                "budget_per_original_per_arm":budget,
                "status":"NOT_CHECKED"}
        try:
            test=task["test"]
            examples=extract_original_assertions(test)
            train=examples[:-2] # Two separate independent author assertions
            heldout=examples[-2:]
            a=solve(train,rule=learned,budget=budget)
            b=solve(train,rule=None,budget=budget)
            c=solve(train,rule=None,budget=256)
            # No use of heldout before a,b,c have returned/frozen ASTs.
            def score(x):
                return [scorable(x["program"],args,goal)
                        for args,goal in heldout]
            aw,bw,cw=score(a),score(b),score(c)
            record.update({
                "status":"EVALUATED","source_training_original_asserts":len(train),
                "source_heldout_original_asserts":2,
                "learned_program":a["program"],
                "learned_program_source":a["status"],
                "cold_equal_budget_program":b["program"],
                "cold_full_search_program":c["program"],
                "learned_candidate_checks":a["attempts"],
                "cold_candidate_checks":b["attempts"],
                "cold_full_candidate_checks":c["attempts"],
                "learned_source_ms":a["wall_ms"],
                "cold_source_ms":b["wall_ms"],
                "cold_full_source_ms":c["wall_ms"],
                "learned_heldout_correct":sum(aw),
                "cold_heldout_correct":sum(bw),
                "cold_full_heldout_correct":sum(cw),
                "learned_heldout_full_exact":all(aw),
                "cold_heldout_full_exact":all(bw),
                "cold_full_heldout_full_exact":all(cw),
                "learned_grammar_caused_exact_gain":bool(
                    all(aw) and not all(bw) and
                    a["status"]=="INVENTED_GRAMMAR_PRODUCTION"),
            })
            if all(aw):
                print("Q3_HUMANEVAL_ORIGINAL_EXACT",ident,
                      "learned",a["status"],"cold",all(bw),
                      "full_cold",all(cw),
                      "attempts",[a["attempts"],b["attempts"],c["attempts"]],
                      flush=True)
        except (ValueError,TypeError,IndexError,KeyError,
                RecursionError,MemoryError,SyntaxError,OverflowError) as e:
            record.update({"status":"INELIGIBLE",
                           "reason":(type(e).__name__+":"+str(e))[:170],
                           "source_heldout_original_asserts":0,
                           "learned_heldout_full_exact":False})
        receipts.append(record)
    eligible=[r for r in receipts if r["status"]=="EVALUATED"]
    summary={
        "original_humaneval_tasks":len(lines),
        "eligible_originals_strict_literal_sequence_test_interface":len(eligible),
        "unsupported_originals":len(lines)-len(eligible),
        "learned_grammar_exact_2_of_2_original_heldout":sum(
            x["learned_heldout_full_exact"] for x in eligible),
        "cold_equal_16_budget_exact_2_of_2":sum(
            x["cold_heldout_full_exact"] for x in eligible),
        "cold_equal_256_larger_budget_exact_2_of_2":sum(
            x["cold_full_heldout_full_exact"] for x in eligible),
        "causal_exact_additional_originals_at_same_budget":sum(
            x["learned_grammar_caused_exact_gain"] for x in eligible),
        "learned_grammar_selected_actual_programs":sum(
            x["learned_program_source"]=="INVENTED_GRAMMAR_PRODUCTION"
            for x in eligible),
        "heldout_assertions_exact_learned":sum(
            x["learned_heldout_correct"] for x in eligible),
        "heldout_assertions_possible":2*len(eligible),
        "total_learned_candidate_checks":sum(
            x["learned_candidate_checks"] for x in eligible),
        "total_cold_equal_budget_checks":sum(
            x["cold_candidate_checks"] for x in eligible),
        "source_meta_invention_ms":source["source_only_learning_ms"],
        "external_scorer_ms":round(
            (time.perf_counter_ns()-start)/1e6,4),
        "target_source_sha256":sha,
        "learned_grammar_sha256":source["frozen_production_sha256"],
    }
    result={
        "schema":SCHEMA,
        "published_original_author":"OpenAI HumanEval",
        "source_grammar_learned_FROM":"previous Google MBPP verified source programs",
        "independent_author_corpus":True,
        "public_original_test_NOT_SEALED":True,
        "no_reference_code_executed":True,
        "no_reference_solution_field_read":True,
        "no_natural_language_prompt_used":True,
        "all_original_task_outcomes_preserved":True,
        "same_base_VM_same_budget_for_memory_ablation":True,
        "first_original_test_data_downloaded_after_source_grammar_frozen":True,
        "human_meta_grammar_kernel_supplied":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "summary":summary,"rows":receipts}
    (out/"FIRST.json").write_text(
        json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("Q3_EXTERNAL_HUMANEVAL_LEARNED_GRAMMAR_FIRST",
          json.dumps(summary,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("phase",choices=("source","external"))
    ap.add_argument("--source-first",type=Path)
    ap.add_argument("--source-proof",type=Path)
    ap.add_argument("--humaneval",type=Path)
    ap.add_argument("--frozen",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--budget",type=int,default=16)
    a=ap.parse_args()
    if a.phase=="source":
        if a.source_first is None or a.source_proof is None:
            raise ValueError("MISSING_SOURCE_EVIDENCE")
        freeze_from_original_sources(a.source_first,a.source_proof,a.out)
    else:
        if a.humaneval is None or a.frozen is None:
            raise ValueError("MISSING_FROZEN_EXTERNAL_INPUTS")
        evaluate_humaneval(a.humaneval,a.frozen,a.out,a.budget)
