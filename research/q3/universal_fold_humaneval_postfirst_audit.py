"""Q3 post-first broader HumanEval interface diagnosis using SAME original data.

Important: all 164 OpenAI HumanEval task IDs were exposed by #715 original
FIRST. This is a DEV-EXPOSED retrospective only, never a second independent
benchmark first or global Q3 PASS. No original reference code or prompt used.
"""
from __future__ import annotations
import argparse,ast,gzip,hashlib,json,time
from pathlib import Path
from collections import Counter
from research.q3.universal_typed_state_fold_postfirst import synthesis,run,same

OFFICIAL_SHA256="b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"

def parse_literal_case(assertnode):
    if not isinstance(assertnode,ast.Assert):raise ValueError("NON_ASSERT")
    compare=assertnode.test
    if (not isinstance(compare,ast.Compare) or len(compare.ops)!=1 or
            not isinstance(compare.ops[0],ast.Eq) or
            len(compare.comparators)!=1):
        raise ValueError("NON_LITERAL_EQUALITY")
    call=compare.left
    if (not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name)
            or call.func.id!="candidate" or len(call.args)!=1
            or call.keywords):
        raise ValueError("NON_DIRECT_CALL")
    try:
        arg=ast.literal_eval(call.args[0])
        goal=ast.literal_eval(compare.comparators[0])
    except (TypeError,SyntaxError,ValueError,MemoryError):
        raise ValueError("UNSAFE_OR_DYNAMIC_EXPRESSION")
    if type(arg) not in (list,tuple,str) or \
       type(goal) not in (str,list,tuple,int,float,bool):
        raise ValueError("UNSUPPORTED_TYPED_FUNCTION")
    if len(arg)>1024 or (type(goal) in (str,list,tuple) and len(goal)>1024):
        raise ValueError("RESOURCE_LIMIT")
    if any(type(x) not in (str,int,float,bool) for x in arg):
        raise ValueError("UNSUPPORTED_INPUT_ELEMENT")
    return [arg],goal

def extract_any(test_source):
    astroot=ast.parse(test_source)
    func=[x for x in astroot.body
          if isinstance(x,ast.FunctionDef) and x.name=="check"]
    if len(func)!=1 or len(func[0].args.args)!=1 or \
       func[0].args.args[0].arg!="candidate":
        raise ValueError("NO_STANDARD_CHECK")
    statements=func[0].body
    if not 4<=len(statements)<=200:
        raise ValueError("NOT_ENOUGH_AUTHOR_TESTS")
    cases=[parse_literal_case(x) for x in statements]
    return cases

def evaluate(source:Path,out:Path,budget=5000):
    if out.exists():raise ValueError("IMMUTABLE_POSTFIRST_NO_OVERWRITE")
    out.mkdir(parents=True)
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    if sha!=OFFICIAL_SHA256:raise ValueError("OFFICIAL_HUMANEVAL_SHA_CHANGED")
    with gzip.open(source,"rt",encoding="utf8") as stream:
        dataset=[json.loads(line) for line in stream if line.strip()]
    if len(dataset)!=164:raise ValueError("NOT_164_ORIGINALS")
    records=[]
    t0=time.perf_counter_ns()
    for row in dataset:
        ident=row.get("task_id")
        receipt={"id":ident,"source_reference_code_UNREAD":True,
                 "source_natural_language_prompt_UNREAD":True,
                 "original_test_indices":"all-but-last-two TRAIN, last-two TEST",
                 "status":"UNSET"}
        try:
            examples=extract_any(row["test"])
            train=examples[:-2]
            tests=examples[-2:]
            born=synthesis(train,budget)
            marks=[born["program"] is not None and
                   same(run(born["program"],args),y) for args,y in tests]
            receipt.update({
                "status":"EXACT" if all(marks) else
                        "WRONG_OR_ABSTAIN",
                "source_input_type":type(train[0][0][0]).__name__,
                "source_output_type":type(train[0][1]).__name__,
                "training_original_count":len(train),
                "heldout_original_count":len(tests),
                "generic_generated_AST":born["program"],
                "source_program_status":born["status"],
                "attempts":born["attempts"],
                "source_ms":born.get("wall_ms"),
                "two_original_tests_exact":all(marks),
                "two_original_tests_correct":sum(marks)})
            if all(marks):
                print("Q3_GENERIC_TYPE_REPR_DEV_EXACT",ident,
                      receipt["source_input_type"],"->",
                      receipt["source_output_type"],
                      "AST",born["program"],"checked",born["attempts"],
                      flush=True)
        except (ValueError,KeyError,IndexError,TypeError,
                SyntaxError,MemoryError,OverflowError,RecursionError) as e:
            receipt.update({"status":"UNSUPPORTED",
                            "reason":(type(e).__name__+":"+str(e))[:200],
                            "heldout_original_count":0,
                            "two_original_tests_exact":False,
                            "two_original_tests_correct":0})
        records.append(receipt)
    eligible=[r for r in records if r.get("heldout_original_count")==2]
    summary={
        "original_HumanEval_program_tasks":164,
        "eligible_under_new_generic_type_interface":len(eligible),
        "unsupported":164-len(eligible),
        "exact_two_original_tests":sum(r["two_original_tests_exact"]
                                        for r in eligible),
        "exact_individual_tests":sum(r["two_original_tests_correct"]
                                     for r in eligible),
        "tested_individual_tests":2*len(eligible),
        "previous_strict_interface_eligible":14,
        "previous_exact_two_original_tests":0,
        "eligible_type_transitions":dict(Counter(
            f'{r["source_input_type"]}->{r["source_output_type"]}'
            for r in eligible)),
        "total_attempted_ASTs":sum(r["attempts"] for r in eligible),
        "full_scoring_ms":round((time.perf_counter_ns()-t0)/1e6,4),
        "same_author_originals_previously_exposed":True,
        "experimental_not_original_FIRST":True,
    }
    result={
        "schema":"neumann.q3.generic_type_fold_humaneval_postfirst.v1",
        "original_first_run_humaneval":42361601013,
        "original_reference_source_sha256":sha,
        "postfirst_DEVELOPMENT_ONLY":True,
        "human_authored_generic_state_update_grammar":True,
        "human_authored_generic_fold_VM":True,
        "no_reference_code_executed_or_read":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "summary":summary,"rows":records}
    (out/"POSTFIRST.json").write_text(json.dumps(
        result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print("Q3_TYPE_INTERFACE_POSTFIRST_DEV",json.dumps(
        summary,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--humaneval",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--budget",type=int,default=5000)
    a=p.parse_args()
    evaluate(a.humaneval,a.out,a.budget)
