"""Independent Z3 proof of source-generated Boolean metagrammar external FIRST.

Reuses ONLY the independent SMT-LIB original specification translator and
third-party Z3 auditor, not the researcher-designed Boolean evaluator.
The new result format is mapped into the previous verifier's immutable ledger.
"""
from __future__ import annotations
import json,pathlib
import independent_z3_causal_boolean_proof_audit as z

SOURCE="new/Q3_AUTO_LAWS_BV_CROSS_RELATION_ORIGINAL_FIRST.json"
TARGET="Q3_META_BOOLEAN_INDEPENDENT_Z3_AUDIT.json"

def main():
    original=json.loads(pathlib.Path(SOURCE).read_text())
    if original.get("source_original_run")!=42434312622:
        raise ValueError("WRONG_FIRST_SOURCE_PROVENANCE")
    targets=original["target_registry"]
    if len(targets)!=32 or original["errors"]!=0:
        raise ValueError("WRONG_FRESH_ORIGINAL_COHORT")
    rows=[]
    for row in original["rows"]:
        arms={}
        for name in ("same_language_cold","automatically_proven_invariant"):
            item=row["arms"][name]
            arms[name]={"program_ast":item["program_ast"],
                        "exact_256":item["full_256_exact"]}
        rows.append({"id":row["task_id"],
          "original_sha256":row["original_sha256"],"arms":arms})
    pathlib.Path("converted").mkdir(exist_ok=True)
    ledger="converted/original.json"
    pathlib.Path(ledger).write_text(json.dumps({"rows":rows}))
    z.LEDGERS=[(ledger,"rows",
                ("same_language_cold","automatically_proven_invariant"))]
    result=z.audit()
    pathlib.Path(TARGET).write_text(json.dumps(result,indent=2))
    assert result["summary"]["claimed_success_not_proved"]==0
    print("INDEPENDENT_CROSS_AUTHOR_META_PROGRAM_PROOFS",
          result["summary"]["independent_unsat_proofs"])
    return result

if __name__=="__main__":main()
