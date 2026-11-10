"""Q3 test that neural train and infer see the identical SOURCE prompt.

These are only input/gradient-contract tests, not any claim of capability gain.
"""
import hashlib
import json

import pytest
from neumann1.q3_prompt_contract import (
    source_discovery_prompt,model_prefix,model_training_ids)
from neumann1.q3_trainable_code_policy import (
    source_training_rows, recertify_source_rows)


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
    program="def transform(x):" + chr(10) + "    return x + 1"
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


def test_neural_training_requires_reexecuted_independent_source_teachers():
    from types import SimpleNamespace
    from neumann1.open_program_inventor import UnsafeProposal
    class Runner:
        def evaluate(self,code,inputs):
            return SimpleNamespace(status="EXECUTED",
                                   outputs=tuple(x+1 for x in inputs))
    program="def transform(x):" + chr(10) + "    return x + 1"
    teacher={
        "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
        "provenance":"ORIGINAL_SOURCE_ONLY",
        "original_id":"external-author-source-1",
        "pairs":[[i,i+1] for i in range(7)],
        "independent_checks":1,
        "program":program,
        "sha256":hashlib.sha256(program.encode()).hexdigest()
    }
    receipts=recertify_source_rows([teacher],runner=Runner())
    assert len(receipts)==1 and len(receipts[0])==64
    false_teacher=dict(teacher)
    false_teacher["pairs"]=[list(p) for p in teacher["pairs"]]
    false_teacher["pairs"][-1][1]=999
    with pytest.raises(UnsafeProposal,match="SOURCE-certified"):
        recertify_source_rows([false_teacher],runner=Runner())
    class AbsentSandbox:
        def evaluate(self,code,inputs):
            return SimpleNamespace(status="ABSTAIN_NO_SANDBOX",outputs=())
    with pytest.raises(UnsafeProposal,match="SOURCE-certified"):
        recertify_source_rows([teacher],runner=AbsentSandbox())


def test_neural_inference_preserves_last_source_error_or_refuses_context():
    from neumann1.q3_prompt_contract import (
        require_full_source_context,SourceContextOverflow)
    class Tokenizer:
        def __call__(self,rendered,*,add_special_tokens=False,
                     truncation=False):
            assert truncation is False
            assert add_special_tokens is False
            return {"input_ids":[ord(c) for c in rendered]}
    tok=Tokenizer()
    prompt="SOURCE_EXAMPLES\nPREVIOUS_WRONG_PROGRAM\nLATEST_CAUSAL_WITNESS"
    assert len(require_full_source_context(
        tok,prompt,max_tokens=128))==len(prompt)
    huge=prompt+"X"*150
    with pytest.raises(SourceContextOverflow,match="no observations discarded"):
        require_full_source_context(tok,huge,max_tokens=128)
