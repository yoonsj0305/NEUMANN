"""Postgrade exhaustive static-structure route C(5,2) *full* ablation.

FIRST original Keijzer7 + Neat5 source, pregrade neural predictions, and
original grade remain SHA-locked from CI #40067150397. This source-only
program does NOT read original true author functions. Unlike first all-five
baseline's DEDUP that may hide action-duplicate programs, execute EVERY one
of the five semantic actions on EACH true source sample separately and retain
each candidate with action provenance. Never tune the learned policy.

The second independent process reads the hidden author truth AFTER this
source-only artifact SHA is sealed and checks exact symbolic entire author
formula. 10 static two-action routes and 31 nonempty global subsets are
enumerated exactly, giving a precise conditional adaptive-vs-static routing
counterfactual on the ALREADY-OPENED original12 data.

This is NOT a new blind first original grade, nor a theorem of superiority
over all classical CONTEXTUAL selectors, nor new mathematical primitive
invention. It targets the exact bottleneck "learned adaptive action choice".
"""
import argparse,collections,hashlib,itertools,json,pathlib,time
import sympy as sp
from learned_dynamic_graph_family_2authors import ACTIONS,execute,X
SOURCE_SHA="e22b82e4cfb47fe605e1b049e01359d1752d7bbb26146d421faf08e71696ba32"
ORIGINAL_PRED_SHA="d6a0d41e5f58f50fbf563aa5d7aabe0e760bbaa63d473c5205b8f2f29bc327b0"
ORIGINAL_TRUTH_SHA="560843ae60804dc5356f1215687707f76908291bfb424210d35b9238d1f94580"
ORIGINAL_GRADE_SHA="f3ad4c51c4ef35e576e56feebdb59d8b3ad4041e0acd99737edbe0a8025e8995"
FIRST_D="D_NEURAL_TOP2_GRAPH_FAMILIES"
FIRST_A="A_ALL_SAME_GRAPH_ACTIONS"
def hash_bytes(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,obj):
    path=pathlib.Path(p);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    return hash_bytes(path)
