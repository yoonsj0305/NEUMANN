"""R0 third-domain original invariant certificates, negative and live controls."""
import shutil
import json

import pytest

from neumann1.hybrid_runtime_r0 import run
from neumann1.hybrid_sygus_r0 import prepare, independent_check

SOURCE = """(set-logic LIA)
(synth-inv inv-f ((x Int)))
(declare-primed-var x Int)
(define-fun pre-f ((x Int)) Bool (= x 0))
(define-fun trans-f ((x Int) (x! Int)) Bool (= x! (+ x 1)))
(define-fun post-f ((x Int)) Bool (>= x 0))
(inv-constraint inv-f pre-f trans-f post-f)
(check-synth)
"""


def task(source=SOURCE, **kwargs):
    return {"domain": "sygus.invariant", "source": source, "budget_s": 10, **kwargs}


def test_lossless_source_translation_and_static_contract():
    rewritten, args, definitions = prepare(SOURCE)
    assert "(declare-var x Int)" in rewritten
    assert "(declare-var x! Int)" in rewritten
    assert "declare-primed-var" not in rewritten
    assert [x[1] for x in definitions] == ["pre-f", "trans-f", "post-f"]
    assert args == [["x", "Int"]]


@pytest.mark.parametrize("bad", [
    "(set-option :produce-models true)\n" + SOURCE,
    SOURCE.replace("inv-constraint inv-f pre-f trans-f post-f",
                   "inv-constraint inv-f post-f trans-f pre-f"),
    SOURCE.replace("(synth-inv inv-f ((x Int)))", "(synth-inv inv-f ((x Real)))"),
    SOURCE.replace("(check-synth)", "(check-sat)"),
    SOURCE + '(define-fun extra () Bool true)\n',
])
def test_unsupported_source_fails_closed_without_native_calls(bad):
    r = run(task(source=bad))
    assert r["status"] == "ERROR", r
    assert r["answer"] is None
    assert not r["events"]


@pytest.mark.parametrize("candidate,expected", [
    ("(define-fun inv-f ((x Int)) Bool (>= x 0))", True),
    ("(define-fun inv-f ((x Int)) Bool true)", False),
    ("(define-fun inv-f ((x Int)) Bool (<= x 0))", False),
    ("(define-fun inv-f ((x Int)) Bool false)", False),
])
def test_independent_three_obligation_verifier(candidate, expected):
    pytest.importorskip("z3")
    _, args, defs = prepare(SOURCE)
    proof = independent_check(args, defs, candidate, timeout_ms=1200)
    assert proof["accepted"] == expected, proof
    assert len(proof["obligations"]) == 3
    if expected:
        assert [p["smt_result"] for p in proof["obligations"]] == ["unsat"]*3


def test_no_fake_cvc5_success_on_optional_dependency_absence(monkeypatch):
    import neumann1.hybrid_sygus_r0 as adapter
    def missing(*args, **kwargs):
        raise FileNotFoundError("cvc5 missing")
    monkeypatch.setattr(adapter.subprocess, "run", missing)
    r = run(task())
    assert r["answer"] is None
    assert r["status"] in ("ERROR", "UNKNOWN")
    assert r["learned_model_inference"] is False


def test_live_native_synthesis_three_original_proofs():
    pytest.importorskip("z3")
    if not shutil.which("cvc5"):
        pytest.skip("cvc5 native solver unavailable")
    r = run(task())
    assert r["status"] == "VERIFIED", json.dumps(r, indent=2, ensure_ascii=False)
    assert r["answer"]["certificate"] == "original-sygus-init-consecution-safety-v1"
    assert r["cost"]["model_calls"] == 0
    proofs = [e for e in r["events"] if e.get("kind") ==
              "independent_original_sygus_certificate"]
    assert len(proofs) == 1 and proofs[0]["passed"]
    assert all(e["smt_result"] == "unsat" for e in proofs[0]["obligations"])
    assert r["research_scope"] == "ENGINEERING_FIXTURE_ONLY_NOT_FRESH_EVIDENCE"


def test_original_checker_accepts_proven_alpha_renamed_formals():
    pytest.importorskip("z3")
    _, args, defs = prepare(SOURCE)
    proof = independent_check(args, defs,
        "(define-fun inv-f ((z Int)) Bool (>= z 0))", timeout_ms=1200)
    assert proof["accepted"], proof
    assert all(x["smt_result"] == "unsat" for x in proof["obligations"])
