"""First Hybrid R0 cold frozen Q34 adapter execution, opened engineering-only."""
from __future__ import annotations
import json
from pathlib import Path
from experiments.lp_expand4_holdout_register_v102 import load_registered
from experiments.lp_expand4_holdout_v102 import SOURCE_MANIFEST, raw_source
from neumann1.hybrid_runtime_r0 import run

out = Path("research/development/hybrid_r0_first_slice")
out.mkdir(parents=True, exist_ok=True)
_manifest, cohort = load_registered(SOURCE_MANIFEST)
source = cohort["sources"][0]
raw = raw_source(source)
base = {"domain": "lp.standard_form",
        "A": raw["A"].tolist(), "b": raw["b"].tolist(), "c": raw["c"].tolist(),
        "budget_s": 15.0}
records = []
for name, opts in (("native", {"policy": "native"}),
                   ("classical_fixed4m", {"policy": "residual_fixed4m"}),
                   ("frozen_q34_seed100001", {"policy": "frozen_q34", "seed": 100001})):
    r = run({**base, **opts})
    records.append({"route": name, "original_case": source["id"],
                    "original_source_sha256": source["sha256"],
                    "receipt": r})
    print("R0_ROUTE=" + json.dumps({"route": name, "status": r["status"],
          "measured_total_ms": r["cost"]["observed_wall_ms"],
          "model_calls": r["cost"]["model_calls"],
          "original_accepted": r["status"] == "VERIFIED"}), flush=True)

data = {"classification": "ENGINEERING_OPENED_SMOKE_ONLY",
        "cases": 1, "route_count": len(records), "records": records,
        "original_v102_unchanged": True, "no_new_training": True,
        "note": "cold restore is charged for frozen Q34, so speed comparisons with historical warm averages are INVALID"}
(out / "opened_q34_three_route_smoke.json").write_text(json.dumps(data, sort_keys=True, indent=2)+"\n")
if len(records) != 3 or not all(x["receipt"]["status"] == "VERIFIED" for x in records):
    raise RuntimeError("Hybrid R0 frozen adapter not admitted; all first receipts retained")
if records[-1]["receipt"]["cost"]["model_calls"] != 1:
    raise RuntimeError("Frozen model inference accounting missing")
