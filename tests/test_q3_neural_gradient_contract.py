"""Q3 test that neural train and infer see the identical SOURCE prompt.

These are only input/gradient-contract tests, not any claim of capability gain.
"""
import hashlib
import json

import pytest
from neumann1.q3_prompt_contract import (
    source_discovery_prompt,model_prefix,model_training_ids)
from neumann1.q3_trainable_code_policy import source_training_rows


class TinyTokenizer:
    chat_template="in-test-template"
    def apply_chat_template(self,messages,tokenize=False,
                            add_generation_prompt=False):
        assert add_generation_prompt and not tokenize
        return "<system>"+messages[0]["content"]+"<user>"+messages[1]["content"]+"<assistant>"
    def __call__(self,content,add_special_tokens=False):
        assert not add_special_tokens
        return {"input_ids":[ord(c) for c in content]}


def test_real_inference_prefix_and_training_mask_are_identical():
    tok=TinyTokenizer()
    observed=[([3,5],8),([4,6],10)]
    prompt=source_discovery_prompt(observed)
    prefix=model_prefix(tok,prompt)
    program="def transform(x):\n    return sum(x)"
    tokens,labels=model_training_ids(
        tok,prompt,program,max_length=10000)
    expected=tok(prefix)["input_ids"]
    assert tokens[:len(expected)]==expected
    assert labels[:len(expected)]==[-100]*len(expected)
    assert labels[len(expected):]==tokens[len(expected):]
    assert "Source input: [3, 5]" in prompt
    assert "Expected source output: 8" in prompt


def test_truncated_teacher_refuses_to_train():
    tok=TinyTokenizer()
    with pytest.raises(ValueError,match="truncate"):
        model_training_ids(
            tok,source_discovery_prompt([(1,2)]),
            "def transform(x): return x",max_length=8)


def test_verified_teacher_source_integrity(tmp_path):
    prog="def transform(x):\n    return sum(x)"
    teacher={
        "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
        "provenance":"ORIGINAL_SOURCE_ONLY",
        "pairs":[[[1,2],3],[[2,3],5]],
        "program":prog,"sha256":hashlib.sha256(prog.encode()).hexdigest(),
        "independent_checks":1,
    }
    file=tmp_path/"source.jsonl"
    file.write_text(json.dumps(teacher)+"\n")
    rows,sha=source_training_rows(file)
    assert len(rows)==1 and len(sha)==64
    teacher["sha256"]="bad"
    file.write_text(json.dumps(teacher)+"\n")
    with pytest.raises(ValueError,match="tampered"):
        source_training_rows(file)
