"""Read-only typed motif admission on already-opened published CHC COPY originals.

A motif is a source-code candidate, not an inductive invariant or an
independently proved original CHC solution. This tool NEVER calls the model.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

PREVIOUSLY_OPENED={
    "standard_copy2_true-unreach-call_ground_000.smt2":
      {"blob":"30b3bab8834aa6f834cf493539180e6b92caf16f","bytes":6318},
    "standard_copy3_true-unreach-call_ground_000.smt2":
      {"blob":"f8fd0b73c3aa45ee5f49426416a378bcfc462605","bytes":8201},
}
RELATION_DECL=re.compile(r"\(\s*declare-fun\s+\|main@bb\d+\.i\|\s+\((.*?)\)\s+Bool\s*\)",re.S)
STORE=re.compile(r"\(\s*=\s+([A-Za-z][\w!]*)\s+\(\s*store\s+([A-Za-z][\w!]*)\s+([A-Za-z][\w!]*)\s+([A-Za-z][\w!]*)\s*\)\s*\)",re.S)
SELECT=re.compile(r"\(\s*=\s+([A-Za-z][\w!]*)\s+\(\s*select\s+([A-Za-z][\w!]*)\s+([A-Za-z][\w!]*)\s*\)\s*\)",re.S)


def gitblob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def inspect(raw:bytes,expected_blob:str,source_name:str)->dict:
    if source_name not in PREVIOUSLY_OPENED:
        raise ValueError("NOT_REGISTERED_ALREADY_OPENED_COPY_ORIGINAL")
    expected=PREVIOUSLY_OPENED[source_name]
    if expected_blob!=expected["blob"] or gitblob(raw)!=expected_blob or len(raw)!=expected["bytes"]:
        raise ValueError("ORIGINAL_COPY_PUBLISHED_SOURCE_DRIFT")
    text=raw.decode("utf8")
    # Do not select a positive based on source name. Type/motif checks use
    # only the unchanged raw source's machine-readable syntax.
    loops=[len(re.findall(r"\(Array\s+Int\s+Int\)",decl))
           for decl in RELATION_DECL.findall(text)]
    if not loops:
        raise ValueError("NO_TYPED_LOOP_PREDICATE")
    if all(n<=1 for n in loops):
        raise ValueError("NO_MULTIPLE_ARRAYS_TO_TEST_NEW_OPERATOR")
    # Each source copy may split the store and select equalities into
    # independent SMT clauses. A candidate pair is drawn ONLY when BOTH
    # occur within the same original assertion text (never across clauses).
    original_assertions=[]
    depth=0;start=None;i=0
    while i<len(text):
        ch=text[i]
        if ch=="(":
            if depth==0:start=i
            depth+=1
        elif ch==")":
            depth-=1
            if depth<0:raise ValueError("UNBALANCED_SOURCE")
            if depth==0 and start is not None:
                form=text[start:i+1]
                if re.match(r"^\(\s*assert\b",form):original_assertions.append(form)
                start=None
        i+=1
    if depth!=0:raise ValueError("UNBALANCED_SOURCE")
    motifs=[]
    for ci,form in enumerate(original_assertions):
        store_rows=[m.groups() for m in STORE.finditer(form)]
        select_rows=[m.groups() for m in SELECT.finditer(form)]
        for value_out,dst_array,dst_index,source_value in store_rows:
            for val,src_array,src_index in select_rows:
                if val!=source_value:
                    continue
                # This relation is only a syntactic candidate: indices and
                # loop cursor roles must still be proven on the original CHC.
                motifs.append({
                    "original_clause_index":ci,"destination_array":dst_array,
                    "destination_index_term":dst_index,"source_array":src_array,
                    "source_index_term":src_index,
                    "store_result_variable":value_out,
                    "source_value_variable":val,
                    "two_distinct_array_variable_names":dst_array!=src_array
                })
    return {
        "schema":"neumann.q3.copy-original-operator-gap-metadata.v1",
        "original_name":source_name,
        "original_git_blob":gitblob(raw),
        "source_sha256":hashlib.sha256(raw).hexdigest(),
        "original_bytes":len(raw),
        "loop_predicate_array_operand_counts":loops,
        "H0_requires_at_most_one_array_per_loop":True,
        "H0_type_admissible":all(n==1 for n in loops),
        "original_clause_count":len(original_assertions),
        "copy_store_select_same_original_clause_motifs":motifs,
        "copy_motif_count":len(motifs),
        "actual_original_CHC_formally_proven":False,
        "neural_model_generated_new_operator":False,
        "source_originals_already_opened_development_not_blind":True,
        "Q3":"OPEN","Q6":"OPEN",
    }


def main():
    if len(sys.argv)!=4:
        raise SystemExit("Usage: python -m research.q3.copy_original_operator_gap PATH FILENAME OUTPUT.json")
    path=Path(sys.argv[1]);name=sys.argv[2];out=Path(sys.argv[3])
    record=PREVIOUSLY_OPENED[name]
    result=inspect(path.read_bytes(),record["blob"],name)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="copy_store_select_same_original_clause_motifs"},sort_keys=True))
    if result["H0_type_admissible"] or result["copy_motif_count"]<1:
        raise SystemExit("NO_RELEVANT_COPY_MOTIF_EVIDENCE_FAIL_CLOSED")


if __name__=="__main__":
    main()
