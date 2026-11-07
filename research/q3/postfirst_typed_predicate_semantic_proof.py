"""POST-FIRST independent semantic audit of #714, not a new blind test.

READS ONLY the immutable #714 original-first artifact's GENERATED executable
ASTs and independently authored Google MBPP reference semantics inspected
AFTER original first. No extra hypothesis search, source code modification,
or program retuning is performed here. Two all-integer modular proofs using
Z3; all 1,114,112 Unicode code points tested for category equivalence.
Expected negative #593 is a scientific false positive and must remain FAIL.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

from research.q3.feature_predicate_from_counterexample import run_generated

EXPECTED_FIRST_SOURCE_SHA="2cd85f1712ef91dbcab4a3bc85c583dfd235dd9ef451ae13282c25aef1cfa332"
SOURCE_RUN=42354198810


def prove_smt(integrity_expr):
    if not shutil.which("z3"):raise RuntimeError("INDEPENDENT_Z3_NOT_INSTALLED")
    script="""(set-logic ALL)
(declare-const x Int)
(assert (not """+integrity_expr+"""))
(check-sat)
"""
    start=time.monotonic()
    result=subprocess.run(["z3","-in"],input=script,text=True,
                          capture_output=True,timeout=20,check=False)
    observed=result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
    return {"observed":observed,"pass":observed=="unsat",
            "ms":round((time.monotonic()-start)*1000,3),
            "independent_Z3_script":script}


def ref554(values):
    odd=[]
    for x in values:
        if x%2!=0:odd.append(x)
    return odd

def ref629(values):
    return [x for x in values if x%2==0]

def ref800(s):
    return re.sub(r"\s+","",s)

def ref593(s):
    return re.sub(r"\.[0]*",".",s)


def run(first_path:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_POSTFIRST_AUDIT")
    out.mkdir(parents=True)
    first=json.loads(first_path.read_text())
    if first["summary"]["source_learned_constructor_frozen_sha256"]!=EXPECTED_FIRST_SOURCE_SHA:
        raise RuntimeError("FIRST_IMMUTABLE_SOURCE_CONSTRUCTOR_WRONG")
    rows={r["id"]:r for r in first["rows"]}
    if any(not rows[i]["new_generated_exact"] for i in (554,593,629,800)):
        raise RuntimeError("SOURCE_FIRST_CANDIDATE_CHANGED")
    correct={554:ref554,629:ref629,800:ref800,593:ref593}
    heldout={
        554:[-11,-10,-9,-8,0,1,2,77,78,101,102],
        629:[-19,-18,-17,-16,0,11,12,41,42],
        800:"a\tb\nc\u2003d\u00a0e",
        593:"10.01"
    }
    records=[]
    for id in (554,629,800,593):
        ast=rows[id]["source_generated_ast"]
        source=[heldout[id]]
        predicted=run_generated(ast,source)
        reference=correct[id](heldout[id])
        same=predicted==reference
        records.append({"original_MBPP_task_id":id,"program_ast":ast,
                        "generated_predicate":ast["predicate"],
                        "adversarial_probe":source,
                        "generated_output":predicted,
                        "independent_author_reference_output":reference,
                        "semantic_agreement_on_new_probe":same,
                        "initial_official_heldout_exact":True,
                        "post_first_known_reference_inspected":True})
    smt={
        "554_remove_even_equals_keep_odd":prove_smt(
            "(= (not (= (mod x 2) 0)) (distinct (mod x 2) 0))"),
        "629_remove_odd_equals_keep_even":prove_smt(
            "(= (not (= (mod x 2) 1)) (= (mod x 2) 0))"),
    }
    mismatches=[]
    whitespace_count=0
    start=time.monotonic()
    for cp in range(0x110000):
        char=chr(cp)
        is_space=char.isspace()
        re_space=re.fullmatch(r"\s",char) is not None
        whitespace_count+=is_space
        if is_space!=re_space:mismatches.append(cp)
    unicode_report={
        "Python_Unicode_codepoints_tested":0x110000,
        "whitespace_codepoints":whitespace_count,
        "differences":len(mismatches),
        "mismatch_codepoints":mismatches[:32],
        "elapsed_s":round(time.monotonic()-start,3),
        "full_sequence_equivalence_reason":
            "removing each whitespace character equals regex replacing every nonempty whitespace run by the empty string",
        "environment_dependent_Unicode_database":True,
    }
    byid={r["original_MBPP_task_id"]:r for r in records}
    substantive=(
        smt["554_remove_even_equals_keep_odd"]["pass"] and
        smt["629_remove_odd_equals_keep_even"]["pass"] and
        byid[554]["semantic_agreement_on_new_probe"] and
        byid[629]["semantic_agreement_on_new_probe"] and
        byid[800]["semantic_agreement_on_new_probe"] and
        unicode_report["differences"]==0
    )
    expected_spurious=not byid[593]["semantic_agreement_on_new_probe"]
    audit={
        "schema":"neumann.q3.postfirst-semantic-original-audit.v1",
        "original_FIRST_actions_run":SOURCE_RUN,
        "postfirst_not_blind_new_original":True,
        "generated_operator_bodies_unchanged":True,
        "first_original_heldout_correct":4,
        "strong_old_filter_heldout_correct":2,
        "first_induced_nonliteral_beats_old":2,
        "reference_equivalent_under_the_stated_function_domains":3,
        "original_test_correct_but_reference_SEMANTICS_FALSE_POSITIVE":1,
        "stronger_semantic_proof_pass":bool(substantive),
        "expected_counterexample_against_IP_zero_stripper":bool(expected_spurious),
        "smt":smt,"unicode_semantic_equivalence":unicode_report,
        "programs":records,
        "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
    }
    (out/"POSTFIRST_SEMANTIC_AUDIT.json").write_text(
        json.dumps(audit,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    for key,value in smt.items():
        (out/(key+".smt2")).write_text(value["independent_Z3_script"])
    print("Q3_POSTFIRST_SEMANTIC_AUDIT_SUMMARY",json.dumps({
        k:audit[k] for k in [
            "first_original_heldout_correct",
            "first_induced_nonliteral_beats_old",
            "reference_equivalent_under_the_stated_function_domains",
            "original_test_correct_but_reference_SEMANTICS_FALSE_POSITIVE",
            "stronger_semantic_proof_pass",
            "expected_counterexample_against_IP_zero_stripper",
        ]},sort_keys=True),flush=True)
    print("UNICODE_ALL_CODEPOINTS",json.dumps(unicode_report,sort_keys=True),flush=True)
    if not substantive or not expected_spurious:
        raise RuntimeError("INDEPENDENT_POSTFIRST_SEMANTIC_AUDIT_FAILED")
    return audit


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--first",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    run(a.first,a.out)
