"""SOURCE-certified meta-learning from self-generated failed executable methods.

Only tests provenance and causal information flow, NOT original Q3 success.
"""
import hashlib
import json
import pytest

from neumann1.open_program_inventor import (
    IsolatedPython,validate_code,Execution)
from neumann1.q3_trainable_code_policy import certified_source_memory
from neumann1.q3_refutation_learning import source_refutation_episodes

INC="def transform(x):"+chr(10)+"    return x + 1"
REV="def transform(x):"+chr(10)+"    return x[::-1]"


def teacher(pid,code,pairs):
    return {
        "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
        "provenance":"ORIGINAL_SOURCE_ONLY",
        "original_id":pid,
        "pairs":pairs,
        "independent_checks":1,
        "program":code,
        "sha256":hashlib.sha256(code.encode()).hexdigest(),
    }


def examples():
    return [
        teacher(7,INC,[[i,i+1] for i in (1,2,3,4,5,6,9)]),
        teacher(8,REV,[[x,x[::-1]] for x in (
            "abcd","wxyz","neumann","structural","proof","open","xyz")])
    ]


def test_real_source_counterexamples_generate_code_repair_training_pairs():
    runner=IsolatedPython(max_seconds=8)
    rows=examples()
    memory=certified_source_memory(rows,runner=runner)
    episodes=source_refutation_episodes(rows,memory,runner,max_per_teacher=2)
    assert len(episodes)>=2
    origins={e["original_source_id"] for e in episodes}
    assert origins=={"source-teacher/7","source-teacher/8"}
    for e in episodes:
        assert e["source_only"] is True
        assert "SOURCE-ONLY REPAIR EPISODE" in e["prompt"]
        assert e["negative_program"] in e["prompt"]
        assert e["program"] not in e["prompt"]  # correct self program is excluded
        assert e["negative_sha256"]!=hashlib.sha256(
            e["program"].encode()).hexdigest()
        assert validate_code(e["negative_program"])
        assert "Original-semantics SOURCE feedback:" in e["prompt"]
        # Independently replay the mutant as a SOURCE hypothesis: it MUST
        # fail at least one originally observed SOURCE pair.
        relevant=rows[0] if e["original_source_id"].endswith("/7") else rows[1]
        out=runner.evaluate(
            e["negative_program"],
            [x for x,y in relevant["pairs"]])
        assert out.status in ("EXECUTED","EXECUTED_WITH_ERRORS")
        assert any(got!=y or err is not None
                   for got,err,(_,y) in zip(
                       out.outputs,out.errors,relevant["pairs"]))
        assert len(e["witness_sha256"])==64


def test_refutation_teacher_cannot_use_failed_or_missing_sandbox():
    class Unavailable:
        def evaluate(self,code,inputs):
            return Execution("ABSTAIN_NO_SANDBOX",(),0)
    rows=examples()
    memory=certified_source_memory(
        rows,runner=IsolatedPython(max_seconds=8))
    assert source_refutation_episodes(
        rows,memory,Unavailable())==[]


def test_refutation_teacher_never_sees_target_gold_sentinel():
    runner=IsolatedPython(max_seconds=8)
    rows=examples()
    memory=certified_source_memory(rows,runner=runner)
    episodes=source_refutation_episodes(rows,memory,runner)
    assert episodes
    assert "TARGET outputs are UNKNOWN" in episodes[0]["prompt"]
    assert "987654321" not in json.dumps(episodes)



def test_actual_model_pilot_unwraps_coreoutcome_without_loading_neural_weights(
        tmp_path,monkeypatch):
    """Prevent a 10-minute SOURCE model run from failing on an API wrapper."""
    from research.q3 import q3_source_refutation_pilot as pilot

    identity="def transform(x):"+chr(10)+"    return x"
    class FakeSandbox:
        def __init__(self,*args,**kwargs):pass
        def evaluate(self,code,inputs):
            if code==INC:
                outputs=tuple(x+1 for x in inputs)
            elif code==REV:
                outputs=tuple(x[::-1] for x in inputs)
            elif code==identity:
                outputs=tuple(inputs)
            else:
                return Execution("ABSTAIN_UNSAFE_SYNTAX",(),0)
            return Execution("EXECUTED",outputs,0,(None,)*len(inputs))
    class FakePolicy:
        def __init__(self,**kwargs):pass
        def propose(self,prompt):return identity
    monkeypatch.setattr(pilot,"IsolatedPython",FakeSandbox)
    monkeypatch.setattr(pilot,"LocalCausalCodePolicy",FakePolicy)
    rows=examples()
    teacher_path=tmp_path/"teachers.jsonl"
    teacher_path.write_text("".join(json.dumps(x)+"\n" for x in rows))
    blind_path=tmp_path/"blind.json"
    blind_path.write_text(json.dumps({
       "schema":"NEUMANN.Q3.NEURAL.CODEARC.BLIND.v1",
       "records":[{
           "id":task,
           "source":[[x,x] for x in range(start,start+7)],
           "target_inputs":[start+7,start+8,start+9]}
           for task,start in ((184,10),(255,100))]}))
    out=tmp_path/"results.json"
    pilot.run(str(blind_path),str(teacher_path),
              "fake-repair-adapter","fake-context-adapter",
              "frozen-model-revision",str(out))
    result=json.loads(out.read_text())
    assert result["original_target_gold_seen"] is False
    assert result["pretrained_memory_correct_source"]==2
    assert result["contextual_imitation_10step_correct_source"]==2
    assert result["source_refutation_10step_correct_source"]==2
    assert all(x["arms"]["C"]["source_verified"]
               for x in result["records"])
    assert all(
        x["arms"]["C"]["original_target_predictions"]
        == [i for i in range((10 if x["id"]==184 else 100)+7,
                             (10 if x["id"]==184 else 100)+10)]
        for x in result["records"])



def test_original_author_gold_only_available_after_frozen_prediction_hash(tmp_path):
    from research.q3.q3_postfirst_repair_original_score import score
    import hashlib
    rows=[]
    for pid in (184,255):
        for index in range(10):
            rows.append({"type":"annotated","problem_id":pid,
                         "index":index,"output":"Result "+str(index)+": "+str(index)})
    original=tmp_path/"author_original.jsonl"
    original.write_text("".join(json.dumps(x)+"\n" for x in rows))
    predictions={
        "schema":"NEUMANN.Q3.SOURCE-REPAIR-PILOT.v1",
        "original_target_gold_seen":False,
        "model_scientific_scope":"PREEXPOSED_CODEARC_DEV_ONLY",
        "records":[{
            "id":pid,"arms":{
                k:{"source_verified":True,
                   "original_target_predictions":([7,8,9] if k=="C" else [])}
                for k in ("A","B","C")}
        } for pid in (184,255)]}
    frozen=tmp_path/"frozen.json"
    frozen.write_text(json.dumps(predictions))
    expected=hashlib.sha256(frozen.read_bytes()).hexdigest()
    summary=score(str(original),str(frozen),expected,str(tmp_path/"score.json"))
    assert summary["repair_curriculum_equal_step_exact"]==2
    assert summary["C_only_vs_B"]==2
    assert summary["global_q3"]=="OPEN"
    assert not summary["novel_original_independent_first"]
    with pytest.raises(ValueError,match="frozen"):
        score(str(original),str(frozen),"0"*64,str(tmp_path/"other.json"))
