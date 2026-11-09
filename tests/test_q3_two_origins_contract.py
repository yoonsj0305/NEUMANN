"""Scientific gate mechanics only. Does NOT constitute Q3 invention proof."""
import hashlib
import json
from pathlib import Path
import pytest

from neumann1.open_program_inventor import Execution, UnsafeProposal
from neumann1.q3_trainable_code_policy import (
    certified_source_memory, contextual_training_prompt)
from neumann1.q3_single_discovery_core import SourceMethodMemory
from research.q3.q3_two_origins_preregistered import (
    SIZES,prepare,score,sha,file_sha)


INC="def transform(x):" + chr(10) + "    return x + 1"
REV="def transform(x):" + chr(10) + "    return x[::-1]"


class Runner:
    def evaluate(self,code,inputs):
        if code==INC:
            values=tuple(x+1 for x in inputs)
        elif code==REV:
            values=tuple(x[::-1] for x in inputs)
        else:
            return Execution("ABSTAIN_UNSAFE_SYNTAX",(),0)
        return Execution("EXECUTED",values,0,(None,)*len(inputs))


def row(original_id,program,items):
    return {"schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
            "provenance":"ORIGINAL_SOURCE_ONLY",
            "original_id":original_id,
            "pairs":items,
            "independent_checks":1,
            "program":program,
            "sha256":hashlib.sha256(program.encode()).hexdigest()}


def test_same_methods_recertified_before_meta_training():
    prior=[
        row(111,INC,[[1,2],[2,3],[3,4]]),
        row(222,REV,[["ABC","CBA"],["dog","god"],["cat","tac"]])
    ]
    memory=certified_source_memory(prior,runner=Runner())
    assert memory.frozen and len(memory.episodes)==2
    first=contextual_training_prompt(prior[0],memory)
    second=contextual_training_prompt(prior[1],memory)
    assert REV in first and INC not in first
    assert INC in second and REV not in second
    assert "Expected source output" in first
    from neumann1.q3_prompt_contract import source_discovery_prompt
    context=memory.context(
        excluded_ids=("source-teacher/111",),
        max_methods=2,max_chars_per_method=320)
    assert first==source_discovery_prompt(prior[0]["pairs"][:6],
                                           method_context=context)


def test_bad_teacher_cannot_become_learned_method():
    invalid=row(111,INC,[[1,2],[2,3],[3,999]])
    with pytest.raises(UnsafeProposal,match="SOURCE-certified"):
        certified_source_memory([invalid],runner=Runner())
    one=row(111,INC,[[1,2],[2,3]])
    memory=certified_source_memory([one],runner=Runner())
    with pytest.raises(ValueError,match="disjoint method"):
        contextual_training_prompt(one,memory)


def _task(i):
    # The external original dataset is NOT this fixture; we only validate
    # that task TEST output cannot enter the blind generation payload.
    return {"train":[
       {"input":[[i]],"output":[[i+1]]},
       {"input":[[i+2]],"output":[[i+3]]},
       {"input":[[i+4]],"output":[[i+5]]}],
       "test":[{"input":[[i+6]],"output":[[99999]]}]}


def test_arcana_original_gold_hidden_until_frozen_score(tmp_path):
    root=tmp_path/"real_external"
    root.mkdir()
    for i in range(6):
        (root/f"author_{i}.json").write_text(json.dumps(_task(i)))
    blind=tmp_path/"BLIND.json"
    prepare("arcana",str(root),str(blind))
    contract=json.loads(blind.read_text())
    assert contract["task_count"]==SIZES["arcana"]
    assert "99999" not in blind.read_text()
    assert not any("test" in rec for rec in contract["records"])
    pred={"schema":"NEUMANN.Q3.TWO-ORIGIN.PREDICTIONS.v1",
          "origin":"arcana","blind_sha256":file_sha(blind),
          "records":[]}
    for rec in contract["records"]:
        pred["records"].append({
            "id":rec["id"],
            "native":[],
            "arms":{
                k:{"source_pass":True,
                   "program_sha256":str(k),
                   "target_predictions":[[[99999]]] if k=="C" else []}
                for k in ("A","B","C")}})
    frozen=tmp_path/"PREDICTIONS.json"
    frozen.write_text(json.dumps(pred))
    out=tmp_path/"SCORE.json"
    score("arcana",str(root),str(blind),str(frozen),file_sha(frozen),str(out))
    result=json.loads(out.read_text())["summary"]
    assert result["n"]==4
    assert result["C_only"]==4 and result["B"]==0
    assert result["native_specialist_checked"]
    with pytest.raises(ValueError,match="freeze"):
        score("arcana",str(root),str(blind),str(frozen),
              "0"*64,str(out))


def test_never_use_dev_original_in_arcana_registry(tmp_path):
    root=tmp_path/"sample"
    root.mkdir()
    for i in range(5):
        (root/f"c{i}.json").write_text(json.dumps(_task(i)))
    (root/"archimedes1.json").write_text(json.dumps(_task(3)))
    blind=tmp_path/"blind.json"
    prepare("arcana",str(root),str(blind))
    data=json.loads(blind.read_text())
    assert "archimedes1.json" not in {t["id"] for t in data["records"]}
    assert len(data["records"])==4
