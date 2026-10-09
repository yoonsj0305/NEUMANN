"""R0 engineering proof that the *old* frozen Q34 checkpoints run in new wrapper.

Opened 2026-10-09 historical v102 original views, not novel data, not admission.
Never trains, renames, regenerates, mutates or chooses samples after scoring.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import torch

from experiments.lp_expand4_holdout_register_v102 import load_registered
from experiments.lp_expand4_holdout_v102 import raw_source, SOURCE_MANIFEST
from neumann1.hybrid_runtime_r0 import run
from neumann1.lp_expand4_holdout_archive_v102 import load_first_evaluation
from experiments.lp_frozen_support_expansion_v101 import frozen_ranking
from neumann1 import hybrid_runtime_r0 as runtime

OUTPUT = Path("research/development/hybrid_r0_first_slice_20261009/frozen_q34_smoke.json")
HISTORICAL = "docs/experiments/results/v102_first_evaluation.manifest.json"


def main():
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    source_manifest, sources = load_registered(SOURCE_MANIFEST)
    historic = load_first_evaluation(HISTORICAL)
    historical = {(row["case_id"], row["route"]): row for row in historic["records"]
                  if row["repeat"] == 0}
    selected = {}
    for group in ("m64_base", "m128_base"):
        source = next(s for s in sources["sources"] if s["group"] == group)
        selected[group] = source
    records = []
    for group, source in selected.items():
        raw = raw_source(source)
        plain = {k: v.tolist() for k,v in raw.items()}
        for policy in ("native", "residual_fixed4m", "frozen_q34"):
            task = {"domain": "lp.standard_form", **plain,
                    "policy": policy, "budget_s": 10.0}
            if policy == "frozen_q34":
                task["seed"] = 100001
            result = run(task)
            if result["status"] != "VERIFIED":
                raise RuntimeError(f"Hybrid original certification failed: {group}, {policy}: {result}")
            if result["answer"]["certificate"] != "neumann.lp-standard-form-certificate.v1":
                raise RuntimeError("Original LP independent verifier absent")
            if policy == "frozen_q34":
                if result["cost"]["model_calls"] != 1:
                    raise RuntimeError("Frozen model didn't actually execute")
                if result["cost"]["offline_training_investment_ms"] == "UNKNOWN":
                    raise RuntimeError("Historical paid training accounting missing")
                models, _training = runtime._FROZEN_Q34_CACHE
                ranking, _ = frozen_ranking(raw, models[100001])
                old = historical[(source["id"], "EXPAND4_s100001")]["ranking"]
                if ranking != old:
                    raise RuntimeError("Frozen ranking historical identity drift")
            elif result["cost"]["model_calls"] != 0:
                raise RuntimeError("Native route unexpectedly called a model")
            records.append({
                "case_id": source["id"], "group": group, "policy": policy,
                "original_problem_sha256": result["original_task_sha256"],
                "status": result["status"],
                "cost": result["cost"], "events": result["events"],
                "original_certificate": result["answer"]["certificate"],
                "historic_opened": True,
            })
            print(json.dumps({"case":source["id"],"policy":policy,
                  "status":result["status"],"wall_ms":round(result["cost"]["observed_wall_ms"],3)},
                  sort_keys=True),flush=True)
    if len(records) != 6:
        raise AssertionError("expected exactly two original Q34 cases with three routes each")
    report = {"schema": "neumann.hybrid-r0-frozen-smoke.v1",
              "scope": "OPENED_ENGINEERING_ONLY",
              "sources_original_count": 2,
              "observations": len(records),
              "original_v102_source_sha256": source_manifest["gzip_sha256"],
              "no_training": True, "new_neural_architecture": False,
              "q1_to_q7_closed": [], "records": records}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print("HYBRID_R0_FROZEN_Q34_VERIFIED=" +
          json.dumps({"observations": len(records),
                      "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
