"""Synthetic P1.12 runtime path tests: NEVER actual pretrained model evidence."""
import copy
import pytest

from experiments.control_plane_p112_catalog import catalog
from experiments.control_plane_p112_runtime import (
    IDS, evaluate, run_item, totals, _raw_top_candidate,
)
from experiments.control_plane_p112_registration import GATE, COUNTS


class FixtureCrossEncoder:
    def __init__(self, winner=None, ties=False, fail_after_forward=False):
        self.winner=winner
        self.ties=ties
        self.fail_after_forward=fail_after_forward
        self.forward_calls=0
        self.last_attempt=None

    def score(self, ir):
        n=len(ir["pairs"])
        self.forward_calls+=1
        self.last_attempt={"forward_calls":1,"input_rows":n,
                           "input_tokens":5*n,"padded_tokens":8*n}
        if self.fail_after_forward:
            raise RuntimeError("synthetic P1.12 attempted forward failure")
        if self.ties:
            logits=[1.0]*n
        else:
            logits=[0.0]*n
            logits[self.winner]=4.5
        return {"logits":logits,"forward_calls":1,
                "input_rows":n,"input_tokens":5*n,"padded_tokens":8*n,
                "device":"cpu-test-only","tokenize_ms":0.1,
                "forward_ms":0.1,"logit_extract_ms":0.1}


def test_all_twelve_synthetic_correct_route_and_original_verification():
    rows,refs=catalog()
    receipts=[]
    for row,ref in zip(rows,refs):
        encoder=FixtureCrossEncoder(winner=ref["expected_candidate"])
        rec=run_item(row,ref,encoder)
        assert rec["status"]=="ACCEPTED",rec.get("error")
        assert rec["accepted"] is True
        assert rec["selected_candidate"]==ref["expected_candidate"]
        assert rec["raw_top_candidate"]==ref["expected_candidate"]
        assert rec["model_calls"]==1
        assert rec["neural_forward_calls"]==1
        assert rec["generated_calls"]==0
        assert rec["selector_complete"] is True
        assert rec["tool_calls"]==rec["verifier_calls"]==1
        assert rec["lexical_baseline"]["unique_selection"] is None
        receipts.append(rec)

    assert [r["task_id"] for r in receipts]==list(IDS)
    verdict=evaluate(receipts,refs,True,True,1000.0)
    assert verdict["verdict"]=="PASS"
    assert verdict["reason"]=="OPENED_P112_CROSS_ENCODER_DIAGNOSTIC_ONLY"
    assert verdict["accepted"]==12
    assert verdict["raw_top_correct"]==12
    assert verdict["path_cost"]["neural_forward_calls"]==12
    assert verdict["path_cost"]["feasibility_calls"]==35


def test_wrong_raw_ranking_is_independently_rejected_without_retry():
    rows,refs=catalog()
    ref=refs[0]
    wrong=1-ref["expected_candidate"]
    rec=run_item(rows[0],ref,FixtureCrossEncoder(winner=wrong))
    assert rec["status"]=="REJECTED_BY_ORIGINAL_VERIFIER"
    assert rec["executed"] is True
    assert rec["accepted"] is False
    assert rec["selected_candidate"]==wrong
    assert rec["tool_calls"]==rec["verifier_calls"]==1


def test_exact_tie_abstains_with_complete_selection_cost():
    rows,refs=catalog()
    rec=run_item(rows[0],refs[0],FixtureCrossEncoder(ties=True))
    assert rec["status"]=="SEMANTIC_ABSTAINED"
    assert rec["selected_candidate"] is None
    assert rec["selector_complete"] is True
    assert rec["model_calls"]==1 and rec["neural_forward_calls"]==1
    assert rec["tool_calls"]==0 and rec["verifier_calls"]==0
    assert rec["accounting_complete"] is True


def test_partial_attempt_is_costed_and_not_admitted():
    rows,refs=catalog()
    rec=run_item(rows[0],refs[0],FixtureCrossEncoder(fail_after_forward=True))
    assert rec["status"]=="FAILED"
    assert rec["accounting_complete"] is True
    assert rec["model_calls"]==1
    assert rec["neural_forward_calls"]==1
    assert rec["input_rows"]==2
    assert rec["input_tokens"]==10
    assert rec["padded_tokens"]==16
    assert rec["selector_complete"] is False
    assert rec["selector_partial_receipt"]["forward_calls"]==1


def test_evaluator_rejects_cost_or_identity_drift():
    rows,refs=catalog()
    receipts=[
        run_item(row,ref,FixtureCrossEncoder(winner=ref["expected_candidate"]))
        for row,ref in zip(rows,refs)
    ]
    assert evaluate(receipts,refs,False,True,1000)["verdict"]=="NOT_EVALUATED"
    assert evaluate(receipts,refs,True,False,1000)["verdict"]=="NOT_EVALUATED"
    assert evaluate(receipts,refs,True,True,GATE["whole_study_wall_ms"]+1)["reason"]=="COMPLETE_COST_WALL_CAP"
    altered=copy.deepcopy(receipts)
    altered[2]["neural_forward_calls"]=2
    assert evaluate(altered,refs,True,True,1000)["reason"]=="CONTROL_WORK_ACCOUNTING_FAILURE"
    altered=copy.deepcopy(receipts)
    altered[0]["accepted"]=False
    altered[1]["accepted"]=False
    altered[2]["accepted"]=False
    altered[3]["accepted"]=False
    assert evaluate(altered,refs,True,True,1000)["reason"]=="P112_SEMANTIC_CAPABILITY_FAILURE"


def test_raw_top_uses_joint_pair_identity():
    ir={"target_role":"target","pairs":[
        {"entity":"X","query":"Target function: target","candidate_text":"Candidate role: first"},
        {"entity":"Y","query":"Target function: target","candidate_text":"Candidate role: second"}]}
    assert _raw_top_candidate(ir,[0.2,0.9],{"X":0,"Y":1})==1
