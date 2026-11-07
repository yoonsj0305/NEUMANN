"""Build and independently certify a parametric COPY-chain CHC invariant.

The grammar is explicitly HUMAN-DESIGNED: aligned quantified array equality,
positivity and cursor bounds. No weight training or open-ended operator creation.
But no target-specific predicate name, per-stage tuple of arguments or manually
supplied H1 interpretation is used: graph and type signatures select them.

Only two ALREADY OPENED DEVELOPMENT originals, copy2/copy3. Reserved copy4-6
and unseen originals are deliberately not accessed. Fail closed on any graph,
signature or source mutation and on any unknown checker outcome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen

from research.q3.real_copy2_chc_h1 import (
    ARR, COPY, WRONG, blob, forms, prove, sha
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/experiments/Q3_COPY_PIPELINE_AUTOGEN_OPENED_DEV_2026_11_07.json"
SCHEMA = "neumann.q3.typed-copy-chain-structural-compiler-v1"

def signatures_and_edges(source: str):
    blocks = forms(source)
    signatures = {}
    clauses = []
    for block in blocks:
        m = re.fullmatch(
            r"\(\s*declare-fun\s+\|main@([^|]+)\|\s*\((.*?)\)\s+Bool\s*\)",
            block, re.S)
        if m:
            name = m.group(1)
            if name in signatures:
                raise ValueError("DUPLICATE_DECLARATION")
            signatures[name] = re.findall(r"\(Array\s+Int\s+Int\)|Int|Bool", m.group(2))
        if re.match(r"^\(\s*assert\s+", block):
            clauses.append(block)
    if not clauses or "entry" not in signatures or "verifier.error.split" not in signatures:
        raise ValueError("MISSING_ORIGINAL_CHC_GRAPH")
    edges = {}
    for block in clauses:
        # Among recognized relation occurrences, the last in an implication
        # is the destination; preceding occurrence (if any) is its source.
        observed = re.findall(r"\|?main@([A-Za-z0-9_.]+)\|?", block)
        observed = [n for n in observed if n in signatures]
        if len(observed) == 2:
            a, b = observed
            if a != b:
                edges.setdefault(a, set()).add(b)
        elif len(observed) > 2:
            raise ValueError("MULTI_RELATION_HORN_OUTSIDE_CHAIN_GRAMMAR")
    stages = []
    here = "entry"
    while here != "verifier.error.split":
        targets = edges.get(here, set())
        if len(targets) != 1:
            raise ValueError("NONLINEAR_STAGE_GRAPH_OR_NO_EXIT")
        here = next(iter(targets))
        if here == "verifier.error.split":
            break
        if here in stages or here in ("entry",):
            raise ValueError("CYCLIC_OR_DUPLICATE_STAGE")
        stages.append(here)
        if len(stages) > 30:
            raise ValueError("STAGE_LIMIT")
    if len(stages) < 3:
        raise ValueError("NOT_A_MULTI_COPY_CHAIN")
    other = set(signatures) - {"entry", "verifier.error.split"} - set(stages)
    if other:
        raise ValueError("UNACCOUNTED_RELATION_TYPES")
    return signatures, clauses, stages


def recognize_stage_types(signatures, stages):
    # N arrays in initial stage, N loop stages. No stage-specific positions
    # from source names. Any layout mismatch means UNKNOWN, never proof.
    n = len([s for s in signatures[stages[0]] if s == ARR])
    if n != len(stages) or n < 3 or n > 12:
        raise ValueError("COPY_CHAIN_ARRAY_COUNT_STAGE_MISMATCH")
    initial = ["Int", "Int", "Int", ARR, "Int", ARR] + ["Int"] * (n-2) + ["Int"] + [ARR] * (n-2)
    if signatures[stages[0]] != initial:
        raise ValueError("FIRST_STAGE_TYPED_LAYOUT_NOT_RECOGNIZED")
    for i, name in enumerate(stages[1:], 1):
        if i == n-1:
            expected = ["Int", ARR, "Int", ARR, "Int", "Int"]
        else:
            expected = ["Int", ARR, "Int", ARR, "Int", "Int", ARR, "Int"]
            expected += sum((["Int", ARR] for _ in range(n-i-2)), [])
        if signatures[name] != expected:
            raise ValueError("MIDDLE_OR_FINAL_STAGE_TYPED_LAYOUT_MISMATCH")
    return n


def relation(dst, db, src, sb, cursor, wrong=False):
    op = "COPY_PREFIX_WRONG" if wrong else "COPY_PREFIX"
    return "(" + " ".join((op, dst, db, src, sb, cursor)) + ")"


def generated_body(stage: int, n: int, wrong: bool):
    if stage == 0:
        limit = n + 4
        base_indexes = [1, 4] + list(range(6, limit))
        checks = [f"(> x{i} 0)" for i in base_indexes+[limit]]
        checks += ["(<= 0 x2)", f"(<= x2 x{limit})"]
        checks += [relation("x3", "x1", "x5", "x4", "x2")]
    elif stage == n-1:
        checks = ["(> x0 0)", "(> x2 0)", "(> x5 0)",
                  "(<= 0 x4)", "(<= x4 x5)",
                  relation("x1", "x0", "x3", "x2", "x5")]
    else:
        # First four arguments are old and current arrays with their bases.
        # The next triple is the new array, cursor and base. Extras are
        # untouched future array/base pairs, inferred from the signature.
        extras = list(range(8, 8 + 2*(n-stage-2), 2))
        checks = [f"(> x{i} 0)" for i in [0, 2, 5, 7] + extras]
        checks += ["(<= 0 x4)", "(<= x4 x7)"]
        checks += [relation("x1", "x0", "x3", "x2", "x7")]
        checks += [relation("x6", "x5", "x3", "x2", "x4",
                            wrong=(wrong and stage==1))]
    return "(and " + " ".join(checks) + ")"


def compile_candidate(source: str, wrong: bool=False):
    signatures, clauses, stages = signatures_and_edges(source)
    n = recognize_stage_types(signatures, stages)
    declarations = []
    for stage_i, name in enumerate(stages):
        types = signatures[name]
        params = " ".join(f"(x{i} {s})" for i,s in enumerate(types))
        declarations.append(
            "(define-fun |main@" + name + "| (" + params + ") Bool " +
            generated_body(stage_i,n,wrong) + ")")
    header = "(set-logic ALL)\n" + COPY + "\n"
    if wrong:
        header += WRONG + "\n"
    header += "(define-fun |main@entry| ((x0 Int) (x1 Int)) Bool true)\n"
    header += "(define-fun |main@verifier.error.split| () Bool false)\n"
    header += "\n".join(declarations) + "\n"
    return {"prefix": header, "assertions": clauses,
            "stages": stages, "n_arrays": n, "generated_invariants": declarations}


def run(out: Path, *, network_timeout: int = 40):
    if out.exists():
        raise ValueError("NO_OVERWRITE_ORIGINAL_DEVELOPMENT_FIRST")
    manifest = json.loads(CONTRACT.read_text())
    if manifest["status"] != "OPENED_DEVELOPMENT_ONLY" or len(manifest["cases"]) != 2:
        raise ValueError("NONFROZEN_SCOPE")
    out.mkdir(parents=True)
    start = time.perf_counter_ns()
    rows = []
    for entry in manifest["cases"]:
        path = out / entry["name"]
        path.mkdir(exist_ok=False)
        repo = entry["repository"]
        upstream = (f"https://raw.githubusercontent.com/{repo}/{entry['commit']}/"
                    + entry["file"])
        with urlopen(Request(upstream,headers={"User-Agent":"NEUMANN-readonly-structural-dev"}),
                     timeout=network_timeout) as handle:
            raw = handle.read(16000)
        if len(raw) != entry["bytes"] or blob(raw) != entry["git_blob"]:
            raise ValueError("OPENED_ORIGINAL_BLOB_NOT_PINNED")
        (path / "original.smt2").write_bytes(raw)
        generated = compile_candidate(raw.decode("utf-8"))
        # Never inspect source names to select interpretation, except for
        # pre-frozen source provenance; semantics come from typed stage graph.
        proofs = prove(generated, path / "all_original_clauses", limit_s=7)
        proved = (len(proofs) == entry["assertions"] and
                  all(x["result"]=="unsat" for x in proofs))
        wrong_proofs = []
        if proved:
            mutant = compile_candidate(raw.decode("utf-8"), wrong=True)
            wrong_proofs = prove(mutant, path/"wrong_relation_control",
                                 limit_s=7, stop_at_sat=True)
        mutation_rejected = any(x["result"]=="sat" for x in wrong_proofs)
        row = {
            "case": entry["name"], "source_git_blob": blob(raw),
            "source_sha256": sha(raw), "unchanged_clauses": entry["assertions"],
            "source_stage_names": generated["stages"],
            "new_predicates_generated_without_manual_stage_program":len(generated["stages"]),
            "parametric_array_count": generated["n_arrays"],
            "original_clauses_proved_UNSAT": sum(x["result"]=="unsat" for x in proofs),
            "original_all_proved": proved,
            "wrong_operator_has_SAT_witness": mutation_rejected,
            "proof_wall_ms":round(sum(x["wall_ms"] for x in proofs),3),
            "negative_wall_ms":round(sum(x["wall_ms"] for x in wrong_proofs),3),
            "proofs": proofs, "wrong_proofs": wrong_proofs,
            "predicate_interpretations": generated["generated_invariants"]
        }
        (path / "report.json").write_text(json.dumps(row,indent=2,sort_keys=True)+"\n")
        rows.append(row)
        # Stop at first failed source instead of changing grammar after FIRST.
        if not (proved and mutation_rejected):
            break
    report = {
        "schema": SCHEMA,
        "research_scope": "TWO_ALREADY_OPENED_CHC_COMP_COPY_FAMILY_DEVELOPMENT_ORIGINALS",
        "programs_expected":2, "programs_passed":sum(
            x["original_all_proved"] and x["wrong_operator_has_SAT_witness"]
            for x in rows),
        "original_proved_clauses":sum(x["original_clauses_proved_UNSAT"] for x in rows),
        "original_expected_clauses":sum(x["unchanged_clauses"] for x in rows),
        "elapsed_total_s":round((time.perf_counter_ns()-start)/1e9,4),
        "human_designed_copy_relation_grammar":True,
        "human_supplied_specific_CHC_predicate_interpretation":False,
        "learned_model_used":False, "new_original_holdout_bodies_opened":0,
        "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
        "rows":rows
    }
    (out/"RUN_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2,sort_keys=True))
    if report["programs_passed"] != 2:
        raise RuntimeError("SOME_EXTERNAL_ORIGINAL_CHC_NOT_PROVEN_OR_NEGATIVE_NOT_DETECTED")
    return report

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    run(parser.parse_args().out)
