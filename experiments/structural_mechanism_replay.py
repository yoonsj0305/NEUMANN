"""External pins, original programs, negative controls and tensor-path replay."""
import json
from pathlib import Path
import sys
from time import perf_counter
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.representation_headroom import digest, package_identity, save
from experiments.representation_headroom_replay import interpret_original
from experiments.structural_mechanism_screen import ROOT, summarize
from neumann1.contraction_structure import certify_path
from neumann1.public_rewrite_search import propose
from neumann1.representation_program import compile_program, verify_original
from neumann1.representation_rewrite_certificate import check_certificate


def replay(preparation, first, archive, destination):
    start = perf_counter()
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    frozen = json.loads((preparation / "freeze-receipt.json").read_text(encoding="utf-8"))
    receipt = json.loads((preparation / "first-result-receipt.json").read_text(encoding="utf-8"))
    assert digest(preparation / "preregister.json") == frozen["contract_sha256"]
    assert digest(first / "report.json") == receipt["report_sha256"]
    assert digest(first / "manifest.json") == receipt["manifest_sha256"]
    assert digest(archive) == reg["source_archive_sha256"]
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert all(digest(first / p) == pin for p, pin in manifest.items())
    assert {str(p.relative_to(first)).replace("\\", "/") for p in first.rglob("*") if p.is_file()} == set(manifest) | {"manifest.json"}
    assert all(digest(ROOT / p) == pin == digest(preparation / "source" / p) for p, pin in reg["source_pins"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    cases = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((first / "cases").glob("*.json"))]
    observations = [json.loads(line) for p in sorted((first / "observations").glob("*.jsonl"))
                    for line in p.read_text(encoding="utf-8").splitlines()]
    proof_rechecked = controls = tensor_paths = tensor_sources = rows_interpreted = 0
    with zipfile.ZipFile(archive) as source:
        members = {n for n in source.namelist() if n.startswith("data/instances/") and n.endswith(".json")}
        assert members == {c["source_file"] for c in cases if c["kind"] == "contraction"}
        cfg = reg["proof_assay"]
        original_order = [f"proof_{motif.lower()}_d{degree}_r{replica}" for degree in cfg["degrees"]
                          for motif in cfg["motifs"] for replica in range(cfg["replicas"])]
        original_order += ["tensor_" + Path(member).stem for member in sorted(members)]
        by_id = {c["id"]: c for c in cases}
        assert len(by_id) == len(cases) == len(original_order) and set(by_id) == set(original_order)
        # Reproduce preregistered generation order, including floating-point
        # aggregation order. Filesystem lexical order is a different order.
        cases = [by_id[identifier] for identifier in original_order]
        for case in cases:
            group = [o for o in observations if o["case_id"] == case["id"]]
            if case["kind"] == "proof":
                reference = interpret_original(case["original"], case["bindings"])
                rows_interpreted += len(reference)
                symbolic = propose(case["original"])
                cached = set()
                for obs in group:
                    if not obs.get("accepted"):
                        continue
                    candidate = obs["candidate"]
                    key = json.dumps(candidate, sort_keys=True)
                    if key not in cached:
                        assert compile_program(candidate).run([tuple(r) for r in case["bindings"]]) == reference
                        cached.add(key)
                    if obs["route"] == "DIRECT":
                        assert candidate == case["original"]
                    elif obs["route"] == "PUBLIC_SYMBOLIC_CERT":
                        assert candidate == symbolic["candidate"] and obs["certificate"] == symbolic["certificate"]
                    else:
                        assert candidate == case["supplied"]["candidate"]
                    if obs["certificate"] and obs["certificate"]["steps"] and obs["route"] != "FREE_FULL_POLYNOMIAL":
                        assert check_certificate(case["original"], candidate, obs["certificate"])["accepted"]
                    if obs["false_control"] is not None:
                        assert not check_certificate(case["original"], candidate, case["false_certificate"])["accepted"]
                        controls += 1
                    assert not obs["learned"]
                    proof_rechecked += 1
                if any(o.get("accepted") and o["route"] == "FREE_FULL_POLYNOMIAL" for o in group):
                    assert verify_original(case["original"], case["supplied"]["candidate"])["accepted"]
            else:
                original = json.loads(source.read(case["source_file"]))
                assert case["public"] == {"equation": original["format_string"], "shapes": original["shapes"]}
                assert case["supplied_paths"] == original.get("paths", {})
                tensor_sources += 1
                for obs in group:
                    if obs["status"] != "CERTIFIED_MODEL_ONLY":
                        continue
                    proof = certify_path(case["public"], obs["path"])
                    assert proof == obs["certificate"]
                    import opt_einsum as oe
                    _, info = oe.contract_path(case["public"]["equation"], *map(tuple, case["public"]["shapes"]),
                                              shapes=True, optimize=[tuple(s) for s in obs["path"]])
                    assert int(info.opt_cost) == proof["dense_arithmetic_work_model"]
                    assert int(info.largest_intermediate) == proof["largest_intermediate_elements"]
                    if obs["strategy"].startswith("FREE_PUBLISHED_"):
                        label = obs["strategy"].removeprefix("FREE_PUBLISHED_")
                        assert obs["path"] == original["paths"][label]["path"] and obs["oracle_used"]
                    else:
                        assert not obs["oracle_used"]
                    tensor_paths += 1
            print("Replayed " + case["id"], flush=True)
    events = json.loads((first / "events.json").read_text(encoding="utf-8"))
    reconstructed = summarize(reg, cases, observations, events)
    report = json.loads((first / "report.json").read_text(encoding="utf-8"))
    assert all(report[k] == value for k, value in reconstructed.items())
    result = {"status": "PASS", "first_report_sha256": receipt["report_sha256"],
        "manifest_files_checked": len(manifest), "accepted_program_observations_rechecked": proof_rechecked,
        "original_rows_independently_interpreted": rows_interpreted, "false_controls_rejected": controls,
        "derived_tensor_sources_checked": tensor_sources, "tensor_paths_and_cost_model_rechecked": tensor_paths,
        "actual_original_tensor_answers_checked": False, "original_results_modified": False,
        "replay_seconds_not_scored": perf_counter() - start}
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError("Preserve first replay")
    save(destination, result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    replay(*map(Path, sys.argv[1:]))
