"""Self-generated world interface tests; fixtures are NOT research teachers."""
import json
import pytest
from neumann1.open_program_inventor import IsolatedPython
from research.q3.q3_selfplay_worlds import (
    KINDS,SCHEMA,canonical,make_json_inputs,sha)
from research.q3.q3_selfplay_train import validate_worlds


@pytest.mark.parametrize("kind",KINDS)
def test_bounded_json_inputs_are_diverse_and_reproducible(kind):
    first=make_json_inputs(kind,1142,n=6)
    assert first==make_json_inputs(kind,1142,n=6)
    assert len(first)==len({canonical(x) for x in first})==6


def test_model_generated_only_teacher_must_be_independently_executable(tmp_path):
    runner=IsolatedPython(max_seconds=8)
    source_codes=(
        "def transform(x):\n    return x*3",
        "def transform(x):\n    return x+5",
    )
    rows=[]
    for i,code in enumerate(source_codes):
        inputs=make_json_inputs("integer",100+i,n=6)
        evaluated=runner.evaluate(code,inputs)
        assert evaluated.status=="EXECUTED"
        rows.append({
            "schema":SCHEMA,"world_id":sha(code),
            "program":code,"program_sha256":sha(code),
            "authorship":"FROZEN_PRETRAINED_MODEL_GENERATED",
            "source_train":list(zip(inputs[:3],evaluated.outputs[:3])),
            "source_sealed_check":list(zip(inputs[3:5],evaluated.outputs[3:5])),
            "synthetic_test":list(zip(inputs[5:],evaluated.outputs[5:])),
            "all_labels_from_isolated_execution":True,
            "original_author_target_gold_read":False,
        })
    path=tmp_path/"worlds.jsonl"
    path.write_text("".join(canonical(w)+"\n" for w in rows))
    accepted,digest=validate_worlds(path,runner)
    assert len(accepted)==2 and len(digest)==64
    rows[0]["synthetic_test"][-1][-1]=888888
    path.write_text("".join(canonical(w)+"\n" for w in rows))
    with pytest.raises(ValueError,match="failed real executor"):
        validate_worlds(path,runner)


def test_no_domain_specific_target_program_in_world_generator():
    import inspect
    import research.q3.q3_selfplay_worlds as mod
    src=inspect.getsource(mod)
    assert "synthesize_relational_grid" not in src
    assert "arc_" not in src.lower()
    assert "TARGET_gold" not in src
