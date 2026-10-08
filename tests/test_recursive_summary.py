from copy import deepcopy
import pytest
from experiments.recursive_summary_cases import lifted_prefix,tree
from neumann1.recursive_summary import (CertifiedSummary,SummaryError,check_summary,program,reference,validate_program)
from neumann1.synduce_reference import reference_projection


def test_new_auxiliary_state_is_certified_and_preserves_ordered_goal():
    problem,proposal=lifted_prefix()
    certificate=check_summary(problem,proposal)
    assert certificate["accepted"] and len(certificate["obligations"])==9
    engine=CertifiedSummary(problem,proposal)
    for values in [[],[-5,4],[4,-5],[2,-8,9,-1],[-3,-2],[10**40,-10**40,7]]:
        for shape in ["left","right","balanced"]:
            assert engine.run(tree(values,shape))==reference(problem,values)


def test_wrong_order_summary_has_a_counterexample():
    problem,proposal=lifted_prefix()
    proposal["merge"]["outputs"][0]=["max","r0",["add","r1","l0"]]
    result=check_summary(problem,proposal)
    assert result["status"]=="REFUTED" and result["obligations"][-1]["counterexample"]
    with pytest.raises(SummaryError):CertifiedSummary(problem,proposal)


def test_deleting_sufficient_state_is_not_authorized():
    problem,_=lifted_prefix()
    proposal={"empty":[0],"step":program(["head","z0"],[["max",["add","head","z0"],0]]),
              "merge":program(["l0","r0"],[["max","l0","r0"]]),"decode":program(["z0"],["z0"]),
              "invariant":program(["z0"],[["ge","z0",0]])}
    assert check_summary(problem,proposal)["status"]=="REFUTED"


def test_vacuous_invariant_cannot_create_proof():
    problem,proposal=lifted_prefix()
    proposal["invariant"]["outputs"]=[False]
    result=check_summary(problem,proposal)
    assert result["status"]=="REFUTED" and result["obligations"][-1]["obligation"]=="INITIAL_VALID"


def test_solver_resource_unknown_blocks_execution():
    problem,proposal=lifted_prefix()
    result=check_summary(problem,proposal,resource_limit=1)
    assert not result["accepted"] and result["status"]=="UNKNOWN"


def test_false_empty_value_and_goal_change_rejected():
    problem,proposal=lifted_prefix()
    proposal["empty"]=[1,0]
    assert not check_summary(problem,proposal)["accepted"]
    proposal=lifted_prefix()[1]
    proposal["decode"]["outputs"]=["z1"]
    assert not check_summary(problem,proposal)["accepted"]


def test_payload_is_typed_and_has_no_executable_constructor():
    for outputs in [[["mul","x","x"]],[["add",True,"x"]],["undeclared"],[["eval","x"]]]:
        with pytest.raises(SummaryError):validate_program(program(["x"],outputs))
    problem,proposal=lifted_prefix()
    proposal["accepted"]=True
    assert check_summary(problem,proposal)["status"]=="BAD_PROPOSAL"


def test_tree_budget_and_noninteger_payload_blocked():
    p,s=lifted_prefix();engine=CertifiedSummary(p,s)
    for malformed in [["single",True],["single",1.5],["other"],["concat",["nil"]]]:
        with pytest.raises(SummaryError):engine.run(malformed)
    with pytest.raises(SummaryError):engine.run(tree([1,2,3],"left"),max_nodes=2)


def test_source_copy_and_certificate_binding():
    p,s=lifted_prefix();engine=CertifiedSummary(p,s)
    s["decode"]["outputs"]=["z1"]
    assert engine.run(tree([-5,4],"left"))==[0]
    engine._proposal["decode"]["outputs"]=["z1"]
    with pytest.raises(SummaryError):engine.run(["nil"])


def test_expression_budget_and_recursive_inputs_blocked():
    expr=["add",0,0]
    expr[1]=expr
    with pytest.raises(SummaryError):validate_program(program([],[expr]))


def test_parser_extracts_tuple_fold_and_ignores_no_semantics():
    source="""let rec f = function | Nil -> 0, 0 | Cons (hd, tl) ->
    let p, s = f tl in let t = s + hd in max p t, t ;;"""
    public=reference_projection(source)
    assert reference(public,[1,-9,3])==[3,-5]
    assert reference(public,[])==[0,0]


def test_parser_rejects_unsupported_reference_operations():
    for op in ["hd * sum tl","other tl","if hd > 0 then hd else 0"]:
        source="let rec sum = function | Nil -> 0 | Cons (hd, tl) -> "+op+" ;;"
        with pytest.raises(SummaryError):reference_projection(source)


def test_parser_nested_comments_and_unterminated_comments():
    source="(* outer (* inner *) done *) let rec sum = function | Nil -> 0 | Cons (hd, tl) -> hd + sum tl ;;"
    assert reference(reference_projection(source),[1,-3,5])==[3]
    with pytest.raises(SummaryError):reference_projection(source+"(*")
