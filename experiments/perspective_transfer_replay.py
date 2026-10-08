"""Audit the first transfer screen, including partial worker failures."""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from experiments.perspective_transfer_headroom import changed_problem, summarize
from experiments.contraction_kernel_calibration import agreement
from neumann1.contraction_structure import certify_path


def replay(preparation, first, output):
    import numpy as np
    import opt_einsum as oe
    from threadpoolctl import threadpool_limits
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    assert digest(preparation / "preregister.json") == json.loads((preparation / "freeze-receipt.json").read_text())["contract_sha256"]
    receipt = json.loads((preparation / "first-result-receipt.json").read_text(encoding="utf-8"))
    assert digest(first / "report.json") == receipt["report_sha256"] and digest(first / "manifest.json") == receipt["manifest_sha256"]
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert all(digest(first / p) == pin for p, pin in manifest.items())
    assert all(digest(ROOT / p) == pin and digest(preparation / "source" / p) == pin for p, pin in reg["sources"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    assert digest(Path(reg["catalog"])) == reg["catalog_sha256"]
    report = json.loads((first / "report.json").read_text(encoding="utf-8"))
    events = json.loads((first / "events.json").read_text(encoding="utf-8"))
    cases, observations, numerical = [], [], 0
    paths, failed, options_checked = 0, [], 0
    with threadpool_limits(limits=1):
        for identifier in reg["source_ids"]:
            source = Path(reg["source_root"]) / (identifier + ".json")
            assert digest(source) == reg["source_pins"][identifier]
            original = json.loads(source.read_text(encoding="utf-8"))
            for mode in reg["modes"]:
                case = json.loads((first / "cases" / (identifier + "_" + mode.lower() + ".json")).read_text(encoding="utf-8"))
                regenerated, lineage = changed_problem(original["public"], mode, case["seed"])
                assert case["public"] == regenerated and case["lineage"] == json.loads(json.dumps(lineage))
                assert case["offline_original_paths"] == original["supplied_paths"]
                cases.append(case)
                folder = first / case["id"]
                batch_arrays = []
                for q in range(2):
                    with np.load(folder / f"inputs_{q}.npz", allow_pickle=False) as arrays:
                        batch = [arrays[f"t{i}"] for i in range(len(regenerated["shapes"]))]
                    assert all(a.dtype == np.float64 and np.array_equal(a, np.random.default_rng(case["seed"] + q * 10000 + i).uniform(.98, 1.02, s)) for i, (a, s) in enumerate(zip(batch, regenerated["shapes"])))
                    batch_arrays.append(batch)
                case_rows = [json.loads(line) for line in (folder / "observations.jsonl").read_text(encoding="utf-8").splitlines()]
                observations.extend(case_rows)
                event = next(e for e in events if e["id"] == case["id"])
                if event.get("exit_code") != 0:
                    # No score or unobserved path/capability estimate is fabricated.
                    failed.append({"case_id": case["id"], "exit_code": event.get("exit_code"),
                        "captured_query_rows": sum(r.get("kind") == "query" for r in case_rows),
                        "inputs_preserved": 2, "offline_trace_available": (folder / "offline-options.json").exists()})
                    continue
                offline = json.loads((folder / "offline-options.json").read_text(encoding="utf-8"))
                choices = offline["options"]
                for option in choices:
                    assert certify_path(regenerated, option["path"]) == option["certificate"]
                    assert option["certificate"]["dense_arithmetic_work_model"] <= reg["budget"]["modeled_work"]
                    assert option["certificate"]["largest_intermediate_elements"] <= reg["budget"]["peak_elements"]
                    options_checked += 1
                assert offline["selected"] == min(choices, key=lambda o: (o["certificate"]["dense_arithmetic_work_model"], o["certificate"]["largest_intermediate_elements"]))
                refs = []
                for q, batch in enumerate(batch_arrays):
                    with np.load(folder / f"reference_{q}.npz", allow_pickle=False) as stored:
                        expected, second = stored["expected"], stored["second"]
                    assert agreement(expected, second, reg["rtol"])
                    independently = np.asarray(oe.contract(regenerated["equation"], *batch, optimize=[tuple(s) for s in choices[1]["path"]], backend="numpy"))
                    assert agreement(expected, independently, reg["rtol"])
                    refs.append(expected)
                for row in case_rows:
                    if row.get("kind") != "query":
                        continue
                    if "path" in row:
                        check = certify_path(regenerated, row["path"])
                        assert check == row["certificate"]
                        paths += 1
                    if row["status"] == "RESOURCE_MODEL_REJECTED":
                        assert check["dense_arithmetic_work_model"] > reg["budget"]["modeled_work"] or check["largest_intermediate_elements"] > reg["budget"]["peak_elements"]
                    if row["status"] != "ACCEPTED":
                        continue
                    if row["route"] == "FREE_STRUCTURE":
                        assert row["path"] == offline["selected"]["path"] and row["oracle_used"]
                    for q, batch in enumerate(batch_arrays):
                        with np.load(folder / f"witness_{row['repetition']}_{row['route']}_{q}.npz", allow_pickle=False) as stored:
                            witness = stored["actual"]
                        actual = np.asarray(oe.contract(regenerated["equation"], *batch, optimize=[tuple(s) for s in row["path"]], backend="numpy"))
                        assert row["queries"][q]["accepted"] and agreement(witness, refs[q], reg["rtol"]) and agreement(actual, witness, reg["rtol"])
                        numerical += 1
                    setup = row["discovery_certificate_seconds"] + row["compile_seconds"]
                    assert math.isclose(row["first_query_seconds"], setup + row["queries"][0]["query_seconds"], abs_tol=1e-9)
                    assert math.isclose(row["two_query_seconds"], setup + sum(q["query_seconds"] for q in row["queries"]), abs_tol=1e-9)
    reconstructed = summarize(cases, observations, events, reg)
    assert all(report[k] == v for k, v in reconstructed.items())
    assert not report["G1_admitted"] and report["fresh_eligible"] == 0
    output.mkdir(parents=True, exist_ok=False)
    save(output / "replay.json", {"status": "PASS_RETAINED_COMPLETE_AND_FAILED_EVIDENCE",
        "manifest_files_checked": len(manifest), "cases_reconstructed": len(cases), "path_certificates_rechecked": paths,
        "offline_candidate_certificates_checked": options_checked, "numeric_witnesses_reexecuted": numerical,
        "failed_workers_preserved": failed, "report_reconstructed_without_retuning": True,
        "report_sha256": digest(first / "report.json"), "manifest_sha256": digest(first / "manifest.json"),
        "original_external_dataset_answers_claimed": False, "G1_admitted": False})
    print((output / "replay.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    replay(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
