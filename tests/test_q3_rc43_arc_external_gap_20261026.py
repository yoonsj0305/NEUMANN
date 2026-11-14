from research.q3.rc43.strict_gate import audit

def test_rc43_honest_24_external_train_tasks_recorded():
    result=audit()
    assert result["source_tasks"]==24
    assert result["opened"]==8
    assert result["heldout_training"]==2
    assert result["status"]=="RECORDED_AUDIT_NOT_PYTHON_FULL_REPLAY"

def test_limited_solver_failure_does_not_authorize_neural():
    r=audit()
    assert r["admission"]=="NOT_ADMITTED" and r["neural_calls"]==0