def infer(args):
    assert hash_bytes(args.source)==SOURCE_SHA
    assert hash_bytes(args.first_pred)==ORIGINAL_PRED_SHA
    source=json.loads(pathlib.Path(args.source).read_text())["source_numeric_without_equations"]
    first=json.loads(pathlib.Path(args.first_pred).read_text())
    assert len(source)==12
    assert tuple(ACTIONS)==("POLYNOMIAL","TRIG_PRODUCT","LOG_SUM","EXP_ROOT","SAFE")
    origA={r["id"]:r for r in first["methods"][FIRST_A]["cases"]}
    assert {r["id"] for r in source}==set(origA)
    t0=time.process_time();records=[];counts=collections.Counter()
    for row in source:
        actions=[]
        if len(row.get("x",[]))==len(row.get("y",[]))==48:
            for action in ACTIONS:
                proposal,calls,nodes=execute(row,action)
                actions.append({"family":action,"source_executable_AST_candidate":proposal,
                                "source_verifier_calls":calls,
                                "program_graph_nodes":nodes})
                counts["source_verifier_calls"]+=calls
                counts["graph_nodes"]+=nodes
                counts["source_valid_macros"]+=int(proposal is not None)
        orig=origA[row["id"]]
        # This alternate first-source-only replay MUST account every action
        # and exactly reproduce total old A model's instrumented calls/nodes.
        assert sum(q["source_verifier_calls"] for q in actions)==orig["verifier_calls"],(
            "FIRST_FULL5_CLASSICAL_SOURCE_WORK_NOT_REPRODUCED",row["id"])
        assert sum(q["program_graph_nodes"] for q in actions)==orig["constructed_graph_nodes"]
        first_expressions={p["named_lambda"] for p in orig["source_valid_defined_macros"]}
        recomputed_expressions={
            q["source_executable_AST_candidate"]["named_lambda"] for q in actions
            if q["source_executable_AST_candidate"] is not None}
        assert first_expressions.issubset(recomputed_expressions),(
            "FIRST_ORIGINAL_FULL5_CANDIDATE_DROPPED",row["id"])
        records.append({"id":row["id"],
                        "input_numeric_samples":len(row.get("x",[])),
                        "per_action_UNDEDUPLICATED_source_first_programs":actions})
    assert counts["source_verifier_calls"]==7523
    assert counts["graph_nodes"]==1306
    data={"schema":"NEUMANN_Q3_POSTGRADE_ALL_5_UNDEDUPLICATED_ORIGINAL12_SOURCE_GRAPH_ACTIONS.v1",
          "first_original_source_SHA256":SOURCE_SHA,
          "first_pred_SHA256":ORIGINAL_PRED_SHA,
          "source_gold_full_author_formulas_present_in_infer":False,
          "same_existing_human_primitive_and_action_grammar":True,
          "existing_frozen_executor_not_modified":True,
          "source_first_original_A_all5_call_count_reproducible":True,
          "source_first_original_A_all5_graph_node_count_reproducible":True,
          "sampling":"EXACT first 48 public source x/y per authored task; first prior author truth is publicly opened by earlier run",
          "source_policy_test_after_original_first_grade":True,
          "per_task_source_action_replay":records,
          "counts":dict(counts),
          "source_replay_CPU_s":time.process_time()-t0,
          "G1":"HOLD","Q3":"OPEN"}
    signature=save(args.out,data)
    print("Q3_FIRST_TWO_AUTHORS_5_SOURCE_GRAPH_ACTIONS_UNDEDUPLICATED_COUNTERFACTUAL_BEFORE_THIS_GRADE",
       json.dumps({"SHA256":signature,"counts":dict(counts),
         "per_task_generated":[{"id":r["id"],
             "families":[q["family"] for q in r["per_action_UNDEDUPLICATED_source_first_programs"]
                         if q["source_executable_AST_candidate"]]} for r in records]},sort_keys=True),flush=True)
