"""Single first-only actual original CHC source screen. NOT learned Q3 success.
Pre-source frozen target commit: 02c0b6e289cf7b27c446a665c50dfcabb20e1e73
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CORE35 = HERE.parent / "core35-20261016" / "core35.py"
ORIGINAL_REV = "e5a86a1ad252fe1df75e06814769ec1d14540032"
PREREG_COMMIT = "02c0b6e289cf7b27c446a665c50dfcabb20e1e73"
FROZEN = (
    "lists-4-inc-some2-safe.smt2",
    "prusti-3-pass-paper_examples-points-compress.smt2",
)
PER_ORIGINAL_SECONDS = 10


def load_original():
    spec = importlib.util.spec_from_file_location("core35_real_source", CORE35)
    if not spec or not spec.loader:
        raise RuntimeError("Missing CORE35 original parser")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def exact_sha(data):
    git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    return {"source_sha256": hashlib.sha256(data).hexdigest(),
            "git_blob_sha1": git_blob, "source_bytes": len(data)}


def frozen_source(filename):
    if filename not in FROZEN:
        raise ValueError("UNREGISTERED_SOURCE")
    url = f"https://raw.githubusercontent.com/chc-comp/rust-horn/{ORIGINAL_REV}/{filename}"
    copies = []
    for _ in range(2):
        with urllib.request.urlopen(url, timeout=20) as response:
            data = response.read()
        copies.append(data)
    if copies[0] != copies[1]:
        raise ValueError("TWO_FETCH_SOURCE_MISMATCH")
    raw = copies[0]
    if not raw or len(raw) > 500_000:
        raise ValueError("SOURCE_LENGTH_OUT_OF_BOUNDS")
    return raw


def run():
    o=load_original()
    receipt = {
        "experiment": "FGSR genuine original strong-classical PRE-SCREEN ONLY",
        "frozen_preregistration_commit": PREREG_COMMIT,
        "external_upstream": "chc-comp/rust-horn",
        "upstream_commit": ORIGINAL_REV,
        "source_paths": list(FROZEN),
        "z3_original_screen_only": True,
        "per_source_wall_cap_seconds": PER_ORIGINAL_SECONDS,
        "training_count": 0, "neural_calls": 0, "frontier_calls": 0,
        "Q1_Q7": "OPEN", "status": "INCOMPLETE",
        "results": [],
        "limitations": ("One native Z3 Horn original run per named external source; "
                        "a timeout is not a validated classical hard gap. "
                        "Do not claim independent model or proof, new learned structure, "
                        "frontier performance, or strongest solver comparison.")
    }
    for name in FROZEN:
        t0=time.monotonic_ns()
        record={"path":name,"status":"UNKNOWN","verdict":"NOT_RUN"}
        try:
            raw=frozen_source(name)
            record.update(exact_sha(raw))
            expr=o.top_level(raw.decode("utf-8"))
            if sum(x.startswith("(check-sat") for x in expr)!=1:
                raise ValueError("ORIGINAL_MISSING_CHECK_SAT")
            if not any(x.startswith("(set-logic ") for x in expr):
                raise ValueError("ORIGINAL_MISSING_SET_LOGIC")
            # Identical unchanged original SMT-LIB bytes and the already-vetted
            # CORE35 isolated C Z3 invocation; no certificate or lemma supplied.
            result=o.one(raw.decode("utf-8"), PER_ORIGINAL_SECONDS)
            record["verdict"]=result["verdict"]
            record["solver_only_wall_ms"]=result["wall_ms"]
            record["status"]=("SOLVER_REPORTED" if result["verdict"] in ("sat","unsat")
                              else "ABSTAIN_NO_SOLVER_PROOF")
            record["eligible_learned_case"]=False
        except Exception as exc:
            record["status"]="BLOCKED_OR_ERROR"
            record["error"]=f"{type(exc).__name__}: {str(exc)[:200]}"
        record["including_double_fetch_wall_ms"]=(time.monotonic_ns()-t0)/1e6
        receipt["results"].append(record)
    receipt["status"]=("CLASSICAL_FIRST_REAL_SOURCE_TRIAGE_COMPLETE"
                       if all(r["status"] in ("SOLVER_REPORTED","ABSTAIN_NO_SOLVER_PROOF")
                              and "source_sha256" in r for r in receipt["results"])
                       else "BLOCKED_INCOMPLETE")
    return receipt


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=pathlib.Path,required=True)
    a=p.parse_args()
    result=run()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    if result["status"]!="CLASSICAL_FIRST_REAL_SOURCE_TRIAGE_COMPLETE":
        raise SystemExit(2)

if __name__=="__main__":
    main()
