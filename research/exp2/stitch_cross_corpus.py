"""Frozen first Stitch macro -> three separately authored-corpus tasks, no learner rerun.

Source targets registered by Git blobs *before* opening any target body.
The independent AST matcher never imports the upstream Stitch engine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from research.exp2.stitch_real_transfer import (
    ROOT, fileblob, h, parse, replace_macro, expand, mutate_nonhole,
    macro_from_stdout, canonical
)

PRE = ROOT / "docs/experiments/Q3_EXP2_STITCH_CROSS_CORPUS_FIRST_PREREG_2026_11_06.json"


def run(source_root: Path, original_first_stdout: Path, destination: Path):
    pre = json.loads(PRE.read_text())
    original = original_first_stdout.read_bytes()
    if h(original) != pre["train_macro"]["stitch_original_stdout_sha256"]:
        raise ValueError("IMMUTABLE_FIRST_STITCH_STDOUT_CHANGED")
    arity, macro = macro_from_stdout(original.decode("utf8"))
    wrong = mutate_nonhole(macro)
    if wrong is None:
        raise ValueError("MUTATION_UNAVAILABLE")
    rows = []
    for target in pre["targets"]:
        data = (source_root / target["path"]).read_bytes()
        if len(data) != target["bytes"] or fileblob(data) != target["git_blob"]:
            raise ValueError("FROZEN_EXTERNAL_TARGET_GIT_BLOB_CHANGED_" + target["path"])
        programs = json.loads(data)
        if type(programs) is not list or not programs or not all(type(s) is str for s in programs):
            raise ValueError("INVALID_EXTERNAL_ORIGINAL_PROGRAMS_" + target["path"])
        sites = 0
        hits = 0
        for source in programs:
            tree = parse(source)
            compact, found = replace_macro(tree, macro, arity)
            if expand(compact, macro, arity) != tree:
                raise ValueError("ORIGINAL_AST_RECONSTRUCTION_FAILED")
            if found:
                hits += 1
                sites += found
                if expand(compact, wrong, arity) == tree:
                    raise ValueError("WRONG_MACRO_NOT_REFUTED")
        rows.append({
            "source_file": target["path"],
            "original_git_blob": fileblob(data),
            "source_sha256": h(data),
            "original_program_count": len(programs),
            "programs_with_frozen_training_macro": hits,
            "total_nonoverlapping_macro_match_sites": sites,
            "all_original_ASTs_reexpanded_exactly": True,
            "incorrect_macro_refuted_when_reused": True if hits else "NOT_APPLICABLE_NO_MATCH"
        })
    passed = sum(row["programs_with_frozen_training_macro"] > 0 for row in rows) >= 2
    outcome = {
        "schema": "neumann.exp2.stitch-real-three-source-readonly-transfer-first.v1",
        "scientific_status": ("SCOPED_CROSS_CORPUS_STATIC_MACRO_TRANSFER_PASS"
                              if passed else "SCOPED_CROSS_CORPUS_STATIC_MACRO_TRANSFER_FAIL"),
        "training_macro_frozen_first_sha256": h(original),
        "upstream_commit": pre["train_macro"]["upstream_commit"],
        "macro_arity": arity, "macro_body": canonical(macro),
        "original_target_corpora": len(rows),
        "original_target_programs": sum(r["original_program_count"] for r in rows),
        "macro_reuse_target_corpora": sum(r["programs_with_frozen_training_macro"] > 0 for r in rows),
        "macro_reuse_target_programs": sum(r["programs_with_frozen_training_macro"] for r in rows),
        "macro_reuse_total_sites": sum(r["total_nonoverlapping_macro_match_sites"] for r in rows),
        "independent_exact_expansion": True,
        "wrong_macro_negative_control": True,
        "source_original_heldout_first": True,
        "training_programs_reopened": False,
        "Stitch_engine_reruns": 0, "own_weight_model_training": False,
        "Q3": "OPEN", "Q4": "OPEN", "Q6": "OPEN", "Q7": "OPEN",
        "rows": rows
    }
    destination.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    return outcome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--first-stdout", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    result = run(a.source_root, a.first_stdout, a.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["scientific_status"].endswith("_PASS"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