def grade(args):
    assert hash_bytes(args.truth)==ORIGINAL_TRUTH_SHA
    assert hash_bytes(args.first_grade)==ORIGINAL_GRADE_SHA
    pre=json.loads(pathlib.Path(args.pred).read_text())
    assert pre["first_original_source_SHA256"]==SOURCE_SHA
    assert pre["first_pred_SHA256"]==ORIGINAL_PRED_SHA
    original=json.loads(pathlib.Path(args.truth).read_text())["private_true_equations"]
    first=json.loads(pathlib.Path(args.first_grade).read_text())
    truth={q["id"]:q for q in original}
    assert len(truth)==12
    solved_first={
        name:{r["id"] for r in records if r["status"]=="WHOLE_REAL_AUTHOR_EXACT"}
        for name,records in first["all_original_cases"].items()
    }
    solved_actions={a:set() for a in ACTIONS};observed=[]
    xreal=sp.Symbol("x",real=True)
    for task in pre["per_task_source_action_replay"]:
        auth=truth[task["id"]]
        expected=sp.sympify(auth["author_full_expression_sympy"],
                           locals={"x":xreal}).subs(xreal,X)
        action_witnesses=[]
        for result in task["per_action_UNDEDUPLICATED_source_first_programs"]:
            p=result["source_executable_AST_candidate"]
            certified=False
            if p is not None:
                try:
                    expr=sp.sympify(p["defined_operator_AST"],locals={"x":X})
                    certified=sp.simplify(expected-expr)==0
                except Exception:pass
            if certified:solved_actions[result["family"]].add(task["id"])
            action_witnesses.append({"action":result["family"],
                "whole_author_exact":bool(certified),
                "defined_lambda":p["named_lambda"] if certified else None,
                "source_calls":result["source_verifier_calls"],
                "source_nodes":result["program_graph_nodes"]})
        observed.append({"id":task["id"],"published_original_author":auth["task_ID"],
                         "author_family":auth["collection"],
                         "per_action_entire_analytic_equivalence":action_witnesses,
                         "first_D_learned_two_actions_exact":task["id"] in solved_first[FIRST_D]})
    all_first=set.union(*solved_actions.values())
    assert all_first==solved_first[FIRST_A],("REPLAY_ALL_FIVE_GRAMMAR_FIRST_GOLD_SET_DIFFERS",
                                            sorted(all_first),sorted(solved_first[FIRST_A]))
    assert len(all_first)==5 and len(solved_first[FIRST_D])==5
    combos=[]
    for k in range(1,6):
        for subset in itertools.combinations(ACTIONS,k):
            covered=set.union(*(solved_actions[a] for a in subset))
            combos.append({"number_of_FIXED_actions":k,"FIXED_graph_families":list(subset),
                           "exact_true_author_tasks":[r["task_ID"] for r in original if r["id"] in covered],
                           "exact_true_author_count":len(covered)})
    twos=[r for r in combos if r["number_of_FIXED_actions"]==2]
    assert len(twos)==10
    best_two=max(v["exact_true_author_count"] for v in twos)
    min_actions=next(r["number_of_FIXED_actions"] for r in combos if r["exact_true_author_count"]==5)
    answer={
        "schema":"NEUMANN_Q3_TWO_AUTHOR12_POSTGRADE_EXHAUSTIVE_STATIC_ACTION_SET_COVER_EXACT.v1",
        "FIRST_4_SHA_first_source_and_grader":{
             "original_source_SHA256":SOURCE_SHA,"first_full_PRED_SHA256":ORIGINAL_PRED_SHA,
             "original_truth_SHA256":ORIGINAL_TRUTH_SHA,"first_original_full_GRADE_SHA256":ORIGINAL_GRADE_SHA},
        "counterfactual_SOURCE_FIRST_PER_ACTION_SHA256":hash_bytes(args.pred),
        "independent_recomputed_whole_author_full_function_identity":True,
        "source_executors_are_same_unmodified_original_five_grammar_modules":True,
        "source_first_full_classical_candidate_dedup_bug_eliminated":True,
        "all_31_nonempty_FIXED_action_subsets_exactly_rechecked":combos,
        "all_ten_two_action_STATIC_program_capabilities":twos,
        "best_static_two_actions_exact_full_authors":best_two,
        "smallest_FIXED_GLOBAL_grammar_action_count_covering_all_5":min_actions,
        "first_neural_adaptive_two_actions_exact_full_authors":5,
        "neural_adaptive_two_per_task_BEATS_EVERY_static_two_for_this_PUBLIC_opened_cohort":5>best_two,
        "source_action_exact_task_sets":{
          a:[r["task_ID"] for r in original if r["id"] in subset]
          for a,subset in solved_actions.items()},
        "original_independent_per_task_recheck":observed,
        "not_first_blind_public_original_after_first_grade":True,
        "not_proof_over_classical_CONTEXTUAL_adaptive_selectors":True,
        "not_including_neural_training_cost_in_action_count":True,
        "G1":"HOLD","Q3_GLOBAL":"OPEN","Q4_ALLIN10X":"NOT_PROVED"}
    digest=save(args.out,answer)
    print("Q3_EXHAUSTIVE_STATIC_TWO_VS_LEARNED_TWO_TWO_AUTHOR_ORIGINAL12_MATH",
       json.dumps({"SHA256":digest,
        "best_static_two":best_two,"learned_adaptive_two":5,
        "minimum_fixed_families_for_same_original_5":min_actions,
        "static_two_each":twos,
        "source_full_actions":answer["source_action_exact_task_sets"]},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=("infer","grade"))
    for t in ("source","first_pred","pred","truth","first_grade","out"):p.add_argument("--"+t)
    a=p.parse_args()
    if a.mode=="infer":infer(a)
    else:grade(a)
