"""Opened M106 negative-transfer *engineering* fixture for Hybrid R0.

Confirms original LP certification and fallback cannot silently become weaker.
No new models, data generation, oracle labels, fresh scientific results or gates.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import torch

from neumann1.q5_evidence import unpack_case
from experiments.q5_transfer_admission import decode_source
from neumann1.hybrid_runtime_r0 import run

DIR = Path("docs/experiments/results/m106_bp_transfer_first")
OUT = Path("research/development/hybrid_r0_first_slice_20261009/bp_negative_smoke.json")
CASES = ("m106_bp_k8_r0", "m106_bp_k16_r0")


def main():
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    source_list = json.loads((DIR / "sources.json").read_text())
    entries = {entry["metadata"]["id"]: entry for entry in source_list["cases"]}
    if len(entries) != 16 or set(CASES) - set(entries):
        raise RuntimeError("Historic opened M106 source registry drift")
    records = []
    for case_id in CASES:
        entry = entries[case_id]
        source = unpack_case(DIR, entry["identity"])  # checks frozen SHA and length.
        if set(source) != {"metadata", "arrays", "input_sha256"}:
            raise RuntimeError("M106 oracle label contamination")
        raw = decode_source(source, entry["metadata"])
        source_shas = {
            "gzip_sha256": entry["identity"]["gzip_sha256"],
            "input_sha256": source["input_sha256"],
        }
        for policy in ("native", "residual_fixed4m", "frozen_q34"):
            task = {"domain": "lp.standard_form",
                    **{k: v.tolist() for k, v in raw.items()},
                    "policy": policy, "budget_s": 10.0}
            if policy == "frozen_q34":
                task["seed"] = 100001
            result = run(task)
            # Native is known capable in original M106. On learned transfer
            # non-acceptance is allowed but must fail closed.
            if policy == "native" and result["status"] != "VERIFIED":
                raise RuntimeError("Original native capability regression: " + str(result))
            if result["status"] == "VERIFIED":
                if (result["answer"]["certificate"] != "neumann.lp-standard-form-certificate.v1"
                        or not result["events"][-1]["passed"]):
                    raise RuntimeError("Uncertified answer admitted")
            elif result["answer"] is not None:
                raise RuntimeError("Uncertified answer leaked")
            if policy == "frozen_q34" and result["cost"]["model_calls"] != 1:
                raise RuntimeError("Frozen learned transfer route did not execute model")
            records.append({
                "case_id":case_id, "policy":policy, "source_shas":source_shas,
                "status":result["status"], "answer_admitted":result["answer"] is not None,
                "events":result["events"], "cost":result["cost"],
                "opened_only":True,
            })
            print(json.dumps({"case":case_id,"policy":policy,
                              "status":result["status"],
                              "total_ms":round(result["cost"]["observed_wall_ms"],3)},
                              sort_keys=True), flush=True)
    if len(records) != 6:
        raise AssertionError("missing BP negative fixture")
    report = {"schema":"neumann.hybrid-r0-m106-negtransfer-fixture.v1",
              "historical_originals":len(CASES),"records":records,
              "new_training":False,"original_verifier_weakened":False,
              "fresh_scientific_admission":False,"global_questions_closed":[]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("HYBRID_R0_BP_NEGATIVE=" + json.dumps({
        "cases":len(CASES),"observations":len(records),
        "sha256":hashlib.sha256(OUT.read_bytes()).hexdigest()},sort_keys=True))


if __name__ == "__main__":
    main()
