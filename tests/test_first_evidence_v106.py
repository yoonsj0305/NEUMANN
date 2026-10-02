import hashlib
import pytest
from experiments.first_evidence_v106 import check_blob, verify


def test_retained_first_archives():
    assert verify()["general"] == "INCOMPLETE_0_OF_15"


def test_same_size_mutation_is_rejected():
    raw = b"first failed attempt\n"
    entry = {"path":"first", "size":len(raw),
             "sha":hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()}
    check_blob(raw,entry)
    with pytest.raises(ValueError,match="first evidence changed"):
        check_blob(b"First failed attempt\n",entry)


def test_truncation_is_rejected():
    with pytest.raises(ValueError):
        check_blob(b"",{"path":"first","size":1,"sha":"0"*40})
