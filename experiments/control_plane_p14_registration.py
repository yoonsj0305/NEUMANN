"""Model-free P1.4 preregistration and construction checks."""
import hashlib
import json
from pathlib import Path

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p13 import admissibility
from neumann1.control_plane_p14 import contract
from neumann1.general_runtime_v106 import verify_original
from experiments.control_plane_p14_catalog import catalog

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "docs/experiments/control_plane_p14.preregister.json"
PUBLIC = ROOT / "docs/experiments/control_plane_p14_public.json"
REFERENCES = ROOT / "docs/experiments/control_plane_p14_references.json"


def registration():
    reg = json.loads(REG.read_bytes())
    rows = json.loads(PUBLIC.read_bytes())["rows"]
    refs = json.loads(REFERENCES.read_bytes())["rows"]
    cat_rows, cat_refs = catalog()
    if rows != cat_rows or refs != cat_refs:
        raise ValueError("catalog/public/reference byte-content drift")
    if reg["architecture_schema"] != contract()["schema"]:
        raise ValueError("P1.4 architecture schema drift")
    if reg["task_ids"] != [r["task_id"] for r in rows] or reg["task_ids"] != [r["task_id"] for r in refs]:
        raise ValueError("P1.4 ordered coverage drift")
    if digest(rows) != reg["public_sha256"] or digest(refs) != reg["references_sha256"]:
        raise ValueError("P1.4 frozen data hash drift")
    if reg["scores_seen_at_registration"] is not False or reg["first_only"] is not True:
        raise ValueError("P1.4 first-only preregistration required")
    return reg, rows, refs


def _checker(ref):
    if ref["family"] == "math_logic":
        task = {
            "id": ref["task_id"], "family": "math_logic",
            "instruction": "Return exact.", "public": {},
        }
        return lambda candidate: verify_original(task, candidate, ref["private"], 2000)
    private = ref["private"]
    task = {
        "id": ref["task_id"], "family": "constraint_planning",
        "instruction": "Return assignment.",
        "public": {
            "domains": private["domains"],
            "constraints": private["constraints"],
        },
    }
    return lambda candidate: verify_original(task, candidate, {}, 2000)


def check_construction():
    reg, rows, refs = registration()
    raw = mixed = positives = negatives = 0
    for i, (row, ref) in enumerate(zip(rows, refs)):
        admitted = admissibility(row["view"])
        if ref["kind"] == "RAW_SEMANTIC":
            raw += 1
            if admitted["interpretation_required"] is not True or admitted["admissible_routes"] != ["DIRECT"]:
                raise ValueError("raw item must stop at P1.3 semantic interpretation")
        elif ref["kind"] == "MIXED_FALLBACK":
            mixed += 1
            if admitted["interpretation_required"] is not False or set(admitted["admissible_routes"]) != {"ARITHMETIC","CSP"}:
                raise ValueError("mixed item must expose exactly arithmetic/CSP")
        else:
            raise ValueError("unknown P1.4 kind")
        check = _checker(ref)
        if not check(ref["witness"]):
            raise ValueError("construction witness rejected")
        positives += 1
        bad = "987654321" if ref["family"] == "math_logic" else {
            k: 987654321 for k in ref["private"]["domains"]
        }
        if check(bad):
            raise ValueError("negative construction control accepted")
        negatives += 1
    if (raw, mixed) != (8, 4):
        raise ValueError("P1.4 composition drift")
    return {
        "registration_valid": True,
        "rows": len(rows),
        "raw_semantic": raw,
        "mixed_fallback": mixed,
        "positive_checker_controls": positives,
        "negative_checker_controls": negatives,
        "model_inference": False,
        "weights_loaded": False,
        "p2_registration_admitted": False,
        "decision3_admitted": False,
    }


if __name__ == "__main__":
    print(json.dumps(check_construction(), sort_keys=True))
