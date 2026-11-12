"""Post-freeze validation controls; no receiver TEST and no inference changes."""
from __future__ import annotations
from collections import defaultdict
import copy
import json
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q6"))
from reference import execute
from source_study import OUT, fold
from neumann1.q6.contracts import Artifact, digest, seal_artifact
from neumann1.q6.transport import tup


def main():
    path = OUT / "negative_controls_complete.json"
    if path.exists():
        raise SystemExit("preserve first negative-control receipt")
    c0 = time.process_time()
    artifacts = json.loads((OUT / "source_artifacts.json").read_text())
    trusted = {a["artifact_id"] for a in artifacts}
    groups = defaultdict(list)
    for a in artifacts:
        m = a["executable_method"]
        groups[(m["kind"], tuple(m["input_types"]), tuple(m["state_types"]), m["output_type"])].append(a)
    rng = random.Random(745)
    records, unchanged = [], 0
    for group in groups.values():
        perm = group.copy()
        rng.shuffle(perm)
        for old, other in zip(group, perm):
            if digest(old["executable_method"]) == digest(other["executable_method"]):
                unchanged += 1
                continue
            for reseal_proof in (False, True):
                wrong = copy.deepcopy(old)
                wrong["executable_method"] = other["executable_method"]
                if reseal_proof:
                    wrong["source_verification"]["method_digest"] = digest(wrong["executable_method"])
                wrong = seal_artifact(wrong)
                try:
                    Artifact.admit(wrong, lambda d: d["artifact_id"] in trusted)
                except ValueError as e:
                    records.append({"source": old["provenance"]["source_id"], "shuffled_with": other["provenance"]["source_id"],
                                    "proof_also_forged": reseal_proof, "rejected": True, "reason": str(e)})
                else:
                    records.append({"rejected": False})
    # Real, type-compatible source procedures under a frozen identity binding.
    # Construct known negative controls using authorized receiver TRAIN only.
    visible = json.loads((ROOT.parent / "q6_source_v1_train_cache.json").read_text())
    relations = []
    for t in visible:
        for a in artifacts:
            if fold(a["provenance"]["source_id"]) == fold(t["id"]):
                continue
            m = a["executable_method"]
            if m["input_types"] != t["in_types"] or m["output_type"] != t["out_type"]:
                continue
            sol = m["kind"], tup(m["ast"])
            bad = [j for j, (i, o) in enumerate(t["train"]) if execute(sol, tup(i)) != tup(o)]
            if bad:
                relations.append({"receiver": t["id"], "source": a["provenance"]["source_id"],
                                  "types_agree": True, "frozen_relation_rejected_on_TRAIN": True,
                                  "counterexample_index": bad[0]})
            if len(relations) >= 16:
                break
        if len(relations) >= 16:
            break
    undefined = []
    for a in artifacts:
        m = a["executable_method"]
        if m["kind"] == "ast" and "head" in str(m["ast"]) and execute((m["kind"], tup(m["ast"])), ((),)) is None:
            undefined.append(a["provenance"]["source_id"])
    r = {"scope": "negative validation controls only, not transfer capability", "seed": 745,
         "shuffled_controls": records, "unchanged_digest_not_a_negative_control": unchanged,
         "all_changed_source_controls_rejected": bool(records) and all(x["rejected"] for x in records),
         "same_type_wrong_relation_controls": relations, "undefined_source_domain_probes": undefined,
         "receiver_TEST_read": False, "cpu_seconds": time.process_time() - c0,
         "other_controls": {"names_only_replay": "tests/q6/test_transport.py",
                            "no_map_ablation": "main C-no-map arm", "extra_budget": "main BudgetOnly arm",
                            "whole_program_replay": "main B arm"}}
    path.write_text(json.dumps(r, indent=2) + "\n")
    print({k: v for k, v in r.items() if k not in ("shuffled_controls", "same_type_wrong_relation_controls")})


if __name__ == "__main__":
    main()
