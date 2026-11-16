"""Authority-boundary tests for the independent verifier, not capability data."""
import copy
import importlib.util
import math
import pathlib

import pytest

PATH = pathlib.Path(__file__).resolve().parents[1] / "research/q3/independent_invention_audit.py"
SPEC = importlib.util.spec_from_file_location("independent_audit", PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def cohort():
    ids = {"rule/a", "rule/b"}
    rows = [dict(arm=a, id=i, fit=False, solved=False, program=None, cpu_seconds=1.0)
            for a in audit.ARMS for i in sorted(ids)]
    return rows, ids


def test_disjoint_equal_count_cohort_is_rejected():
    assert audit.controls()["disjoint_equal_count_cohort_rejected"]


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "extra", "missing_arm", "nan", "inf", "negative",
                                     "bool_cpu", "not_bool", "solved_without_fit", "fit_without_program"])
def test_invalid_rows_fail_before_scoring(mutation):
    rows, ids = cohort()
    if mutation == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows[0]["id"] = "rule/unregistered"
    elif mutation == "missing_arm":
        rows = [r for r in rows if r["arm"] != "S"]
    elif mutation in ("nan", "inf", "negative", "bool_cpu"):
        rows[0]["cpu_seconds"] = {"nan": math.nan, "inf": math.inf, "negative": -1, "bool_cpu": True}[mutation]
    elif mutation == "not_bool":
        rows[0]["solved"] = 0
    elif mutation == "solved_without_fit":
        rows[0]["solved"] = True
    else:
        rows[0]["fit"] = True
    with pytest.raises(ValueError):
        audit.rescore(rows, ids)


def test_valid_paired_ids_and_exact_statistics():
    rows, ids = cohort()
    assert len(audit.validate_rows(rows, ids)) == 6
    assert audit.paired_p(0, 0) == 1
    assert audit.paired_p(4, 1) == 0.375
    assert audit.paired_p(8, 1) == 0.0390625
    assert audit.paired_p(7, 0) == 0.015625
    assert not audit.rescore(rows, ids)["rule"]["pass"]


def test_interpreter_is_lazy_and_failures_stay_distinct():
    assert audit.execute(audit.parse_program("(ifI (eq 1 1) 7 (head nil))"), ()) == 7
    assert audit.execute(audit.parse_program("(head nil)"), ()) is None
    assert audit.execute(audit.parse_program("(cons 1 nil)"), ()) == (1,)
    assert audit.execute(audit.parse_program("(add 1000000000000000000 1)"), ()) is None
    assert audit.execute(audit.parse_program("(range 41)"), ()) is None
    assert audit.execute(audit.parse_program("(div 4 0)"), ()) is None


def test_independent_binders_and_traversal():
    # right-fold subtract has direction-sensitive semantics
    sol = audit.parse_program("(foldrI (sub $1 $2) 0 $0)")
    assert audit.execute(sol, ((1, 2, 3),)) == 2
    sol = audit.parse_program("(map (add $1 1) $0)")
    assert audit.execute(sol, ((3, 5),)) == (4, 6)
    sol = audit.parse_program("<zmap e=$0 j=$1 r=$2 pre=$3 suf=$4 x=$5 | (mul $0 (add $1 1))>")
    assert audit.execute(sol, ((2, 3, 4),)) == (2, 6, 12)


@pytest.mark.parametrize("text", ["(add 1", "7 8", "<rec n=$0 hist=$1 | 0>", "mystery"])
def test_unknown_or_malformed_programs_are_not_accepted(text):
    with pytest.raises(ValueError):
        audit.parse_program(text)
