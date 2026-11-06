"""Post-first mechanism diagnosis only: why a frozen Stitch macro cannot transfer.

Read-only source-level operator/skeleton comparison on ALREADY OPENED 3 corpora.
Not a new original source-blind test and not a new model/solver/proposer.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from research.exp2.stitch_real_transfer import ROOT, macro_from_stdout, parse, fileblob, h

CONTRACT = ROOT / "docs/experiments/Q3_EXP2_STITCH_CROSS_CORPUS_FIRST_PREREG_2026_11_06.json"


def all_nodes(node):
    if isinstance(node, tuple):
        yield node
        for x in node:
            yield from all_nodes(x)


def ops(node):
    return set(n[0] for n in all_nodes(node) if n and isinstance(n[0], str))


def root_skeleton(node):
    # Frozen fn0's root is (T (repeat ...) (M ...)): require these 3
    # function-call heads. Holes/arguments are unrestricted in this test.
    return (
        len(node) == 3 and node[0] == "T"
        and isinstance(node[1], tuple) and node[1][0] == "repeat"
        and isinstance(node[2], tuple) and node[2][0] == "M"
    )


def study(source_root, first_stdout):
    prereg = json.loads(CONTRACT.read_text())
    first = first_stdout.read_bytes()
    if h(first) != prereg["train_macro"]["stitch_original_stdout_sha256"]:
        raise ValueError("FROZEN_FIRST_STDOUT_IDENTITY")
    arity, pattern = macro_from_stdout(first.decode())
    required = sorted(ops(pattern))
    expected_skeleton = root_skeleton(pattern)
    if not expected_skeleton:
        raise ValueError("THIS_POSTFIRST_DIAGNOSTIC_ONLY_COVERS_FROZEN_POLYGON_TEMPLATE")
    rows = []
    for target in prereg["targets"]:
        data = (source_root / target["path"]).read_bytes()
        if fileblob(data) != target["git_blob"] or len(data) != target["bytes"]:
            raise ValueError("ORIGINAL_TARGET_DRIFT")
        programs = json.loads(data)
        counts = Counter()
        for program in programs:
            tree = parse(program)
            observed_ops = ops(tree)
            counts["programs"] += 1
            counts["contains_all_required_operators"] += int(set(required).issubset(observed_ops))
            counts["contains_polygon_math_tan"] += int("tan" in observed_ops)
            counts["contains_repeat"] += int("repeat" in observed_ops)
            counts["contains_T"] += int("T" in observed_ops)
            counts["has_three_head_root_skeleton"] += int(any(root_skeleton(x) for x in all_nodes(tree)))
            for op in required:
                counts["contains_operator_" + op] += int(op in observed_ops)
        rows.append({"source":target["path"],"original_programs":len(programs),
                     "root_skeleton_is_necessary_not_sufficient":True,
                     "counts":dict(sorted(counts.items()))})
    return {
        "schema":"neumann.exp2.stitch-postfirst-cross-corpus-structural-diagnosis.v1",
        "status":"DIAGNOSTIC_ON_OPENED_FAILED_TARGETS_ONLY",
        "independently_original_first_science":"SCOPED_CROSS_CORPUS_STATIC_MACRO_TRANSFER_FAIL",
        "first_run":42193800489, "source_macro_first_engine_run":42192798081,
        "macro_arity":arity, "required_operator_heads":required,
        "original_target_programs":sum(r["original_programs"] for r in rows),
        "all_original_source_blobs_unchanged":True,
        "new_stitch_engine_runs":0, "new_student_weights":0,
        "Q3":"OPEN", "Q6":"OPEN", "rows":rows
    }


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--first-stdout",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=study(a.source_root,a.first_stdout)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
